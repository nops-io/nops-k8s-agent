from nops_k8s_agent.container_cost.base_metrics import BaseMetrics


class PodMetrics(BaseMetrics):
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
    }
    FILE_PREFIX = "pod_metrics"
    FILENAME = "pod_metrics_0.parquet"
