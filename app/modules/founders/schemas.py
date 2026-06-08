from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class FounderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=64)
    education: str | None = None
    experience_summary: str | None = None
    linkedin_url: str | None = Field(default=None, max_length=500)
    role_in_startup: str | None = Field(default=None, max_length=255)


class FounderUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=64)
    education: str | None = None
    experience_summary: str | None = None
    linkedin_url: str | None = Field(default=None, max_length=500)
    role_in_startup: str | None = Field(default=None, max_length=255)


class FounderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    startup_id: UUID
    name: str
    email: EmailStr | None
    phone: str | None
    education: str | None
    experience_summary: str | None
    linkedin_url: str | None
    role_in_startup: str | None
    created_at: datetime
    updated_at: datetime
