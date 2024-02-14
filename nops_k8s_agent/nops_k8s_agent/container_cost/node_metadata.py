from nops_k8s_agent.container_cost.base_metrics import BaseLabels


def custom_metrics_function(data: dict) -> str:
    provider_id = data.get("metric", {}).get("provider_id", "")
    parts = provider_id.split("/")
    instance_id = ""
    if len(parts) > 1:
        instance_id = parts[-1]  # Return the last part for EC2 or the first part for Fargate
    return instance_id


class NodeMetrics(BaseLabels):
    # This class to get pod metrics from prometheus and put it in dictionary
    # List of metrics:
    list_of_metrics = {
        "kube_node_info": [],
    }
    FILE_PREFIX = "node_metadata"
    FILENAME = "node_metadata_0.parquet"
    CUSTOM_METRICS_FUNCTION = None
    CUSTOM_COLUMN = {"instance_id": []}

    CUSTOM_METRICS_FUNCTION = custom_metrics_function
