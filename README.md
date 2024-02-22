# nops-k8s-agent

This Kubernetes agent collects metadata from user accounts and sends container cost export data to a S3 bucket for analysis within the nOps platform.


## Development requirements:

* Tilt: https://tilt.dev
* Helm: https://helm.sh/
* kubectl: https://kubernetes.io/docs/reference/kubectl/overview/ connected to a Kubernetes cluster (version v1.23.6+ recommended)
* k3d (for development): https://k3d.io/v5.1.0/
* make

## Development

Copy ./charts/nops-k8s-agent-dev/values.yaml to ./charts/nops-k8s-agent-dev/local_values.yaml

Enter configuration to local_values.yaml

Use any k8s cluster provider. This example would be using [k3d](https://k3d.io/).

    # Launch cluster
    make dev_infra

    # Launch stack
    make run

## Prerequisites

* nOps account: You'll need a nOps account to use this agent.

### Crete name space

* Kubernetes namespace: Create a dedicated namespace for the agent.


```
    kubectl create namespace nops-k8s-agent
    kubectl config set-context --current --namespace=nops-k8s-agent
```


### Deploy Prometheus

Deploy Prometheus in your cluster, or have an accessible Prometheus instance

```
    helm install prometheus --repo https://prometheus-community.github.io/helm-charts prometheus \
      --namespace prometheus-system --create-namespace \
      --set prometheus-pushgateway.enabled=false \
      --set alertmanager.enabled=false
```


### Create S3 Bucket and IAM Access Key

* Create an S3 bucket for container cost export data.
* Grant the nops-k8s-agent write permissions to this bucket using an IAM Access Key or a Service Role.

### Secret Creation

Create Secret "nops-k8s-agent" with following values in it.
* aws_access_key_id: IAM Access Key ID
* aws_secret_access_key: IAM Access Key Secret


Example Secret Manifest Reference
```
apiVersion: v1
kind: Secret
type: Opaque
metadata:
  name: nops-k8s-agent
  namespace: <same as nops-k8s-agent installation>
data:
  aws_access_key_id: MWYyZDFlMmU2N2Rm 
  aws_secret_access_key: MWYyZDFlMmU2N2Rm
```

### Configure values.yaml

There are required variables:

- APP_PROMETHEUS_SERVER_ENDPOINT - Prometheus server endpoint
- APP_NOPS_K8S_AGENT_CLUSTER_ARN - needs to match with your cluster arn (starting with arn ending with cluster name)
- APP_AWS_S3_BUCKET - S3 Bucket that this service has write permission
- APP_AWS_S3_PREFIX - S3 Prefix path include trailing slash
- NOPS_K8S_AGENT_PROM_TOKEN - (Optional) provide if your prometheus is protected by token


Example configuration
```
APP_PROMETHEUS_SERVER_ENDPOINT: "http://prometheus-server.prometheus-system.svc.cluster.local:80"
APP_NOPS_K8S_AGENT_CLUSTER_ARN: "arn:aws:eks:us-west-2:12345679012:cluster/nOps-Testing-EKS"
APP_AWS_S3_BUCKET: "container-cost-export-customer-abc"
APP_AWS_S3_PREFIX: "test-container-cost/"
```


## Deployment

There are 2 options for deployment

### Deploy Agent From Source Code

Using helm chart for deployment. You need to clone this repo first to get chart files.

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



### Deploy Agent via Helm repo

    helm repo add nops-k8s-agent https://nops-io.github.io/nops-k8s-agent
    helm install -f values.yaml nops-k8s-agent


## Configure nOps Integration


* Log into your nOps account.
* Go to Settings -> Integrations -> Container Cost.
* Configure your S3 bucket and permissions.

Configure the S3 bucket for that account. If you have multiple EKS clusters please use the same bucket.
Configure the read permission on the bucket for the IAM Role that we used on previous setup. Or click to install new Cloudformation Stack to provide the permission automatically.

