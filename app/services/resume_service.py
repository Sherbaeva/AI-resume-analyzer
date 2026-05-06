"""Resume service: upload, deduplication, deletion."""
from typing import Optional
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.resume import Resume
from app.repositories.resume_repo import ResumeRepository
from app.repositories.audit_log_repo import AuditLogRepository
from app.storage.factory import get_storage

ALLOWED_CONTENT_TYPES = {
    "application/pdf": "pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "docx",
    "text/plain": "txt",
}

settings = get_settings()


class ResumeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.resume_repo = ResumeRepository(db)
        self.audit_repo = AuditLogRepository(db)
        self.storage = get_storage()   # ← auto-selects S3 or local based on env

    async def upload(self, file: UploadFile) -> Resume:
        # Validate content type
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file type: {file.content_type}. Allowed: pdf, docx, txt",
            )

        file_bytes = await file.read()

        # Validate size
        if len(file_bytes) > settings.max_upload_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File exceeds maximum size of {settings.MAX_UPLOAD_MB}MB",
            )

        # Store file (handles dedup by hash internally)
        stored = self.storage.save(file_bytes, file.filename or "upload")

        # Deduplication: if hash already in DB, return existing resume
        existing = await self.resume_repo.get_by_hash(stored.hash)
        if existing and existing.deleted_at is None:
            return existing

        resume = await self.resume_repo.create(
            filename=stored.filename,
            file_path=stored.path,
            file_hash=stored.hash,
            file_size=stored.size,
            content_type=file.content_type,
        )
        await self.audit_repo.log("upload", "resume", resume.id)
        return resume

    async def get(self, resume_id: int) -> Resume:
        resume = await self.resume_repo.get_by_id(resume_id)
        if not resume or resume.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
        return resume

    async def delete(self, resume_id: int) -> Resume:
        resume = await self.resume_repo.get_by_id(resume_id)
        if not resume or resume.deleted_at is not None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resume not found")
        resume = await self.resume_repo.soft_delete(resume)
        await self.audit_repo.log("soft_delete", "resume", resume.id)
        return resume

    def extract_text(self, resume: Resume) -> str:
        """Read file bytes from storage and parse to text."""
        file_bytes = self.storage.get(resume.file_path)
        ext = resume.file_path.rsplit(".", 1)[-1].lower()
        if ext == "pdf":
            from app.parsers.pdf_parser import extract_text
        elif ext == "docx":
            from app.parsers.docx_parser import extract_text
        else:
            from app.parsers.txt_parser import extract_text
        return extract_text(file_bytes)
