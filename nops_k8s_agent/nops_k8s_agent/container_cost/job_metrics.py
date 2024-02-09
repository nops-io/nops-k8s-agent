from nops_k8s_agent.container_cost.base_metrics import BaseMetrics


class JobMetrics(BaseMetrics):
    # This class to get pod metrics from prometheus and put it in dictionary
    # List of metrics:
    list_of_metrics = {"kube_job_status_failed": ["job_name", "namespace", "reason"]}
    FILENAME = "job_metrics.parquet"
