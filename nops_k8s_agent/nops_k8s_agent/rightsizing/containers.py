from decimal import Decimal

from kubernetes.utils.quantity import parse_quantity
from kubernetes_asyncio.client import V1Container

from nops_k8s_agent.rightsizing.utils import percentages_difference_threshold_met
from nops_k8s_agent.rightsizing.utils import format_quantity
from nops_k8s_agent.rightsizing.models import ContainerPatch


def get_container_patch(
    container: V1Container,
    recommended_cpu_requests: Decimal,
    recommended_ram_requests: Decimal,
    deployment_policy_requests_change_threshold: float,
) -> ContainerPatch | None:
    new_requests = {}

    actual_cpu_requests = container.resources.requests.get("cpu")
    actual_ram_requests = container.resources.requests.get("memory")

    # Set new CPU requests if they were not set OR current request is lower than recommended
    if recommended_cpu_requests and not actual_cpu_requests:
        new_requests["cpu"] = recommended_cpu_requests
    elif recommended_cpu_requests and percentages_difference_threshold_met(
        parse_quantity(actual_cpu_requests),
        recommended_cpu_requests,
        deployment_policy_requests_change_threshold,
    ):
        new_requests["cpu"] = recommended_cpu_requests

    # Set new Memory requests if they were not set OR current request is lower than recommended
    if recommended_ram_requests and not actual_ram_requests:
        new_requests["memory"] = recommended_ram_requests

    elif recommended_ram_requests and percentages_difference_threshold_met(
        parse_quantity(actual_ram_requests),
        recommended_ram_requests,
        deployment_policy_requests_change_threshold,
    ):
        new_requests["memory"] = recommended_ram_requests

    if new_requests:
        container_patch = ContainerPatch(container_name=container.name, requests={})

        # Convert resources requests back from Decimal numbers to k8s notation (e.g. 256Mi)
        if new_requests.get("cpu"):
            container_patch.requests["cpu"] = format_quantity(new_requests["cpu"], "m")
        if new_requests.get("memory"):
            container_patch.requests["memory"] = format_quantity(new_requests["memory"], "Mi")

        return container_patch
