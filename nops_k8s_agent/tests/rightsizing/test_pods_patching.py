from unittest.mock import AsyncMock, patch
import pytest
import pytest_asyncio

import nops_k8s_agent.management.commands.rightsize
from kubernetes_asyncio.client import V1LimitRangeItem
from nops_k8s_agent.management.commands.rightsize import Command
from nops_k8s_agent.rightsizing import Container

from nops_k8s_agent.rightsizing.dependency_ingection.services import KubernetesClientService


@pytest_asyncio.fixture(scope="module", autouse=True)
def container():
    container = Container()
    container.init_resources()
    container.wire(modules=[nops_k8s_agent.management.commands.rightsize])
    return container


@pytest.mark.asyncio
@patch.object(
    KubernetesClientService,
    "container_min_max_ranges",
    AsyncMock(
        return_value=V1LimitRangeItem(
            max={"cpu": "999E", "memory": "999E"},
            min={"cpu": "0", "memory": "0"},
            type="Container",
        )
    ),
)
async def test_pods_patching(
    patch_skip_incluster_config_creation,
    patch_k8s_feature_gates,
    patch_k8s_core_api,
    patch_k8s_list_namespaced_deployment,
):
    rightsize_command = Command()
    await rightsize_command.rightsize()

    assert rightsize_command.nops_configs == {"opencost": {"opencost": {"policy": {"threshold_percentage": 0.1}}}}
    patch_k8s_core_api.patch_namespaced_pod.assert_called_once_with(
        **{
            "name": "opencost-1234",
            "namespace": "opencost",
            "body": {
                "spec": {
                    "containers": [{"name": "opencost", "resources": {"requests": {"cpu": "320m", "memory": "70Mi"}}}]
                }
            },
        },
        _content_type="application/json-patch+json",
    )


@pytest.mark.asyncio
@patch.object(
    KubernetesClientService,
    "container_min_max_ranges",
    AsyncMock(
        return_value=V1LimitRangeItem(
            max={"cpu": "50m", "memory": "999E"},
            min={"cpu": "0", "memory": "0"},
            type="Container",
        )
    ),
)
async def test_pods_patching_max_cpu_limit_range_not_satisfied(
    patch_skip_incluster_config_creation,
    patch_k8s_feature_gates,
    patch_k8s_core_api,
    patch_k8s_list_namespaced_deployment,
):
    rightsize_command = Command()
    await rightsize_command.rightsize()

    assert rightsize_command.nops_configs == {"opencost": {"opencost": {"policy": {"threshold_percentage": 0.1}}}}
    assert patch_k8s_core_api.patch_namespaced_pod.call_count == 0


@pytest.mark.asyncio
@patch.object(
    KubernetesClientService,
    "container_min_max_ranges",
    AsyncMock(
        return_value=V1LimitRangeItem(
            max={"cpu": "900m", "memory": "999E"},
            min={"cpu": "500m", "memory": "0"},
            type="Container",
        )
    ),
)
async def test_pods_patching_min_cpu_limit_range_not_satisfied(
    patch_skip_incluster_config_creation,
    patch_k8s_feature_gates,
    patch_k8s_core_api,
    patch_k8s_list_namespaced_deployment,
):
    rightsize_command = Command()
    await rightsize_command.rightsize()

    assert rightsize_command.nops_configs == {"opencost": {"opencost": {"policy": {"threshold_percentage": 0.1}}}}
    assert patch_k8s_core_api.patch_namespaced_pod.call_count == 0


@pytest.mark.asyncio
@patch.object(
    KubernetesClientService,
    "container_min_max_ranges",
    AsyncMock(
        return_value=V1LimitRangeItem(
            max={"cpu": "900m", "memory": "50Mi"},
            min={"cpu": "100m", "memory": "0"},
            type="Container",
        )
    ),
)
async def test_pods_patching_max_memory_limit_range_not_satisfied(
    patch_skip_incluster_config_creation,
    patch_k8s_feature_gates,
    patch_k8s_core_api,
    patch_k8s_list_namespaced_deployment,
):
    rightsize_command = Command()
    await rightsize_command.rightsize()

    assert rightsize_command.nops_configs == {"opencost": {"opencost": {"policy": {"threshold_percentage": 0.1}}}}
    assert patch_k8s_core_api.patch_namespaced_pod.call_count == 0


@pytest.mark.asyncio
@patch.object(
    KubernetesClientService,
    "container_min_max_ranges",
    AsyncMock(
        return_value=V1LimitRangeItem(
            max={"cpu": "900m", "memory": "500Mi"},
            min={"cpu": "100m", "memory": "100Mi"},
            type="Container",
        )
    ),
)
async def test_pods_patching_min_memory_limit_range_not_satisfied(
    patch_skip_incluster_config_creation,
    patch_k8s_feature_gates,
    patch_k8s_core_api,
    patch_k8s_list_namespaced_deployment,
):
    rightsize_command = Command()
    await rightsize_command.rightsize()

    assert rightsize_command.nops_configs == {"opencost": {"opencost": {"policy": {"threshold_percentage": 0.1}}}}
    assert patch_k8s_core_api.patch_namespaced_pod.call_count == 0
