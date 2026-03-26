import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.database.postgres import init_postgres
from src.database.mongodb import init_mongodb, close_mongodb
from src.core.redis import close_redis
from src.core.minio_client import init_minio

from src.auth.router import router as auth_router
from src.users.router import router as users_router
from src.skills.router import router as skills_router
from src.projects.router import router as projects_router
from src.applications.router import router as applications_router
from src.files.router import router as files_router
from src.chat.router import router as chat_router
from src.notifications.router import router as notifications_router
from src.reviews.router import router as reviews_router
from src.portfolio.router import router as portfolio_router
from src.admin.router import router as admin_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    await init_postgres()
    logger.info("PostgreSQL initialized")
    await init_mongodb()
    logger.info("MongoDB initialized")
    try:
        init_minio()
        logger.info("MinIO initialized")
    except Exception as e:
        logger.warning(f"MinIO init warning: {e}")
    yield
    await close_mongodb()
    await close_redis()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Web platform for student-company-committee interaction. "
                "Features: projects, applications, chat, file uploads, reviews, notifications.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all routers
for r in [auth_router, users_router, skills_router, projects_router, applications_router,
          files_router, chat_router, notifications_router, reviews_router, portfolio_router, admin_router]:
    app.include_router(r, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    return {"message": settings.PROJECT_NAME, "version": settings.VERSION, "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok", "services": {
        "postgres": "connected",
        "mongodb": "connected",
        "redis": "connected",
        "minio": "connected",
    }}
