from fastapi import HTTPException, Request

from app.services.health_service import HealthService, PodDraining, health_service


class HealthController:
    """HTTP controller layer for health endpoints."""

    def __init__(self, service: HealthService) -> None:
        self.service = service

    def healthz(self):
        return self.service.get_health_status()

    def readyz(self):
        try:
            return self.service.get_readiness_status()
        except PodDraining:
            # 정상 종료 중. 세부 상태는 /healthz가 계속 응답한다.
            raise HTTPException(status_code=503, detail={"status": "draining"})
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

    def drain(self, request: Request):
        client_host = request.client.host if request.client else ""

        if client_host not in {"127.0.0.1", "::1"}:
            raise HTTPException(status_code=403, detail="drain is local-only")

        return self.service.start_draining("pre_stop")


health_controller = HealthController(health_service)
