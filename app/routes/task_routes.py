from typing import List

from fastapi import APIRouter

from app.controllers.task_controller import task_controller
from app.models.task_model import TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])

router.add_api_route(
    "", task_controller.create_task, methods=["POST"], response_model=TaskResponse
)
router.add_api_route(
    "", task_controller.list_tasks, methods=["GET"], response_model=List[TaskResponse]
)
router.add_api_route(
    "/{task_id}", task_controller.get_task, methods=["GET"], response_model=TaskResponse
)
router.add_api_route(
    "/{task_id}", task_controller.update_task, methods=["PATCH"], response_model=TaskResponse
)
router.add_api_route(
    "/{task_id}", task_controller.delete_task, methods=["DELETE"], status_code=204
)
