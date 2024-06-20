import sys
from unittest.mock import patch

import pytest

from nops_k8s_agent.container_cost.base_prom import BaseProm


@pytest.mark.parametrize("token", [None, "Bearer abc123"])
def test_initialization_with_authorization_token(token):
    expected_headers = {"Authorization": token} if token else {}
    with patch("django.conf.settings.NOPS_K8S_AGENT_PROM_TOKEN", new=token), patch(
        "nops_k8s_agent.container_cost.base_prom.PrometheusConnect"
    ) as mock_prometheus_connect:
        # Initialize BaseProm to trigger the __init__ logic
        BaseProm(cluster_arn="arn:aws:eks:us-west-2:123456789012:cluster/my-cluster")

        # Check if PrometheusConnect was called with the correct arguments
        mock_prometheus_connect.assert_called_once_with(
            url="http://prometheus-server.prometheus-system.svc.cluster.local:80",
            headers=expected_headers,
            disable_ssl=True,
        )


def test_initialization_without_authorization_token():
    with patch("django.conf.settings.NOPS_K8S_AGENT_PROM_TOKEN", new=None), patch(
        "nops_k8s_agent.container_cost.base_prom.PrometheusConnect"
    ) as mock_prometheus_connect:
        BaseProm(cluster_arn="arn:aws:eks:us-west-2:123456789012:cluster/my-cluster")
        mock_prometheus_connect.assert_called_once_with(
            url="http://prometheus-server.prometheus-system.svc.cluster.local:80",
            headers={},
            disable_ssl=True,
        )


@pytest.mark.parametrize("debug_setting", [True, False])
def test_logger_configuration(debug_setting):
    with patch("django.conf.settings.DEBUG", new=debug_setting), patch(
        "nops_k8s_agent.container_cost.base_prom.logger"
    ) as mock_logger:
        BaseProm(cluster_arn="arn:aws:eks:us-west-2:123456789012:cluster/my-cluster")
        if debug_setting:
            mock_logger.remove.assert_not_called()
            mock_logger.add.assert_not_called()
        else:
            mock_logger.remove.assert_called_once()
            mock_logger.add.assert_called_with(sys.stderr, level="WARNING")


def test_prometheus_client_configuration():
    with patch("django.conf.settings.NOPS_K8S_AGENT_PROM_TOKEN", new=None), patch(
        "nops_k8s_agent.container_cost.base_prom.PrometheusConnect"
    ) as mock_prometheus_connect:
        BaseProm(cluster_arn="arn:aws:eks:us-west-2:123456789012:cluster/my-cluster")
        mock_prometheus_connect.assert_called_once_with(
            url="http://prometheus-server.prometheus-system.svc.cluster.local:80",
            headers={},
            disable_ssl=True,
        )
