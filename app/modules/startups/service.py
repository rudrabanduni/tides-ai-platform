from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.enums import StartupStatus
from app.core.exceptions import NotFoundError
from app.db.mixins import utcnow
from app.modules.audit.service import AuditService
from app.modules.startups.models import StartupApplication, StartupStatusHistory
from app.modules.startups.repository import StartupRepository, StartupStatusHistoryRepository
from app.modules.startups.schemas import StartupCreate, StartupUpdate

from app.modules.reviews.models import ReviewerComment, CommitteeNote, ScoreOverride
from app.modules.evaluations.models import Evaluation, EvaluationScore, EvaluationEvidence
from app.modules.startup_profiles.models import StartupProfile, StartupProfileVersion, AIAssessmentRecord
from app.modules.founders.models import Founder
from app.modules.company_profiles.models import CompanyProfile
from app.modules.documents.models import Document, DocumentSource


class StartupService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.startups = StartupRepository(db)
        self.history = StartupStatusHistoryRepository(db)
        self.audit = AuditService(db)

    def create(self, payload: StartupCreate, *, actor_id: UUID | None) -> StartupApplication:
        startup = StartupApplication(**payload.model_dump(), created_by=actor_id)
        self.startups.add(startup)
        self.history.add(
            StartupStatusHistory(
                startup_id=startup.id,
                old_status=None,
                new_status=StartupStatus.DRAFT,
                changed_by=actor_id,
                reason="Startup application created",
            )
        )
        self.audit.log(
            actor_id=actor_id,
            entity_type="startup",
            entity_id=startup.id,
            action="startup_created",
            details={"startup_name": startup.startup_name},
        )
        self.db.commit()
        self.db.refresh(startup)
        return startup

    def get(self, startup_id: UUID) -> StartupApplication:
        startup = self.startups.get(startup_id)
        if not startup:
            raise NotFoundError("Startup not found")
        return startup

    def list(self, *, skip: int = 0, limit: int = 100) -> Sequence[StartupApplication]:
        return self.startups.list(skip=skip, limit=limit)

    def update(self, startup_id: UUID, payload: StartupUpdate, *, actor_id: UUID | None) -> StartupApplication:
        startup = self.get(startup_id)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(startup, field, value)
        self.audit.log(
            actor_id=actor_id,
            entity_type="startup",
            entity_id=startup.id,
            action="startup_updated",
            details=data,
        )
        self.db.commit()
        self.db.refresh(startup)
        return startup

    def change_status(
        self,
        startup_id: UUID,
        *,
        new_status: StartupStatus,
        reason: str,
        actor_id: UUID | None,
    ) -> StartupApplication:
        startup = self.get(startup_id)
        old_status = startup.current_status
        startup.current_status = new_status
        if new_status == StartupStatus.SUBMITTED and startup.submitted_at is None:
            startup.submitted_at = utcnow()
        self.history.add(
            StartupStatusHistory(
                startup_id=startup.id,
                old_status=old_status,
                new_status=new_status,
                changed_by=actor_id,
                reason=reason,
            )
        )
        self.audit.log(
            actor_id=actor_id,
            entity_type="startup",
            entity_id=startup.id,
            action="startup_status_changed",
            reason=reason,
            details={"old_status": old_status.value, "new_status": new_status.value},
        )
        self.db.commit()
        self.db.refresh(startup)
        return startup

    def submit(self, startup_id: UUID, *, actor_id: UUID | None) -> StartupApplication:
        return self.change_status(
            startup_id,
            new_status=StartupStatus.SUBMITTED,
            reason="Startup submitted for evaluation",
            actor_id=actor_id,
        )

    def status_history(self, startup_id: UUID) -> Sequence[StartupStatusHistory]:
        self.get(startup_id)
        return self.history.list_for_startup(startup_id)

    def delete(self, startup_id: UUID, *, actor_id: UUID | None) -> None:
        startup = self.get(startup_id)

        # 1. Fetch evaluations to get evaluation IDs
        evaluations = self.db.query(Evaluation).filter(Evaluation.startup_id == startup_id).all()
        eval_ids = [e.id for e in evaluations]

        # 2. Fetch evaluation scores to get score IDs
        eval_score_ids = []
        if eval_ids:
            eval_scores = self.db.query(EvaluationScore).filter(EvaluationScore.evaluation_id.in_(eval_ids)).all()
            eval_score_ids = [es.id for es in eval_scores]

        # 3. Fetch startup profiles to get profile IDs
        profiles = self.db.query(StartupProfile).filter(StartupProfile.startup_id == startup_id).all()
        profile_ids = [p.id for p in profiles]

        # 4. Perform sequential deletions in correct dependency order
        # Score overrides & evidence
        if eval_score_ids:
            self.db.query(ScoreOverride).filter(ScoreOverride.evaluation_score_id.in_(eval_score_ids)).delete(synchronize_session=False)
            self.db.query(EvaluationEvidence).filter(EvaluationEvidence.evaluation_score_id.in_(eval_score_ids)).delete(synchronize_session=False)

        # Evaluation scores
        if eval_ids:
            self.db.query(EvaluationScore).filter(EvaluationScore.evaluation_id.in_(eval_ids)).delete(synchronize_session=False)

        # Evaluations
        self.db.query(Evaluation).filter(Evaluation.startup_id == startup_id).delete(synchronize_session=False)

        # Reviewer comments & committee notes
        self.db.query(ReviewerComment).filter(ReviewerComment.startup_id == startup_id).delete(synchronize_session=False)
        self.db.query(CommitteeNote).filter(CommitteeNote.startup_id == startup_id).delete(synchronize_session=False)

        # Startup status history
        self.db.query(StartupStatusHistory).filter(StartupStatusHistory.startup_id == startup_id).delete(synchronize_session=False)

        # Startup profile versions
        if profile_ids:
            self.db.query(StartupProfileVersion).filter(StartupProfileVersion.startup_profile_id.in_(profile_ids)).delete(synchronize_session=False)

        # Startup profiles
        self.db.query(StartupProfile).filter(StartupProfile.startup_id == startup_id).delete(synchronize_session=False)

        # Founders
        self.db.query(Founder).filter(Founder.startup_id == startup_id).delete(synchronize_session=False)

        # Company profiles
        self.db.query(CompanyProfile).filter(CompanyProfile.startup_id == startup_id).delete(synchronize_session=False)

        # Document sources
        self.db.query(DocumentSource).filter(DocumentSource.startup_id == startup_id).delete(synchronize_session=False)

        # Documents
        self.db.query(Document).filter(Document.startup_id == startup_id).delete(synchronize_session=False)

        # AI assessment records
        self.db.query(AIAssessmentRecord).filter(AIAssessmentRecord.startup_id == startup_id).delete(synchronize_session=False)

        # Audit log entry for deletion
        self.audit.log(
            actor_id=actor_id,
            entity_type="startup",
            entity_id=startup_id,
            action="startup_deleted",
            details={"startup_name": startup.startup_name},
        )

        # Finally delete startup application itself
        self.db.query(StartupApplication).filter(StartupApplication.id == startup_id).delete(synchronize_session=False)
        self.db.commit()
