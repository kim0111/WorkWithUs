from uuid import UUID

from fastapi import APIRouter, Depends, UploadFile

from src.auth.dependencies import get_current_user, require_role
from src.files import service
from src.files.schemas import FileDownloadRead, FileRead
from src.projects.service import get_project_model
from src.users.models import User, UserRole

router = APIRouter()


@router.post("", response_model=FileRead, status_code=201)
async def upload_file(
    project_id: UUID,
    file: UploadFile,
    user: User = Depends(require_role(UserRole.COMPANY)),
):
    project = await get_project_model(project_id)
    return await service.upload_file(project, user, file)


@router.get("", response_model=list[FileRead])
async def list_files(
    project_id: UUID,
    _: User = Depends(get_current_user),
):
    return await service.list_files(project_id)


@router.get("/{file_id}/download", response_model=FileDownloadRead)
async def download_file(
    file_id: UUID,
    _: User = Depends(get_current_user),
):
    return await service.download_file(file_id)


@router.delete("/{file_id}", status_code=204)
async def delete_file(
    file_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
):
    await service.delete_file(file_id, user)
