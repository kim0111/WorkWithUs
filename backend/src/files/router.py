import io
import os
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from src.core.dependencies import get_current_user
from src.core.config import settings
from src.core.minio_client import upload_file, delete_file, download_file
from src.users.models import User, RoleEnum
from src.projects.models import Project, ProjectFile

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


# -- Schemas --

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


# -- Router --

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/project/{project_id}", response_model=FileResponse, status_code=201)
async def upload_project_file(
    project_id: int,
    file: UploadFile = File(...),
    file_type: str = Query("attachment", pattern="^(attachment|submission)$"),
    current_user: User = Depends(get_current_user),
):
    project = await Project.filter(id=project_id).prefetch_related("applications").first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    is_owner = project.owner_id == current_user.id
    applications = await project.applications.all()
    is_applicant = any(a.applicant_id == current_user.id for a in applications)

    if file_type == "attachment" and not (is_owner or current_user.role == RoleEnum.admin):
        raise HTTPException(status_code=403, detail="Only project owner can upload attachments")
    if file_type == "submission" and not is_applicant:
        raise HTTPException(status_code=403, detail="Only applicants can upload submissions")

    safe_filename = sanitize_filename(file.filename or "unnamed_file")
    ext = os.path.splitext(safe_filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed")

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large (max {settings.MAX_FILE_SIZE // 1024 // 1024}MB)")

    bucket = settings.MINIO_BUCKET_PROJECTS if file_type == "attachment" else settings.MINIO_BUCKET_SUBMISSIONS
    object_name = upload_file(bucket, content, safe_filename, file.content_type or "application/octet-stream")

    project_file = await ProjectFile.create(
        project_id=project_id, uploader_id=current_user.id,
        filename=safe_filename, object_name=object_name,
        file_size=len(content), content_type=file.content_type,
        file_type=file_type,
    )
    return project_file


@router.get("/project/{project_id}", response_model=list[FileResponse])
async def list_project_files(
    project_id: int,
    file_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    filters = {"project_id": project_id}
    if file_type:
        filters["file_type"] = file_type
    files = await ProjectFile.filter(**filters).order_by("-created_at")

    response = []
    for f in files:
        data = FileResponse.model_validate(f)
        data.download_url = f"{settings.API_PREFIX}/files/{f.id}/download"
        response.append(data)
    return response


@router.get("/{file_id}/download")
async def download_project_file(file_id: int, current_user: User = Depends(get_current_user)):
    pf = await ProjectFile.filter(id=file_id).first()
    if not pf:
        raise HTTPException(status_code=404, detail="File not found")

    bucket = settings.MINIO_BUCKET_PROJECTS if pf.file_type == "attachment" else settings.MINIO_BUCKET_SUBMISSIONS
    try:
        file_data = download_file(bucket, pf.object_name)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found in storage")

    content_type = pf.content_type or "application/octet-stream"
    return StreamingResponse(
        io.BytesIO(file_data),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{pf.filename}"'},
    )


@router.delete("/{file_id}", status_code=204)
async def delete_project_file(file_id: int, current_user: User = Depends(get_current_user)):
    pf = await ProjectFile.filter(id=file_id).first()
    if not pf:
        raise HTTPException(status_code=404, detail="File not found")
    if pf.uploader_id != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    bucket = settings.MINIO_BUCKET_PROJECTS if pf.file_type == "attachment" else settings.MINIO_BUCKET_SUBMISSIONS
    delete_file(bucket, pf.object_name)
    await pf.delete()
