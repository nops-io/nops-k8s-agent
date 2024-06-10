"""
OpenCost parquet exporter.

This module exports data from OpenCost API to parquet format, making it suitable
for further analysis or storage in data warehouses.
"""
import logging
import os
import sys
import traceback
from datetime import datetime
from datetime import timedelta

from django.conf import settings

import botocore.exceptions as boto_exceptions
import pandas as pd
import requests

# Set up a custom logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # Adjust the level as needed

# Console handler for standard output
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # Adjust the level as needed
console_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)

# File handler for logging to file
log_path = "/tmp/logfile.log"
file_handler = logging.FileHandler(log_path)
file_handler.setLevel(logging.DEBUG)  # Adjust the level as needed
file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)

logger.addHandler(console_handler)
logger.addHandler(file_handler)


def get_config(hostname=None, port=None, window_start=None, window_end=None, aggregate_by=None, step=None):
    """
    Get configuration for the parquet exporter based on either provided
    parameters or environment variables.
    """
    config = {}

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
    if window_start is None or window_end is None:
        yesterday = datetime.now() - timedelta(1)
        window_start = int(yesterday.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        window_end = int(yesterday.replace(hour=23, minute=59, second=59, microsecond=0).timestamp())
    else:
        if isinstance(window_start, str) or isinstance(window_end, str):
            timestamp_format = "%Y-%m-%dT%H:%M:%SZ"
            window_start_timestamp = datetime.strptime(window_start, timestamp_format)
            window_end_timestamp = datetime.strptime(window_end, timestamp_format)
            window_start = window_start_timestamp.strftime(timestamp_format)
            window_end = window_end_timestamp.strftime(timestamp_format)
        else:
            window_start = int(window_start.timestamp())
            window_end = int(window_end.timestamp())
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
    """
    url, params = config["url"], config["params"]
    try:
        response = requests.get(
            url,
            params=params,
            timeout=(15, None),
        )
        response.raise_for_status()
        if "application/json" in response.headers["content-type"]:
            response_object = response.json()["data"]
            return response_object
        logger.error(f"Invalid content type: {response.headers['content-type']}")
        return None
    except (
        requests.exceptions.RequestException,
        requests.exceptions.Timeout,
        requests.exceptions.TooManyRedirects,
        ValueError,
        KeyError,
    ) as err:
        logger.error(f"Request error: {err}")
        return None


def process_result(result, config):
    """
    Process raw results from the OpenCost API data request.
    """
    for split in result:
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
        logger.error(f"No data: {err}")
        return None
    except pd.errors.ParserError as err:
        logger.error(f"Error parsing data: {err}")
        return None
    except pd.errors.MergeError as err:
        logger.error(f"Data merge error: {err}")
        return None
    except ValueError as err:
        logger.error(f"Value error: {err}")
        return None
    except KeyError as err:
        error_message = str(err)
        logger.error(f"Key error: {err}")
        logger.debug(traceback.format_exc())
        if "Only a column name can be used for the key in a dtype mappings argument." in error_message:
            logger.info("No data available for nops-cost on specified range.")
            return None
        raise err
    return processed_data


def main_command(window_start=None, window_end=None):
    """
    Main function to execute the workflow of fetching, processing, and saving data
    for yesterday.
    """
    config = get_config(window_start=window_start, window_end=window_end)
    logger.debug("Configuration: %s", config)
    logger.info("Retrieving data from nops-cost API")
    result = request_data(config)
    if result:
        logger.info("nOpsCost data retrieved successfully")
        logger.info("Processing the data")
        processed_data = process_result(result, config)
        return processed_data
