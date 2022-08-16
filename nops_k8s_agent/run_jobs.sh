/workspace/manage.py send_healthcheck || true
/workspace/manage.py send_metadata || true
/workspace/manage.py send_metrics high || true
/workspace/manage.py send_metrics medium || true
/workspace/manage.py send_metrics low
