import io
import uuid
from typing import Optional
from minio import Minio
from minio.error import S3Error
from src.core.config import settings

_client: Optional[Minio] = None

BUCKETS = [
    settings.MINIO_BUCKET_AVATARS,
    settings.MINIO_BUCKET_PROJECTS,
    settings.MINIO_BUCKET_SUBMISSIONS,
    settings.MINIO_BUCKET_RESUMES,
]


def get_minio() -> Minio:
    global _client
    if _client is None:
        _client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE,
        )
    return _client


def init_minio():
    """Create buckets if they don't exist."""
    client = get_minio()
    for bucket in BUCKETS:
        try:
            if not client.bucket_exists(bucket):
                client.make_bucket(bucket)
        except S3Error as e:
            print(f"MinIO bucket init error ({bucket}): {e}")


def upload_file(
    bucket: str,
    file_data: bytes,
    original_filename: str,
    content_type: str = "application/octet-stream",
) -> str:
    """Upload file, return unique object name."""
    client = get_minio()
    ext = original_filename.rsplit(".", 1)[-1] if "." in original_filename else ""
    object_name = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex

    client.put_object(
        bucket,
        object_name,
        io.BytesIO(file_data),
        length=len(file_data),
        content_type=content_type,
    )
    return object_name


def get_file_url(bucket: str, object_name: str, expires_hours: int = 1) -> str:
    """Get presigned URL for file download."""
    from datetime import timedelta
    client = get_minio()
    return client.presigned_get_object(bucket, object_name, expires=timedelta(hours=expires_hours))


def delete_file(bucket: str, object_name: str):
    """Delete file from bucket."""
    client = get_minio()
    try:
        client.remove_object(bucket, object_name)
    except S3Error:
        pass


def download_file(bucket: str, object_name: str) -> bytes:
    """Download file as bytes."""
    client = get_minio()
    response = client.get_object(bucket, object_name)
    data = response.read()
    response.close()
    response.release_conn()
    return data
