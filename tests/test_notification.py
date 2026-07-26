import json
from unittest.mock import Mock, patch

from app.services.notification_service import (
    LoggingNotifier,
    NullNotifier,
    SlackNotifier,
    build_notifier,
)
from app.services.task_service import TaskService

from tests.test_cache_tracing import _RecordingCache


class _RecordingNotifier:
    def __init__(self) -> None:
        self.sent: list[int] = []

    def task_completed(self, task: dict) -> None:
        self.sent.append(task["id"])


def _service(notifier, updated: dict | None, became_done: bool = False):
    repository = Mock()
    repository.update_task.return_value = (
        None if updated is None else (updated, became_done)
    )
    return TaskService(
        repository=repository,
        cache_client=_RecordingCache(),
        notifier_client=notifier,
    )


def test_completing_a_task_notifies_once():
    recorder = _RecordingNotifier()
    service = _service(
        recorder,
        {"id": 7, "title": "x", "done": True},
        became_done=True,
    )

    service.update_task(7, Mock(title=None, done=True))

    assert recorder.sent == [7]


def test_renaming_a_task_does_not_notify():
    recorder = _RecordingNotifier()
    service = _service(recorder, {"id": 7, "title": "새 제목", "done": False})

    service.update_task(7, Mock(title="새 제목", done=None))

    assert recorder.sent == []


def test_updating_an_already_completed_task_does_not_notify():
    recorder = _RecordingNotifier()
    service = _service(recorder, {"id": 7, "title": "x", "done": True})

    service.update_task(7, Mock(title=None, done=True))

    assert recorder.sent == []


def test_missing_task_does_not_notify():
    recorder = _RecordingNotifier()
    service = _service(recorder, None)

    service.update_task(999, Mock(title=None, done=True))

    assert recorder.sent == []


def test_notifier_failure_does_not_break_the_update():
    """Notifier가 예외를 던져도 update_task는 정상 결과를 반환해야 한다."""
    exploding = Mock()
    exploding.task_completed.side_effect = RuntimeError("slack down")
    service = _service(
        exploding,
        {"id": 7, "title": "x", "done": True},
        became_done=True,
    )

    try:
        result = service.update_task(7, Mock(title=None, done=True))
    except RuntimeError:
        raise AssertionError("알림 실패가 호출자에게 전파되면 안 된다")

    assert result == {"id": 7, "title": "x", "done": True}
    exploding.task_completed.assert_called_once()


def test_slack_notifier_swallows_transport_errors():
    slack = SlackNotifier("https://hooks.example.invalid/x")

    with patch("app.services.notification_service.urllib.request.urlopen",
               side_effect=OSError("connection refused")):
        slack.task_completed({"id": 1, "title": "x", "done": True})


def test_slack_notifier_posts_json_payload():
    slack = SlackNotifier("https://hooks.example.invalid/x")

    with patch("app.services.notification_service.urllib.request.urlopen") as urlopen:
        slack.task_completed({"id": 1, "title": "빨래 개기", "done": True})

    request = urlopen.call_args.args[0]
    assert request.method == "POST"
    assert request.headers["Content-type"] == "application/json"
    assert "빨래 개기" in json.loads(request.data)["text"]


def test_slack_notifier_escapes_user_supplied_markup():
    slack = SlackNotifier("https://hooks.example.invalid/x")

    with patch("app.services.notification_service.urllib.request.urlopen") as urlopen:
        slack.task_completed({"id": 1, "title": "<!channel> & 완료", "done": True})

    text = json.loads(urlopen.call_args.args[0].data)["text"]
    assert "&lt;!channel&gt; &amp; 완료" in text


def test_build_notifier_picks_by_env():
    cases = {
        (): NullNotifier,
        ("none",): NullNotifier,
        ("log",): LoggingNotifier,
    }
    for env, expected in cases.items():
        environ = {"NOTIFIER": env[0]} if env else {}
        with patch.dict("os.environ", environ, clear=True):
            assert isinstance(build_notifier(), expected)


def test_slack_without_webhook_url_falls_back_to_null():
    with patch.dict("os.environ", {"NOTIFIER": "slack"}, clear=True):
        assert isinstance(build_notifier(), NullNotifier)


def test_slack_with_webhook_url_is_selected():
    env = {"NOTIFIER": "slack", "NOTIFY_WEBHOOK_URL": "https://hooks.example.invalid/x"}
    with patch.dict("os.environ", env, clear=True):
        assert isinstance(build_notifier(), SlackNotifier)


def test_unknown_notifier_falls_back_with_warning():
    with (
        patch.dict("os.environ", {"NOTIFIER": "slcak"}, clear=True),
        patch("app.services.notification_service.logger.warning") as warning,
    ):
        assert isinstance(build_notifier(), NullNotifier)

    warning.assert_called_once()
