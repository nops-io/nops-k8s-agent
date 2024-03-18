import json
from datetime import datetime
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import pytz

from nops_k8s_agent.container_cost.node_metadata import NodeMetadata


@pytest.fixture
def node_metadata():
    node_metadata_instance = NodeMetadata(cluster_arn="arn:aws:eks:us-west-2:123456789012:cluster/my-cluster")
    node_metadata_instance.prom_client = MagicMock()
    return node_metadata_instance


@pytest.fixture
def mock_os_makedirs():
    with patch("os.makedirs") as mock:
        yield mock


@pytest.fixture
def mock_pq_write_table():
    with patch("pyarrow.parquet.write_table") as mock:
        yield mock


@pytest.fixture
def mock_datetime_now():
    # Mock datetime class in the context it's used
    with patch("nops_k8s_agent.container_cost.base_labels.datetime") as mock_datetime:
        # Configure the mock to return a specific datetime when now() is called
        mock_now = datetime(2024, 1, 1, 12, 0, tzinfo=pytz.utc)
        mock_datetime.now.return_value = mock_now
        yield mock_datetime


def test_custom_metrics_function_with_varied_data():
    node_metadata = NodeMetadata(cluster_arn="arn:aws:eks:us-west-2:123456789012:cluster/my-cluster")

    varied_data_cases = [
        {
            "metric": {
                "provider_id": "aws://us-west-2/1bb72fc007-d59a588733124b01b54ed242db0b51ad/fargate-ip-10-50-44-142.us-west-2.compute.internal"
            },
            "expected": "fargate-ip-10-50-44-142.us-west-2.compute.internal",
        },
        {"metric": {"provider_id": "aws:///us-west-2/i-024a9b9e9e148ce8d"}, "expected": "i-024a9b9e9e148ce8d"},
        {
            "metric": {
                "provider_id": "fargate:///us-west-2/1bb72fc007-d59a588733124b01b54ed242db0b51ad/fargate-ip-10-50-45-143.us-west-2.compute.internal"
            },
            "expected": "fargate-ip-10-50-45-143.us-west-2.compute.internal",
        },
        {
            "metric": {"node": "node_name"},
            "expected": "",
        },
        {
            "metric": {"pod": "pod_name"},
            "expected": "",
        },
        {
            "metric": {"namespace": "namespace_name"},
            "expected": "",
        },
        {"metric": {"invalid_metric": "node_value"}, "expected": ""},
    ]

    for case in varied_data_cases:
        metric_name = list(case.get("metric", {}).keys())[0]
        actual = node_metadata.custom_metrics_function(case)
        assert (
            actual == case["expected"]
        ), f"custom_metrics_function failed for {case['metric'][metric_name]} - expected {case['expected']}, got {actual}"


def test_convert_to_table_and_save_with_custom_columns(
    node_metadata, mock_os_makedirs, mock_pq_write_table, mock_datetime_now
):
    # Setup custom column and metrics function
    node_metadata = NodeMetadata(cluster_arn="arn:aws:eks:us-west-2:123456789012:cluster/my-cluster")
    node_metadata.CUSTOM_COLUMN = {"custom_metric": []}
    node_metadata.CUSTOM_METRICS_FUNCTION = lambda data: "custom_value"

    POD_VALUE = "pod_value"
    NODE_VALUE = "node_value"
    NODE_VALUE_1 = f"{NODE_VALUE}_1"
    NAMESPACE_VALUE = "namespace_value"
    labels_dict = {
        "metric": {
            "__name__": "kube_pod_labels",
            "custom_label": "label_value",
            "pod": POD_VALUE,
            "node": NODE_VALUE,
            "namespace": NAMESPACE_VALUE,
        },
        "values": [[1609459200.0, "1"]],
    }

    labels_dict_with_none = {
        "metric": {
            "__name__": "kube_pod_labels",
            "custom_label": "label_value",
            "pod": None,
            "node": NODE_VALUE_1,
            "namespace": None,
        },
        "values": [[1609459200.0, "1"]],
    }

    node_metadata.get_all_metrics = MagicMock(return_value={"kube_pod_labels": [labels_dict, labels_dict_with_none]})

    node_metadata.convert_to_table_and_save("last_hour")

    # Verify custom column was handled correctly
    mock_pq_write_table.assert_called_once()
    args, _ = mock_pq_write_table.call_args
    table = args[0]

    assert "labels" in table.column_names
    assert "node" in table.column_names
    assert list(item.as_py() for item in table.column("node")) == [NODE_VALUE, NODE_VALUE_1]
    assert "namespace" in table.column_names
    assert list(item.as_py() for item in table.column("namespace")) == [NAMESPACE_VALUE, None]

    assert "pod" in table.column_names
    assert list(item.as_py() for item in table.column("pod")) == [POD_VALUE, None]

    assert type(table.column("labels")[0].as_py()) == str
    assert "custom_metric" in table.column_names
    assert table.column("custom_metric").to_pylist()[0] == "custom_value"
    assert json.loads(str(table.column("labels")[0])) == labels_dict["metric"]
