import json
import logging
import os
import urllib.request
from html import escape
from typing import Protocol

from app.metrics import NOTIFICATION_FAILED_TOTAL, NOTIFICATION_SENT_TOTAL


logger = logging.getLogger(__name__)


class Notifier(Protocol):
    """할 일 완료를 외부에 알리는 인터페이스."""

    def task_completed(self, task: dict) -> None: ...


class NullNotifier:
    """알림을 발송하지 않는다."""

    def task_completed(self, task: dict) -> None:
        pass


class LoggingNotifier:
    """완료 사실을 애플리케이션 로그로 남긴다."""

    def task_completed(self, task: dict) -> None:
        logger.info("event=task_completed channel=log task_id=%s", task["id"])
        NOTIFICATION_SENT_TOTAL.labels(channel="log").inc()


class SlackNotifier:
    """Slack incoming webhook으로 완료 메시지를 보낸다."""

    def __init__(
        self,
        webhook_url: str,
        timeout: float = 2.0,
        raise_on_error: bool = False,
    ) -> None:
        self.webhook_url = webhook_url
        self.timeout = timeout
        self.raise_on_error = raise_on_error

    def task_completed(self, task: dict) -> None:
        title = escape(task["title"], quote=False)
        payload = json.dumps(
            {"text": f":white_check_mark: 완료: {title} (#{task['id']})"}
        ).encode()
        request = urllib.request.Request(
            self.webhook_url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout):
                pass
            NOTIFICATION_SENT_TOTAL.labels(channel="slack").inc()
            logger.info("event=task_completed channel=slack task_id=%s", task["id"])
        except Exception:
            NOTIFICATION_FAILED_TOTAL.labels(channel="slack").inc()
            logger.exception("event=notification_failed channel=slack task_id=%s", task["id"])
            if self.raise_on_error:
                raise


class NotificationServiceClient:
    """완료 사실을 cluster 내부 Notification Service에 전달한다."""

    def __init__(self, service_url: str, timeout: float = 2.0) -> None:
        self.endpoint = f"{service_url.rstrip('/')}/notifications/task-completed"
        self.timeout = timeout

    def task_completed(self, task: dict) -> None:
        payload = json.dumps(
            {"id": task["id"], "title": task["title"]}
        ).encode()
        request = urllib.request.Request(
            self.endpoint,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=self.timeout):
                pass
            NOTIFICATION_SENT_TOTAL.labels(channel="service").inc()
            logger.info(
                "event=notification_forwarded channel=service task_id=%s",
                task["id"],
            )
        except Exception:
            NOTIFICATION_FAILED_TOTAL.labels(channel="service").inc()
            logger.exception(
                "event=notification_failed channel=service task_id=%s",
                task["id"],
            )
            raise


def build_notifier() -> Notifier:
    """
    NOTIFIER 환경변수에 따라 Notifier를 만든다.
    slack / service / log / none(기본값)을 지원하며,
    필수 URL이 없으면 NullNotifier를 반환한다.
    """
    kind = os.getenv("NOTIFIER", "none").strip().lower()

    if kind == "slack":
        webhook_url = os.getenv("NOTIFY_WEBHOOK_URL")
        if webhook_url:
            return SlackNotifier(webhook_url)
        logger.warning("event=notifier_fallback reason=missing_webhook_url")
    elif kind == "service":
        service_url = os.getenv("NOTIFICATION_SERVICE_URL")
        if service_url:
            return NotificationServiceClient(service_url)
        logger.warning("event=notifier_fallback reason=missing_service_url")
    elif kind == "log":
        return LoggingNotifier()
    elif kind != "none":
        logger.warning("event=notifier_fallback reason=unknown_notifier notifier=%s", kind)

    return NullNotifier()


notifier = build_notifier()
