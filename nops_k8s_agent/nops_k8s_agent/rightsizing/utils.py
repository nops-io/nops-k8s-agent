from decimal import Decimal

from kubernetes.utils.quantity import parse_quantity
from kubernetes_asyncio.client import V1Container

from nops_k8s_agent.rightsizing.models import ContainerPatch

_EXPONENTS = {
    "n": -3,
    "u": -2,
    "m": -1,
    "K": 1,
    "k": 1,
    "M": 2,
    "G": 3,
    "T": 4,
    "P": 5,
    "E": 6,
}


# Waits for https://github.com/kubernetes-client/python/issues/2205 to be merged
def format_quantity(quantity_value, suffix, quantize=Decimal("1")) -> str:
    """
    Takes a decimal and produces a string value in kubernetes' canonical quantity form,
    like "200Mi".Users can specify an additional decimal number to quantize the output.
    Example -  Relatively increase pod memory limits:
    # retrieve my_pod
    current_memory: Decimal = parse_quantity(my_pod.spec.containers[0].resources.limits.memory)
    desired_memory = current_memory * 1.2
    desired_memory_str = format_quantity(desired_memory, suffix="Gi", quantize=Decimal(1))
    # patch pod with desired_memory_str
    'quantize=Decimal(1)' ensures that the result does not contain any fractional digits.
    Supported SI suffixes:
    base1024: Ki | Mi | Gi | Ti | Pi | Ei
    base1000: n | u | m | "" | k | M | G | T | P | E
    See https://github.com/kubernetes/apimachinery/blob/master/pkg/api/resource/quantity.go
    Input:
    quantity: Decimal.  Quantity as a number which is supposed to converted to a string
                        with SI suffix.
    suffix: string.     The desired suffix/unit-of-measure of the output string
    quantize: Decimal.  Can be used to round/quantize the value before the string
                        is returned. Defaults to None.
    Returns:
    string. Canonical Kubernetes quantity string containing the SI suffix.
    Raises:
    ValueError if the SI suffix is not supported.
    """

    if not suffix:
        return str(quantity_value)

    if isinstance(quantity_value, float) or isinstance(quantity_value, int):
        quantity_value = Decimal(quantity_value)

    if suffix.endswith("i"):
        base = 1024
    elif len(suffix) == 1:
        base = 1000
    else:
        raise ValueError(f"{quantity_value} has unknown suffix")

    if suffix == "ki":
        raise ValueError(f"{quantity_value} has unknown suffix")

    if suffix[0] not in _EXPONENTS:
        raise ValueError(f"{quantity_value} has unknown suffix")

    different_scale = quantity_value / Decimal(base ** _EXPONENTS[suffix[0]])
    if quantize:
        different_scale = different_scale.quantize(quantize)
    return str(different_scale) + suffix


def percentages_difference_threshold_met(old_value: Decimal, new_value: Decimal, threshold_percent: float) -> bool:
    larger_value = max(abs(old_value), abs(new_value))
    return (abs(old_value - new_value) / larger_value) >= threshold_percent


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
