/workspace/manage.py send_healthcheck || true
/workspace/manage.py send_metadata || true
/workspace/manage.py send_metrics -f high
