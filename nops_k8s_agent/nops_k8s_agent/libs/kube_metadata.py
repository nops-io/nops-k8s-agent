import uuid
from datetime import datetime

from django.conf import settings

import pandas as pd
import ujson as json
from kubernetes import client
from kubernetes import config
from loguru import logger


def transform(inp, non_metric_cols):
    x = {}
    y = []
    for col in non_metric_cols:
        # Check if this is json string change it to object
        try:
            x[col] = json.loads(inp[col])
        except:
            x[col] = inp[col]
    y.append(x)
    return pd.Series(y)


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

    def get_cluster_name(self):
        # This is a tricky one we can get it inside from API, so we assume it's first node name
        resource = self.list_node()
        try:
            cluster_name = "-".join(resource["items"][0]["metadata"]["name"].split("-")[:-2])
            if not cluster_name:
                cluster_name = resource["items"][0]["metadata"]["name"]
            return cluster_name
        except Exception as err:
            logger.exception(err)
            return "Not Available"

    def list_node(self):
        # TODO CACHE HERE
        node = self.v1.list_node(_preload_content=False)
        return json.loads(node.data)

    def get_metadata(self):
        resource = self.list_node()
        df = pd.json_normalize(resource["items"])
        df["cluster_id"] = str(self.get_cluster_name())
        df.drop(
            columns=[
                "status.conditions",
                "status.addresses",
                "status.images",
                "spec.taints",
                "status.volumesInUse",
                "status.volumesAttached",
                "metadata.managedFields",
            ],
            inplace=True,
            errors="ignore",
        )
        k8s_node_metadata = [col for col in list(df.columns)]
        df[["k8s_node_metadata"]] = df.apply(lambda x: transform(x, k8s_node_metadata), axis=1)
        df["extraction_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        df["schema_version"] = settings.SCHEMA_VERSION
        df["cluster_id"] = self.get_cluster_name()
        df["event_id"] = str(uuid.uuid4())
        df["cloud"] = "aws"  # TODO SUPPORT MORE CLOUD
        df["event_type"] = "k8s_node_metadata"
        df.drop(columns=k8s_node_metadata, inplace=True)
        return df.to_dict(orient="records")
