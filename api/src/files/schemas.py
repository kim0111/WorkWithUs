from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class FileRead(BaseModel):
    id: UUID
    project_id: UUID
    uploaded_by_id: UUID
    original_filename: str
    content_type: str
    size_bytes: int
    created_at: datetime


class FileDownloadRead(BaseModel):
    url: str
    filename: str
