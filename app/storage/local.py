"""Local filesystem implementation of StorageService."""
import hashlib
import os
from pathlib import Path

from app.storage.base import StorageFile, StorageService
from app.core.config import get_settings


class LocalStorageService(StorageService):
    def __init__(self, storage_dir: str | None = None):
        settings = get_settings()
        self._base = Path(storage_dir or settings.STORAGE_DIR) / "resumes"
        self._base.mkdir(parents=True, exist_ok=True)

    def _hash(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _resolve(self, path: str) -> Path:
        return self._base.parent / path

    def save(self, file_bytes: bytes, filename: str) -> StorageFile:
        sha = self._hash(file_bytes)
        ext = Path(filename).suffix.lstrip(".")
        relative = f"resumes/{sha}.{ext}"
        abs_path = self._base.parent / relative

        if not abs_path.exists():
            abs_path.write_bytes(file_bytes)

        return StorageFile(
            path=relative,
            filename=filename,
            size=len(file_bytes),
            hash=sha,
        )

    def get(self, path: str) -> bytes:
        abs_path = self._resolve(path)
        if not abs_path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        return abs_path.read_bytes()

    def delete(self, path: str) -> None:
        abs_path = self._resolve(path)
        if abs_path.exists():
            abs_path.unlink()

    def exists(self, path: str) -> bool:
        return self._resolve(path).exists()
