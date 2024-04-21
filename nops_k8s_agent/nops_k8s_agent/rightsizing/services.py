import os
import re
from abc import ABC
from abc import abstractmethod
from typing import Any

from kubernetes_asyncio import client
from kubernetes_asyncio import config
from kubernetes_asyncio.client import VersionInfo
from kubernetes_asyncio.client import V1Deployment
from kubernetes_asyncio.client import V1DeploymentList
from kubernetes_asyncio.client import V1NamespaceList
from kubernetes_asyncio.client import V1Pod
from kubernetes_asyncio.client.api_client import ApiClient

from nops_k8s_agent.rightsizing.models import PodPatch


class RightsizingClient(ABC):
    @abstractmethod
    async def get_configs(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def get_namespace_recommendations(self, namespace: str) -> dict[str, Any]:
        raise NotImplementedError


class KubernetesClient(ABC):
    @abstractmethod
    async def get_cluster_info(self) -> VersionInfo:
        raise NotImplementedError

    @abstractmethod
    async def in_place_pod_vertical_scaling_enabled(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def get_feature_gates_statuses(self) -> dict[str, bool]:
        raise NotImplementedError

    @abstractmethod
    async def list_all_namespaces(self) -> V1NamespaceList:
        raise NotImplementedError

    @abstractmethod
    async def list_namespace_deployments(self, namespace_name: str) -> V1DeploymentList:
        raise NotImplementedError

    @abstractmethod
    async def list_deployment_pods(self, deployment: V1Deployment) -> list[V1Pod]:
        raise NotImplementedError

    @abstractmethod
    async def patch_pod(self, pod_patch: PodPatch) -> None:
        raise NotImplementedError


class RightsizingClientService(RightsizingClient):
    async def get_configs(self) -> dict[str, Any]:
        raise NotImplementedError

    async def get_namespace_recommendations(self, namespace: str) -> dict[str, Any]:
        raise NotImplementedError


class RightsizingClientMock(RightsizingClient):
    async def get_configs(self) -> dict[str, Any]:
        """
        MOCKED! Gets the list of nOps configured deployments for a cluster
        Returns:
        {
            "namespace_1": {
                "deployment_1": {
                    "policy": {
                        "threshold_percentage": 0.1  # Do not do rightsizing if the current and new value difference is smaller than the threshold percentage
                    }
                }
            }
        }
        """
        return {"opencost": {"opencost": {"policy": {"threshold_percentage": 0.1}}}}

    async def get_namespace_recommendations(self, namespace: str) -> dict[str, Any]:
        """
        MOCKED! Gets limits/requests recommendations for containers by deployment
        Returns:
        {
            "deployment_1": {
                "container_1": {
                    "requests": {"cpu": 0.2, "memory": 220000000}
                }
            }
        }
        """
        if namespace == "opencost":
            return {"opencost": {"opencost": {"requests": {"cpu": 0.32, "memory": 73401320}}}}
        else:
            return {}


class KubernetesClientService(KubernetesClient):
    def __init__(self) -> None:
        config.load_incluster_config()

    async def get_cluster_info(self) -> VersionInfo:
        async with ApiClient() as api:
            version_client = client.VersionApi(api)
            version_info = await version_client.get_code()
            return version_info

    async def in_place_pod_vertical_scaling_enabled(self) -> bool:
        return (await self.get_feature_gates_statuses()).get("InPlacePodVerticalScaling") is True

    async def get_feature_gates_statuses(self) -> dict[str, bool]:
        feature_statuses = {}
        try:
            async with ApiClient() as api:
                api_client = client.ApiClient(api)
                api_response = await api_client.call_api(
                    "/metrics", "GET", auth_settings=["BearerToken"], response_type="str", _preload_content=False
                )
                metrics = api_response[0].data.decode('utf-8').split("\n")

            feature_gates = [metric for metric in metrics if metric.startswith("kubernetes_feature_enabled")]
            for feature_gate in feature_gates:
                match = re.search(r"name=\"([^\"]*)\"", feature_gate)
                if match:
                    feature_statuses[match.group(1)] = feature_gate[-1] == "1"
        except Exception as e:
            print(f"get_feature_gates_statuses error {e}")
        return feature_statuses

    async def list_all_namespaces(self) -> V1NamespaceList:
        async with ApiClient() as api:
            v1_client = client.CoreV1Api(api)
            return await v1_client.list_namespace(watch=False)

    async def list_namespace_deployments(self, namespace_name: str) -> V1DeploymentList:
        async with ApiClient() as api:
            apps_v1 = client.AppsV1Api(api)
            return await apps_v1.list_namespaced_deployment(namespace=namespace_name, watch=False)

    async def list_deployment_pods(self, deployment: V1Deployment) -> list[V1Pod]:
        pods: list[V1Pod] = []
        async with ApiClient() as api:
            v1_client = client.CoreV1Api(api)
            selector = deployment.spec.selector.match_labels
            selector_query = ",".join([f"{k}={v}" for k, v in selector.items()])
            deployment_pods = await v1_client.list_namespaced_pod(
                namespace=deployment.metadata.namespace, label_selector=selector_query
            )
            pods.extend(deployment_pods.items)
        return pods

    async def patch_pod(self, pod_patch: PodPatch) -> None:
        async with ApiClient() as api:
            v1 = client.CoreV1Api(api)
            pod_patch_kwargs = pod_patch.to_patch_kwargs()
            print(f"Patching pod {pod_patch.pod_name} setting containers {pod_patch_kwargs=}")
            await v1.patch_namespaced_pod(
                **pod_patch_kwargs,
                _content_type="application/json-patch+json",  # (optional, default if patch is a list)
            )


nops_client: RightsizingClient | None = None
kubernetes_client: KubernetesClient | None = None


def get_rightsizing_nops_client() -> RightsizingClient:
    global nops_client
    if nops_client is None:
        if os.environ.get("APP_ENV") == "live":
            # nops_client = RightsizingClientService()
            nops_client = RightsizingClientMock()
        else:
            nops_client = RightsizingClientMock()
    return nops_client


def get_kubernetes_client() -> KubernetesClient:
    global kubernetes_client
    if kubernetes_client is None:
        if os.environ.get("APP_ENV") == "live":
            kubernetes_client = KubernetesClientService()
        else:
            kubernetes_client = KubernetesClientService()
    return kubernetes_client
