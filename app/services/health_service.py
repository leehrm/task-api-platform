import os

from app import __version__
from app.config.database import Database, database
from app.lifecycle import lifecycle_state


class PodDraining(Exception):
    """readiness 실패 중 '종료 중'을 DB 장애와 구분하기 위한 신호."""


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
            raise PodDraining()

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
            "version": os.getenv("APP_VERSION", __version__),
        }


health_service = HealthService(database)
