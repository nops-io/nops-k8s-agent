from nops_k8s_agent.container_cost.base_labels import BaseLabels
from nops_k8s_agent.settings import SCHEMA_VERSION_DATE


class DeploymentMetrics(BaseLabels):
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
    FILE_PREFIX = "deployment_metadata"
    FILENAME = f"v{SCHEMA_VERSION_DATE}_deployment_metadata_0.parquet"
