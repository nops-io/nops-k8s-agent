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


class BaseMetrics(BaseProm):
    # This class to get pod metrics from prometheus and put it in dictionary
    # List of metrics:
    list_of_metrics = {}
    FILENAME = "base_metrics.parquet"

    def get_metrics(self, start_time: datetime, end_time: datetime, metric_name: str, step: str) -> Any:
        # This function to get metrics from prometheus
        group_by_list = self.list_of_metrics.get(metric_name)
        group_by_str = ",".join(group_by_list)

        query = f"avg(avg_over_time({metric_name}[{step}])) by ({group_by_str})"
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
        # Initialize lists for each column
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
        }

        # Dynamically handle labels as columns
        dynamic_labels = set()

        for metric_name, data_list in all_metrics_data.items():
            for data in data_list:
                columns["cluster_arn"].append(self.cluster_arn)
                columns["metric_name"].append(metric_name)
                if "values" not in data or len(data["values"]) == 0:
                    continue
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

                # Handle each label, ensure dynamic columns are created
                for label, value in data["metric"].items():
                    if label != "__name__":
                        if label not in dynamic_labels:
                            dynamic_labels.add(label)
                            columns[label] = [None] * (
                                len(columns["metric_name"]) - 1
                            )  # Initialize previous rows with None
                        columns[label].append(value)

                # Ensure all dynamic columns are updated
                for label in dynamic_labels:
                    if label not in data["metric"]:
                        columns[label].append(None)

        # Ensure all columns are of equal length
        max_len = max(len(col) for col in columns.values())
        for col in columns.keys():
            if len(columns[col]) < max_len:
                columns[col].extend([None] * (max_len - len(columns[col])))

        # Create PyArrow arrays for each column
        arrays = {k: pa.array(v) for k, v in columns.items()}

        # Create a PyArrow Table
        table = pa.Table.from_pydict(arrays)
        directory = os.path.dirname(filename)

        # Ensure the directory exists
        os.makedirs(directory, exist_ok=True)

        # Write the table to a Parquet file
        pq.write_table(table, filename)
