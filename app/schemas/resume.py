"""Pydantic schemas for Resume."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ResumeResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    file_hash: str
    file_size: int
    content_type: str
    uploaded_at: datetime
    deleted_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
