from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.startups.models import StartupApplication, StartupStatusHistory
from app.repositories.base import BaseRepository


class StartupRepository(BaseRepository[StartupApplication]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, StartupApplication)

    def list(self, *, skip: int = 0, limit: int = 100) -> Sequence[StartupApplication]:
        statement = (
            select(StartupApplication)
            .order_by(StartupApplication.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return self.db.scalars(statement).all()


class StartupStatusHistoryRepository(BaseRepository[StartupStatusHistory]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, StartupStatusHistory)

    def list_for_startup(self, startup_id: UUID) -> Sequence[StartupStatusHistory]:
        statement = (
            select(StartupStatusHistory)
            .where(StartupStatusHistory.startup_id == startup_id)
            .order_by(StartupStatusHistory.created_at.desc())
        )
        return self.db.scalars(statement).all()
