import pytest
import pytest_asyncio

import nops_k8s_agent.management.commands.rightsize
from nops_k8s_agent.management.commands.rightsize import Command
from nops_k8s_agent.rightsizing import Container


@pytest_asyncio.fixture(scope="module", autouse=True)
def container():
    container = Container()
    container.init_resources()
    container.wire(modules=[nops_k8s_agent.management.commands.rightsize])
    return container


@pytest.mark.asyncio
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
