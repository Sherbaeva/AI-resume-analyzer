"""ORM model registry — import all models here so Alembic and Base.metadata see them."""
from app.core.database import Base  # noqa: F401

from app.models.job_description import JobDescription  # noqa: F401
from app.models.resume import Resume  # noqa: F401
from app.models.analysis import Analysis  # noqa: F401
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.user import User, UserRole  # noqa: F401
from app.models.permission import Permission, UserPermission  # noqa: F401
from app.models.skill_taxonomy import SkillTaxonomy  # noqa: F401

__all__ = [
    "Base",
    "JobDescription",
    "Resume",
    "Analysis",
    "AuditLog",
    "User",
    "UserRole",
    "Permission",
    "UserPermission",
    "SkillTaxonomy",
]
