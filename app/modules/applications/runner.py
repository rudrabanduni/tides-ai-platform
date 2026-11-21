"""Evaluation-run execution: starts the real evaluation pipeline for a submitted application and
persists every genuine stage transition to the `evaluation_runs` row.

Execution modes (setting EVALUATION_RUNNER_MODE):
  * "thread" (default): pipeline runs in a background worker thread with its own DB session.
  * "inline": pipeline runs inside the request (used by automated tests for determinism).
"""

from __future__ import annotations

import asyncio
import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import ValidationError
from app.modules.applications.models import ApplicationSubmission, EvaluationRun
from app.modules.applications.service import ACTIVE_RUN_STATUSES, ApplicationService
from app.modules.workflow.progress import bind_progress_reporter, reset_progress_reporter

logger = logging.getLogger(__name__)

MOCK_DISCLOSURE = "MOCK DEMONSTRATION — OFFLINE SYNTHETIC RESULTS — NOT A REAL AI EVALUATION"

DOMAIN_LABELS = {
    "problem_solution": "Problem & Solution",
    "market_opportunity": "Market Opportunity",
    "founder_team": "Founder & Team",
    "commercialisation": "Business Model & Commercialisation",
    "innovation_impact": "Innovation & Impact",
    "financials_support": "Financials & Incubation Support",
}

_PIPELINE_STAGE_KEYS = {
    "Knowledge Graph Construction": "pipeline:Knowledge Graph Construction",
    "Report Generation": "pipeline:Report Generation",
    "PDF Serialization": "pipeline:PDF Serialization",
}

_lock = threading.Lock()


def _stage_template() -> list[dict[str, Any]]:
    from app.modules.ai.orchestrator.extraction_checkpoint import EXTRACTION_STAGE_SPECS

    stages: list[dict[str, Any]] = [
        {"key": "intake", "label": "Application & documents registered", "group": "intake", "status": "SUCCESS"},
        {"key": "pipeline:Document Extraction", "label": "Document parsing & extraction", "group": "extraction", "status": "PENDING"},
    ]
    for spec in EXTRACTION_STAGE_SPECS:
        stages.append({"key": f"extraction:{spec.key}", "label": spec.title, "group": "extraction", "status": "PENDING"})
    stages.append({"key": "claims", "label": "Claims & evidence persisted", "group": "extraction", "status": "PENDING"})
    for dkey, label in DOMAIN_LABELS.items():
        stages.append({"key": f"domain:{dkey}", "label": label, "group": "domains", "status": "PENDING"})
    stages.append({"key": "supervisory", "label": "Supervisory review", "group": "supervisory", "status": "PENDING"})
    stages.append({"key": "pipeline:Knowledge Graph Construction", "label": "Evidence graph", "group": "report", "status": "PENDING"})
    stages.append({"key": "pipeline:Report Generation", "label": "Due-diligence report generation", "group": "report", "status": "PENDING"})
    stages.append({"key": "pipeline:PDF Serialization", "label": "PDF generation", "group": "report", "status": "PENDING"})
    stages.append({"key": "validation", "label": "Canonical 87-criterion report validation", "group": "report", "status": "PENDING"})
    return stages


def _progress_pct(stages: list[dict[str, Any]]) -> int:
    done = sum(1 for s in stages if s.get("status") in ("SUCCESS", "SKIPPED"))
    return int(round(100 * done / max(1, len(stages))))


def resolve_run_mode() -> str:
    provider = (get_settings().ai_provider or "").strip().lower()
    return "MOCK_DEMONSTRATION" if provider == "mock" else "LIVE_PROVIDER"


