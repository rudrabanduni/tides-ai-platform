from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

ALLOWED_STAGES = ("Ideation", "Pre-Seed", "Seed", "MVP", "Early Revenue", "Growth", "Scale")


class FounderInput(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    role_in_startup: str | None = Field(default=None, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=64)
    education: str | None = Field(default=None, max_length=2000)
    experience_summary: str | None = Field(default=None, max_length=4000)
    linkedin_url: str | None = Field(default=None, max_length=500)


class Declarations(BaseModel):
    information_accurate: bool = Field(description="Applicant confirms the information is accurate")
    consent_to_evaluation: bool = Field(description="Applicant consents to AI-assisted diligence")
    documents_owned_or_authorised: bool = Field(description="Applicant owns or is authorised to share documents")
    synthetic_demo_data: bool = Field(default=False, description="Marks the application as synthetic demonstration data")


class ApplicationCreate(BaseModel):
    """Full LaunchIndex startup incubation application form."""

    company_name: str = Field(min_length=2, max_length=255)
    sector: str = Field(min_length=2, max_length=128)
    industry: str | None = Field(default=None, max_length=255)
    stage: str = Field(min_length=2, max_length=128)
    location: str | None = Field(default=None, max_length=255)
    website: str | None = Field(default=None, max_length=500)

    contact_name: str = Field(min_length=2, max_length=255)
    contact_email: EmailStr
    contact_phone: str | None = Field(default=None, max_length=64)

    founders: list[FounderInput] = Field(min_length=1, max_length=10)

    problem_statement: str = Field(min_length=20, max_length=5000)
    proposed_solution: str = Field(min_length=20, max_length=5000)
    product_technology: str | None = Field(default=None, max_length=5000)
    target_market: str = Field(min_length=10, max_length=5000)
    business_model: str = Field(min_length=10, max_length=5000)
    traction: str | None = Field(default=None, max_length=5000)
    revenue_information: str | None = Field(default=None, max_length=3000)
    financial_information: str | None = Field(default=None, max_length=5000)
    funding_requirement: str | None = Field(default=None, max_length=3000)
    incubation_support_requirement: str | None = Field(default=None, max_length=3000)

    declarations: Declarations

    @field_validator("stage")
    @classmethod
    def _stage_known(cls, value: str) -> str:
        cleaned = value.strip()
        for allowed in ALLOWED_STAGES:
            if cleaned.lower() == allowed.lower():
                return allowed
        raise ValueError(f"stage must be one of {', '.join(ALLOWED_STAGES)}")

    @field_validator("declarations")
    @classmethod
    def _declarations_required(cls, value: Declarations) -> Declarations:
        if not (value.information_accurate and value.consent_to_evaluation and value.documents_owned_or_authorised):
            raise ValueError("All three applicant declarations must be accepted before submission")
        return value


class DocumentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    document_type: str
    original_filename: str
    content_type: str | None
    file_size: int
    processing_status: str
    created_at: datetime


class FounderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    role_in_startup: str | None = None
    email: str | None = None
    phone: str | None = None
    education: str | None = None
    experience_summary: str | None = None
    linkedin_url: str | None = None


class EvaluationRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    startup_id: UUID
    application_id: UUID | None
    status: str
    mode: str
    current_stage: str | None
    progress_pct: int
    stages: list[dict[str, Any]]
    pipeline_status: str | None
    error_message: str | None
    report_id: str | None
    summary: dict[str, Any]
    cost_usd: float
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    disclosure: str | None = None


class ApplicationRead(BaseModel):
    id: UUID
    application_ref: str
    startup_id: UUID
    company_name: str
    sector: str | None
    industry: str | None
    stage: str | None
    location: str | None
    website: str | None
    status: str
    contact_name: str | None
    contact_email: str | None
    contact_phone: str | None
    problem_statement: str | None
    proposed_solution: str | None
    product_technology: str | None
    target_market: str | None
    business_model: str | None
    traction: str | None
    revenue_information: str | None
    financial_information: str | None
    funding_requirement: str | None
    incubation_support_requirement: str | None
    declarations: dict[str, Any]
    is_synthetic: bool
    submitted_at: datetime | None
    created_at: datetime
    founders: list[FounderRead] = []
    documents: list[DocumentSummary] = []
    latest_run: EvaluationRunRead | None = None


class ApplicationListItem(BaseModel):
    id: UUID
    application_ref: str
    startup_id: UUID
    company_name: str
    sector: str | None
    stage: str | None
    status: str
    is_synthetic: bool
    document_count: int
    created_at: datetime
    latest_run_status: str | None = None
    latest_run_id: str | None = None
