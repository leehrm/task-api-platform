from fastapi import HTTPException
from app.services.health_service import get_health_status, get_readiness_status

def healthz():
    return get_health_status()

def readyz():
    try:
        return get_readiness_status()
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "not_ready",
                "db": "disconnected",
                "error": str(e),
            },
        )