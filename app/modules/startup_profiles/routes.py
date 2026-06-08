from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import EvaluatorUser, ReadOnlyUser
from app.modules.startup_profiles.models import StartupProfileVersion
from app.modules.startup_profiles.schemas import (
    StartupProfilePayload,
    StartupProfileRead,
    StartupProfileVersionRead,
)
from app.modules.startup_profiles.service import StartupProfileService

router = APIRouter(prefix="/startups", tags=["Startup Profiles"])


@router.put("/{startup_id}/profile", response_model=StartupProfileRead, status_code=status.HTTP_200_OK)
def upsert_startup_profile(
    startup_id: UUID,
    payload: StartupProfilePayload,
    current_user: EvaluatorUser,
    db: Annotated[Session, Depends(get_db)],
):
    return StartupProfileService(db).upsert(startup_id, payload, actor_id=current_user.id)


@router.get("/{startup_id}/profile", response_model=StartupProfileRead)
def get_startup_profile(startup_id: UUID, current_user: ReadOnlyUser, db: Annotated[Session, Depends(get_db)]):
    return StartupProfileService(db).get_by_startup(startup_id)


@router.get("/{startup_id}/profile/versions", response_model=list[StartupProfileVersionRead])
def get_startup_profile_versions(
    startup_id: UUID,
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
) -> Sequence[StartupProfileVersion]:
    return StartupProfileService(db).versions_for_startup(startup_id)
