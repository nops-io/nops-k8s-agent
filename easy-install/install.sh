#!/bin/bash

# Exit script on error
set -e

# AWS credentials with write permission to S3 bucket
AWS_ACCESS_KEY_ID="<REPLACE-YourAccessKeyId>"
AWS_SECRET_ACCESS_KEY="<REPLACE-YourSecretAccessKey>"

APP_NOPS_K8S_AGENT_CLUSTER_ARN="<REPLACE-YourClusternARN>"
APP_AWS_S3_BUCKET="<REPLACE-YourS3Bucket>"
APP_AWS_S3_PREFIX="<REPLACE-YourS3Prefix>"

# Ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are replaced
if [[ $AWS_ACCESS_KEY_ID == "<REPLACE-YourAccessKeyId>" || $AWS_SECRET_ACCESS_KEY == "<REPLACE-YourSecretAccessKey>" ]]; then
  echo "AWS credentials must be set before running this script."
  exit 1
fi

if [[ $APP_NOPS_K8S_AGENT_CLUSTER_ARN == "<REPLACE-YourClusternARN>" || $APP_AWS_S3_BUCKET == "<REPLACE-YourS3Bucket>" || $APP_AWS_S3_PREFIX == "<REPLACE-YourS3Prefix>" ]]; then
  echo "Agent environment variables must be set before running this script."
  exit 1
fi


# Create namespace for nops-k8s-agent
kubectl create namespace nops-k8s-agent || { echo "Failed to create namespace nops-k8s-agent"; exit 1; }
# Set kubectl context to use nops-k8s-agent namespace
kubectl config set-context --current --namespace=nops-k8s-agent || { echo "Failed to set kubectl context to nops-k8s-agent namespace"; exit 1; }

# Create secret for AWS access
kubectl create secret generic nops-k8s-agent \
--from-literal=aws_access_key_id=$AWS_ACCESS_KEY_ID \
--from-literal=aws_secret_access_key=$AWS_SECRET_ACCESS_KEY \
--namespace=nops-k8s-agent || { echo "Failed to create secret for AWS access"; exit 1; }

# Installing nops-Prometheus
helm upgrade --install nops-prometheus prometheus-community/prometheus   --namespace nops-prometheus-system --create-namespace   -f ./prometheus.yaml || { echo "Failed to install Prometheus"; exit 1; }

# Installing nops-cost
helm install nops-cost --repo https://opencost.github.io/opencost-helm-chart opencost \
--namespace nops-cost --create-namespace -f ./nops-cost.yaml || { echo "Failed to install nops-cost"; exit 1; }

# Installing k8s-agent
helm install nops-k8s-agent --repo https://nops-io.github.io/nops-k8s-agent \
nops-k8s-agent --namespace nops-k8s-agent -f ./values.yaml \
--set env_variables.APP_NOPS_K8S_AGENT_CLUSTER_ARN=$APP_NOPS_K8S_AGENT_CLUSTER_ARN,\
env_variables.APP_AWS_S3_BUCKET=$APP_AWS_S3_BUCKET,\
env_variables.APP_AWS_S3_PREFIX=$APP_AWS_S3_PREFIX || { echo "Failed to install k8s-agent"; exit 1; }

echo "All operations completed successfully."
echo "Proceed to nOps Dashboard and finish the integration."
