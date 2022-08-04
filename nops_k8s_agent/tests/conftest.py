import pytest

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
