import os
from datetime import datetime
from datetime import timedelta
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import requests

from nops_k8s_agent.container_cost.nopscost.nopscost_parquet_exporter import get_config
from nops_k8s_agent.container_cost.nopscost.nopscost_parquet_exporter import main_command
from nops_k8s_agent.container_cost.nopscost.nopscost_parquet_exporter import process_result
from nops_k8s_agent.container_cost.nopscost.nopscost_parquet_exporter import request_data


@pytest.fixture
def mock_config():
    return get_config()


# Valid result set to be used for mocking responses from the OpenCost API
@pytest.fixture
def valid_result():
    return [
        {
            "kube-system/__unallocated__/aws-node-48cn9/aws-eks-nodeagent": {
                "name": "kube-system/__unallocated__/aws-node-48cn9/aws-eks-nodeagent",
                "properties": {
                    "cluster": "default-cluster",
                    "node": "ip-172-31-28-200.us-west-2.compute.internal",
                    "container": "aws-eks-nodeagent",
                    "controller": "aws-node",
                    "controllerKind": "daemonset",
                    "namespace": "kube-system",
                    "pod": "aws-node-48cn9",
                    "providerID": "i-0863bf81a09cd437f",
                    "labels": {
                        "app_kubernetes_io_instance": "aws-vpc-cni",
                        "app_kubernetes_io_name": "aws-node",
                        "controller_revision_hash": "749d66ddf5",
                        "eks_amazonaws_com_nodegroup": "nopsqak8sagent-nodegroup",
                        "k8s_app": "aws-node",
                        "kubernetes_io_metadata_name": "kube-system",
                        "node_kubernetes_io_instance_type": "t3.medium",
                        "pod_template_generation": "2",
                        "topology_kubernetes_io_region": "us-west-2",
                        "topology_kubernetes_io_zone": "us-west-2b",
                    },
                    "namespaceLabels": {"kubernetes_io_metadata_name": "kube-system"},
                },
                "window": {"start": "2024-03-19T00:00:00Z", "end": "2024-03-19T01:00:00Z"},
                "start": "2024-03-19T00:00:00Z",
                "end": "2024-03-19T01:00:00Z",
                "minutes": 60,
                "cpuCores": 0.025,
                "cpuCoreRequestAverage": 0.025,
                "cpuCoreUsageAverage": 0.00037,
                "cpuCoreHours": 0.025,
                "cpuCost": 0.00042,
                "cpuCostAdjustment": 0,
                "cpuEfficiency": 0.01496,
                "gpuCount": 0,
                "gpuHours": 0,
                "gpuCost": 0,
                "gpuCostAdjustment": 0,
                "networkTransferBytes": 33787026.3929,
                "networkReceiveBytes": 34080885.709,
                "networkCost": 0,
                "networkCrossZoneCost": 0,
                "networkCrossRegionCost": 0,
                "networkInternetCost": 0,
                "networkCostAdjustment": 0,
                "loadBalancerCost": 0,
                "loadBalancerCostAdjustment": 0,
                "pvBytes": 0,
                "pvByteHours": 0,
                "pvCost": 0,
                "pvs": None,
                "pvCostAdjustment": 0,
                "ramBytes": 10906112,
                "ramByteRequestAverage": 0,
                "ramByteUsageAverage": 16157309.90164,
                "ramByteHours": 10906112,
                "ramCost": 2e-05,
                "ramCostAdjustment": 0,
                "ramEfficiency": 1,
                "externalCost": 0,
                "sharedCost": 0,
                "totalCost": 0.00044,
                "totalEfficiency": 0.06583,
                "rawAllocationOnly": {"cpuCoreUsageMax": 0.00041877638084207526, "ramByteUsageMax": 16158720},
                "lbAllocations": None,
            }
        }
    ]


