import os
import time

from fastapi import APIRouter, HTTPException


router = APIRouter(prefix="/debug", tags=["debug"])


def _debug_enabled() -> bool:
    return os.getenv("ENABLE_DEBUG_ENDPOINTS", "false").lower() == "true"


def _raise_not_found_when_disabled() -> None:
    if not _debug_enabled():
        raise HTTPException(status_code=404, detail="Not found")


@router.get("/error")
def generate_error():
    """
    Alert test endpoint.
    ENABLE_DEBUG_ENDPOINTS=true 일 때만 500 응답을 발생시킨다.
    """
    _raise_not_found_when_disabled()
    print("event=debug_error status=500", flush=True)
    raise HTTPException(status_code=500, detail="debug error for alert test")


@router.get("/slow")
def generate_slow_response():
    """
    Latency alert test endpoint.
    DEBUG_SLOW_SECONDS 값만큼 sleep 후 200 응답을 반환한다.
    """
    _raise_not_found_when_disabled()
    sleep_seconds = float(os.getenv("DEBUG_SLOW_SECONDS", "0.3"))
    print(f"event=debug_slow sleep_seconds={sleep_seconds}", flush=True)
    time.sleep(sleep_seconds)
    return {"status": "ok", "sleep_seconds": sleep_seconds}
