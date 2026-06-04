from typing import Optional

from app.config.cache import cache
from app.models.task_model import TaskCreate, TaskUpdate
from app.repositories.task_repository import TaskRepository, task_repository


class TaskService:

    TASK_LIST_CACHE_KEY = "tasks:list"

    def __init__(self, repository: TaskRepository) -> None:
        self.repository = repository

    def create_task(self, task: TaskCreate) -> dict:
        created_task = self.repository.create_task(task.title)

        cache.delete(self.TASK_LIST_CACHE_KEY)

        return created_task

    def list_tasks(self) -> list[dict]:
        cached_tasks = cache.get(self.TASK_LIST_CACHE_KEY)

        if cached_tasks is not None:
            return cached_tasks

        tasks = self.repository.list_tasks()
        cache.set(self.TASK_LIST_CACHE_KEY, tasks)

        return tasks

    def get_task(self, task_id: int) -> Optional[dict]:
        cache_key = self._task_item_cache_key(task_id)

        cached_task = cache.get(cache_key)

        if cached_task is not None:
            return cached_task

        task = self.repository.get_task_by_id(task_id)

        if task is not None:
            cache.set(cache_key, task)

        return task

    def update_task(self, task_id: int, task: TaskUpdate) -> Optional[dict]:
        updated_task = self.repository.update_task(
            task_id=task_id,
            title=task.title,
            done=task.done,
        )

        if updated_task is not None:
            cache.delete(
                self.TASK_LIST_CACHE_KEY,
                self._task_item_cache_key(task_id),
            )

        return updated_task

    def delete_task(self, task_id: int) -> bool:
        deleted = self.repository.delete_task(task_id)

        if deleted:
            cache.delete(
                self.TASK_LIST_CACHE_KEY,
                self._task_item_cache_key(task_id),
            )

        return deleted

    @staticmethod
    def _task_item_cache_key(task_id: int) -> str:
        return f"tasks:item:{task_id}"


task_service = TaskService(task_repository)
