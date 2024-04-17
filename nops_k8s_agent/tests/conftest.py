import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock
import kubernetes_asyncio.client
from kubernetes_asyncio.config import load_incluster_config

EXAMPLE_RESPONSE = [
    {
        "metric": {
            "container": "alertmanager",
            "instance": "172.18.0.2:10250",
            "namespace": "default",
            "node": "k3d-nops-local-server-0",
            "pod": "alertmanager-prometheus-kube-prometheus-alertmanager-0",
        },
        "value": [1659626322.182, "37751113.14285714"],
    },
    {
        "metric": {
            "container": "config-reloader",
            "instance": "172.18.0.2:10250",
            "namespace": "default",
            "node": "k3d-nops-local-server-0",
            "pod": "prometheus-prometheus-kube-prometheus-prometheus-0",
        },
        "value": [1659626322.182, "7550537.142857143"],
    },
    {
        "metric": {
            "container": "config-reloader",
            "instance": "172.18.0.2:10250",
            "namespace": "default",
            "node": "k3d-nops-local-server-0",
            "pod": "alertmanager-prometheus-kube-prometheus-alertmanager-0",
        },
        "value": [1659626322.182, "7204425.142857143"],
    },
    {
        "metric": {
            "container": "coredns",
            "instance": "172.18.0.2:10250",
            "namespace": "kube-system",
            "node": "k3d-nops-local-server-0",
            "pod": "coredns-d76bd69b-rqk2f",
        },
        "value": [1659626322.182, "61477120"],
    },
    {
        "metric": {
            "container": "grafana",
            "instance": "172.18.0.2:10250",
            "namespace": "default",
            "node": "k3d-nops-local-server-0",
            "pod": "prometheus-grafana-59dc6b9db7-64xs5",
        },
        "value": [1659626322.182, "53642581.33333333"],
    },
    {
        "metric": {
            "container": "grafana-sc-dashboard",
            "instance": "172.18.0.2:10250",
            "namespace": "default",
            "node": "k3d-nops-local-server-0",
            "pod": "prometheus-grafana-59dc6b9db7-64xs5",
        },
        "value": [1659626322.182, "84913115.42857143"],
    },
    {
        "metric": {
            "container": "grafana-sc-datasources",
            "instance": "172.18.0.2:10250",
            "namespace": "default",
            "node": "k3d-nops-local-server-0",
            "pod": "prometheus-grafana-59dc6b9db7-64xs5",
        },
        "value": [1659626322.182, "73524114.28571428"],
    },
    {
        "metric": {
            "container": "kafka",
            "instance": "172.18.0.2:10250",
            "namespace": "kafka",
            "node": "k3d-nops-local-server-0",
            "pod": "kafka-0",
        },
        "value": [1659626322.182, "432825380.57142854"],
    },
    {
        "metric": {
            "container": "kafka-ui",
            "instance": "172.18.0.2:10250",
            "namespace": "kafka",
            "node": "k3d-nops-local-server-0",
            "pod": "kafka-ui-5c7bd7cc6b-smh2n",
        },
        "value": [1659626322.182, "901095277.7142857"],
    },
    {
        "metric": {
            "container": "ken-event-collector-api",
            "instance": "172.18.0.2:10250",
            "namespace": "ken-event-collector-api",
            "node": "k3d-nops-local-server-0",
            "pod": "ken-event-collector-api-dc9654489-zpxpd",
        },
        "value": [1659626322.182, "6610944"],
    },
    {
        "metric": {
            "container": "kube-prometheus-stack",
            "instance": "172.18.0.2:10250",
            "namespace": "default",
            "node": "k3d-nops-local-server-0",
            "pod": "prometheus-kube-prometheus-operator-685b44fc8d-6hgmp",
        },
        "value": [1659626322.182, "102173622.85714287"],
    },
    {
        "metric": {
            "container": "kube-state-metrics",
            "instance": "172.18.0.2:10250",
            "namespace": "default",
            "node": "k3d-nops-local-server-0",
            "pod": "prometheus-kube-state-metrics-668449846c-dpnp7",
        },
        "value": [1659626322.182, "49438171.42857143"],
    },
    {
        "metric": {
            "container": "lb-tcp-443",
            "instance": "172.18.0.2:10250",
            "namespace": "kube-system",
            "node": "k3d-nops-local-server-0",
            "pod": "svclb-traefik-858r8",
        },
        "value": [1659626322.182, "307200"],
    },
    {
        "metric": {
            "container": "lb-tcp-80",
            "instance": "172.18.0.2:10250",
            "namespace": "kube-system",
            "node": "k3d-nops-local-server-0",
            "pod": "svclb-traefik-858r8",
        },
        "value": [1659626322.182, "2281472"],
    },
    {
        "metric": {
            "container": "local-path-provisioner",
            "instance": "172.18.0.2:10250",
            "namespace": "kube-system",
            "node": "k3d-nops-local-server-0",
            "pod": "local-path-provisioner-6c79684f77-lmh6z",
        },
        "value": [1659626322.182, "34079890.28571428"],
    },
    {
        "metric": {
            "container": "metrics-server",
            "instance": "172.18.0.2:10250",
            "namespace": "kube-system",
            "node": "k3d-nops-local-server-0",
            "pod": "metrics-server-7cd5fcb6b7-jt69q",
        },
        "value": [1659626322.182, "61061449.14285714"],
    },
    {
        "metric": {
            "container": "node-exporter",
            "instance": "172.18.0.2:10250",
            "namespace": "default",
            "node": "k3d-nops-local-server-0",
            "pod": "prometheus-prometheus-node-exporter-887hf",
        },
        "value": [1659626322.182, "22698642.285714284"],
    },
    {
        "metric": {
            "container": "nops-k8s-agent",
            "instance": "172.18.0.2:10250",
            "namespace": "nops-k8s-agent",
            "node": "k3d-nops-local-server-0",
            "pod": "nops-k8s-agent-55744fbb65-g4szv",
        },
        "value": [1659626322.182, "20563163.42857143"],
    },
    {
        "metric": {
            "container": "nops-k8s-agent",
            "instance": "172.18.0.2:10250",
            "namespace": "nops-k8s-agent",
            "node": "k3d-nops-local-server-0",
            "pod": "nops-k8s-agent-6f959fd5c4-5cz6d",
        },
        "value": [1659626322.182, "50143232"],
    },
    {
        "metric": {
            "container": "prometheus",
            "instance": "172.18.0.2:10250",
            "namespace": "default",
            "node": "k3d-nops-local-server-0",
            "pod": "prometheus-prometheus-kube-prometheus-prometheus-0",
        },
        "value": [1659626322.182, "463852982.8571428"],
    },
    {
        "metric": {
            "container": "traefik",
            "instance": "172.18.0.2:10250",
            "namespace": "kube-system",
            "node": "k3d-nops-local-server-0",
            "pod": "traefik-df4ff85d6-scgw9",
        },
        "value": [1659626322.182, "100242688"],
    },
    {
        "metric": {
            "container": "zookeeper",
            "instance": "172.18.0.2:10250",
            "namespace": "kafka",
            "node": "k3d-nops-local-server-0",
            "pod": "kafka-zookeeper-0",
        },
        "value": [1659626322.182, "169702400"],
    },
]


