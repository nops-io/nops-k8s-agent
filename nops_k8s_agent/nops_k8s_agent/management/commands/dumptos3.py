import datetime as dt
import logging
import os
import sys

from django.conf import settings
from django.core.management.base import BaseCommand

import boto3

from nops_k8s_agent.container_cost.base_labels import BaseLabels
from nops_k8s_agent.container_cost.container_metrics import ContainerMetrics
from nops_k8s_agent.container_cost.deployment_metrics import DeploymentMetrics
from nops_k8s_agent.container_cost.job_metrics import JobMetrics
from nops_k8s_agent.container_cost.node_metadata import NodeMetadata
from nops_k8s_agent.container_cost.node_metrics import NodeMetrics
from nops_k8s_agent.container_cost.nopscost.nopscost_parquet_exporter import main_command
from nops_k8s_agent.container_cost.persistentvolume_metrics import PersistentvolumeMetrics
from nops_k8s_agent.container_cost.persistentvolumeclaim_metrics import PersistentvolumeclaimMetrics
from nops_k8s_agent.container_cost.pod_metrics import PodMetrics
from nops_k8s_agent.settings import SCHEMA_VERSION_DATE
from nops_k8s_agent.utils import derive_suffix_from_settings


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
        self.close()
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__


class Command(BaseCommand):
    log_path = "/tmp/logfile.log"
    retry_log_path = "/tmp/retry_logfile.log"
    errors = []

    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.setup_logging()

    def setup_logging(self, log_path=None):
        self.logger.setLevel(logging.DEBUG)

        if log_path is None:
            log_path = self.log_path

        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        ch_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        ch.setFormatter(ch_formatter)

        fh = logging.FileHandler(log_path)
        fh.setLevel(logging.DEBUG)
        fh_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        fh.setFormatter(fh_formatter)

        self.logger.handlers = []
        self.logger.addHandler(ch)
        self.logger.addHandler(fh)

    def handle(self, *args, **options):
        s3 = boto3.client("s3")
        s3_bucket = settings.AWS_S3_BUCKET
        s3_prefix = settings.AWS_S3_PREFIX
        cluster_arn = settings.NOPS_K8S_AGENT_CLUSTER_ARN
        module_to_collect = options["module_to_collect"]
        start_date_str = options["start_date"]
        end_date_str = options["end_date"]
        retry = options.get("retry", False)
        modules_to_retry = options.get("modules_to_retry", [])
        now = dt.datetime.now()

        log_path = self.retry_log_path if retry else self.log_path
        self.setup_logging(log_path)
        with DualOutput(log_path):
            if modules_to_retry:
                self.logger.info(f"Retrying for {modules_to_retry}")
            try:
                if start_date_str and end_date_str:
                    self.process_date_range(
                        s3,
                        s3_bucket,
                        s3_prefix,
                        cluster_arn,
                        module_to_collect,
                        start_date_str,
                        end_date_str,
                        modules_to_retry,
                    )
                else:
                    self.process_current_data(
                        s3, s3_bucket, s3_prefix, cluster_arn, module_to_collect, now, modules_to_retry
                    )
            except Exception:
                import traceback

                self.logger.debug(f"Exception on handle call: {traceback.format_exc()}")
            finally:
                self.upload_job_log(s3, s3_bucket, s3_prefix, cluster_arn, now, module_to_collect, retry)
                self.cleanup_log_file(log_path)
                if self.errors:
                    if not retry:
                        self.logger.debug(f"Failed to finish all exports: {self.errors}")
                        self.logger.error(f"Errors occurred during exports: {self.errors}")
                        self.logger.info("Failed to export some modules, retrying")
                        options.update({"retry": True, "modules_to_retry": self.errors})
                        self.flush_and_retry(*args, **options)
                    else:
                        self.logger.info("Failed on retry, exiting")
                        self.cleanup_log_file(self.retry_log_path)
                        sys.exit(1)

    def flush_and_retry(self, *args, **options):
        for handler in self.logger.handlers:
            handler.flush()
        self.handle(*args, **options)

    def process_date_range(
        self, s3, s3_bucket, s3_prefix, cluster_arn, module_to_collect, start_date_str, end_date_str, modules_to_retry
    ):
        start_date = dt.datetime.strptime(start_date_str, "%Y-%m-%d")
        end_date = dt.datetime.strptime(end_date_str, "%Y-%m-%d") + dt.timedelta(days=1)
        self.logger.info(f"Exporting data for {start_date} until {end_date}")
        for single_date in (start_date + dt.timedelta(n) for n in range(int((end_date - start_date).days))):
            self.process_single_date(
                s3, s3_bucket, s3_prefix, cluster_arn, module_to_collect, single_date, modules_to_retry
            )

    def process_single_date(
        self, s3, s3_bucket, s3_prefix, cluster_arn, module_to_collect, single_date, modules_to_retry
    ):
        self.logger.debug(f"Processing single date: {single_date}")
        if module_to_collect != "nopscost":
            self.export_nopscost_data(s3, s3_bucket, s3_prefix, cluster_arn, single_date)
            for hour in range(24):
                current_time = single_date + dt.timedelta(hours=hour)
                self.process_hourly_data(
                    s3, s3_bucket, s3_prefix, cluster_arn, module_to_collect, current_time, modules_to_retry
                )
        else:
            self.export_nopscost_data(s3, s3_bucket, s3_prefix, cluster_arn, single_date)

    def process_hourly_data(
        self, s3, s3_bucket, s3_prefix, cluster_arn, module_to_collect, current_time, modules_to_retry
    ):
        if not module_to_collect or module_to_collect == "":
            for klass_name in self.yield_all_klass():
                if not modules_to_retry or klass_name in modules_to_retry:
                    self.export_data(s3, s3_bucket, s3_prefix, cluster_arn, current_time, klass_name)
        else:
            if not modules_to_retry or module_to_collect in modules_to_retry:
                self.export_data(s3, s3_bucket, s3_prefix, cluster_arn, current_time, module_to_collect)

    def process_current_data(self, s3, s3_bucket, s3_prefix, cluster_arn, module_to_collect, now, modules_to_retry):
        self.logger.debug(f"Processing current data with module: {module_to_collect}")
        if not module_to_collect or module_to_collect == "":
            self.export_nopscost_data(s3, s3_bucket, s3_prefix, cluster_arn, now)
            for klass_name in self.yield_all_klass():
                if not modules_to_retry or klass_name in modules_to_retry:
                    self.export_data(s3, s3_bucket, s3_prefix, cluster_arn, now, klass_name)
        else:
            if module_to_collect == "nopscost":
                self.export_nopscost_data(s3, s3_bucket, s3_prefix, cluster_arn, now)
            else:
                if isinstance(module_to_collect, list):
                    for klass in module_to_collect:
                        if not modules_to_retry or klass in modules_to_retry:
                            self.export_data(s3, s3_bucket, s3_prefix, cluster_arn, now, klass)
                else:
                    if not modules_to_retry or module_to_collect in modules_to_retry:
                        self.export_data(s3, s3_bucket, s3_prefix, cluster_arn, now, module_to_collect)

    def upload_job_log(self, s3, s3_bucket, s3_prefix, cluster_arn, start_time, module_to_collect, retry):
        cluster_name = cluster_arn.split("/")[-1] if cluster_arn else "unknown_cluster"
        if not module_to_collect:
            module_to_collect = "ALL"
        path = f"{s3_prefix}container_cost/agent_job_logs/{module_to_collect}/year={start_time.year}/month={start_time.month}/day={start_time.day}/hour={start_time.hour}/cluster_name={cluster_name}"
        s3_key = f"{path}/agent_job.log" if not retry else f"{path}/agent_job_retry.log"
        s3.upload_file(Filename=self.retry_log_path if retry else self.log_path, Bucket=s3_bucket, Key=s3_key)
        self.logger.info(f"Uploaded job log to {s3_bucket}/{s3_key}")

    def cleanup_log_file(self, log_path):
        try:
            os.remove(log_path)
        except Exception as e:
            self.logger.debug(f"Error when removing {log_path}: {e}")

    def add_arguments(self, parser):
        parser.add_argument("--module-to-collect", type=str, help="Name of the metric module to collect")
        parser.add_argument("--start-date", type=str, help="Start date in YYYY-MM-DD format")
        parser.add_argument("--end-date", type=str, help="End date in YYYY-MM-DD format")

    def _get_s3_key(self, s3_prefix, start_time, cluster_arn):
        cluster_name = cluster_arn.split("/")[-1] if cluster_arn else "unknown_cluster"
        s3_key = f"{s3_prefix}container_cost/nops_cost/year={start_time.year}/month={start_time.month}/day={start_time.day}/cluster_name={cluster_name}/v{SCHEMA_VERSION_DATE}_k8s_nopscost-{derive_suffix_from_settings()}.parquet"
        return s3_key

    def _is_nops_cost_exported(self, s3_bucket, s3_prefix, start_time, cluster_arn):
        s3 = boto3.client("s3")
        s3_key = self._get_s3_key(s3_prefix, start_time, cluster_arn)

        response = s3.list_objects_v2(Bucket=s3_bucket, Prefix=s3_key)
        for obj in response.get("Contents", []):
            if obj["Key"] == s3_key:
                return True
        return False

    def _should_backfill(self, s3, s3_bucket, s3_prefix, start_time, cluster_arn):
        backfill_windows = list(range(1, 24, 6))
        if start_time.hour not in backfill_windows:
            self.logger.info("Skipping backfill check.")
            self.logger.info(f"Current hour: {start_time.hour}")
            self.logger.info(f"Backfill local hours: {backfill_windows}")
            return False
        backfill_days = 3
        # List objects for the entire month
        s3_key_prefix = f"{s3_prefix}container_cost/nops_cost/year={start_time.year}/month={start_time.month}/"
        response = s3.list_objects_v2(Bucket=s3_bucket, Prefix=s3_key_prefix)

        existing_keys = set(obj["Key"] for obj in response.get("Contents", []))

        for i in range(0, backfill_days):
            backfill_date = start_time - dt.timedelta(days=i)
            s3_key = self._get_s3_key(s3_prefix, backfill_date, cluster_arn)
            if s3_key not in existing_keys:
                return backfill_date

        return None

    def _make_nopscost_exporting_request(self, s3_bucket, s3_prefix, cluster_arn, window_start, window_end):
        try:
            processed_data = main_command(window_start=window_start, window_end=window_end)
            path = f"s3://{s3_bucket}/{self._get_s3_key(s3_prefix, window_start, cluster_arn)}"
            if processed_data is not None and not processed_data.empty:
                processed_data.to_parquet(path)
            self.logger.info(
                f"nops_cost export successful for {window_start.year}-{window_start.month}-{window_start.day}"
            )
        except Exception as e:
            self.logger.debug(f"Error while exporting nopscost data: {e}")
            self.errors.append("nops_cost")

    def export_nopscost_data(self, s3, s3_bucket, s3_prefix, cluster_arn, start_time):
        try:
            backfill_date = self._should_backfill(s3, s3_bucket, s3_prefix, start_time, cluster_arn)
            if backfill_date:
                self.logger.info(f"Backfilling for {backfill_date}")
                window_start = backfill_date.replace(hour=0, minute=0, second=0, microsecond=0)
                window_end = backfill_date.replace(hour=23, minute=59, second=59, microsecond=0)
                self._make_nopscost_exporting_request(s3_bucket, s3_prefix, cluster_arn, window_start, window_end)
                return
            if self._is_nops_cost_exported(s3_bucket, s3_prefix, start_time, cluster_arn):
                self.logger.info(f"File for nops_cost for {start_time} already exported. Skipping export.")
                return
        except Exception as e:
            self.logger.debug(f"Error while checking if nops-cost data is exported: {e}")
            self.logger.error(
                f"Failed to check if nops-cost data is exported for {start_time}\nProceeding with export."
            )
            self.errors.append("nops_cost")
        window_start, window_end = None, None
        self._make_nopscost_exporting_request(s3_bucket, s3_prefix, cluster_arn, window_start, window_end)

    def export_data(self, s3, s3_bucket, s3_prefix, cluster_arn, start_time, klass_name):
        tmp_path = f"/tmp/year={start_time.year}/month={start_time.month}/day={start_time.day}/hour={start_time.hour}/"
        cluster_name = cluster_arn.split("/")[-1] if cluster_arn else "unknown_cluster"
        collect_klass = {
            "base_labels": BaseLabels,
            "container_metrics": ContainerMetrics,
            "deployment_metrics": DeploymentMetrics,
            "job_metrics": JobMetrics,
            "node_metrics": NodeMetrics,
            "pv_metrics": PersistentvolumeMetrics,
            "pvc_metrics": PersistentvolumeclaimMetrics,
            "pod_metrics": PodMetrics,
            "node_metadata": NodeMetadata,
        }
        try:
            klass = collect_klass[klass_name]
            instance = klass(cluster_arn=cluster_arn)
            FILE_PREFIX = klass.FILE_PREFIX
            path = f"{s3_prefix}container_cost/{FILE_PREFIX}/year={start_time.year}/month={start_time.month}/day={start_time.day}/hour={start_time.hour}/cluster_name={cluster_name}"
            tmp_file = f"{tmp_path}{klass.FILENAME}"
            instance.convert_to_table_and_save(
                period="last_hour", current_time=start_time, step="5m", filename=tmp_file
            )
            s3_key = f"{path}/{klass.FILENAME}"
            s3.upload_file(Filename=tmp_file, Bucket=s3_bucket, Key=s3_key)
            self.logger.debug(f"File {tmp_file} successfully uploaded to s3://{s3_bucket}/{s3_key}")
            self.logger.info(f"Successfully exported {klass_name}")
        except KeyError:
            self.logger.error(f"Wrong metric module name: {klass_name}")
            return
        except Exception as e:
            import traceback

            traceback_info = traceback.format_exc()
            self.logger.info(f"Failed to export {klass_name}")
            self.logger.debug(traceback_info)
            self.logger.debug(f"Error when processing {type(klass)} {e}")
            self.errors.append(f"{klass_name}")
        finally:
            try:
                os.remove(tmp_file)
            except Exception as e:
                self.logger.error(f"Error when removing {tmp_file}: {e}")

    def yield_all_klass(self):
        collect_klass = [
            "base_labels",
            "container_metrics",
            "deployment_metrics",
            "job_metrics",
            "node_metrics",
            "pv_metrics",
            "pvc_metrics",
            "pod_metrics",
            "node_metadata",
        ]
        for klass in collect_klass:
            yield klass
