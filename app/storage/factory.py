"""Storage backend factory.

Selects S3StorageService or LocalStorageService based on environment:
  - If S3_BUCKET_NAME is set → use S3 (MinIO / AWS / R2 / B2)
  - Otherwise              → use local filesystem
"""
from app.core.config import get_settings
from app.storage.base import StorageService


def get_storage() -> StorageService:
    settings = get_settings()

    if settings.S3_BUCKET_NAME:
        from app.storage.s3 import S3StorageService
        return S3StorageService(
            bucket_name=settings.S3_BUCKET_NAME,
            access_key=settings.S3_ACCESS_KEY,
            secret_key=settings.S3_SECRET_KEY,
            endpoint_url=settings.S3_ENDPOINT_URL or None,
            region=settings.S3_REGION,
            public_url=settings.S3_PUBLIC_URL or None,
        )

    from app.storage.local import LocalStorageService
    return LocalStorageService()
