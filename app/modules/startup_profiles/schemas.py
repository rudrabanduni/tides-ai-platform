from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class StartupProfilePayload(BaseModel):
    problem_statement: str | None = None
    solution_summary: str | None = None
    target_market: str | None = None
    business_model: str | None = None
    technology_summary: str | None = None
    traction_summary: str | None = None
    funding_summary: str | None = None
    ip_summary: str | None = None


class StartupProfileRead(StartupProfilePayload):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    startup_id: UUID
    generated_at: datetime
    updated_at: datetime


class StartupProfileVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    startup_profile_id: UUID
    version_number: int
    profile_snapshot: dict
    created_at: datetime
class StartupProfileAgentOutput(BaseModel):
    executive_summary: str
    business_model: str
    customer_segments: str
    market_opportunity: str
    strengths: list[str]
    risks: list[str]
    missing_information: list[str]


class StartupEvaluationScore(BaseModel):
    innovation_score: int
    market_score: int
    execution_score: int
    overall_score: int
    rationale: list[str]


class StartupEvaluationOutput(BaseModel):
    executive_summary: str
    innovation_score: int
    market_score: int
    execution_score: int
    overall_score: int
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]


class StartupAssessmentResult(BaseModel):
    profile: StartupProfileAgentOutput
    rule_based_score: StartupEvaluationScore
    ai_evaluation: StartupEvaluationOutput


class AIAssessmentRecordRead(BaseModel):
    """API read-schema for a persisted AI assessment record."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    startup_id: UUID
    executive_summary: str
    innovation_score: int
    market_score: int
    execution_score: int
    overall_score: int
    strengths: list[str]
    weaknesses: list[str]
    recommendations: list[str]
    assessed_by: UUID | None
    created_at: datetime