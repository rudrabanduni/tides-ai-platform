from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import StartupStatus
from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utcnow


startup_status_enum = Enum(
    StartupStatus,
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    native_enum=False,
    length=64,
)


class StartupApplication(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "startup_applications"

    startup_name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    sector: Mapped[str | None] = mapped_column(String(128), index=True)
    stage: Mapped[str | None] = mapped_column(String(128))
    current_status: Mapped[StartupStatus] = mapped_column(
        startup_status_enum,
        default=StartupStatus.DRAFT,
        nullable=False,
        index=True,
    )
    problem_statement: Mapped[str | None] = mapped_column(Text)
    solution_summary: Mapped[str | None] = mapped_column(Text)
    business_model: Mapped[str | None] = mapped_column(Text)
    target_market: Mapped[str | None] = mapped_column(Text)
    traction_summary: Mapped[str | None] = mapped_column(Text)
    funding_status: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    creator = relationship("User")
    status_history: Mapped[list[StartupStatusHistory]] = relationship(
        back_populates="startup",
        cascade="all, delete-orphan",
    )


class StartupStatusHistory(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "startup_status_history"

    startup_id: Mapped[UUID] = mapped_column(
        ForeignKey("startup_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    old_status: Mapped[StartupStatus | None] = mapped_column(startup_status_enum)
    new_status: Mapped[StartupStatus] = mapped_column(startup_status_enum, nullable=False)
    changed_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    startup: Mapped[StartupApplication] = relationship(back_populates="status_history")
    changed_by_user = relationship("User")
