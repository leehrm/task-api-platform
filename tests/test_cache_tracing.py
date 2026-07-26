from unittest.mock import Mock, patch

from app.config.cache import Cache
from app.services.task_service import TaskService


class _RecordingCache:
    """Cache 대역. span/log에 남을 label만 기록한다."""

    def __init__(self) -> None:
        self.labels: list[str] = []

    def get(self, key, label=None):
        self.labels.append(label or key)
        return None

    def set(self, key, value, ttl_seconds=None, label=None):
        self.labels.append(label or key)

    def delete(self, *keys, label=None):
        self.labels.append(label or ",".join(keys))


def _service_with_recording_cache():
    recorder = _RecordingCache()
    return TaskService(repository=Mock(), cache_client=recorder), recorder


def test_task_ids_never_reach_cache_labels():
    service, recorder = _service_with_recording_cache()

    service.get_task(42)
    service.update_task(42, Mock(title="x", done=None))
    service.delete_task(42)

    assert recorder.labels, "cache 호출이 기록되지 않았다"
    assert not any("42" in label for label in recorder.labels)


def test_list_key_is_used_as_its_own_label():
    service, recorder = _service_with_recording_cache()
    service.repository.list_tasks.return_value = []

    service.list_tasks()

    assert recorder.labels == ["tasks:list", "tasks:list"]


def test_redis_error_is_not_reported_as_cache_miss():
    cache = Cache()
    cache.client = Mock()
    cache.client.get.side_effect = TimeoutError("redis timeout")
    span = Mock()
    span_context = Mock()
    span_context.__enter__ = Mock(return_value=span)
    span_context.__exit__ = Mock(return_value=False)
    tracer = Mock()
    tracer.start_as_current_span.return_value = span_context

    with patch("app.config.cache.get_tracer", return_value=tracer):
        assert cache.get("tasks:list") is None

    span.set_attribute.assert_any_call("cache.result", "error")
    assert not any(
        call.args == ("cache.hit", False)
        for call in span.set_attribute.call_args_list
    )
