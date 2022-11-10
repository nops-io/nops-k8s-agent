from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from nops_k8s_agent.libs.kube_metadata import KubeMetadata
from nops_k8s_agent.libs.nops_http_client import forward_logs


class Command(BaseCommand):
    help = "Send metadata to nOps"

    def handle(self, *args, **options):
        try:
            metadata = KubeMetadata().get_metadata()
            forward_logs(metadata, settings.NOPS_K8S_COLLECTOR_AWS_ACCOUNT_NUMBER)
        except Exception as e:
            raise CommandError(f"Error when getting metadata {str(e)}")
        self.stdout.write(f"Got {len(metadata)} metadata event")
