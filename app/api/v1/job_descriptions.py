"""Job Descriptions API router."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.auth.dependencies import require_permission
from app.repositories.job_description_repo import JobDescriptionRepository
from app.schemas.job_description import JobDescriptionCreate, JobDescriptionResponse

router = APIRouter(prefix="/job-descriptions", tags=["Job Descriptions"])


@router.post(
    "", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[require_permission("jd.write")],
)
async def create_job_description(
    payload: JobDescriptionCreate,
    db: AsyncSession = Depends(get_session),
):
    repo = JobDescriptionRepository(db)
    jd = await repo.create(title=payload.title, raw_text=payload.raw_text)
    return jd


@router.get(
    "", response_model=List[JobDescriptionResponse],
    dependencies=[require_permission("jd.read")],
)
async def list_job_descriptions(
    db: AsyncSession = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """List all job descriptions, newest first."""
    repo = JobDescriptionRepository(db)
    return await repo.list(skip=skip, limit=limit)


@router.get(
    "/{jd_id}", response_model=JobDescriptionResponse,
    dependencies=[require_permission("jd.read")],
)
async def get_job_description(jd_id: int, db: AsyncSession = Depends(get_session)):
    repo = JobDescriptionRepository(db)
    jd = await repo.get_by_id(jd_id)
    if not jd:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job description not found")
    return jd
