import sys
import uuid
from datetime import datetime
from typing import Any

from django.conf import settings

from loguru import logger
from prometheus_api_client import PrometheusConnect

from nops_k8s_agent.libs.commonutils import duration_string
from nops_k8s_agent.libs.commonutils import flatten_dict
from nops_k8s_agent.libs.constants import FREQUENCY_TO_EVENT_TYPE_MAP
from nops_k8s_agent.libs.constants import METRICS_SET

"""
TO Add a new new frequency
nops_k8s_agent/nops_k8s_agent/management/commands/send_metrics.py
start_time
get_metrics
Run job
"""


class KubeMetrics(object):
    def __init__(self):
        if settings.NOPS_K8S_AGENT_PROM_TOKEN:
            headers = {"Authorization": settings.NOPS_K8S_AGENT_PROM_TOKEN}
        else:
            headers = {}
        self.prom_client = PrometheusConnect(url=settings.PROMETHEUS_SERVER_ENDPOINT, headers=headers, disable_ssl=True)
        if settings.DEBUG is not True:
            logger.remove()
            logger.add(sys.stderr, level="WARNING")

    def get_status(self):
        try:
            assert self.prom_client.get_metric_range_data(metric_name="kube_node_info")
            status = "Success"
        except Exception:
            status = "Failed"
        return status

    @property
    def cluster_id(self) -> str:
        return settings.NOPS_K8S_AGENT_CLUSTER_ID

    @staticmethod
    def build_metrics_query(template: str, input_params: dict[Any, Any]) -> str:
        return template.format(**input_params)

    def get_metrics(self, frequency="high"):
        metrics_result = []
        now = datetime.utcnow()
        event_type = FREQUENCY_TO_EVENT_TYPE_MAP.get(frequency, "k8s_metrics")

        try:
            metric_config = METRICS_SET[frequency]

            metrics_params = {
                "cluster_id": "instance",
                "start_time": duration_string(metric_config["period_seconds"]),
                "period": duration_string(metric_config["period_seconds"]),
            }

            for key, query_template in metric_config["templates"].items():
                metrics_query = self.build_metrics_query(query_template, input_params=metrics_params)
                response = self.prom_client.custom_query(query=metrics_query)
                for metric in response:
                    formatted_metric = self.process_metric(metric)
                    metric_enrichment = {
                        "metric_name": key,
                        "cluster_id": self.cluster_id,
                        "event_id": str(uuid.uuid4()),
                        "cloud": "aws",
                        "event_type": event_type,
                        "extraction_time": now.isoformat(),
                        "schema_version": settings.SCHEMA_VERSION,
                    }
                    formatted_metric.update(metric_enrichment)
                    metrics_result.append(formatted_metric)
        except Exception as err:
            logger.warning(err)

        return metrics_result

    @staticmethod
    def process_metric(record):
        metric_value = record["value"] if "value" in record else next(iter(record["values"]), [])
        if metric_value is None:
            return
        return {
            "value": metric_value[1],
            "time": datetime.fromtimestamp(metric_value[0]).isoformat(),
            "metrics_metadata": flatten_dict(record, exclude=["values"], skip_parsing=True),
        }
