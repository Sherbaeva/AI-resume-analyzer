"""Analysis orchestration service."""
import json
import structlog
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis import Analysis
from app.repositories.analysis_repo import AnalysisRepository
from app.repositories.job_description_repo import JobDescriptionRepository
from app.schemas.analysis import AnalysisCallbackPayload
from app.services.resume_service import ResumeService
from app.services.n8n_service import N8nService

logger = structlog.get_logger()


class AnalysisService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.analysis_repo = AnalysisRepository(db)
        self.jd_repo = JobDescriptionRepository(db)
        self.resume_service = ResumeService(db)
        self.n8n = N8nService()

    async def create_analysis(self, resume_id: int, job_description_id: int) -> Analysis:
        # Validate resume exists
        resume = await self.resume_service.get(resume_id)

        # Validate job description exists
        jd = await self.jd_repo.get_by_id(job_description_id)
        if not jd:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found"
            )

        # Idempotency check
        existing = await self.analysis_repo.get_existing(resume_id, job_description_id)
        if existing:
            logger.info(
                "Returning existing analysis (idempotency)",
                analysis_id=existing.id,
                status=existing.status,
            )
            return existing

        # Create analysis record
        analysis = await self.analysis_repo.create(resume_id, job_description_id)
        logger.info("Created analysis", analysis_id=analysis.id)

        # Extract texts
        resume_text = self.resume_service.extract_text(resume)
        job_text = jd.raw_text

        # Mark as processing
        analysis = await self.analysis_repo.update_status(analysis, "processing")

        # Call n8n (fire and forget; failures handled in callback)
        try:
            await self.n8n.trigger_analysis(analysis.id, resume_text, job_text)
        except Exception as exc:
            logger.error("Failed to call n8n webhook", analysis_id=analysis.id, error=str(exc))
            analysis = await self.analysis_repo.update_status(
                analysis, "failed", error_message=f"n8n unreachable: {exc}"
            )

        return analysis

    async def handle_callback(self, payload: AnalysisCallbackPayload) -> Analysis:
        analysis = await self.analysis_repo.get_by_id(payload.analysis_id)
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis {payload.analysis_id} not found",
            )

        matched_json = json.dumps(payload.matched_skills) if payload.matched_skills is not None else None
        missing_json = json.dumps(payload.missing_skills) if payload.missing_skills is not None else None
        explanations_json = json.dumps(payload.explanations) if payload.explanations is not None else None

        analysis = await self.analysis_repo.update_status(
            analysis,
            status=payload.status,
            score=payload.score,
            matched_skills_json=matched_json,
            missing_skills_json=missing_json,
            explanations_json=explanations_json,
            error_message=payload.error_message,
        )
        logger.info("Analysis callback processed", analysis_id=analysis.id, status=analysis.status)
        return analysis

    async def get_analysis(self, analysis_id: int) -> Analysis:
        analysis = await self.analysis_repo.get_by_id(analysis_id)
        if not analysis:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Analysis not found")
        return analysis

    async def list_results(self, job_description_id: int) -> list[Analysis]:
        return await self.analysis_repo.list_by_job_description(job_description_id)
