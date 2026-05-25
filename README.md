# Task API Platform

FastAPI + PostgreSQL 기반의 Task API 프로젝트입니다.  
이 프로젝트는 Docker, Docker Compose, Kubernetes YAML, Helm Chart, ECR, GitHub Actions, ArgoCD 기반 GitOps 배포 흐름을 단계적으로 학습하기 위한 실습용 애플리케이션입니다.

---

## 프로젝트 목표

이 repository의 주요 목표는 단순히 API 서버를 만드는 것이 아니라, 애플리케이션을 컨테이너화하고 Kubernetes 환경에 배포한 뒤, 최종적으로 CI/CD와 GitOps를 이용해 자동 배포 파이프라인을 구성하는 것입니다.

현재까지 구성한 흐름은 다음과 같습니다.

```text
FastAPI 코드 작성
  ↓
Docker 이미지 빌드
  ↓
ECR에 이미지 Push
  ↓
Helm Chart로 Kubernetes 배포 정의
  ↓
GitHub Actions로 이미지 빌드/Push 자동화
  ↓
gitops-argocd repo의 image tag 자동 업데이트
  ↓
ArgoCD Auto Sync
  ↓
EKS에 새 버전 자동 배포
```

---

## Repository 역할

| Repository | 역할 |
|---|---|
| `task-api-platform` | 애플리케이션 코드, Dockerfile, Helm Chart, GitHub Actions workflow 관리 |
| `task-api-gitops` | Week 5 FluxCD 기반 GitOps 학습 결과 보존 |
| `gitops-argocd` | Week 6 ArgoCD 기반 GitOps 배포 상태 관리 |

`task-api-platform`은 애플리케이션 개발 repository이고, `gitops-argocd`는 EKS에 어떤 image tag를 배포할지 선언하는 GitOps repository입니다.

---

## 프로젝트 구조

현재 주요 구조는 다음과 같습니다.

```text
task-api-platform/
├── app/
│   ├── config/
│   │   └── database.py
│   ├── controllers/
│   │   ├── health_controller.py
│   │   └── task_controller.py
│   ├── models/
│   │   └── task_model.py
│   ├── repositories/
│   │   └── task_repository.py
│   ├── routes/
│   │   ├── health_routes.py
│   │   └── task_routes.py
│   ├── services/
│   │   ├── health_service.py
│   │   └── task_service.py
│   └── main.py
├── helm/
│   └── task-api/
│       ├── Chart.yaml
│       ├── Chart.lock
│       ├── charts/
│       │   └── postgresql-16.4.5.tgz
│       ├── templates/
│       │   ├── _helpers.tpl
│       │   ├── configmap.yaml
│       │   ├── deployment.yaml
│       │   ├── ingress.yaml
│       │   ├── secret.yaml
│       │   └── service.yaml
│       ├── values.yaml
│       ├── values.dev.yaml
│       ├── values.eks.yaml
│       └── values.prod.yaml
├── k8s/
│   ├── deployment.yaml
│   ├── ingress.yaml
│   ├── namespace.yaml
│   └── service.yaml
├── .github/
│   └── workflows/
│       └── ci-cd.yaml
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

> `__pycache__/`, `*.pyc`, `.env`, `.venv/` 등은 Git에 포함하지 않습니다.

---

## 애플리케이션 구조

이 프로젝트는 단일 `main.py` 중심 구조에서 역할별로 코드를 분리했습니다.

| 디렉터리 | 역할 |
|---|---|
| `app/main.py` | FastAPI 애플리케이션 생성, router 등록, startup 처리 |
| `app/config/` | DB 연결 설정 |
| `app/routes/` | API route 정의 |
| `app/controllers/` | 요청을 받아 service 호출 |
| `app/services/` | 비즈니스 로직 처리 |
| `app/repositories/` | DB 접근 로직 |
| `app/models/` | 데이터 모델 정의 |

이 구조를 사용하면 API 요청 처리, 비즈니스 로직, DB 접근 로직을 분리할 수 있어 테스트와 유지보수가 쉬워집니다.

---

## 로컬 실행

### Python 가상환경 생성

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 의존성 설치

```bash
pip install -r requirements.txt
```

### FastAPI 서버 실행

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Health Check

```bash
curl http://localhost:8000/healthz
```

예상 응답:

```json
{"status":"ok"}
```

---

## Docker 실행

### Docker 이미지 빌드

```bash
docker build -t task-api:local .
```

### API 컨테이너 단독 실행

```bash
docker run --rm -p 8000:8000 task-api:local
```

단, 현재 애플리케이션은 startup 시점에 PostgreSQL 연결을 시도합니다.  
따라서 DB 없이 API 컨테이너만 단독 실행하면 DB hostname을 찾지 못해 실패할 수 있습니다.

로컬에서 API와 PostgreSQL을 함께 테스트하려면 Docker Compose 사용을 권장합니다.

---

## Docker Compose 실행

### API + PostgreSQL 실행

```bash
docker compose up --build
```

백그라운드 실행:

```bash
docker compose up -d --build
```

### 상태 확인

```bash
docker compose ps
```

### 로그 확인

```bash
docker compose logs -f
```

### Health Check

```bash
curl http://localhost:8000/healthz
```

### 종료

```bash
docker compose down
```

PostgreSQL volume까지 제거:

```bash
docker compose down -v
```

---

## Kubernetes YAML 배포

Minikube 또는 Kubernetes 클러스터에 기본 manifest를 적용할 수 있습니다.

### Namespace 생성

```bash
kubectl apply -f k8s/namespace.yaml
```

### Deployment / Service / Ingress 적용

```bash
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/ingress.yaml
```

### 리소스 확인

```bash
kubectl get all -n task-api
kubectl get ingress -n task-api
```

---

## Helm 배포

이 프로젝트는 Helm Chart를 통해 Kubernetes 리소스를 패키징합니다.

### Helm Chart Lint

```bash
helm lint ./helm/task-api
```

### Template 렌더링 확인

```bash
helm template task-api ./helm/task-api \
  -n task-api-dev \
  -f ./helm/task-api/values.dev.yaml
