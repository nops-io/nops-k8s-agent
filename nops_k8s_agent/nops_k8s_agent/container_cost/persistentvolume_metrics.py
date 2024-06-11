from nops_k8s_agent.container_cost.base_metrics import BaseMetrics
from nops_k8s_agent.settings import SCHEMA_VERSION_DATE
from nops_k8s_agent.utils import derive_suffix_from_settings


class PersistentvolumeMetrics(BaseMetrics):
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
    FILENAME = f"v{SCHEMA_VERSION_DATE}_persistentvolume_metrics_0-{derive_suffix_from_settings()}.parquet"
