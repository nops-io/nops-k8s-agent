#!/bin/bash

# Exit script on error
set -e

####################  REPLACE CLUSTER ARN #############################

APP_NOPS_K8S_AGENT_CLUSTER_ARN="<REPLACE-YourClusternARN>" # You can find this on your EKS dashboard on AWS

#######################################################################
#######################################################################
################### OPTIONAL CUSTOM SETTINGS ##########################

# Set these if you have a custom registry to pull images from

USE_CUSTOM_REGISTRY=false # Change this to true, if necessary
CUSTOM_REGISTRY="<REPLACE-YourCustomRegistry>" # Set here the url to your custom registry

# Set these if you don't want to use OIDC and service account roles
USE_SECRETS=false # If you want to use IAM User secrets instead of service account roles, change this to true
AGENT_AWS_ACCESS_KEY_ID="<REPLACE-YourAccessKeyId>" # Set your credentials here, if necessary
AGENT_AWS_SECRET_ACCESS_KEY="<REPLACE-YourSecretAccessKey>"
#######################################################################


APP_AWS_S3_BUCKET="<REPLACE-YourS3Bucket>"
APP_AWS_S3_PREFIX="<REPLACE-YourS3Prefix>"
APP_PROMETHEUS_SERVER_ENDPOINT="http://nops-prometheus-server.nops-prometheus-system.svc.cluster.local:80"

PROMETHEUS_CONFIG_URL="https://raw.githubusercontent.com/nops-io/nops-k8s-agent/master/easy-install/prometheus-ksm.yaml"

derive_iam_role_arn() {
    local eks_cluster_arn=$1
    local role_name="nops-ccost"

    # Extract the account ID, region, and cluster name from the EKS cluster ARN
    local account_id=$(echo "$eks_cluster_arn" | cut -d':' -f5)
    local cluster_region=$(echo "$eks_cluster_arn" | cut -d':' -f4)
    local cluster_name=$(echo "$eks_cluster_arn" | awk -F'[:/]' '{print $NF}')

    # Construct the IAM role ARN
    local iam_role_arn="arn:aws:iam::$account_id:role/${role_name}-${cluster_name}_${cluster_region}"

    echo "$iam_role_arn"
}

SERVICE_ACCOUNT_ROLE=$(derive_iam_role_arn "$APP_NOPS_K8S_AGENT_CLUSTER_ARN")
echo "Using service account role: $SERVICE_ACCOUNT_ROLE"
# PROMETHEUS_CONFIG_URL="https://raw.githubusercontent.com/nops-io/nops-k8s-agent/master/easy-install/prometheus.yaml" # this is with ksm disabled

# Check if helm and kubectl are installed
if ! command -v kubectl &>/dev/null; then
    echo "kubectl is not installed. Please install kubectl and try again."
    exit 1
fi

if ! command -v helm &>/dev/null; then
    echo "Helm is not installed. Please install Helm and try again."
    exit 1
fi

if [[ "$USE_CUSTOM_REGISTRY" == "true" ]]; then
    if [[ $CUSTOM_REGISTRY == "<REPLACE-YourCustomRegistry>" ]]; then
    echo "Set your custom registry url."
    exit 1
    fi
fi


# Check current kubectl context and compare it with the required ARN
current_context=$(kubectl config current-context)
if [ "$current_context" != "$APP_NOPS_K8S_AGENT_CLUSTER_ARN" ]; then
    echo "Current context ($current_context) is not set to required ARN ($APP_NOPS_K8S_AGENT_CLUSTER_ARN). Attempting to switch..."
    if ! kubectl config use-context "$APP_NOPS_K8S_AGENT_CLUSTER_ARN"; then
        echo "Failed to switch to context $APP_NOPS_K8S_AGENT_CLUSTER_ARN. Please check your configuration."
        exit 1
    fi
    echo "Switched context to $APP_NOPS_K8S_AGENT_CLUSTER_ARN successfully."
fi

if [[ $APP_NOPS_K8S_AGENT_CLUSTER_ARN == "<REPLACE-YourClusternARN>"  ]]; then
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


