import enum
from datetime import datetime, timezone
from typing import Optional, Sequence
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Enum, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from src.database.postgres import Base, get_db
from src.core.dependencies import get_current_user
from src.core.email import send_application_status_email, send_new_application_email, send_submission_email
from src.users.models import User, RoleEnum
from src.users.repository import UserRepository


# ── Model ────────────────────────────────────────────

class ApplicationStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    in_progress = "in_progress"
    submitted = "submitted"           # student submitted work
    revision_requested = "revision_requested"  # owner requests changes
    approved = "approved"             # owner approves work
    completed = "completed"           # final state


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    applicant_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    cover_letter = Column(Text)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.pending)
    submission_note = Column(Text)  # note when submitting work
    revision_note = Column(Text)    # note when requesting revision
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(),
                        onupdate=lambda: datetime.utcnow())

    project = relationship("Project", back_populates="applications")
    applicant = relationship("User", back_populates="applications")


# ── Schemas ──────────────────────────────────────────

class ApplicationCreate(BaseModel):
    project_id: int
    cover_letter: Optional[str] = None


class ApplicationUpdateStatus(BaseModel):
    status: ApplicationStatus
    note: Optional[str] = None  # for submission_note or revision_note


class ApplicationResponse(BaseModel):
    id: int
    project_id: int
    applicant_id: int
    cover_letter: Optional[str] = None
    status: ApplicationStatus
    submission_note: Optional[str] = None
    revision_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


# ── Repository ───────────────────────────────────────

class ApplicationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, app_id: int) -> Optional[Application]:
        return (await self.db.execute(select(Application).where(Application.id == app_id))).scalar_one_or_none()

    async def get_by_project_and_applicant(self, project_id: int, applicant_id: int) -> Optional[Application]:
        return (await self.db.execute(
            select(Application).where(Application.project_id == project_id, Application.applicant_id == applicant_id)
        )).scalar_one_or_none()

    async def get_by_project(self, project_id: int) -> Sequence[Application]:
        return (await self.db.execute(select(Application).where(Application.project_id == project_id))).scalars().all()

    async def get_by_applicant(self, applicant_id: int) -> Sequence[Application]:
        return (await self.db.execute(
            select(Application).where(Application.applicant_id == applicant_id).order_by(Application.created_at.desc())
        )).scalars().all()

    async def create(self, app: Application) -> Application:
        self.db.add(app)
        await self.db.flush()
        await self.db.refresh(app)
        return app

    async def update(self, app: Application) -> Application:
        await self.db.flush()
        await self.db.refresh(app)
        return app

    async def count(self) -> int:
        return (await self.db.execute(select(func.count(Application.id)))).scalar()


# ── Transition validation ────────────────────────────

VALID_TRANSITIONS = {
    ApplicationStatus.pending: [ApplicationStatus.accepted, ApplicationStatus.rejected],
    ApplicationStatus.accepted: [ApplicationStatus.in_progress],
    ApplicationStatus.in_progress: [ApplicationStatus.submitted],
    ApplicationStatus.submitted: [ApplicationStatus.approved, ApplicationStatus.revision_requested],
    ApplicationStatus.revision_requested: [ApplicationStatus.submitted],
    ApplicationStatus.approved: [ApplicationStatus.completed],
}


# ── Service ──────────────────────────────────────────

