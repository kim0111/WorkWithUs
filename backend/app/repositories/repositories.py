from typing import Optional, Sequence
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.models import (
    User, Skill, Project, Application, PortfolioItem,
    Review, Notification, CompanyProfile, StudentProfile,
    RoleEnum, ProjectStatus, ApplicationStatus, user_skills, project_skills
)


# ── User Repository ──────────────────────────────────

class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(
            select(User).options(selectinload(User.skills)).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user: User) -> User:
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_all(self, skip: int = 0, limit: int = 20) -> Sequence[User]:
        result = await self.db.execute(
            select(User).offset(skip).limit(limit)
        )
        return result.scalars().all()

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(User.id)))
        return result.scalar()

    async def count_by_role(self, role: RoleEnum) -> int:
        result = await self.db.execute(
            select(func.count(User.id)).where(User.role == role)
        )
        return result.scalar()

    async def add_skill(self, user_id: int, skill_id: int):
        await self.db.execute(
            user_skills.insert().values(user_id=user_id, skill_id=skill_id)
        )

    async def remove_skill(self, user_id: int, skill_id: int):
        await self.db.execute(
            delete(user_skills).where(
                user_skills.c.user_id == user_id,
                user_skills.c.skill_id == skill_id
            )
        )


# ── Skill Repository ─────────────────────────────────

class SkillRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, skill_id: int) -> Optional[Skill]:
        result = await self.db.execute(select(Skill).where(Skill.id == skill_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Skill]:
        result = await self.db.execute(select(Skill).where(Skill.name == name))
        return result.scalar_one_or_none()

    async def get_all(self) -> Sequence[Skill]:
        result = await self.db.execute(select(Skill).order_by(Skill.name))
        return result.scalars().all()

    async def create(self, skill: Skill) -> Skill:
        self.db.add(skill)
        await self.db.flush()
        await self.db.refresh(skill)
        return skill

    async def get_by_ids(self, ids: list[int]) -> Sequence[Skill]:
        result = await self.db.execute(select(Skill).where(Skill.id.in_(ids)))
        return result.scalars().all()


# ── Company Profile Repository ────────────────────────

class CompanyProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: int) -> Optional[CompanyProfile]:
        result = await self.db.execute(
            select(CompanyProfile).where(CompanyProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, profile: CompanyProfile) -> CompanyProfile:
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def update(self, profile: CompanyProfile) -> CompanyProfile:
        await self.db.flush()
        await self.db.refresh(profile)
        return profile


# ── Student Profile Repository ────────────────────────

class StudentProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: int) -> Optional[StudentProfile]:
        result = await self.db.execute(
            select(StudentProfile).where(StudentProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, profile: StudentProfile) -> StudentProfile:
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def update(self, profile: StudentProfile) -> StudentProfile:
        await self.db.flush()
        await self.db.refresh(profile)
        return profile


# ── Project Repository ────────────────────────────────

class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, project_id: int) -> Optional[Project]:
        result = await self.db.execute(
            select(Project)
            .options(selectinload(Project.required_skills), selectinload(Project.applications))
            .where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 20,
        status: Optional[ProjectStatus] = None,
        owner_id: Optional[int] = None,
        is_student_project: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> Sequence[Project]:
        query = select(Project).options(selectinload(Project.required_skills))

        if status:
            query = query.where(Project.status == status)
        if owner_id:
            query = query.where(Project.owner_id == owner_id)
        if is_student_project is not None:
            query = query.where(Project.is_student_project == is_student_project)
        if search:
            query = query.where(Project.title.ilike(f"%{search}%"))

        query = query.order_by(Project.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def count(
        self,
        status: Optional[ProjectStatus] = None,
        owner_id: Optional[int] = None,
        is_student_project: Optional[bool] = None,
        search: Optional[str] = None,
    ) -> int:
        query = select(func.count(Project.id))
        if status:
            query = query.where(Project.status == status)
        if owner_id:
            query = query.where(Project.owner_id == owner_id)
        if is_student_project is not None:
            query = query.where(Project.is_student_project == is_student_project)
        if search:
            query = query.where(Project.title.ilike(f"%{search}%"))
        result = await self.db.execute(query)
        return result.scalar()

    async def create(self, project: Project) -> Project:
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def update(self, project: Project) -> Project:
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def delete(self, project: Project):
        await self.db.delete(project)

    async def add_skill(self, project_id: int, skill_id: int):
        await self.db.execute(
            project_skills.insert().values(project_id=project_id, skill_id=skill_id)
        )


# ── Application Repository ───────────────────────────

class ApplicationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, app_id: int) -> Optional[Application]:
        result = await self.db.execute(
            select(Application).where(Application.id == app_id)
        )
        return result.scalar_one_or_none()

    async def get_by_project_and_applicant(
        self, project_id: int, applicant_id: int
    ) -> Optional[Application]:
        result = await self.db.execute(
            select(Application).where(
                Application.project_id == project_id,
                Application.applicant_id == applicant_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_by_project(self, project_id: int) -> Sequence[Application]:
        result = await self.db.execute(
            select(Application).where(Application.project_id == project_id)
        )
        return result.scalars().all()

    async def get_by_applicant(self, applicant_id: int) -> Sequence[Application]:
        result = await self.db.execute(
            select(Application).where(Application.applicant_id == applicant_id)
        )
        return result.scalars().all()

    async def create(self, application: Application) -> Application:
        self.db.add(application)
        await self.db.flush()
        await self.db.refresh(application)
        return application

    async def update(self, application: Application) -> Application:
        await self.db.flush()
        await self.db.refresh(application)
        return application

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(Application.id)))
        return result.scalar()


# ── Portfolio Repository ──────────────────────────────

class PortfolioRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_student(self, student_id: int) -> Sequence[PortfolioItem]:
        result = await self.db.execute(
            select(PortfolioItem).where(PortfolioItem.student_id == student_id)
        )
        return result.scalars().all()

    async def get_by_id(self, item_id: int) -> Optional[PortfolioItem]:
        result = await self.db.execute(
            select(PortfolioItem).where(PortfolioItem.id == item_id)
        )
        return result.scalar_one_or_none()

    async def create(self, item: PortfolioItem) -> PortfolioItem:
        self.db.add(item)
        await self.db.flush()
        await self.db.refresh(item)
        return item

    async def delete(self, item: PortfolioItem):
        await self.db.delete(item)


# ── Review Repository ────────────────────────────────

class ReviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_for_user(self, user_id: int) -> Sequence[Review]:
        result = await self.db.execute(
            select(Review).where(Review.reviewee_id == user_id)
        )
        return result.scalars().all()

    async def create(self, review: Review) -> Review:
        self.db.add(review)
        await self.db.flush()
        await self.db.refresh(review)
        return review

    async def get_average_rating(self, user_id: int) -> Optional[float]:
        result = await self.db.execute(
            select(func.avg(Review.rating)).where(Review.reviewee_id == user_id)
        )
        return result.scalar()


# ── Notification Repository ──────────────────────────

class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_for_user(self, user_id: int, unread_only: bool = False) -> Sequence[Notification]:
        query = select(Notification).where(Notification.user_id == user_id)
        if unread_only:
            query = query.where(Notification.is_read == False)
        query = query.order_by(Notification.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, notification: Notification) -> Notification:
        self.db.add(notification)
        await self.db.flush()
        await self.db.refresh(notification)
        return notification

    async def mark_as_read(self, notification: Notification) -> Notification:
        notification.is_read = True
        await self.db.flush()
        return notification
