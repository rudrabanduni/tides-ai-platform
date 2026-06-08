from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.modules.audit.service import AuditService
from app.modules.recommendation_rules.models import RecommendationRule
from app.modules.recommendation_rules.repository import RecommendationRuleRepository
from app.modules.recommendation_rules.schemas import RecommendationRuleCreate, RecommendationRuleUpdate


class RecommendationRuleService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.rules = RecommendationRuleRepository(db)
        self.audit = AuditService(db)

    def create(self, payload: RecommendationRuleCreate, *, actor_id: UUID | None) -> RecommendationRule:
        rule = RecommendationRule(**payload.model_dump())
        self.rules.add(rule)
        self.audit.log(
            actor_id=actor_id,
            entity_type="recommendation_rule",
            entity_id=rule.id,
            action="recommendation_rule_created",
        )
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def get(self, rule_id: UUID) -> RecommendationRule:
        rule = self.rules.get(rule_id)
        if not rule:
            raise NotFoundError("Recommendation rule not found")
        return rule

    def list(self, *, skip: int = 0, limit: int = 100) -> Sequence[RecommendationRule]:
        return self.rules.list(skip=skip, limit=limit)

    def update(
        self,
        rule_id: UUID,
        payload: RecommendationRuleUpdate,
        *,
        actor_id: UUID | None,
    ) -> RecommendationRule:
        rule = self.get(rule_id)
        data = payload.model_dump(exclude_unset=True)
        min_score = data.get("min_score", rule.min_score)
        max_score = data.get("max_score", rule.max_score)
        if min_score > max_score:
            raise ValidationError("min_score must be less than or equal to max_score")
        for field, value in data.items():
            setattr(rule, field, value)
        self.audit.log(
            actor_id=actor_id,
            entity_type="recommendation_rule",
            entity_id=rule.id,
            action="recommendation_rule_updated",
            details=data,
        )
        self.db.commit()
        self.db.refresh(rule)
        return rule

    def find_for_score(self, score: float) -> RecommendationRule | None:
        return self.rules.find_for_score(score)

    def seed_defaults(self, *, actor_id: UUID | None) -> Sequence[RecommendationRule]:
        defaults = [
            RecommendationRuleCreate(
                rule_name="Recommended",
                min_score=80,
                max_score=100,
                recommendation="Recommended",
            ),
            RecommendationRuleCreate(
                rule_name="Committee Review",
                min_score=65,
                max_score=79.99,
                recommendation="Committee Review",
            ),
            RecommendationRuleCreate(
                rule_name="Conditionally Recommended",
                min_score=50,
                max_score=64.99,
                recommendation="Conditionally Recommended",
            ),
            RecommendationRuleCreate(
                rule_name="Not Recommended",
                min_score=0,
                max_score=49.99,
                recommendation="Not Recommended",
            ),
        ]
        existing = {(rule.min_score, rule.max_score, rule.recommendation) for rule in self.rules.list_active()}
        created: list[RecommendationRule] = []
        for payload in defaults:
            key = (payload.min_score, payload.max_score, payload.recommendation)
            if key in existing:
                continue
            rule = RecommendationRule(**payload.model_dump())
            self.rules.add(rule)
            created.append(rule)
        if created:
            self.audit.log(
                actor_id=actor_id,
                entity_type="recommendation_rule",
                entity_id="defaults",
                action="recommendation_rules_seeded",
                details={"created": len(created)},
            )
            self.db.commit()
            for rule in created:
                self.db.refresh(rule)
        return created
