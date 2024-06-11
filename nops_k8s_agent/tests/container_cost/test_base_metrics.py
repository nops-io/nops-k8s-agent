import os
from datetime import datetime
from datetime import timedelta
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from nops_k8s_agent.container_cost.base_labels import BaseLabels


@pytest.fixture
def base_labels_instance():
    with patch("nops_k8s_agent.container_cost.base_prom.BaseProm", MagicMock()):
        yield BaseLabels(cluster_arn="arn:aws:eks:us-west-2:123456789012:cluster/my-cluster")


def test_get_metrics_success(base_labels_instance):
    metric_name = "kube_pod_labels"
    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow()
    step = "5m"
    mock_response = [{"metric": {"__name__": metric_name}, "values": [[1609459200.0, "1"]]}]

    with patch.object(
        base_labels_instance.prom_client, "custom_query_range", return_value=mock_response
    ) as mock_method:
        query = base_labels_instance.build_query(metric_name, step)
        response = base_labels_instance.get_metrics(
            query=query, start_time=start_time, end_time=end_time, metric_name=metric_name, step=step
        )

        mock_method.assert_called_once_with(
            f"avg_over_time({metric_name}[{step}])", start_time=start_time, end_time=end_time, step=step
        )

        assert response == mock_response


def test_get_metrics_exception(base_labels_instance):
    metric_name = "kube_pod_labels"
    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow()
    step = "5m"

    with patch.object(
        base_labels_instance.prom_client, "custom_query_range", side_effect=Exception("Test exception")
    ) as mock_method:
        query = base_labels_instance.build_query(metric_name, step)
        response = base_labels_instance.get_metrics(
            query=query, start_time=start_time, end_time=end_time, metric_name=metric_name, step=step
        )

        mock_method.assert_called_once_with(
            f"avg_over_time({metric_name}[{step}])", start_time=start_time, end_time=end_time, step=step
        )

        assert response is None


def test_get_all_metrics_success(base_labels_instance):
    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow()
    step = "5m"

    def mock_get_metrics(query, start_time, end_time, metric_name, step):
        # Generate a mock response for any metric name
        mock_value = 1
        return [{"metric": {"__name__": metric_name}, "values": [[1609459200.0, str(mock_value)]]}]

    with patch.object(base_labels_instance, "get_metrics", side_effect=mock_get_metrics) as mock_method:
        result = base_labels_instance.get_all_metrics(start_time=start_time, end_time=end_time, step=step)

        assert mock_method.call_count == len(
            BaseLabels.list_of_metrics
        ), "get_metrics should be called for each metric in list_of_metrics"

        for metric_name in BaseLabels.list_of_metrics:
            assert metric_name in result, f"Expected {metric_name} in results"
            assert "values" in result[metric_name][0], "Expected value in results metric"


def test_get_all_metrics_partial_data(base_labels_instance):
    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow()
    step = "5m"

    # Correctly simulate partial data: use actual metric names and simulate data for some
    partial_response = {
        "kube_pod_labels": [{"metric": {"__name__": "kube_pod_labels"}, "value": [1609459200.0, "1"]}],
        # Other metrics not listed here will simulate a None return value (no data scenario)
    }

    # Adjust mock_get_metrics to return data for metrics in partial_response, None otherwise
    def mock_get_metrics(query, start_time, end_time, metric_name, step):
        return partial_response.get(metric_name, None)  # Return None for metrics not in partial_response

    with patch.object(base_labels_instance, "get_metrics", side_effect=mock_get_metrics):
        result = base_labels_instance.get_all_metrics(start_time=start_time, end_time=end_time, step=step)

        # Ensure get_metrics is called for each metric name
        assert len(result) == len(
            partial_response
        ), "Result should only contain metrics for which we provided partial data"

        for metric_name, expected_data in partial_response.items():
            assert metric_name in result, f"Expected {metric_name} to be in the result"
            assert result[metric_name] == expected_data, f"Data for {metric_name} did not match expected partial data"

        for metric_name in set(BaseLabels.list_of_metrics.keys()) - set(partial_response.keys()):
            assert (
                metric_name not in result or result[metric_name] == []
            ), f"Expected no data (or empty list) for {metric_name} not in partial response"


def test_get_all_metrics_no_data(base_labels_instance):
    start_time = datetime.utcnow() - timedelta(hours=1)
    end_time = datetime.utcnow()
    step = "5m"
    with patch.object(base_labels_instance, "get_metrics", return_value=None) as mock_method:
        result = base_labels_instance.get_all_metrics(start_time=start_time, end_time=end_time, step=step)
        assert mock_method.call_count == len(BaseLabels.list_of_metrics), "get_metrics should be called for each metric"
        assert all(value == [] for value in result.values()), "Expected no data for all metrics"


