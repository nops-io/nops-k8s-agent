import datetime as dt
import os

from django.conf import settings
from django.core.management.base import BaseCommand

import boto3

from nops_k8s_agent.container_cost.base_labels import BaseLabels
from nops_k8s_agent.container_cost.deployment_metrics import DeploymentMetrics
from nops_k8s_agent.container_cost.job_metrics import JobMetrics
from nops_k8s_agent.container_cost.node_metadata import NodeMetadata
from nops_k8s_agent.container_cost.node_metrics import NodeMetrics
from nops_k8s_agent.container_cost.persistentvolume_metrics import PersistentvolumeMetrics
from nops_k8s_agent.container_cost.persistentvolumeclaim_metrics import PersistentvolumeclaimMetrics
from nops_k8s_agent.container_cost.pod_metrics import PodMetrics


class Command(BaseCommand):
    def handle(self, *args, **options):
        collect_klass = [
            BaseLabels,
            DeploymentMetrics,
            JobMetrics,
            NodeMetrics,
            PersistentvolumeMetrics,
            PersistentvolumeclaimMetrics,
            PodMetrics,
            NodeMetadata,
        ]
        s3 = boto3.client("s3")

        s3_bucket = settings.AWS_S3_BUCKET
        s3_prefix = settings.AWS_S3_PREFIX
        cluster_arn = settings.NOPS_K8S_AGENT_CLUSTER_ARN
        now = dt.datetime.now()
        tmp_path = f"/tmp/year={now.year}/month={now.month}/day={now.day}/hour={now.hour}/"
        for klass in collect_klass:
            try:
                instance = klass()
                FILE_PREFIX = klass.FILE_PREFIX
                path = f"{s3_prefix}container_cost/{FILE_PREFIX}/year={now.year}/month={now.month}/day={now.day}/hour={now.hour}"
                tmp_file = f"{tmp_path}{klass.FILENAME}"
                instance.convert_to_table_and_save(period="last_hour", step="5m", filename=tmp_file)
                s3_key = f"{path}/{klass.FILENAME}"
                s3.upload_file(Filename=tmp_file, Bucket=s3_bucket, Key=s3_key)
                self.stdout.write(f"File {tmp_file} successfully uploaded to s3://{s3_bucket}/{s3_key}")
            except Exception as e:
                self.stderr.write(f"Error when processing {type(klass)} {str(e)}")
            finally:
                # Trying to remove the tmp file
                try:
                    os.remove(tmp_file)
                except Exception as e:
                    self.stderr.write(f"Error when removing {tmp_file} {str(e)}")
