#!/bin/bash
# Optional parameters
# --debug to enable debug mode
# --ipv6 if your cluster is setup with ipv6
# --custom-registry if you want to use your custom registry for container images (This will prompt your registry URL)
# Exit script on error
set -e

####################  REPLACE CLUSTER ARN #############################

APP_NOPS_K8S_AGENT_CLUSTER_ARN="<REPLACE-YourClusternARN>" # You can find this on your EKS dashboard on AWS

####################  OPTIONAL: SET USER SECRET ######################

USE_SECRETS=false # Set this to true if you don't want to use identity provider service role
AGENT_AWS_ACCESS_KEY_ID="<REPLACE-YourAccessKeyId>"
AGENT_AWS_SECRET_ACCESS_KEY="<REPLACE-YourSecretAccessKey>"

######################################################################

# Logging setup
LOG_FILE="./nops-k8s-agent-install.log"
exec > >(tee -a "$LOG_FILE") 2>&1

# Timestamp for log messages
log() {
    echo "$(date +"%Y-%m-%d %T") - $1"
}

# Error handling
trap 'log "An error occurred. Exiting..."; exit 1' ERR


USE_CUSTOM_REGISTRY=false
CUSTOM_REGISTRY="<REPLACE-YourCustomRegistry>"
APP_AWS_S3_BUCKET="<REPLACE-YourS3Bucket>"
APP_AWS_S3_PREFIX="<REPLACE-YourS3Prefix>"
APP_PROMETHEUS_SERVER_ENDPOINT="http://nops-prometheus-server.nops-prometheus-system.svc.cluster.local:80"

PROMETHEUS_CONFIG_URL="https://raw.githubusercontent.com/nops-io/nops-k8s-agent/master/easy-install/prometheus-ksm.yaml"
PROMETHEUS_CONFIG_URL_DEBUG="https://raw.githubusercontent.com/nops-io/nops-k8s-agent/master/easy-install/prometheus-ksm-debug.yaml"

# Initialize variables
IPV_TYPE_RECORD="A"
DEBUG_MODE="false"

# Validate configuration
validate_config() {
    if [[ "$USE_CUSTOM_REGISTRY" == "true" && ($CUSTOM_REGISTRY == "<REPLACE-YourCustomRegistry>" || -z $CUSTOM_REGISTRY) ]]; then
        log "Error: Set your custom registry URL."
        exit 1
    fi

    if [[ $APP_NOPS_K8S_AGENT_CLUSTER_ARN == "<REPLACE-YourClusternARN>" ]]; then
        log "Error: Cluster ARN variables must be set before running this script."
        exit 1
    fi
}

# Process arguments
process_arguments() {
    for arg in "$@"; do
        case $arg in
            --ipv6) IPV_TYPE_RECORD="AAAA"; shift ;;
            --debug|--DEBUG) DEBUG_MODE="true"; shift ;;
            --custom-registry)
                USE_CUSTOM_REGISTRY=true
                shift
                read -p "Enter the custom registry URL: " CUSTOM_REGISTRY
                ;;
        esac
    done
}

# Derive IAM role ARN
derive_iam_role_arn() {
    local eks_cluster_arn=$1
    local role_name="nops-ccost"
    local account_id=$(echo "$eks_cluster_arn" | cut -d':' -f5)
    local cluster_region=$(echo "$eks_cluster_arn" | cut -d':' -f4)
    local cluster_name=$(echo "$eks_cluster_arn" | awk -F'[:/]' '{print $NF}')
    local iam_role_arn="arn:aws:iam::$account_id:role/${role_name}-${cluster_name}_${cluster_region}"
    echo "$iam_role_arn"
}

# Check dependencies
check_dependencies() {
    for cmd in kubectl helm; do
        if ! command -v $cmd &>/dev/null; then
            log "Error: $cmd is not installed. Please install $cmd and try again."
            exit 1
        fi
    done
}

# Switch kubectl context
switch_kubectl_context() {
    local required_context=$1
    local current_context=$(kubectl config current-context)
    if [ "$current_context" != "$required_context" ]; then
        log "Current context ($current_context) is not set to required ARN ($required_context). Attempting to switch..."
        if ! kubectl config use-context "$required_context"; then
            log "Error: Failed to switch to context $required_context."
            log "Current context is $current_context. Is this correct? (y/n)"
            read -r user_input
            if [ "$user_input" != "y" ]; then
                log "Exiting script."
                exit 1
            else
                log "Proceeding installation on $current_context"
            fi
        else
            log "Switched context to $required_context successfully."
        fi
    else
        log "Current context is already set to the required ARN."
    fi
}

# Create namespace
create_namespace() {
    local namespace=$1
    kubectl get namespace $namespace >/dev/null 2>&1 || kubectl create namespace $namespace
}

# Install Prometheus
install_prometheus() {
    local config_url=$1
    helm upgrade --install nops-prometheus prometheus --repo https://prometheus-community.github.io/helm-charts \
        --namespace nops-prometheus-system --create-namespace -f $config_url \
        --set extraScrapeConfigs='- job_name: nops-cost
  honor_labels: true
  scrape_interval: 1m
  scrape_timeout: 10s
  metrics_path: /metrics
  scheme: http
  dns_sd_configs:
  - names:
    - nops-cost.nops-cost.svc.cluster.local
    type: "'"${IPV_TYPE_RECORD}"'"
    port: 9003' \
        $( [[ "$USE_CUSTOM_REGISTRY" == "true" ]] && echo "--set server.image.repository=$CUSTOM_REGISTRY/prometheus/prometheus \
        --set configmapReload.prometheus.image.repository=$CUSTOM_REGISTRY/prometheus-operator/prometheus-config-reloader \
        --set kube-state-metrics.image.registry=$CUSTOM_REGISTRY \
        --set kube-state-metrics.image.repository=kube-state-metrics/kube-state-metrics \
        --set prometheus-node-exporter.image.registry=$CUSTOM_REGISTRY \
        --set prometheus-node-exporter.image.repository=prometheus/node-exporter" ) \
        || { log "Error: Failed to install Prometheus"; exit 1; }
}

