"""Auth endpoints: login (sends OTP), verify-otp (returns JWT), me, logout."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import CurrentUser
from app.auth.jwt import create_access_token
from app.auth.otp import delete_otp, generate_otp, save_otp, verify_otp
from app.auth.password import verify_password
from app.auth.schemas import (
    LoginRequest,
    OtpSentResponse,
    OtpVerifyRequest,
    TokenResponse,
    UserMeResponse,
)
from app.audit.service import write_audit
from app.core.config import get_settings
from app.core.database import get_db
from app.rbac.service import get_effective_permissions
from app.repositories.user_repo import UserRepository
from app.services.email_service import send_otp_email

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()


@router.post("/login", response_model=OtpSentResponse)
async def login(
    body: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 1 of 2FA: validate credentials, send OTP to email.
    On success returns {"status": "otp_sent"} — does NOT return a JWT yet.
    """
    import structlog
    log = structlog.get_logger()
    log.info("auth.login.step1", email=body.email)
    
    repo = UserRepository(db)
    user = await repo.get_by_email(body.email)

    if not user or not verify_password(body.password, user.password_hash):
        await write_audit(
            db, action="auth.login.failed", entity_type="user",
            meta={"email": body.email},
            ip=request.client.host if request.client else None,
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account is deactivated",
        )

    # Generate and store OTP
    otp_code = generate_otp()
    await save_otp(body.email, otp_code)

    # Send OTP email (raises exception if SMTP fails)
    try:
        await send_otp_email(body.email, otp_code)
    except Exception as exc:
        log.error("auth.login.email_failed", email=body.email, error=str(exc))
        await delete_otp(body.email)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Failed to send verification email. Please try again.",
        ) from exc

    await write_audit(
        db, action="auth.otp.sent", entity_type="user", entity_id=user.id,
        actor_user_id=user.id,
        ip=request.client.host if request.client else None,
    )
    await db.commit()

    return OtpSentResponse()


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp_endpoint(
    body: OtpVerifyRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Step 2 of 2FA: verify the OTP code and return JWT access token.
    """
    repo = UserRepository(db)
    user = await repo.get_by_email(body.email)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid request",
        )

    is_valid = await verify_otp(body.email, body.code)
    if not is_valid:
        await write_audit(
            db, action="auth.otp.failed", entity_type="user", entity_id=user.id,
            actor_user_id=user.id,
            meta={"reason": "invalid or expired code"},
            ip=request.client.host if request.client else None,
        )
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification code",
        )

    # Update last_login_at
    await repo.update(user, last_login_at=datetime.now(timezone.utc))

    token = create_access_token({"sub": str(user.id)})
    expires_in = settings.JWT_EXPIRES_MIN * 60

    await write_audit(
        db, action="auth.login.success", entity_type="user", entity_id=user.id,
        actor_user_id=user.id,
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    await db.commit()

    return TokenResponse(access_token=token, expires_in=expires_in)


@router.get("/me", response_model=UserMeResponse)
async def me(current_user: CurrentUser):
    return UserMeResponse(
        id=current_user.id,
        email=current_user.email,
        role=current_user.role.value,
        is_active=current_user.is_active,
        permissions=sorted(get_effective_permissions(current_user)),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(current_user: CurrentUser):
    """Stateless logout — client should discard the token."""
    return None
