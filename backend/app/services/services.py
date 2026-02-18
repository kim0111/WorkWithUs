from typing import Optional, Sequence
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.models.models import (
    User, Skill, Project, Application, PortfolioItem,
    Review, Notification, CompanyProfile, StudentProfile,
    RoleEnum, ProjectStatus, ApplicationStatus
)
from app.schemas.schemas import (
    RegisterRequest, TokenResponse, UserUpdate,
    ProjectCreate, ProjectUpdate, ApplicationCreate, ApplicationUpdate,
    PortfolioItemCreate, ReviewCreate, SkillCreate,
    CompanyProfileCreate, StudentProfileCreate, AdminUserUpdate, StatsResponse,
)
from app.repositories.repositories import (
    UserRepository, SkillRepository, ProjectRepository,
    ApplicationRepository, PortfolioRepository, ReviewRepository,
    NotificationRepository, CompanyProfileRepository, StudentProfileRepository,
)


# ── Auth Service ──────────────────────────────────────

class AuthService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)
        self.company_repo = CompanyProfileRepository(db)
        self.student_repo = StudentProfileRepository(db)
        self.db = db

    async def register(self, data: RegisterRequest) -> User:
        if await self.user_repo.get_by_email(data.email):
            raise HTTPException(status_code=400, detail="Email already registered")
        if await self.user_repo.get_by_username(data.username):
            raise HTTPException(status_code=400, detail="Username already taken")

        user = User(
            email=data.email,
            username=data.username,
            hashed_password=hash_password(data.password),
            full_name=data.full_name,
            role=data.role,
        )
        user = await self.user_repo.create(user)

        # Create role-specific profile
        if data.role == RoleEnum.company:
            profile = CompanyProfile(user_id=user.id, company_name=data.username)
            await self.company_repo.create(profile)
        elif data.role == RoleEnum.student:
            profile = StudentProfile(user_id=user.id)
            await self.student_repo.create(profile)

        return user

    async def login(self, username: str, password: str) -> TokenResponse:
        user = await self.user_repo.get_by_username(username)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if user.is_blocked:
            raise HTTPException(status_code=403, detail="Account is blocked")

        token_data = {"sub": str(user.id), "role": user.role.value}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        user = await self.user_repo.get_by_id(int(payload["sub"]))
        if not user:
            raise HTTPException(status_code=401, detail="User not found")

        token_data = {"sub": str(user.id), "role": user.role.value}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
        )

    async def get_current_user(self, token: str) -> User:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await self.user_repo.get_by_id(int(payload["sub"]))
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if user.is_blocked:
            raise HTTPException(status_code=403, detail="Account is blocked")
        return user


# ── User Service ──────────────────────────────────────

class UserService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)
        self.skill_repo = SkillRepository(db)

    async def get_user(self, user_id: int) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def update_user(self, user_id: int, data: UserUpdate, current_user: User) -> User:
        if current_user.id != user_id and current_user.role != RoleEnum.admin:
            raise HTTPException(status_code=403, detail="Not authorized")

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        return await self.user_repo.update(user)

    async def add_skill_to_user(self, user_id: int, skill_id: int, current_user: User):
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        skill = await self.skill_repo.get_by_id(skill_id)
        if not skill:
            raise HTTPException(status_code=404, detail="Skill not found")
        await self.user_repo.add_skill(user_id, skill_id)

    async def remove_skill_from_user(self, user_id: int, skill_id: int, current_user: User):
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        await self.user_repo.remove_skill(user_id, skill_id)

    async def get_all_users(self, skip: int = 0, limit: int = 20) -> Sequence[User]:
        return await self.user_repo.get_all(skip, limit)


# ── Skill Service ─────────────────────────────────────

class SkillService:
    def __init__(self, db: AsyncSession):
        self.skill_repo = SkillRepository(db)

    async def create_skill(self, data: SkillCreate) -> Skill:
        existing = await self.skill_repo.get_by_name(data.name)
        if existing:
            raise HTTPException(status_code=400, detail="Skill already exists")
        skill = Skill(name=data.name, category=data.category)
        return await self.skill_repo.create(skill)

    async def get_all_skills(self) -> Sequence[Skill]:
        return await self.skill_repo.get_all()


