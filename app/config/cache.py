import json
import os
from typing import Any

import redis

from app.metrics import CACHE_HIT_TOTAL, CACHE_MISS_TOTAL


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
            print(f"event=cache_skip key={key} reason=disabled", flush=True)
            return None

        try:
            value = self.client.get(key)

            if value is None:
                CACHE_MISS_TOTAL.inc()
                print(f"event=cache_lookup key={key} result=miss", flush=True)
                return None

            CACHE_HIT_TOTAL.inc()
            print(f"event=cache_lookup key={key} result=hit", flush=True)
            return json.loads(value)

        except Exception as e:
            print(f"event=cache_error action=get key={key} error={e}", flush=True)
            return None

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        if not self.enabled:
            return

        ttl = ttl_seconds or self.ttl_seconds

        try:
            self.client.setex(key, ttl, json.dumps(value))
            print(f"event=cache_set key={key} ttl={ttl}", flush=True)

        except Exception as e:
            print(f"event=cache_error action=set key={key} error={e}", flush=True)

    def delete(self, *keys: str) -> None:
        if not self.enabled or not keys:
            return

        try:
            deleted = self.client.delete(*keys)
            print(f"event=cache_delete keys={','.join(keys)} deleted={deleted}", flush=True)

        except Exception as e:
            print(f"event=cache_error action=delete keys={','.join(keys)} error={e}", flush=True)


cache = Cache()
