from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.enums import DocumentProcessingStatus, DocumentType, SourceType
from app.db.base_class import Base
from app.db.mixins import TimestampMixin, UUIDPrimaryKeyMixin, utcnow


document_type_enum = Enum(
    DocumentType,
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    native_enum=False,
    length=64,
)
document_processing_status_enum = Enum(
    DocumentProcessingStatus,
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    native_enum=False,
    length=64,
)
source_type_enum = Enum(
    SourceType,
    values_callable=lambda enum_cls: [item.value for item in enum_cls],
    native_enum=False,
    length=64,
)


class Document(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "documents"

    startup_id: Mapped[UUID] = mapped_column(
        ForeignKey("startup_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_type: Mapped[DocumentType] = mapped_column(document_type_enum, nullable=False)
    original_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(500), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1000), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(255))
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    parsed_text: Mapped[str | None] = mapped_column(Text)
    processing_status: Mapped[DocumentProcessingStatus] = mapped_column(
        document_processing_status_enum,
        default=DocumentProcessingStatus.UPLOADED,
        nullable=False,
    )
    uploaded_by: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)

    startup = relationship("StartupApplication")
    uploader = relationship("User")
    sources: Mapped[list[DocumentSource]] = relationship(back_populates="document")


class DocumentSource(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "document_sources"

    startup_id: Mapped[UUID] = mapped_column(
        ForeignKey("startup_applications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    document_id: Mapped[UUID | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"), index=True)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[SourceType] = mapped_column(source_type_enum, nullable=False, index=True)
    confidence: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    startup = relationship("StartupApplication")
    document: Mapped[Document | None] = relationship(back_populates="sources")
