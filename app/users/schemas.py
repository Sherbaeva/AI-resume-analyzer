"""Pydantic schemas for users API."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "hr"


class UserUpdate(BaseModel):
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None


class PermissionOut(BaseModel):
    id: int
    code: str
    description: str

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    permissions: list[str] = []

    model_config = {"from_attributes": True}


class PermissionsSetRequest(BaseModel):
    permission_codes: list[str]
