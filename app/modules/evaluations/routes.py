from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import AdminUser, EvaluatorUser, ReadOnlyUser
from app.modules.evaluations.models import (
    Evaluation,
    EvaluationCriterion,
    EvaluationEvidence,
    EvaluationRubric,
    EvaluationScore,
)
from app.modules.evaluations.schemas import (
    EvaluationCreate,
    EvaluationCriterionCreate,
    EvaluationCriterionRead,
    EvaluationCriterionUpdate,
    EvaluationEvidenceCreate,
    EvaluationEvidenceRead,
    EvaluationFinalizeResponse,
    EvaluationRead,
    EvaluationRubricCreate,
    EvaluationRubricRead,
    EvaluationRubricUpdate,
    EvaluationScoreCreate,
    EvaluationScoreRead,
)
from app.modules.evaluations.service import EvaluationService

router = APIRouter(tags=["Evaluations"])


@router.post("/evaluation-rubrics", response_model=EvaluationRubricRead, status_code=status.HTTP_201_CREATED)
def create_rubric(payload: EvaluationRubricCreate, current_user: AdminUser, db: Annotated[Session, Depends(get_db)]):
    return EvaluationService(db).create_rubric(payload, actor_id=current_user.id)


@router.get("/evaluation-rubrics", response_model=list[EvaluationRubricRead])
def list_rubrics(
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> Sequence[EvaluationRubric]:
    return EvaluationService(db).list_rubrics(skip=skip, limit=limit)


@router.get("/evaluation-rubrics/{rubric_id}", response_model=EvaluationRubricRead)
def get_rubric(rubric_id: UUID, current_user: ReadOnlyUser, db: Annotated[Session, Depends(get_db)]):
    return EvaluationService(db).get_rubric(rubric_id)


@router.patch("/evaluation-rubrics/{rubric_id}", response_model=EvaluationRubricRead)
def update_rubric(
    rubric_id: UUID,
    payload: EvaluationRubricUpdate,
    current_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    return EvaluationService(db).update_rubric(rubric_id, payload, actor_id=current_user.id)


@router.post(
    "/evaluation-rubrics/{rubric_id}/criteria",
    response_model=EvaluationCriterionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_criterion(
    rubric_id: UUID,
    payload: EvaluationCriterionCreate,
    current_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    return EvaluationService(db).create_criterion(rubric_id, payload, actor_id=current_user.id)


@router.get("/evaluation-rubrics/{rubric_id}/criteria", response_model=list[EvaluationCriterionRead])
def list_criteria(
    rubric_id: UUID,
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
) -> Sequence[EvaluationCriterion]:
    return EvaluationService(db).list_criteria(rubric_id)


@router.patch("/evaluation-criteria/{criterion_id}", response_model=EvaluationCriterionRead)
def update_criterion(
    criterion_id: UUID,
    payload: EvaluationCriterionUpdate,
    current_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    return EvaluationService(db).update_criterion(criterion_id, payload, actor_id=current_user.id)


@router.post("/startups/{startup_id}/evaluations", response_model=EvaluationRead, status_code=status.HTTP_201_CREATED)
def create_evaluation(
    startup_id: UUID,
    payload: EvaluationCreate,
    current_user: EvaluatorUser,
    db: Annotated[Session, Depends(get_db)],
):
    return EvaluationService(db).create_evaluation(startup_id, payload, actor_id=current_user.id)


@router.get("/startups/{startup_id}/evaluations", response_model=list[EvaluationRead])
def list_evaluations_for_startup(
    startup_id: UUID,
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
) -> Sequence[Evaluation]:
    return EvaluationService(db).list_evaluations_for_startup(startup_id)


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationRead)
def get_evaluation(evaluation_id: UUID, current_user: ReadOnlyUser, db: Annotated[Session, Depends(get_db)]):
    return EvaluationService(db).get_evaluation(evaluation_id)


@router.post("/evaluations/{evaluation_id}/scores", response_model=EvaluationScoreRead, status_code=status.HTTP_201_CREATED)
def add_evaluation_score(
    evaluation_id: UUID,
    payload: EvaluationScoreCreate,
    current_user: EvaluatorUser,
    db: Annotated[Session, Depends(get_db)],
):
    return EvaluationService(db).add_score(evaluation_id, payload, actor_id=current_user.id)


@router.get("/evaluations/{evaluation_id}/scores", response_model=list[EvaluationScoreRead])
def list_evaluation_scores(
    evaluation_id: UUID,
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
) -> Sequence[EvaluationScore]:
    return EvaluationService(db).list_scores(evaluation_id)


@router.post(
    "/evaluation-scores/{score_id}/evidence",
    response_model=EvaluationEvidenceRead,
    status_code=status.HTTP_201_CREATED,
)
def add_evaluation_evidence(
    score_id: UUID,
    payload: EvaluationEvidenceCreate,
    current_user: EvaluatorUser,
    db: Annotated[Session, Depends(get_db)],
):
    return EvaluationService(db).add_evidence(score_id, payload, actor_id=current_user.id)


@router.get("/evaluation-scores/{score_id}/evidence", response_model=list[EvaluationEvidenceRead])
def list_evaluation_evidence(
    score_id: UUID,
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
) -> Sequence[EvaluationEvidence]:
    return EvaluationService(db).list_evidence(score_id)


@router.post("/evaluations/{evaluation_id}/finalize", response_model=EvaluationFinalizeResponse)
def finalize_evaluation(
    evaluation_id: UUID,
    current_user: EvaluatorUser,
    db: Annotated[Session, Depends(get_db)],
):
    evaluation, applied_rule = EvaluationService(db).finalize(evaluation_id, actor_id=current_user.id)
    return EvaluationFinalizeResponse(evaluation=evaluation, applied_rule=applied_rule)
