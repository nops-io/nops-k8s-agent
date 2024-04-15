import asyncio
from collections import defaultdict
from decimal import Decimal
from typing import Any

from django.core.management.base import BaseCommand

from kubernetes.utils.quantity import parse_quantity
from kubernetes_asyncio import client
from kubernetes_asyncio import config
from kubernetes_asyncio.client.api_client import ApiClient

from nops_k8s_agent.rightsizing.utils import format_quantity
from nops_k8s_agent.rightsizing.utils import percentages_difference_threshold_met


class Command(BaseCommand):
    nops_configs: dict[str, Any] = {}

    @staticmethod
    def _init_client():
        config.load_incluster_config()

    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.rightsize())

    async def rightsize(self):
        self._init_client()
        self.nops_configs = await self._get_nops_configs()
        print(f"{self.nops_configs=}\n\n")
        tasks = []

        async with ApiClient() as api:
            v1_client = client.CoreV1Api(api)
            all_namespaces = await v1_client.list_namespace(watch=False)
            for namespace in all_namespaces.items:
                tasks.append(self.process_namespace(namespace.metadata.name))

        await asyncio.gather(*tasks)

    async def process_namespace(self, namespace: str):
        all_deployments = await self._list_deployments(namespace=namespace)
        configured_deployments = all_deployments  # TODO: add filtering logic
        configured_deployments = await self._enrich_deployments_with_pods(namespace, configured_deployments)
        pods_to_patch = await self._find_pods_to_patch(namespace, configured_deployments)

        tasks = []
        for pod_name, pod_data in pods_to_patch.items():
            tasks.append(self._patch_pod(namespace, pod_name, pod_data.get("containers", {})))

        await asyncio.gather(*tasks)

    @staticmethod
    async def _get_nops_configs() -> dict[str, Any]:
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

    def _deployment_policy(self, namespace: str, deployment_name: str) -> None | dict:
        return self.nops_configs.get(namespace, {}).get(deployment_name, {}).get("policy")

    def _deployment_policy_threshold(self, namespace: str, deployment_name: str) -> float:
        policy = self._deployment_policy(namespace, deployment_name)
        if isinstance(policy, dict):
            return policy.get("threshold_percentage", 0.0)
        else:
            return 0.0

    async def _list_deployments(self, namespace: str):
        deployments = {}

        async with ApiClient() as api:
            apps_v1 = client.AppsV1Api(api)
            all_deployments = await apps_v1.list_namespaced_deployment(namespace=namespace, watch=False)
            nops_configured_deployments = list(self.nops_configs.get(namespace, {}).keys())

            for deployment in all_deployments.items:
                if deployment.metadata.name not in nops_configured_deployments:
                    continue

                selector = deployment.spec.selector.match_labels
                deployments[deployment.metadata.name] = {"selector": selector}

        return deployments

    @staticmethod
    async def _enrich_deployments_with_pods(namespace: str, deployments: dict[str, Any]) -> dict[str, Any]:
        """
        Enriches deployments with pods that are controlled by them.
        """

        async with ApiClient() as api:
            v1_client = client.CoreV1Api(api)
            for deployment, deployment_data in deployments.items():
                # Fetch the selector for each deployment
                selector = deployment_data.get("selector")
                selector_query = ",".join([f"{k}={v}" for k, v in selector.items()])
                deployment_pods = await v1_client.list_namespaced_pod(
                    namespace=namespace, label_selector=selector_query
                )
                deployment_data["pods"] = {}
                for pod in deployment_pods.items:
                    deployment_data["pods"][pod.metadata.name] = {
                        "containers": {container.name: container.resources for container in pod.spec.containers}
                    }

        return deployments

    @staticmethod
    async def _get_container_recommendations(namespace: str) -> dict[str, Any]:
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
        return {"opencost": {"opencost": {"requests": {"cpu": 0.32, "memory": 73401320}}}}

    async def _find_pods_to_patch(self, namespace: str, configured_deployments: dict[str, Any]) -> dict[str, Any]:
        pods_to_patch = defaultdict(lambda: defaultdict(dict))
        recommendations = await self._get_container_recommendations(namespace=namespace)

        for deployment, deployment_data in configured_deployments.items():
            deployment_policy_threshold = self._deployment_policy_threshold(namespace, deployment)

            deployment_recommendations = recommendations.get(deployment, {})
            if not deployment_recommendations:
                continue

            for pod, pod_data in deployment_data.get("pods", {}).items():
                for container, container_data in pod_data.get("containers", {}).items():
                    container_requests_recommendations = deployment_recommendations.get(deployment, {}).get(
                        "requests", {}
                    )
                    if not container_requests_recommendations:
                        continue

                    new_requests = {}

                    recommended_cpu_requests = Decimal(container_requests_recommendations.get("cpu", 0))
                    recommended_ram_requests = Decimal(container_requests_recommendations.get("memory", 0))

                    actual_cpu_requests = container_data.requests.get("cpu")
                    actual_ram_requests = container_data.requests.get("memory")

                    # Set new CPU requests if they were not set OR current request is lower than recommended
                    if recommended_cpu_requests and not actual_cpu_requests:
                        new_requests["cpu"] = recommended_cpu_requests
                    elif recommended_cpu_requests and percentages_difference_threshold_met(
                        parse_quantity(actual_cpu_requests),
                        recommended_cpu_requests,
                        deployment_policy_threshold,
                    ):
                        new_requests["cpu"] = recommended_cpu_requests

                    # Set new Memory requests if they were not set OR current request is lower than recommended
                    if recommended_ram_requests and not actual_ram_requests:
                        new_requests["memory"] = recommended_ram_requests

                    elif recommended_ram_requests and percentages_difference_threshold_met(
                        parse_quantity(actual_ram_requests),
                        recommended_ram_requests,
                        deployment_policy_threshold,
                    ):
                        new_requests["memory"] = recommended_ram_requests

                    if new_requests:
                        pods_to_patch[pod]["containers"][container] = {"requests": {}}

                        # Convert resources requests back from Decimal numbers to k8s notation (e.g. 256Mi)
                        if new_requests.get("cpu"):
                            pods_to_patch[pod]["containers"][container]["requests"]["cpu"] = format_quantity(
                                new_requests["cpu"], "m"
                            )
                        if new_requests.get("memory"):
                            pods_to_patch[pod]["containers"][container]["requests"]["memory"] = format_quantity(
                                new_requests["memory"], "Mi"
                            )

        return pods_to_patch

    @staticmethod
    async def _patch_pod(namespace: str, pod_name: str, containers: dict[str, Any]):
        try:
            async with ApiClient() as api:
                v1 = client.CoreV1Api(api)

                pod_patch_body = {
                    "spec": {
                        "containers": [
                            {"name": container_name, "resources": resources}
                            for container_name, resources in containers.items()
                        ]
                    }
                }

                print(pod_patch_body)

                print(f"Patching pod {pod_name} setting containers {containers}")
                await v1.patch_namespaced_pod(
                    pod_name,
                    namespace,
                    pod_patch_body,
                    _content_type="application/json-patch+json",  # (optional, default if patch is a list)
                )
        except Exception as e:
            print(f"Error: {e}")
