from nops_k8s_agent.container_cost.base_metrics import BaseMetrics


class PersistentvolumeMetrics(BaseMetrics):
    list_of_metrics = {
        "kube_persistentvolume_capacity_bytes": [
            "persistentvolume",
        ],
        "kube_persistentvolume_status_phase": [
            "persistentvolume",
            "phase",
        ],
    }
    FILE_PREFIX = "persistentvolume_metrics"
    FILENAME = "persistentvolume_metrics_0.parquet"