```

### Helm Install

```bash
helm install task-api ./helm/task-api \
  -n task-api-dev \
  --create-namespace \
  -f ./helm/task-api/values.dev.yaml
```

### 배포 확인

```bash
helm list -n task-api-dev
kubectl get all -n task-api-dev
```

### Port Forward 테스트

```bash
kubectl port-forward svc/task-api 8000:8000 -n task-api-dev
curl http://localhost:8000/healthz
```

### Upgrade

```bash
helm upgrade task-api ./helm/task-api \
  -n task-api-dev \
  -f ./helm/task-api/values.dev.yaml
```

### Rollback

```bash
helm history task-api -n task-api-dev
helm rollback task-api 1 -n task-api-dev
```

### Uninstall

```bash
helm uninstall task-api -n task-api-dev
```

---

## CI/CD + 이미지 자동 빌드

코드 변경 이후 수동으로 Docker 이미지를 빌드하고 배포하지 않아도, GitHub Actions와 ArgoCD를 통해 EKS에 자동 반영되는 파이프라인을 만드는 것입니다.

최종 흐름은 다음과 같습니다.

```text
task-api-platform 코드 push
  ↓
GitHub Actions 실행
  ↓
Python syntax check
  ↓
Docker image build
  ↓
Amazon ECR push
  ↓
gitops-argocd repo의 image tag 자동 변경
  ↓
ArgoCD Auto Sync
  ↓
EKS에 새 이미지 자동 배포
```

---

## 주요 개념 정리

### CI/CD

CI/CD는 코드 변경 이후 테스트, 빌드, 배포 과정을 자동화하는 방식입니다.

| 개념 | 설명 | 이번 프로젝트에서의 역할 |
|---|---|---|
| CI | Continuous Integration | Python syntax check, Docker build |
| CD | Continuous Delivery/Deployment | ECR push 후 GitOps repo 변경, ArgoCD 자동 배포 |

이번 프로젝트에서 CI/CD 실행 도구는 GitHub Actions입니다.

---

### GitHub Actions

GitHub Actions는 repository에 push 같은 이벤트가 발생했을 때 workflow를 자동 실행하는 도구입니다.

이번 workflow는 다음 작업을 수행합니다.

```text
1. task-api-platform repository checkout
2. Python syntax check
3. Git commit SHA 기반 image tag 생성
4. AWS OIDC 인증
5. Amazon ECR login
6. Docker image build
7. Docker image push
8. gitops-argocd repository checkout
9. ArgoCD Application manifest의 image tag 수정
10. gitops-argocd deploy/dev branch에 commit/push
```

Workflow 파일 위치:

```text
.github/workflows/ci-cd.yaml
```

---

### Amazon ECR

Amazon ECR은 Docker image를 저장하는 AWS Container Registry입니다.

Kubernetes는 Python 코드를 직접 실행하는 것이 아니라, ECR에 저장된 Docker image를 pull해서 Pod로 실행합니다.

```text
FastAPI code
  ↓ docker build
