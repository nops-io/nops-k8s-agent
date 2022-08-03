from nops_k8s_agent.libs.kube_metrics import KubeMetrics


def test_get_kube_metrics():
    metrics = KubeMetrics().get_metrics()
    assert metrics
