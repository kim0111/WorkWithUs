import uuid as _uuid
from uuid import UUID

from fastapi import HTTPException, UploadFile, status

from src.config import settings
from src.files import storage
from src.files.models import FileAttachment
from src.files.schemas import FileDownloadRead, FileRead
from src.projects.models import Project
from src.users.models import User


def _file_to_read(f: FileAttachment) -> FileRead:
    return FileRead(
        id=f.id,
        project_id=f.project_id,
        uploaded_by_id=f.uploaded_by_id,
        original_filename=f.original_filename,
        content_type=f.content_type,
        size_bytes=f.size_bytes,
        created_at=f.created_at,
    )


async def upload_file(project: Project, user: User, file: UploadFile) -> FileRead:
    if project.company_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the project owner")

    data = await file.read()
    if len(data) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit",
        )

    storage_key = f"projects/{project.id}/{_uuid.uuid4()}_{file.filename}"
    await storage.upload_file(storage_key, data, file.content_type or "application/octet-stream")

    attachment = await FileAttachment.create(
        project=project,
        uploaded_by=user,
        original_filename=file.filename or "unknown",
        storage_key=storage_key,
        content_type=file.content_type or "application/octet-stream",
        size_bytes=len(data),
    )
    return _file_to_read(attachment)


async def list_files(project_id: UUID) -> list[FileRead]:
    files = await FileAttachment.filter(project_id=project_id).order_by("-created_at")
    return [_file_to_read(f) for f in files]


async def download_file(file_id: UUID) -> FileDownloadRead:
    f = await FileAttachment.get_or_none(id=file_id)
    if not f:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    url = await storage.get_presigned_url(f.storage_key)
    return FileDownloadRead(url=url, filename=f.original_filename)


async def delete_file(file_id: UUID, user: User) -> None:
    f = await FileAttachment.get_or_none(id=file_id)
    if not f:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")

    project = await Project.get(id=f.project_id)
    if project.company_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the project owner")

    await storage.delete_file(f.storage_key)
    await f.delete()
