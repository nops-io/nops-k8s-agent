#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys

import nops_k8s_agent.management.commands.rightsize
from nops_k8s_agent.rightsizing import Container


def main():
    """Run administrative tasks."""
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nops_k8s_agent.settings")
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == "__main__":
    container = Container()
    container.init_resources()
    container.wire(modules=[nops_k8s_agent.management.commands.rightsize])
    main()
