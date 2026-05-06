"""Auth, RBAC, and Skill Taxonomy tables — migration 002."""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "002_auth_rbac"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ─── users ───────────────────────────────────────────────
    # Create enum type first, explicitly, so create_table doesn't try to create it again
    op.execute("DO $$ BEGIN CREATE TYPE userrole AS ENUM ('admin', 'hr'); EXCEPTION WHEN DUPLICATE_OBJECT THEN NULL; END $$;")

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("password_hash", sa.String(256), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM("admin", "hr", name="userrole", create_type=False),
            nullable=False,
        ),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    # ─── permissions ─────────────────────────────────────────
    op.create_table(
        "permissions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(128), nullable=False),
        sa.Column("description", sa.String(512), nullable=False, server_default=""),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_permissions_code", "permissions", ["code"])

    # ─── user_permissions ────────────────────────────────────
    op.create_table(
        "user_permissions",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("permission_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["permission_id"], ["permissions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id", "permission_id"),
        sa.UniqueConstraint("user_id", "permission_id", name="uq_user_permission"),
    )

    # ─── skill_taxonomy ──────────────────────────────────────
    op.create_table(
        "skill_taxonomy",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(256), nullable=False),
        sa.Column("category", sa.String(128), nullable=True),
        sa.Column("aliases", postgresql.JSONB(), nullable=False, server_default="[]"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_by_id", sa.Integer(), nullable=True),
        sa.Column("updated_by_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["updated_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_skill_taxonomy_name", "skill_taxonomy", ["name"])

    # ─── expand audit_log ────────────────────────────────────
    # Rename entity → entity_type (keep old data)
    op.alter_column("audit_log", "entity", new_column_name="entity_type")

    op.add_column("audit_log", sa.Column(
        "actor_user_id", sa.Integer(),
        sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    ))
    op.add_column("audit_log", sa.Column(
        "meta_json", postgresql.JSONB(), nullable=True
    ))
    op.add_column("audit_log", sa.Column(
        "ip", sa.String(64), nullable=True
    ))
    op.add_column("audit_log", sa.Column(
        "user_agent", sa.String(512), nullable=True
    ))

    op.create_index("ix_audit_log_action", "audit_log", ["action"])
    op.create_index("ix_audit_log_entity_type", "audit_log", ["entity_type"])
    op.create_index("ix_audit_log_actor_user_id", "audit_log", ["actor_user_id"])
    op.create_index("ix_audit_log_created_at", "audit_log", ["created_at"])


def downgrade() -> None:
    # Drop audit_log additions
    op.drop_index("ix_audit_log_created_at", table_name="audit_log")
    op.drop_index("ix_audit_log_actor_user_id", table_name="audit_log")
    op.drop_index("ix_audit_log_entity_type", table_name="audit_log")
    op.drop_index("ix_audit_log_action", table_name="audit_log")
    op.drop_column("audit_log", "user_agent")
    op.drop_column("audit_log", "ip")
    op.drop_column("audit_log", "meta_json")
    op.drop_column("audit_log", "actor_user_id")
    op.alter_column("audit_log", "entity_type", new_column_name="entity")

    op.drop_index("ix_skill_taxonomy_name", table_name="skill_taxonomy")
    op.drop_table("skill_taxonomy")
    op.drop_table("user_permissions")
    op.drop_index("ix_permissions_code", table_name="permissions")
    op.drop_table("permissions")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    postgresql.ENUM("admin", "hr", name="userrole").drop(op.get_bind())
