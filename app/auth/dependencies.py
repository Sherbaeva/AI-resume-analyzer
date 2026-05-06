"""FastAPI dependencies for authentication and authorization."""
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt import decode_token
from app.core.database import get_db
from app.models.user import User
from app.rbac.service import get_effective_permissions, has_permission
from app.repositories.user_repo import UserRepository

_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    db: AsyncSession = Depends(get_db),
) -> User:
    """Validate Bearer token and return the active User. Raises 401 on any failure."""
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if not credentials:
        raise exc
    try:
        payload = decode_token(credentials.credentials)
        user_id: int | None = payload.get("sub")
        if user_id is None:
            raise exc
    except JWTError:
        raise exc

    user = await UserRepository(db).get_by_id(int(user_id))
    if not user or not user.is_active:
        raise exc
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_role(*roles: str):
    """Dependency factory: user must have one of the given roles."""
    async def _check(current_user: CurrentUser) -> User:
        if current_user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {' or '.join(roles)}",
            )
        return current_user
    return Depends(_check)


def require_permission(code: str):
    """Dependency factory: user must have effective permission `code`."""
    async def _check(current_user: CurrentUser) -> User:
        if not has_permission(current_user, code):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required permission: {code}",
            )
        return current_user
    return Depends(_check)
