import io
import os
import re
from fastapi import HTTPException
from fastapi.responses import StreamingResponse
from src.core.config import settings
from src.core.minio_client import upload_file as minio_upload, delete_file as minio_delete, download_file as minio_download
from src.files import repository
from src.files.schemas import FileResponse
from src.projects.models import ProjectFile
from src.users.models import User, RoleEnum

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".txt", ".csv", ".zip", ".rar", ".7z",
    ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs",
    ".json", ".xml", ".yaml", ".yml", ".md",
}


def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    filename = re.sub(r'[^\w\s\-.]', '_', filename)
    filename = filename.strip('. ')
    return filename or "unnamed_file"


def _get_bucket(file_type: str) -> str:
    return settings.MINIO_BUCKET_PROJECTS if file_type == "attachment" else settings.MINIO_BUCKET_SUBMISSIONS


async def upload_project_file(project_id: int, user: User, file_content: bytes,
                              filename: str, content_type: str | None,
                              file_type: str) -> ProjectFile:
    project = await repository.get_project_with_applications(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    is_owner = project.owner_id == user.id
    applications = await project.applications.all()
    is_applicant = any(a.applicant_id == user.id for a in applications)

    if file_type == "attachment" and not (is_owner or user.role == RoleEnum.admin):
        raise HTTPException(status_code=403, detail="Only project owner can upload attachments")
    if file_type == "submission" and not is_applicant:
        raise HTTPException(status_code=403, detail="Only applicants can upload submissions")

    safe_filename = sanitize_filename(filename)
    ext = os.path.splitext(safe_filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed")
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large (max {settings.MAX_FILE_SIZE // 1024 // 1024}MB)")

    bucket = _get_bucket(file_type)
    object_name = minio_upload(bucket, file_content, safe_filename, content_type or "application/octet-stream")

    return await repository.create_file(
        project_id, user.id, safe_filename, object_name, len(file_content), content_type, file_type,
    )


async def list_project_files(project_id: int, file_type: str | None) -> list[FileResponse]:
    files = await repository.list_files(project_id, file_type)
    result = []
    for f in files:
        data = FileResponse.model_validate(f)
        data.download_url = f"{settings.API_PREFIX}/files/{f.id}/download"
        result.append(data)
    return result


async def download_project_file(file_id: int) -> StreamingResponse:
    pf = await repository.get_file_by_id(file_id)
    if not pf:
        raise HTTPException(status_code=404, detail="File not found")

    bucket = _get_bucket(pf.file_type)
    try:
        file_data = minio_download(bucket, pf.object_name)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found in storage")

    content_type = pf.content_type or "application/octet-stream"
    return StreamingResponse(
        io.BytesIO(file_data),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{pf.filename}"'},
    )


async def delete_project_file(file_id: int, user: User) -> None:
    pf = await repository.get_file_by_id(file_id)
    if not pf:
        raise HTTPException(status_code=404, detail="File not found")
    if pf.uploader_id != user.id and user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    bucket = _get_bucket(pf.file_type)
    minio_delete(bucket, pf.object_name)
    await repository.delete_file(pf)