if [[ "$USE_SECRETS" == "true" ]]; then
    # Ensure AGENT_AWS_ACCESS_KEY_ID and AGENT_AWS_SECRET_ACCESS_KEY are replaced
    if [[ $AGENT_AWS_ACCESS_KEY_ID == "<REPLACE-YourAccessKeyId>" || $AGENT_AWS_SECRET_ACCESS_KEY == "<REPLACE-YourSecretAccessKey>" ]]; then
    echo "AWS credentials must be set before running this script."
    exit 1
    fi

    # Check if the secret already exists
    nops_k8s_agent_secret="nops-k8s-agent"
    if kubectl get secret $nops_k8s_agent_secret --namespace $nops_k8s_agent_namespace >/dev/null 2>&1; then
        echo "Secret 'nops-k8s-agent' already exists in namespace '${nops_k8s_agent_namespace}'. Updating it..."
        # Command to update the existing secret
        kubectl create secret generic $nops_k8s_agent_secret \
        --from-literal=aws_access_key_id=$AGENT_AWS_ACCESS_KEY_ID \
        --from-literal=aws_secret_access_key=$AGENT_AWS_SECRET_ACCESS_KEY \
        --namespace=${nops_k8s_agent_namespace} --dry-run=client -o yaml | kubectl apply -f -
    else
        echo "Secret 'nops-k8s-agent' does not exist in namespace '${nops_k8s_agent_namespace}'. Creating it..."
        # Command to create the secret
        if kubectl create secret generic $nops_k8s_agent_secret \
        --from-literal=aws_access_key_id=$AGENT_AWS_ACCESS_KEY_ID \
        --from-literal=aws_secret_access_key=$AGENT_AWS_SECRET_ACCESS_KEY \
        --namespace=${nops_k8s_agent_namespace} --save-config; then
            echo "Secret 'nops-k8s-agent' created successfully."
        else
            echo "Failed to create secret for AWS access."
            exit 1
        fi
    fi
fi

# Set kubectl context to use nops-k8s-agent namespace
kubectl config set-context --current --namespace=$nops_k8s_agent_namespace || { echo "Failed to set kubectl context to nops-k8s-agent namespace"; exit 1; }


if [[ "$USE_CUSTOM_REGISTRY" == "true" ]]; then
    # Installing nops-Prometheus
    helm upgrade --install nops-prometheus prometheus --repo https://prometheus-community.github.io/helm-charts \
        --namespace nops-prometheus-system --create-namespace -f $PROMETHEUS_CONFIG_URL \
        --set server.image.repository="$CUSTOM_REGISTRY/prometheus/prometheus" \
        --set configmapReload.prometheus.image.repository="$CUSTOM_REGISTRY/prometheus-operator/prometheus-config-reloader" \
        --set kube-state-metrics.image.registry=$CUSTOM_REGISTRY \
        --set kube-state-metrics.image.repository="kube-state-metrics/kube-state-metrics" \
        --set prometheus-node-exporter.image.registry=$CUSTOM_REGISTRY \
        --set prometheus-node-exporter.image.repository="prometheus/node-exporter" \
        || { echo "Failed to install Prometheus"; exit 1; }

    # # Installing nops-cost
    helm upgrade -i nops-cost --repo https://opencost.github.io/opencost-helm-chart opencost \
    --namespace nops-cost --create-namespace -f https://raw.githubusercontent.com/nops-io/nops-k8s-agent/master/easy-install/nops-cost.yaml  \
    --set prometheus.internal.serviceName=$PROMETHEUS_SERVICE \
    --set prometheus.internal.namespaceName=$PROMETHEUS_NAMESPACE \
    --set prometheus.bearer_token=$NOPS_K8S_AGENT_PROM_TOKEN \
    --set networkPolicies.prometheus.namespace=$PROMETHEUS_NAMESPACE \
    --set opencost.exporter.env[0].value=$APP_PROMETHEUS_SERVER_ENDPOINT \
    --set opencost.exporter.env[0].name=PROMETHEUS_SERVER_ENDPOINT \
    --set opencost.exporter.image.registry=$CUSTOM_REGISTRY \
    --set opencost.exporter.image.repository="opencost/opencost" \
    || { echo "Failed to install nops-cost"; exit 1; }

    # Installing k8s-agent
    helm upgrade -i nops-k8s-agent --repo https://nops-io.github.io/nops-k8s-agent \
    nops-k8s-agent --namespace nops-k8s-agent -f https://raw.githubusercontent.com/nops-io/nops-k8s-agent/master/easy-install/values.yaml \
    --set service_account_role=$SERVICE_ACCOUNT_ROLE \
    --set env_variables.APP_NOPS_K8S_AGENT_CLUSTER_ARN=$APP_NOPS_K8S_AGENT_CLUSTER_ARN \
    --set env_variables.APP_PROMETHEUS_SERVER_ENDPOINT=$APP_PROMETHEUS_SERVER_ENDPOINT \
    --set env_variables.NOPS_K8S_AGENT_PROM_TOKEN=$NOPS_K8S_AGENT_PROM_TOKEN \
    --set env_variables.APP_AWS_S3_BUCKET=$APP_AWS_S3_BUCKET \
    --set env_variables.APP_AWS_S3_PREFIX=$APP_AWS_S3_PREFIX \
    --set image.repository="$CUSTOM_REGISTRY/nops-io/nops-k8s-agent" \
    || { echo "Failed to install k8s-agent"; exit 1; }

