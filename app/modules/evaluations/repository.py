from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.evaluations.models import (
    Evaluation,
    EvaluationCriterion,
    EvaluationEvidence,
    EvaluationRubric,
    EvaluationScore,
)
from app.repositories.base import BaseRepository


class EvaluationRubricRepository(BaseRepository[EvaluationRubric]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, EvaluationRubric)

    def list(self, *, skip: int = 0, limit: int = 100) -> Sequence[EvaluationRubric]:
        statement = select(EvaluationRubric).order_by(EvaluationRubric.created_at.desc()).offset(skip).limit(limit)
        return self.db.scalars(statement).all()


class EvaluationCriterionRepository(BaseRepository[EvaluationCriterion]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, EvaluationCriterion)

    def list_for_rubric(self, rubric_id: UUID) -> Sequence[EvaluationCriterion]:
        statement = (
            select(EvaluationCriterion)
            .where(EvaluationCriterion.rubric_id == rubric_id)
            .order_by(EvaluationCriterion.created_at.asc())
        )
        return self.db.scalars(statement).all()


class EvaluationRepository(BaseRepository[Evaluation]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Evaluation)

    def get(self, entity_id: UUID) -> Evaluation | None:
        statement = select(Evaluation).options(joinedload(Evaluation.scores)).where(Evaluation.id == entity_id)
        return self.db.scalar(statement)

    def list_for_startup(self, startup_id: UUID) -> Sequence[Evaluation]:
        statement = select(Evaluation).where(Evaluation.startup_id == startup_id).order_by(Evaluation.created_at.desc())
        return self.db.scalars(statement).all()


class EvaluationScoreRepository(BaseRepository[EvaluationScore]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, EvaluationScore)

    def get_for_evaluation_criterion(self, evaluation_id: UUID, criteria_id: UUID) -> EvaluationScore | None:
        statement = select(EvaluationScore).where(
            EvaluationScore.evaluation_id == evaluation_id,
            EvaluationScore.criteria_id == criteria_id,
        )
        return self.db.scalar(statement)

    def list_for_evaluation(self, evaluation_id: UUID) -> Sequence[EvaluationScore]:
        statement = select(EvaluationScore).where(EvaluationScore.evaluation_id == evaluation_id)
        return self.db.scalars(statement).all()


class EvaluationEvidenceRepository(BaseRepository[EvaluationEvidence]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, EvaluationEvidence)

    def list_for_score(self, evaluation_score_id: UUID) -> Sequence[EvaluationEvidence]:
        statement = select(EvaluationEvidence).where(EvaluationEvidence.evaluation_score_id == evaluation_score_id)
        return self.db.scalars(statement).all()
