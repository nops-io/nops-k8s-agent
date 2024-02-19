import sys
import uuid
from collections import defaultdict
from datetime import datetime
from typing import Any

from django.conf import settings

from loguru import logger
from prometheus_api_client import PrometheusConnect


class BaseUsage:
    def __init__(self):
        if settings.NOPS_K8S_AGENT_PROM_TOKEN:
            headers = {"Authorization": settings.NOPS_K8S_AGENT_PROM_TOKEN}
        else:
            headers = {}
        self.prom_client = PrometheusConnect(url=settings.PROMETHEUS_SERVER_ENDPOINT, headers=headers, disable_ssl=True)
        if settings.DEBUG is not True:
            logger.remove()
            logger.add(sys.stderr, level="WARNING")

    @property
    def cluster_id(self) -> str:
        return settings.NOPS_K8S_AGENT_CLUSTER_ARN

    @staticmethod
    def build_metrics_query(template: str, input_params: dict[Any, Any]) -> str:
        return template.format(**input_params)

    @staticmethod
    def get_metric_value(record) -> float:
        metric_value = record["value"] if "value" in record else next(iter(record["values"]), [])
        if metric_value is None:
            return
        return metric_value[1]
