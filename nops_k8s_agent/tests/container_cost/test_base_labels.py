import json
from datetime import datetime
from datetime import timedelta
from unittest.mock import MagicMock
from unittest.mock import patch


import pytest
import pytz

from nops_k8s_agent.container_cost.base_labels import BaseLabels


@pytest.fixture
def base_labels():
    base_labels_instance = BaseLabels(cluster_arn="arn:aws:eks:us-west-2:123456789012:cluster/my-cluster")
    base_labels_instance.prom_client = MagicMock()
    return base_labels_instance


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


@patch("nops_k8s_agent.container_cost.base_labels.logger")  # Mock the logger
def test_valid_query(mock_logger, base_labels):
    metric_name = "kube_pod_labels"
    start_time = datetime.now(pytz.utc) - timedelta(hours=1)
    end_time = datetime.now(pytz.utc)
    step = "5m"
    expected_response = [{"metric": {"__name__": metric_name}, "value": [1234567890, "100"]}]

    base_labels.prom_client.custom_query_range.return_value = expected_response

    response = base_labels.get_metrics(start_time, end_time, metric_name, step)

    base_labels.prom_client.custom_query_range.assert_called_once_with(
        f"avg_over_time({metric_name}[{step}])", start_time=start_time, end_time=end_time, step=step
    )
    assert response == expected_response
    mock_logger.error.assert_not_called()


@patch("nops_k8s_agent.container_cost.base_labels.logger")
def test_invalid_query_parameters(mock_logger, base_labels):
    base_labels.prom_client.custom_query_range.side_effect = Exception("Query failed")

    metric_name = "invalid_metric"
    start_time = datetime.now(pytz.utc)
    end_time = datetime.now(pytz.utc) - timedelta(hours=1)  # End time before start time
    step = "invalid"

    response = base_labels.get_metrics(start_time, end_time, metric_name, step)

    assert response is None
    mock_logger.error.assert_called_once()


def test_exception_handling(base_labels):
    base_labels.prom_client.custom_query_range.side_effect = Exception("Network error")

    metric_name = "kube_pod_labels"
    start_time = datetime.now(pytz.utc) - timedelta(hours=1)
    end_time = datetime.now(pytz.utc)
    step = "5m"

    with patch("nops_k8s_agent.container_cost.base_labels.logger") as mock_logger:
        response = base_labels.get_metrics(start_time, end_time, metric_name, step)
        assert response is None
        mock_logger.error.assert_called_once_with("Error in get_metrics: Network error")


def test_get_all_metrics_all_available(base_labels):
    def mock_get_metrics(start_time, end_time, metric_name, step):
        mock_value = 1
        return [{"metric": {"__name__": metric_name}, "values": [[1609459200.0, str(mock_value)]]}]

    with patch.object(base_labels, "get_metrics", side_effect=mock_get_metrics) as mock_get_metrics:
        start_time = datetime.now(pytz.utc) - timedelta(hours=1)
        end_time = datetime.now(pytz.utc)
        step = "5m"

        response = base_labels.get_all_metrics(start_time, end_time, step)
        assert mock_get_metrics.call_count == len(
            BaseLabels.list_of_metrics
        ), "get_metrics should be called for each metric in list_of_metrics"

        for metric_name in BaseLabels.list_of_metrics:
            assert metric_name in response, f"Expected {metric_name} in results"
            assert "values" in response[metric_name][0], "Expected value in results metric"
        for metric in base_labels.list_of_metrics:
            assert metric in response


def test_get_all_metrics_some_missing(base_labels):
    def fake_response(start_time, end_time, metric_name, step):
        if metric_name == "kube_pod_labels":
            return None  # Simulate no data for this metric
        return [{"metric": {"__name__": metric_name}, "value": [1234567890, "100"]}]

    with patch.object(base_labels, "get_metrics", side_effect=fake_response):
        start_time = datetime.now(pytz.utc) - timedelta(hours=1)
        end_time = datetime.now(pytz.utc)
        step = "5m"

        response = base_labels.get_all_metrics(start_time, end_time=end_time, step=step)

        # Check if response correctly handles missing data
        assert "kube_pod_labels" not in response  # No data for this metric
        for metric in base_labels.list_of_metrics:
            if metric != "kube_pod_labels":
                assert metric in response


def test_get_all_metrics_empty_list(base_labels):
    # Modify the list_of_metrics to be empty for this test
    base_labels.list_of_metrics = {}

    start_time = datetime.now(pytz.utc) - timedelta(hours=1)
    end_time = datetime.now(pytz.utc)
    step = "5m"

    with patch.object(base_labels, "get_metrics") as mock_get_metrics:
        response = base_labels.get_all_metrics(start_time, end_time, step)

        # Verify get_metrics was not called due to empty metrics list
        mock_get_metrics.assert_not_called()

        # Ensure the response is an empty dictionary
        assert response == {}


