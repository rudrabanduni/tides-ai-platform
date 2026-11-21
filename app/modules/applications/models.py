"""Persistent records for the end-to-end incubation application workflow.

* ApplicationSubmission - the full LaunchIndex intake form submitted for one startup
  (1:1 with StartupApplication). Holds a human-readable application reference and an
  idempotency key so a retried browser submission never creates a duplicate application.
* EvaluationRun - one execution of the evaluation pipeline for a startup. Its stage list is
  written by the pipeline's progress events; the UI reads progress only from this row.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ApplicationSubmission(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "application_submissions"

    application_ref: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    startup_id: Mapped[UUID] = mapped_column(
        ForeignKey("startup_applications.id", ondelete="CASCADE"), unique=True, nullable=False, index=True
    )
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True, index=True)

    industry: Mapped[str | None] = mapped_column(String(255))
    location: Mapped[str | None] = mapped_column(String(255))
    contact_name: Mapped[str | None] = mapped_column(String(255))
    contact_email: Mapped[str | None] = mapped_column(String(320))
    contact_phone: Mapped[str | None] = mapped_column(String(64))
    website: Mapped[str | None] = mapped_column(String(500))
    product_technology: Mapped[str | None] = mapped_column(Text)
    revenue_information: Mapped[str | None] = mapped_column(Text)
    financial_information: Mapped[str | None] = mapped_column(Text)
    funding_requirement: Mapped[str | None] = mapped_column(Text)
    incubation_support_requirement: Mapped[str | None] = mapped_column(Text)
    declarations: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    submitted_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    startup = relationship("StartupApplication")


class EvaluationRun(TimestampMixin, Base):
    __tablename__ = "evaluation_runs"
    __table_args__ = (Index("ix_evaluation_runs_startup_status", "startup_id", "status"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # == pipeline evaluation_id
    startup_id: Mapped[UUID] = mapped_column(
        ForeignKey("startup_applications.id", ondelete="CASCADE"), nullable=False, index=True
    )
    application_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("application_submissions.id", ondelete="SET NULL"), index=True
    )
    # QUEUED | RUNNING | COMPLETED | BLOCKED | FAILED
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="QUEUED", index=True)
    # MOCK_DEMONSTRATION | LIVE_PROVIDER
    mode: Mapped[str] = mapped_column(String(32), nullable=False)
    current_stage: Mapped[str | None] = mapped_column(String(128))
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    stages: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    pipeline_status: Mapped[str | None] = mapped_column(String(64))
    error_message: Mapped[str | None] = mapped_column(Text)
    report_id: Mapped[str | None] = mapped_column(String(64))
    summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    started_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
