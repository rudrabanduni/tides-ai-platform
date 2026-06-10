from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import EvaluatorUser, ReadOnlyUser
from app.modules.company_profiles.repository import CompanyProfileRepository
from app.modules.documents.repository import DocumentRepository
from app.modules.founders.repository import FounderRepository
from app.modules.startup_profiles.agent import StartupProfileAgentService
from app.modules.startup_profiles.context import StartupProfileContextBuilder
from app.modules.startup_profiles.models import AIAssessmentRecord, StartupProfile, StartupProfileVersion
from app.modules.startup_profiles.repository import AIAssessmentRecordRepository
from app.modules.startup_profiles.schemas import (
    AIAssessmentRecordRead,
    StartupAssessmentResult,
    StartupProfilePayload,
    StartupProfileRead,
    StartupProfileVersionRead,
)
from app.modules.startup_profiles.service import StartupProfileService
from app.modules.startups.service import StartupService

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


@router.post("/{startup_id}/assess", response_model=StartupAssessmentResult, status_code=status.HTTP_200_OK)
def assess_startup(
    startup_id: UUID,
    current_user: EvaluatorUser,
    db: Annotated[Session, Depends(get_db)],
) -> StartupAssessmentResult:
    """Run a full AI-assisted startup assessment: profile + rule-based score + AI evaluation.

    The AI evaluation result is persisted to ``ai_assessment_records`` so it
    can be retrieved later via GET /{startup_id}/evaluations.
    """
    startup = StartupService(db).get(startup_id)

    founders = FounderRepository(db).list_for_startup(startup_id)
    company_profile = CompanyProfileRepository(db).get_by_startup(startup_id)
    documents = DocumentRepository(db).list_for_startup(startup_id)
    startup_profile = StartupProfileService(db).profiles.get_by_startup(startup_id)

    context = StartupProfileContextBuilder().build(
        startup=startup,
        founders=founders,
        profile=startup_profile,
        company_profile=company_profile,
        documents=documents,
    )

    agent = StartupProfileAgentService(db)
    result = agent.assess_startup(context)

    # Persist the AI evaluation result so it can be retrieved later.
    ai = result.ai_evaluation
    record = AIAssessmentRecord(
        startup_id=startup_id,
        executive_summary=ai.executive_summary,
        innovation_score=ai.innovation_score,
        market_score=ai.market_score,
        execution_score=ai.execution_score,
        overall_score=ai.overall_score,
        strengths=ai.strengths,
        weaknesses=ai.weaknesses,
        recommendations=ai.recommendations,
        assessed_by=current_user.id,
    )
    repo = AIAssessmentRecordRepository(db)
    repo.add(record)
    db.commit()

    return result


@router.get("/{startup_id}/evaluations", response_model=list[AIAssessmentRecordRead])
def list_startup_evaluations(
    startup_id: UUID,
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
) -> Sequence[AIAssessmentRecord]:
    """Return all persisted AI assessment records for a startup, newest first."""
    # Verify the startup exists before querying assessments.
    StartupService(db).get(startup_id)
    return AIAssessmentRecordRepository(db).list_for_startup(startup_id)
