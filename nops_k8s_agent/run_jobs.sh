/workspace/manage.py send_healthcheck || true
/workspace/manage.py send_metadata || true
/workspace/manage.py send_metrics -f high || true
/workspace/manage.py send_metrics -f medium || true
/workspace/manage.py send_metrics -f low
