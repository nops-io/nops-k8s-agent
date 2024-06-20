from nops_k8s_agent.container_cost.base_metrics import BaseMetrics
from nops_k8s_agent.utils import derive_suffix_from_settings
from nops_k8s_agent.settings import SCHEMA_VERSION_DATE


class DeploymentMetrics(BaseMetrics):
    # This class to get pod metrics from prometheus and put it in dictionary
    # List of metrics:
    list_of_metrics = {
        "kube_deployment_spec_replicas": [
            "deployment",
            "namespace",
        ],
        "kube_deployment_status_replicas_available": [
            "deployment",
            "namespace",
        ],
    }
    FILE_PREFIX = "deployment_metrics"
    FILENAME = f"v{SCHEMA_VERSION_DATE}_deployment_metrics_0-{derive_suffix_from_settings()}.parquet"
