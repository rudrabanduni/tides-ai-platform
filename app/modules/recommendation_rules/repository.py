from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.recommendation_rules.models import RecommendationRule
from app.repositories.base import BaseRepository


class RecommendationRuleRepository(BaseRepository[RecommendationRule]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, RecommendationRule)

    def list_active(self) -> Sequence[RecommendationRule]:
        statement = (
            select(RecommendationRule)
            .where(RecommendationRule.active.is_(True))
            .order_by(RecommendationRule.min_score.desc())
        )
        return self.db.scalars(statement).all()

    def find_for_score(self, score: float) -> RecommendationRule | None:
        statement = select(RecommendationRule).where(
            RecommendationRule.active.is_(True),
            RecommendationRule.min_score <= score,
            RecommendationRule.max_score >= score,
        )
        return self.db.scalar(statement)
