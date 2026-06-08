from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import EvaluationStatus, SourceType
from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utcnow
from app.modules.documents.models import source_type_enum


evaluation_status_enum = Enum(
    EvaluationStatus,
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    native_enum=False,
    length=64,
)


class EvaluationRubric(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evaluation_rubrics"
    __table_args__ = (UniqueConstraint("name", "version", name="uq_evaluation_rubrics_name_version"),)

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    criteria: Mapped[list[EvaluationCriterion]] = relationship(
        back_populates="rubric",
        cascade="all, delete-orphan",
    )


class EvaluationCriterion(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "evaluation_criteria"

    rubric_id: Mapped[UUID] = mapped_column(
        ForeignKey("evaluation_rubrics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    weight: Mapped[float] = mapped_column(Float, nullable=False)
    max_score: Mapped[int] = mapped_column(Integer, default=10, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)

    rubric: Mapped[EvaluationRubric] = relationship(back_populates="criteria")


class Evaluation(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "evaluations"

    startup_id: Mapped[UUID] = mapped_column(
        ForeignKey("startup_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rubric_id: Mapped[UUID] = mapped_column(ForeignKey("evaluation_rubrics.id", ondelete="RESTRICT"), nullable=False)
    startup_profile_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("startup_profile_versions.id", ondelete="SET NULL"),
        index=True,
    )
    status: Mapped[EvaluationStatus] = mapped_column(
        evaluation_status_enum,
        default=EvaluationStatus.CREATED,
        nullable=False,
        index=True,
    )
    overall_score: Mapped[float | None] = mapped_column(Float)
    recommendation: Mapped[str | None] = mapped_column(String(128))
    recommendation_rule_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("recommendation_rules.id", ondelete="SET NULL"),
        index=True,
    )
    confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    startup = relationship("StartupApplication")
    rubric: Mapped[EvaluationRubric] = relationship()
    startup_profile_version = relationship("StartupProfileVersion")
    recommendation_rule = relationship("RecommendationRule")
    scores: Mapped[list[EvaluationScore]] = relationship(
        back_populates="evaluation",
        cascade="all, delete-orphan",
    )


class EvaluationScore(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "evaluation_scores"
    __table_args__ = (UniqueConstraint("evaluation_id", "criteria_id", name="uq_evaluation_scores_criterion"),)

    evaluation_id: Mapped[UUID] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    criteria_id: Mapped[UUID] = mapped_column(
        ForeignKey("evaluation_criteria.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    ai_score: Mapped[float | None] = mapped_column(Float)
    reviewer_score: Mapped[float | None] = mapped_column(Float)
    final_score: Mapped[float | None] = mapped_column(Float)
    confidence: Mapped[float | None] = mapped_column(Float)
    reasoning: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    evaluation: Mapped[Evaluation] = relationship(back_populates="scores")
    criterion: Mapped[EvaluationCriterion] = relationship()
    evidence: Mapped[list[EvaluationEvidence]] = relationship(
        back_populates="evaluation_score",
        cascade="all, delete-orphan",
    )


class EvaluationEvidence(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "evaluation_evidence"

    evaluation_score_id: Mapped[UUID] = mapped_column(
        ForeignKey("evaluation_scores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_text: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[SourceType] = mapped_column(source_type_enum, nullable=False)
    source_id: Mapped[UUID] = mapped_column(ForeignKey("document_sources.id", ondelete="RESTRICT"), nullable=False)
    source_reference: Mapped[str | None] = mapped_column(String(500))
    page_number: Mapped[int | None] = mapped_column(Integer)
    section_name: Mapped[str | None] = mapped_column(String(255))
    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    evaluation_score: Mapped[EvaluationScore] = relationship(back_populates="evidence")
    source = relationship("DocumentSource")
