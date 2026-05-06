"""SQLAlchemy model for analyses table."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, Float, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

ANALYSIS_STATUSES = ("queued", "processing", "done", "failed")


class Analysis(Base):
    __tablename__ = "analyses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"), nullable=False, index=True)
    job_description_id: Mapped[int] = mapped_column(
        ForeignKey("job_descriptions.id"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued", index=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    matched_skills_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    missing_skills_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    explanations_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scoring_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0")
    parser_version: Mapped[str] = mapped_column(String(32), nullable=False, default="1.0")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
