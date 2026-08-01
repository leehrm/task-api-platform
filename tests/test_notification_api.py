from unittest.mock import Mock, patch

from fastapi.testclient import TestClient

from app.notification_main import app


client = TestClient(app)


def test_healthz_is_live_without_slack_configuration():
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_readyz_requires_slack_configuration():
    with patch("app.notification_main.delivery_notifier", None):
        response = client.get("/readyz")

    assert response.status_code == 503


def test_readyz_succeeds_with_delivery_notifier():
    with patch("app.notification_main.delivery_notifier", Mock()):
        response = client.get("/readyz")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_task_completed_delivers_validated_payload():
    notifier = Mock()

    with patch("app.notification_main.delivery_notifier", notifier):
        response = client.post(
            "/notifications/task-completed",
            json={"id": 7, "title": "보고서 작성"},
        )

    assert response.status_code == 204
    assert response.content == b""
    notifier.task_completed.assert_called_once_with(
        {"id": 7, "title": "보고서 작성"}
    )


def test_task_completed_rejects_invalid_payload():
    with patch("app.notification_main.delivery_notifier", Mock()):
        response = client.post(
            "/notifications/task-completed",
            json={"id": 0, "title": ""},
        )

    assert response.status_code == 422


def test_task_completed_reports_slack_failure():
    notifier = Mock()
    notifier.task_completed.side_effect = OSError("slack unavailable")

    with patch("app.notification_main.delivery_notifier", notifier):
        response = client.post(
            "/notifications/task-completed",
            json={"id": 7, "title": "보고서 작성"},
        )

    assert response.status_code == 502
    assert response.json() == {"detail": "Slack delivery failed"}
