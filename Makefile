run: create_namespace
	TILT_PORT=10355 tilt up
down:
	tilt down

dev_infra: infra install_precommit create_namespace
ci_infra: infra create_namespace create_secret

infra:
	k3d cluster create nops-local --registry-create nops-local-registry:127.0.0.1:5001 --kubeconfig-update-default --kubeconfig-switch-context --api-port 0.0.0.0:50956

exec:
	kubectl -n nops-k8s-agent exec -it deploy/nops-k8s-agent -- bash
shell:
	kubectl -n nops-k8s-agent exec -it deploy/nops-k8s-agent -- python ./manage.py shell_plus --ipython
test:
	kubectl -n nops-k8s-agent exec -it deploy/nops-k8s-agent -- pytest
test_prometheus:
	kubectl -n nops-k8s-agent exec -it deploy/nops-k8s-agent -- pytest --runslow

test_debug:
	kubectl -n nops-k8s-agent exec -it deploy/nops-k8s-agent -- pytest -s -vvv

create_secret:
	kubectl create secret generic nops-k8s-agent --from-literal=aws_access_key_id=ABCDEF --from-literal=aws_secret_access_key=abcdef -n nops-k8s-agent

install_precommit:
	pre-commit install > /dev/null

create_namespace:
	kubectl create namespace nops-k8s-agent || true
cp:
	@POD_NAME=$$(kubectl get pods -n nops-k8s-agent -l app=nops-k8s-agent -o jsonpath="{.items[0].metadata.name}") && \
	kubectl cp nops-k8s-agent/$$POD_NAME:$(filename) ./$(filename)
