import uuid
from datetime import datetime

from django.conf import settings

import pandas as pd
import ujson as json
from kubernetes import client
from kubernetes import config
from loguru import logger

from nops_k8s_agent.libs.commonutils import flatten_dict
from nops_k8s_agent.libs.constants import metadata_exclude_fields


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
        return settings.NOPS_K8S_AGENT_CLUSTER_ID

    def list_node(self):
        # TODO CACHE HERE
        node = self.v1.list_node(_preload_content=False)
        return json.loads(node.data)

    def get_metadata(self):
        resource = self.list_node()

        record_enrichment = {
            "extraction_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "schema_version": settings.SCHEMA_VERSION,
            "cluster_id": self.cluster_id(),
            "event_id": str(uuid.uuid4()),
            "cloud": "aws",
            "event_type": "k8s_node_metadata",
        }

        return [
            {"k8s_node_metadata": flatten_dict(item, exclude=metadata_exclude_fields), **record_enrichment}
            for item in resource["items"]
        ]
