from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.company_profiles.models import CompanyProfile
from app.repositories.base import BaseRepository


class CompanyProfileRepository(BaseRepository[CompanyProfile]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, CompanyProfile)

    def get_by_startup(self, startup_id: UUID) -> CompanyProfile | None:
        return self.db.scalar(select(CompanyProfile).where(CompanyProfile.startup_id == startup_id))
