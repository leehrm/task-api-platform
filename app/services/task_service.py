from app.models.task_model import TaskCreate, TaskUpdate
from app.repositories import task_repository

def create_task(task: TaskCreate):
    return task_repository.create_task(task.title)

def list_tasks():
    return task_repository.list_tasks()

def get_task(task_id: int):
    return task_repository.get_task_by_id(task_id)

def update_task(task_id: int, task: TaskUpdate):
    return task_repository.update_task(
        task_id=task_id,
        title=task.title,
        done=task.done,
    )

def delete_task(task_id: int):
    return task_repository.delete_task(task_id)