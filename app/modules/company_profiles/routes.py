from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import EvaluatorUser, ReadOnlyUser
from app.modules.company_profiles.schemas import CompanyProfilePayload, CompanyProfileRead
from app.modules.company_profiles.service import CompanyProfileService

router = APIRouter(prefix="/startups", tags=["Company Profiles"])


@router.put("/{startup_id}/company-profile", response_model=CompanyProfileRead, status_code=status.HTTP_200_OK)
def upsert_company_profile(
    startup_id: UUID,
    payload: CompanyProfilePayload,
    current_user: EvaluatorUser,
    db: Annotated[Session, Depends(get_db)],
):
    return CompanyProfileService(db).upsert(startup_id, payload, actor_id=current_user.id)


@router.get("/{startup_id}/company-profile", response_model=CompanyProfileRead)
def get_company_profile(startup_id: UUID, current_user: ReadOnlyUser, db: Annotated[Session, Depends(get_db)]):
    return CompanyProfileService(db).get_by_startup(startup_id)
