"""Analyses API router."""
from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.auth.dependencies import require_permission
from app.schemas.analysis import AnalysisCreate, AnalysisResponse
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="", tags=["Analyses"])


@router.post(
    "/analyses", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[require_permission("analysis.write")],
)
async def create_analysis(
    payload: AnalysisCreate,
    db: AsyncSession = Depends(get_session),
):
    """Create (or return idempotent) analysis for (resume_id, job_description_id)."""
    service = AnalysisService(db)
    return await service.create_analysis(payload.resume_id, payload.job_description_id)


@router.get(
    "/analyses/{analysis_id}", response_model=AnalysisResponse,
    dependencies=[require_permission("results.read")],
)
async def get_analysis(analysis_id: int, db: AsyncSession = Depends(get_session)):
    service = AnalysisService(db)
    return await service.get_analysis(analysis_id)


@router.get(
    "/results", response_model=List[AnalysisResponse],
    dependencies=[require_permission("results.read")],
)
async def get_results(
    job_description_id: int = Query(..., description="Filter results by job description"),
    db: AsyncSession = Depends(get_session),
):
    service = AnalysisService(db)
    return await service.list_results(job_description_id)
