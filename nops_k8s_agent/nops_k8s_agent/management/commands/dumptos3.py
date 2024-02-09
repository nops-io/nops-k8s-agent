import datetime as dt
import os

from django.conf import settings
from django.core.management.base import BaseCommand

import boto3

from nops_k8s_agent.container_cost.base_labels import BaseLabels
from nops_k8s_agent.container_cost.deployment_metrics import DeploymentMetrics
from nops_k8s_agent.container_cost.job_metrics import JobMetrics
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
        ]
        s3 = boto3.client("s3")

        s3_bucket = settings.AWS_S3_BUCKET
        s3_prefix = settings.AWS_S3_PREFIX
        month = dt.datetime.now().month
        year = dt.datetime.now().year
        path = f"{s3_prefix}container_cost/year={year}/month={month}"
        tmp_path = f"/tmp/year={year}/month={month}/"
        for klass in collect_klass:
            try:
                instance = klass()
                tmp_file = f"{tmp_path}{klass.FILENAME}"
                instance.convert_to_table_and_save(filename=tmp_file)
                s3_key = f"{path}/{klass.FILENAME}"
                s3.upload_file(Filename=tmp_file, Bucket=s3_bucket, Key=s3_key)
                self.stdout.write("File {filename} successfully uploaded to s3://{s3_bucket}/{s3_key}")
                self.stdout.write("Got no metrics event")
            except Exception as e:
                self.stderr.write(f"Error when processing {type(klass)} {str(e)}")
            finally:
                # Trying to remove the tmp file
                try:
                    os.remove(tmp_file)
                except Exception as e:
                    self.stderr.write(f"Error when removing {tmp_file} {str(e)}")
