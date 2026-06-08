from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.enums import DocumentProcessingStatus, DocumentType, SourceType


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    startup_id: UUID
    document_type: DocumentType
    original_filename: str
    stored_filename: str
    file_path: str
    content_type: str | None
    file_size: int
    parsed_text: str | None
    processing_status: DocumentProcessingStatus
    uploaded_by: UUID | None
    created_at: datetime
    updated_at: datetime


class DocumentParsedTextUpdate(BaseModel):
    parsed_text: str = Field(min_length=1)
    processing_status: DocumentProcessingStatus = DocumentProcessingStatus.PARSED


class DocumentSourceCreate(BaseModel):
    document_id: UUID | None = None
    source_name: str = Field(min_length=1, max_length=255)
    source_type: SourceType
    confidence: float | None = Field(default=None, ge=0, le=1)


class DocumentSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    startup_id: UUID
    document_id: UUID | None
    source_name: str
    source_type: SourceType
    confidence: float | None
    created_at: datetime
