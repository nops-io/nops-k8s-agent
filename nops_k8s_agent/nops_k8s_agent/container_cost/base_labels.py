from collections import defaultdict
from datetime import datetime
from datetime import timedelta
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq
import pytz
from loguru import logger

from nops_k8s_agent.container_cost.base_prom import BaseProm


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
    FILENAME = "base_labels.parquet"

    def get_metrics(self, metric_name: str, period: str = "last_hour") -> Any:
        # This function to get metrics from prometheus
        now = datetime.now(pytz.utc)

        if period == "last_hour":
            start_time = now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1)
            end_time = start_time + timedelta(hours=1) - timedelta(seconds=1)
        elif period == "last_day":
            start_time = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
            end_time = start_time + timedelta(days=1) - timedelta(seconds=1)

        query = f"avg_over_time({metric_name}[15m])"
        try:
            response = self.prom_client.custom_query_range(query, start_time=start_time, end_time=end_time, step="1h")
            return response
        except Exception as e:
            logger.error(f"Error in get_metrics: {e}")
            return None

    def get_all_metrics(self, period: str = "last_hour") -> dict:
        # This function to get all metrics from prometheus
        metrics = defaultdict(list)
        for metric_name in self.list_of_metrics.keys():
            response = self.get_metrics(metric_name, period)
            if response:
                metrics[metric_name] = response
        return metrics

    def convert_to_table_and_save(self, period: str = "last_hour", filename: str = FILENAME) -> None:
        all_metrics_data = self.get_all_metrics(period)
        now = datetime.now(pytz.utc)

        # Prepare data structure for PyArrow
        columns = {
            "metric_name": [],
            "timestamp": [],
            "value": [],
            "period": [],
            "created_at": [],
        }

        # Dynamically handle labels as columns
        dynamic_labels = set()

        for metric_name, data_list in all_metrics_data.items():
            for data in data_list:
                metric_labels = data["metric"]
                metric_values = data["values"]  # This is a list of [timestamp, value] lists

                for value_pair in metric_values:
                    timestamp, value = value_pair
                    columns["metric_name"].append(metric_name)
                    columns["timestamp"].append(timestamp)
                    columns["value"].append(value)
                    columns["period"].append(period)
                    columns["created_at"].append(now.timestamp())

                    # Add/update dynamic labels for this metric
                    for label, label_value in metric_labels.items():
                        if label not in columns:
                            columns[label] = [None] * (len(columns["metric_name"]) - 1)  # Initialize with Nones
                            dynamic_labels.add(label)
                        columns[label].append(label_value)

                # Ensure all dynamic label columns are of equal length to other columns
                for label in dynamic_labels:
                    if label not in metric_labels:
                        columns[label].append(None)

        # Normalize column lengths
        max_len = max(len(col) for col in columns.values())
        for label in dynamic_labels:
            if len(columns[label]) < max_len:
                columns[label].extend([None] * (max_len - len(columns[label])))

        # Create PyArrow arrays for each column and build the table
        arrays = {k: pa.array(v, pa.string() if k in dynamic_labels else None) for k, v in columns.items()}
        table = pa.Table.from_pydict(arrays)

        # Write the table to a Parquet file
        pq.write_table(table, filename)
