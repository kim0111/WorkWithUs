from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.schemas import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from app.services.services import ApplicationService
from app.api.deps import get_current_user
from app.models.models import User

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("/", response_model=ApplicationResponse, status_code=201)
async def apply(
    data: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ApplicationService(db)
    return await service.apply(data, current_user)


@router.put("/{app_id}/status", response_model=ApplicationResponse)
async def update_status(
    app_id: int,
    data: ApplicationUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ApplicationService(db)
    return await service.update_status(app_id, data, current_user)


@router.get("/project/{project_id}", response_model=list[ApplicationResponse])
async def get_project_applications(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ApplicationService(db)
    return await service.get_project_applications(project_id, current_user)


@router.get("/my", response_model=list[ApplicationResponse])
async def get_my_applications(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ApplicationService(db)
    return await service.get_my_applications(current_user)
