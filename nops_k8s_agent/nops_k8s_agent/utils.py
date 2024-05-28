from nops_k8s_agent.settings import NOPS_K8S_AGENT_CLUSTER_ARN
import uuid

def derive_suffix_from_settings():
    if NOPS_K8S_AGENT_CLUSTER_ARN:
        arn_parts = NOPS_K8S_AGENT_CLUSTER_ARN.split(":")
        region = arn_parts[3]
        return region
    else:
        return str(uuid.uuid4())[:4]