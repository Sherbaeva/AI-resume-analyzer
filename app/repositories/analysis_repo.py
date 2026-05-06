"""Repository for Analysis CRUD."""
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.analysis import Analysis


class AnalysisRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, resume_id: int, job_description_id: int) -> Analysis:
        obj = Analysis(
            resume_id=resume_id,
            job_description_id=job_description_id,
            status="queued",
        )
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def get_by_id(self, analysis_id: int) -> Optional[Analysis]:
        result = await self.db.execute(
            select(Analysis).where(Analysis.id == analysis_id)
        )
        return result.scalar_one_or_none()

    async def get_existing(self, resume_id: int, job_description_id: int) -> Optional[Analysis]:
        """Idempotency check — return active analysis if one exists."""
        result = await self.db.execute(
            select(Analysis).where(
                Analysis.resume_id == resume_id,
                Analysis.job_description_id == job_description_id,
                Analysis.status.in_(["queued", "processing", "done"]),
            )
        )
        return result.scalar_one_or_none()

    async def list_by_job_description(self, job_description_id: int) -> List[Analysis]:
        result = await self.db.execute(
            select(Analysis).where(Analysis.job_description_id == job_description_id)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        analysis: Analysis,
        status: str,
        score: Optional[float] = None,
        matched_skills_json: Optional[str] = None,
        missing_skills_json: Optional[str] = None,
        explanations_json: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Analysis:
        analysis.status = status
        now = datetime.now(timezone.utc)

        if status == "processing":
            analysis.started_at = now
        elif status in ("done", "failed"):
            analysis.finished_at = now
            if score is not None:
                analysis.score = score
            if matched_skills_json is not None:
                analysis.matched_skills_json = matched_skills_json
            if missing_skills_json is not None:
                analysis.missing_skills_json = missing_skills_json
            if explanations_json is not None:
                analysis.explanations_json = explanations_json
            if error_message is not None:
                analysis.error_message = error_message

        await self.db.flush()
        await self.db.refresh(analysis)
        return analysis
