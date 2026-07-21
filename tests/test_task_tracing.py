from unittest.mock import Mock, patch

from app.services.task_service import TaskService


def test_task_operation_is_added_to_current_span():
    span = Mock()
    span.is_recording.return_value = True

    with patch("app.services.task_service.trace.get_current_span", return_value=span):
        TaskService._set_operation("list")

    span.set_attribute.assert_called_once_with("task.operation", "list")
