from nops_k8s_agent.container_cost.base_metrics import BaseMetrics


class JobMetrics(BaseMetrics):
    list_of_metrics = {"kube_job_status_failed": ["job_name", "namespace", "reason"]}
    FILE_PREFIX = "job_metrics"
    FILENAME = "job_metrics_0.parquet"
