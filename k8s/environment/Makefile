.PHONY: kafka postgres nginx setup

KUBECTL?=kubectl
HELM?=helm
POSTGRES_VERSION?=11


setup:
	$(HELM) repo add stable https://kubernetes-charts.storage.googleapis.com
	$(HELM) repo add incubator http://storage.googleapis.com/kubernetes-charts-incubator

kafka: setup
	$(HELM) upgrade -i kafka -f kafka.yaml incubator/kafka

postgres: setup
	$(HELM) upgrade -i postgres -f postgres.yaml stable/postgresql

postgres-pwd:
	@echo POSTGRES_PASSWORD=$(shell kubectl get secret --namespace default postgres-postgresql -o jsonpath="{.data.postgresql-password}" | base64 --decode)

redis: setup
	$(HELM) upgrade -i redis-ha -f redis.yaml stable/redis-ha

metrics-server: setup
	$(HELM) upgrade -i metrics-server -f metrics-server.yaml stable/metrics-server

nginx:
	@echo "Deploying NGINX ingress controller on Docker4Mac "
	$(KUBECTL) apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/nginx-0.30.0/deploy/static/mandatory.yaml
	$(KUBECTL) apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/nginx-0.30.0/deploy/static/provider/cloud-generic.yaml

toolbox:
	$(KUBECTL) run --generator=run-pod/v1 -i --tty toolbox --image=gcr.io/google-containers/toolbox -- sh
