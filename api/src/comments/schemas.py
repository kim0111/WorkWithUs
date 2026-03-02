from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CommentCreate(BaseModel):
    body: str
    parent_id: UUID | None = None


class CommentRead(BaseModel):
    id: UUID
    application_id: UUID
    author_id: UUID
    body: str
    parent_id: UUID | None
    created_at: datetime
    replies: list["CommentRead"] = []
