import json
import logging
import os
from typing import Any

import redis

from app.metrics import CACHE_HIT_TOTAL, CACHE_MISS_TOTAL
from app.observability import get_tracer
from opentelemetry.trace import Status, StatusCode


logger = logging.getLogger(__name__)


class Cache:
    def __init__(self) -> None:
        self.enabled = os.getenv("CACHE_ENABLED", "true").lower() == "true"
        self.ttl_seconds = int(os.getenv("CACHE_TTL_SECONDS", "60"))

        self.redis_host = os.getenv("REDIS_HOST", "localhost")
        self.redis_port = int(os.getenv("REDIS_PORT", "6379"))
        self.redis_password = os.getenv("REDIS_PASSWORD")

        self.client = redis.Redis(
            host=self.redis_host,
            port=self.redis_port,
            password=self.redis_password,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
        )

    def get(self, key: str) -> Any | None:
        if not self.enabled:
            logger.info("event=cache_skip key_pattern=%s reason=disabled", self._key_pattern(key))
            return None

        with get_tracer().start_as_current_span("task.cache.get") as span:
            self._set_common_attributes(span, "get", key)
            try:
                value = self.client.get(key)

                if value is None:
                    CACHE_MISS_TOTAL.inc()
                    span.set_attribute("cache.hit", False)
                    span.set_attribute("cache.result", "miss")
                    logger.info("event=cache_lookup key_pattern=%s result=miss", self._key_pattern(key))
                    return None

                CACHE_HIT_TOTAL.inc()
                span.set_attribute("cache.hit", True)
                span.set_attribute("cache.result", "hit")
                logger.info("event=cache_lookup key_pattern=%s result=hit", self._key_pattern(key))
                return json.loads(value)

            except Exception as exc:
                span.set_attribute("cache.result", "error")
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, type(exc).__name__))
                logger.exception("event=cache_error action=get key_pattern=%s", self._key_pattern(key))
                return None

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        if not self.enabled:
            return

        ttl = ttl_seconds or self.ttl_seconds

        with get_tracer().start_as_current_span("task.cache.set") as span:
            self._set_common_attributes(span, "set", key)
            try:
                self.client.setex(key, ttl, json.dumps(value))
                logger.info("event=cache_set key_pattern=%s ttl=%s", self._key_pattern(key), ttl)
            except Exception as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, type(exc).__name__))
                logger.exception("event=cache_error action=set key_pattern=%s", self._key_pattern(key))

    def delete(self, *keys: str) -> None:
        if not self.enabled or not keys:
            return

        with get_tracer().start_as_current_span("task.cache.delete") as span:
            span.set_attribute("cache.operation", "delete")
            span.set_attribute("cache.key_pattern", ",".join(self._key_pattern(key) for key in keys))
            try:
                deleted = self.client.delete(*keys)
                logger.info("event=cache_delete key_count=%s deleted=%s", len(keys), deleted)
            except Exception as exc:
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, type(exc).__name__))
                logger.exception("event=cache_error action=delete key_count=%s", len(keys))

    @staticmethod
    def _key_pattern(key: str) -> str:
        return "tasks:item:{task_id}" if key.startswith("tasks:item:") else key

    @classmethod
    def _set_common_attributes(cls, span, operation: str, key: str) -> None:
        span.set_attribute("cache.operation", operation)
        span.set_attribute("cache.key_pattern", cls._key_pattern(key))

cache = Cache()
