from decimal import Decimal
from typing import Any, Union

from kubernetes.utils.quantity import parse_quantity
from kubernetes_asyncio.client import V1LimitRangeItem, V1PodTemplateSpec
from kubernetes_asyncio.client import V1Pod

from nops_k8s_agent.rightsizing.containers import get_container_patch
from nops_k8s_agent.rightsizing.models import PodPatch, ContainerPatch


async def find_deployment_pods_to_patch(
    deployment_pods: list[V1Pod],
    deployment_recommendations: dict[str, Any],
    container_min_max_ranges: V1LimitRangeItem,
    deployment_policy_requests_change_threshold: float,
) -> list[PodPatch]:
    pods_to_patch: list[PodPatch] = []

    for pod in deployment_pods:
        container_patches: list[ContainerPatch] = get_pod_patches(
            pod,
            deployment_recommendations,
            container_min_max_ranges,
            deployment_policy_requests_change_threshold,
        )
        if container_patches:
            pods_to_patch.append(
                PodPatch(
                    pod_name=pod.metadata.name,
                    pod_namespace=pod.metadata.namespace,
                    containers=container_patches
                )
            )
    return pods_to_patch


def get_pod_patches(
    pod: Union[V1Pod, V1PodTemplateSpec],
    deployment_recommendations: dict[str, Any],
    container_min_max_ranges: V1LimitRangeItem,
    deployment_policy_requests_change_threshold: float,
) -> list[ContainerPatch]:
    container_patches: list[ContainerPatch] = []

    for container in pod.spec.containers:
        container_requests_recommendations = deployment_recommendations.get(container.name, {}).get("requests", {})
        if not container_requests_recommendations:
            continue

        recommended_cpu_requests = Decimal(container_requests_recommendations.get("cpu", 0))
        recommended_ram_requests = Decimal(container_requests_recommendations.get("memory", 0))

        if not (
                parse_quantity(container_min_max_ranges.max.get("cpu", "999E"))
                > recommended_cpu_requests
                > parse_quantity(container_min_max_ranges.min.get("cpu", "0"))
        ):
            print(
                f"Skipping container because {recommended_cpu_requests=} conflicts with {container_min_max_ranges=}"
            )
            continue
        if not (
                parse_quantity(container_min_max_ranges.max.get("memory", "999E"))
                > recommended_ram_requests
                > parse_quantity(container_min_max_ranges.min.get("memory", "0"))
        ):
            print(
                f"Skipping container because {recommended_ram_requests=} conflicts with {container_min_max_ranges=}"
            )
            continue

        container_patch = get_container_patch(
            container=container,
            recommended_cpu_requests=recommended_cpu_requests,
            recommended_ram_requests=recommended_ram_requests,
            deployment_policy_requests_change_threshold=deployment_policy_requests_change_threshold,
        )
        if container_patch:
            container_patches.append(container_patch)

    return container_patches
