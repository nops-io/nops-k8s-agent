from unittest.mock import patch

import pytest
from tests.conftest import EXAMPLE_RESPONSE

from nops_k8s_agent.libs.constants import METRICS_SET
from nops_k8s_agent.libs.kube_metrics import KubeMetrics


@patch("nops_k8s_agent.libs.kube_metrics.PrometheusConnect.custom_query")
def test_get_kube_metrics(mock_prom_conn):
    mock_prom_conn.return_value = EXAMPLE_RESPONSE
    metrics = KubeMetrics().get_metrics()
    assert metrics


@pytest.mark.slow
def test_get_kube_metrics_real():
    frequencies = METRICS_SET.keys()
    for frequency in frequencies:
        metrics = KubeMetrics().get_metrics(frequency)
        assert metrics, frequency


def test_get_kube_status_failed():
    with patch("django.conf.settings.PROMETHEUS_SERVER_ENDPOINT", "http://app.nops.io"):
        status = KubeMetrics().get_status()
        assert status == "Failed"


@patch("nops_k8s_agent.libs.kube_metrics.PrometheusConnect.get_metric_range_data")
def test_get_kube_status_success(mock_prom_conn):
    mock_prom_conn.return_value = EXAMPLE_RESPONSE
    status = KubeMetrics().get_status()
    assert status == "Success"
