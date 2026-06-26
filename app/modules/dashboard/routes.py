"""Dashboard summary endpoints."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import ReadOnlyUser
from app.modules.startup_profiles.repository import AIAssessmentRecordRepository
from app.modules.startup_profiles.schemas import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def get_dashboard_summary(
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
) -> DashboardSummary:
    """Return aggregate assessment counts for the incubator dashboard.

    Uses the *latest* assessment per startup to determine its current status.
    Startups that have never been assessed appear in ``unassessed``.
    """
    counts = AIAssessmentRecordRepository(db).dashboard_counts()
    return DashboardSummary(**counts)
