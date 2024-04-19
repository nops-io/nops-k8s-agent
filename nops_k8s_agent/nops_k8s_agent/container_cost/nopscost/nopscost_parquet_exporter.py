"""OpenCost parquet exporter.

This module exports data from OpenCost API to parquet format, making it suitable
for further analysis or storage in data warehouses.
"""
import os
import sys
from datetime import datetime
from datetime import timedelta

from django.conf import settings

import botocore.exceptions as boto_exceptions
import pandas as pd
import requests


def get_config(
    hostname=None,
    port=None,
    window_start=None,
    window_end=None,
    aggregate_by=None,
    step=None,
):
    """
    Get configuration for the parquet exporter based on either provided
    parameters or environment variables.

    Parameters:
    - hostname (str): Hostname for the OpenCost service,
                      defaults to the 'NOPSCOST_SVC_HOSTNAME' environment variable,
                      or 'localhost' if the environment variable is not set.
    - port (int): Port number for the OpenCost service,
                  defaults to the 'NOPSCOST_SVC_PORT' environment variable,
                  or 9003 if the environment variable is not set.
    - window_start (str): Start datetime window for fetching data, in ISO format,
                          defaults to yesterday's date at 00:00:00 if not set.
    - window_end (str): End datetime window for fetching data, in ISO format,
                        defaults to yesterday's date at 23:59:59 if not set.
    - aggregate_by (str): Criteria for aggregating data, separated by commas,
                          defaults to the 'NOPSCOST_AGGREGATE' environment variable,
                          or 'cluster,namespace,deployment,statefulset,job,controller,controllerKind,pod,container' if not set.
    - step (str): Granularity for the data aggregation,
                  defaults to the 'NOPSCOST_STEP' environment variable,
                  or '1h' if not set.

    Returns:
    - dict: Configuration dictionary with keys for 'url', 'params',
         'data_types', 'ignored_alloc_keys', and 'rename_columns_config'.
    """
    config = {}

    # If function was called passing parameters the default value is ignored and environment
    # variable is also ignored.
    # This is done, so passing parameters have precedence to environment variables.
    if hostname is None:
        hostname = os.environ.get("NOPSCOST_SVC_HOSTNAME", "nops-cost.nops-cost.svc.cluster.local")
    if port is None:
        port = int(os.environ.get("NOPSCOST_SVC_PORT", 9003))
    if aggregate_by is None:
        aggregate_by = os.environ.get(
            "NOPSCOST_AGGREGATE",
            "cluster,namespace,deployment,statefulset,job,controller,controllerKind,pod,container",
        )
    if step is None:
        step = os.environ.get("NOPSCOST_STEP", "1h")

    config["url"] = f"http://{hostname}:{port}/allocation/compute"
    # If window is not specified assume we want yesterday data.
    if window_start is None or window_end is None:
        yesterday = datetime.now() - timedelta(1)
        window_start = int(yesterday.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        window_end = int(yesterday.replace(hour=23, minute=59, second=59, microsecond=0).timestamp())
    window = f"{window_start},{window_end}"
    config["aggregate_by"] = aggregate_by
    config["params"] = (
        ("window", window),
        ("aggregate", aggregate_by),
        ("includeIdle", "true"),
        ("idleByNode", "false"),
        ("includeProportionalAssetResourceCosts", "false"),
        ("format", "json"),
        ("step", step),
    )
    # This is required to ensure consistency without this
    # we could have type change from int to float over time
    # And this will result in an HIVE PARTITION SCHEMA MISMATCH
    config["data_types"] = {
        "cpuCoreHours": "float",
        "cpuCoreRequestAverage": "float",
        "cpuCoreUsageAverage": "float",
        "cpuCores": "float",
        "cpuCost": "float",
        "cpuCostAdjustment": "float",
        "cpuEfficiency": "float",
        "externalCost": "float",
        "gpuCost": "float",
        "gpuCostAdjustment": "float",
        "gpuCount": "float",
        "gpuHours": "float",
        "loadBalancerCost": "float",
        "loadBalancerCostAdjustment": "float",
        "networkCost": "float",
        "networkCostAdjustment": "float",
        "networkCrossRegionCost": "float",
        "networkCrossZoneCost": "float",
        "networkInternetCost": "float",
        "networkReceiveBytes": "float",
        "networkTransferBytes": "float",
        "pvByteHours": "float",
        "pvBytes": "float",
        "pvCost": "float",
        "pvCostAdjustment": "float",
        "ramByteHours": "float",
        "ramByteRequestAverage": "float",
        "ramByteUsageAverage": "float",
        "ramBytes": "float",
        "ramCost": "float",
        "ramCostAdjustment": "float",
        "ramEfficiency": "float",
        "running_minutes": "float",
        "sharedCost": "float",
        "totalCost": "float",
        "totalEfficiency": "float",
    }
    config["ignored_alloc_keys"] = ["pvs", "lbAllocations"]
    config["rename_columns_config"] = {
        "start": "running_start_time",
        "end": "running_end_time",
        "minutes": "running_minutes",
        "properties.labels.node_type": "label.node_type",
        "properties.labels.product": "label.product",
        "properties.labels.project": "label.project",
        "properties.labels.role": "label.role",
        "properties.labels.team": "label.team",
        "properties.namespaceLabels.product": "namespaceLabels.product",
        "properties.namespaceLabels.project": "namespaceLabels.project",
        "properties.namespaceLabels.role": "namespaceLabels.role",
        "properties.namespaceLabels.team": "namespaceLabels.team",
    }
    config["window_start"] = window_start
    return config


def request_data(config):
    """
    Request data from the OpenCost service using the provided configuration.

    Parameters:
    - config (dict): Configuration dictionary with necessary URL and parameters for the API request.

    Returns:
    - dict or None: The response from the OpenCost API parsed as a dictionary, or None if an error
                    occurs.
    """
    url, params = config["url"], config["params"]
    try:
        response = requests.get(
            url,
            params=params,
            # 15 seconds connect timeout
            # No read timeout, in case it takes a long
            timeout=(15, None),
        )
        response.raise_for_status()
        if "application/json" in response.headers["content-type"]:
            response_object = response.json()["data"]
            return response_object
        print(f"Invalid content type: {response.headers['content-type']}")
        return None
    except (
        requests.exceptions.RequestException,
        requests.exceptions.Timeout,
        requests.exceptions.TooManyRedirects,
        ValueError,
        KeyError,
    ) as err:
        print(f"Request error: {err}")
        return None


def process_result(result, config):
    """
    Process raw results from the OpenCost API data request.

    Parameters:
    - result (dict): Raw response data from the OpenCost API.
    - config (dict): Configuration dictionary with data types and other processing options.

    Returns:
    - DataFrame or None: Processed data as a Pandas DataFrame, or None if an error occurs.
    """
    for split in result:
        # Remove entry for unmounted pv's .
        # this break the table schema in athena
        split.pop("__unmounted__/__unmounted__/__unmounted__", None)
    for split in result:
        for alloc_name in split.keys():
            for ignored_key in config["ignored_alloc_keys"]:
                split[alloc_name].pop(ignored_key, None)
    try:
        frames = []
        for split in result:
            df = pd.json_normalize(split.values())
            label_columns = [col for col in df.columns if col.startswith("properties.labels.")]
            df["labels"] = df.apply(lambda row: {col.split(".")[-1]: row[col] for col in label_columns}, axis=1)
            df.drop(columns=label_columns, inplace=True)
            if "deployment" in config["aggregate_by"] and "name" in df:
                aggregate_components = config["aggregate_by"].split(",")
                deployment_index = aggregate_components.index("deployment")
                df["deployment"] = df["name"].apply(
                    lambda x: x.split("/")[deployment_index] if x.count("/") >= deployment_index else "__unallocated__"
                )
            if "start" in df.columns:
                df["start"] = pd.to_datetime(df["start"]).apply(lambda x: x.timestamp())
            if "end" in df.columns:
                df["end"] = pd.to_datetime(df["end"]).apply(lambda x: x.timestamp())
            df["cluster_arn"] = settings.NOPS_K8S_AGENT_CLUSTER_ARN
            frames.append(df)
        processed_data = pd.concat(frames)
        processed_data.rename(columns=config["rename_columns_config"], inplace=True)
        processed_data = processed_data.astype(config["data_types"])
    except pd.errors.EmptyDataError as err:
        print(f"No data: {err}")
        return None
    except pd.errors.ParserError as err:
        print(f"Error parsing data: {err}")
        return None
    except pd.errors.MergeError as err:
        print(f"Data merge error: {err}")
        return None
    except ValueError as err:
        print(f"Value error: {err}")
        return None
    except KeyError as err:
        print(f"Key error: {err}")
        import traceback

        traceback_info = traceback.format_exc()
        print(traceback_info)
        return None
    return processed_data


def main_command():
    """
    Main function to execute the workflow of fetching, processing, and saving data
    for yesterday.
    """
    print("Starting run")
    config = get_config()
    print(config)
    print("Retrieving data from nops-cost api")
    result = request_data(config)
    if result:
        print("nOpsCost data retrieved successfully")
        print("Processing the data")
        processed_data = process_result(result, config)
        return processed_data
