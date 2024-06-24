from datetime import datetime
from typing import Any

from loguru import logger

from nops_k8s_agent.container_cost.base_metrics import BaseMetrics
from nops_k8s_agent.settings import SCHEMA_VERSION_DATE
from nops_k8s_agent.utils import derive_suffix_from_settings


# as of June 17, 2024 -- unused
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
    }
    FILE_PREFIX = "container_metrics"
    FILENAME = f"v{SCHEMA_VERSION_DATE}_container_metrics_0-{derive_suffix_from_settings()}.parquet"

class ContainerMetricsGranular(BaseMetrics):
    list_of_metrics = {
        "container_memory_usage_bytes": [],
        "container_cpu_usage_seconds_total": [],
        "container_memory_rss": [],
        "container_memory_cache": [],
        "container_memory_working_set_bytes": [],
        "container_cpu_cfs_throttled_seconds_total": [],
        "container_spec_cpu_quota": [],
        "container_spec_cpu_period": [],
    }
    FILE_PREFIX = "container_metrics_granular"
    FILENAME = f"v{SCHEMA_VERSION_DATE}_container_metrics_granular_0-{derive_suffix_from_settings()}.parquet"

    def get_metrics(self, metric_name: str, **kwargs) -> Any:
        query = f"{metric_name}[60m]"
        try:
            response = self.prom_client.custom_query(query)
            logger.info(f"{metric_name} response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error in get_metrics: {e}")
        return None
