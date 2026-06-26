from __future__ import annotations

import enum
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class PipelineStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    WAITING_FOR_AI = "WAITING_FOR_AI"
    WAITING_FOR_RETRY = "WAITING_FOR_RETRY"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class KnowledgeFieldRegistry(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "knowledge_field_registry"

    field_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    value_type: Mapped[str] = mapped_column(String(32), nullable=False)  # string, number, boolean, date, json
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class StartupIntelligenceProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "startup_intelligence_profiles"

    startup_id: Mapped[UUID] = mapped_column(
        ForeignKey("startup_applications.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True
    )

    startup = relationship("StartupApplication")
    claims = relationship("StartupClaim", back_populates="profile", cascade="all, delete-orphan")
    conflicts = relationship("FieldConflict", back_populates="profile", cascade="all, delete-orphan")
    versions = relationship("StartupIntelligenceProfileVersion", back_populates="profile", cascade="all, delete-orphan")


class StartupClaim(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "startup_claims"

    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("startup_intelligence_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    field_id: Mapped[UUID] = mapped_column(
        ForeignKey("knowledge_field_registry.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    value_string: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    value_number: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_boolean: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    value_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    value_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=False)
    validation_status: Mapped[str] = mapped_column(String(32), default="UNVALIDATED", nullable=False)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    merge_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_preferred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    profile = relationship("StartupIntelligenceProfile", back_populates="claims")
    field = relationship("KnowledgeFieldRegistry")
    evidence = relationship("StartupEvidence", back_populates="claim", cascade="all, delete-orphan")
    versions = relationship("FieldVersion", back_populates="claim", cascade="all, delete-orphan")
    sources = relationship("FieldSource", back_populates="claim", cascade="all, delete-orphan")


class StartupEvidence(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "startup_evidence"

    claim_id: Mapped[UUID] = mapped_column(
        ForeignKey("startup_claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    source_document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    page_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    section_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    evidence_snippet: Mapped[str | None] = mapped_column(Text, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    reasoning: Mapped[str | None] = mapped_column(Text, nullable=True)
    validation_status: Mapped[str] = mapped_column(String(32), default="UNVALIDATED", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    claim = relationship("StartupClaim", back_populates="evidence")
    source_document = relationship("Document")


class FieldVersion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "field_versions"

    claim_id: Mapped[UUID] = mapped_column(
        ForeignKey("startup_claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    value_string: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    value_number: Mapped[float | None] = mapped_column(Float, nullable=True)
    value_boolean: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    value_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    value_json: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    changed_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    change_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    claim = relationship("StartupClaim", back_populates="versions")
    changer = relationship("User")


class FieldConflict(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "field_conflicts"

    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("startup_intelligence_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    field_id: Mapped[UUID] = mapped_column(
        ForeignKey("knowledge_field_registry.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    resolved: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    resolution_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    resolved_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    profile = relationship("StartupIntelligenceProfile", back_populates="conflicts")
    field = relationship("KnowledgeFieldRegistry")
    resolver = relationship("User")


class FieldSource(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "field_sources"

    claim_id: Mapped[UUID] = mapped_column(
        ForeignKey("startup_claims.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    document_id: Mapped[UUID] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    claim = relationship("StartupClaim", back_populates="sources")
    document = relationship("Document")


class StartupProcessingStatus(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "startup_processing_status"

    startup_id: Mapped[UUID] = mapped_column(
        ForeignKey("startup_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    pipeline_name: Mapped[str] = mapped_column(String(128), nullable=False)
    current_stage: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[PipelineStatus] = mapped_column(
        Enum(PipelineStatus, native_enum=False, length=32),
        default=PipelineStatus.QUEUED,
        nullable=False,
        index=True
    )
    progress_percentage: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    processing_time_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False
    )

    startup = relationship("StartupApplication")


class StartupIntelligenceProfileVersion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "startup_intelligence_profile_versions"

    profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("startup_intelligence_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    profile_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    profile = relationship("StartupIntelligenceProfile", back_populates="versions")
    creator = relationship("User")
