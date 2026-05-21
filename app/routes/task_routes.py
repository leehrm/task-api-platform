from typing import List

from fastapi import APIRouter

from app.controllers.task_controller import task_controller
from app.models.task_model import TaskCreate, TaskResponse, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse)
def create_task(task: TaskCreate):
    return task_controller.create_task(task)


@router.get("", response_model=List[TaskResponse])
def list_tasks():
    return task_controller.list_tasks()


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int):
    return task_controller.get_task(task_id)


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, task: TaskUpdate):
    return task_controller.update_task(task_id, task)


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int):
    return task_controller.delete_task(task_id)
