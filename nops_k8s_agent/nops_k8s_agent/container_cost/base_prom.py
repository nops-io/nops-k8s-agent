import os
import sys

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
