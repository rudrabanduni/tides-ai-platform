from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.mixins import UUIDPrimaryKeyMixin, utcnow


class ReviewerComment(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "reviewer_comments"

    startup_id: Mapped[UUID] = mapped_column(ForeignKey("startup_applications.id", ondelete="CASCADE"), index=True)
    evaluation_id: Mapped[UUID] = mapped_column(ForeignKey("evaluations.id", ondelete="CASCADE"), index=True)
    reviewer_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    startup = relationship("StartupApplication")
    evaluation = relationship("Evaluation")
    reviewer = relationship("User")


class CommitteeNote(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "committee_notes"

    startup_id: Mapped[UUID] = mapped_column(ForeignKey("startup_applications.id", ondelete="CASCADE"), index=True)
    evaluation_id: Mapped[UUID] = mapped_column(ForeignKey("evaluations.id", ondelete="CASCADE"), index=True)
    committee_member_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    startup = relationship("StartupApplication")
    evaluation = relationship("Evaluation")
    committee_member = relationship("User")


class ScoreOverride(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "score_overrides"

    evaluation_score_id: Mapped[UUID] = mapped_column(
        ForeignKey("evaluation_scores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    original_score: Mapped[float] = mapped_column(Float, nullable=False)
    overridden_score: Mapped[float] = mapped_column(Float, nullable=False)
    overridden_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    evaluation_score = relationship("EvaluationScore")
    overridden_by_user = relationship("User")
