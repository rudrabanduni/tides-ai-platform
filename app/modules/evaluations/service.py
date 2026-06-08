from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.enums import EvaluationStatus
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.db.mixins import utcnow
from app.modules.audit.service import AuditService
from app.modules.documents.service import DocumentService
from app.modules.evaluations.models import (
    Evaluation,
    EvaluationCriterion,
    EvaluationEvidence,
    EvaluationRubric,
    EvaluationScore,
)
from app.modules.evaluations.repository import (
    EvaluationCriterionRepository,
    EvaluationEvidenceRepository,
    EvaluationRepository,
    EvaluationRubricRepository,
    EvaluationScoreRepository,
)
from app.modules.evaluations.schemas import (
    EvaluationCreate,
    EvaluationCriterionCreate,
    EvaluationCriterionUpdate,
    EvaluationEvidenceCreate,
    EvaluationRubricCreate,
    EvaluationRubricUpdate,
    EvaluationScoreCreate,
)
from app.modules.recommendation_rules.service import RecommendationRuleService
from app.modules.startup_profiles.service import StartupProfileService
from app.modules.startups.service import StartupService


class EvaluationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.rubrics = EvaluationRubricRepository(db)
        self.criteria = EvaluationCriterionRepository(db)
        self.evaluations = EvaluationRepository(db)
        self.scores = EvaluationScoreRepository(db)
        self.evidence = EvaluationEvidenceRepository(db)
        self.audit = AuditService(db)
        self.startups = StartupService(db)
        self.profiles = StartupProfileService(db)
        self.documents = DocumentService(db)
        self.recommendations = RecommendationRuleService(db)

    def create_rubric(self, payload: EvaluationRubricCreate, *, actor_id: UUID | None) -> EvaluationRubric:
        rubric = EvaluationRubric(**payload.model_dump())
        self.rubrics.add(rubric)
        self.audit.log(
            actor_id=actor_id,
            entity_type="evaluation_rubric",
            entity_id=rubric.id,
            action="evaluation_rubric_created",
        )
        self.db.commit()
        self.db.refresh(rubric)
        return rubric

    def list_rubrics(self, *, skip: int = 0, limit: int = 100) -> Sequence[EvaluationRubric]:
        return self.rubrics.list(skip=skip, limit=limit)

    def get_rubric(self, rubric_id: UUID) -> EvaluationRubric:
        rubric = self.rubrics.get(rubric_id)
        if not rubric:
            raise NotFoundError("Evaluation rubric not found")
        return rubric

    def update_rubric(
        self,
        rubric_id: UUID,
        payload: EvaluationRubricUpdate,
        *,
        actor_id: UUID | None,
    ) -> EvaluationRubric:
        rubric = self.get_rubric(rubric_id)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(rubric, field, value)
        self.audit.log(
            actor_id=actor_id,
            entity_type="evaluation_rubric",
            entity_id=rubric.id,
            action="evaluation_rubric_updated",
            details=data,
        )
        self.db.commit()
        self.db.refresh(rubric)
        return rubric

    def create_criterion(
        self,
        rubric_id: UUID,
        payload: EvaluationCriterionCreate,
        *,
        actor_id: UUID | None,
    ) -> EvaluationCriterion:
        self.get_rubric(rubric_id)
        criterion = EvaluationCriterion(rubric_id=rubric_id, **payload.model_dump())
        self.criteria.add(criterion)
        self.audit.log(
            actor_id=actor_id,
            entity_type="evaluation_criterion",
            entity_id=criterion.id,
            action="evaluation_criterion_created",
            details={"rubric_id": str(rubric_id)},
        )
        self.db.commit()
        self.db.refresh(criterion)
        return criterion

    def list_criteria(self, rubric_id: UUID) -> Sequence[EvaluationCriterion]:
        self.get_rubric(rubric_id)
        return self.criteria.list_for_rubric(rubric_id)

    def update_criterion(
        self,
        criterion_id: UUID,
        payload: EvaluationCriterionUpdate,
        *,
        actor_id: UUID | None,
    ) -> EvaluationCriterion:
        criterion = self.criteria.get(criterion_id)
        if not criterion:
            raise NotFoundError("Evaluation criterion not found")
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(criterion, field, value)
        self.audit.log(
            actor_id=actor_id,
            entity_type="evaluation_criterion",
            entity_id=criterion.id,
            action="evaluation_criterion_updated",
            details=data,
        )
        self.db.commit()
        self.db.refresh(criterion)
        return criterion

    def create_evaluation(
        self,
        startup_id: UUID,
        payload: EvaluationCreate,
        *,
        actor_id: UUID | None,
    ) -> Evaluation:
        self.startups.get(startup_id)
        self.get_rubric(payload.rubric_id)
        profile_version = self.profiles.latest_version_for_startup(startup_id)
        evaluation = Evaluation(
            startup_id=startup_id,
            rubric_id=payload.rubric_id,
            startup_profile_version_id=profile_version.id if profile_version else None,
            status=EvaluationStatus.CREATED,
        )
        self.evaluations.add(evaluation)
        self.audit.log(
            actor_id=actor_id,
            entity_type="evaluation",
            entity_id=evaluation.id,
            action="evaluation_created",
            details={
                "startup_id": str(startup_id),
                "rubric_id": str(payload.rubric_id),
                "startup_profile_version_id": str(profile_version.id) if profile_version else None,
            },
        )
        self.db.commit()
        self.db.refresh(evaluation)
        return evaluation

    def get_evaluation(self, evaluation_id: UUID) -> Evaluation:
        evaluation = self.evaluations.get(evaluation_id)
        if not evaluation:
            raise NotFoundError("Evaluation not found")
        return evaluation

    def list_evaluations_for_startup(self, startup_id: UUID) -> Sequence[Evaluation]:
        self.startups.get(startup_id)
        return self.evaluations.list_for_startup(startup_id)

    def add_score(
        self,
        evaluation_id: UUID,
        payload: EvaluationScoreCreate,
        *,
        actor_id: UUID | None,
    ) -> EvaluationScore:
        evaluation = self.get_evaluation(evaluation_id)
        criterion = self.criteria.get(payload.criteria_id)
        if not criterion:
            raise NotFoundError("Evaluation criterion not found")
        if criterion.rubric_id != evaluation.rubric_id:
            raise ValidationError("Criterion does not belong to the evaluation rubric")
        if self.scores.get_for_evaluation_criterion(evaluation_id, payload.criteria_id):
            raise ConflictError("Score already exists for this criterion")
        for score_value in (payload.ai_score, payload.reviewer_score, payload.final_score):
            if score_value is not None and score_value > criterion.max_score:
                raise ValidationError(f"Score cannot exceed criterion max_score of {criterion.max_score}")
        score = EvaluationScore(evaluation_id=evaluation_id, **payload.model_dump())
        self.scores.add(score)
        self.audit.log(
            actor_id=actor_id,
            entity_type="evaluation_score",
            entity_id=score.id,
            action="evaluation_score_created",
            details={"evaluation_id": str(evaluation_id), "criteria_id": str(payload.criteria_id)},
        )
        self.db.commit()
        self.db.refresh(score)
        return score

    def list_scores(self, evaluation_id: UUID) -> Sequence[EvaluationScore]:
        self.get_evaluation(evaluation_id)
        return self.scores.list_for_evaluation(evaluation_id)

    def add_evidence(
        self,
        evaluation_score_id: UUID,
        payload: EvaluationEvidenceCreate,
        *,
        actor_id: UUID | None,
    ) -> EvaluationEvidence:
        score = self.scores.get(evaluation_score_id)
        if not score:
            raise NotFoundError("Evaluation score not found")
        evaluation = self.get_evaluation(score.evaluation_id)
        source = self.documents.get_source(payload.source_id)
        if source.startup_id != evaluation.startup_id:
            raise ValidationError("Evidence source must belong to the evaluated startup")
        if source.source_type != payload.source_type:
            raise ValidationError("Evidence source_type does not match the registered document source")
        evidence = EvaluationEvidence(evaluation_score_id=evaluation_score_id, **payload.model_dump())
        self.evidence.add(evidence)
        self.audit.log(
            actor_id=actor_id,
            entity_type="evaluation_evidence",
            entity_id=evidence.id,
            action="evaluation_evidence_created",
            details={"evaluation_score_id": str(evaluation_score_id), "source_id": str(payload.source_id)},
        )
        self.db.commit()
        self.db.refresh(evidence)
        return evidence

    def list_evidence(self, evaluation_score_id: UUID) -> Sequence[EvaluationEvidence]:
        score = self.scores.get(evaluation_score_id)
        if not score:
            raise NotFoundError("Evaluation score not found")
        return self.evidence.list_for_score(evaluation_score_id)

    def finalize(self, evaluation_id: UUID, *, actor_id: UUID | None) -> tuple[Evaluation, str | None]:
        evaluation = self.get_evaluation(evaluation_id)
        scores = self.scores.list_for_evaluation(evaluation_id)
        if not scores:
            raise ValidationError("Evaluation cannot be finalized without scores")

        total_weight = 0.0
        weighted_score = 0.0
        confidence_values: list[float] = []
        for score in scores:
            criterion = score.criterion
            selected_score = self._selected_score(score)
            if selected_score is None:
                raise ValidationError("Every evaluation score must have a score value before finalization")
            if score.ai_score is not None and len(score.evidence) == 0:
                raise ValidationError("AI-generated scores require cited evidence before finalization")
            if selected_score > criterion.max_score:
                raise ValidationError(f"Score cannot exceed criterion max_score of {criterion.max_score}")
            total_weight += criterion.weight
            weighted_score += (selected_score / criterion.max_score) * criterion.weight
            if score.confidence is not None:
                confidence_values.append(score.confidence)

        if total_weight <= 0:
            raise ValidationError("Total rubric weight must be greater than zero")

        overall_score = round((weighted_score / total_weight) * 100, 2)
        rule = self.recommendations.find_for_score(overall_score)
        evaluation.overall_score = overall_score
        evaluation.recommendation = rule.recommendation if rule else None
        evaluation.recommendation_rule_id = rule.id if rule else None
        evaluation.confidence = (
            round(sum(confidence_values) / len(confidence_values), 4) if confidence_values else None
        )
        evaluation.status = EvaluationStatus.FINALIZED
        evaluation.completed_at = utcnow()
        self.audit.log(
            actor_id=actor_id,
            entity_type="evaluation",
            entity_id=evaluation.id,
            action="evaluation_finalized",
            details={
                "overall_score": evaluation.overall_score,
                "recommendation": evaluation.recommendation,
                "recommendation_rule_id": str(rule.id) if rule else None,
            },
        )
        self.db.commit()
        self.db.refresh(evaluation)
        return evaluation, rule.rule_name if rule else None

    @staticmethod
    def _selected_score(score: EvaluationScore) -> float | None:
        if score.final_score is not None:
            return score.final_score
        if score.reviewer_score is not None:
            return score.reviewer_score
        return score.ai_score
