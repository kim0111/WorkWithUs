from src.users.models import User, CompanyProfile, StudentProfile, RoleEnum
from tortoise.transactions import in_transaction
from src.core.security import hash_password
from src.core.config import settings


async def get_user_by_email(email: str) -> User | None:
    return await User.filter(email=email).first()


async def get_user_by_username(username: str) -> User | None:
    return await User.filter(username=username).first()


async def get_user_by_id(user_id: int) -> User | None:
    return await User.filter(id=user_id).prefetch_related("skills").first()


async def email_exists(email: str) -> bool:
    return await User.filter(email=email).exists()


async def username_exists(username: str) -> bool:
    return await User.filter(username=username).exists()


async def create_user(email: str, username: str, password: str,
                      full_name: str | None, role: RoleEnum) -> User:
    async with in_transaction():
        user = await User.create(
            email=email, username=username,
            hashed_password=hash_password(password),
            full_name=full_name, role=role,
            is_active=not settings.EMAIL_VERIFICATION_REQUIRED,
        )
        if role == RoleEnum.company:
            await CompanyProfile.create(user=user, company_name=username)
        elif role == RoleEnum.student:
            await StudentProfile.create(user=user)

    await user.fetch_related("skills")
    return user


async def activate_user(user: User) -> User:
    user.is_active = True
    await user.save()
    return user
