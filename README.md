# action-man-faust


Setup environment with `make kafka postgres redis metrics-server nginx` inside `k8s/environment`

Bring up the apps with `skaffold dev`


POSTGRES password will have to be checked with `make postgres-pwd` always inside the `k8s/environment` and you will need to recreate the secret inside the `secret.yaml` files in `k8s/kafka` and `k8s/web`
