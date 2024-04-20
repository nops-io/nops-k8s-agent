#!/bin/bash

# Exit script on error
set -e

# AWS credentials with write permission to S3 bucket
# REPLACE THESE VALUES
######################################################################
AWS_ACCESS_KEY_ID="<REPLACE-YourAccessKeyId>"
AWS_SECRET_ACCESS_KEY="<REPLACE-YourSecretAccessKey>"

APP_NOPS_K8S_AGENT_CLUSTER_ARN="<REPLACE-YourClusternARN>"
APP_AWS_S3_BUCKET="<REPLACE-YourS3Bucket>"
APP_AWS_S3_PREFIX="<REPLACE-YourS3Prefix>"
#######################################################################
# DONT CHANGE ANYTHING BELOW THIS
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
nops_k8s_agent_namespace="nops-k8s-agent"
if kubectl get namespace $nops_k8s_agent_namespace >/dev/null 2>&1; then
    echo "Namespace 'nops-k8s-agent' already exists, no need to create it."
else
    echo "Namespace 'nops-k8s-agent' does not exist. Attempting to create it..."
    # Try to create the namespace
    if kubectl create namespace nops-k8s-agent >/dev/null 2>&1; then
        echo "Namespace 'nops-k8s-agent' created successfully."
    else
        echo "Failed to create namespace 'nops-k8s-agent'."
        exit 1
    fi
fi

# Set kubectl context to use nops-k8s-agent namespace
kubectl config set-context --current --namespace=$nops_k8s_agent_namespace || { echo "Failed to set kubectl context to nops-k8s-agent namespace"; exit 1; }


# Check if the secret already exists
nops_k8s_agent_secret="nops-k8s-agent"
if kubectl get secret $nops_k8s_agent_secret --namespace $nops_k8s_agent_namespace >/dev/null 2>&1; then
    echo "Secret 'nops-k8s-agent' already exists in namespace '${nops_k8s_agent_namespace}'. Updating it..."
    # Command to update the existing secret
    kubectl create secret generic $nops_k8s_agent_secret \
    --from-literal=aws_access_key_id=$AWS_ACCESS_KEY_ID \
    --from-literal=aws_secret_access_key=$AWS_SECRET_ACCESS_KEY \
    --namespace=${nops_k8s_agent_namespace} --dry-run=client -o yaml | kubectl apply -f -
else
    echo "Secret 'nops-k8s-agent' does not exist in namespace '${nops_k8s_agent_namespace}'. Creating it..."
    # Command to create the secret
    if kubectl create secret generic $nops_k8s_agent_secret \
    --from-literal=aws_access_key_id=$AWS_ACCESS_KEY_ID \
    --from-literal=aws_secret_access_key=$AWS_SECRET_ACCESS_KEY \
    --namespace=${nops_k8s_agent_namespace} --save-config; then
        echo "Secret 'nops-k8s-agent' created successfully."
    else
        echo "Failed to create secret for AWS access."
        exit 1
    fi
fi
# Installing nops-Prometheus
helm upgrade --install nops-prometheus prometheus --repo https://prometheus-community.github.io/helm-charts  --namespace nops-prometheus-system --create-namespace   -f ./prometheus.yaml || { echo "Failed to install Prometheus"; exit 1; }

# Installing nops-cost
helm upgrade -i nops-cost --repo https://opencost.github.io/opencost-helm-chart opencost \
--namespace nops-cost --create-namespace -f ./nops-cost.yaml || { echo "Failed to install nops-cost"; exit 1; }

# Installing k8s-agent
helm upgrade -i nops-k8s-agent --repo https://nops-io.github.io/nops-k8s-agent \
nops-k8s-agent --namespace nops-k8s-agent -f ./values.yaml \
--set env_variables.APP_NOPS_K8S_AGENT_CLUSTER_ARN=$APP_NOPS_K8S_AGENT_CLUSTER_ARN,\
env_variables.APP_AWS_S3_BUCKET=$APP_AWS_S3_BUCKET,\
env_variables.APP_AWS_S3_PREFIX=$APP_AWS_S3_PREFIX || { echo "Failed to install k8s-agent"; exit 1; }

echo "All operations completed successfully."
echo "Proceed to nOps Dashboard and finish the integration."
