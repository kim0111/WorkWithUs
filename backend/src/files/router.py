from typing import Optional
from fastapi import APIRouter, Depends, UploadFile, File, Query
from src.core.dependencies import get_current_user
from src.users.models import User
from src.files import service
from src.files.schemas import FileResponse

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/project/{project_id}", response_model=FileResponse, status_code=201)
async def upload_project_file(
    project_id: int,
    file: UploadFile = File(...),
    file_type: str = Query("attachment", pattern="^(attachment|submission)$"),
    current_user: User = Depends(get_current_user),
):
    content = await file.read()
    return await service.upload_project_file(
        project_id, current_user, content,
        file.filename or "unnamed_file", file.content_type, file_type,
    )


@router.get("/project/{project_id}", response_model=list[FileResponse])
async def list_project_files(
    project_id: int,
    file_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    return await service.list_project_files(project_id, file_type)


@router.get("/{file_id}/download")
async def download_project_file(file_id: int, current_user: User = Depends(get_current_user)):
    return await service.download_project_file(file_id)


@router.delete("/{file_id}", status_code=204)
async def delete_project_file(file_id: int, current_user: User = Depends(get_current_user)):
    await service.delete_project_file(file_id, current_user)
