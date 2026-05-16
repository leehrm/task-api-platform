from fastapi import HTTPException, Response, status
from app.models.task_model import TaskCreate, TaskUpdate
from app.services import task_service

def create_task(task: TaskCreate):
    return task_service.create_task(task)

def list_tasks():
    return task_service.list_tasks()

def get_task(task_id: int):
    task = task_service.get_task(task_id)

    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return task

def update_task(task_id: int, task: TaskUpdate):
    updated_task = task_service.update_task(task_id, task)

    if updated_task is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return updated_task

def delete_task(task_id: int):
    deleted = task_service.delete_task(task_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")

    return Response(status_code=status.HTTP_204_NO_CONTENT)