def pytest_addoption(parser):
    parser.addoption("--runslow", action="store_true", default=False, help="run slow tests")


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption("--runslow"):
        # --runslow given in cli: do not skip slow tests
        return
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)


@pytest_asyncio.fixture(scope="function")
def patch_skip_incluster_config_creation():
    kubernetes_asyncio.config.load_incluster_config = Mock()

    # Yield the mock to be used in the test
    yield


@pytest_asyncio.fixture(scope="function")
def patch_k8s_core_api():
    async def list_namespaced_pod_side_effect(namespace: str, label_selector: str):
        items = []
        if namespace == "opencost" and label_selector=="app.kubernetes.io/instance=opencost":
            # Setup the return values of the mock methods and attributes
            mock_metadata = Mock()
            mock_metadata.configure_mock(name="opencost-1234", namespace="opencost")
            containers = []

            for i in range(1):
                mock_container = Mock()
                mock_container.configure_mock(name="opencost")
                mock_container.configure_mock(resources=Mock(requests={"cpu": "200m"}))
                containers.append(mock_container)

            mock_item = Mock()
            mock_item.configure_mock(metadata=mock_metadata)
            mock_item.configure_mock(spec=Mock(containers=containers))
            items.append(mock_item)

        return Mock(items=items)

    # Store the original CoreV1Api to restore it later
    original_core_v1_api = kubernetes_asyncio.client.CoreV1Api

    # Create the mock objects
    mock_api = Mock()

    mock_list_namespaced_pod = AsyncMock()
    mock_list_namespaced_pod.side_effect = list_namespaced_pod_side_effect
    mock_api.list_namespaced_pod = mock_list_namespaced_pod

    mock_list_namespace = AsyncMock()
    mock_metadata = Mock()
    mock_metadata.configure_mock(name="opencost")
    mock_list_namespace.return_value = Mock(items=[Mock(metadata=mock_metadata)])
    mock_api.list_namespace = mock_list_namespace

    mock_patch_namespaced_pod = AsyncMock()
    mock_api.patch_namespaced_pod = mock_patch_namespaced_pod

    # Replace the CoreV1Api with the mock
    kubernetes_asyncio.client.CoreV1Api = Mock(return_value=mock_api)

    # Yield the mock to be used in the test
    yield mock_api

    # Clean up: Restore the original CoreV1Api
    kubernetes_asyncio.client.CoreV1Api = original_core_v1_api


@pytest_asyncio.fixture(scope="function")
def patch_k8s_list_namespaced_deployment():
    async def list_namespaced_deployment_side_effect(namespace: str, watch: bool = False):
        items = []
        if namespace == "opencost":
            # Setup the return values of the mock methods and attributes
            mock_metadata = Mock()
            mock_metadata.configure_mock(name="opencost", namespace="opencost")
            mock_selector = Mock()
            mock_selector.configure_mock(match_labels={"app.kubernetes.io/instance": "opencost"})
            mock_items = Mock()
            mock_items.configure_mock(metadata=mock_metadata)
            mock_items.configure_mock(spec=Mock(selector=mock_selector))
            items.append(mock_items)

        return Mock(items=items)

    # Store the original AppsV1Api to restore it later
    original_apps_v1_api = kubernetes_asyncio.client.AppsV1Api

    # Create the mock objects
    mock_api = Mock()

    mock_list_namespaced_deployment = AsyncMock()
    mock_list_namespaced_deployment.side_effect = list_namespaced_deployment_side_effect
    mock_api.list_namespaced_deployment = mock_list_namespaced_deployment

    # Replace the AppsV1Api with the mock
    kubernetes_asyncio.client.AppsV1Api = Mock(return_value=mock_api)

    # Yield the mock to be used in the test
    yield mock_api

    # Clean up: Restore the original AppsV1Api
    kubernetes_asyncio.client.AppsV1Api = original_apps_v1_api