def start_evaluation_run(
    db: Session,
    submission: ApplicationSubmission,
    *,
    actor_id: uuid.UUID | None,
    rerun: bool = False,
) -> tuple[EvaluationRun, bool]:
    """Creates (or returns the existing) evaluation run for an application. Returns (run, created)."""
    settings = get_settings()
    service = ApplicationService(db)
    service.assert_ready_for_evaluation(submission)

    mode = resolve_run_mode()
    if mode == "LIVE_PROVIDER" and not settings.allow_ui_live_evaluations:
        raise ValidationError(
            "Live-provider evaluations are disabled for the web application "
            "(ALLOW_UI_LIVE_EVALUATIONS=false). Use the offline demonstration mode or an authorised pilot procedure."
        )

    with _lock:
        active = (
            db.query(EvaluationRun)
            .filter(EvaluationRun.startup_id == submission.startup_id, EvaluationRun.status.in_(ACTIVE_RUN_STATUSES))
            .order_by(EvaluationRun.created_at.desc())
            .first()
        )
        if active:
            return active, False
        latest = service.latest_run(submission.startup_id)
        if latest and latest.status == "COMPLETED" and not rerun:
            return latest, False

        run = EvaluationRun(
            id=str(uuid.uuid4()),
            startup_id=submission.startup_id,
            application_id=submission.id,
            status="QUEUED",
            mode=mode,
            current_stage="queued",
            stages=_stage_template(),
            progress_pct=0,
            summary={},
            started_by=actor_id,
        )
        run.progress_pct = _progress_pct(run.stages)
        db.add(run)
        db.commit()
        db.refresh(run)

    if settings.evaluation_runner_mode == "inline":
        execute_evaluation_run(run.id, session_factory=_session_factory_for(db))
        db.refresh(run)
    else:
        worker = threading.Thread(
            target=execute_evaluation_run,
            args=(run.id,),
            kwargs={"session_factory": _session_factory_for(db)},
            name=f"tides-eval-{run.id[:8]}",
            daemon=True,
        )
        worker.start()
    return run, True


def _session_factory_for(db: Session):
    bind = db.get_bind()
    from sqlalchemy.orm import sessionmaker

    return sessionmaker(bind=bind, autoflush=False, autocommit=False, expire_on_commit=False)


class _RunProgressWriter:
    """Persists pipeline progress events onto the evaluation run row."""

    def __init__(self, run_id: str, session_factory) -> None:
        self.run_id = run_id
        self.session_factory = session_factory

    def __call__(self, stage: str, status: str, detail: dict[str, Any] | None = None) -> None:
        with self.session_factory() as s:
            run = s.get(EvaluationRun, self.run_id)
            if run is None:
                return
            stages = [dict(x) for x in (run.stages or [])]
            now = datetime.now(timezone.utc).isoformat()
            match = next((x for x in stages if x.get("key") == stage), None)
            if match is None:
                return  # untracked internal stage (e.g. legacy committee engine)
            match["status"] = status
            if status == "RUNNING":
                match.setdefault("started_at", now)
            else:
                match["finished_at"] = now
            if detail:
                match["detail"] = {k: v for k, v in detail.items() if v not in (None, "", [])}
            if stage == "pipeline:Document Extraction" and status == "SUCCESS":
                claims = next((x for x in stages if x["key"] == "claims"), None)
                if claims:
                    claims["status"] = "SUCCESS"
                    claims["finished_at"] = now
            run.stages = stages
            run.current_stage = match.get("label") if status == "RUNNING" else run.current_stage
            run.progress_pct = _progress_pct(stages)
            s.commit()


