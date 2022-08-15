from nops_k8s_agent.libs.kube_metadata import KubeMetadata


def test_get_kube_metadata():
    metadata = KubeMetadata().get_metadata()
    assert metadata


def test_get_kube_metadata_status():
    status = KubeMetadata.get_status()
    assert status == "Success"
