from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import ReadOnlyUser, ReviewerUser
from app.modules.reviews.models import CommitteeNote, ReviewerComment, ScoreOverride
from app.modules.reviews.schemas import (
    CommitteeNoteCreate,
    CommitteeNoteRead,
    ReviewerCommentCreate,
    ReviewerCommentRead,
    ScoreOverrideCreate,
    ScoreOverrideRead,
)
from app.modules.reviews.service import ReviewService

router = APIRouter(tags=["Committee Review"])


@router.post(
    "/evaluations/{evaluation_id}/comments",
    response_model=ReviewerCommentRead,
    status_code=status.HTTP_201_CREATED,
)
def add_reviewer_comment(
    evaluation_id: UUID,
    payload: ReviewerCommentCreate,
    current_user: ReviewerUser,
    db: Annotated[Session, Depends(get_db)],
):
    return ReviewService(db).add_comment(evaluation_id, payload, actor_id=current_user.id)


@router.get("/evaluations/{evaluation_id}/comments", response_model=list[ReviewerCommentRead])
def list_reviewer_comments(
    evaluation_id: UUID,
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
) -> Sequence[ReviewerComment]:
    return ReviewService(db).list_comments(evaluation_id)


@router.post(
    "/evaluations/{evaluation_id}/committee-notes",
    response_model=CommitteeNoteRead,
    status_code=status.HTTP_201_CREATED,
)
def add_committee_note(
    evaluation_id: UUID,
    payload: CommitteeNoteCreate,
    current_user: ReviewerUser,
    db: Annotated[Session, Depends(get_db)],
):
    return ReviewService(db).add_committee_note(evaluation_id, payload, actor_id=current_user.id)


@router.get("/evaluations/{evaluation_id}/committee-notes", response_model=list[CommitteeNoteRead])
def list_committee_notes(
    evaluation_id: UUID,
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
) -> Sequence[CommitteeNote]:
    return ReviewService(db).list_committee_notes(evaluation_id)


@router.post(
    "/evaluation-scores/{score_id}/override",
    response_model=ScoreOverrideRead,
    status_code=status.HTTP_201_CREATED,
)
def override_score(
    score_id: UUID,
    payload: ScoreOverrideCreate,
    current_user: ReviewerUser,
    db: Annotated[Session, Depends(get_db)],
):
    return ReviewService(db).override_score(score_id, payload, actor_id=current_user.id)


@router.get("/evaluation-scores/{score_id}/overrides", response_model=list[ScoreOverrideRead])
def list_score_overrides(
    score_id: UUID,
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
) -> Sequence[ScoreOverride]:
    return ReviewService(db).list_overrides(score_id)
