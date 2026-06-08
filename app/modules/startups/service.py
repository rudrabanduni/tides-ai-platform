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
