import os
import socket
import time


class AppLifecycleState:
    def __init__(self) -> None:
        self.started_at = time.time()
        self.pod_name = os.getenv("POD_NAME") or socket.gethostname()
        self.draining = False
        self.drain_reason: str | None = None
        self.draining_since: float | None = None

    def mark_draining(self, reason: str) -> None:
        if self.draining:
            return

        self.draining = True
        self.drain_reason = reason
        self.draining_since = time.time()
        print(
            f"event=draining_started pod={self.pod_name} reason={reason}",
            flush=True,
        )

    def status(self) -> dict:
        return {
            "pod": self.pod_name,
            "draining": self.draining,
            "drain_reason": self.drain_reason,
            "draining_since": self.draining_since,
            "uptime_seconds": round(time.time() - self.started_at, 3),
        }


lifecycle_state = AppLifecycleState()
