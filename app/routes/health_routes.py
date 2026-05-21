from fastapi import APIRouter

from app.controllers.health_controller import health_controller

router = APIRouter()

router.add_api_route("/healthz", health_controller.healthz, methods=["GET"])
router.add_api_route("/readyz", health_controller.readyz, methods=["GET"])
router.add_api_route("/version", health_controller.get_version, methods=["GET"])
