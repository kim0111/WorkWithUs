from contextlib import asynccontextmanager

from fastapi import FastAPI
from loguru import logger
from tortoise import Tortoise

from src.config import TORTOISE_ORM
from src.logging import setup_logging

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Connecting to database...")
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()
    logger.info("Database ready")

    from src.files.storage import ensure_bucket

    try:
        await ensure_bucket()
        logger.info("MinIO bucket ready")
    except Exception as e:
        logger.warning(f"MinIO not available: {e}")

    yield
    await Tortoise.close_connections()
    logger.info("Database connections closed")


app = FastAPI(title="WorkWithUs API", version="0.1.0", lifespan=lifespan)

from src.auth.router import router as auth_router  # noqa: E402
from src.users.router import router as users_router  # noqa: E402
from src.skills.router import router as skills_router  # noqa: E402
from src.projects.router import router as projects_router  # noqa: E402
from src.files.router import router as files_router  # noqa: E402
from src.applications.router import router as applications_router  # noqa: E402
from src.comments.router import router as comments_router  # noqa: E402

app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(skills_router, prefix="/api/v1/skills", tags=["skills"])
app.include_router(projects_router, prefix="/api/v1/projects", tags=["projects"])
app.include_router(files_router, prefix="/api/v1/projects/{project_id}/files", tags=["files"])
app.include_router(applications_router, prefix="/api/v1", tags=["applications"])
app.include_router(comments_router, prefix="/api/v1/applications/{application_id}/comments", tags=["comments"])
