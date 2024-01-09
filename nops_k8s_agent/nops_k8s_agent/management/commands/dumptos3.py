import uuid
from django.conf import settings
from django.core.management.base import BaseCommand
import boto3
import json
from nops_k8s_agent.libs.kube_metadata import KubeMetadata
from nops_k8s_agent.libs.kube_metrics import KubeMetrics
from nops_k8s_agent.libs.container_usage import ContainerUsage
from nops_k8s_agent.libs.node_usage import NodeUsage
from nops_k8s_agent.libs.pod_usage import PodUsage
import datetime as dt

class Command(BaseCommand):

    def handle(self, *args, **options):
        export_datetime = dt.datetime.utcnow().strftime("%Y-%m-%d-%H-%M-%S")
        bucket = "k8s-agent-data"
        for event_type, func in [
            ("healtcheck", self.get_healtcheck), 
            ("node_usage", self.get_k8s_node_usage), 
            ("pod_usage", self.get_k8s_pod_usage), 
            ("container_usage", self.get_k8s_container_usage), 
            ("node_metadata", self.get_node_metadata), 
            ("pod_metadata", self.get_pod_metadata), 
            ("node_metrics", self.get_node_metrics), 
            ("low_frequency_metrics", self.get_low_frequency_metrics), 
            ("medium_frequency_metrics", self.get_medium_frequency_metrics), 
            ("high_frequency_metrics", self.get_high_frequency_metrics),
        ]:
            try:
                events = func()
                if events:
                    client = boto3.client('s3')
                    client.put_object(
                        Body=json.dumps(events, default=str),
                        Bucket=bucket,
                        Key=f"{export_datetime}/{event_type}.json",
                    )
                    self.stderr.write(f"Got {len(events)} events for {event_type}, dumped to s3.")
                else:
                    self.stdout.write("Got no metrics event")
            except Exception as e:
                self.stderr.write(f"Error when processing {event_type} {str(e)}")

    def get_healtcheck(self):
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
        return healthcheck
    
    def get_k8s_node_usage(self):
        return NodeUsage().get_events()

    def get_k8s_pod_usage(self):
        return PodUsage().get_events()

    def get_k8s_container_usage(self):
        return ContainerUsage().get_events()
    
    def get_node_metadata(self):
        return KubeMetadata().get_metadata()
    
    def get_pod_metadata(self):
        return KubeMetrics().get_metrics(frequency="pod_metadata")

    def get_node_metrics(self):
        return KubeMetrics().get_metrics(frequency="node_metrics")
    
    def get_low_frequency_metrics(self):
        return KubeMetrics().get_metrics(frequency="low")
    
    def get_medium_frequency_metrics(self):
        return KubeMetrics().get_metrics(frequency="medium")
    
    def get_high_frequency_metrics(self):
        return KubeMetrics().get_metrics(frequency="high")