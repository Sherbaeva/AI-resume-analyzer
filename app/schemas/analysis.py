"""Pydantic schemas for Analysis."""
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class AnalysisCreate(BaseModel):
    resume_id: int
    job_description_id: int


class AnalysisResponse(BaseModel):
    id: int
    resume_id: int
    job_description_id: int
    status: str
    score: Optional[float] = None
    matched_skills_json: Optional[str] = None
    missing_skills_json: Optional[str] = None
    explanations_json: Optional[str] = None
    error_message: Optional[str] = None
    scoring_version: str
    parser_version: str
    created_at: datetime
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AnalysisCallbackPayload(BaseModel):
    analysis_id: int
    status: str = Field(..., pattern="^(done|failed)$")
    score: Optional[float] = None
    matched_skills: Optional[List[Any]] = None
    missing_skills: Optional[List[Any]] = None
    explanations: Optional[Any] = None
    error_message: Optional[str] = None
