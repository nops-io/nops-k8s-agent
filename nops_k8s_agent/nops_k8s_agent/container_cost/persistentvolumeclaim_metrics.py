from nops_k8s_agent.container_cost.base_metrics import BaseMetrics


class PersistentvolumeclaimMetrics(BaseMetrics):
    list_of_metrics = {
        "kube_persistentvolumeclaim_info": [
            "namespace",
            "persistentvolumeclaim",
            "storageclass",
            "volumename",
            "volumemode",
        ],
        "kube_persistentvolumeclaim_resource_requests_storage_bytes": [
            "namespace",
            "persistentvolumeclaim",
        ],
    }
    FILE_PREFIX = "persistentvolumeclaim_metrics"
    FILENAME = "persistentvolumeclaim_metrics_0.parquet"
