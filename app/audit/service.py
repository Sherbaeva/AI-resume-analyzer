"""Audit log utility — write structured entries to audit_log table."""
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog


async def write_audit(
    db: AsyncSession,
    action: str,
    entity_type: str,
    entity_id: int | None = None,
    meta: dict[str, Any] | None = None,
    actor_user_id: int | None = None,
    ip: str | None = None,
    user_agent: str | None = None,
) -> AuditLog:
    """Insert an audit log entry and flush (does not commit — caller's transaction)."""
    entry = AuditLog(
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        meta_json=meta,
        actor_user_id=actor_user_id,
        ip=ip,
        user_agent=user_agent,
    )
    db.add(entry)
    await db.flush()
    return entry
