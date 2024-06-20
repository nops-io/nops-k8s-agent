from nops_k8s_agent.container_cost.base_metrics import BaseMetrics
from nops_k8s_agent.settings import SCHEMA_VERSION_DATE
from nops_k8s_agent.utils import derive_suffix_from_settings


class PodMetrics(BaseMetrics):
    # This class to get pod metrics from prometheus and put it in dictionary
    # List of metrics:
    list_of_metrics = {
        "kube_pod_owner": ["pod", "owner_name", "owner_kind", "namespace", "owner_is_controller", "uid"],
        # kube_pod_labels empty now
        "kube_pod_container_status_running": ["container", "pod", "namespace", "uid"],
        "kube_pod_container_resource_requests": ["resource", "unit", "container", "pod", "namespace", "node", "uid"],
        # kube_pod_annotations empty now
        "kube_pod_status_phase": ["phase", "pod", "namespace", "uid"],
        "kube_pod_container_status_terminated_reason": ["reason", "container", "pod", "namespace", "uid"],
        "kube_pod_container_status_restarts_total": ["container", "pod", "namespace", "uid"],
        "kube_pod_container_resource_limits": ["resource", "unit", "container", "pod", "namespace", "node", "uid"],
        # "kube_pod_container_resource_limits_cpu_cores": [], # Does not has
        # "kube_pod_container_resource_limits_memory_bytes": [], # Does not has
        "container_network_receive_bytes_total": ["pod", "namespace", "instance"],
        "container_network_transmit_bytes_total": ["pod", "namespace", "instance"],
        "pod_pvc_allocation": ["namespace", "persistentvolume", "persistentvolumeclaim", "pod"],
        "kube_pod_spec_volumes_persistentvolumeclaims_info": [
            "namespace",
            "node",
            "pod",
            "persistentvolumeclaim",
            "uid",
        ],
    }
    FILE_PREFIX = "pod_metrics"
    FILENAME = f"v{SCHEMA_VERSION_DATE}_pod_metrics_0-{derive_suffix_from_settings()}.parquet"
