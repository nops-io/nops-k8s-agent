from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from nops_k8s_agent.libs.kube_metrics import KubeMetrics
from nops_k8s_agent.libs.nops_http_client import forward_logs


class Command(BaseCommand):
    help = "Send metrics to nOps"

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--frequency",
            default="high",
            type=str,
            help="Frequency to send low/medium/high",
            choices=["low", "medium", "high", "pod_metadata", "node_metrics"],
        )

    def handle(self, *args, **options):
        try:
            metrics = KubeMetrics().get_metrics(frequency=options["frequency"])
            forward_logs(metrics, settings.NOPS_K8S_COLLECTOR_AWS_ACCOUNT_NUMBER)
        except Exception as e:
            raise CommandError(f"Error when getting metrics {str(e)}")
        self.stdout.write(f"Got {len(metrics)} metrics event")
