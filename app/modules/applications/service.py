"""Application intake and evaluation-run orchestration service."""

from __future__ import annotations

import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.enums import StartupStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.modules.applications.models import ApplicationSubmission, EvaluationRun
from app.modules.applications.schemas import ApplicationCreate
from app.modules.audit.service import AuditService
from app.modules.company_profiles.models import CompanyProfile
from app.modules.documents.models import Document
from app.modules.founders.models import Founder
from app.modules.startups.models import StartupApplication, StartupStatusHistory

logger = logging.getLogger(__name__)

ACTIVE_RUN_STATUSES = ("QUEUED", "RUNNING")


def _new_application_ref(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    for _ in range(10):
        ref = f"TIDES-{year}-{secrets.token_hex(3).upper()}"
        if not db.query(ApplicationSubmission.id).filter(ApplicationSubmission.application_ref == ref).first():
            return ref
    raise RuntimeError("Unable to allocate a unique application reference")


class ApplicationService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.audit = AuditService(db)

    # ------------------------------------------------------------------ intake
    def create(
        self,
        payload: ApplicationCreate,
        *,
        actor_id: UUID | None,
        idempotency_key: str | None = None,
    ) -> tuple[ApplicationSubmission, bool]:
        """Creates the startup, founders, company profile and submission in ONE transaction.

        Returns (submission, created). A repeated request with the same Idempotency-Key returns
        the original submission instead of creating a duplicate.
        """
        key = (idempotency_key or "").strip()[:128] or None
        if key:
            existing = self.db.query(ApplicationSubmission).filter(ApplicationSubmission.idempotency_key == key).first()
            if existing:
                return existing, False

        now = datetime.now(timezone.utc)
        try:
            startup = StartupApplication(
                startup_name=payload.company_name.strip(),
                sector=payload.sector.strip(),
                stage=payload.stage,
                current_status=StartupStatus.SUBMITTED,
                problem_statement=payload.problem_statement.strip(),
                solution_summary=payload.proposed_solution.strip(),
                business_model=payload.business_model.strip(),
                target_market=payload.target_market.strip(),
                traction_summary=(payload.traction or "").strip() or None,
                funding_status=(payload.funding_requirement or "").strip() or None,
                created_by=actor_id,
                submitted_at=now,
            )
            self.db.add(startup)
            self.db.flush()
            self.db.add(
                StartupStatusHistory(
                    startup_id=startup.id,
                    old_status=None,
                    new_status=StartupStatus.SUBMITTED,
                    changed_by=actor_id,
                    reason="Application submitted through intake form",
                )
            )
            for f in payload.founders:
                self.db.add(Founder(startup_id=startup.id, **f.model_dump()))
            self.db.add(
                CompanyProfile(
                    startup_id=startup.id,
                    website=payload.website,
                    location=payload.location,
                    team_size=len(payload.founders),
                    revenue_status=payload.revenue_information,
                    market_category=payload.industry,
                )
            )
            submission = ApplicationSubmission(
                application_ref=_new_application_ref(self.db),
                startup_id=startup.id,
                idempotency_key=key,
                industry=payload.industry,
                location=payload.location,
                contact_name=payload.contact_name,
                contact_email=str(payload.contact_email),
                contact_phone=payload.contact_phone,
                website=payload.website,
                product_technology=payload.product_technology,
                revenue_information=payload.revenue_information,
                financial_information=payload.financial_information,
                funding_requirement=payload.funding_requirement,
                incubation_support_requirement=payload.incubation_support_requirement,
                declarations=payload.declarations.model_dump(),
                is_synthetic=bool(payload.declarations.synthetic_demo_data),
                submitted_by=actor_id,
                submitted_at=now,
            )
            self.db.add(submission)
            self.db.flush()
            # Audit entries carry identifiers only - no founder or contact PII.
            self.audit.log(
                actor_id=actor_id,
                entity_type="application",
                entity_id=submission.id,
                action="application_submitted",
                details={"startup_id": str(startup.id), "application_ref": submission.application_ref},
            )
            self.db.commit()
        except IntegrityError:
            self.db.rollback()
            if key:
                existing = self.db.query(ApplicationSubmission).filter(ApplicationSubmission.idempotency_key == key).first()
                if existing:
                    return existing, False
            raise
        self.db.refresh(submission)
        return submission, True

    def get(self, application_id: UUID) -> ApplicationSubmission:
        sub = self.db.get(ApplicationSubmission, application_id)
        if not sub:
            raise NotFoundError("Application not found")
        return sub

    def get_by_startup(self, startup_id: UUID) -> ApplicationSubmission | None:
        return self.db.query(ApplicationSubmission).filter(ApplicationSubmission.startup_id == startup_id).first()

    def list(self, *, skip: int = 0, limit: int = 100) -> Sequence[ApplicationSubmission]:
        return (
            self.db.query(ApplicationSubmission)
            .order_by(ApplicationSubmission.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def documents_for(self, startup_id: UUID) -> list[Document]:
        return (
            self.db.query(Document)
            .filter(Document.startup_id == startup_id)
            .order_by(Document.created_at.asc())
            .all()
        )

    def founders_for(self, startup_id: UUID) -> list[Founder]:
        return self.db.query(Founder).filter(Founder.startup_id == startup_id).order_by(Founder.created_at.asc()).all()

    def document_counts(self, startup_ids: list[UUID]) -> dict[UUID, int]:
        if not startup_ids:
            return {}
        rows = (
            self.db.query(Document.startup_id, func.count(Document.id))
            .filter(Document.startup_id.in_(startup_ids))
            .group_by(Document.startup_id)
            .all()
        )
        return {sid: int(cnt) for sid, cnt in rows}

    # ------------------------------------------------------------------ runs
    def latest_run(self, startup_id: UUID) -> EvaluationRun | None:
        return (
            self.db.query(EvaluationRun)
            .filter(EvaluationRun.startup_id == startup_id)
            .order_by(EvaluationRun.created_at.desc())
            .first()
        )

    def runs_for(self, startup_id: UUID) -> list[EvaluationRun]:
        return (
            self.db.query(EvaluationRun)
            .filter(EvaluationRun.startup_id == startup_id)
            .order_by(EvaluationRun.created_at.desc())
            .all()
        )

    def get_run(self, run_id: str) -> EvaluationRun:
        run = self.db.get(EvaluationRun, run_id)
        if not run:
            raise NotFoundError("Evaluation run not found")
        return run

    def assert_ready_for_evaluation(self, sub: ApplicationSubmission) -> list[Document]:
        docs = self.documents_for(sub.startup_id)
        if not docs:
            raise ValidationError("Upload at least one supporting document (pitch deck) before starting the evaluation.")
        return docs

    def dashboard_counts(self) -> dict[str, Any]:
        total = self.db.query(func.count(ApplicationSubmission.id)).scalar() or 0
        synthetic = (
            self.db.query(func.count(ApplicationSubmission.id)).filter(ApplicationSubmission.is_synthetic.is_(True)).scalar()
            or 0
        )
        latest_by_startup: dict[UUID, EvaluationRun] = {}
        for run in self.db.query(EvaluationRun).order_by(EvaluationRun.created_at.asc()).all():
            latest_by_startup[run.startup_id] = run
        statuses = [r.status for r in latest_by_startup.values()]
        under_eval = sum(1 for s in statuses if s in ACTIVE_RUN_STATUSES)
        completed = sum(1 for s in statuses if s == "COMPLETED")
        blocked = sum(1 for s in statuses if s in ("BLOCKED", "FAILED"))
        evaluated_ids = set(latest_by_startup.keys())
        sub_startups = [sid for (sid,) in self.db.query(ApplicationSubmission.startup_id).all()]
        pending = sum(1 for sid in sub_startups if sid not in evaluated_ids)
        pending_supervisory = sum(
            1 for r in latest_by_startup.values()
            if r.status == "BLOCKED" or (r.summary or {}).get("supervisory_status") in ("BLOCKED", "PENDING")
        )
        sectors: dict[str, int] = {}
        stages: dict[str, int] = {}
        for sector, stage in (
            self.db.query(StartupApplication.sector, StartupApplication.stage)
            .join(ApplicationSubmission, ApplicationSubmission.startup_id == StartupApplication.id)
            .all()
        ):
            sectors[sector or "Unspecified"] = sectors.get(sector or "Unspecified", 0) + 1
            stages[stage or "Unspecified"] = stages.get(stage or "Unspecified", 0) + 1
        return {
            "total_applications": int(total),
            "synthetic_applications": int(synthetic),
            "pending_applications": int(pending),
            "under_evaluation": int(under_eval),
            "completed_evaluations": int(completed),
            "blocked_or_failed_evaluations": int(blocked),
            "pending_supervisory_reviews": int(pending_supervisory),
            "sectors": sectors,
            "stages": stages,
        }
