import sys

from django.conf import settings

from loguru import logger
from prometheus_api_client import PrometheusConnect


class BaseProm:
    def __init__(self, cluster_arn: str) -> None:
        if settings.NOPS_K8S_AGENT_PROM_TOKEN:
            headers = {"Authorization": settings.NOPS_K8S_AGENT_PROM_TOKEN}
        else:
            headers = {}
        self.prom_client = PrometheusConnect(
            url="http://nops-prometheus-server.nops-prometheus-system.svc.cluster.local:80",
            headers=headers,
            disable_ssl=True,
        )
        if settings.DEBUG is not True:
            logger.remove()
            logger.add(sys.stderr, level="WARNING")

        self.cluster_arn = cluster_arn
