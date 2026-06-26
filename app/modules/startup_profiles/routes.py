"""Routes for startup profiles, assessment, bulk assessment, rankings, and PDF reports."""
from __future__ import annotations

import io
from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.core.enums import RecommendationStatus
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
    BulkAssessRequest,
    BulkAssessResult,
    StartupAssessmentResult,
    StartupProfilePayload,
    StartupProfileRead,
    StartupProfileVersionRead,
    StartupRankEntry,
)
from app.modules.startup_profiles.service import StartupProfileService
from app.modules.startups.service import StartupService
from app.services.report.pdf import generate_assessment_pdf

router = APIRouter(prefix="/startups", tags=["Startup Profiles"])


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _derive_recommendation_status(overall_score: int) -> str:
    """Map overall_score to a RecommendationStatus value.

    Rules:
        overall_score >= 80  -> recommended
        overall_score >= 60  -> review
        overall_score < 60   -> rejected
    """
    if overall_score >= 80:
        return RecommendationStatus.RECOMMENDED.value
    if overall_score >= 60:
        return RecommendationStatus.REVIEW.value
    return RecommendationStatus.REJECTED.value


def _run_single_assessment(
    startup_id: UUID,
    actor_id: UUID,
    db: Session,
) -> AIAssessmentRecord:
    """Load a startup, run AI assessment, persist and return the record.

    Raises any exception on failure — callers decide whether to abort or
    continue (e.g. bulk-assess catches and records the error).
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

    ai = result.ai_evaluation
    rec_status = _derive_recommendation_status(ai.overall_score)

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
        recommendation_status=rec_status,
        assessed_by=actor_id,
    )
    repo = AIAssessmentRecordRepository(db)
    repo.add(record)
    db.commit()
    return record


# ---------------------------------------------------------------------------
# Profile endpoints
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Bulk assess  —  MUST be registered before /{startup_id}/... routes
# ---------------------------------------------------------------------------

@router.post("/bulk-assess", response_model=BulkAssessResult, status_code=status.HTTP_200_OK)
def bulk_assess_startups(
    payload: BulkAssessRequest,
    current_user: EvaluatorUser,
    db: Annotated[Session, Depends(get_db)],
) -> BulkAssessResult:
    """Assess multiple startups in a single request.

    Processing continues even if individual startups fail. The response
    summarises how many were processed, succeeded, and failed.
    """
    successful = 0
    errors: list[dict] = []

    for startup_id in payload.startup_ids:
        try:
            _run_single_assessment(startup_id, current_user.id, db)
            successful += 1
        except Exception as exc:  # noqa: BLE001
            errors.append({"startup_id": str(startup_id), "error": str(exc)})

    return BulkAssessResult(
        processed=len(payload.startup_ids),
        successful=successful,
        failed=len(errors),
        errors=errors,
    )


# ---------------------------------------------------------------------------
# Rankings
# ---------------------------------------------------------------------------

@router.get("/rankings", response_model=list[StartupRankEntry])
def get_startup_rankings(
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=100, ge=1, le=500),
) -> list[StartupRankEntry]:
    """Return startups ranked by their latest assessment score (descending)."""
    rows = AIAssessmentRecordRepository(db).ranked_startups(limit=limit)
    return [
        StartupRankEntry(
            rank=idx + 1,
            startup_id=row["startup_id"],
            startup_name=row["startup_name"],
            overall_score=row["overall_score"],
            recommendation_status=row["recommendation_status"],
        )
        for idx, row in enumerate(rows)
    ]


@router.get("/top", response_model=list[StartupRankEntry])
def get_top_startups(
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
    limit: int = Query(default=10, ge=1, le=100),
) -> list[StartupRankEntry]:
    """Return the top-N startups ranked by latest overall_score."""
    rows = AIAssessmentRecordRepository(db).ranked_startups(limit=limit)
    return [
        StartupRankEntry(
            rank=idx + 1,
            startup_id=row["startup_id"],
            startup_name=row["startup_name"],
            overall_score=row["overall_score"],
            recommendation_status=row["recommendation_status"],
        )
        for idx, row in enumerate(rows)
    ]


# ---------------------------------------------------------------------------
# Single assess
# ---------------------------------------------------------------------------

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
    rec_status = _derive_recommendation_status(ai.overall_score)

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
        recommendation_status=rec_status,
        assessed_by=current_user.id,
    )
    repo = AIAssessmentRecordRepository(db)
    repo.add(record)
    db.commit()

    return result


# ---------------------------------------------------------------------------
# Evaluation history
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# PDF report
# ---------------------------------------------------------------------------

@router.get("/{startup_id}/report", response_class=StreamingResponse)
def download_assessment_report(
    startup_id: UUID,
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
) -> StreamingResponse:
    """Download the latest AI assessment for a startup as a PDF report.

    Returns 404 if the startup does not exist or has no assessments yet.
    """
    startup = StartupService(db).get(startup_id)

    records = AIAssessmentRecordRepository(db).list_for_startup(startup_id)
    if not records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No assessment found for this startup. Run POST /assess first.",
        )

    latest = records[0]
    record_schema = AIAssessmentRecordRead.model_validate(latest)

    pdf_bytes = generate_assessment_pdf(
        startup_name=startup.startup_name,
        record=record_schema,
    )

    filename = f"assessment_{startup_id}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
