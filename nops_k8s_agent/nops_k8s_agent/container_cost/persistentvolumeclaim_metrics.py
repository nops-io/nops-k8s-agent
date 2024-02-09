from base_metrics import BaseMetrics


class PersistentvolumeclaimMetrics(BaseMetrics):
    # This class to get pod metrics from prometheus and put it in dictionary
    # List of metrics:
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
    FILENAME = "persistentvolumeclaim_metrics.parquet"