def test_handling_custom_columns_and_metrics(base_labels_instance):
    # Setup custom column and metric function
    base_labels_instance.CUSTOM_COLUMN = {"custom_column": ["custom_column_1"]}
    base_labels_instance.CUSTOM_METRICS_FUNCTION = MagicMock(return_value="custom_metric_value")

    # Mock datetime and os.makedirs, pq.write_table
    with patch("nops_k8s_agent.container_cost.base_labels.datetime") as mock_datetime, patch(
        "nops_k8s_agent.container_cost.base_labels.os.makedirs"
    ), patch("nops_k8s_agent.container_cost.base_labels.pq.write_table") as mock_write_table:

        mock_datetime.now.return_value = datetime(2023, 1, 1, 12, 0)
        mock_datetime.utcnow.return_value = datetime(2023, 1, 1, 12, 0)

        # Mock get_all_metrics to return sample data
        base_labels_instance.get_all_metrics = MagicMock(
            return_value={
                "kube_pod_labels": [
                    {
                        "metric": {"__name__": "kube_pod_labels", "custom_label": "label_value"},
                        "values": [[1609459200.0, "1"]],
                    }
                ]
            }
        )

        # Perform the test
        base_labels_instance.convert_to_table_and_save(period="last_hour", filename="test_custom.parquet")

        # Assert CUSTOM_METRICS_FUNCTION was called and custom column added to table
        base_labels_instance.CUSTOM_METRICS_FUNCTION.assert_called()
        args, _ = mock_write_table.call_args
        table = args[0]
        assert "labels" in table.column_names
        assert "custom_column" in table.column_names, "Custom column should be in the table"

        assert table.column("custom_column").length() > 0


def test_parquet_file_writing_and_directory_handling_non_empty_files(base_labels_instance):
    test_filename = "test_output/test_parquet_file.parquet"
    # Mock datetime, os.makedirs, and pq.write_table
    with patch("nops_k8s_agent.container_cost.base_labels.datetime") as mock_datetime, patch(
        "nops_k8s_agent.container_cost.base_labels.os.makedirs"
    ) as mock_makedirs, patch("nops_k8s_agent.container_cost.base_labels.pq.write_table") as mock_write_table:

        mock_datetime.now.return_value = datetime(2023, 1, 1)
        mock_datetime.utcnow.return_value = datetime(2023, 1, 1)

        # Mock get_all_metrics to return sample data with varying labels
        base_labels_instance.get_all_metrics = MagicMock(
            return_value={
                "kube_pod_labels": [
                    {"metric": {"__name__": "kube_pod_labels", "label1": "value1"}, "values": [[1609459200.0, "1"]]},
                    {"metric": {"__name__": "kube_pod_labels", "label2": "value2"}, "values": [[1609459200.0, "2"]]},
                ]
            }
        )

        # Perform the test
        base_labels_instance.convert_to_table_and_save(period="last_hour", filename=test_filename)

        # Verify dynamic labels are correctly handled
        args, _ = mock_write_table.call_args
        table = args[0]
        assert "labels" in table.column_names

        mock_makedirs.assert_called_with(os.path.dirname(test_filename), exist_ok=True)
        mock_write_table.assert_called_once()
        args, _ = mock_write_table.call_args
        assert args[1] == test_filename, "Parquet file should be written to the correct path"


def test_parquet_file_writing_and_directory_handling_empty_files(base_labels_instance):
    test_filename = "test_output/test_parquet_file.parquet"

    # Mock datetime, os.makedirs, and pq.write_table
    with patch("nops_k8s_agent.container_cost.base_labels.datetime") as mock_datetime, patch(
        "nops_k8s_agent.container_cost.base_labels.os.makedirs"
    ) as mock_makedirs, patch("nops_k8s_agent.container_cost.base_labels.pq.write_table") as mock_write_table:

        mock_datetime.now.return_value = datetime(2023, 1, 1)
        mock_datetime.utcnow.return_value = datetime(2023, 1, 1)

        # Mock get_all_metrics to return empty data (focus on file writing)
        base_labels_instance.get_all_metrics = MagicMock(return_value={})

        # Perform the test
        base_labels_instance.convert_to_table_and_save(period="last_hour", filename=test_filename)

        # Verify that empty files are not created
        mock_makedirs.assert_not_called()
        mock_write_table.assert_not_called()
