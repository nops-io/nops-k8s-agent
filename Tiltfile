# Enable helm and setup kafka:
namespace = "nops-k8s-agent"
service_name = "nops-k8s-agent"

load("ext://helm_remote", "helm_remote")
load('ext://helm_resource', 'helm_resource', 'helm_repo')

if not os.environ.get('CI'):
   helm_repo(name="prometheus-community",url="https://prometheus-community.github.io/helm-charts")
   helm_resource(name="prometheus", chart="prometheus-community/kube-prometheus-stack")
   local_resource(
       "test-everything-prometheus",
       "make test_prometheus",
        deps=["./nops-k8s-agent/", "prometheus"],
        trigger_mode=TRIGGER_MODE_MANUAL,
        resource_deps=[service_name],
        allow_parallel=True
   )
else:
   local_resource(
        "test-everything",
        "make test",
        deps=["./nops-k8s-agent/"],
        trigger_mode=TRIGGER_MODE_MANUAL,
        resource_deps=[service_name],
        allow_parallel=True
    )


# Build repo:
docker_build(
    "ghcr.io/nops-io/nops-k8s-agent",
    ".",
    build_args={"debug": "true"},
    live_update=[sync("./nops_k8s_agent", "/workspace")],
    entrypoint="echo 'WARNING: container is running in dev mode. Entrypoint is overriden in Tiltfile'; sleep 9999999999"
)

k8s_yaml(helm("./charts-dev/nops-k8s-agent-dev", name=service_name, namespace=namespace, 
    values=['./charts-dev/nops-k8s-agent-dev/values.yaml'],
))
