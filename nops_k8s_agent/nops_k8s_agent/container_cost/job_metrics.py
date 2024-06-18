from datetime import datetime
from typing import Any

from loguru import logger

from nops_k8s_agent.container_cost.base_metrics import BaseMetrics
from nops_k8s_agent.settings import SCHEMA_VERSION_DATE
from nops_k8s_agent.utils import derive_suffix_from_settings


class JobMetrics(BaseMetrics):
    # This class to get pod metrics from prometheus and put it in dictionary
    # List of metrics:
    list_of_metrics = {"kube_job_status_failed": ["job_name", "namespace", "reason"], "up": ["job"]}
    FILE_PREFIX = "job_metrics"
    FILENAME = f"v{SCHEMA_VERSION_DATE}_job_metrics_0-{derive_suffix_from_settings()}.parquet"

    def get_metrics(self, start_time: datetime, end_time: datetime, metric_name: str, step: str) -> Any:
        if metric_name == "up":
            query = f"{metric_name}[60m]"
            try:
                response = self.prom_client.custom_query(query)
                logger.info(f"{metric_name} response: {response}")
                return response
            except Exception as e:
                logger.error(f"Error in get_metrics: {e}")
                return None
        return super().get_metrics(start_time, end_time, metric_name, step)
