import os

from app.config.database import Database, database


class HealthService:

    def __init__(self, db: Database) -> None:
        self.db = db

    def get_health_status(self) -> dict:
        return {"status": "ok"}

    def get_readiness_status(self) -> dict:
        self.db.check_connection()

        return {
            "status": "ready",
            "db": "connected",
        }

    def get_version_status(self) -> dict:
        return {
            "app": "task-api",
            "version": os.getenv("APP_VERSION", "local"),
        }


health_service = HealthService(database)
