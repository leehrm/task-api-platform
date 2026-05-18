from fastapi import APIRouter
from app.controllers.health_controller import healthz, readyz, get_version

router = APIRouter()

router.add_api_route("/healthz", healthz, methods=["GET"])
router.add_api_route("/readyz", readyz, methods=["GET"])
router.add_api_route("/version", get_version, methods=["GET"])