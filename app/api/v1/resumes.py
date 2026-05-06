"""Resumes API router."""
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.auth.dependencies import require_permission
from app.repositories.resume_repo import ResumeRepository
from app.schemas.resume import ResumeResponse
from app.services.resume_service import ResumeService

router = APIRouter(prefix="/resumes", tags=["Resumes"])


@router.post(
    "", response_model=ResumeResponse, status_code=status.HTTP_201_CREATED,
    dependencies=[require_permission("resumes.write")],
)
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_session),
):
    """Upload a resume file (PDF, DOCX, TXT). Deduplicates by sha256 hash."""
    service = ResumeService(db)
    resume = await service.upload(file)
    return resume


@router.get(
    "", response_model=List[ResumeResponse],
    dependencies=[require_permission("resumes.read")],
)
async def list_resumes(
    db: AsyncSession = Depends(get_session),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
):
    """List all non-deleted resumes, newest first."""
    repo = ResumeRepository(db)
    return await repo.list(skip=skip, limit=limit)


@router.get(
    "/{resume_id}", response_model=ResumeResponse,
    dependencies=[require_permission("resumes.read")],
)
async def get_resume(resume_id: int, db: AsyncSession = Depends(get_session)):
    service = ResumeService(db)
    return await service.get(resume_id)


@router.delete(
    "/{resume_id}", response_model=ResumeResponse,
    dependencies=[require_permission("resumes.delete")],
)
async def delete_resume(resume_id: int, db: AsyncSession = Depends(get_session)):
    """Soft-delete a resume (sets deleted_at). Writes audit log entry."""
    service = ResumeService(db)
    return await service.delete(resume_id)
