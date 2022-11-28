import uuid

from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from nops_k8s_agent.libs.kube_metadata import KubeMetadata
from nops_k8s_agent.libs.kube_metrics import KubeMetrics
from nops_k8s_agent.libs.nops_http_client import forward_logs


class Command(BaseCommand):
    help = "Send agent healthcheck to nOps"

    def handle(self, *args, **options):
        try:
            prometheus_status = KubeMetrics().get_status()
            kube_status = KubeMetadata.get_status()
            healthcheck = {
                "event_type": "k8s_healthcheck",
                "event_id": str(uuid.uuid4()),
                "app_version": settings.APP_VERSION,
                "chart_version": settings.CHART_VERSION,
                "prometheus_status": prometheus_status,
                "kube_status": kube_status,
            }
            forward_logs([healthcheck], settings.NOPS_K8S_COLLECTOR_AWS_ACCOUNT_NUMBER)
        except Exception as e:
            raise CommandError(f"Error when getting healthcheck {str(e)}")
        self.stdout.write("Got healthcheck event")
