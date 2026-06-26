from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.modules.startup_profiles.models import AIAssessmentRecord, StartupProfile, StartupProfileVersion
from app.modules.startups.models import StartupApplication
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

    def latest_for_startup(self, startup_id: UUID) -> AIAssessmentRecord | None:
        """Return the most recent assessment record for a startup, or None."""
        statement = (
            select(AIAssessmentRecord)
            .where(AIAssessmentRecord.startup_id == startup_id)
            .order_by(AIAssessmentRecord.created_at.desc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def ranked_startups(self, limit: int = 100) -> list[dict]:
        """Return startups ranked by their latest overall_score (descending).

        Uses a correlated subquery to find the latest assessment per startup
        and joins to startup_applications for the name.

        Returns a list of dicts with keys:
            startup_id, startup_name, overall_score, recommendation_status
        """
        # Subquery: latest created_at per startup_id
        latest_ts_sub = (
            select(
                AIAssessmentRecord.startup_id,
                func.max(AIAssessmentRecord.created_at).label("max_ts"),
            )
            .group_by(AIAssessmentRecord.startup_id)
            .subquery("latest_ts")
        )

        # Join back to get the full record for that timestamp
        latest_record_sub = (
            select(AIAssessmentRecord)
            .join(
                latest_ts_sub,
                (AIAssessmentRecord.startup_id == latest_ts_sub.c.startup_id)
                & (AIAssessmentRecord.created_at == latest_ts_sub.c.max_ts),
            )
            .subquery("latest_record")
        )

        # Join to startup_applications to get the name
        statement = (
            select(
                StartupApplication.id.label("startup_id"),
                StartupApplication.startup_name,
                latest_record_sub.c.overall_score,
                latest_record_sub.c.recommendation_status,
            )
            .join(
                latest_record_sub,
                StartupApplication.id == latest_record_sub.c.startup_id,
            )
            .order_by(latest_record_sub.c.overall_score.desc())
            .limit(limit)
        )

        rows = self.db.execute(statement).all()
        return [
            {
                "startup_id": row.startup_id,
                "startup_name": row.startup_name,
                "overall_score": row.overall_score,
                "recommendation_status": row.recommendation_status,
            }
            for row in rows
        ]

    def dashboard_counts(self) -> dict:
        """Return aggregate counts for the dashboard summary.

        Returns:
            dict with keys: total_startups, assessed, recommended, review,
            rejected, unassessed, approved_startups, pending_committee_review,
            ai_recommended, final_rejected.
        """
        # Total startups in the system
        total_startups = self.db.scalar(
            select(func.count()).select_from(StartupApplication)
        ) or 0

        # Subquery: latest record per startup
        latest_ts_sub = (
            select(
                AIAssessmentRecord.startup_id,
                func.max(AIAssessmentRecord.created_at).label("max_ts"),
            )
            .group_by(AIAssessmentRecord.startup_id)
            .subquery("dash_latest_ts")
        )

        latest_records = (
            select(AIAssessmentRecord.recommendation_status)
            .join(
                latest_ts_sub,
                (AIAssessmentRecord.startup_id == latest_ts_sub.c.startup_id)
                & (AIAssessmentRecord.created_at == latest_ts_sub.c.max_ts),
            )
            .subquery("dash_latest_records")
        )

        statuses = self.db.scalars(select(latest_records.c.recommendation_status)).all()

        recommended = sum(1 for s in statuses if s == "recommended")
        review = sum(1 for s in statuses if s == "review")
        rejected = sum(1 for s in statuses if s == "rejected")
        assessed = recommended + review + rejected

        # Count committee statuses from StartupApplication
        from app.core.enums import StartupStatus
        approved_startups = self.db.scalar(
            select(func.count())
            .select_from(StartupApplication)
            .where(StartupApplication.current_status == StartupStatus.APPROVED_FOR_INCUBATION)
        ) or 0
        
        pending_committee_review = self.db.scalar(
            select(func.count())
            .select_from(StartupApplication)
            .where(StartupApplication.current_status == StartupStatus.UNDER_REVIEW)
        ) or 0

        final_rejected = self.db.scalar(
            select(func.count())
            .select_from(StartupApplication)
            .where(StartupApplication.current_status == StartupStatus.REJECTED)
        ) or 0

        ai_recommended = recommended

        return {
            "total_startups": total_startups,
            "assessed": assessed,
            "recommended": recommended,
            "review": review,
            "rejected": rejected,
            "unassessed": total_startups - assessed,
            "approved_startups": approved_startups,
            "pending_committee_review": pending_committee_review,
            "ai_recommended": ai_recommended,
            "final_rejected": final_rejected,
        }
