from typing import Any

from loguru import logger

from nops_k8s_agent.container_cost.base_metrics import BaseMetrics
from nops_k8s_agent.settings import SCHEMA_VERSION_DATE
from nops_k8s_agent.utils import derive_suffix_from_settings


class NodeMetrics(BaseMetrics):
    # This class to get pod metrics from prometheus and put it in dictionary
    # List of metrics:
    list_of_metrics = {
        "kube_node_status_condition": [
            "condition",
            "node",
            "status",
        ],
        "kube_node_status_capacity": [
            "resource",
            "node",
            "unit",
        ],
        "kube_node_status_allocatable": [
            "resource",
            "node",
            "unit",
        ],
        "node_total_hourly_cost": ["instance_type", "node", "provider_id"],
    }
    FILE_PREFIX = "node_metrics"
    FILENAME = f"v{SCHEMA_VERSION_DATE}_node_metrics_0-{derive_suffix_from_settings()}.parquet"


class NodeMetricsGranular(BaseMetrics):
    list_of_metrics = {
        "kube_node_info": [],
        "kube_node_status_condition": [],
        "kube_node_status_capacity": [],
        "kube_node_status_allocatable": [],
        "kube_node_status_allocatable_cpu_cores": [],
    }
    FILE_PREFIX = "node_metrics_granular"
    FILENAME = f"v{SCHEMA_VERSION_DATE}_node_metrics_granular_0-{derive_suffix_from_settings()}.parquet"

    def get_metrics(self, metric_name: str, **kwargs) -> Any:
        query = f"{metric_name}[60m]"
        try:
            response = self.prom_client.custom_query(query)
            logger.info(f"{metric_name} response: {response}")
            return response
        except Exception as e:
            logger.error(f"Error in get_metrics: {e}")
            return None
