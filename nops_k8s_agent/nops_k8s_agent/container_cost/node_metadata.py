from nops_k8s_agent.container_cost.base_labels import BaseLabels
from nops_k8s_agent.settings import SCHEMA_VERSION_DATE
from nops_k8s_agent.utils import derive_suffix_from_settings

class NodeMetadata(BaseLabels):
    # This class to get pod metrics from prometheus and put it in dictionary
    # List of metrics:
    list_of_metrics = {
        "kube_node_info": [],
    }
    FILE_PREFIX = "node_metadata"
    FILENAME = f"v{SCHEMA_VERSION_DATE}_node_metadata_0-{derive_suffix_from_settings()}.parquet"
    CUSTOM_COLUMN = {"instance_id": []}
    POP_OUT_COLUMN = {"node": [], "namespace": []}

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

    CUSTOM_METRICS_FUNCTION = custom_metrics_function
