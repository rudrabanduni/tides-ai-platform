from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.audit.service import AuditService
from app.modules.founders.models import Founder
from app.modules.founders.repository import FounderRepository
from app.modules.founders.schemas import FounderCreate, FounderUpdate
from app.modules.startups.service import StartupService


class FounderService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.founders = FounderRepository(db)
        self.startups = StartupService(db)
        self.audit = AuditService(db)

    def create(self, startup_id: UUID, payload: FounderCreate, *, actor_id: UUID | None) -> Founder:
        self.startups.get(startup_id)
        founder = Founder(startup_id=startup_id, **payload.model_dump())
        self.founders.add(founder)
        self.audit.log(
            actor_id=actor_id,
            entity_type="founder",
            entity_id=founder.id,
            action="founder_created",
            details={"startup_id": str(startup_id)},
        )
        self.db.commit()
        self.db.refresh(founder)
        return founder

    def get(self, founder_id: UUID) -> Founder:
        founder = self.founders.get(founder_id)
        if not founder:
            raise NotFoundError("Founder not found")
        return founder

    def list_for_startup(self, startup_id: UUID) -> Sequence[Founder]:
        self.startups.get(startup_id)
        return self.founders.list_for_startup(startup_id)

    def update(self, founder_id: UUID, payload: FounderUpdate, *, actor_id: UUID | None) -> Founder:
        founder = self.get(founder_id)
        data = payload.model_dump(exclude_unset=True)
        for field, value in data.items():
            setattr(founder, field, value)
        self.audit.log(
            actor_id=actor_id,
            entity_type="founder",
            entity_id=founder.id,
            action="founder_updated",
            details=data,
        )
        self.db.commit()
        self.db.refresh(founder)
        return founder
