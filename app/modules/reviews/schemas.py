from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReviewerCommentCreate(BaseModel):
    comment: str = Field(min_length=1)


class ReviewerCommentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    startup_id: UUID
    evaluation_id: UUID
    reviewer_id: UUID | None
    comment: str
    created_at: datetime


class CommitteeNoteCreate(BaseModel):
    note: str = Field(min_length=1)


class CommitteeNoteRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    startup_id: UUID
    evaluation_id: UUID
    committee_member_id: UUID | None
    note: str
    created_at: datetime


class ScoreOverrideCreate(BaseModel):
    overridden_score: float = Field(ge=0)
    reason: str = Field(min_length=1)


class ScoreOverrideRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    evaluation_score_id: UUID
    original_score: float
    overridden_score: float
    overridden_by: UUID | None
    reason: str
    created_at: datetime
