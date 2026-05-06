"""Repository for Resume CRUD."""
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.resume import Resume


class ResumeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        filename: str,
        file_path: str,
        file_hash: str,
        file_size: int,
        content_type: str,
    ) -> Resume:
        obj = Resume(
            filename=filename,
            file_path=file_path,
            file_hash=file_hash,
            file_size=file_size,
            content_type=content_type,
        )
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def get_by_id(self, resume_id: int) -> Optional[Resume]:
        result = await self.db.execute(
            select(Resume).where(Resume.id == resume_id)
        )
        return result.scalar_one_or_none()

    async def get_by_hash(self, file_hash: str) -> Optional[Resume]:
        result = await self.db.execute(
            select(Resume).where(Resume.file_hash == file_hash)
        )
        return result.scalar_one_or_none()

    async def soft_delete(self, resume: Resume) -> Resume:
        resume.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(resume)
        return resume

    async def list(
        self,
        skip: int = 0,
        limit: int = 50,
        include_deleted: bool = False,
    ) -> List[Resume]:
        q = select(Resume)
        if not include_deleted:
            q = q.where(Resume.deleted_at.is_(None))
        q = q.order_by(Resume.id.desc()).offset(skip).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all())
