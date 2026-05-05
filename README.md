# Task API Platform

FastAPI + PostgreSQL API project for practicing Docker, docker-compose, Kubernetes YAML deployment, and Helm chart packaging.

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- Docker
- Docker Compose
- GitHub

## Project Structure

```text
task-api-platform/
├── app/
│   └── main.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Local Run
Create and activate a Python virtual environment.
```Bash
python3 -m venv .venv
source .venv/bin/activate
```
Install dependencies.
```Bash
pip install -r requirements.txt
```
Run the FastAPI server locally.
```
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Health Check
```bash
curl http://localhost:8000/healthz
```
Expected resoponse:
```JSON
{"status":"ok"}
```

## Run with Docker
Build the Docker image.
```Bash
docker build -t task-api:local .
```

Run the API container
```Bash
docker run --rm -p 8000:8000 task-api:local
```

Check the API.
```Bash
curl http://localhost:8000/healthz
```

## Run with Docker Compose
Create a local environment file.
```Bash
cp .env.example .env
```
Start the API and PostgreSQL containers.
```Bash
docker compose up --build
```
Check running containers.
```Bash
docker compose ps
```
Check the API.
```Bash
curl http://localhost:8000/healthz
```
Stop containers.
```Bash
docker compose down
```
Stop containers and remove PostgreSQL volume data.
```Bash
docker compose down -v
```


## Branch Strategy
- `main`: stable branch
- `dev`: integration branch
- `feature/*`: feature branches

Example workflow:
```Bash
git checkout dev
git pull origin dev
git checkout -b feature/week1-add-dockerfile
```

After changes:
```Bash
git status
git add .
git commit -m "Add Dockerfile for FastAPI app"
git push -u origin feature/week1-add-dockerfile
```

Then create a Pull Request on GitHub:
```text
base: dev
compare: compare: feature/week1-add-dockerfile
```

## Run on Kubernetes with Minikube

Start Minikube.

```bash
minikube start --driver=docker
```

Build the API image.
```bash
docker build -t task-api:local .
```

Load the image into Minikube.
```bash
minikube image load task-api:local
```

Enable Ingress addon.
```Bash
minikube addons enable ingress
```

Check that the Ingress controller is running:
```bash
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
```


Apply Kubernetes manifests.
```bash
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

Check resources.
```bash
kubectl get all -n task-api
kubectl get ingress -n task-api
kubectl get endpoints -n task-api task-api
```

Test with port-forward.
Use port-forward to expose the Ingress controller locally:
```bash
kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80
```

Health check.
```bash
curl http://task-api.local:8080/healthz
```

Expected response:
```JSON
{"status":"ok"}
```


## Helm Deployment

Lint
```bash
helm lint ./helm/task-api
```

Render manifests
```bash
helm template task-api ./helm/task-api \
  -n task-api-dev \
  -f ./helm/task-api/values.dev.yaml
```
Install
```bash
helm install task-api ./helm/task-api \
  -n task-api-dev \
  --create-namespace \
  -f ./helm/task-api/values.dev.yaml
```
Check resources
```bash
helm list -n task-api-dev
kubectl get all -n task-api-dev
```
Test with Service port-forward
```bash
kubectl port-forward svc/task-api 8000:8000 -n task-api-dev
curl http://localhost:8000/healthz
```
Test with Ingress Controller port-forward
```bash
kubectl -n ingress-nginx port-forward svc/ingress-nginx-controller 8080:80
curl -H "Host: task-api.dev.local" http://localhost:8080/healthz
```
Upgrade
```bash
helm upgrade task-api ./helm/task-api \
  -n task-api-dev \
  -f ./helm/task-api/values.dev.yaml
```
Rollback
```bash
helm history task-api -n task-api-dev
helm rollback task-api 1 -n task-api-dev
```
Uninstall
```bash
helm uninstall task-api -n task-api-dev
```
