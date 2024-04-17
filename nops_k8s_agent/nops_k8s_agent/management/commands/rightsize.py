import asyncio
from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand

from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject
from kubernetes_asyncio.client import V1Deployment
from kubernetes_asyncio.client import V1Pod

from nops_k8s_agent.rightsizing.containers import Container
from nops_k8s_agent.rightsizing.models import PodPatch
from nops_k8s_agent.rightsizing.services import KubernetesClient
from nops_k8s_agent.rightsizing.services import RightsizingClient
from nops_k8s_agent.rightsizing.utils import get_container_patch


@inject
class Command(BaseCommand):
    nops_configs: dict[str, Any] = {}

    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.rightsize())

    @inject
    async def rightsize(self, kubernetes_client: KubernetesClient = Provide[Container.kubernetes_client]):
        self.nops_configs = await self._get_nops_configs()

        tasks = []
        all_namespaces = await kubernetes_client.list_all_namespaces()
        for namespace in all_namespaces.items:
            tasks.append(self.process_namespace(namespace.metadata.name))
        await asyncio.gather(*tasks)

    async def process_namespace(self, namespace: str):
        all_deployments: list[V1Deployment] = await self._list_deployments(namespace=namespace)
        configured_deployments: list[V1Deployment] = all_deployments  # TODO: add filtering logic

        tasks = []
        for deployment in configured_deployments:
            tasks.append(self.process_deployment(deployment))
        await asyncio.gather(*tasks)

    async def process_deployment(self, deployment: V1Deployment):
        pods_patches: list[PodPatch] = await self._find_deployment_pods_to_patch(deployment)

        tasks = []
        for pod_patch in pods_patches:
            tasks.append(self._patch_pod(pod_patch))
        await asyncio.gather(*tasks)

    @staticmethod
    @inject
    async def _get_nops_configs(
        rightsizing_client: RightsizingClient = Provide[Container.rightsizing_client],
    ) -> dict[str, Any]:
        return await rightsizing_client.get_configs()

    @staticmethod
    @inject
    async def _get_container_recommendations(
        namespace: str, rightsizing_client: RightsizingClient = Provide[Container.rightsizing_client]
    ) -> dict[str, Any]:
        return await rightsizing_client.get_namespace_recommendations(namespace=namespace)

    def _deployment_policy(self, namespace: str, deployment_name: str) -> None | dict:
        return self.nops_configs.get(namespace, {}).get(deployment_name, {}).get("policy")

    def _deployment_policy_requests_change_threshold(self, deployment: V1Deployment) -> float:
        policy = self._deployment_policy(deployment.metadata.namespace, deployment.metadata.name)
        if isinstance(policy, dict):
            return policy.get("threshold_percentage", 0.0)
        else:
            return 0.0

    @inject
    async def _list_deployments(
        self, namespace: str, kubernetes_client: KubernetesClient = Provide[Container.kubernetes_client]
    ) -> list[V1Deployment]:
        configured_deployments: list[V1Deployment] = []
        all_deployments = await kubernetes_client.list_namespace_deployments(namespace_name=namespace)
        nops_configured_deployments = list(self.nops_configs.get(namespace, {}).keys())

        for deployment in all_deployments.items:
            if deployment.metadata.name not in nops_configured_deployments:
                continue
            configured_deployments.append(deployment)

        return configured_deployments

    @inject
    async def _find_deployment_pods_to_patch(
        self, deployment: V1Deployment, kubernetes_client: KubernetesClient = Provide[Container.kubernetes_client]
    ) -> list[PodPatch]:
        pods_to_patch: list[PodPatch] = []

        deployment_policy_requests_change_threshold = self._deployment_policy_requests_change_threshold(deployment)
        deployment_pods: list[V1Pod] = await kubernetes_client.list_deployment_pods(deployment)
        namespace_recommendations = await self._get_container_recommendations(namespace=deployment.metadata.namespace)
        deployment_recommendations = namespace_recommendations.get(deployment.metadata.name, {})

        print(f"{deployment_recommendations=}")

        if not deployment_recommendations:
            return pods_to_patch

        for pod in deployment_pods:
            pod_patch = PodPatch(pod_name=pod.metadata.name, pod_namespace=pod.metadata.namespace, containers=[])

            for container in pod.spec.containers:
                container_requests_recommendations = deployment_recommendations.get(container.name, {}).get(
                    "requests", {}
                )
                if not container_requests_recommendations:
                    continue

                recommended_cpu_requests = Decimal(container_requests_recommendations.get("cpu", 0))
                recommended_ram_requests = Decimal(container_requests_recommendations.get("memory", 0))
                container_patch = get_container_patch(
                    container=container,
                    recommended_cpu_requests=recommended_cpu_requests,
                    recommended_ram_requests=recommended_ram_requests,
                    deployment_policy_requests_change_threshold=deployment_policy_requests_change_threshold,
                )
                if container_patch:
                    pod_patch.containers.append(container_patch)

            if pod_patch.containers:
                pods_to_patch.append(pod_patch)
        return pods_to_patch

    @staticmethod
    @inject
    async def _patch_pod(
        pod_patch: PodPatch, kubernetes_client: KubernetesClient = Provide[Container.kubernetes_client]
    ):
        try:
            await kubernetes_client.patch_pod(pod_patch)
        except Exception as e:
            print(f"Error: {e}")
