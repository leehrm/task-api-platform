import os

from app.config.database import Database, database
from app.lifecycle import lifecycle_state


class HealthService:

    def __init__(self, db: Database) -> None:
        self.db = db

    def get_health_status(self) -> dict:
        return {
            "status": "ok",
            **lifecycle_state.status(),
        }

    def get_readiness_status(self) -> dict:
        if lifecycle_state.draining:
            raise RuntimeError("pod is draining")

        self.db.check_connection()

        return {
            "status": "ready",
            "db": "connected",
            **lifecycle_state.status(),
        }

    def start_draining(self, reason: str) -> dict:
        lifecycle_state.mark_draining(reason)
        return {
            "status": "draining",
            **lifecycle_state.status(),
        }

    def get_version_status(self) -> dict:
        return {
            "app": "task-api",
            "version": os.getenv("APP_VERSION", "local"),
        }


health_service = HealthService(database)
