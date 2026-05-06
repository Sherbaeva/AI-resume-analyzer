"""User repository — CRUD for User and UserPermission."""
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.user import User, UserRole
from app.models.permission import Permission, UserPermission
from app.auth.password import hash_password


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.user_permissions).selectinload(UserPermission.permission))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.user_permissions).selectinload(UserPermission.permission))
            .where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def list_all(self, skip: int = 0, limit: int = 100) -> list[User]:
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.user_permissions).selectinload(UserPermission.permission))
            .offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def create(
        self, email: str, password: str, role: UserRole = UserRole.hr
    ) -> User:
        user = User(email=email, password_hash=hash_password(password), role=role)
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update(self, user: User, **kwargs) -> User:
        for key, value in kwargs.items():
            if key == "password":
                setattr(user, "password_hash", hash_password(value))
            else:
                setattr(user, key, value)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def set_permissions(self, user_id: int, permission_ids: list[int]) -> None:
        """Replace all user permissions with the given set."""
        await self.db.execute(
            delete(UserPermission).where(UserPermission.user_id == user_id)
        )
        for pid in permission_ids:
            self.db.add(UserPermission(user_id=user_id, permission_id=pid))
        await self.db.flush()

    async def get_permissions(self, user_id: int) -> list[Permission]:
        result = await self.db.execute(
            select(Permission)
            .join(UserPermission, UserPermission.permission_id == Permission.id)
            .where(UserPermission.user_id == user_id)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        from sqlalchemy import func
        result = await self.db.execute(select(func.count()).select_from(User))
        return result.scalar_one()
