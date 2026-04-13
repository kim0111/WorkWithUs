from src.database.mongodb import get_mongodb
from src.users.models import User, RoleEnum
from src.projects.models import Project, ProjectStatus
from src.applications.models import Application


async def count_users() -> int:
    return await User.all().count()


async def count_students() -> int:
    return await User.filter(role=RoleEnum.student).count()


async def count_companies() -> int:
    return await User.filter(role=RoleEnum.company).count()


async def count_projects() -> int:
    return await Project.all().count()


async def count_applications() -> int:
    return await Application.all().count()


async def count_active_projects() -> int:
    return await Project.filter(status=ProjectStatus.open).count()


async def count_chat_messages() -> int:
    mongo = await get_mongodb()
    return await mongo.chat_messages.count_documents({})


async def count_notifications() -> int:
    mongo = await get_mongodb()
    return await mongo.notifications.count_documents({})


async def get_all_users(skip: int, limit: int) -> list[User]:
    return await User.all().offset(skip).limit(limit).prefetch_related("skills")


async def get_user_by_id(user_id: int) -> User | None:
    return await User.filter(id=user_id).prefetch_related("skills").first()


async def update_user(user: User, data: dict) -> User:
    await user.update_from_dict(data).save()
    return user
