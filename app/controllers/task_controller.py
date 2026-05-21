from fastapi import HTTPException, Response, status

from app.models.task_model import TaskCreate, TaskUpdate
from app.services.task_service import TaskService, task_service


class TaskController:

    def __init__(self, service: TaskService) -> None:
        self.service = service

    def create_task(self, task: TaskCreate):
        return self.service.create_task(task)

    def list_tasks(self):
        return self.service.list_tasks()

    def get_task(self, task_id: int):
        task = self.service.get_task(task_id)

        if task is None:
            raise HTTPException(status_code=404, detail="Task not found")

        return task

    def update_task(self, task_id: int, task: TaskUpdate):
        updated_task = self.service.update_task(task_id, task)

        if updated_task is None:
            raise HTTPException(status_code=404, detail="Task not found")

        return updated_task

    def delete_task(self, task_id: int):
        deleted = self.service.delete_task(task_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Task not found")

        return Response(status_code=status.HTTP_204_NO_CONTENT)


task_controller = TaskController(task_service)
