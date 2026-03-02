from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgres://postgres:postgres@localhost:5432/platform_db"
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 600
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "workwithus"
    MINIO_USE_SSL: bool = False
    MAX_FILE_SIZE_MB: int = 50

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()

TORTOISE_ORM = {
    "connections": {"default": settings.DATABASE_URL},
    "apps": {
        "models": {
            "models": [
                "src.users.models",
                "src.skills.models",
                "src.projects.models",
                "src.files.models",
                "src.applications.models",
                "src.comments.models",
                "aerich.models",
            ],
            "default_connection": "default",
        },
    },
}
