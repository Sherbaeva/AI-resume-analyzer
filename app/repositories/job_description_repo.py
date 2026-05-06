"""Repository for JobDescription CRUD."""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.job_description import JobDescription


class JobDescriptionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, title: str, raw_text: str) -> JobDescription:
        obj = JobDescription(title=title, raw_text=raw_text)
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def get_by_id(self, jd_id: int) -> Optional[JobDescription]:
        result = await self.db.execute(
            select(JobDescription).where(JobDescription.id == jd_id)
        )
        return result.scalar_one_or_none()

    async def list(self, skip: int = 0, limit: int = 50) -> List[JobDescription]:
        q = select(JobDescription).order_by(JobDescription.id.desc()).offset(skip).limit(limit)
        result = await self.db.execute(q)
        return list(result.scalars().all())
