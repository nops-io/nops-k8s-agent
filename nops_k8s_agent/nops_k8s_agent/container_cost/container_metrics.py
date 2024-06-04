from datetime import datetime
from typing import Any

from loguru import logger

from nops_k8s_agent.container_cost.base_metrics import BaseMetrics
from nops_k8s_agent.settings import SCHEMA_VERSION_DATE
from nops_k8s_agent.utils import derive_suffix_from_settings


class ContainerMetrics(BaseMetrics):
    # cAdvisor
    list_of_metrics = {
        "container_cpu_usage_seconds_total": ["namespace", "pod", "container"],
        "container_cpu_cfs_throttled_seconds_total": ["namespace", "pod", "container"],
        "container_memory_usage_bytes": ["namespace", "pod", "container"], 
        "container_memory_working_set_bytes": ["namespace", "pod", "container"],
        "container_memory_cache": ["namespace", "pod", "container"],
        "container_memory_rss": ["namespace", "pod", "container"],
        "container_fs_usage_bytes": ["namespace", "pod", "container"],
        "container_fs_reads_bytes_total": ["namespace", "pod", "container"],
        "container_fs_writes_bytes_total": ["namespace", "pod", "container"], 
        "rate_container_cpu_usage_seconds_total": [],
    }
    FILE_PREFIX = "container_metrics"
    FILENAME = f"v{SCHEMA_VERSION_DATE}_container_metrics_0-{derive_suffix_from_settings()}.parquet"

    def get_metrics(self, start_time: datetime, end_time: datetime, metric_name: str, step: str) -> Any:
        if metric_name == "rate_container_cpu_usage_seconds_total":
            query = 'rate(container_cpu_usage_seconds_total{pod!="",container!=""}[5m])'
            try:
                response = self.prom_client.custom_query_range(query, start_time=start_time, end_time=end_time, step=step)
                return response
            except Exception as e:
                logger.error(f"Error in get_metrics: {e}")
                return None
        return super().get_metrics(start_time, end_time, metric_name, step)