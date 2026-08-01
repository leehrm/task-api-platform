import os

from fastapi import FastAPI, HTTPException, Response, status
from pydantic import BaseModel, Field

from app import __version__
from app.logging_config import configure_logging
from app.services.notification_service import SlackNotifier


class TaskCompleted(BaseModel):
    id: int = Field(gt=0)
    title: str = Field(min_length=1, max_length=255)


def _build_delivery_notifier() -> SlackNotifier | None:
    webhook_url = os.getenv("NOTIFY_WEBHOOK_URL")
    if not webhook_url:
        return None
    return SlackNotifier(webhook_url, raise_on_error=True)


configure_logging()
delivery_notifier = _build_delivery_notifier()
app = FastAPI(title="Notification Service", version=__version__)


@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.get("/readyz")
def readyz() -> dict:
    if delivery_notifier is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="NOTIFY_WEBHOOK_URL is not configured",
        )
    return {"status": "ready"}


@app.post("/notifications/task-completed", status_code=status.HTTP_204_NO_CONTENT)
def task_completed(task: TaskCompleted) -> Response:
    if delivery_notifier is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="NOTIFY_WEBHOOK_URL is not configured",
        )

    try:
        delivery_notifier.task_completed(task.model_dump())
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Slack delivery failed",
        ) from exc

    return Response(status_code=status.HTTP_204_NO_CONTENT)
