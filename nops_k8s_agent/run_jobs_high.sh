/workspace/manage.py send_healthcheck || true
/workspace/manage.py send_metadata || true
/workspace/manage.py send_metrics -f k8s_node_usage || true
/workspace/manage.py send_metrics -f k8s_pod_usage || true
/workspace/manage.py send_metrics -f k8s_container_usage
