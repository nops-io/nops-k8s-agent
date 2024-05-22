import asyncio
from typing import Any

from django.core.management.base import BaseCommand

from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject
from kubernetes_asyncio.client import V1Deployment
from kubernetes_asyncio.client import V1LimitRangeItem
from kubernetes_asyncio.client import V1Pod

from nops_k8s_agent.rightsizing.dependency_ingection.containers import Container
from nops_k8s_agent.rightsizing.dependency_ingection.services import KubernetesClient
from nops_k8s_agent.rightsizing.dependency_ingection.services import RightsizingClient
from nops_k8s_agent.rightsizing.deployments import find_deployment_patch
from nops_k8s_agent.rightsizing.models import PodPatch, DeploymentPatch
from nops_k8s_agent.rightsizing.pods import find_deployment_pods_to_patch


processes_semaphore = asyncio.Semaphore(10)


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

    @inject
    async def process_deployment(
        self, deployment: V1Deployment, kubernetes_client: KubernetesClient = Provide[Container.kubernetes_client]
    ):
        async with processes_semaphore:
            # Live-patch pods if this feature is enabled
            if await kubernetes_client.in_place_pod_vertical_scaling_enabled():
                pods_patches: list[PodPatch] = await self._find_deployment_pods_to_patch(deployment)

                tasks = []
                for pod_patch in pods_patches:
                    tasks.append(self._patch_pod(pod_patch))
                await asyncio.gather(*tasks)

            deployment_patch: DeploymentPatch | None = await self._find_deployment_patch(deployment)
            if deployment_patch:
                await self._patch_deployment(deployment_patch)

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
        namespace = deployment.metadata.namespace
        deployment_policy_requests_change_threshold = self._deployment_policy_requests_change_threshold(deployment)
        namespace_recommendations = await self._get_container_recommendations(namespace=namespace)
        deployment_recommendations: dict[str, Any] = namespace_recommendations.get(deployment.metadata.name, {})
        container_min_max_ranges = await kubernetes_client.container_min_max_ranges(namespace_name=namespace)
        deployment_pods: list[V1Pod] = await kubernetes_client.list_deployment_pods(deployment)

        if not deployment_recommendations:
            return []

        return await find_deployment_pods_to_patch(
            deployment_pods,
            deployment_recommendations,
            container_min_max_ranges,
            deployment_policy_requests_change_threshold,
        )

    @inject
    async def _find_deployment_patch(
        self, deployment: V1Deployment, kubernetes_client: KubernetesClient = Provide[Container.kubernetes_client]
    ) -> DeploymentPatch | None:
        namespace = deployment.metadata.namespace
        deployment_policy_requests_change_threshold = self._deployment_policy_requests_change_threshold(deployment)
        namespace_recommendations = await self._get_container_recommendations(namespace=namespace)
        deployment_recommendations: dict[str, Any] = namespace_recommendations.get(deployment.metadata.name, {})
        container_min_max_ranges = await kubernetes_client.container_min_max_ranges(namespace_name=namespace)

        return await find_deployment_patch(
            deployment,
            deployment_recommendations,
            container_min_max_ranges,
            deployment_policy_requests_change_threshold,
        )

    @staticmethod
    @inject
    async def _patch_pod(
            pod_patch: PodPatch, kubernetes_client: KubernetesClient = Provide[Container.kubernetes_client]
    ):
        try:
            await kubernetes_client.patch_pod(pod_patch)
        except Exception as e:
            print(f"_patch_pod Error: {e}")

    @staticmethod
    @inject
    async def _patch_deployment(
            deployment_patch: DeploymentPatch, kubernetes_client: KubernetesClient = Provide[Container.kubernetes_client]
    ):
        try:
            await kubernetes_client.patch_deployment(deployment_patch)
        except Exception as e:
            print(f"_patch_deployment Error: {e}")

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
