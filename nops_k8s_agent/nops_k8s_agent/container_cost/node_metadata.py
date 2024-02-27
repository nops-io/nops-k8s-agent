from nops_k8s_agent.container_cost.base_labels import BaseLabels


class NodeMetadata(BaseLabels):
    list_of_metrics = {
        "kube_node_info": [],
    }
    FILE_PREFIX = "node_metadata"
    FILENAME = "node_metadata_0.parquet"
    CUSTOM_COLUMN = {"instance_id": []}

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
