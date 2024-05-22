from unittest.mock import AsyncMock
from unittest.mock import patch

import pytest
import pytest_asyncio
from kubernetes_asyncio.client import V1LimitRangeItem

import nops_k8s_agent.management.commands.rightsize
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
    patch_k8s_apps_api,
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
    patch_k8s_apps_api.patch_namespaced_deployment.assert_called_once_with(
        **{
            "name": "opencost",
            "namespace": "opencost",
            "body": {
                "spec": {
                    "template": {
                        "spec": {
                            "containers": [
                                {"name": "opencost", "resources": {"requests": {"cpu": "320m", "memory": "70Mi"}}}
                            ]
                        }
                    }
                }
            },
        },
        _content_type="application/json-patch+json",
    )
