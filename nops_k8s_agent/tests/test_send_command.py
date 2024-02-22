from unittest.mock import patch

from django.core.management import call_command

import responses
from tests.conftest import EXAMPLE_RESPONSE


@responses.activate
@patch("nops_k8s_agent.container_cost.base_prom.PrometheusConnect.custom_query_range")
def test_dumptos3(mock_prom_conn):
    # mock s3.upload_file for test upload
    with patch("nops_k8s_agent.management.commands.dumptos3.boto3.client") as mock_s3:
        mock_s3.return_value.upload_file.return_value = None
        mock_prom_conn.return_value = EXAMPLE_RESPONSE
        call_command("dumptos3")
        assert mock_prom_conn.called
        assert mock_s3.return_value.upload_file.call_count == 8