# ── Project Service ───────────────────────────────────

class ProjectService:
    def __init__(self, db: AsyncSession):
        self.project_repo = ProjectRepository(db)
        self.skill_repo = SkillRepository(db)
        self.notification_repo = NotificationRepository(db)

    async def create_project(self, data: ProjectCreate, current_user: User) -> Project:
        if data.is_student_project and current_user.role != RoleEnum.student:
            raise HTTPException(status_code=403, detail="Only students can create student projects")
        if not data.is_student_project and current_user.role not in (RoleEnum.company, RoleEnum.admin):
            raise HTTPException(status_code=403, detail="Only companies can create company projects")

        project = Project(
            title=data.title,
            description=data.description,
            owner_id=current_user.id,
            max_participants=data.max_participants,
            deadline=data.deadline,
            is_student_project=data.is_student_project,
        )
        project = await self.project_repo.create(project)

        if data.skill_ids:
            skills = await self.skill_repo.get_by_ids(data.skill_ids)
            project.required_skills = list(skills)

        return project

    async def get_project(self, project_id: int) -> Project:
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    async def get_projects(
        self,
        page: int = 1,
        size: int = 20,
        status: Optional[ProjectStatus] = None,
        owner_id: Optional[int] = None,
        is_student_project: Optional[bool] = None,
        search: Optional[str] = None,
    ):
        skip = (page - 1) * size
        items = await self.project_repo.get_all(skip, size, status, owner_id, is_student_project, search)
        total = await self.project_repo.count(status, owner_id, is_student_project, search)
        return {"items": items, "total": total, "page": page, "size": size}

    async def update_project(self, project_id: int, data: ProjectUpdate, current_user: User) -> Project:
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.owner_id != current_user.id and current_user.role != RoleEnum.admin:
            raise HTTPException(status_code=403, detail="Not authorized")

        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        return await self.project_repo.update(project)

    async def delete_project(self, project_id: int, current_user: User):
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.owner_id != current_user.id and current_user.role != RoleEnum.admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        await self.project_repo.delete(project)


# ── Application Service ──────────────────────────────

