from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.reviews.models import CommitteeNote, ReviewerComment, ScoreOverride
from app.repositories.base import BaseRepository


class ReviewerCommentRepository(BaseRepository[ReviewerComment]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ReviewerComment)

    def list_for_evaluation(self, evaluation_id: UUID) -> Sequence[ReviewerComment]:
        statement = (
            select(ReviewerComment)
            .where(ReviewerComment.evaluation_id == evaluation_id)
            .order_by(ReviewerComment.created_at.desc())
        )
        return self.db.scalars(statement).all()


class CommitteeNoteRepository(BaseRepository[CommitteeNote]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, CommitteeNote)

    def list_for_evaluation(self, evaluation_id: UUID) -> Sequence[CommitteeNote]:
        statement = (
            select(CommitteeNote)
            .where(CommitteeNote.evaluation_id == evaluation_id)
            .order_by(CommitteeNote.created_at.desc())
        )
        return self.db.scalars(statement).all()


class ScoreOverrideRepository(BaseRepository[ScoreOverride]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ScoreOverride)

    def list_for_score(self, evaluation_score_id: UUID) -> Sequence[ScoreOverride]:
        statement = (
            select(ScoreOverride)
            .where(ScoreOverride.evaluation_score_id == evaluation_score_id)
            .order_by(ScoreOverride.created_at.desc())
        )
        return self.db.scalars(statement).all()
