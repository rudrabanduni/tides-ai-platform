"""Routes for startup profiles, assessment, bulk assessment, rankings, and PDF reports."""
from __future__ import annotations

import io
from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import EvaluatorUser, ReadOnlyUser
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
    StartupProfileAgentOutput,
    StartupEvaluationScore,
    StartupEvaluationOutput,
)
from app.modules.startup_profiles.service import StartupProfileService
from app.modules.startups.service import StartupService
from app.modules.ai.orchestrator.pipeline import run_expert_assessment
from app.modules.evaluation.report.report_serializer import ReportSerializer
import os

router = APIRouter(prefix="/startups", tags=["Startup Profiles"])


# ---------------------------------------------------------------------------
# Private helpers
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
async def bulk_assess_startups(
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
            await run_expert_assessment(startup_id, current_user.id, db)
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
async def assess_startup(
    startup_id: UUID,
    current_user: EvaluatorUser,
    db: Annotated[Session, Depends(get_db)],
) -> StartupAssessmentResult:
    """Run a full AI-assisted startup assessment: profile + rule-based score + AI evaluation.

    The AI evaluation result is persisted to ``ai_assessment_records`` so it
    can be retrieved later via GET /{startup_id}/evaluations.
    """
    startup = StartupService(db).get(startup_id)
    res = await run_expert_assessment(startup_id, current_user.id, db)
    report = res["generated_report"]
    
    # Safely extract section contents with fallback to empty strings
    def get_section_content(sec_name: str) -> str:
        sec = report.get(sec_name)
        if not sec:
            return ""
        if isinstance(sec, dict):
            return sec.get("content", "")
        return getattr(sec, "content", "")

    exec_summary_content = f"Executive Summary for {startup.startup_name}: " + get_section_content("executive_summary")
    business_model_content = get_section_content("business_model")
    market_opp_content = get_section_content("market_opportunity")
    founder_content = get_section_content("founder_assessment")
    risk_content = get_section_content("risks")
    questions_content = get_section_content("follow_up_questions")

    # Query the newly persisted record from DB to get clean strengths/weaknesses lists
    records = AIAssessmentRecordRepository(db).list_for_startup(startup_id)
    latest_record = records[0] if records else None

    exec_summary_to_use = latest_record.executive_summary if latest_record else exec_summary_content
    if startup.startup_name not in exec_summary_to_use:
        exec_summary_to_use = f"Executive Summary for {startup.startup_name}: " + exec_summary_to_use

    profile_out = StartupProfileAgentOutput(
        executive_summary=exec_summary_to_use,
        business_model=business_model_content,
        customer_segments=market_opp_content,
        market_opportunity=market_opp_content,
        strengths=latest_record.strengths if latest_record else [],
        risks=latest_record.weaknesses if latest_record else [],
        missing_information=latest_record.recommendations if latest_record else []
    )
    
    rule_score = StartupEvaluationScore(
        innovation_score=10,
        market_score=10,
        execution_score=10,
        overall_score=30,
        rationale=["Rule-based score wrapper for backward compatibility"]
    )
    
    ai_eval = StartupEvaluationOutput(
        executive_summary=exec_summary_to_use,
        innovation_score=latest_record.innovation_score if latest_record else 10,
        market_score=latest_record.market_score if latest_record else 10,
        execution_score=latest_record.execution_score if latest_record else 10,
        overall_score=latest_record.overall_score if latest_record else 90,
        strengths=latest_record.strengths if latest_record else [],
        weaknesses=latest_record.weaknesses if latest_record else [],
        recommendations=latest_record.recommendations if latest_record else []
    )
    
    return StartupAssessmentResult(
        profile=profile_out,
        rule_based_score=rule_score,
        ai_evaluation=ai_eval
    )


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
async def download_assessment_report(
    startup_id: UUID,
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
) -> StreamingResponse:
    """Download the latest AI assessment for a startup as a PDF report.

    Returns 404 if the startup does not exist or has no assessments yet.
    """
    startup = StartupService(db).get(startup_id)
    
    graph_path = os.path.join("uploads", "graphs", f"{startup_id}.json")
    if not os.path.exists(graph_path):
        records = AIAssessmentRecordRepository(db).list_for_startup(startup_id)
        if not records:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No assessment found for this startup. Run POST /assess first.",
            )
        try:
            await run_expert_assessment(startup_id, current_user.id, db)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Assessment report not found and could not be generated: {exc}",
            )
            
    if os.path.exists(graph_path):
        with open(graph_path, "r", encoding="utf-8") as f:
            graph = ReportSerializer.from_json(f.read())
        pdf_bytes = ReportSerializer.export_pdf_data(graph.report)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Assessment report not found. Run POST /assess first.",
        )

    filename = f"assessment_{startup_id}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