class ApplicationService:
    def __init__(self, db: AsyncSession):
        self.app_repo = ApplicationRepository(db)
        self.project_repo = ProjectRepository(db)
        self.notification_repo = NotificationRepository(db)

    async def apply(self, data: ApplicationCreate, current_user: User) -> Application:
        if current_user.role != RoleEnum.student:
            raise HTTPException(status_code=403, detail="Only students can apply")

        project = await self.project_repo.get_by_id(data.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.status != ProjectStatus.open:
            raise HTTPException(status_code=400, detail="Project is not open")

        existing = await self.app_repo.get_by_project_and_applicant(data.project_id, current_user.id)
        if existing:
            raise HTTPException(status_code=400, detail="Already applied")

        application = Application(
            project_id=data.project_id,
            applicant_id=current_user.id,
            cover_letter=data.cover_letter,
        )
        application = await self.app_repo.create(application)

        # Notify project owner
        notification = Notification(
            user_id=project.owner_id,
            title="New Application",
            message=f"New application for project '{project.title}'",
        )
        await self.notification_repo.create(notification)

        return application

    async def update_status(self, app_id: int, data: ApplicationUpdate, current_user: User) -> Application:
        application = await self.app_repo.get_by_id(app_id)
        if not application:
            raise HTTPException(status_code=404, detail="Application not found")

        project = await self.project_repo.get_by_id(application.project_id)
        if project.owner_id != current_user.id and current_user.role != RoleEnum.admin:
            raise HTTPException(status_code=403, detail="Not authorized")

        application.status = data.status
        application = await self.app_repo.update(application)

        # Notify applicant
        notification = Notification(
            user_id=application.applicant_id,
            title="Application Status Updated",
            message=f"Your application for '{project.title}' is now {data.status.value}",
        )
        await self.notification_repo.create(notification)

        return application

    async def get_project_applications(self, project_id: int, current_user: User) -> Sequence[Application]:
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.owner_id != current_user.id and current_user.role != RoleEnum.admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        return await self.app_repo.get_by_project(project_id)

    async def get_my_applications(self, current_user: User) -> Sequence[Application]:
        return await self.app_repo.get_by_applicant(current_user.id)


# ── Portfolio Service ─────────────────────────────────

class PortfolioService:
    def __init__(self, db: AsyncSession):
        self.portfolio_repo = PortfolioRepository(db)
        self.student_repo = StudentProfileRepository(db)

    async def add_item(self, data: PortfolioItemCreate, current_user: User) -> PortfolioItem:
        if current_user.role != RoleEnum.student:
            raise HTTPException(status_code=403, detail="Only students have portfolios")

        student = await self.student_repo.get_by_user_id(current_user.id)
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")

        item = PortfolioItem(
            student_id=student.id,
            title=data.title,
            description=data.description,
            project_url=data.project_url,
            image_url=data.image_url,
        )
        return await self.portfolio_repo.create(item)

    async def get_portfolio(self, user_id: int) -> Sequence[PortfolioItem]:
        student = await self.student_repo.get_by_user_id(user_id)
        if not student:
            raise HTTPException(status_code=404, detail="Student profile not found")
        return await self.portfolio_repo.get_by_student(student.id)

    async def delete_item(self, item_id: int, current_user: User):
        item = await self.portfolio_repo.get_by_id(item_id)
        if not item:
            raise HTTPException(status_code=404, detail="Portfolio item not found")

        student = await self.student_repo.get_by_user_id(current_user.id)
        if not student or item.student_id != student.id:
            raise HTTPException(status_code=403, detail="Not authorized")
        await self.portfolio_repo.delete(item)


# ── Review Service ────────────────────────────────────

class ReviewService:
    def __init__(self, db: AsyncSession):
        self.review_repo = ReviewRepository(db)
        self.notification_repo = NotificationRepository(db)

    async def create_review(self, data: ReviewCreate, current_user: User) -> Review:
        if current_user.id == data.reviewee_id:
            raise HTTPException(status_code=400, detail="Cannot review yourself")

        review = Review(
            reviewer_id=current_user.id,
            reviewee_id=data.reviewee_id,
            project_id=data.project_id,
            rating=data.rating,
            comment=data.comment,
        )
        review = await self.review_repo.create(review)

        notification = Notification(
            user_id=data.reviewee_id,
            title="New Review",
            message=f"You received a new review with rating {data.rating}/5",
        )
        await self.notification_repo.create(notification)
        return review

    async def get_reviews_for_user(self, user_id: int) -> Sequence[Review]:
        return await self.review_repo.get_for_user(user_id)

    async def get_average_rating(self, user_id: int) -> Optional[float]:
        return await self.review_repo.get_average_rating(user_id)


# ── Notification Service ─────────────────────────────

class NotificationService:
    def __init__(self, db: AsyncSession):
        self.notification_repo = NotificationRepository(db)

    async def get_notifications(self, current_user: User, unread_only: bool = False):
        return await self.notification_repo.get_for_user(current_user.id, unread_only)

    async def mark_as_read(self, notification_id: int, current_user: User):
        notifications = await self.notification_repo.get_for_user(current_user.id)
        notification = next((n for n in notifications if n.id == notification_id), None)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return await self.notification_repo.mark_as_read(notification)


# ── Admin Service ─────────────────────────────────────

class AdminService:
    def __init__(self, db: AsyncSession):
        self.user_repo = UserRepository(db)
        self.project_repo = ProjectRepository(db)
        self.app_repo = ApplicationRepository(db)

    async def update_user(self, user_id: int, data: AdminUserUpdate) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        return await self.user_repo.update(user)

    async def get_stats(self) -> StatsResponse:
        return StatsResponse(
            total_users=await self.user_repo.count(),
            total_students=await self.user_repo.count_by_role(RoleEnum.student),
            total_companies=await self.user_repo.count_by_role(RoleEnum.company),
            total_projects=await self.project_repo.count(),
            total_applications=await self.app_repo.count(),
            active_projects=await self.project_repo.count(status=ProjectStatus.open),
        )

    async def get_all_users(self, skip: int = 0, limit: int = 20) -> Sequence[User]:
        return await self.user_repo.get_all(skip, limit)
