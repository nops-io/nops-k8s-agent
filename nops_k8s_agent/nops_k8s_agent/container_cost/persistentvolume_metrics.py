from nops_k8s_agent.container_cost.base_metrics import BaseMetrics
from nops_k8s_agent.settings import SCHEMA_VERSION_DATE


class PersistentvolumeMetrics(BaseMetrics):
    # This class to get pod metrics from prometheus and put it in dictionary
    # List of metrics:
    list_of_metrics = {
        "kube_persistentvolume_capacity_bytes": [
            "persistentvolume",
        ],
        "kube_persistentvolume_status_phase": [
            "persistentvolume",
            "phase",
        ],
        "kube_persistentvolume_info": ["persistentvolume", "ebs_volume_id", "storageclass"],
    }
    FILE_PREFIX = "persistentvolume_metrics"
    FILENAME = f"v{SCHEMA_VERSION_DATE}_persistentvolume_metrics_0.parquet"
