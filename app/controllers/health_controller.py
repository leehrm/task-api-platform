from fastapi import HTTPException

from app.services.health_service import HealthService, health_service


class HealthController:
    """HTTP controller layer for health endpoints."""

    def __init__(self, service: HealthService) -> None:
        self.service = service

    def healthz(self):
        return self.service.get_health_status()

    def readyz(self):
        try:
            return self.service.get_readiness_status()
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail={
                    "status": "not_ready",
                    "db": "disconnected",
                    "error": str(e),
                },
            )

    def get_version(self):
        return self.service.get_version_status()


health_controller = HealthController(health_service)
