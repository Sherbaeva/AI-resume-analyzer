"""Permission repository — seed and lookup."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.permission import Permission


class PermissionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_code(self, code: str) -> Permission | None:
        result = await self.db.execute(
            select(Permission).where(Permission.code == code)
        )
        return result.scalar_one_or_none()

    async def get_by_codes(self, codes: list[str]) -> list[Permission]:
        result = await self.db.execute(
            select(Permission).where(Permission.code.in_(codes))
        )
        return list(result.scalars().all())

    async def get_all(self) -> list[Permission]:
        result = await self.db.execute(select(Permission))
        return list(result.scalars().all())

    async def get_by_id(self, permission_id: int) -> Permission | None:
        result = await self.db.execute(
            select(Permission).where(Permission.id == permission_id)
        )
        return result.scalar_one_or_none()

    async def create(self, code: str, description: str = "") -> Permission:
        perm = Permission(code=code, description=description)
        self.db.add(perm)
        await self.db.flush()
        return perm

    async def seed(self, permissions_data: list[dict]) -> None:
        """Insert permissions that don't already exist."""
        for data in permissions_data:
            existing = await self.get_by_code(data["code"])
            if not existing:
                await self.create(data["code"], data.get("description", ""))