def test_convert_to_table_and_save_last_hour(base_labels, mock_os_makedirs, mock_pq_write_table, mock_datetime_now):
    base_labels.get_all_metrics = MagicMock(
        return_value={"kube_pod_labels": [{"metric": {"pod": "pod1"}, "values": [[1234567890, "100"]]}]}
    )

    base_labels.convert_to_table_and_save("last_hour")

    # Check if the directory creation was attempted
    mock_os_makedirs.assert_called_once()

    # Verify PyArrow's write_table was called with expected arguments
    mock_pq_write_table.assert_called_once()
    args, kwargs = mock_pq_write_table.call_args
    table = args[0]

    # Validate table schema and content
    assert "metric_name" in table.column_names
    assert "start_time" in table.column_names
    assert "values" in table.column_names

    # Check if the period calculation for "last_hour" was correct
    assert table.column("period").to_pylist()[0] == "last_hour"


def test_convert_to_table_for_no_entries(base_labels, mock_os_makedirs, mock_pq_write_table, mock_datetime_now):
    base_labels.get_all_metrics = MagicMock(return_value={})

    base_labels.convert_to_table_and_save("last_hour")

    # Make sure no empty files will be created
    mock_os_makedirs.assert_not_called()
    mock_pq_write_table.assert_not_called()


def test_convert_to_table_and_save_last_day(base_labels, mock_os_makedirs, mock_pq_write_table, mock_datetime_now):
    base_labels.get_all_metrics = MagicMock(
        return_value={"kube_namespace_labels": [{"metric": {"namespace": "default"}, "values": [[1234567890, "200"]]}]}
    )

    base_labels.convert_to_table_and_save("last_day")

    # Check if PyArrow's write_table was called
    mock_pq_write_table.assert_called_once()
    args, kwargs = mock_pq_write_table.call_args
    table = args[0]

    # Validate the 'period' was correctly calculated as "last_day"
    assert table.column("period").to_pylist()[0] == "last_day"


def test_convert_to_table_and_save_with_custom_columns(
    base_labels, mock_os_makedirs, mock_pq_write_table, mock_datetime_now
):
    # Setup custom column and metrics function
    base_labels.CUSTOM_COLUMN = {"custom_metric": []}
    base_labels.CUSTOM_METRICS_FUNCTION = lambda data: "custom_value"

    labels_dict = {"annotation": "annot1"}

    base_labels.get_all_metrics = MagicMock(
        return_value={"kube_pod_annotations": [{"metric": labels_dict, "values": [[1234567890, "300"]]}]}
    )

    base_labels.convert_to_table_and_save("last_hour")

    # Verify custom column was handled correctly
    mock_pq_write_table.assert_called_once()
    args, kwargs = mock_pq_write_table.call_args
    table = args[0]

    assert "labels" in table.column_names
    assert type(table.column("labels")[0].as_py()) == str
    assert json.loads(str(table.column("labels")[0])) == labels_dict
    assert "custom_metric" in table.column_names
    assert table.column("custom_metric").to_pylist()[0] == "custom_value"


def test_convert_to_table_and_save_with_pop_out_columns(
    base_labels, mock_os_makedirs, mock_pq_write_table, mock_datetime_now
):
    # Setup custom column and metrics function
    base_labels.CUSTOM_COLUMN = {"custom_metric": []}
    base_labels.CUSTOM_METRICS_FUNCTION = lambda data: "custom_value"

    labels_dict = {"annotation": "annot1"}

    base_labels.get_all_metrics = MagicMock(
        return_value={
            "kube_pod_annotations": [{"metric": labels_dict, "values": [[1234567890, "300"]]}],
            "kube_pod_info": [
                {
                    "metric": {
                        "pod": "pod_value",
                        "namespace": "namespace_value",
                        "node": "node_value",
                        "some-other": "another",
                    },
                    "values": [[1234567890, "300"]],
                }
            ],
        }
    )
    base_labels.convert_to_table_and_save("last_hour")

    # Verify custom column was handled correctly
    mock_pq_write_table.assert_called_once()
    args, kwargs = mock_pq_write_table.call_args
    table = args[0]

    assert "labels" in table.column_names
    assert "pod" in table.column_names
    assert "namespace" in table.column_names
    assert "node" in table.column_names
    assert "some-other" not in table.column_names
    assert type(table.column("labels")[0].as_py()) == str
    assert json.loads(str(table.column("labels")[0])) == labels_dict
    assert "some-other" in json.loads(str(table.column("labels")[1]))
    assert "custom_metric" in table.column_names
    assert table.column("custom_metric").to_pylist()[0] == "custom_value"
