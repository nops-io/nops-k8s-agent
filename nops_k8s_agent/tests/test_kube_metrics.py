from unittest.mock import patch

import pytest
from tests.conftest import EXAMPLE_RESPONSE

from nops_k8s_agent.libs.kube_metrics import KubeMetrics


@patch("nops_k8s_agent.libs.kube_metrics.PrometheusConnect.custom_query")
def test_get_kube_metrics(mock_prom_conn):
    mock_prom_conn.return_value = EXAMPLE_RESPONSE
    metrics = KubeMetrics().get_metrics()
    assert metrics


@pytest.mark.slow
def test_get_kube_metrics_real():
    metrics = KubeMetrics().get_metrics()
    assert metrics
