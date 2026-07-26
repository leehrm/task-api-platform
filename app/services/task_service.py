import logging
from typing import Optional

from app.config.cache import Cache, cache
from app.models.task_model import TaskCreate, TaskUpdate
from app.repositories.task_repository import TaskRepository, task_repository
from app.services.notification_service import Notifier, notifier
from opentelemetry import trace


logger = logging.getLogger(__name__)


class TaskService:

    TASK_LIST_CACHE_KEY = "tasks:list"
    TASK_ITEM_LABEL = "tasks:item:{task_id}"
    TASK_INVALIDATE_LABEL = f"{TASK_LIST_CACHE_KEY},{TASK_ITEM_LABEL}"

    def __init__(
        self,
        repository: TaskRepository,
        cache_client: Cache = cache,
        notifier_client: Notifier = notifier,
    ) -> None:
        self.repository = repository
        self.cache = cache_client
        self.notifier = notifier_client

    def create_task(self, task: TaskCreate) -> dict:
        self._set_operation("create")
        created_task = self.repository.create_task(task.title)

        self.cache.delete(self.TASK_LIST_CACHE_KEY)

        return created_task

    def list_tasks(self) -> list[dict]:
        self._set_operation("list")
        cached_tasks = self.cache.get(self.TASK_LIST_CACHE_KEY)

        if cached_tasks is not None:
            return cached_tasks

        tasks = self.repository.list_tasks()
        self.cache.set(self.TASK_LIST_CACHE_KEY, tasks)

        return tasks

    def get_task(self, task_id: int) -> Optional[dict]:
        self._set_operation("get")
        cache_key = self._task_item_cache_key(task_id)

        cached_task = self.cache.get(cache_key, label=self.TASK_ITEM_LABEL)

        if cached_task is not None:
            return cached_task

        task = self.repository.get_task_by_id(task_id)

        if task is not None:
            self.cache.set(cache_key, task, label=self.TASK_ITEM_LABEL)

        return task

    def update_task(self, task_id: int, task: TaskUpdate) -> Optional[dict]:
        self._set_operation("update")
        result = self.repository.update_task(
            task_id=task_id,
            title=task.title,
            done=task.done,
        )

        if result is None:
            return None

        updated_task, became_done = result
        self._invalidate(task_id)

        if became_done:
            self._notify_completed(updated_task)

        return updated_task

    def delete_task(self, task_id: int) -> bool:
        self._set_operation("delete")
        deleted = self.repository.delete_task(task_id)

        if deleted:
            self._invalidate(task_id)

        return deleted

    def _notify_completed(self, task: dict) -> None:
        """완료 알림을 발송한다. 구현이 무엇이든 발송 실패는 호출자에게 전파하지 않는다."""
        # ponytail: best-effort 동기 발송, 보장 전달이 필요해지면 transactional outbox로 교체.
        try:
            self.notifier.task_completed(task)
        except Exception:
            logger.exception("event=notification_failed task_id=%s", task["id"])

    def _invalidate(self, task_id: int) -> None:
        self.cache.delete(
            self.TASK_LIST_CACHE_KEY,
            self._task_item_cache_key(task_id),
            label=self.TASK_INVALIDATE_LABEL,
        )

    @staticmethod
    def _task_item_cache_key(task_id: int) -> str:
        return f"tasks:item:{task_id}"

    @staticmethod
    def _set_operation(operation: str) -> None:
        span = trace.get_current_span()
        if span.is_recording():
            span.set_attribute("task.operation", operation)


task_service = TaskService(task_repository)
