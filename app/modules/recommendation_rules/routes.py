from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import AdminUser, ReadOnlyUser
from app.modules.recommendation_rules.models import RecommendationRule
from app.modules.recommendation_rules.schemas import (
    RecommendationRuleCreate,
    RecommendationRuleRead,
    RecommendationRuleUpdate,
)
from app.modules.recommendation_rules.service import RecommendationRuleService

router = APIRouter(prefix="/admin/recommendation-rules", tags=["Recommendation Rules"])


@router.post("", response_model=RecommendationRuleRead, status_code=status.HTTP_201_CREATED)
def create_recommendation_rule(
    payload: RecommendationRuleCreate,
    current_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    return RecommendationRuleService(db).create(payload, actor_id=current_user.id)


@router.post("/defaults", response_model=list[RecommendationRuleRead], status_code=status.HTTP_201_CREATED)
def seed_default_recommendation_rules(current_user: AdminUser, db: Annotated[Session, Depends(get_db)]):
    return RecommendationRuleService(db).seed_defaults(actor_id=current_user.id)


@router.get("", response_model=list[RecommendationRuleRead])
def list_recommendation_rules(
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> Sequence[RecommendationRule]:
    return RecommendationRuleService(db).list(skip=skip, limit=limit)


@router.patch("/{rule_id}", response_model=RecommendationRuleRead)
def update_recommendation_rule(
    rule_id: UUID,
    payload: RecommendationRuleUpdate,
    current_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    return RecommendationRuleService(db).update(rule_id, payload, actor_id=current_user.id)
