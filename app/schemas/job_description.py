"""Pydantic schemas for JobDescription."""
from datetime import datetime
from pydantic import BaseModel, Field


class JobDescriptionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=512)
    raw_text: str = Field(..., min_length=1)


class JobDescriptionResponse(BaseModel):
    id: int
    title: str
    raw_text: str
    created_at: datetime

    model_config = {"from_attributes": True}
