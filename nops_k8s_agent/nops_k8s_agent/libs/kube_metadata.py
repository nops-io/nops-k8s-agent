import uuid
from datetime import datetime
from typing import Iterable

from django.conf import settings

from kubernetes import client
from kubernetes import config
from kubernetes.client import V1Node
from loguru import logger

from nops_k8s_agent.libs.commonutils import flatten_dict
from nops_k8s_agent.libs.constants import METADATA_EXCLUDE_FIELDS


class KubeMetadata:
    def __init__(self):
        try:
            config.load_incluster_config()
        except config.ConfigException:
            try:
                config.load_kube_config()
            except config.ConfigException as err:
                logger.exception(err)
                raise Exception("Could not configure kubernetes python client")
        self.v1 = client.CoreV1Api()

    @classmethod
    def get_status(cls):
        try:
            cls()
            status = "Success"
        except Exception:
            status = "Failed"
        return status

    def cluster_id(self) -> str:
        return settings.NOPS_K8S_AGENT_CLUSTER_ARN

    def list_node(self) -> Iterable[V1Node]:
        # TODO CACHE HERE

        continue_token = "Initial"
        while continue_token is not None:
            call_kwargs = {"_continue": continue_token if continue_token != "Initial" else None}
            response = self.v1.list_node(**call_kwargs)
            continue_token = response.metadata._continue
            yield from response.items

    def get_metadata(self):
        nodes = self.list_node()

        record_enrichment = {
            "extraction_time": datetime.utcnow().isoformat(),
            "schema_version": settings.SCHEMA_VERSION,
            "cluster_id": self.cluster_id(),
            "event_id": str(uuid.uuid4()),
            "cloud": "aws",
            "event_type": "k8s_node_metadata",
        }
        return [
            {"k8s_node_metadata": flatten_dict(item.to_dict(), exclude=METADATA_EXCLUDE_FIELDS), **record_enrichment}
            for item in nodes
        ]
