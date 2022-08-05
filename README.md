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

### Deploy Agent via Helm repo

    helm repo add nops-k8s-agent https://nops-io.github.io/nops-k8s-agent
    helm install -f values.yaml nops-k8s-agent
