from nops_k8s_agent.settings import NOPS_K8S_AGENT_CLUSTER_ARN


def derive_suffix_from_settings():
    arn_parts = NOPS_K8S_AGENT_CLUSTER_ARN.split(":")
    region = arn_parts[3]
    return region
