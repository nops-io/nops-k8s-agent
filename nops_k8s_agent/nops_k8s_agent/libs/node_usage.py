import sys
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any

from django.conf import settings

from loguru import logger
from prometheus_api_client import PrometheusConnect

from nops_k8s_agent.libs.base_usage import BaseUsage


class NodeUsage(BaseUsage):
    def get_node_dict(self) -> dict:
        # Expect retuning is a list of node with name , IP and instand id
        response = self.prom_client.custom_query(query="avg_over_time(kube_node_info[30m])")
        node_dict = {}
        for node_record in response:
            record = node_record["metric"]
            node_name = record["node"]
            provider_id = record["provider_id"]
            if provider_id.startswith("aws:///"):
                instance_id = provider_id.split("/")[-1]
                availability_zone = provider_id[7:].split("/")[0]
                node_host = node_name.split(".")[0][3:].replace("-", ".")
            else:
                instance_id = "N/A"
                availability_zone = "N/A"
                node_host = record["internal_ip"]

            node_dict[node_host] = {
                "node": node_name,
                "provider_id": provider_id,
                "instance_id": instance_id,
                "availability_zone": availability_zone,
            }
        return node_dict

    def get_metrics_dict(self, query) -> dict:
        response = self.prom_client.custom_query(query)
        node_dict = {}
        for node_record in response:
            node_host = node_record["metric"]["instance"].split(":")[0]
            value = node_record["value"][1]
            node_dict[node_host] = value
        return node_dict

    def get_node_metric_dict(self) -> dict:
        start_time = "30m"
        metrics_dict = {
            "node_metrics_fmt_node_memory_Buffers_bytes": "avg(avg_over_time(node_memory_Buffers_bytes[{start_time}])) by (instance)",
            "node_metrics_fmt_node_memory_Cached_bytes": "avg(avg_over_time(node_memory_Cached_bytes[{start_time}])) by (instance)",
            "node_metrics_fmt_node_memory_MemFree_bytes": "avg(avg_over_time(node_memory_Buffers_bytes[{start_time}])) by (instance)",
            "node_metrics_fmt_node_cpu_seconds_total": 'avg(avg_over_time(node_cpu_seconds_total{{mode="idle"}}[{start_time}])) by (instance)',
        }
        node_usage_dict = defaultdict(dict)
        for key, query_template in metrics_dict.items():
            metrics_params = {"start_time": start_time}
            metrics_query = self.build_metrics_query(query_template, input_params=metrics_params)
            responses = self.prom_client.custom_query(query=metrics_query)
            for metric_response in responses:
                instance = metric_response["metric"]["instance"].split(":")[0]
                node_usage_dict[instance][key] = self.get_metric_value(metric_response)

        return node_usage_dict

    def get_events(self) -> list:
        now = datetime.utcnow()
        final_result = []
        node_dict = self.get_node_dict()
        node_metric_dict = self.get_node_metric_dict()
        for key in node_dict:
            metadata = {
                "cluster_id": self.cluster_id,
                "event_id": str(uuid.uuid4()),
                "cloud": "aws",
                "node_ip": key,
                "event_type": "k8s_node_usage",
                "extraction_time": now.isoformat(),
            }
            result = node_dict[key] | node_metric_dict.get(key) | metadata
            final_result.append(result)
        return final_result
