from nops_k8s_agent.container_cost.base_metrics import BaseMetrics
from nops_k8s_agent.settings import SCHEMA_VERSION_DATE
from nops_k8s_agent.utils import derive_suffix_from_settings


class JobMetrics(BaseMetrics):
    list_of_metrics = {"kube_job_status_failed": ["job_name", "namespace", "reason"]}
    FILE_PREFIX = "job_metrics"
    FILENAME = f"v{SCHEMA_VERSION_DATE}_job_metrics_0-{derive_suffix_from_settings()}.parquet"
