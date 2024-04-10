import asyncio
from collections import defaultdict

from django.core.management.base import BaseCommand

from kubernetes_asyncio import client
from kubernetes_asyncio import config
from kubernetes_asyncio.client.api_client import ApiClient


class Command(BaseCommand):
    @staticmethod
    def _init_client():
        config.load_incluster_config()

    @staticmethod
    async def _list_pods():
        pods = defaultdict(dict)

        async with ApiClient() as api:
            v1_client = client.CoreV1Api(api)
            all_pods_response = await v1_client.list_pod_for_all_namespaces(watch=False)

            for pod in all_pods_response.items:
                pods[pod.metadata.namespace][pod.metadata.name] = {
                    "containers": {container.name: container.resources for container in pod.spec.containers}
                }

        return pods

    async def rightsize(self):
        self._init_client()
        pods = await self._list_pods()
        print(pods)

    def handle(self, *args, **options):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.rightsize())
