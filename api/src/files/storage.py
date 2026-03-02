import asyncio
from datetime import timedelta
from io import BytesIO

from minio import Minio

from src.config import settings

_client: Minio | None = None


def get_minio_client() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
    return _client


async def ensure_bucket() -> None:
    client = get_minio_client()
    exists = await asyncio.to_thread(client.bucket_exists, settings.MINIO_BUCKET)
    if not exists:
        await asyncio.to_thread(client.make_bucket, settings.MINIO_BUCKET)


async def upload_file(storage_key: str, data: bytes, content_type: str) -> None:
    client = get_minio_client()
    await asyncio.to_thread(
        client.put_object,
        settings.MINIO_BUCKET,
        storage_key,
        BytesIO(data),
        len(data),
        content_type=content_type,
    )


async def get_presigned_url(storage_key: str, expires: timedelta = timedelta(hours=1)) -> str:
    client = get_minio_client()
    return await asyncio.to_thread(
        client.presigned_get_object,
        settings.MINIO_BUCKET,
        storage_key,
        expires=expires,
    )


async def delete_file(storage_key: str) -> None:
    client = get_minio_client()
    await asyncio.to_thread(
        client.remove_object,
        settings.MINIO_BUCKET,
        storage_key,
    )