Docker image
  ↓ docker push
Amazon ECR
  ↓ Kubernetes pull
Pod 실행
```

---

### Image Tag 전략

이번 CI/CD에서는 Docker image tag로 Git commit SHA 앞 7자리를 사용합니다.

예시:

```text
Git commit SHA: 6362dbf1234...
Docker image tag: 6362dbf
```

ECR image 예시:

```text
519330023984.dkr.ecr.ap-northeast-1.amazonaws.com/task-api:6362dbf
```

Git SHA 기반 tag를 사용하는 이유는 다음과 같습니다.

| 이유 | 설명 |
|---|---|
| 추적성 | 현재 배포된 이미지가 어떤 Git commit에서 만들어졌는지 확인 가능 |
| Rollback 용이 | 이전 GitOps commit으로 되돌리면 이전 이미지로 배포 가능 |
| `latest`보다 안전 | `latest`는 같은 tag가 계속 덮어써져 어떤 코드인지 추적하기 어려움 |
| GitOps와 적합 | GitOps repo에 image tag 변경 이력이 명확히 남음 |

---

### GitOps

GitOps는 Kubernetes 배포 상태를 Git repository에 선언하고, Git에 기록된 상태를 기준으로 클러스터를 동기화하는 방식입니다.

일반적인 배포 방식은 CI가 직접 Kubernetes에 배포하는 것입니다.

```text
GitHub Actions
  ↓
kubectl apply 또는 helm upgrade
  ↓
Kubernetes 변경
```

이번 프로젝트에서는 GitOps 방식을 사용합니다.

```text
GitHub Actions
  ↓
gitops-argocd repo의 image tag 수정
  ↓
ArgoCD가 Git 변경 감지
  ↓
Kubernetes 배포
```

즉, GitHub Actions는 Kubernetes를 직접 수정하지 않고, GitOps repo만 수정합니다. 실제 배포는 ArgoCD가 담당합니다.

---

### ArgoCD

ArgoCD는 GitOps 방식으로 Kubernetes 애플리케이션을 배포하는 도구입니다.

이번 구성에서는 ArgoCD가 `gitops-argocd` repository의 `deploy/dev` branch를 감시합니다.

```text
gitops-argocd/deploy/dev
  ↓
dev-root Application
  ↓
argo-task-api Application
  ↓
task-api-platform Helm Chart
  ↓
EKS argo-task-api namespace
```

---

## GitHub Actions 구성

### Workflow Trigger

```yaml
on:
  push:
    branches:
      - feature/week6-cicd
      - main
```

현재 테스트 단계에서는 `feature/week6-cicd` 브랜치 push 시 workflow가 실행되도록 구성했고, 최종적으로 `main` 브랜치 push 시에도 실행되도록 구성했습니다.

---

### GitHub Actions Variables

`task-api-platform` repository의 Actions variables에 다음 값을 등록했습니다.

| Name | Value |
|---|---|
| `AWS_REGION` | `ap-northeast-1` |
| `AWS_ACCOUNT_ID` | `519330023984` |
| `ECR_REPOSITORY` | `task-api` |
| `GITOPS_REPO` | `leehrm/gitops-argocd` |
| `GITOPS_BRANCH` | `deploy/dev` |

---

### GitHub Actions Secrets

| Name | 설명 |
|---|---|
| `AWS_ROLE_TO_ASSUME` | GitHub Actions가 AWS에 OIDC 방식으로 접근하기 위한 IAM Role ARN |
| `GITOPS_REPO_TOKEN` | GitHub Actions가 `gitops-argocd` repo에 image tag 변경 commit을 push하기 위한 token |

---

## AWS IAM / OIDC 구성

GitHub Actions가 AWS ECR에 image를 push하기 위해 GitHub Actions OIDC Provider와 IAM Role을 구성했습니다.

### GitHub Actions OIDC Provider

GitHub Actions용 OIDC Provider:

```text
arn:aws:iam::519330023984:oidc-provider/token.actions.githubusercontent.com
```

GitHub Actions에서 AWS Role을 assume하기 위해서는 `token.actions.githubusercontent.com` Provider가 별도로 필요합니다.

### IAM Role

GitHub Actions에서 assume하는 Role:

```text
arn:aws:iam::519330023984:role/task-api-github-actions-ecr-role
```

이 Role은 `task-api-platform` repository의 GitHub Actions workflow에서만 assume할 수 있도록 Trust Policy를 구성했습니다.

### ECR Push 권한

GitHub Actions는 다음 ECR repository에 push할 수 있습니다.

```text
arn:aws:ecr:ap-northeast-1:519330023984:repository/task-api
```

---

## 배포 결과 확인

### ECR image tag 확인

```bash
aws ecr describe-images \
  --repository-name task-api \
  --region ap-northeast-1 \
  --query 'imageDetails[*].imageTags'
