from unittest.mock import patch

from django.core.management import call_command

import responses
from tests.conftest import EXAMPLE_RESPONSE


@responses.activate
def test_send_metadata():
    rsp1 = responses.Response(
        responses.POST,
        "https://app.nops.io:443/svc/event_collector/v1/kube_collector",
        status=200,
    )

    responses.add(rsp1)
    call_command("send_metadata")
    assert rsp1.call_count


@responses.activate
@patch("nops_k8s_agent.libs.kube_metrics.PrometheusConnect.custom_query")
def test_send_metrics_low(mock_prom_conn):
    rsp1 = responses.Response(
        responses.POST,
        "https://app.nops.io:443/svc/event_collector/v1/kube_collector",
        status=200,
    )

    responses.add(rsp1)

    mock_prom_conn.return_value = EXAMPLE_RESPONSE
    call_command("send_metrics", frequency="low")
    assert rsp1.call_count


@responses.activate
@patch("nops_k8s_agent.libs.kube_metrics.PrometheusConnect.custom_query")
def test_send_metrics_medium(mock_prom_conn):
    rsp1 = responses.Response(
        responses.POST,
        "https://app.nops.io:443/svc/event_collector/v1/kube_collector",
        status=200,
    )

    responses.add(rsp1)

    mock_prom_conn.return_value = EXAMPLE_RESPONSE
    call_command("send_metrics", frequency="medium")
    assert rsp1.call_count


@responses.activate
@patch("nops_k8s_agent.libs.kube_metrics.PrometheusConnect.custom_query")
def test_send_metrics_high(mock_prom_conn):
    rsp1 = responses.Response(
        responses.POST,
        "https://app.nops.io:443/svc/event_collector/v1/kube_collector",
        status=200,
    )
    responses.add(rsp1)

    mock_prom_conn.return_value = EXAMPLE_RESPONSE
    call_command("send_metrics", frequency="high")
    assert rsp1.call_count


@responses.activate
def test_send_healthcheck():
    rsp1 = responses.Response(
        responses.POST,
        "https://app.nops.io:443/svc/event_collector/v1/kube_collector",
        status=200,
    )

    responses.add(rsp1)
    call_command("send_healthcheck")
    assert rsp1.call_count
