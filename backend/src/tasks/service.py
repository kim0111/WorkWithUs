from datetime import datetime
from typing import Optional
from fastapi import HTTPException

from src.tasks import repository
from src.tasks.models import Task, TaskComment, TaskActivity, TaskStatus, TaskPriority
from src.tasks.schemas import TaskResponse, CommentResponse, ActivityResponse
from src.projects.models import Project
from src.users.models import User, RoleEnum
from src.teams import repository as teams_repo
from src.notifications.service import create_notification


# ── Auth helpers ──────────────────────────────────────────

async def _project_or_404(project_id: int) -> Project:
    project = await Project.filter(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


async def _task_or_404(task_id: int) -> Task:
    task = await repository.get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


async def _ensure_can_view(project: Project, user: User) -> None:
    if user.role == RoleEnum.admin or project.owner_id == user.id:
        return
    membership = await teams_repo.get_by_project_and_user(project.id, user.id)
    if membership:
        return
    raise HTTPException(status_code=403, detail="Not a team member on this project")


async def _ensure_can_edit(project: Project, user: User) -> None:
    # Same rule as view for now — team members can move/edit cards, owner/admin always can.
    await _ensure_can_view(project, user)


async def _ensure_can_delete(project: Project, user: User) -> None:
    if user.role == RoleEnum.admin or project.owner_id == user.id:
        return
    membership = await teams_repo.get_by_project_and_user(project.id, user.id)
    if membership and membership.is_lead:
        return
    raise HTTPException(status_code=403, detail="Only project owner, admin, or team lead can delete tasks")


# ── Response mappers ──────────────────────────────────────

async def _task_to_response(task: Task) -> TaskResponse:
    assignee_username = None
    if task.assignee_id:
        u = await User.filter(id=task.assignee_id).only("id", "username").first()
        if u:
            assignee_username = u.username
    return TaskResponse(
        id=task.id,
        project_id=task.project_id,
        title=task.title,
        description=task.description or "",
        status=task.status,
        priority=task.priority,
        assignee_id=task.assignee_id,
        assignee_username=assignee_username,
        deadline=task.deadline,
        created_by=task.created_by_id,
        created_at=task.created_at,
        updated_at=task.updated_at,
    )


async def _comment_to_response(comment: TaskComment) -> CommentResponse:
    u = await User.filter(id=comment.author_id).only("id", "username").first()
    return CommentResponse(
        id=comment.id,
        task_id=comment.task_id,
        author_id=comment.author_id,
        author_username=u.username if u else "",
        content=comment.content,
        created_at=comment.created_at,
    )


async def _activity_to_response(activity: TaskActivity) -> ActivityResponse:
    u = await User.filter(id=activity.actor_id).only("id", "username").first()
    return ActivityResponse(
        id=activity.id,
        task_id=activity.task_id,
        actor_id=activity.actor_id,
        actor_username=u.username if u else "",
        action=activity.action,
        from_value=activity.from_value,
        to_value=activity.to_value,
        created_at=activity.created_at,
    )


# ── Notification helper ───────────────────────────────────

async def _notify_assignee(task: Task, title: str, message: str, acting_user_id: int) -> None:
    if task.assignee_id and task.assignee_id != acting_user_id:
        await create_notification(
            task.assignee_id, title, message,
            notification_type="task", link=f"/projects/{task.project_id}/board",
        )


# ── Public service methods ────────────────────────────────

async def list_tasks(project_id: int, user: User,
                     assignee_id: Optional[int], priority: Optional[TaskPriority],
                     deadline_before: Optional[datetime]) -> list[TaskResponse]:
    project = await _project_or_404(project_id)
    await _ensure_can_view(project, user)
    tasks = await repository.list_project_tasks(project_id, assignee_id, priority, deadline_before)
    return [await _task_to_response(t) for t in tasks]


async def get_task(task_id: int, user: User) -> TaskResponse:
    task = await _task_or_404(task_id)
    project = await _project_or_404(task.project_id)
    await _ensure_can_view(project, user)
    return await _task_to_response(task)


async def create_task(project_id: int, user: User, title: str, description: str,
                      status: TaskStatus, priority: TaskPriority,
                      assignee_id: Optional[int], deadline: Optional[datetime]) -> TaskResponse:
    project = await _project_or_404(project_id)
    await _ensure_can_edit(project, user)

    if assignee_id is not None:
        target = await User.filter(id=assignee_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Assignee not found")
        # Assignee must be owner or a team member on this project
        if target.id != project.owner_id:
            membership = await teams_repo.get_by_project_and_user(project_id, assignee_id)
            if not membership:
                raise HTTPException(status_code=400, detail="Assignee is not on the project team")

    task = await repository.create_task(
        project_id=project_id, created_by=user.id, title=title, description=description,
        status=status, priority=priority, assignee_id=assignee_id, deadline=deadline,
    )
    await repository.log_activity(task.id, user.id, "created", None, status.value)

    if assignee_id and assignee_id != user.id:
        await create_notification(
            assignee_id, "Task Assigned",
            f"You were assigned to task '{title}'",
            notification_type="task", link=f"/projects/{project_id}/board",
        )

    return await _task_to_response(task)


async def update_task(task_id: int, user: User, data: dict) -> TaskResponse:
    task = await _task_or_404(task_id)
    project = await _project_or_404(task.project_id)
    await _ensure_can_edit(project, user)

    old_status = task.status
    old_assignee_id = task.assignee_id
    changed: list[tuple[str, Optional[str], Optional[str]]] = []

    if "title" in data and data["title"] is not None and data["title"] != task.title:
        changed.append(("title", task.title, data["title"]))
        task.title = data["title"]

    if "description" in data and data["description"] is not None:
        if data["description"] != (task.description or ""):
            changed.append(("description", None, None))
            task.description = data["description"]

    if "status" in data and data["status"] is not None and data["status"] != task.status:
        changed.append(("status", task.status.value, data["status"].value))
        task.status = data["status"]

    if "priority" in data and data["priority"] is not None and data["priority"] != task.priority:
        changed.append(("priority", task.priority.value, data["priority"].value))
        task.priority = data["priority"]

    if "deadline" in data and data["deadline"] != task.deadline:
        old = task.deadline.isoformat() if task.deadline else None
        new = data["deadline"].isoformat() if data["deadline"] else None
        changed.append(("deadline", old, new))
        task.deadline = data["deadline"]

    if "assignee_id" in data and data["assignee_id"] != task.assignee_id:
        new_id = data["assignee_id"]
        if new_id is not None:
            target = await User.filter(id=new_id).first()
            if not target:
                raise HTTPException(status_code=404, detail="Assignee not found")
            if target.id != project.owner_id:
                membership = await teams_repo.get_by_project_and_user(project.id, new_id)
                if not membership:
                    raise HTTPException(status_code=400, detail="Assignee is not on the project team")
        changed.append(("assignee", str(task.assignee_id) if task.assignee_id else None,
                        str(new_id) if new_id else None))
        task.assignee_id = new_id

    if not changed:
        return await _task_to_response(task)

    await repository.save_task(task)

    for action, from_v, to_v in changed:
        await repository.log_activity(task.id, user.id, action, from_v, to_v)

    # Notify assignee about changes
    if task.status != old_status:
        await _notify_assignee(
            task, "Task Updated",
            f"Task '{task.title}' moved to {task.status.value}",
            user.id,
        )
    if task.assignee_id and task.assignee_id != old_assignee_id and task.assignee_id != user.id:
        await create_notification(
            task.assignee_id, "Task Assigned",
            f"You were assigned to task '{task.title}'",
            notification_type="task", link=f"/projects/{task.project_id}/board",
        )

    return await _task_to_response(task)


async def delete_task(task_id: int, user: User) -> None:
    task = await _task_or_404(task_id)
    project = await _project_or_404(task.project_id)
    await _ensure_can_delete(project, user)
    await repository.delete_task(task_id)


async def add_comment(task_id: int, user: User, content: str) -> CommentResponse:
    task = await _task_or_404(task_id)
    project = await _project_or_404(task.project_id)
    await _ensure_can_view(project, user)

    comment = await repository.add_comment(task_id, user.id, content)
    await repository.log_activity(task_id, user.id, "commented", None, None)

    if task.assignee_id and task.assignee_id != user.id:
        await create_notification(
            task.assignee_id, "New Task Comment",
            f"New comment on task '{task.title}'",
            notification_type="task", link=f"/projects/{task.project_id}/board",
        )

    return await _comment_to_response(comment)


async def list_comments(task_id: int, user: User) -> list[CommentResponse]:
    task = await _task_or_404(task_id)
    project = await _project_or_404(task.project_id)
    await _ensure_can_view(project, user)
    comments = await repository.list_comments(task_id)
    return [await _comment_to_response(c) for c in comments]


async def list_activity(task_id: int, user: User) -> list[ActivityResponse]:
    task = await _task_or_404(task_id)
    project = await _project_or_404(task.project_id)
    await _ensure_can_view(project, user)
    activities = await repository.list_activity(task_id)
    return [await _activity_to_response(a) for a in activities]