class ApplicationService:
    def __init__(self, db: AsyncSession):
        self.repo = ApplicationRepository(db)
        self.user_repo = UserRepository(db)

    async def apply(self, data: ApplicationCreate, current_user: User, bg: BackgroundTasks) -> Application:
        if current_user.role != RoleEnum.student:
            raise HTTPException(status_code=403, detail="Only students can apply")

        from src.projects.router import ProjectRepository
        project_repo = ProjectRepository(self.repo.db)
        project = await project_repo.get_by_id(data.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.status.value != "open":
            raise HTTPException(status_code=400, detail="Project is not open")
        if await self.repo.get_by_project_and_applicant(data.project_id, current_user.id):
            raise HTTPException(status_code=400, detail="Already applied")

        application = await self.repo.create(Application(
            project_id=data.project_id, applicant_id=current_user.id, cover_letter=data.cover_letter,
        ))

        # Email owner
        owner = await self.user_repo.get_by_id(project.owner_id)
        if owner:
            bg.add_task(send_new_application_email, owner.email, owner.username, project.title, current_user.username)

        return application

    async def update_status(self, app_id: int, data: ApplicationUpdateStatus,
                            current_user: User, bg: BackgroundTasks) -> Application:
        application = await self.repo.get_by_id(app_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        from src.projects.router import ProjectRepository
        project_repo = ProjectRepository(self.repo.db)
        project = await project_repo.get_by_id(application.project_id)

        # Validate who can perform transition
        is_owner = project.owner_id == current_user.id
        is_applicant = application.applicant_id == current_user.id
        is_admin = current_user.role == RoleEnum.admin

        # Owner/admin: accept, reject, approve, request_revision, complete
        # Applicant: submit, in_progress
        owner_statuses = {ApplicationStatus.accepted, ApplicationStatus.rejected,
                          ApplicationStatus.approved, ApplicationStatus.revision_requested, ApplicationStatus.completed}
        applicant_statuses = {ApplicationStatus.in_progress, ApplicationStatus.submitted}

        if data.status in owner_statuses and not (is_owner or is_admin):
            raise HTTPException(status_code=403, detail="Only project owner can perform this action")
        if data.status in applicant_statuses and not is_applicant:
            raise HTTPException(status_code=403, detail="Only applicant can perform this action")

        # Validate transition
        allowed = VALID_TRANSITIONS.get(application.status, [])
        if data.status not in allowed:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot transition from {application.status.value} to {data.status.value}. "
                       f"Allowed: {[s.value for s in allowed]}"
            )

        application.status = data.status
        if data.status == ApplicationStatus.submitted and data.note:
            application.submission_note = data.note
        if data.status == ApplicationStatus.revision_requested and data.note:
            application.revision_note = data.note

        application = await self.repo.update(application)

        # Send email notification
        applicant = await self.user_repo.get_by_id(application.applicant_id)
        if applicant:
            if data.status in owner_statuses:
                bg.add_task(send_application_status_email, applicant.email, applicant.username,
                            project.title, data.status.value)
            elif data.status == ApplicationStatus.submitted:
                owner = await self.user_repo.get_by_id(project.owner_id)
                if owner:
                    bg.add_task(send_submission_email, owner.email, owner.username,
                                project.title, applicant.username)

        return application

    async def get_by_project(self, project_id: int, current_user: User) -> Sequence[Application]:
        from src.projects.router import ProjectRepository
        project = await ProjectRepository(self.repo.db).get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.owner_id != current_user.id and current_user.role != RoleEnum.admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        return await self.repo.get_by_project(project_id)

    async def get_my(self, current_user: User) -> Sequence[Application]:
        return await self.repo.get_by_applicant(current_user.id)


# ── Router ───────────────────────────────────────────

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("/", response_model=ApplicationResponse, status_code=201)
async def apply(data: ApplicationCreate, bg: BackgroundTasks,
                db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await ApplicationService(db).apply(data, current_user, bg)


@router.put("/{app_id}/status", response_model=ApplicationResponse)
async def update_status(app_id: int, data: ApplicationUpdateStatus, bg: BackgroundTasks,
                        db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await ApplicationService(db).update_status(app_id, data, current_user, bg)


@router.get("/project/{project_id}", response_model=list[ApplicationResponse])
async def get_project_applications(project_id: int, db: AsyncSession = Depends(get_db),
                                   current_user: User = Depends(get_current_user)):
    return await ApplicationService(db).get_by_project(project_id, current_user)


@router.get("/my", response_model=list[ApplicationResponse])
async def get_my_applications(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await ApplicationService(db).get_my(current_user)
