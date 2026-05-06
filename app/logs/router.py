"""Audit logs read API — admin only."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_permission
from app.core.database import get_db
from app.models.audit_log import AuditLog
from pydantic import BaseModel

router = APIRouter(prefix="/logs", tags=["Audit Logs"])
_admin = require_permission("logs.view")


class AuditLogOut(BaseModel):
    id: int
    actor_user_id: Optional[int] = None
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    meta_json: Optional[dict] = None
    ip: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


@router.get("/audit", response_model=list[AuditLogOut], dependencies=[_admin])
async def get_audit_logs(
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    actor_user_id: Optional[int] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AuditLog)
    if action:
        stmt = stmt.where(AuditLog.action.ilike(f"%{action}%"))
    if entity_type:
        stmt = stmt.where(AuditLog.entity_type == entity_type)
    if actor_user_id:
        stmt = stmt.where(AuditLog.actor_user_id == actor_user_id)
    if date_from:
        stmt = stmt.where(AuditLog.created_at >= date_from)
    if date_to:
        stmt = stmt.where(AuditLog.created_at <= date_to)

    stmt = stmt.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)
    result = await db.execute(stmt)
    return list(result.scalars().all())
