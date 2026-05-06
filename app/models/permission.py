"""SQLAlchemy models for permissions and user_permissions."""
from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    description: Mapped[str] = mapped_column(String(512), nullable=False, default="")

    user_permissions: Mapped[list["UserPermission"]] = relationship(
        "UserPermission", back_populates="permission"
    )


class UserPermission(Base):
    __tablename__ = "user_permissions"
    __table_args__ = (
        UniqueConstraint("user_id", "permission_id", name="uq_user_permission"),
    )

    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    permission_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True
    )

    user: Mapped["User"] = relationship("User", back_populates="user_permissions")
    permission: Mapped["Permission"] = relationship("Permission", back_populates="user_permissions")
