import uuid
from collections import defaultdict
from datetime import datetime

from nops_k8s_agent.libs.base_usage import BaseUsage


class PodUsage(BaseUsage):
    def get_owner_dict(self) -> dict:
        # return a dictionary of owner
        # There is some kind of nested owner so we need to get 2 time to get the base name
        owner_types = {
            "Job": "sum(avg_over_time(kube_job_owner[{start_time}])) by (job_name, owner_name, owner_kind, namespace)",
            "ReplicaSet": "sum(avg_over_time(kube_replicaset_owner[{start_time}])) by (replicaset, owner_name, owner_kind, namespace)",
            "ReplicationController": "sum(avg_over_time(kube_replicationcontroller_owner[{start_time}])) by (replicationcontroller, owner_name, owner_kind, namespace)",
        }
        owner_map = {"Job": "job_name", "ReplicationController": "replicationcontroller", "ReplicaSet": "replicaset"}
        owner_dict = defaultdict(lambda: defaultdict(dict))
        for key, query_template in owner_types.items():
            metrics_params = {"start_time": "30m"}
            metrics_query = self.build_metrics_query(query_template, input_params=metrics_params)
            responses = self.prom_client.custom_query(query=metrics_query)
            for metric_response in responses:
                owner_name = metric_response["metric"]["owner_name"]
                namespace = metric_response["metric"]["namespace"]
                name = metric_response["metric"][owner_map.get(key)]
                if owner_name == "<none>":
                    owner_name = None
                owner_dict[key][namespace][name] = owner_name
        return owner_dict

    def get_status_dict(self) -> dict:
        response = self.prom_client.custom_query(
            query="avg(kube_pod_container_status_running{}) by (pod, namespace)[30m:30m]"
        )
        status_dict = defaultdict(dict)
        for metric_response in response:
            namespace = metric_response["metric"]["namespace"]
            name = metric_response["metric"]["pod"]
            status_dict[namespace][name] = self.get_metric_value(metric_response)
        return status_dict

    def get_pod_dict(self) -> dict:
        # Expect retuning is a list of pod with pod name
        response = self.prom_client.custom_query(query="avg_over_time(kube_pod_info[30m])")
        pod_dict = {}
        owner_dict = self.get_owner_dict()
        status_dict = self.get_status_dict()
        for pod_record in response:
            record = pod_record["metric"]
            uid = record["uid"]
            if record["created_by_name"] and record["created_by_name"] != "<none>":
                owner = (
                    owner_dict.get(record["created_by_kind"], {}).get(record["created_by_name"], {}).get(record["pod"])
                )
                if owner is None:
                    owner = record["created_by_name"]
            else:
                owner = ""
            status = status_dict.get(record["namespace"], {}).get(record["pod"])
            pod_dict[uid] = {
                "uid": uid,
                "pod": record["pod"],
                "host_ip": record["host_ip"],
                "pod_ip": record.get("pod_ip", ""),
                "namespace": record["namespace"],
                "basename": owner,
                "status": status,
                "created_by_kind": record["created_by_kind"],
                "created_by_name": record["created_by_name"],
            }
        return pod_dict

    def get_events(self) -> list:
        now = datetime.utcnow()
        final_result = []
        pod_dict = self.get_pod_dict()
        for key in pod_dict:
            metadata = {
                "cluster_id": self.cluster_id,
                "event_id": str(uuid.uuid4()),
                "cloud": "aws",
                "uid": key,
                "event_type": "k8s_pod_usage",
                "extraction_time": now.isoformat(),
            }
            result = pod_dict.get(key, {}) | metadata
            final_result.append(result)
        return final_result
