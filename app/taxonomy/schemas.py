"""Pydantic schemas for skill taxonomy API."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class SkillCreate(BaseModel):
    name: str
    category: Optional[str] = None
    aliases: list[str] = []
    is_active: bool = True


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    aliases: Optional[list[str]] = None
    is_active: Optional[bool] = None


class SkillOut(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    aliases: list[str] = []
    is_active: bool
    created_by_id: Optional[int] = None
    updated_by_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