```

확인된 image tags 예시:

```text
manual-test
0.2.2
86394bd
6362dbf
```

---

### GitOps repo commit 확인

```bash
cd ~/gitops-argocd
git switch deploy/dev
git pull origin deploy/dev
git log --oneline -n 5
```

예시:

```text
ff18544 chore: update task-api image tag to 6362dbf
e0c5611 chore: update task-api image tag to 86394bd
7a2dff0 feat: add dev argocd applications
a712e9f feat: add dev argocd application for task-api
18994c5 docs: add README
```

GitHub Actions가 `gitops-argocd` repo의 image tag를 자동으로 수정하고 commit/push한 것을 확인했습니다.

---

### ArgoCD Application 상태 확인

```bash
kubectl get app -n argocd
```

결과:

```text
NAME            SYNC STATUS   HEALTH STATUS
argo-task-api   Synced        Healthy
dev-root        Synced        Healthy
```

---

### 실제 EKS Deployment image 확인

```bash
kubectl get deploy argo-task-api -n argo-task-api \
  -o=jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
```

결과 예시:

```text
519330023984.dkr.ecr.ap-northeast-1.amazonaws.com/task-api:6362dbf
```

GitHub Actions가 빌드한 Git SHA 기반 image가 실제 EKS Deployment에 반영되었습니다.

---

## 중간 이슈와 해결

| 문제 | 원인 | 해결 |
|---|---|---|
| `ErrImageNeverPull` | Helm values의 `imagePullPolicy`가 `Never`로 설정되어 ECR에서 image를 pull하지 않음 | `pullPolicy: Always` 설정 |
| DB 연결 실패 | ArgoCD 배포 시 PostgreSQL Service 이름이 `argo-task-api-postgresdb`인데 API는 기존 `task-api-postgresdb`를 바라봄 | `DB_HOST=argo-task-api-postgresdb`로 override |
| ArgoCD App 상태 `Progressing` | Ingress Controller가 없어서 Ingress에 CLASS/ADDRESS가 할당되지 않음 | `ingress.enabled=false` 설정 |
| FluxCD repo와 ArgoCD repo 혼동 | 기존 `task-api-gitops`에 FluxCD 리소스와 ArgoCD 리소스가 섞임 | `gitops-argocd` repo를 새로 분리 |

---

## 최종 흐름

```text
Code Push
  ↓
GitHub Actions
  ↓
Docker Build
  ↓
ECR Push
  ↓
GitOps Repo Image Tag Update
  ↓
ArgoCD Auto Sync
  ↓
EKS Deployment Update
```

`task-api-platform`에 push하면 새로운 Docker image가 ECR에 올라가고, `gitops-argocd` repository의 image tag가 자동으로 갱신되며, ArgoCD가 해당 변경을 감지해 EKS에 자동 배포하는 것을 확인했습니다.

---

## Branch 전략

### 애플리케이션 repository: `task-api-platform`

| 브랜치 | 역할 |
|---|---|
| `main` | 안정 브랜치, 최종 CI/CD workflow 반영 대상 |
| `dev` | 통합 개발 브랜치 |
| `feature/*` | 기능 개발 및 실습 작업 브랜치 |
| `feature/week6-cicd` | Week 6 GitHub Actions CI/CD 구성 작업 브랜치 |

Week 6 작업 완료 후 `feature/week6-cicd`를 `main`으로 PR merge하여, 이후 `main` push 기준으로 CI/CD가 동작하도록 구성합니다.

### GitOps repository: `gitops-argocd`

| 브랜치 | 역할 |
|---|---|
| `main` | README 및 repository 설명 관리 |
| `deploy/dev` | ArgoCD가 바라보는 dev 환경 배포 브랜치 |

`task-api-platform`의 GitHub Actions는 `gitops-argocd/deploy/dev` 브랜치의 image tag를 수정합니다.