def execute_evaluation_run(run_id: str, *, session_factory) -> None:
    """Runs the full evaluation pipeline for one run. Never raises; outcome is written to the row."""
    from app.modules.ai.orchestrator.pipeline import coordinate_evaluation_pipeline
    from app.modules.applications.results import build_run_summary

    with session_factory() as db:
        run = db.get(EvaluationRun, run_id)
        if run is None:
            return
        startup = run.startup_id
        run.status = "RUNNING"
        run.started_at = datetime.now(timezone.utc)
        run.current_stage = "Document parsing & extraction"
        db.commit()
        from app.modules.startups.models import StartupApplication

        st = db.get(StartupApplication, startup)
        startup_name, sector, stage = st.startup_name, st.sector or "", st.stage or ""

    writer = _RunProgressWriter(run_id, session_factory)
    token = bind_progress_reporter(writer)
    result: dict[str, Any] | None = None
    error: str | None = None
    try:
        with session_factory() as work_db:
            result = asyncio.run(
                coordinate_evaluation_pipeline(
                    db=work_db,
                    startup_name=startup_name,
                    sector=sector,
                    stage=stage,
                    files=[],
                    existing_startup_id=startup,
                    max_budget_usd=get_settings().ai_max_evaluation_budget_usd,
                    evaluation_id=run_id,
                )
            )
    except Exception as exc:  # pipeline crash: record, never hide
        logger.exception("Evaluation run %s failed", run_id)
        error = f"{type(exc).__name__}: {str(exc)[:500]}"
    finally:
        reset_progress_reporter(token)

    with session_factory() as db:
        run = db.get(EvaluationRun, run_id)
        if run is None:
            return
        stages = [dict(x) for x in (run.stages or [])]
        run.finished_at = datetime.now(timezone.utc)
        simulated_cost: float | None = None
        if result is not None:
            run.pipeline_status = str(result.get("evaluation_status") or "")
            run.report_id = result.get("assessment_identifier")
            cost = float((result.get("cost_observability") or {}).get("total_spent_usd") or 0.0)
            # Mock runs incur no provider spend; the mock ledger only simulates token pricing
            # to exercise the budget guards, so it is never reported as actual cost.
            run.cost_usd = 0.0 if run.mode == "MOCK_DEMONSTRATION" else cost
            simulated_cost = cost if run.mode == "MOCK_DEMONSTRATION" else None
        summary: dict[str, Any] = {}
        if error is None and result is not None:
            try:
                summary = build_run_summary(db, run)
            except Exception as exc:
                logger.exception("Could not build run summary for %s", run_id)
                summary = {"summary_error": f"{type(exc).__name__}: {str(exc)[:300]}"}
        if simulated_cost is not None:
            summary["simulated_provider_cost_usd"] = round(simulated_cost, 6)
            summary["actual_provider_spend_usd"] = 0.0
        run.summary = summary

        pipeline_status = run.pipeline_status or ""
        validation = summary.get("validation") or {}
        for x in stages:
            if x["key"] == "validation":
                x["status"] = "SUCCESS" if validation.get("valid") else ("FAILED" if result is not None else "PENDING")
                x["detail"] = {"errors": (validation.get("errors") or [])[:10]}
            elif x["status"] == "RUNNING":
                x["status"] = "FAILED" if (error or pipeline_status != "COMPLETED") else "SUCCESS"

        if error:
            run.status, run.error_message = "FAILED", error
        elif pipeline_status == "COMPLETED" and validation.get("valid") and summary.get("coverage", {}).get("complete"):
            run.status = "COMPLETED"
        elif pipeline_status in ("COMPLETED", "COMPLETED_WITH_PARTIAL_DOMAIN_FAILURES"):
            # Report exists but is not complete/valid: never labelled complete.
            run.status = "BLOCKED"
            run.error_message = (
                "Evaluation incomplete: supervisory review was blocked or the canonical report failed validation."
            )
        else:
            run.status = "FAILED"
            run.error_message = str(
                (result or {}).get("error_message") or (result or {}).get("exhaustion_reason") or pipeline_status
            )[:1000]
        run.stages = stages
        run.progress_pct = _progress_pct(stages)
        run.current_stage = {"COMPLETED": "Report ready", "BLOCKED": "Blocked", "FAILED": "Failed"}.get(run.status)

        from app.core.enums import StartupStatus
        from app.modules.startups.models import StartupApplication

        st = db.get(StartupApplication, run.startup_id)
        if st is not None and run.status == "COMPLETED":
            st.current_status = StartupStatus.AI_EVALUATED
        db.commit()
