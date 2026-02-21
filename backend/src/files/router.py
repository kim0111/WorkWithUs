from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.postgres import get_db
from src.core.dependencies import get_current_user
from src.core.config import settings
from src.core.minio_client import upload_file, get_file_url, delete_file
from src.users.models import User, RoleEnum
from src.projects.models import ProjectFile
from src.projects.router import ProjectRepository


# ── Schemas ──────────────────────────────────────────

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


# ── Router ───────────────────────────────────────────

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/project/{project_id}", response_model=FileResponse, status_code=201)
async def upload_project_file(
    project_id: int,
    file: UploadFile = File(...),
    file_type: str = Query("attachment", regex="^(attachment|submission)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a file to a project. file_type: 'attachment' (ТЗ) or 'submission' (student work)."""
    project = await ProjectRepository(db).get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Permission checks
    is_owner = project.owner_id == current_user.id
    is_applicant = any(a.applicant_id == current_user.id for a in project.applications)

    if file_type == "attachment" and not (is_owner or current_user.role == RoleEnum.admin):
        raise HTTPException(status_code=403, detail="Only project owner can upload attachments")
    if file_type == "submission" and not is_applicant:
        raise HTTPException(status_code=403, detail="Only applicants can upload submissions")

    # File size check
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large (max {settings.MAX_FILE_SIZE // 1024 // 1024}MB)")

    # Upload to MinIO
    bucket = settings.MINIO_BUCKET_PROJECTS if file_type == "attachment" else settings.MINIO_BUCKET_SUBMISSIONS
    object_name = upload_file(bucket, content, file.filename, file.content_type or "application/octet-stream")

    # Save metadata to PostgreSQL
    project_file = ProjectFile(
        project_id=project_id, uploader_id=current_user.id,
        filename=file.filename, object_name=object_name,
        file_size=len(content), content_type=file.content_type,
        file_type=file_type,
    )
    db.add(project_file)
    await db.flush()
    await db.refresh(project_file)

    return project_file


@router.get("/project/{project_id}", response_model=list[FileResponse])
async def list_project_files(
    project_id: int,
    file_type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(ProjectFile).where(ProjectFile.project_id == project_id)
    if file_type:
        query = query.where(ProjectFile.file_type == file_type)
    result = await db.execute(query.order_by(ProjectFile.created_at.desc()))
    files = result.scalars().all()

    # Add download URLs
    response = []
    for f in files:
        bucket = settings.MINIO_BUCKET_PROJECTS if f.file_type == "attachment" else settings.MINIO_BUCKET_SUBMISSIONS
        try:
            url = get_file_url(bucket, f.object_name)
        except Exception:
            url = None
        data = FileResponse.model_validate(f)
        data.download_url = url
        response.append(data)
    return response


@router.get("/{file_id}/download")
async def get_download_url(file_id: int, db: AsyncSession = Depends(get_db),
                           current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ProjectFile).where(ProjectFile.id == file_id))
    pf = result.scalar_one_or_none()
    if not pf:
        raise HTTPException(status_code=404, detail="File not found")

    bucket = settings.MINIO_BUCKET_PROJECTS if pf.file_type == "attachment" else settings.MINIO_BUCKET_SUBMISSIONS
    url = get_file_url(bucket, pf.object_name, expires_hours=2)
    return {"download_url": url, "filename": pf.filename}


@router.delete("/{file_id}", status_code=204)
async def delete_project_file(file_id: int, db: AsyncSession = Depends(get_db),
                               current_user: User = Depends(get_current_user)):
    result = await db.execute(select(ProjectFile).where(ProjectFile.id == file_id))
    pf = result.scalar_one_or_none()
    if not pf:
        raise HTTPException(status_code=404, detail="File not found")
    if pf.uploader_id != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    bucket = settings.MINIO_BUCKET_PROJECTS if pf.file_type == "attachment" else settings.MINIO_BUCKET_SUBMISSIONS
    delete_file(bucket, pf.object_name)
    await db.delete(pf)
