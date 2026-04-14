from tortoise import Tortoise
from src.core.config import settings


TORTOISE_ORM = {
    "connections": {"default": settings.DATABASE_URL},
    "apps": {
        "models": {
            "models": [
                "src.users.models",
                "src.skills.models",
                "src.projects.models",
                "src.applications.models",
                "src.reviews.models",
                "src.portfolio.models",
                "src.teams.models",
                "src.tasks.models",
                "aerich.models",
            ],
            "default_connection": "default",
        }
    },
}


async def init_postgres():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def close_postgres():
    await Tortoise.close_connections()
