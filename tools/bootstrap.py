#!/usr/bin/env python3
"""
Bootstrap script — run once at startup:
1. seed_permissions(): insert permission codes from RBAC registry if missing
2. create_admin(): create first admin user from env if users table is empty
"""
import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.core.config import get_settings
from app.rbac.permissions import ALL_PERMISSIONS
from app.repositories.permission_repo import PermissionRepository
from app.repositories.user_repo import UserRepository
from app.models.user import UserRole

settings = get_settings()


async def seed_permissions(db: AsyncSession) -> None:
    repo = PermissionRepository(db)
    await repo.seed(ALL_PERMISSIONS)
    await db.commit()
    print(f"[bootstrap] Seeded {len(ALL_PERMISSIONS)} permissions.")


async def create_admin(db: AsyncSession) -> None:
    repo = UserRepository(db)
    count = await repo.count()
    if count > 0:
        print("[bootstrap] Users exist — skipping admin creation.")
        return

    email = settings.ADMIN_BOOTSTRAP_EMAIL
    password = settings.ADMIN_BOOTSTRAP_PASSWORD
    user = await repo.create(email=email, password=password, role=UserRole.admin)
    await db.commit()
    print(f"[bootstrap] Created admin user: {email} (id={user.id})")


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        await seed_permissions(db)
        await create_admin(db)

    await engine.dispose()
    print("[bootstrap] Done.")


if __name__ == "__main__":
    asyncio.run(main())
