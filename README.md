# nops-k8s-agent

Worker contains database to keep users entries and pulls metadata from their accounts on a scheduled basis.
Puts output to kafka topic.

## Requirements:

- Tilt [tilt.dev](https://tilt.dev)
- Helm [helm.sh](https://helm.sh/)
- kubectl connected to any k8s cluster (Recommence version v1.23.6). Example is using [k3d](https://k3d.io/v5.1.0/)
- make

## Development

Copy ./charts/nops-k8s-agent/values.yaml to ./charts/nops-k8s-agent/local_values.yaml

Enter configuration to local_values.yaml

Use any k8s cluster provider. This example would be using [k3d](https://k3d.io/).

    # Launch cluster
    make dev_infra

    # Launch stack
    make run

## Deployment


### Get the repository

As the current version using helm chart for deployment. You need to clone this repo first to get chart files.


### Crete name space

    kubectl create namespace nops-k8s-agent
    kubectl config set-context --current --namespace=nops-k8s-agent


### Deploy Prometheus

You can use your own Prometheus instance or launching your nops-k8s-agent namespace

    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm install prometheus prometheus-community/kube-prometheus-stack

### Configure values.yaml

There are required variables:

- APP_PROMETHEUS_SERVER_ENDPOINT - depends on your prometheus stack installation 
- APP_NOPS_K8S_AGENT_CLUSTER_ID - needs to match with your cluster id 
- APP_NOPS_K8S_COLLECTOR_API_KEY - Currently no support signature verification https://docs.nops.io/en/articles/5955764-getting-started-with-the-nops-developer-api
- APP_NOPS_K8S_COLLECTOR_AWS_ACCOUNT_NUMBER - The AWS account number of which is configured within nOps

You can use your own Chart values file or using our example setup_values script to fetch variable_env from Parameter Store SSM (Not encrypted)

    # Patch values for env_variables using SSM store.
    python3 deploy/setup_values.py $CI_ENVIRONMENT_SLUG charts/nops-k8s-agent/values.yaml > /tmp/values.yaml

### Deploy Agent

Start the helm chart

    # Upgrade chart.
    helm \
      upgrade -i nops-k8s-agent ./charts/nops-k8s-agent \
      -f /tmp/values.yaml \
      --namespace nops-k8s-agent \
      --set image.repository=ghcr.io/nops-io/nops-k8s-agent \
      --set image.tag=deploy \
      --set env_variables.APP_ENV=live \
      --wait --timeout=300s