from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Knowledge Field Registry Schemas ---
class KnowledgeFieldRegistryBase(BaseModel):
    field_key: str = Field(..., max_length=128)
    field_name: str = Field(..., max_length=255)
    description: str | None = None
    value_type: str = Field(..., max_length=32)
    is_active: bool = True


class KnowledgeFieldRegistryCreate(KnowledgeFieldRegistryBase):
    pass


class KnowledgeFieldRegistryUpdate(BaseModel):
    field_name: str | None = Field(None, max_length=255)
    description: str | None = None
    value_type: str | None = Field(None, max_length=32)
    is_active: bool | None = None


class KnowledgeFieldRegistryRead(KnowledgeFieldRegistryBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Startup Intelligence Profile Version Schemas ---
class StartupIntelligenceProfileVersionBase(BaseModel):
    profile_id: UUID
    version_number: int
    profile_snapshot: dict[str, Any]
    created_by: UUID | None = None


class StartupIntelligenceProfileVersionCreate(BaseModel):
    profile_snapshot: dict[str, Any]


class StartupIntelligenceProfileVersionRead(StartupIntelligenceProfileVersionBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Startup Evidence Schemas ---
class StartupEvidenceBase(BaseModel):
    claim_id: UUID
    source_document_id: UUID | None = None
    page_number: int | None = None
    section_name: str | None = Field(None, max_length=255)
    evidence_snippet: str | None = None
    confidence_score: float = Field(1.0, ge=0.0, le=1.0)
    reasoning: str | None = None
    validation_status: str = Field("UNVALIDATED", max_length=32)


class StartupEvidenceCreate(StartupEvidenceBase):
    pass


class StartupEvidenceUpdate(BaseModel):
    page_number: int | None = None
    section_name: str | None = Field(None, max_length=255)
    evidence_snippet: str | None = None
    confidence_score: float | None = Field(None, ge=0.0, le=1.0)
    reasoning: str | None = None
    validation_status: str | None = Field(None, max_length=32)


class StartupEvidenceRead(StartupEvidenceBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Startup Claim Schemas ---
class StartupClaimBase(BaseModel):
    profile_id: UUID
    field_id: UUID
    value_string: str | None = Field(None, max_length=1000)
    value_number: float | None = None
    value_boolean: bool | None = None
    value_date: datetime | None = None
    value_json: Any | None = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    validation_status: str = Field("UNVALIDATED", max_length=32)
    reasoning: str | None = None
    confidence_reason: str | None = None
    merge_reason: str | None = None
    is_preferred: bool = False


class StartupClaimCreate(StartupClaimBase):
    pass


class StartupClaimUpdate(BaseModel):
    value_string: str | None = Field(None, max_length=1000)
    value_number: float | None = None
    value_boolean: bool | None = None
    value_date: datetime | None = None
    value_json: Any | None = None
    confidence_score: float | None = Field(None, ge=0.0, le=1.0)
    validation_status: str | None = Field(None, max_length=32)
    reasoning: str | None = None
    confidence_reason: str | None = None
    merge_reason: str | None = None
    is_preferred: bool | None = None


class StartupClaimRead(StartupClaimBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    evidence: list[StartupEvidenceRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# --- Field Conflict Schemas ---
class FieldConflictBase(BaseModel):
    profile_id: UUID
    field_id: UUID
    resolved: bool = False
    resolution_reason: str | None = None
    resolved_by: UUID | None = None


class FieldConflictCreate(FieldConflictBase):
    pass


class FieldConflictUpdate(BaseModel):
    resolved: bool | None = None
    resolution_reason: str | None = None
    resolved_by: UUID | None = None


class FieldConflictRead(FieldConflictBase):
    id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Startup Intelligence Profile Schemas ---
class StartupIntelligenceProfileBase(BaseModel):
    startup_id: UUID


class StartupIntelligenceProfileCreate(StartupIntelligenceProfileBase):
    pass


class StartupIntelligenceProfileRead(StartupIntelligenceProfileBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    claims: list[StartupClaimRead] = Field(default_factory=list)
    conflicts: list[FieldConflictRead] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


# --- Startup Processing Status Schemas ---
class StartupProcessingStatusBase(BaseModel):
    startup_id: UUID
    pipeline_name: str = Field(..., max_length=128)
    current_stage: str = Field(..., max_length=64)
    status: str = Field(..., max_length=32)
    progress_percentage: int = Field(0, ge=0, le=100)
    retry_count: int = 0
    last_error: str | None = None
    processing_time_ms: int = 0


class StartupProcessingStatusCreate(StartupProcessingStatusBase):
    pass


class StartupProcessingStatusUpdate(BaseModel):
    current_stage: str | None = Field(None, max_length=64)
    status: str | None = Field(None, max_length=32)
    progress_percentage: int | None = Field(None, ge=0, le=100)
    retry_count: int | None = None
    last_error: str | None = None
    processing_time_ms: int | None = None


class StartupProcessingStatusRead(StartupProcessingStatusBase):
    id: UUID
    started_at: datetime
    completed_at: datetime | None = None
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
