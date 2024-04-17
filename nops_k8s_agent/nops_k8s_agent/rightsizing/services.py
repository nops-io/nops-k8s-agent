import os
from abc import ABC, abstractmethod
from typing import Any


class RightsizingClient(ABC):
    @abstractmethod
    async def get_configs(self) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def get_namespace_recommendations(self, namespace: str) -> dict[str, Any]:
        raise NotImplementedError


class RightsizingClientService(RightsizingClient):
    async def get_configs(self) -> dict[str, Any]:
        raise NotImplementedError

    async def get_namespace_recommendations(self, namespace: str) -> dict[str, Any]:
        raise NotImplementedError


class RightsizingClientMock(RightsizingClient):
    async def get_configs(self) -> dict[str, Any]:
        """
        MOCKED! Gets the list of nOps configured deployments for a cluster
        Returns:
        {
            "namespace_1": {
                "deployment_1": {
                    "policy": {
                        "threshold_percentage": 0.1  # Do not do rightsizing if the current and new value difference is smaller than the threshold percentage
                    }
                }
            }
        }
        """
        return {"opencost": {"opencost": {"policy": {"threshold_percentage": 0.1}}}}

    async def get_namespace_recommendations(self, namespace: str) -> dict[str, Any]:
        """
        MOCKED! Gets limits/requests recommendations for containers by deployment
        Returns:
        {
            "deployment_1": {
                "container_1": {
                    "requests": {"cpu": 0.2, "memory": 220000000}
                }
            }
        }
        """
        if namespace == "opencost":
            return {"opencost": {"opencost": {"requests": {"cpu": 0.32, "memory": 73401320}}}}
        else:
            return {}


client = None


def get_rightsizing_client() -> RightsizingClient:
    global client
    if client is None:
        if os.environ.get("APP_ENV") == "live":
            # client = RightsizingClientService()
            client = RightsizingClientMock()
        else:
            client = RightsizingClientMock()
    return client
