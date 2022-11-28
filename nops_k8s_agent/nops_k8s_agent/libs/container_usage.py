import sys
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any

from django.conf import settings

from loguru import logger
from prometheus_api_client import PrometheusConnect

from nops_k8s_agent.libs.base_usage import BaseUsage


class ContainerUsage(BaseUsage):
    def get_container_metric_dict(self) -> dict:
        start_time = "30m"
        metrics_dict = {
            "container_ram_usage_bytes": 'avg(avg_over_time(container_memory_usage_bytes{{container!="", container!="POD", node!=""}}[{start_time}])) by (container, pod, namespace)',
            # "container_cpu_usage_avg": 'avg(rate(container_cpu_usage_seconds_total{{container!="", container_name!="POD", container!="POD"}}[{start_time}])) by (container, pod, namespace)',
            # "container_cpu_usage_max": 'max(rate(container_cpu_usage_seconds_total{{container!="", container_name!="POD", container!="POD"}}[{start_time}])) by (container, pod, namespace)',
            "container_ram_bytes_limit": 'avg(avg_over_time(kube_pod_container_resource_limits_memory_bytes{{container!="", container!="POD", node!=""}}[{start_time}])) by (container, pod, namespace)',
            "container_fmt_cpu_cores_limit": 'avg(avg_over_time(kube_pod_container_resource_limits_cpu_cores{{container!="", container!="POD", node!=""}}[{start_time}])) by (container, pod, namespace )',
            "container_ram_bytes_allocated": 'avg(avg_over_time(kube_pod_container_resource_requests_memory_bytes{{container!="", container!="POD", node!=""}}[{start_time}])) by (container, pod, namespace)',
            "container_cpu_cores_allocated": 'avg(avg_over_time(kube_pod_container_resource_requests_cpu_cores{{container!="", container!="POD", node!=""}}[{start_time}])) by (container, pod, namespace)',
        }
        container_usage_dict = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        for key, query_template in metrics_dict.items():
            metrics_params = {"start_time": start_time}
            from pprint import pprint;import pdb; pdb.set_trace()  # fmt: skip
            metrics_query = self.build_metrics_query(query_template, input_params=metrics_params)
            responses = self.prom_client.custom_query(query=metrics_query)
            for metric_response in responses:
                namespace = metric_response["metric"]["namespace"]
                pod = metric_response["metric"]["pod"]
                container = metric_response["metric"]["container"]
                container_usage_dict[namespace][pod][container][key] = self.get_metric_value(metric_response)
        return container_usage_dict

    def get_container_dict(self) -> dict:
        container_metric_dict = self.get_container_metric_dict()
        response = self.prom_client.custom_query(query="avg_over_time(kube_pod_container_info[30m])")
        container_dict = {}
        for node_record in response:
            record = node_record["metric"]
            container = record["container"]
            container_id = record["container_id"]
            pod = record["pod"]
            namespace = record["namespace"]
            container_metrics = container_metric_dict.get(namespace, {}).get(pod, {}).get(container, {})
            container_dict[container_id] = {
                "container": container,
                "container_id": container_id,
                "pod": pod,
                "namespace": namespace,
                "pod_uid": record["uid"],
            } | container_metrics
        return container_dict
