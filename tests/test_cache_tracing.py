from unittest.mock import Mock, patch

from app.config.cache import Cache


def test_cache_key_patterns_hide_task_ids():
    assert Cache._key_pattern("tasks:list") == "tasks:list"
    assert Cache._key_pattern("tasks:item:42") == "tasks:item:{task_id}"


def test_unknown_cache_key_is_preserved():
    assert Cache._key_pattern("other:key") == "other:key"


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
