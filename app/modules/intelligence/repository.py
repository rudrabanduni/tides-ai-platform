from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.modules.intelligence.models import (
    FieldConflict,
    FieldSource,
    FieldVersion,
    KnowledgeFieldRegistry,
    PipelineStatus,
    StartupClaim,
    StartupEvidence,
    StartupIntelligenceProfile,
    StartupIntelligenceProfileVersion,
    StartupProcessingStatus,
)
from app.repositories.base import BaseRepository


class KnowledgeFieldRegistryRepository(BaseRepository[KnowledgeFieldRegistry]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, KnowledgeFieldRegistry)

    def get_by_key(self, field_key: str) -> KnowledgeFieldRegistry | None:
        statement = select(KnowledgeFieldRegistry).where(KnowledgeFieldRegistry.field_key == field_key)
        return self.db.scalar(statement)

    def list_active(self) -> Sequence[KnowledgeFieldRegistry]:
        statement = select(KnowledgeFieldRegistry).where(KnowledgeFieldRegistry.is_active == True)
        return self.db.scalars(statement).all()


class StartupIntelligenceProfileRepository(BaseRepository[StartupIntelligenceProfile]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, StartupIntelligenceProfile)

    def get_by_startup(self, startup_id: UUID) -> StartupIntelligenceProfile | None:
        statement = select(StartupIntelligenceProfile).where(StartupIntelligenceProfile.startup_id == startup_id)
        return self.db.scalar(statement)


class StartupClaimRepository(BaseRepository[StartupClaim]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, StartupClaim)

    def list_for_profile(self, profile_id: UUID) -> Sequence[StartupClaim]:
        statement = select(StartupClaim).where(StartupClaim.profile_id == profile_id)
        return self.db.scalars(statement).all()

    def list_preferred_for_profile(self, profile_id: UUID) -> Sequence[StartupClaim]:
        statement = select(StartupClaim).where(
            StartupClaim.profile_id == profile_id,
            StartupClaim.is_preferred == True
        )
        return self.db.scalars(statement).all()

    def get_for_field(self, profile_id: UUID, field_id: UUID) -> Sequence[StartupClaim]:
        statement = select(StartupClaim).where(
            StartupClaim.profile_id == profile_id,
            StartupClaim.field_id == field_id
        )
        return self.db.scalars(statement).all()


class StartupEvidenceRepository(BaseRepository[StartupEvidence]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, StartupEvidence)

    def list_for_claim(self, claim_id: UUID) -> Sequence[StartupEvidence]:
        statement = select(StartupEvidence).where(StartupEvidence.claim_id == claim_id)
        return self.db.scalars(statement).all()


class FieldVersionRepository(BaseRepository[FieldVersion]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, FieldVersion)

    def list_for_claim(self, claim_id: UUID) -> Sequence[FieldVersion]:
        statement = select(FieldVersion).where(FieldVersion.claim_id == claim_id).order_by(FieldVersion.version_number.desc())
        return self.db.scalars(statement).all()

    def get_latest_version_number(self, claim_id: UUID) -> int:
        statement = select(FieldVersion.version_number).where(FieldVersion.claim_id == claim_id).order_by(FieldVersion.version_number.desc()).limit(1)
        res = self.db.scalar(statement)
        return res if res is not None else 0


class FieldConflictRepository(BaseRepository[FieldConflict]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, FieldConflict)

    def list_unresolved_for_profile(self, profile_id: UUID) -> Sequence[FieldConflict]:
        statement = select(FieldConflict).where(
            FieldConflict.profile_id == profile_id,
            FieldConflict.resolved == False
        )
        return self.db.scalars(statement).all()


class FieldSourceRepository(BaseRepository[FieldSource]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, FieldSource)

    def list_for_claim(self, claim_id: UUID) -> Sequence[FieldSource]:
        statement = select(FieldSource).where(FieldSource.claim_id == claim_id)
        return self.db.scalars(statement).all()


