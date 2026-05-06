"""Pydantic schemas for auth endpoints."""
from pydantic import BaseModel, EmailStr


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class OtpVerifyRequest(BaseModel):
    email: EmailStr
    code: str


class OtpSentResponse(BaseModel):
    status: str = "otp_sent"
    message: str = "A verification code has been sent to your email address."


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserMeResponse(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool
    permissions: list[str]

    model_config = {"from_attributes": True}
