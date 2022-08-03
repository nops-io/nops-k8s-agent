from django.core.management import call_command


def test_send_command():
    call_command("send_metadata")
    call_command("send_metrics")
