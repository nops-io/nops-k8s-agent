# Enable helm and setup kafka:
namespace = "nops-k8s-agent"
service_name = "nops-k8s-agent"

load("ext://helm_remote", "helm_remote")
load('ext://helm_resource', 'helm_resource', 'helm_repo')

helm_repo(name="prometheus-community",url="https://prometheus-community.github.io/helm-charts")


helm_resource(name="prometheus", chart="prometheus-community/kube-prometheus-stack")


# Build repo:
docker_build(
    "registry.gitlab.com/nopsteam/nops-k8s-agent",
    ".",
    build_args={"debug": "true"},
    live_update=[sync("./nops_k8s_agent", "/workspace")]
)

k8s_yaml(helm("./charts/nops-k8s-agent", name=service_name, namespace=namespace, 
    values=['./charts/nops-k8s-agent/values-local.yaml'],
))
