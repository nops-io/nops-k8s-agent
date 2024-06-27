# Table of Contents

- [Introduction to nOps Kubernetes Agent](#introduction-to-nops-kubernetes-agent)
- [Development Requirements](#development-requirements)
  * [Tilt](https://tilt.dev)
  * [Helm](https://helm.sh/)
  * [kubectl](https://kubernetes.io/docs/reference/kubectl/overview/)
  * [k3d (for development)](https://k3d.io/v5.1.0/)
  * [make](#make)
- [Easy Install](#easy-install)
- [Development Setup](#development-setup)
- [Agent Deployment](#agent-deployment)
  * [Option 1: Deploy Agent From Source Code](#deploy-agent-from-source-code)
  * [Option 2: Deploy Agent via Helm Repo (recommended)](#deploy-agent-via-helm-repo)
- [Configure nOps Integration](#configure-nops-integration)

# Introduction to nOps Kubernetes Agent

The **nOps Kubernetes Agent** (nops-k8s-agent) is essential for **optimizing cloud infrastructure management**. It is designed to:

* **Collect metadata** from Kubernetes clusters.
* **Securely transfer** this data to an Amazon S3 bucket.

This enables the nOps platform to:
 * **Analyze** the collected data.
 * Provide **insights for cost optimization** and **resource management**.

This document guides you through the setup and deployment process, ensuring a smooth integration with the nOps platform for enhanced operational efficiency.

## nOps Integration 

Check our <a href="https://help.nops.io/Configure-nOps-Kubernetes-Agent-on-EKS.html">help page</a> to walk you through the integration.

---

## Development Requirements

Before starting with the development of the nOps Kubernetes Agent, ensure you have the following tools installed and configured:

- **Tilt**: Automates the development cycle by updating containers in real time. Useful for rapid testing and iteration. [Learn more](https://tilt.dev).
- **Helm**: Helps manage Kubernetes applications through Helm charts. Helm charts simplify the deployment and management of applications on Kubernetes. [Learn more](https://helm.sh/).
- **kubectl**: A command-line tool for interacting with Kubernetes clusters. You will need it to deploy and manage applications, inspect cluster resources, and view logs. Ensure it's connected to a Kubernetes cluster (version v1.23.6+ recommended). [Learn more](https://kubernetes.io/docs/reference/kubectl/overview/).
- **k3d**: Simplifies running a local Kubernetes cluster within Docker containers. It's particularly handy for development purposes. [Learn more](https://k3d.io/v5.1.0/).
- **make**: A build automation tool that automatically builds executable programs and libraries from source code by reading files called Makefiles which specify how to derive the target program.

These tools are essential for setting up your development environment and will be used throughout the setup and deployment process.

---

## Development Setup

Follow these steps to set up your development environment for the nOps Kubernetes Agent:

1. **Prepare the Helm Chart Values**:
   - Copy the Helm chart values file from `./charts/nops-k8s-agent-dev/values.yaml` to a new file named `./charts/nops-k8s-agent-dev/local_values.yaml`.
   - Edit `local_values.yaml` to enter your specific configuration settings.

2. **Set Up a Kubernetes Cluster**:
   - Use any Kubernetes cluster provider of your choice. For development purposes, we recommend using [k3d](https://k3d.io/) due to its simplicity and ease of use.
   - If using k3d, you can quickly launch a local cluster by running the following command:
     ```shell
     make dev_infra
     ```
   - This command initializes a local Kubernetes cluster suitable for development.

3. **Deploy the Development Stack**:
   - With your Kubernetes cluster running, deploy the nOps Kubernetes Agent development stack to the cluster:
     ```shell
     make run
     ```
   - This command deploys the necessary components, including the nOps Kubernetes Agent, into your Kubernetes cluster.

4. **Verify the Deployment**:
   - Ensure that all components are correctly deployed and running. You can check the status of the deployments by using:
     ```shell
     kubectl get pods
     ```
   - Look for pods related to the nOps Kubernetes Agent and confirm they are in the `Running` state.

By following these steps, you'll have a development environment set up for the nOps Kubernetes Agent. This environment will allow you to develop, test, and iterate on the agent within a local Kubernetes cluster.

---

### Configure values.yaml

There are required variables:

- APP_NOPS_K8S_AGENT_CLUSTER_ARN - needs to match with your cluster arn (starting with arn ending with cluster name)
- APP_AWS_S3_BUCKET - S3 Bucket that this service has write permission
- APP_AWS_S3_PREFIX - S3 Prefix path include trailing slash


Example configuration
```
APP_NOPS_K8S_AGENT_CLUSTER_ARN: "arn:aws:eks:us-west-2:12345679012:cluster/nOps-Testing-EKS"
APP_AWS_S3_BUCKET: "container-cost-export-customer-abc"
APP_AWS_S3_PREFIX: "test-container-cost/"
```

---

## Agent Deployment

There are 2 options for deployment

### Option 1: Deploy Agent via Helm Repo (recommended)

Linux:
```shell
    helm \
      install nops-k8s-agent --repo  https://nops-io.github.io/nops-k8s-agent \
      nops-k8s-agent --namespace nops-k8s-agent -f ./charts/nops-k8s-agent/values.yaml
```
Windows PowerShell:
```shell
    helm `
      install nops-k8s-agent --repo https://nops-io.github.io/nops-k8s-agent `
      nops-k8s-agent --namespace nops-k8s-agent -f ./charts/nops-k8s-agent/values.yaml

```


### Option 2: Deploy Agent From Source Code

Using helm chart for deployment from a cloned repository.
  Linux:
  ```shell
    helm \
      upgrade -i nops-k8s-agent ./charts/nops-k8s-agent \
      -f ./charts/nops-k8s-agent/values.yaml \
      --namespace nops-k8s-agent \
      --set image.repository=ghcr.io/nops-io/nops-k8s-agent \
      --set image.tag=deploy \
      --set env_variables.APP_ENV=live \
      --wait --timeout=300s
```

  Windows PowerShell:
  ```shell
    helm upgrade -i nops-k8s-agent .\charts\nops-k8s-agent `
    -f .\charts\nops-k8s-agent\values.yaml `
    --namespace nops-k8s-agent `
    --set image.repository=ghcr.io/nops-io/nops-k8s-agent `
    --set image.tag=deploy `
    --set env_variables.APP_ENV=live `
    --wait --timeout=300s
```