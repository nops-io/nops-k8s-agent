from django.conf import settings
from django.core.management.base import BaseCommand
from django.core.management.base import CommandError

from nops_k8s_agent.libs.container_usage import ContainerUsage
from nops_k8s_agent.libs.kube_metrics import KubeMetrics
from nops_k8s_agent.libs.node_usage import NodeUsage
from nops_k8s_agent.libs.nops_http_client import forward_logs
from nops_k8s_agent.libs.pod_usage import PodUsage


class Command(BaseCommand):
    help = "Send metrics to nOps"

    def add_arguments(self, parser):
        parser.add_argument(
            "-f",
            "--frequency",
            default="high",
            type=str,
            help="Frequency to send low/medium/high",
            choices=[
                "low",
                "medium",
                "high",
                "pod_metadata",
                "node_metrics",
                "k8s_container_usage",
                "k8s_pod_usage",
                "k8s_node_usage",
            ],
        )

    def handle(self, *args, **options):
        try:
            UsageClass = None
            if options["frequency"] == "k8s_pod_usage":
                UsageClass = PodUsage
            elif options["frequency"] == "k8s_container_usage":
                UsageClass = ContainerUsage
            elif options["frequency"] == "k8s_node_usage":
                UsageClass = NodeUsage
            if UsageClass:
                events = UsageClass().get_events()
            else:
                events = KubeMetrics().get_metrics(frequency=options["frequency"])
            if events:
                forward_logs(events, settings.NOPS_K8S_COLLECTOR_AWS_ACCOUNT_NUMBER)
            else:
                self.stdout.write("Got no metrics event")
        except Exception as e:
            raise CommandError(f"Error when getting metrics {str(e)}")
        if events:
            self.stdout.write(f"Got {len(events)} events")
