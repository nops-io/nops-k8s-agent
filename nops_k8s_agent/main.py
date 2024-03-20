import os

os.system("hypercorn --config hypercorn.toml nops_k8s_agent.asgi:application")#
