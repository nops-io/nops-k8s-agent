from nops_k8s_agent.container_cost.base_metrics import BaseMetrics
from nops_k8s_agent.settings import SCHEMA_VERSION_DATE

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
        "container_cpu_utilization": ["namespace", "pod", "container"],
        "container_memory_utilization": ["namespace", "pod", "container"],
    }
    FILE_PREFIX = "container_metrics"
    FILENAME = f"v{SCHEMA_VERSION_DATE}_container_metrics_0.parquet"
