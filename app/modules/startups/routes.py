from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import EvaluatorUser, ReadOnlyUser
from app.modules.startups.models import StartupApplication, StartupStatusHistory
from app.modules.startups.schemas import (
    StartupCreate,
    StartupRead,
    StartupStatusHistoryRead,
    StartupStatusUpdate,
    StartupUpdate,
)
from app.modules.startups.service import StartupService

router = APIRouter(prefix="/startups", tags=["Startups"])


@router.post("", response_model=StartupRead, status_code=status.HTTP_201_CREATED)
def create_startup(payload: StartupCreate, current_user: EvaluatorUser, db: Annotated[Session, Depends(get_db)]):
    return StartupService(db).create(payload, actor_id=current_user.id)


@router.get("", response_model=list[StartupRead])
def list_startups(
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> Sequence[StartupApplication]:
    return StartupService(db).list(skip=skip, limit=limit)


@router.get("/{startup_id}", response_model=StartupRead)
def get_startup(startup_id: UUID, current_user: ReadOnlyUser, db: Annotated[Session, Depends(get_db)]):
    return StartupService(db).get(startup_id)


@router.patch("/{startup_id}", response_model=StartupRead)
def update_startup(
    startup_id: UUID,
    payload: StartupUpdate,
    current_user: EvaluatorUser,
    db: Annotated[Session, Depends(get_db)],
):
    return StartupService(db).update(startup_id, payload, actor_id=current_user.id)


@router.post("/{startup_id}/submit", response_model=StartupRead)
def submit_startup(startup_id: UUID, current_user: EvaluatorUser, db: Annotated[Session, Depends(get_db)]):
    return StartupService(db).submit(startup_id, actor_id=current_user.id)


@router.patch("/{startup_id}/status", response_model=StartupRead)
def update_startup_status(
    startup_id: UUID,
    payload: StartupStatusUpdate,
    current_user: EvaluatorUser,
    db: Annotated[Session, Depends(get_db)],
):
    return StartupService(db).change_status(
        startup_id,
        new_status=payload.new_status,
        reason=payload.reason,
        actor_id=current_user.id,
    )


@router.get("/{startup_id}/status-history", response_model=list[StartupStatusHistoryRead])
def get_status_history(
    startup_id: UUID,
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
) -> Sequence[StartupStatusHistory]:
    return StartupService(db).status_history(startup_id)
