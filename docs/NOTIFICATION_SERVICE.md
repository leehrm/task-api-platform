# Notification Service 구현 및 변경 설명서

기존 Task API의 완료 알림 책임을 실제 Notification Service workload로 분리하기 위해 추가·변경한 애플리케이션 코드를 정리함. 파일별 변경 목적, 요청 흐름, 설정, 오류 처리와 검증 범위를 설명함.

## 구현 목적

기존 알림 흐름은 Task API 프로세스 내부의 Python 객체 호출이었음.

```text
TaskService
  -> SlackNotifier.task_completed()
  -> Slack webhook
```

Kiali와 Istio는 network를 통과하는 workload 간 traffic을 관찰함. 같은 프로세스 안의 Python method 호출은 network traffic이 아니므로 별도 service edge로 표시할 수 없음. 내부 service 통신을 실제로 관찰하기 위해 비교용 Task API의 알림 대상을 HTTP 기반 Notification Service로 분리함.

```text
TaskService
  -> NotificationServiceClient
  -> HTTP POST /notifications/task-completed
  -> Notification Service
  -> SlackNotifier
  -> Slack webhook
```

이 변경으로 다음 동작을 확인할 수 있게 됨.

- Task API와 Notification Service가 별도 Deployment, Pod, Service와 identity로 실행됨
- 두 workload 사이 요청량, 오류율과 latency를 Kiali에서 확인할 수 있음
- Envoy가 workload 간 HTTP를 mTLS로 전달하고 Istio 정책으로 호출 주체를 제한할 수 있음
- Slack credential을 Notification Service에만 배치할 수 있음

애플리케이션에 Istio SDK, mTLS 인증서 또는 Envoy 제어 코드를 추가하지 않음. 애플리케이션은 일반 HTTP를 사용하며 mTLS와 telemetry는 배포 환경의 Istio sidecar가 처리함.

## 기존 환경과 비교 환경

같은 애플리케이션 코드가 환경변수에 따라 다른 notifier를 선택함.

| 실행 환경 | `NOTIFIER` | 완료 알림 흐름 | Slack webhook 보유 |
|---|---|---|---|
| 기존 Task API | `slack` | Task API → Slack | Task API |
| 비교용 Istio Task API | `service` | Task API → Notification Service | 없음 |
| Notification Service | 사용하지 않음 | Notification Service → Slack | Notification Service |

기존 Task API 동작은 유지하고 비교용 Istio Task API만 내부 service를 호출함. 따라서 기존 경로를 대조군으로 남기면서 실제 workload 간 통신을 추가함.

## 전체 처리 흐름

```text
PATCH /tasks/{id} done=true
  -> TaskRepository.update_task()
  -> DB UPDATE와 commit 완료
  -> TaskService가 false -> true 전환 감지
  -> NotificationServiceClient.task_completed()
  -> POST /notifications/task-completed
  -> Notification Service 입력 검증
  -> SlackNotifier.task_completed()
  -> Slack webhook
```

Task repository의 write context가 종료될 때 DB commit이 완료된 뒤 notifier를 호출함. Notification Service 또는 Slack 전송이 실패해도 이미 완료된 task 상태를 되돌리지 않음.

## 핵심 설계 결정

### 기존 Notifier 경계를 재사용함

`TaskService`는 이미 `Notifier` protocol만 의존하고 있었음. 새로운 조건문을 business logic에 추가하지 않고 `NotificationServiceClient`가 같은 protocol을 구현하도록 구성함.

```text
Notifier
├─ NullNotifier
├─ LoggingNotifier
├─ SlackNotifier
└─ NotificationServiceClient
```

`build_notifier()`가 환경변수를 읽어 구현체를 선택하므로 Task 완료 판단과 저장 로직은 변경하지 않음.

### 알림은 best-effort 동기 호출로 유지함

Task API는 Notification Service를 동기 HTTP로 호출하지만 실패를 사용자 요청까지 전파하지 않음. task 완료 상태가 핵심 데이터이고 Slack 알림은 부가 기능이기 때문임.

- HTTP timeout: 2초
- 자동 retry: 없음
- queue/outbox: 없음
- 실패 기록: log와 Prometheus metric
- task 완료 상태 rollback: 없음

보장 전달이나 자동 retry가 실제 요구사항이 될 때 transactional outbox 또는 queue를 검토함.

### Notification Service의 책임을 제한함

Notification Service는 완료 알림을 Slack으로 전달하는 역할만 수행함.

- 입력: task `id`, `title`
- 저장소: 사용하지 않음
- RDS·Redis: 사용하지 않음
- credential: Slack webhook만 사용함
- public endpoint: 없음

## 설정값

### `NOTIFIER`

Task API가 사용할 notifier 구현을 선택함.

