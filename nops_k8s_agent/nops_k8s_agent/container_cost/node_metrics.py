from nops_k8s_agent.container_cost.base_metrics import BaseMetrics


class NodeMetrics(BaseMetrics):
    # This class to get pod metrics from prometheus and put it in dictionary
    # List of metrics:
    list_of_metrics = {
        "kube_node_status_condition": [
            "condition",
            "node",
            "status",
        ],
        "kube_node_status_capacity": [
            "resource",
            "node",
            "unit",
        ],
        "kube_node_status_allocatable": [
            "resource",
            "node",
            "unit",
        ],
    }
    FILE_PREFIX = "node_metrics"
    FILENAME = "node_metrics_0.parquet"
