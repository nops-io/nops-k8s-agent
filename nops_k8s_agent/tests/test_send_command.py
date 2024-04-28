from unittest.mock import MagicMock
from unittest.mock import patch

from django.core.management import call_command

import responses
from tests.conftest import EXAMPLE_RESPONSE


@responses.activate
@patch("nops_k8s_agent.container_cost.base_prom.PrometheusConnect.custom_query_range")
@patch("nops_k8s_agent.container_cost.nopscost.nopscost_parquet_exporter.main_command")
def test_dumptos3(main_mock, mock_prom_conn):
    # mock s3.upload_file for test upload
    with patch("nops_k8s_agent.management.commands.dumptos3.boto3.client") as mock_s3:
        mock_s3.return_value.upload_file.return_value = None
        mock_prom_conn.return_value = EXAMPLE_RESPONSE
        mock_df = MagicMock()
        mock_df.to_parquet = MagicMock()  # Add the .to_parquet() method to the mock
        main_mock.return_value = None

        call_command("dumptos3")
        assert mock_prom_conn.called
        assert mock_s3.return_value.upload_file.call_count == 9
