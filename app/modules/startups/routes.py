from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import AdminUser, EvaluatorUser, ReadOnlyUser
from app.modules.startups.models import StartupApplication, StartupStatusHistory
from app.modules.startups.schemas import (
    StartupCreate,
    StartupRead,
    StartupStatusHistoryRead,
    StartupStatusUpdate,
    StartupUpdate,
    BulkStatusUpdate,
    BulkDelete,
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


@router.post("/bulk-status", status_code=status.HTTP_200_OK)
def bulk_update_startup_status(
    payload: BulkStatusUpdate,
    current_user: EvaluatorUser,
    db: Annotated[Session, Depends(get_db)],
):
    service = StartupService(db)
    for startup_id in payload.startup_ids:
        service.change_status(
            startup_id,
            new_status=payload.new_status,
            reason=payload.reason,
            actor_id=current_user.id,
        )
    return {"status": "success", "count": len(payload.startup_ids)}


@router.delete("/{startup_id}", status_code=status.HTTP_200_OK)
def delete_startup(
    startup_id: UUID,
    current_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    StartupService(db).delete(startup_id, actor_id=current_user.id)
    return {"success": True, "message": "Startup deleted successfully"}


@router.post("/bulk-delete", status_code=status.HTTP_200_OK)
def bulk_delete_startups(
    payload: BulkDelete,
    current_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    service = StartupService(db)
    for startup_id in payload.startup_ids:
        service.delete(startup_id, actor_id=current_user.id)
    return {"success": True, "message": "Startups deleted successfully"}
