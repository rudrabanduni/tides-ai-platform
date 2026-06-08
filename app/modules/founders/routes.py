from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import EvaluatorUser, ReadOnlyUser
from app.modules.founders.models import Founder
from app.modules.founders.schemas import FounderCreate, FounderRead, FounderUpdate
from app.modules.founders.service import FounderService

router = APIRouter(tags=["Founders"])


@router.post("/startups/{startup_id}/founders", response_model=FounderRead, status_code=status.HTTP_201_CREATED)
def create_founder(
    startup_id: UUID,
    payload: FounderCreate,
    current_user: EvaluatorUser,
    db: Annotated[Session, Depends(get_db)],
):
    return FounderService(db).create(startup_id, payload, actor_id=current_user.id)


@router.get("/startups/{startup_id}/founders", response_model=list[FounderRead])
def list_founders(
    startup_id: UUID,
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
) -> Sequence[Founder]:
    return FounderService(db).list_for_startup(startup_id)


@router.get("/founders/{founder_id}", response_model=FounderRead)
def get_founder(founder_id: UUID, current_user: ReadOnlyUser, db: Annotated[Session, Depends(get_db)]):
    return FounderService(db).get(founder_id)


@router.patch("/founders/{founder_id}", response_model=FounderRead)
def update_founder(
    founder_id: UUID,
    payload: FounderUpdate,
    current_user: EvaluatorUser,
    db: Annotated[Session, Depends(get_db)],
):
    return FounderService(db).update(founder_id, payload, actor_id=current_user.id)
