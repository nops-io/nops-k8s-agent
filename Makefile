
run: create_namespace
	TILT_PORT=10355 tilt up
down:
	tilt down

dev_infra: infra install_precommit create_namespace
ci_infra: infra create_namespace

infra:
	k3d cluster create nops-local --registry-create nops-local-registry:127.0.0.1:5001 --kubeconfig-update-default --kubeconfig-switch-context --api-port 0.0.0.0:50956

exec:
	kubectl -n nops-k8s-agent exec -it deploy/nops-k8s-agent -- bash
shell:
	kubectl -n nops-k8s-agent exec -it deploy/nops-k8s-agent -- python ./manage.py shell_plus --ipython
test:
	kubectl -n nops-k8s-agent exec -it deploy/nops-k8s-agent -- pytest -n 4

server:
	kubectl exec -n nops-k8s-agent -it deploy/nops-k8s-agent -- python3 main.py

test_debug:
	kubectl -n nops-k8s-agent exec -it deploy/nops-k8s-agent -- pytest -s -vvv

install_precommit:
	pre-commit install > /dev/null

create_namespace:
	kubectl create namespace nops-k8s-agent || true
