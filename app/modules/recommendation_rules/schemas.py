from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator


class RecommendationRuleCreate(BaseModel):
    rule_name: str = Field(min_length=1, max_length=255)
    min_score: float = Field(ge=0, le=100)
    max_score: float = Field(ge=0, le=100)
    recommendation: str = Field(min_length=1, max_length=128)
    active: bool = True

    @model_validator(mode="after")
    def validate_score_range(self) -> "RecommendationRuleCreate":
        if self.min_score > self.max_score:
            raise ValueError("min_score must be less than or equal to max_score")
        return self


class RecommendationRuleUpdate(BaseModel):
    rule_name: str | None = Field(default=None, min_length=1, max_length=255)
    min_score: float | None = Field(default=None, ge=0, le=100)
    max_score: float | None = Field(default=None, ge=0, le=100)
    recommendation: str | None = Field(default=None, min_length=1, max_length=128)
    active: bool | None = None


class RecommendationRuleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    rule_name: str
    min_score: float
    max_score: float
    recommendation: str
    active: bool
    created_at: datetime
    updated_at: datetime