| 값 | 구현 | 동작 |
|---|---|---|
| `none` 또는 미설정 | `NullNotifier` | 알림을 보내지 않음 |
| `log` | `LoggingNotifier` | 완료 사실을 log와 metric에 기록함 |
| `slack` | `SlackNotifier` | Slack webhook을 직접 호출함 |
| `service` | `NotificationServiceClient` | Notification Service를 호출함 |

알 수 없는 값이나 필수 URL이 없는 경우 프로세스를 중단하지 않고 warning을 남긴 뒤 `NullNotifier`로 fallback함.

### `NOTIFICATION_SERVICE_URL`

`NOTIFIER=service`일 때 사용하는 Notification Service base URL임.

```text
http://notification-service.notification-service.svc.cluster.local:8000
```

Client가 `/notifications/task-completed` 경로를 자동으로 추가함.

### `NOTIFY_WEBHOOK_URL`

`SlackNotifier`가 사용하는 Slack incoming webhook임. 기존 Task API의 직접 호출 환경과 Notification Service에서 사용함. 비교용 Istio Task API가 `NOTIFIER=service`를 사용할 때에는 이 credential을 보유하지 않음.

## 파일별 변경

### `.env.example`

Notification Service의 cluster DNS 주소를 설정할 수 있도록 `NOTIFICATION_SERVICE_URL` 예시를 추가함.

```text
NOTIFICATION_SERVICE_URL=http://notification-service.notification-service.svc.cluster.local:8000
```

실제 namespace와 Service 이름은 GitOps 배포 설정에서 관리함.

### `app/services/notification_service.py`

기존 notifier module을 network client와 Notification Service 양쪽에서 재사용할 수 있도록 확장함.

#### `SlackNotifier`

- `raise_on_error` option을 추가함
- 기존 Task API에서는 기본값 `False`를 사용해 Slack 오류를 내부에서 처리함
- Notification Service에서는 `True`를 사용해 Slack 오류를 API의 HTTP `502`로 변환할 수 있게 함
- 사용자 입력 title을 `html.escape()`로 처리해 Slack 특수 mention 형식이 그대로 해석되지 않게 함

#### `NotificationServiceClient`

- `Notifier` protocol과 같은 `task_completed(task)` method를 구현함
- `POST /notifications/task-completed`를 호출함
- JSON body에는 `id`, `title`만 포함함
- Python 표준 라이브러리 `urllib.request`를 사용해 HTTP dependency를 추가하지 않음
- 기본 timeout을 2초로 설정함
- 성공 시 `channel="service"` metric과 log를 기록함
- transport 오류 또는 HTTP 오류 발생 시 failure metric을 기록하고 예외를 전달함

#### `build_notifier()`

- `NOTIFIER=service` 선택을 추가함
- `NOTIFICATION_SERVICE_URL`이 있으면 `NotificationServiceClient`를 생성함
- URL이 없으면 warning을 남기고 `NullNotifier`로 fallback함
- 기존 `slack`, `log`, `none` 선택은 유지함

### `app/notification_main.py`

Notification Service로 실행할 별도 FastAPI application을 추가함.

GitOps Deployment는 같은 image에서 다음 entrypoint를 실행함.

```text
python -m uvicorn app.notification_main:app --host 0.0.0.0 --port 8000
```

#### `TaskCompleted`

내부 요청 body를 검증하는 Pydantic model임.

- `id`: 0보다 큰 정수
- `title`: 1~255자 문자열

#### `_build_delivery_notifier()`

- `NOTIFY_WEBHOOK_URL`을 읽어 `SlackNotifier`를 생성함
- `raise_on_error=True`를 사용해 Slack 실패를 API 응답으로 표현함
- webhook이 없으면 `None`을 반환함

#### API endpoint

| Method | Path | 정상 응답 | 역할 |
|---|---|---:|---|
| `GET` | `/healthz` | `200` | FastAPI process 생존 확인 |
| `GET` | `/readyz` | `200` | Slack notifier 설정 준비 확인 |
| `POST` | `/notifications/task-completed` | `204` | 완료 알림을 Slack으로 전달 |

오류 응답:

| 조건 | 응답 |
|---|---:|
| `id`, `title` 입력 검증 실패 | `422` |
| Slack webhook 미설정 | `503` |
| Slack 호출 실패 | `502` |

`/healthz`는 webhook 설정과 무관하게 process 생존만 확인함. `/readyz`는 실제 Slack 전송 준비 여부를 확인함.

### `app/services/task_service.py`

Notification Service 분리 과정에서는 이 파일을 변경하지 않음. 기존 `Notifier` 의존성과 `_notify_completed()` 오류 경계를 그대로 재사용함.

- task가 `done=false`에서 `done=true`로 바뀔 때만 알림을 한 번 호출함
- 제목만 변경하거나 이미 완료된 task를 다시 수정할 때에는 알림을 보내지 않음
- notifier 예외를 log로 기록하고 API update 결과는 정상 반환함

### `app/repositories/task_repository.py`

