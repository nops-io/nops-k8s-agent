#!/usr/bin/env python3
# Helm helper script that will patch values.yaml and replace values in it with secure data from SSM.
# Usage: python3 setup_values.py uat|prod|staging values_file_path

import copy
import sys

import boto3
import yaml

if len(sys.argv) == 1:
    print("Usage: python3 setup_values.py uat|prod|staging values_file_path")
    sys.exit(1)

workspace = sys.argv[1]
values_file = sys.argv[2]

with open(values_file) as f:
    values_data = yaml.safe_load(f)
    keys_to_fetch = list(values_data["env_variables"].keys())

filter_value = "/nops/{}/".format(workspace)
client = boto3.client("ssm")
paginator = client.get_paginator("describe_parameters")
call_kwargs = {
    "ParameterFilters": [{"Key": "Name", "Option": "Contains", "Values": [filter_value]}],
    "MaxResults": 50,  # this is the max of results allowed
}

filtered_keys = []
for response in paginator.paginate(**call_kwargs):
    for element in response["Parameters"]:
        if element["Name"].replace(filter_value, "") in keys_to_fetch:
            filtered_keys.append(element)

response = {"env_variables": copy.deepcopy(values_data["env_variables"])}
for key in filtered_keys:
    parameter_response = client.get_parameter(Name=key["Name"])["Parameter"]
    parameter_name = parameter_response["Name"].replace(filter_value, "")
    parameter_value = parameter_response["Value"]
    response["env_variables"][parameter_name] = parameter_value

output = copy.deepcopy(values_data)
output.update(response)


print(yaml.dump(output))
