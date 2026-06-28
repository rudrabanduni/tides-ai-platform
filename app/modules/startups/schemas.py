from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.core.enums import StartupStatus


class StartupCreate(BaseModel):
    startup_name: str = Field(min_length=1, max_length=255)
    sector: str | None = Field(default=None, max_length=128)
    stage: str | None = Field(default=None, max_length=128)
    problem_statement: str | None = None
    solution_summary: str | None = None
    business_model: str | None = None
    target_market: str | None = None
    traction_summary: str | None = None
    funding_status: str | None = None


class StartupUpdate(BaseModel):
    startup_name: str | None = Field(default=None, min_length=1, max_length=255)
    sector: str | None = Field(default=None, max_length=128)
    stage: str | None = Field(default=None, max_length=128)
    problem_statement: str | None = None
    solution_summary: str | None = None
    business_model: str | None = None
    target_market: str | None = None
    traction_summary: str | None = None
    funding_status: str | None = None


class StartupStatusUpdate(BaseModel):
    new_status: StartupStatus
    reason: str = Field(min_length=1)


class BulkStatusUpdate(BaseModel):
    startup_ids: list[UUID]
    new_status: StartupStatus
    reason: str = Field(min_length=1)


class BulkDelete(BaseModel):
    startup_ids: list[UUID]


class StartupRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    startup_name: str
    sector: str | None
    stage: str | None
    current_status: StartupStatus
    problem_statement: str | None
    solution_summary: str | None
    business_model: str | None
    target_market: str | None
    traction_summary: str | None
    funding_status: str | None
    created_by: UUID | None
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @computed_field
    def status(self) -> str:
        return self.current_status.value if hasattr(self.current_status, "value") else str(self.current_status)


class StartupStatusHistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    startup_id: UUID
    old_status: StartupStatus | None
    new_status: StartupStatus
    changed_by: UUID | None
    reason: str | None
    created_at: datetime
