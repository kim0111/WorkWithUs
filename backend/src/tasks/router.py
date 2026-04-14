from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query

from src.core.dependencies import get_current_user
from src.users.models import User
from src.tasks import service
from src.tasks.models import TaskPriority
from src.tasks.schemas import (
    TaskCreate, TaskUpdate, TaskResponse,
    CommentCreate, CommentResponse, ActivityResponse,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get("/project/{project_id}", response_model=list[TaskResponse])
async def list_project_tasks(
    project_id: int,
    assignee_id: Optional[int] = Query(default=None),
    priority: Optional[TaskPriority] = Query(default=None),
    deadline_before: Optional[datetime] = Query(default=None),
    current_user: User = Depends(get_current_user),
):
    return await service.list_tasks(project_id, current_user, assignee_id, priority, deadline_before)


@router.post("/project/{project_id}", response_model=TaskResponse, status_code=201)
async def create_task(project_id: int, data: TaskCreate,
                      current_user: User = Depends(get_current_user)):
    return await service.create_task(
        project_id, current_user, data.title, data.description,
        data.status, data.priority, data.assignee_id, data.deadline,
    )


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int, current_user: User = Depends(get_current_user)):
    return await service.get_task(task_id, current_user)


@router.put("/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, data: TaskUpdate,
                      current_user: User = Depends(get_current_user)):
    return await service.update_task(task_id, current_user, data.model_dump(exclude_unset=True))


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: int, current_user: User = Depends(get_current_user)):
    await service.delete_task(task_id, current_user)


@router.get("/{task_id}/comments", response_model=list[CommentResponse])
async def list_comments(task_id: int, current_user: User = Depends(get_current_user)):
    return await service.list_comments(task_id, current_user)


@router.post("/{task_id}/comments", response_model=CommentResponse, status_code=201)
async def add_comment(task_id: int, data: CommentCreate,
                      current_user: User = Depends(get_current_user)):
    return await service.add_comment(task_id, current_user, data.content)


@router.get("/{task_id}/activity", response_model=list[ActivityResponse])
async def list_activity(task_id: int, current_user: User = Depends(get_current_user)):
    return await service.list_activity(task_id, current_user)
