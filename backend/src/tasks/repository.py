from datetime import datetime
from typing import Optional
from src.tasks.models import Task, TaskComment, TaskActivity, TaskStatus, TaskPriority


async def create_task(project_id: int, created_by: int, title: str, description: str,
                      status: TaskStatus, priority: TaskPriority,
                      assignee_id: Optional[int], deadline: Optional[datetime]) -> Task:
    return await Task.create(
        project_id=project_id, created_by_id=created_by, title=title,
        description=description, status=status, priority=priority,
        assignee_id=assignee_id, deadline=deadline,
    )


async def get_task(task_id: int) -> Task | None:
    return await Task.filter(id=task_id).first()


async def list_project_tasks(project_id: int, assignee_id: Optional[int] = None,
                             priority: Optional[TaskPriority] = None,
                             deadline_before: Optional[datetime] = None) -> list[Task]:
    qs = Task.filter(project_id=project_id)
    if assignee_id is not None:
        qs = qs.filter(assignee_id=assignee_id)
    if priority is not None:
        qs = qs.filter(priority=priority)
    if deadline_before is not None:
        qs = qs.filter(deadline__lte=deadline_before)
    return await qs.order_by("created_at")


async def save_task(task: Task) -> None:
    await task.save()


async def delete_task(task_id: int) -> int:
    return await Task.filter(id=task_id).delete()


async def add_comment(task_id: int, author_id: int, content: str) -> TaskComment:
    return await TaskComment.create(task_id=task_id, author_id=author_id, content=content)


async def list_comments(task_id: int) -> list[TaskComment]:
    return await TaskComment.filter(task_id=task_id).order_by("created_at")


async def log_activity(task_id: int, actor_id: int, action: str,
                       from_value: Optional[str] = None,
                       to_value: Optional[str] = None) -> TaskActivity:
    return await TaskActivity.create(
        task_id=task_id, actor_id=actor_id, action=action,
        from_value=from_value, to_value=to_value,
    )


async def list_activity(task_id: int) -> list[TaskActivity]:
    return await TaskActivity.filter(task_id=task_id).order_by("-created_at")
