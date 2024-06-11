import os
import sys
from collections import defaultdict
from datetime import datetime
from typing import Any

from django.conf import settings

from loguru import logger
from prometheus_api_client import PrometheusConnect


class BaseProm:
    def __init__(self, cluster_arn: str) -> None:
        env_prom_token = settings.NOPS_K8S_AGENT_PROM_TOKEN
        env_prom_endpoint = os.environ.get("APP_PROMETHEUS_SERVER_ENDPOINT", None)

        if env_prom_token and len(env_prom_token):
            headers = {"Authorization": env_prom_token}
        else:
            headers = {}
        self.prom_client = PrometheusConnect(
            url=env_prom_endpoint,
            headers=headers,
            disable_ssl=True,
        )
        if settings.DEBUG is not True:
            logger.remove()
            logger.add(sys.stderr, level="WARNING")

        self.cluster_arn = cluster_arn

    def get_metrics(self, query: str, start_time: datetime, end_time: datetime, metric_name: str, step: str) -> Any:
        try:
            response = self.prom_client.custom_query_range(query, start_time=start_time, end_time=end_time, step=step)
            return response
        except Exception as e:
            logger.error(f"Error in get_metrics: {e}")
            return None

    def build_query(metric_name, step):
        pass

    def get_all_metrics(self, start_time: datetime, end_time: datetime, step: str) -> dict:
        # This function to get all metrics from prometheus
        metrics = defaultdict(list)
        for metric_name in self.list_of_metrics.keys():
            query = self.build_query(metric_name, step)
            response = self.get_metrics(
                query=query, start_time=start_time, end_time=end_time, metric_name=metric_name, step=step
            )
            if response:
                metrics[metric_name] = response
        return metrics
