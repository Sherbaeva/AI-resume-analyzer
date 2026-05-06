"""S3-compatible storage implementation.

Works with:
- AWS S3
- Cloudflare R2 (recommended — 10GB free, no egress fees)
- MinIO (self-hosted, free)
- Backblaze B2

Configuration via environment variables:
  S3_BUCKET_NAME      = your-bucket-name
  S3_ACCESS_KEY       = your-access-key
  S3_SECRET_KEY       = your-secret-key
  S3_ENDPOINT_URL     = https://...r2.cloudflarestorage.com  (leave empty for AWS)
  S3_REGION           = auto  (or us-east-1 etc.)
  S3_PUBLIC_URL       = https://files.yourdomain.com  (optional CDN/public URL prefix)
"""
import hashlib
import io
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

from app.storage.base import StorageFile, StorageService


class S3StorageService(StorageService):
    """S3-compatible storage backend."""

    def __init__(
        self,
        bucket_name: str,
        access_key: str,
        secret_key: str,
        endpoint_url: str | None = None,  # None = AWS, set for R2/MinIO/B2
        region: str = "auto",
        public_url: str | None = None,    # Optional CDN prefix for public file URLs
    ):
        self._bucket = bucket_name
        self._public_url = public_url.rstrip("/") if public_url else None

        self._client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            endpoint_url=endpoint_url,
            region_name=region,
        )
        self._ensure_bucket()

    # ─── Internal ─────────────────────────────────────────────

    def _ensure_bucket(self) -> None:
        """Create bucket if it doesn't exist."""
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError as e:
            if e.response["Error"]["Code"] in ("404", "NoSuchBucket"):
                self._client.create_bucket(Bucket=self._bucket)

    @staticmethod
    def _hash(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _key(self, path: str) -> str:
        """Convert relative path to S3 key (strip leading slash)."""
        return path.lstrip("/")

    # ─── StorageService interface ──────────────────────────────

    def save(self, file_bytes: bytes, filename: str) -> StorageFile:
        sha = self._hash(file_bytes)
        ext = Path(filename).suffix.lstrip(".")
        relative = f"resumes/{sha}.{ext}"
        key = self._key(relative)

        # Deduplicate: skip upload if object already exists
        if not self.exists(relative):
            self._client.upload_fileobj(
                io.BytesIO(file_bytes),
                self._bucket,
                key,
                ExtraArgs={"ContentType": self._content_type(ext)},
            )

        return StorageFile(
            path=relative,
            filename=filename,
            size=len(file_bytes),
            hash=sha,
        )

    def get(self, path: str) -> bytes:
        key = self._key(path)
        try:
            response = self._client.get_object(Bucket=self._bucket, Key=key)
            return response["Body"].read()
        except ClientError as e:
            if e.response["Error"]["Code"] == "NoSuchKey":
                raise FileNotFoundError(f"S3 object not found: {key}")
            raise

    def delete(self, path: str) -> None:
        key = self._key(path)
        try:
            self._client.delete_object(Bucket=self._bucket, Key=key)
        except ClientError:
            pass  # Best-effort delete

    def exists(self, path: str) -> bool:
        key = self._key(path)
        try:
            self._client.head_object(Bucket=self._bucket, Key=key)
            return True
        except ClientError:
            return False

    def public_url(self, path: str) -> str | None:
        """Return CDN/public URL if configured, else None."""
        if not self._public_url:
            return None
        return f"{self._public_url}/{self._key(path)}"

    # ─── Helpers ──────────────────────────────────────────────

    @staticmethod
    def _content_type(ext: str) -> str:
        return {
            "pdf": "application/pdf",
            "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "txt": "text/plain",
        }.get(ext.lower(), "application/octet-stream")
