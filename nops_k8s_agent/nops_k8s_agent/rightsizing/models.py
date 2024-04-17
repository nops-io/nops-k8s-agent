from dataclasses import dataclass
from typing import Any


@dataclass
class ContainerPatch:
    container_name: str
    requests: dict[str, str]


@dataclass
class PodPatch:
    pod_name: str
    pod_namespace: str
    containers: list[ContainerPatch]

    def to_patch_kwargs(self) -> dict[str, Any]:
        return {
            "name": self.pod_name,
            "namespace": self.pod_namespace,
            "body": {
                "spec": {
                    "containers": [
                        {"name": container.container_name, "resources": {"requests": container.requests}}
                        for container in self.containers
                    ]
                }
            },
        }
