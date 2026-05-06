"""Shared FastAPI dependencies."""
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from app.core.database import get_db


async def get_session(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    return db
