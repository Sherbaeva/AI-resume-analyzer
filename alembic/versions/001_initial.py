"""Initial database schema migration."""
from alembic import op
import sqlalchemy as sa

revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "job_descriptions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("title", sa.String(512), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "resumes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("file_hash", sa.String(64), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("content_type", sa.String(128), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("file_hash"),
    )
    op.create_index("ix_resumes_file_hash", "resumes", ["file_hash"])

    op.create_table(
        "analyses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("resume_id", sa.Integer(), nullable=False),
        sa.Column("job_description_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="queued"),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("matched_skills_json", sa.Text(), nullable=True),
        sa.Column("missing_skills_json", sa.Text(), nullable=True),
        sa.Column("explanations_json", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("scoring_version", sa.String(32), nullable=False, server_default="1.0"),
        sa.Column("parser_version", sa.String(32), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"]),
        sa.ForeignKeyConstraint(["job_description_id"], ["job_descriptions.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_analyses_resume_id", "analyses", ["resume_id"])
    op.create_index("ix_analyses_job_description_id", "analyses", ["job_description_id"])
    op.create_index("ix_analyses_status", "analyses", ["status"])

    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("action", sa.String(128), nullable=False),
        sa.Column("entity", sa.String(128), nullable=False),
        sa.Column("entity_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("audit_log")
    op.drop_index("ix_analyses_status", table_name="analyses")
    op.drop_index("ix_analyses_job_description_id", table_name="analyses")
    op.drop_index("ix_analyses_resume_id", table_name="analyses")
    op.drop_table("analyses")
    op.drop_index("ix_resumes_file_hash", table_name="resumes")
    op.drop_table("resumes")
    op.drop_table("job_descriptions")
