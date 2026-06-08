from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.modules.audit.service import AuditService
from app.modules.evaluations.repository import EvaluationRepository, EvaluationScoreRepository
from app.modules.reviews.models import CommitteeNote, ReviewerComment, ScoreOverride
from app.modules.reviews.repository import CommitteeNoteRepository, ReviewerCommentRepository, ScoreOverrideRepository
from app.modules.reviews.schemas import CommitteeNoteCreate, ReviewerCommentCreate, ScoreOverrideCreate


class ReviewService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.evaluations = EvaluationRepository(db)
        self.scores = EvaluationScoreRepository(db)
        self.comments = ReviewerCommentRepository(db)
        self.notes = CommitteeNoteRepository(db)
        self.overrides = ScoreOverrideRepository(db)
        self.audit = AuditService(db)

    def add_comment(
        self,
        evaluation_id: UUID,
        payload: ReviewerCommentCreate,
        *,
        actor_id: UUID | None,
    ) -> ReviewerComment:
        evaluation = self.evaluations.get(evaluation_id)
        if not evaluation:
            raise NotFoundError("Evaluation not found")
        comment = ReviewerComment(
            startup_id=evaluation.startup_id,
            evaluation_id=evaluation.id,
            reviewer_id=actor_id,
            comment=payload.comment,
        )
        self.comments.add(comment)
        self.audit.log(
            actor_id=actor_id,
            entity_type="reviewer_comment",
            entity_id=comment.id,
            action="reviewer_comment_created",
            details={"evaluation_id": str(evaluation_id)},
        )
        self.db.commit()
        self.db.refresh(comment)
        return comment

    def list_comments(self, evaluation_id: UUID) -> Sequence[ReviewerComment]:
        if not self.evaluations.get(evaluation_id):
            raise NotFoundError("Evaluation not found")
        return self.comments.list_for_evaluation(evaluation_id)

    def add_committee_note(
        self,
        evaluation_id: UUID,
        payload: CommitteeNoteCreate,
        *,
        actor_id: UUID | None,
    ) -> CommitteeNote:
        evaluation = self.evaluations.get(evaluation_id)
        if not evaluation:
            raise NotFoundError("Evaluation not found")
        note = CommitteeNote(
            startup_id=evaluation.startup_id,
            evaluation_id=evaluation.id,
            committee_member_id=actor_id,
            note=payload.note,
        )
        self.notes.add(note)
        self.audit.log(
            actor_id=actor_id,
            entity_type="committee_note",
            entity_id=note.id,
            action="committee_note_created",
            details={"evaluation_id": str(evaluation_id)},
        )
        self.db.commit()
        self.db.refresh(note)
        return note

    def list_committee_notes(self, evaluation_id: UUID) -> Sequence[CommitteeNote]:
        if not self.evaluations.get(evaluation_id):
            raise NotFoundError("Evaluation not found")
        return self.notes.list_for_evaluation(evaluation_id)

    def override_score(
        self,
        evaluation_score_id: UUID,
        payload: ScoreOverrideCreate,
        *,
        actor_id: UUID | None,
    ) -> ScoreOverride:
        score = self.scores.get(evaluation_score_id)
        if not score:
            raise NotFoundError("Evaluation score not found")
        original_score = self._selected_score(score)
        if original_score is None:
            raise ValidationError("Cannot override a score that has no existing score value")
        if payload.overridden_score > score.criterion.max_score:
            raise ValidationError(f"Overridden score cannot exceed {score.criterion.max_score}")
        override = ScoreOverride(
            evaluation_score_id=evaluation_score_id,
            original_score=original_score,
            overridden_score=payload.overridden_score,
            overridden_by=actor_id,
            reason=payload.reason,
        )
        score.reviewer_score = payload.overridden_score
        score.final_score = payload.overridden_score
        self.overrides.add(override)
        self.audit.log(
            actor_id=actor_id,
            entity_type="score_override",
            entity_id=override.id,
            action="score_override_created",
            reason=payload.reason,
            details={
                "evaluation_score_id": str(evaluation_score_id),
                "original_score": original_score,
                "overridden_score": payload.overridden_score,
            },
        )
        self.db.commit()
        self.db.refresh(override)
        return override

    def list_overrides(self, evaluation_score_id: UUID) -> Sequence[ScoreOverride]:
        if not self.scores.get(evaluation_score_id):
            raise NotFoundError("Evaluation score not found")
        return self.overrides.list_for_score(evaluation_score_id)

    @staticmethod
    def _selected_score(score) -> float | None:
        if score.final_score is not None:
            return score.final_score
        if score.reviewer_score is not None:
            return score.reviewer_score
        return score.ai_score