# Install nops-cost
install_nops_cost() {
    helm upgrade -i nops-cost --repo https://opencost.github.io/opencost-helm-chart opencost \
        --namespace nops-cost --create-namespace -f https://raw.githubusercontent.com/nops-io/nops-k8s-agent/master/easy-install/nops-cost.yaml \
        --set prometheus.bearer_token=$NOPS_K8S_AGENT_PROM_TOKEN \
        --set networkPolicies.prometheus.namespace=$PROMETHEUS_NAMESPACE \
        --set opencost.exporter.env[0].value=$APP_PROMETHEUS_SERVER_ENDPOINT \
        --set opencost.exporter.env[0].name=PROMETHEUS_SERVER_ENDPOINT \
        $( [[ "$USE_CUSTOM_REGISTRY" == "true" ]] && echo "--set opencost.exporter.image.registry=$CUSTOM_REGISTRY --set opencost.exporter.image.repository=opencost/opencost" ) \
        $( [[ "$DEBUG_MODE" == "true" ]] && echo "--set loglevel=debug" ) \
        || { log "Error: Failed to install nops-cost"; exit 1; }
}

# Install k8s agent
install_k8s_agent() {
    helm upgrade -i nops-k8s-agent --repo https://nops-io.github.io/nops-k8s-agent \
        nops-k8s-agent --namespace nops-k8s-agent -f https://raw.githubusercontent.com/nops-io/nops-k8s-agent/master/easy-install/values.yaml \
        --set service_account_role=$SERVICE_ACCOUNT_ROLE \
        --set secrets.useAwsCredentials=$USE_SECRETS \
        --set env_variables.APP_NOPS_K8S_AGENT_CLUSTER_ARN=$APP_NOPS_K8S_AGENT_CLUSTER_ARN \
        --set env_variables.APP_PROMETHEUS_SERVER_ENDPOINT=$APP_PROMETHEUS_SERVER_ENDPOINT \
        --set env_variables.NOPS_K8S_AGENT_PROM_TOKEN=$NOPS_K8S_AGENT_PROM_TOKEN \
        --set env_variables.APP_AWS_S3_BUCKET=$APP_AWS_S3_BUCKET \
        --set env_variables.APP_AWS_S3_PREFIX=$APP_AWS_S3_PREFIX \
        $( [[ "$DEBUG_MODE" == "true" ]] && echo "--set debug=true" ) \
        $( [[ "$USE_CUSTOM_REGISTRY" == "true" ]] && echo "--set image.repository=$CUSTOM_REGISTRY/nops-io/nops-k8s-agent" ) \
        || { log "Error: Failed to install k8s-agent"; exit 1; }
}

# Main script
main() {
    validate_config
    process_arguments "$@"
    log "Selected configuration for agent and cluster"
    log "Type record: $( [[ "$IPV_TYPE_RECORD" == "A" ]] && echo "IPV4" || echo "IPV6" )"
    [[ "$DEBUG_MODE" == "true" ]] && log "Debug mode: ENABLED"
    [[ "$USE_CUSTOM_REGISTRY" == "true" ]] && log "Custom registry: $CUSTOM_REGISTRY" || log "Using public repositories"

    SERVICE_ACCOUNT_ROLE=$(derive_iam_role_arn "$APP_NOPS_K8S_AGENT_CLUSTER_ARN")
    log "Using service account role: $SERVICE_ACCOUNT_ROLE"

    check_dependencies
    switch_kubectl_context "$APP_NOPS_K8S_AGENT_CLUSTER_ARN"
    create_namespace "nops-k8s-agent"

    if [[ "$USE_SECRETS" == "true" ]]; then
        if [[ $AGENT_AWS_ACCESS_KEY_ID == "<REPLACE-YourAccessKeyId>" || $AGENT_AWS_SECRET_ACCESS_KEY == "<REPLACE-YourSecretAccessKey>" ]]; then
            log "Error: AWS credentials must be set before running this script."
            exit 1
        fi

        nops_k8s_agent_secret="nops-k8s-agent"
        kubectl create secret generic $nops_k8s_agent_secret \
            --from-literal=aws_access_key_id=$AGENT_AWS_ACCESS_KEY_ID \
            --from-literal=aws_secret_access_key=$AGENT_AWS_SECRET_ACCESS_KEY \
            --namespace=nops-k8s-agent --dry-run=client -o yaml | kubectl apply -f -
    fi

    kubectl config set-context --current --namespace=nops-k8s-agent || { log "Error: Failed to set kubectl context to nops-k8s-agent namespace"; exit 1; }

    if [[ "$DEBUG_MODE" == "true" ]]; then
        install_prometheus $PROMETHEUS_CONFIG_URL_DEBUG
    else
        install_prometheus $PROMETHEUS_CONFIG_URL
    fi

    install_nops_cost
    install_k8s_agent

    log "All operations completed successfully."
}

main "$@"
