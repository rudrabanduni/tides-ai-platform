"""Tests for evaluation persistence and GET /startups/{startup_id}/evaluations."""
from collections.abc import Generator
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.startup_profiles.agent import StartupProfileAgentService
from app.modules.startup_profiles.models import AIAssessmentRecord
from app.services.ai import MockAIGateway

# ---------------------------------------------------------------------------
# Fixed AI response
# ---------------------------------------------------------------------------

_FIXED_AI_RESPONSE = {
    "executive_summary": "A promising CleanTech startup targeting industrial energy users.",
    "innovation_score": 8,
    "market_score": 7,
    "execution_score": 5,
    "overall_score": 20,
    "strengths": ["Clear solution", "Defined market"],
    "weaknesses": ["No traction data"],
    "recommendations": ["Run a pilot"],
}

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    Base.metadata.create_all(engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def client(db_session: Session) -> Generator[TestClient, None, None]:
    fake_user = SimpleNamespace(id=uuid4(), is_active=True, role=SimpleNamespace(name="admin"))

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def _override_get_current_user():
        return fake_user

    def _override_agent_init(self, db) -> None:  # noqa: ANN001
        self.db = db
        self.gateway = MockAIGateway(fixed_response=_FIXED_AI_RESPONSE)

    original_init = StartupProfileAgentService.__init__
    StartupProfileAgentService.__init__ = _override_agent_init

    app.dependency_overrides[get_db] = _override_get_db
    app.dependency_overrides[get_current_user] = _override_get_current_user
    try:
        yield TestClient(app)
    finally:
        StartupProfileAgentService.__init__ = original_init
        app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _create_startup(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/startups",
        json={
            "startup_name": "GridAI",
            "sector": "CleanTech",
            "stage": "MVP",
            "problem_statement": "Grid storage is expensive.",
            "solution_summary": "AI-driven battery analytics.",
            "target_market": "Industrial energy users",
            "business_model": "SaaS",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# Persistence tests
# ---------------------------------------------------------------------------


def test_assess_startup_persists_record(client: TestClient, db_session: Session) -> None:
    """After POST /assess, an AIAssessmentRecord must exist in the DB."""
    startup = _create_startup(client)
    startup_id = startup["id"]

    response = client.post(f"/api/v1/startups/{startup_id}/assess")

    assert response.status_code == 200, response.text

    records = db_session.scalars(
        select(AIAssessmentRecord).where(AIAssessmentRecord.startup_id == UUID(startup_id))
    ).all()
    assert len(records) == 1


def test_assess_startup_persisted_record_has_correct_fields(client: TestClient, db_session: Session) -> None:
    """The persisted record must store all required fields from the AI evaluation."""
    startup = _create_startup(client)
    startup_id = startup["id"]

    client.post(f"/api/v1/startups/{startup_id}/assess")

    record = db_session.scalars(
        select(AIAssessmentRecord).where(AIAssessmentRecord.startup_id == UUID(startup_id))
    ).one()

    assert record.executive_summary == _FIXED_AI_RESPONSE["executive_summary"]
    assert record.innovation_score == _FIXED_AI_RESPONSE["innovation_score"]
    assert record.market_score == _FIXED_AI_RESPONSE["market_score"]
    assert record.execution_score == _FIXED_AI_RESPONSE["execution_score"]
    assert record.overall_score == 67
    assert record.strengths == _FIXED_AI_RESPONSE["strengths"]
    assert record.weaknesses == _FIXED_AI_RESPONSE["weaknesses"]
    assert record.recommendations == _FIXED_AI_RESPONSE["recommendations"]


def test_assess_startup_multiple_calls_persist_multiple_records(
    client: TestClient, db_session: Session
) -> None:
    """Each call to POST /assess creates a new separate history record."""
    startup = _create_startup(client)
    startup_id = startup["id"]

    client.post(f"/api/v1/startups/{startup_id}/assess")
    client.post(f"/api/v1/startups/{startup_id}/assess")

    records = db_session.scalars(
        select(AIAssessmentRecord).where(AIAssessmentRecord.startup_id == UUID(startup_id))
    ).all()
    assert len(records) == 2


def test_assess_startup_persists_assessed_by(client: TestClient, db_session: Session) -> None:
    """The persisted record must capture the assessor user ID."""
    startup = _create_startup(client)
    startup_id = startup["id"]

    client.post(f"/api/v1/startups/{startup_id}/assess")

    record = db_session.scalars(
        select(AIAssessmentRecord).where(AIAssessmentRecord.startup_id == UUID(startup_id))
    ).one()

    assert record.assessed_by is not None


# ---------------------------------------------------------------------------
# Evaluation history endpoint tests
# ---------------------------------------------------------------------------


def test_list_evaluations_returns_empty_list_before_any_assessment(client: TestClient) -> None:
    """GET /evaluations on a startup with no assessments must return []."""
    startup = _create_startup(client)
    startup_id = startup["id"]

    response = client.get(f"/api/v1/startups/{startup_id}/evaluations")

    assert response.status_code == 200, response.text
    assert response.json() == []


def test_list_evaluations_returns_record_after_assessment(client: TestClient) -> None:
    """GET /evaluations returns one record after one POST /assess call."""
    startup = _create_startup(client)
    startup_id = startup["id"]

    client.post(f"/api/v1/startups/{startup_id}/assess")
    response = client.get(f"/api/v1/startups/{startup_id}/evaluations")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    record = data[0]
    assert record["startup_id"] == startup_id
    assert record["executive_summary"] == _FIXED_AI_RESPONSE["executive_summary"]
    assert record["innovation_score"] == _FIXED_AI_RESPONSE["innovation_score"]
    assert record["market_score"] == _FIXED_AI_RESPONSE["market_score"]
    assert record["execution_score"] == _FIXED_AI_RESPONSE["execution_score"]
    assert record["overall_score"] == 67
    assert record["strengths"] == _FIXED_AI_RESPONSE["strengths"]
    assert record["weaknesses"] == _FIXED_AI_RESPONSE["weaknesses"]
    assert record["recommendations"] == _FIXED_AI_RESPONSE["recommendations"]


def test_list_evaluations_returns_history_newest_first(client: TestClient) -> None:
    """GET /evaluations returns records in descending created_at order."""
    startup = _create_startup(client)
    startup_id = startup["id"]

    client.post(f"/api/v1/startups/{startup_id}/assess")
    client.post(f"/api/v1/startups/{startup_id}/assess")

    response = client.get(f"/api/v1/startups/{startup_id}/evaluations")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Newest first: created_at of first item >= second item
    assert data[0]["created_at"] >= data[1]["created_at"]


def test_list_evaluations_not_found_for_missing_startup(client: TestClient) -> None:
    """GET /evaluations returns 404 for a non-existent startup."""
    missing_id = uuid4()
    response = client.get(f"/api/v1/startups/{missing_id}/evaluations")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_list_evaluations_response_schema_is_valid(client: TestClient) -> None:
    """GET /evaluations response includes all required schema fields."""
    startup = _create_startup(client)
    startup_id = startup["id"]

    client.post(f"/api/v1/startups/{startup_id}/assess")
    response = client.get(f"/api/v1/startups/{startup_id}/evaluations")

    assert response.status_code == 200
    record = response.json()[0]
    required_fields = {
        "id",
        "startup_id",
        "executive_summary",
        "innovation_score",
        "market_score",
        "execution_score",
        "overall_score",
        "strengths",
        "weaknesses",
        "recommendations",
        "assessed_by",
        "created_at",
    }
    assert required_fields.issubset(record.keys())
