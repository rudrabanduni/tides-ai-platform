from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.core.enums import EvaluationStatus, SourceType


class EvaluationRubricCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    version: str = Field(min_length=1, max_length=64)
    is_active: bool = True


class EvaluationRubricUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    version: str | None = Field(default=None, min_length=1, max_length=64)
    is_active: bool | None = None


class EvaluationRubricRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None
    version: str
    is_active: bool
    created_at: datetime
    updated_at: datetime


class EvaluationCriterionCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    weight: float = Field(gt=0)
    max_score: int = Field(default=10, gt=0)
    is_active: bool = True


class EvaluationCriterionUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    weight: float | None = Field(default=None, gt=0)
    max_score: int | None = Field(default=None, gt=0)
    is_active: bool | None = None


class EvaluationCriterionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rubric_id: UUID
    name: str
    description: str | None
    weight: float
    max_score: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class EvaluationCreate(BaseModel):
    rubric_id: UUID


class EvaluationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    startup_id: UUID
    rubric_id: UUID
    startup_profile_version_id: UUID | None
    status: EvaluationStatus
    overall_score: float | None
    recommendation: str | None
    recommendation_rule_id: UUID | None
    confidence: float | None
    created_at: datetime
    completed_at: datetime | None


class EvaluationScoreCreate(BaseModel):
    criteria_id: UUID
    ai_score: float | None = Field(default=None, ge=0)
    reviewer_score: float | None = Field(default=None, ge=0)
    final_score: float | None = Field(default=None, ge=0)
    confidence: float | None = Field(default=None, ge=0, le=1)
    reasoning: str | None = None

    @model_validator(mode="after")
    def require_one_score(self) -> "EvaluationScoreCreate":
        if self.ai_score is None and self.reviewer_score is None and self.final_score is None:
            raise ValueError("At least one score value is required")
        return self


class EvaluationScoreRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    evaluation_id: UUID
    criteria_id: UUID
    ai_score: float | None
    reviewer_score: float | None
    final_score: float | None
    confidence: float | None
    reasoning: str | None
    created_at: datetime


class EvaluationEvidenceCreate(BaseModel):
    evidence_text: str = Field(min_length=1)
    source_type: SourceType
    source_id: UUID
    source_reference: str | None = Field(default=None, max_length=500)
    page_number: int | None = Field(default=None, ge=1)
    section_name: str | None = Field(default=None, max_length=255)
    confidence: float = Field(ge=0, le=1)


class EvaluationEvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    evaluation_score_id: UUID
    evidence_text: str
    source_type: SourceType
    source_id: UUID
    source_reference: str | None
    page_number: int | None
    section_name: str | None
    confidence: float


class EvaluationFinalizeResponse(BaseModel):
    evaluation: EvaluationRead
    applied_rule: str | None