class StartupProcessingStatusRepository(BaseRepository[StartupProcessingStatus]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, StartupProcessingStatus)

    def get_by_startup_pipeline(self, startup_id: UUID, pipeline_name: str) -> StartupProcessingStatus | None:
        statement = select(StartupProcessingStatus).where(
            StartupProcessingStatus.startup_id == startup_id,
            StartupProcessingStatus.pipeline_name == pipeline_name
        )
        return self.db.scalar(statement)

    def create_status(self, startup_id: UUID, pipeline_name: str, stage: str) -> StartupProcessingStatus:
        status_record = StartupProcessingStatus(
            startup_id=startup_id,
            pipeline_name=pipeline_name,
            current_stage=stage,
            status=PipelineStatus.QUEUED,
            progress_percentage=0
        )
        return self.add(status_record)

    def update_progress(self, entity_id: UUID, stage: str, progress: int, status: PipelineStatus = PipelineStatus.RUNNING) -> None:
        statement = (
            update(StartupProcessingStatus)
            .where(StartupProcessingStatus.id == entity_id)
            .values(current_stage=stage, progress_percentage=progress, status=status)
        )
        self.db.execute(statement)
        self.db.flush()

    def mark_completed(self, entity_id: UUID, processing_time_ms: int) -> None:
        from app.db.mixins import utcnow
        statement = (
            update(StartupProcessingStatus)
            .where(StartupProcessingStatus.id == entity_id)
            .values(
                status=PipelineStatus.COMPLETED,
                progress_percentage=100,
                completed_at=utcnow(),
                processing_time_ms=processing_time_ms
            )
        )
        self.db.execute(statement)
        self.db.flush()

    def mark_failed(self, entity_id: UUID, error_message: str) -> None:
        from app.db.mixins import utcnow
        statement = (
            update(StartupProcessingStatus)
            .where(StartupProcessingStatus.id == entity_id)
            .values(
                status=PipelineStatus.FAILED,
                last_error=error_message,
                completed_at=utcnow()
            )
        )
        self.db.execute(statement)
        self.db.flush()

    def retry(self, entity_id: UUID, stage: str) -> None:
        statement = (
            update(StartupProcessingStatus)
            .where(StartupProcessingStatus.id == entity_id)
            .values(
                status=PipelineStatus.RUNNING,
                current_stage=stage,
                retry_count=StartupProcessingStatus.retry_count + 1
            )
        )
        self.db.execute(statement)
        self.db.flush()


class StartupIntelligenceProfileVersionRepository(BaseRepository[StartupIntelligenceProfileVersion]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, StartupIntelligenceProfileVersion)

    def create_version(self, profile_id: UUID, snapshot: dict, created_by: UUID | None = None) -> StartupIntelligenceProfileVersion:
        latest = self.latest_version(profile_id)
        next_num = (latest.version_number + 1) if latest else 1
        version = StartupIntelligenceProfileVersion(
            profile_id=profile_id,
            version_number=next_num,
            profile_snapshot=snapshot,
            created_by=created_by
        )
        return self.add(version)

    def load_version(self, profile_id: UUID, version_number: int) -> StartupIntelligenceProfileVersion | None:
        statement = select(StartupIntelligenceProfileVersion).where(
            StartupIntelligenceProfileVersion.profile_id == profile_id,
            StartupIntelligenceProfileVersion.version_number == version_number
        )
        return self.db.scalar(statement)

    def list_versions(self, profile_id: UUID) -> Sequence[StartupIntelligenceProfileVersion]:
        statement = select(StartupIntelligenceProfileVersion).where(
            StartupIntelligenceProfileVersion.profile_id == profile_id
        ).order_by(StartupIntelligenceProfileVersion.version_number.desc())
        return self.db.scalars(statement).all()

    def latest_version(self, profile_id: UUID) -> StartupIntelligenceProfileVersion | None:
        statement = select(StartupIntelligenceProfileVersion).where(
            StartupIntelligenceProfileVersion.profile_id == profile_id
        ).order_by(StartupIntelligenceProfileVersion.version_number.desc()).limit(1)
        return self.db.scalar(statement)
