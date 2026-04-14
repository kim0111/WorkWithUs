from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from src.tasks.models import TaskStatus, TaskPriority


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = ""
    status: TaskStatus = TaskStatus.todo
    priority: TaskPriority = TaskPriority.medium
    assignee_id: Optional[int] = None
    deadline: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assignee_id: Optional[int] = None
    deadline: Optional[datetime] = None


class TaskResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    assignee_id: Optional[int] = None
    assignee_username: Optional[str] = None
    deadline: Optional[datetime] = None
    created_by: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CommentCreate(BaseModel):
    content: str = Field(min_length=1)


class CommentResponse(BaseModel):
    id: int
    task_id: int
    author_id: int
    author_username: str = ""
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ActivityResponse(BaseModel):
    id: int
    task_id: int
    actor_id: int
    actor_username: str = ""
    action: str
    from_value: Optional[str] = None
    to_value: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
