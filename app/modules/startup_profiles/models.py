from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.mixins import UUIDPrimaryKeyMixin, utcnow


class StartupProfile(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "startup_profiles"

    startup_id: Mapped[UUID] = mapped_column(
        ForeignKey("startup_applications.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    problem_statement: Mapped[str | None] = mapped_column(Text)
    solution_summary: Mapped[str | None] = mapped_column(Text)
    target_market: Mapped[str | None] = mapped_column(Text)
    business_model: Mapped[str | None] = mapped_column(Text)
    technology_summary: Mapped[str | None] = mapped_column(Text)
    traction_summary: Mapped[str | None] = mapped_column(Text)
    funding_summary: Mapped[str | None] = mapped_column(Text)
    ip_summary: Mapped[str | None] = mapped_column(Text)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
        nullable=False,
    )

    startup = relationship("StartupApplication")
    versions: Mapped[list[StartupProfileVersion]] = relationship(
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="StartupProfileVersion.version_number",
    )


class StartupProfileVersion(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "startup_profile_versions"
    __table_args__ = (
        UniqueConstraint("startup_profile_id", "version_number", name="uq_startup_profile_versions_number"),
    )

    startup_profile_id: Mapped[UUID] = mapped_column(
        ForeignKey("startup_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    profile_snapshot: Mapped[dict] = mapped_column(JSON, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    profile: Mapped[StartupProfile] = relationship(back_populates="versions")
