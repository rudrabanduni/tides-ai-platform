from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CompanyProfilePayload(BaseModel):
    website: str | None = Field(default=None, max_length=500)
    incorporation_status: str | None = Field(default=None, max_length=128)
    registration_number: str | None = Field(default=None, max_length=128)
    location: str | None = Field(default=None, max_length=255)
    team_size: int | None = Field(default=None, ge=0)
    revenue_status: str | None = None
    ip_status: str | None = None
    market_category: str | None = Field(default=None, max_length=128)


class CompanyProfileRead(CompanyProfilePayload):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    startup_id: UUID
    created_at: datetime
    updated_at: datetime
