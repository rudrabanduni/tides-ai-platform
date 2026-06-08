from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.db.mixins import utcnow
from app.modules.audit.service import AuditService
from app.modules.startup_profiles.models import StartupProfile, StartupProfileVersion
from app.modules.startup_profiles.repository import StartupProfileRepository, StartupProfileVersionRepository
from app.modules.startup_profiles.schemas import StartupProfilePayload
from app.modules.startups.service import StartupService


PROFILE_FIELDS = [
    "problem_statement",
    "solution_summary",
    "target_market",
    "business_model",
    "technology_summary",
    "traction_summary",
    "funding_summary",
    "ip_summary",
]


class StartupProfileService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.profiles = StartupProfileRepository(db)
        self.versions = StartupProfileVersionRepository(db)
        self.startups = StartupService(db)
        self.audit = AuditService(db)

    def get_by_startup(self, startup_id: UUID) -> StartupProfile:
        profile = self.profiles.get_by_startup(startup_id)
        if not profile:
            raise NotFoundError("Startup profile not found")
        return profile

    def upsert(self, startup_id: UUID, payload: StartupProfilePayload, *, actor_id: UUID | None) -> StartupProfile:
        self.startups.get(startup_id)
        profile = self.profiles.get_by_startup(startup_id)
        data = payload.model_dump()
        if profile is None:
            profile = StartupProfile(startup_id=startup_id, **data)
            self.profiles.add(profile)
            action = "startup_profile_created"
        else:
            for field, value in data.items():
                setattr(profile, field, value)
            profile.updated_at = utcnow()
            action = "startup_profile_updated"

        snapshot = self._snapshot(profile)
        version_number = self.versions.next_version_number(profile.id)
        version = StartupProfileVersion(
            startup_profile_id=profile.id,
            version_number=version_number,
            profile_snapshot=snapshot,
        )
        self.versions.add(version)
        self.audit.log(
            actor_id=actor_id,
            entity_type="startup_profile",
            entity_id=profile.id,
            action=action,
            details={"startup_id": str(startup_id), "version_number": version_number},
        )
        self.db.commit()
        self.db.refresh(profile)
        return profile

    def versions_for_startup(self, startup_id: UUID) -> Sequence[StartupProfileVersion]:
        profile = self.get_by_startup(startup_id)
        return self.versions.list_for_profile(profile.id)

    def latest_version_for_startup(self, startup_id: UUID) -> StartupProfileVersion | None:
        profile = self.profiles.get_by_startup(startup_id)
        if not profile:
            return None
        return self.versions.latest_for_profile(profile.id)

    def _snapshot(self, profile: StartupProfile) -> dict:
        snapshot = {"startup_id": str(profile.startup_id)}
        for field in PROFILE_FIELDS:
            snapshot[field] = getattr(profile, field)
        return snapshot