else
    # Installing nops-Prometheus
    helm upgrade --install nops-prometheus prometheus --repo https://prometheus-community.github.io/helm-charts  --namespace nops-prometheus-system --create-namespace -f $PROMETHEUS_CONFIG_URL || { echo "Failed to install Prometheus"; exit 1; }

    # # Installing nops-cost
    helm upgrade -i nops-cost --repo https://opencost.github.io/opencost-helm-chart opencost \
    --namespace nops-cost --create-namespace -f https://raw.githubusercontent.com/nops-io/nops-k8s-agent/master/easy-install/nops-cost.yaml  \
    --set prometheus.internal.serviceName=$PROMETHEUS_SERVICE \
    --set prometheus.internal.namespaceName=$PROMETHEUS_NAMESPACE \
    --set prometheus.bearer_token=$NOPS_K8S_AGENT_PROM_TOKEN \
    --set networkPolicies.prometheus.namespace=$PROMETHEUS_NAMESPACE \
    --set opencost.exporter.env[0].value=$APP_PROMETHEUS_SERVER_ENDPOINT \
    --set opencost.exporter.env[0].name=PROMETHEUS_SERVER_ENDPOINT  || { echo "Failed to install nops-cost"; exit 1; }

    # Installing k8s-agent
    helm upgrade -i nops-k8s-agent --repo https://nops-io.github.io/nops-k8s-agent \
    nops-k8s-agent --namespace nops-k8s-agent -f https://raw.githubusercontent.com/nops-io/nops-k8s-agent/master/easy-install/values.yaml \
    --set service_account_role=$SERVICE_ACCOUNT_ROLE \
    --set secrets.useAwsCredentials=$USE_SECRETS \
    --set env_variables.APP_NOPS_K8S_AGENT_CLUSTER_ARN=$APP_NOPS_K8S_AGENT_CLUSTER_ARN \
    --set env_variables.APP_PROMETHEUS_SERVER_ENDPOINT=$APP_PROMETHEUS_SERVER_ENDPOINT \
    --set env_variables.NOPS_K8S_AGENT_PROM_TOKEN=$NOPS_K8S_AGENT_PROM_TOKEN \
    --set env_variables.APP_AWS_S3_BUCKET=$APP_AWS_S3_BUCKET \
    --set env_variables.APP_AWS_S3_PREFIX=$APP_AWS_S3_PREFIX || { echo "Failed to install k8s-agent"; exit 1; }
fi

echo "All operations completed successfully."