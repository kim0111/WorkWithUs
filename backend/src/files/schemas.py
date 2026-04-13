from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class FileResponse(BaseModel):
    id: int
    project_id: int
    uploader_id: int
    filename: str
    object_name: str
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    file_type: str
    download_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
