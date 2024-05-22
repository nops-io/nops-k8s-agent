from typing import Any

from kubernetes_asyncio.client import V1LimitRangeItem, V1Deployment, V1PodTemplateSpec

from nops_k8s_agent.rightsizing.models import DeploymentPatch, ContainerPatch
from nops_k8s_agent.rightsizing.pods import get_pod_patches


async def find_deployment_patch(
    deployment: V1Deployment,
    deployment_recommendations: dict[str, Any],
    container_min_max_ranges: V1LimitRangeItem,
    deployment_policy_requests_change_threshold: float,
) -> DeploymentPatch | None:

    deployment_template: V1PodTemplateSpec = deployment.spec.template
    container_patches: list[ContainerPatch] = get_pod_patches(
        deployment_template,
        deployment_recommendations,
        container_min_max_ranges,
        deployment_policy_requests_change_threshold,
    )
    if container_patches:
        return DeploymentPatch(
            deployment_name=deployment.metadata.name,
            deployment_namespace=deployment.metadata.namespace,
            containers=container_patches
        )
