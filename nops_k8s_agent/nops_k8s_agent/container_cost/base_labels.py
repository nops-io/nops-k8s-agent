import json
import os
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytz
from loguru import logger

from nops_k8s_agent.container_cost.base_prom import BaseProm
from nops_k8s_agent.settings import SCHEMA_VERSION_DATE
from nops_k8s_agent.utils import derive_region_from_settings


class BaseLabels(BaseProm):
    # This class to get pod metrics from prometheus and put it in dictionary
    # List of metrics:
    list_of_metrics = {
        "kube_pod_labels": [],
        "kube_node_labels": [],
        "kube_namespace_labels": [],
        "kube_namespace_annotations": [],
        "kube_pod_annotations": [],
    }
    FILE_PREFIX = "base_labels"
    FILENAME = f"v{SCHEMA_VERSION_DATE}_base_labels_0-{derive_region_from_settings()}.parquet"
    CUSTOM_METRICS_FUNCTION = None
    CUSTOM_COLUMN = None
    POP_OUT_COLUMN = {"node": [], "pod": [], "namespace": []}

    def get_metrics(self, start_time: datetime, end_time: datetime, metric_name: str, step: str) -> Any:
        # This function to get metrics from prometheus

        query = f"avg_over_time({metric_name}[{step}])"
        try:
            response = self.prom_client.custom_query_range(query, start_time=start_time, end_time=end_time, step=step)
            return response
        except Exception as e:
            logger.error(f"Error in get_metrics: {e}")
            return None

    def get_all_metrics(self, start_time: datetime, end_time: datetime, step: str) -> dict:
        # This function to get all metrics from prometheus
        metrics = defaultdict(list)
        for metric_name in self.list_of_metrics.keys():
            response = self.get_metrics(start_time=start_time, end_time=end_time, metric_name=metric_name, step=step)
            if response:
                metrics[metric_name] = response
        return metrics

    def pop_out_metric(self, metric: str, data: dict) -> str:
        return data.get("metric", {}).get(metric, "")

    def convert_to_table_and_save(
        self, period: str, current_time: datetime = None, step: str = "5m", filename: str = FILENAME
    ) -> None:
        now = datetime.now(pytz.utc)
        if current_time is None:
            current_time = now - timedelta(hours=1)
        if period == "last_hour":
            start_time = current_time.replace(minute=0, second=0, microsecond=0)
            end_time = start_time + timedelta(hours=1) - timedelta(seconds=1)
        elif period == "last_day":
            start_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
            end_time = start_time + timedelta(days=1) - timedelta(seconds=1)
        all_metrics_data = self.get_all_metrics(start_time=start_time, end_time=end_time, step=step)

        # Prepare data structure for PyArrow
        columns = {
            "cluster_arn": [],
            "metric_name": [],
            "start_time": [],
            "created_at": [],
            "value": [],
            "values": [],
            "avg_value": [],
            "count_value": [],
            "period": [],
            "step": [],
            "labels": [],
        }
        if self.CUSTOM_COLUMN:
            # Create custom colum base on custom column key instead of update
            columns[list(self.CUSTOM_COLUMN.keys())[0]] = []
        if self.POP_OUT_COLUMN:
            for pop_out_column_name in self.POP_OUT_COLUMN:
                columns[pop_out_column_name] = []

        for metric_name, data_list in all_metrics_data.items():
            for data in data_list:
                if "values" not in data or len(data["values"]) == 0:
                    continue
                columns["cluster_arn"].append(self.cluster_arn)
                metric_labels = data["metric"]
                columns["metric_name"].append(metric_name)
                columns["start_time"].append(int(start_time.timestamp()))
                avg_value = sum([float(x[1]) for x in data["values"]]) / len(data["values"])
                count_value = len(data["values"])
                columns["avg_value"].append(avg_value)
                columns["count_value"].append(count_value)
                columns["values"].append(json.dumps(data["values"]))
                columns["value"].append(float(data["values"][0][1]))
                columns["step"].append(step)
                columns["created_at"].append(now.timestamp())
                columns["period"].append(period)
                columns["labels"].append(json.dumps(metric_labels))
                if self.CUSTOM_METRICS_FUNCTION and callable(self.CUSTOM_METRICS_FUNCTION) and self.CUSTOM_COLUMN:
                    custom_metrics = self.CUSTOM_METRICS_FUNCTION(data)
                    columns[list(self.CUSTOM_COLUMN.keys())[0]].append(custom_metrics)
                if self.POP_OUT_COLUMN:
                    for pop_out_column_name in self.POP_OUT_COLUMN:
                        custom_metrics = self.pop_out_metric(pop_out_column_name, data)
                        columns[pop_out_column_name].append(custom_metrics)

        arrays = {k: pa.array(v) for k, v in columns.items()}
        table = pa.Table.from_pydict(arrays)
        if table.num_rows > 0:
            directory = os.path.dirname(filename)
            os.makedirs(directory, exist_ok=True)
            pq.write_table(table, filename)