이 파일도 변경하지 않음. 기존 write context가 SQL 성공 후 commit하고 결과를 반환하므로 notifier 호출 전에 task 상태가 확정되는 구조를 그대로 사용함.

### `tests/test_notification.py`

기존 notifier 테스트에 내부 service client와 선택 로직 검증을 추가함.

- 완료 전환 시 알림 한 번 호출
- 이름 변경과 이미 완료된 task 수정 시 미호출
- notifier 실패가 task update 결과에 영향을 주지 않음
- `SlackNotifier`의 오류 처리와 선택적 예외 전달
- Slack JSON payload와 사용자 입력 escape
- `NotificationServiceClient`의 URL, method, JSON body, timeout
- 내부 client transport 오류 전달
- `NOTIFIER=service` 선택과 URL 누락 fallback

### `tests/test_notification_api.py`

Notification Service API test를 추가함.

- `/healthz` 정상 응답
- webhook 유무에 따른 `/readyz` 응답
- 정상 완료 알림 `204`
- 잘못된 입력 `422`
- Slack 실패 `502`

### `.github/workflows/ci-cd.yaml`

애플리케이션 변경이 배포 workload마다 다른 image version으로 실행되지 않도록 GitOps tag update 범위를 확장함.

- test를 통과한 commit으로 image를 한 번 build하고 ECR에 push함
- 기존 Task API tag를 갱신함
- 비교용 Istio Task API tag를 함께 갱신함
- Notification Service Kustomize `newTag`를 함께 갱신함
- 세 tag 변경을 하나의 GitOps commit으로 push함

세 workload가 같은 code artifact를 실행하므로 client와 server API contract가 서로 다른 version으로 배포되는 문제를 방지함.

### `helm/task-api/templates/deployment.yaml`

Pod template에 ConfigMap checksum annotation을 추가함.

```yaml
checksum/config: <rendered ConfigMap hash>
```

Kubernetes는 ConfigMap 내용만 바뀌어도 기존 Pod를 자동 재시작하지 않음. `NOTIFIER` 또는 `NOTIFICATION_SERVICE_URL` 변경 시 checksum이 달라져 Deployment rollout이 발생하고 새 Pod가 변경된 환경변수를 읽게 함.

## 오류 처리 흐름

```text
Notification Service 호출 성공
  -> Task API service success metric
  -> Notification Service Slack success metric
  -> HTTP 204

Notification Service 호출 실패
  -> Task API service failure metric
  -> NotificationServiceClient가 예외 전달
  -> TaskService가 예외를 log로 기록
  -> 완료된 task 상태와 API update 응답은 유지

Slack 호출 실패
  -> Notification Service Slack failure metric
  -> Notification Service가 HTTP 502 반환
  -> Task API가 service failure metric과 log 기록
  -> 완료된 task 상태는 유지
```

## Metric과 log

기존 notification metric을 client와 server에서 함께 사용함.

| Metric | label | 의미 |
|---|---|---|
| `notification_sent_total` | `channel=service` | Task API가 Notification Service 호출에 성공함 |
| `notification_failed_total` | `channel=service` | 내부 service 호출에 실패함 |
| `notification_sent_total` | `channel=slack` | Notification Service 또는 기존 Task API가 Slack 호출에 성공함 |
| `notification_failed_total` | `channel=slack` | Slack 호출에 실패함 |

주요 structured log event:

- `event=notification_forwarded channel=service`
- `event=task_completed channel=slack`
- `event=notification_failed channel=service`
- `event=notification_failed channel=slack`
- `event=notifier_fallback`

Kiali traffic graph는 이 application metric이 아니라 Envoy가 생성한 Istio telemetry를 사용함. Application metric은 알림 단계별 성공·실패 원인을 확인하는 용도임.

## 검증

전체 test 실행:

```bash
pytest -q
```

최종 구현 commit 기준 결과:

```text
43 passed
```

Notification Service process 확인:

```bash
NOTIFY_WEBHOOK_URL='<webhook>' \
python -m uvicorn app.notification_main:app --host 0.0.0.0 --port 8000
```

```bash
curl -sS http://127.0.0.1:8000/healthz
curl -sS http://127.0.0.1:8000/readyz
```

실제 Kubernetes Deployment, Service, Secret, Istio mTLS와 AuthorizationPolicy는 `gitops-argocd` 저장소의 `docs/istio-kiali-notification-service-changes.md`에서 설명함.

## 의도적으로 제외한 범위

- 자동 retry
- queue, Kafka, RabbitMQ
- transactional outbox
- Notification Service의 DB·Redis 연결
- 별도 public endpoint
- 애플리케이션 내부 Istio SDK 또는 TLS 인증서 처리
- Python HTTP client trace context 전파

## 주요 작업 commit

- `e458dd4` — 내부 Notification Service application, client와 test 추가
- `4970877` — 세 workload image tag 동기화 CI
- `e13f102` — ConfigMap 변경 시 Task API Pod 자동 rollout
