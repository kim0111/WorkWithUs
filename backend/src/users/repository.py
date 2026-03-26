from typing import Optional, Sequence
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.users.models import User, CompanyProfile, StudentProfile, RoleEnum, user_skills


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
        result = await self.db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()

    async def count(self) -> int:
        result = await self.db.execute(select(func.count(User.id)))
        return result.scalar()

    async def count_by_role(self, role: RoleEnum) -> int:
        result = await self.db.execute(select(func.count(User.id)).where(User.role == role))
        return result.scalar()

    async def add_skill(self, user_id: int, skill_id: int):
        await self.db.execute(user_skills.insert().values(user_id=user_id, skill_id=skill_id))

    async def remove_skill(self, user_id: int, skill_id: int):
        await self.db.execute(
            delete(user_skills).where(user_skills.c.user_id == user_id, user_skills.c.skill_id == skill_id)
        )


class CompanyProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: int) -> Optional[CompanyProfile]:
        result = await self.db.execute(select(CompanyProfile).where(CompanyProfile.user_id == user_id))
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


class StudentProfileRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_user_id(self, user_id: int) -> Optional[StudentProfile]:
        result = await self.db.execute(select(StudentProfile).where(StudentProfile.user_id == user_id))
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
