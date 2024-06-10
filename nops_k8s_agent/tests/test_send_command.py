import datetime as dt
from unittest.mock import MagicMock
from unittest.mock import patch

from django.core.management import call_command

import pytest
import responses
from tests.conftest import EXAMPLE_RESPONSE


@pytest.mark.skip
@responses.activate
@patch("nops_k8s_agent.container_cost.base_prom.PrometheusConnect.custom_query_range")
@patch("nops_k8s_agent.container_cost.nopscost.nopscost_parquet_exporter.main_command")
def test_dumptos3(main_mock, mock_prom_conn):
    with patch("nops_k8s_agent.management.commands.dumptos3.boto3.client") as mock_s3:
        mock_s3.return_value.upload_file.return_value = None
        mock_prom_conn.return_value = EXAMPLE_RESPONSE
        mock_df = MagicMock()
        mock_df.to_parquet = MagicMock()
        main_mock.return_value = mock_df

        call_command("dumptos3")
        assert mock_prom_conn.called
        assert mock_s3.return_value.upload_file.call_count == 10


@pytest.mark.skip
@responses.activate
@patch("nops_k8s_agent.container_cost.base_prom.PrometheusConnect.custom_query_range")
@patch("nops_k8s_agent.container_cost.nopscost.nopscost_parquet_exporter.main_command")
def test_dumptos3_with_module(main_mock, mock_prom_conn):
    with patch("nops_k8s_agent.management.commands.dumptos3.boto3.client") as mock_s3:
        mock_s3.return_value.upload_file.return_value = None
        mock_prom_conn.return_value = EXAMPLE_RESPONSE
        mock_df = MagicMock()
        mock_df.to_parquet = MagicMock()
        main_mock.return_value = mock_df

        call_command("dumptos3", module_to_collect="node_metrics")
        assert mock_prom_conn.called
        assert mock_s3.return_value.upload_file.call_count == 2


@pytest.mark.skip
@patch("nops_k8s_agent.management.commands.dumptos3.Command._is_nops_cost_exported")
@patch("nops_k8s_agent.management.commands.dumptos3.boto3.client")
def test_nops_cost_already_exported(mock_s3, mock_is_exported_ok):
    mock_is_exported_ok.return_value = True
    mock_s3.return_value.upload_file.return_value = None

    call_command("dumptos3")
    mock_is_exported_ok.assert_called_once()
    assert mock_s3.return_value.upload_file.call_count == 10


@pytest.mark.skip
@patch("nops_k8s_agent.management.commands.dumptos3.boto3.client")
@patch("nops_k8s_agent.container_cost.nopscost.nopscost_parquet_exporter.request_data")
def test_export_happy_case_upload_file_count(mock_requests, mock_s3):
    mock_s3.return_value.upload_file.return_value = None

    call_command("dumptos3")
    assert mock_s3.return_value.upload_file.call_count == 10


@pytest.mark.skip
@patch("nops_k8s_agent.management.commands.dumptos3.Command._is_nops_cost_exported")
@patch("nops_k8s_agent.management.commands.dumptos3.boto3.client")
def test_nops_cost_export_failure_from_list_bucket(mock_boto3_client, mock_is_nops_cost_exported):
    mock_is_nops_cost_exported.side_effect = Exception("S3 error")
    mock_s3 = MagicMock()
    mock_boto3_client.return_value = mock_s3

    with pytest.raises(SystemExit):
        call_command("dumptos3")

    mock_is_nops_cost_exported.assert_called_once()
    assert mock_s3.upload_file.call_count == 10
