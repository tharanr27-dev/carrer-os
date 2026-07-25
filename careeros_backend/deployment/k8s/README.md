Kubernetes manifests for CareerOS AI

Apply in order (adjust values for production):

kubectl apply -f namespace.yaml
kubectl apply -f secrets-example.yaml
kubectl apply -f postgres-statefulset.yaml
kubectl apply -f redis-deployment.yaml
kubectl apply -f qdrant-deployment.yaml
kubectl apply -f api-deployment.yaml
kubectl apply -f api-service.yaml
kubectl apply -f ingress.yaml
kubectl apply -f prometheus-rules.yaml
kubectl apply -f grafana-configmap.yaml

Notes:
- Replace `secrets-example.yaml` with secrets from your secret manager.
- Use StatefulSet with persistent volumes for Postgres in production and consider managed DB services.
- Exchange emptyDir volumes for PVCs backed by appropriate StorageClasses.
- Use Helm/Kustomize for templating and lifecycle management.
