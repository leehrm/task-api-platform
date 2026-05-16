from fastapi import APIRouter
from app.controllers.health_controller import healthz, readyz

router = APIRouter()

router.add_api_route("/healthz", healthz, methods=["GET"])
router.add_api_route("/readyz", readyz, methods=["GET"])