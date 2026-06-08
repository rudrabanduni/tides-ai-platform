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
