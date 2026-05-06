"""Repository for AuditLog writes."""
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(
        self,
        action: str,
        entity_type: str,
        entity_id: int | None = None,
        actor_user_id: int | None = None,
        meta_json: dict | None = None,
        ip: str | None = None,
        user_agent: str | None = None,
    ) -> AuditLog:
        entry = AuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            actor_user_id=actor_user_id,
            meta_json=meta_json,
            ip=ip,
            user_agent=user_agent,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry
