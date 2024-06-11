from nops_k8s_agent.container_cost.base_metrics import BaseMetrics
from nops_k8s_agent.settings import SCHEMA_VERSION_DATE
from nops_k8s_agent.utils import derive_suffix_from_settings


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
    FILENAME = f"v{SCHEMA_VERSION_DATE}_persistentvolumeclaim_metrics_0-{derive_suffix_from_settings()}.parquet"
