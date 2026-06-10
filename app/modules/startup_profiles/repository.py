from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.startup_profiles.models import AIAssessmentRecord, StartupProfile, StartupProfileVersion
from app.repositories.base import BaseRepository


class StartupProfileRepository(BaseRepository[StartupProfile]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, StartupProfile)

    def get_by_startup(self, startup_id: UUID) -> StartupProfile | None:
        return self.db.scalar(select(StartupProfile).where(StartupProfile.startup_id == startup_id))


class StartupProfileVersionRepository(BaseRepository[StartupProfileVersion]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, StartupProfileVersion)

    def next_version_number(self, startup_profile_id: UUID) -> int:
        statement = select(func.max(StartupProfileVersion.version_number)).where(
            StartupProfileVersion.startup_profile_id == startup_profile_id
        )
        current = self.db.scalar(statement)
        return int(current or 0) + 1

    def latest_for_profile(self, startup_profile_id: UUID) -> StartupProfileVersion | None:
        statement = (
            select(StartupProfileVersion)
            .where(StartupProfileVersion.startup_profile_id == startup_profile_id)
            .order_by(StartupProfileVersion.version_number.desc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def list_for_profile(self, startup_profile_id: UUID) -> Sequence[StartupProfileVersion]:
        statement = (
            select(StartupProfileVersion)
            .where(StartupProfileVersion.startup_profile_id == startup_profile_id)
            .order_by(StartupProfileVersion.version_number.desc())
        )
        return self.db.scalars(statement).all()


class AIAssessmentRecordRepository(BaseRepository[AIAssessmentRecord]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, AIAssessmentRecord)

    def list_for_startup(self, startup_id: UUID) -> Sequence[AIAssessmentRecord]:
        statement = (
            select(AIAssessmentRecord)
            .where(AIAssessmentRecord.startup_id == startup_id)
            .order_by(AIAssessmentRecord.created_at.desc())
        )
        return self.db.scalars(statement).all()

