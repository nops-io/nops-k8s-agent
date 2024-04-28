import datetime as dt
import os
import sys

from django.conf import settings
from django.core.management.base import BaseCommand

import boto3

from nops_k8s_agent.container_cost.base_labels import BaseLabels
from nops_k8s_agent.container_cost.deployment_metrics import DeploymentMetrics
from nops_k8s_agent.container_cost.job_metrics import JobMetrics
from nops_k8s_agent.container_cost.node_metadata import NodeMetadata
from nops_k8s_agent.container_cost.node_metrics import NodeMetrics
from nops_k8s_agent.container_cost.nopscost.nopscost_parquet_exporter import main_command
from nops_k8s_agent.container_cost.persistentvolume_metrics import PersistentvolumeMetrics
from nops_k8s_agent.container_cost.persistentvolumeclaim_metrics import PersistentvolumeclaimMetrics
from nops_k8s_agent.container_cost.pod_metrics import PodMetrics
from nops_k8s_agent.settings import SCHEMA_VERSION_DATE


class DualOutput:
    def __init__(self, file_path):
        self.file = open(file_path, "w+")
        self.stdout = sys.stdout

    def write(self, message):
        self.file.write(message)
        self.stdout.write(message)

    def flush(self):
        self.file.flush()
        self.stdout.flush()

    def close(self):
        self.file.close()

    def __enter__(self):
        sys.stdout = sys.stderr = self
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout = sys.stderr = self.stdout
        self.close()


class Command(BaseCommand):
    log_path = "/tmp/logfile.log"

    def add_arguments(self, parser):
        # Optional command-line arguments for start and end date
        parser.add_argument("--start-date", type=str, help="Start date in YYYY-MM-DD format")
        parser.add_argument("--end-date", type=str, help="End date in YYYY-MM-DD format")

    def upload_job_log(self, s3, s3_bucket, s3_prefix, cluster_arn, start_time):
        cluster_name = cluster_arn.split("/")[-1] if cluster_arn else "unknown_cluster"
        path = f"{s3_prefix}container_cost/agent_job_logs/year={start_time.year}/month={start_time.month}/day={start_time.day}/hour={start_time.hour}/cluster_name={cluster_name}"

        s3_key = f"{path}/agent_job.log"
        s3.upload_file(Filename=self.log_path, Bucket=s3_bucket, Key=s3_key)

    def export_nopscost_data(self, s3_bucket, s3_prefix, cluster_arn, start_time):
        try:
            cluster_name = cluster_arn.split("/")[-1] if cluster_arn else "unknown_cluster"
            processed_data = main_command()
            path = f"s3://{s3_bucket}/{s3_prefix}container_cost/nops_cost/year={start_time.year}/month={start_time.month}/day={start_time.day}/cluster_name={cluster_name}/v{SCHEMA_VERSION_DATE}_k8s_nopscost.parquet"
            if processed_data is not None and not processed_data.empty:
                print(f"\nSaving nops-cost data to {path}")
                processed_data.to_parquet(path)
        except Exception as e:
            print("\nError while exporting nopscost data: {}".format(str(e)))

    def export_data(self, s3, s3_bucket, s3_prefix, cluster_arn, start_time):
        tmp_path = f"/tmp/year={start_time.year}/month={start_time.month}/day={start_time.day}/hour={start_time.hour}/"
        cluster_name = cluster_arn.split("/")[-1] if cluster_arn else "unknown_cluster"
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
        for klass in collect_klass:
            try:
                instance = klass(cluster_arn=cluster_arn)
                FILE_PREFIX = klass.FILE_PREFIX
                path = f"{s3_prefix}container_cost/{FILE_PREFIX}/year={start_time.year}/month={start_time.month}/day={start_time.day}/hour={start_time.hour}/cluster_name={cluster_name}"
                tmp_file = f"{tmp_path}{klass.FILENAME}"
                instance.convert_to_table_and_save(
                    period="last_hour", current_time=start_time, step="5m", filename=tmp_file
                )
                s3_key = f"{path}/{klass.FILENAME}"
                s3.upload_file(Filename=tmp_file, Bucket=s3_bucket, Key=s3_key)
                print(f"File {tmp_file} successfully uploaded to s3://{s3_bucket}/{s3_key}")
            except Exception as e:
                import traceback

                traceback_info = traceback.format_exc()
                print(traceback_info)
                print(f"Error when processing {type(klass)} {str(e)}")
            finally:
                # Trying to remove the tmp file
                try:
                    os.remove(tmp_file)
                except Exception as e:
                    print(f"Error when removing {tmp_file} {str(e)}")

    def handle(self, *args, **options):
        s3 = boto3.client("s3")
        s3_bucket = settings.AWS_S3_BUCKET
        s3_prefix = settings.AWS_S3_PREFIX
        cluster_arn = settings.NOPS_K8S_AGENT_CLUSTER_ARN
        start_date_str = options["start_date"]
        end_date_str = options["end_date"]

        if start_date_str and end_date_str:
            start_date = dt.datetime.strptime(start_date_str, "%Y-%m-%d")
            end_date = dt.datetime.strptime(end_date_str, "%Y-%m-%d") + dt.timedelta(days=1)
            for single_date in (start_date + dt.timedelta(n) for n in range(int((end_date - start_date).days))):
                for hour in range(24):
                    current_time = single_date + dt.timedelta(hours=hour)
                    with DualOutput(self.log_path):
                        self.export_data(s3, s3_bucket, s3_prefix, cluster_arn, current_time)

        else:
            now = dt.datetime.now()
            with DualOutput(self.log_path):
                self.export_nopscost_data(s3_bucket, s3_prefix, cluster_arn, now)
                self.export_data(s3, s3_bucket, s3_prefix, cluster_arn, now)

        self.upload_job_log(s3, s3_bucket, s3_prefix, cluster_arn, now)
        try:
            os.remove(self.log_path)
        except Exception as e:
            print(f"Error when removing {self.log_path} {str(e)}")