from typing import Optional

from app.models.task_model import TaskCreate, TaskUpdate
from app.repositories.task_repository import TaskRepository, task_repository


class TaskService:

    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def create_task(self, task: TaskCreate) -> dict:
        return self.repository.create_task(task.title)

    def list_tasks(self) -> list[dict]:
        return self.repository.list_tasks()

    def get_task(self, task_id: int) -> Optional[dict]:
        return self.repository.get_task_by_id(task_id)

    def update_task(self, task_id: int, task: TaskUpdate) -> Optional[dict]:
        return self.repository.update_task(
            task_id=task_id,
            title=task.title,
            done=task.done,
        )

    def delete_task(self, task_id: int) -> bool:
        return self.repository.delete_task(task_id)


task_service = TaskService(task_repository)
