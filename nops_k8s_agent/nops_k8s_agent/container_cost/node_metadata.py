from nops_k8s_agent.container_cost.base_labels import BaseLabels
from nops_k8s_agent.settings import SCHEMA_VERSION_DATE


class NodeMetadata(BaseLabels):
    # This class to get pod metrics from prometheus and put it in dictionary
    # List of metrics:
    list_of_metrics = {
        "kube_node_info": [],
    }
    FILE_PREFIX = "node_metadata"
    FILENAME = f"v{SCHEMA_VERSION_DATE}_node_metadata_0.parquet"
    CUSTOM_COLUMN = {"instance_id": []}
    POP_OUT_COLUMN = {"node": [], "pod": [], "namespace": []}

    def custom_metrics_function(self, data: dict) -> str:
        try:
            provider_id = data.get("metric", {}).get("provider_id", "")
            parts = provider_id.split("/")
            instance_id = ""
            if len(parts) > 1:
                instance_id = parts[-1]  # Return the last part for EC2 or the first part for Fargate
            return instance_id
        except Exception:
            return ""

    def pop_out_metric(self, metric: str, data: dict) -> str:
        return data.get("metric", {}).get(metric, "")

    CUSTOM_METRICS_FUNCTION = custom_metrics_function
