#!/bin/bash

# Exit script on error
set -e

# Declare AWS credentials - Use the credentials created using cf-bucket-access-key.yaml template
AWS_ACCESS_KEY_ID="<REPLACE-YourAccessKeyId>"
AWS_SECRET_ACCESS_KEY="<REPLACE-YourSecretAccessKey>"

# Ensure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are replaced
if [[ $AWS_ACCESS_KEY_ID == "<REPLACE-YourAccessKeyId>" || $AWS_SECRET_ACCESS_KEY == "<REPLACE-YourSecretAccessKey>" ]]; then
  echo "AWS credentials must be set before running this script."
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

# Installing Prometheus
helm install prometheus --repo https://prometheus-community.github.io/helm-charts prometheus \
  --namespace prometheus-system --create-namespace \
  --set prometheus-pushgateway.enabled=false \
  --set alertmanager.enabled=false \
  -f https://raw.githubusercontent.com/opencost/opencost/develop/kubernetes/prometheus/extraScrapeConfigs.yaml || { echo "Failed to install Prometheus"; exit 1; }

# Installing OpenCost
helm install opencost --repo https://opencost.github.io/opencost-helm-chart opencost \
--namespace opencost --create-namespace -f ./opencost_local.yaml || { echo "Failed to install OpenCost"; exit 1; }

# Installing k8s-agent
helm install nops-k8s-agent --repo https://nops-io.github.io/nops-k8s-agent \
nops-k8s-agent --namespace nops-k8s-agent -f ./values.yaml || { echo "Failed to install k8s-agent"; exit 1; }

echo "All operations completed successfully."
echo "Proceed to nOps Dashboard and finish the integration."