@patch.dict(os.environ, {}, clear=True)
def test_get_config_defaults():
    """
    Test get_config uses default values when no arguments or environment variables are set.
    """
    aggregations = "cluster,namespace,deployment,statefulset,job,controller,controllerKind,pod,container"
    yesterday = datetime.now() - timedelta(1)
    expected_window_start = int(yesterday.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
    expected_window_end = int(yesterday.replace(hour=23, minute=59, second=59, microsecond=0).timestamp())

    config = get_config()
    assert config["url"] == "http://nops-cost.nops-cost.svc.cluster.local:9003/allocation/compute"
    assert config["aggregate_by"] == aggregations
    assert config["params"][0][1] == f"{expected_window_start},{expected_window_end}"


@patch.dict(
    os.environ,
    {
        "NOPSCOST_SVC_HOSTNAME": "envhost",
        "NOPSCOST_SVC_PORT": "8000",
        "NOPSCOST_AGGREGATE": "pod,container",
        "NOPSCOST_STEP": "30m",
    },
    clear=True,
)
def test_get_config_from_environment_variables():
    """
    Test that get_config correctly uses values from environment variables.
    """
    config = get_config()
    assert config["url"] == "http://envhost:8000/allocation/compute"
    assert config["aggregate_by"] == "pod,container"
    assert config["params"][6] == ("step", "30m")


@patch.dict(os.environ, {}, clear=True)
def test_get_config_with_arguments():
    """
    Test that get_config correctly prioritizes function arguments over environment variables.
    """
    config = get_config(
        hostname="arghost",
        port=8080,
        window_start="2023-02-01T00:00:00Z",
        window_end="2023-02-01T23:59:59Z",
        aggregate_by="namespace,deployment",
        step="15m",
    )
    assert config["url"] == "http://arghost:8080/allocation/compute"
    assert config["aggregate_by"] == "namespace,deployment"
    assert config["params"][0][1] == "2023-02-01T00:00:00Z,2023-02-01T23:59:59Z"
    assert config["params"][6] == ("step", "15m")


def test_request_data_success():
    """
    Test request_data successfully retrieves and returns data.
    """
    mock_response = {"data": [{"key": "value"}]}
    config = {
        "url": "http://testserver.com/api",
        "params": (
            ("window", "1234567890,1234567899"),
            ("aggregate", "namespace,pod,container"),
            ("includeIdle", "false"),
            ("idleByNode", "false"),
            ("includeProportionalAssetResourceCosts", "false"),
            ("format", "json"),
            ("step", "1h"),
        ),
    }

    with patch("requests.get") as mock_get:
        mock_get.return_value.ok = True
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.headers = {"content-type": "application/json"}

        response = request_data(config)
        assert response == mock_response["data"]
        mock_get.assert_called_once_with(config["url"], params=config["params"], timeout=(15, None))


def test_request_data_failure():
    """
    Test request_data handles HTTP errors correctly.
    """
    config = {
        "url": "http://testserver.com/api",
        "params": (
            ("window", "1234567890,1234567899"),
            # other params
        ),
    }

    with patch("requests.get") as mock_get:
        mock_get.return_value.raise_for_status.side_effect = requests.exceptions.HTTPError

        response = request_data(config)
        assert response is None
        mock_get.assert_called_once()


def test_request_data_invalid_content_type():
    """
    Test request_data handles unexpected content types correctly.
    """
    config = {
        "url": "http://testserver.com/api",
        "params": (
            ("window", "1234567890,1234567899"),
            # other params
        ),
    }

    with patch("requests.get") as mock_get:
        mock_get.return_value.ok = True
        mock_get.return_value.headers = {"content-type": "text/html"}

        response = request_data(config)
        assert response is None
        mock_get.assert_called_once()


def test_request_data_json_decode_error():
    """
    Test request_data handles JSON decode errors correctly.
    """
    config = {
        "url": "http://testserver.com/api",
        "params": (
            ("window", "1234567890,1234567899"),
            # other params
        ),
    }

    with patch("requests.get") as mock_get:
        mock_get.return_value.ok = True
        mock_get.return_value.json.side_effect = ValueError("No JSON object could be decoded")
        mock_get.return_value.headers = {"content-type": "application/json"}

        response = request_data(config)
        assert response is None
        mock_get.assert_called_once()


def test_process_result_with_valid_data(valid_result, mock_config):
    processed_data = process_result(valid_result, mock_config)
    assert not processed_data.empty
    assert processed_data["cpuCoreHours"].dtype == "float"


def test_process_result_with_empty_result(mock_config):
    result = []
    processed_data = process_result(result, mock_config)
    assert processed_data is None, "Expected None for empty result input"


def test_process_result_with_invalid_data_structure(mock_config):
    invalid_result = [{"invalid_key": "invalid_value"}]  # Misstructured input
    with pytest.raises(AttributeError):
        process_result(invalid_result, mock_config)


def test_process_result_ignores_unmounted_volumes(valid_result, mock_config):
    # Add an unmounted volume to the valid result
    valid_result[0]["__unmounted__/__unmounted__/__unmounted__"] = {}
    processed_data = process_result(valid_result, mock_config)
    assert (
        "__unmounted__/__unmounted__/__unmounted__" not in processed_data.columns
    ), "Unmounted volumes should be ignored"


@pytest.fixture
def mock_config_main():
    return {
        "url": "http://fakeurl.com/api",
        "params": {"param1": "value1"},
        "s3_bucket": "mock_bucket",
        "file_key_prefix": "/mock/prefix/",
        # Additional config settings as needed
    }


@pytest.fixture
def mock_api_response():
    # Mock response structure based on your API's format
    return [{"mock_key": "mock_value"}]


@pytest.fixture
def mock_processed_data():
    # Assuming the processed data is a DataFrame, adjust as needed
    return MagicMock(name="DataFrame")


@patch("nops_k8s_agent.container_cost.nopscost.nopscost_parquet_exporter.get_config")
@patch("nops_k8s_agent.container_cost.nopscost.nopscost_parquet_exporter.request_data")
@patch("nops_k8s_agent.container_cost.nopscost.nopscost_parquet_exporter.process_result")
def test_main_command_success(
    mock_process_result, mock_request_data, mock_get_config, mock_config_main, mock_api_response, mock_processed_data
):
    mock_get_config.return_value = mock_config_main
    mock_request_data.return_value = mock_api_response
    mock_process_result.return_value = mock_processed_data

    # Execute the function under test
    result = main_command()

    # Validate that the workflow was executed as expected
    mock_get_config.assert_called_once()
    mock_request_data.assert_called_once_with(mock_config_main)
    mock_process_result.assert_called_once_with(mock_api_response, mock_config_main)
    assert result == mock_processed_data, "Expected main_command to return the processed data"


@patch("nops_k8s_agent.container_cost.nopscost.nopscost_parquet_exporter.get_config")
@patch("nops_k8s_agent.container_cost.nopscost.nopscost_parquet_exporter.request_data")
@patch("nops_k8s_agent.container_cost.nopscost.nopscost_parquet_exporter.process_result")
def test_main_command_api_failure(mock_process_result, mock_request_data, mock_get_config, mock_config_main):
    mock_get_config.return_value = mock_config_main
    mock_request_data.return_value = None  # Simulate an API failure

    # Execute the function under test
    result = main_command()

    # Validate that the workflow was executed as expected, but returned early due to the API failure
    mock_get_config.assert_called_once()
    mock_request_data.assert_called_once_with(mock_config_main)
    mock_process_result.assert_not_called()
    assert result is None, "Expected main_command to return None on API failure"
