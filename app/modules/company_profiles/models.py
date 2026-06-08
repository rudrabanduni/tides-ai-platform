from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class CompanyProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "company_profiles"

    startup_id: Mapped[UUID] = mapped_column(
        ForeignKey("startup_applications.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    website: Mapped[str | None] = mapped_column(String(500))
    incorporation_status: Mapped[str | None] = mapped_column(String(128))
    registration_number: Mapped[str | None] = mapped_column(String(128))
    location: Mapped[str | None] = mapped_column(String(255))
    team_size: Mapped[int | None] = mapped_column(Integer)
    revenue_status: Mapped[str | None] = mapped_column(Text)
    ip_status: Mapped[str | None] = mapped_column(Text)
    market_category: Mapped[str | None] = mapped_column(String(128))

    startup = relationship("StartupApplication")
