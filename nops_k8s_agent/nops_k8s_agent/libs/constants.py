METADATA_EXCLUDE_FIELDS = [
    "status.conditions",
    "status.addresses",
    "status.images",
    "spec.taints",
    "status.volumesInUse",
    "status.volumesAttached",
    "metadata.managedFields",
]


METRICS_SET = {
    "pod_metadata": {
        "period_seconds": 65 * 60,  # 65 minutes
        "templates": {
            "pod_metadata_fmt_pod_info": "avg_over_time(kube_pod_info[{start_time}])",
            "pod_metadata_fmt_pod_owners": "sum(avg_over_time(kube_pod_owner[{start_time}])) by (pod, owner_name, owner_kind, namespace, uid, {cluster_id})",
            "pod_metadata_fmt_job_owners": "sum(avg_over_time(kube_job_owner[{start_time}])) by (job_name, owner_name, owner_kind, namespace , {cluster_id})",
            "pod_metadata_fmt_replicaset_owners": "sum(avg_over_time(kube_replicaset_owner[{start_time}])) by (replicaset, owner_name, owner_kind, namespace , {cluster_id})",
            "pod_metadata": "sum(avg_over_time(kube_replicationcontroller_owner[{start_time}])) by (replicationcontroller, owner_name, owner_kind, namespace , {cluster_id})",
        },
    },
    "node_metrics": {
        "period_seconds": 15 * 60,  # 15 minutes
        "templates": {
            "node_metrics_fmt_node_memory_Buffers_bytes": "avg(avg_over_time(node_memory_Buffers_bytes[{start_time}])) by (instance, {cluster_id})",
            "node_metrics_fmt_node_memory_Cached_bytes": "avg(avg_over_time(node_memory_Cached_bytes[{start_time}])) by (instance, {cluster_id})",
            "node_metrics_fmt_node_memory_MemFree_bytes": "avg(avg_over_time(node_memory_Buffers_bytes[{start_time}])) by (instance, {cluster_id})",
            "node_metrics_fmt_node_cpu_seconds_total": 'avg(avg_over_time(node_cpu_seconds_total{{mode="idle"}}[{start_time}])) by (instance, {cluster_id}, mode, cpu)',
        },
    },
    "low": {
        "period_seconds": 65 * 60,  # 65 minutes
        "templates": {
            "metrics_fmt_ram_bytes_limit": 'avg(avg_over_time(kube_pod_container_resource_limits_memory_bytes{{container!="", container!="POD", node!=""}}[{start_time}])) by (container, pod, namespace, node, {cluster_id}, provider_id)',
            "metrics_fmt_cpu_cores_limit": 'avg(avg_over_time(kube_pod_container_resource_limits_cpu_cores{{container!="", container!="POD", node!=""}}[{start_time}])) by (container, pod, namespace, node, {cluster_id})',
            "metrics_fmt_ram_bytes_allocated": 'avg(avg_over_time(kube_pod_container_resource_requests_memory_bytes{{container!="", container!="POD", node!=""}}[{start_time}])) by (container, pod, namespace, node, {cluster_id}, provider_id)',
            "metrics_fmt_cpu_cores_allocated": 'avg(avg_over_time(kube_pod_container_resource_requests_cpu_cores{{container!="", container!="POD", node!=""}}[{start_time}])) by (container, pod, namespace, node, {cluster_id})',
            "metrics_fmt_namespace_labels": "avg_over_time(kube_namespace_labels[{start_time}])",
            "metrics_fmt_namespace_annnotations": "avg_over_time(kube_namespace_annotations[{start_time}])",
            "metrics_fmt_pod_labels": "avg_over_time(kube_pod_labels[{start_time}])",
            "metrics_fmt_pod_annotations": "avg_over_time(kube_pod_annotations[{start_time}])",
            "metrics_fmt_service_labels": "avg_over_time(service_selector_labels[{start_time}])",
            "metrics_fmt_deployment_labels": "avg_over_time(deployment_match_labels[{start_time}])",
            "metrics_fmt_statefulset_labels": "avg_over_time(statefulSet_match_labels[{start_time}])",
            "metrics_fmt_pod_info": "avg_over_time(kube_pod_info[{start_time}])",
            "metrics_fmt_container_info": "avg_over_time(kube_pod_container_info[{start_time}])",
            "metrics_fmt_pod_owners": "sum(avg_over_time(kube_pod_owner[{start_time}])) by (pod, owner_name, owner_kind, namespace , {cluster_id})",
        },
    },
    "medium": {
        "period_seconds": 35 * 60,  # 35 minutes
        "templates": {
            "metrics_fmt_ram_usage_bytes": 'avg(avg_over_time(container_memory_usage_bytes{{container!="", container!="POD", node!=""}}[{start_time}])) by (container, pod, namespace, node, {cluster_id}, provider_id)',
            "metrics_fmt_net_transfer_bytes": 'sum(increase(container_network_transmit_bytes_total{{pod!=""}}[{start_time}])) by (pod_name, pod, namespace, {cluster_id})',
            "metrics_fmt_cpu_usage_avg": 'avg(rate(container_cpu_usage_seconds_total{{container!="", container_name!="POD", container!="POD"}}[{start_time}])) by (container_name, container, pod_name, pod, namespace, instance,  {cluster_id})',
            "metrics_fmt_cpu_usage_max": 'max(rate(container_cpu_usage_seconds_total{{container!="", container_name!="POD", container!="POD"}}[{start_time}])) by (container_name, container, pod_name, pod, namespace, instance,  {cluster_id})',
        },
    },
    "high": {
        "period_seconds": 15 * 60,  # 15 minutes
        "templates": {
            "metrics_fmt_pods": "avg(kube_pod_container_status_running{{}}) by (pod, namespace, {cluster_id})[{start_time}:{period}]",
            "metrics_fmt_pods_uid": "avg(kube_pod_container_status_running{{}}) by (pod, namespace, uid, {cluster_id})[{start_time}:{period}]",
        },
    },
}


FREQUENCY_TO_EVENT_TYPE_MAP = {"pod_metadata": "k8s_pod_metadata", "node_metrics": "k8s_node_metrics"}
