from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.founders.models import Founder
from app.repositories.base import BaseRepository


class FounderRepository(BaseRepository[Founder]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Founder)

    def list_for_startup(self, startup_id: UUID) -> Sequence[Founder]:
        statement = select(Founder).where(Founder.startup_id == startup_id).order_by(Founder.created_at.asc())
        return self.db.scalars(statement).all()
