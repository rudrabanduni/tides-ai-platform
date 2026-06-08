from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.modules.audit.service import AuditService
from app.modules.company_profiles.models import CompanyProfile
from app.modules.company_profiles.repository import CompanyProfileRepository
from app.modules.company_profiles.schemas import CompanyProfilePayload
from app.modules.startups.service import StartupService


class CompanyProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.company_profiles = CompanyProfileRepository(db)
        self.startups = StartupService(db)
        self.audit = AuditService(db)

    def get_by_startup(self, startup_id: UUID) -> CompanyProfile:
        profile = self.company_profiles.get_by_startup(startup_id)
        if not profile:
            raise NotFoundError("Company profile not found")
        return profile

    def upsert(self, startup_id: UUID, payload: CompanyProfilePayload, *, actor_id: UUID | None) -> CompanyProfile:
        self.startups.get(startup_id)
        profile = self.company_profiles.get_by_startup(startup_id)
        data = payload.model_dump()
        if profile is None:
            profile = CompanyProfile(startup_id=startup_id, **data)
            self.company_profiles.add(profile)
            action = "company_profile_created"
        else:
            for field, value in data.items():
                setattr(profile, field, value)
            action = "company_profile_updated"
        self.audit.log(
            actor_id=actor_id,
            entity_type="company_profile",
            entity_id=profile.id,
            action=action,
            details={"startup_id": str(startup_id)},
        )
        self.db.commit()
        self.db.refresh(profile)
        return profile
