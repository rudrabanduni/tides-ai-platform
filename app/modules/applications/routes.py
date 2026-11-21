"""REST API for the incubation application workflow.

POST   /applications                         submit the intake form (Idempotency-Key supported)
GET    /applications                         list applications
GET    /applications/{id}                    application details (+ founders, documents, latest run)
POST   /applications/{id}/documents          upload a supporting document (validated)
POST   /applications/{id}/evaluations        start (or return the active/completed) evaluation run
GET    /applications/{id}/evaluations        all runs for the application
GET    /evaluation-runs/{run_id}             live progress, read from the database
GET    /evaluation-runs/{run_id}/results     six domains, 87-criterion coverage, supervisory synthesis
GET    /evaluation-runs/{run_id}/evidence    evidence records behind an assessment (startup-scoped)
GET    /evaluation-runs/{run_id}/report.pdf  validated due-diligence PDF
GET    /applications-dashboard               dashboard statistics from real records
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.enums import DocumentType
from app.core.exceptions import ValidationError
from app.db.session import get_db
from app.modules.applications.models import ApplicationSubmission, EvaluationRun
from app.modules.applications.results import build_run_results, evidence_records
from app.modules.applications.runner import MOCK_DISCLOSURE, start_evaluation_run
from app.modules.applications.schemas import (
    ApplicationCreate,
    ApplicationListItem,
    ApplicationRead,
    DocumentSummary,
    EvaluationRunRead,
    FounderRead,
)
from app.modules.applications.service import ApplicationService
from app.modules.auth.dependencies import EvaluatorUser, ReadOnlyUser
from app.modules.documents.service import DocumentService
from app.modules.startups.models import StartupApplication

router = APIRouter(tags=["Applications"])

DbSession = Annotated[Session, Depends(get_db)]


def _run_read(run: EvaluationRun | None) -> EvaluationRunRead | None:
    if run is None:
        return None
    data = EvaluationRunRead.model_validate(run)
    data.disclosure = MOCK_DISCLOSURE if run.mode == "MOCK_DEMONSTRATION" else None
    return data


def _app_read(db: Session, sub: ApplicationSubmission) -> ApplicationRead:
    svc = ApplicationService(db)
    st: StartupApplication = db.get(StartupApplication, sub.startup_id)
    return ApplicationRead(
        id=sub.id,
        application_ref=sub.application_ref,
        startup_id=sub.startup_id,
        company_name=st.startup_name,
        sector=st.sector,
        industry=sub.industry,
        stage=st.stage,
        location=sub.location,
        website=sub.website,
        status=getattr(st.current_status, "value", str(st.current_status)),
        contact_name=sub.contact_name,
        contact_email=sub.contact_email,
        contact_phone=sub.contact_phone,
        problem_statement=st.problem_statement,
        proposed_solution=st.solution_summary,
        product_technology=sub.product_technology,
        target_market=st.target_market,
        business_model=st.business_model,
        traction=st.traction_summary,
        revenue_information=sub.revenue_information,
        financial_information=sub.financial_information,
        funding_requirement=sub.funding_requirement,
        incubation_support_requirement=sub.incubation_support_requirement,
        declarations=sub.declarations or {},
        is_synthetic=sub.is_synthetic,
        submitted_at=sub.submitted_at,
        created_at=sub.created_at,
        founders=[FounderRead.model_validate(f) for f in svc.founders_for(sub.startup_id)],
        documents=[
            DocumentSummary(
                id=d.id,
                document_type=getattr(d.document_type, "value", str(d.document_type)),
                original_filename=d.original_filename,
                content_type=d.content_type,
                file_size=d.file_size,
                processing_status=getattr(d.processing_status, "value", str(d.processing_status)),
                created_at=d.created_at,
            )
            for d in svc.documents_for(sub.startup_id)
        ],
        latest_run=_run_read(svc.latest_run(sub.startup_id)),
    )


@router.post("/applications", response_model=ApplicationRead, status_code=status.HTTP_201_CREATED)
def submit_application(
    payload: ApplicationCreate,
    current_user: EvaluatorUser,
    db: DbSession,
    response: Response,
    idempotency_key: Annotated[str | None, Header(alias="Idempotency-Key")] = None,
) -> ApplicationRead:
    sub, created = ApplicationService(db).create(payload, actor_id=current_user.id, idempotency_key=idempotency_key)
    if not created:
        response.status_code = status.HTTP_200_OK
    return _app_read(db, sub)


@router.get("/applications", response_model=list[ApplicationListItem])
def list_applications(
    current_user: ReadOnlyUser,
    db: DbSession,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> list[ApplicationListItem]:
    svc = ApplicationService(db)
    subs = svc.list(skip=skip, limit=limit)
    counts = svc.document_counts([s.startup_id for s in subs])
    items = []
    for s in subs:
        st = db.get(StartupApplication, s.startup_id)
        run = svc.latest_run(s.startup_id)
        items.append(ApplicationListItem(
            id=s.id,
            application_ref=s.application_ref,
            startup_id=s.startup_id,
            company_name=st.startup_name,
            sector=st.sector,
            stage=st.stage,
            status=getattr(st.current_status, "value", str(st.current_status)),
            is_synthetic=s.is_synthetic,
            document_count=counts.get(s.startup_id, 0),
            created_at=s.created_at,
            latest_run_status=run.status if run else None,
            latest_run_id=run.id if run else None,
        ))
    return items


@router.get("/runtime-mode")
def runtime_mode(current_user: ReadOnlyUser) -> dict:
    """Evaluation mode the server is configured for (no secrets, no key presence details)."""
    from app.core.config import get_settings
    from app.modules.applications.runner import resolve_run_mode

    mode = resolve_run_mode()
    return {
        "mode": mode,
        "disclosure": MOCK_DISCLOSURE if mode == "MOCK_DEMONSTRATION" else None,
        "live_evaluations_enabled_in_ui": bool(get_settings().allow_ui_live_evaluations),
        "evaluation_budget_usd": get_settings().ai_max_evaluation_budget_usd,
    }


@router.get("/applications-dashboard")
def applications_dashboard(current_user: ReadOnlyUser, db: DbSession) -> dict:
    svc = ApplicationService(db)
    stats = svc.dashboard_counts()
    recent = []
    for run in db.query(EvaluationRun).order_by(EvaluationRun.updated_at.desc()).limit(8).all():
        st = db.get(StartupApplication, run.startup_id)
        recent.append({
            "type": "evaluation",
            "evaluation_id": run.id,
            "startup_name": st.startup_name if st else None,
            "status": run.status,
            "mode": run.mode,
            "at": (run.finished_at or run.started_at or run.created_at).isoformat(),
        })
    for sub in svc.list(limit=8):
        st = db.get(StartupApplication, sub.startup_id)
        recent.append({
            "type": "application",
            "application_id": str(sub.id),
            "application_ref": sub.application_ref,
            "startup_name": st.startup_name if st else None,
            "status": "SUBMITTED",
            "at": sub.created_at.isoformat(),
        })
    recent.sort(key=lambda x: x["at"], reverse=True)
    stats["recent_activity"] = recent[:10]
    return stats


@router.get("/applications/{application_id}", response_model=ApplicationRead)
def get_application(application_id: UUID, current_user: ReadOnlyUser, db: DbSession) -> ApplicationRead:
    return _app_read(db, ApplicationService(db).get(application_id))


@router.post("/applications/{application_id}/documents", response_model=DocumentSummary, status_code=status.HTTP_201_CREATED)
def upload_application_document(
    application_id: UUID,
    current_user: EvaluatorUser,
    db: DbSession,
    document_type: DocumentType = Form(DocumentType.PITCH_DECK),
    file: UploadFile = File(...),
) -> DocumentSummary:
    sub = ApplicationService(db).get(application_id)
    latest = ApplicationService(db).latest_run(sub.startup_id)
    if latest and latest.status in ("QUEUED", "RUNNING"):
        raise ValidationError("Documents cannot be changed while an evaluation is running.")
    doc = DocumentService(db).upload(sub.startup_id, file=file, document_type=document_type, actor_id=current_user.id)
    return DocumentSummary(
        id=doc.id,
        document_type=getattr(doc.document_type, "value", str(doc.document_type)),
        original_filename=doc.original_filename,
        content_type=doc.content_type,
        file_size=doc.file_size,
        processing_status=getattr(doc.processing_status, "value", str(doc.processing_status)),
        created_at=doc.created_at,
    )


@router.post("/applications/{application_id}/evaluations", response_model=EvaluationRunRead)
def start_application_evaluation(
    application_id: UUID,
    current_user: EvaluatorUser,
    db: DbSession,
    response: Response,
    rerun: bool = Query(default=False),
) -> EvaluationRunRead:
    sub = ApplicationService(db).get(application_id)
    run, created = start_evaluation_run(db, sub, actor_id=current_user.id, rerun=rerun)
    db.refresh(run)
    response.status_code = status.HTTP_202_ACCEPTED if created else status.HTTP_200_OK
    return _run_read(run)


@router.get("/applications/{application_id}/evaluations", response_model=list[EvaluationRunRead])
def list_application_evaluations(application_id: UUID, current_user: ReadOnlyUser, db: DbSession):
    sub = ApplicationService(db).get(application_id)
    return [_run_read(r) for r in ApplicationService(db).runs_for(sub.startup_id)]


@router.get("/evaluation-runs/{run_id}", response_model=EvaluationRunRead)
def get_evaluation_run(run_id: str, current_user: ReadOnlyUser, db: DbSession) -> EvaluationRunRead:
    return _run_read(ApplicationService(db).get_run(run_id))


@router.get("/evaluation-runs/{run_id}/results")
def get_evaluation_results(run_id: str, current_user: ReadOnlyUser, db: DbSession) -> dict:
    run = ApplicationService(db).get_run(run_id)
    data = build_run_results(db, run)
    data["disclosure"] = MOCK_DISCLOSURE if run.mode == "MOCK_DEMONSTRATION" else None
    return data


@router.get("/evaluation-runs/{run_id}/evidence")
def get_evaluation_evidence(
    run_id: str,
    current_user: ReadOnlyUser,
    db: DbSession,
    ids: str = Query(..., description="Comma-separated evidence IDs"),
) -> list[dict]:
    run = ApplicationService(db).get_run(run_id)
    return evidence_records(db, run.startup_id, [x.strip() for x in ids.split(",") if x.strip()])


@router.get("/evaluation-runs/{run_id}/report.pdf")
def download_run_report(run_id: str, current_user: ReadOnlyUser, db: DbSession) -> Response:
    from app.modules.applications.pdf_report import get_or_build_run_pdf

    run = ApplicationService(db).get_run(run_id)
    if run.status != "COMPLETED":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"No validated report: evaluation status is {run.status}. Incomplete evaluations never produce a final report.",
        )
    pdf_bytes, filename = get_or_build_run_pdf(db, run)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"', "Cache-Control": "no-store"},
    )
