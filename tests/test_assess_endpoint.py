"""Tests for POST /api/v1/startups/{startup_id}/assess endpoint."""
from collections.abc import Generator
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.modules.auth.dependencies import get_current_user
from app.modules.startup_profiles.agent import StartupProfileAgentService
from app.modules.startup_profiles.schemas import StartupAssessmentResult
from app.services.ai import MockAIGateway

# ---------------------------------------------------------------------------
# Fixed AI response matching StartupEvaluationOutput schema
# ---------------------------------------------------------------------------

_FIXED_AI_RESPONSE = {
    "executive_summary": "A promising AI startup targeting industrial energy users.",
    "innovation_score": 8,
    "market_score": 7,
    "execution_score": 5,
    "overall_score": 20,
    "strengths": ["Clear solution", "Defined market"],
    "weaknesses": ["No traction data"],
    "recommendations": ["Run a pilot programme"],
}


# ---------------------------------------------------------------------------
# Shared fixtures
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
    fake_user = SimpleNamespace(
        id=uuid4(),
        is_active=True,
        role=SimpleNamespace(name="admin"),
    )

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def _override_get_current_user():
        return fake_user

    # Patch the AI gateway so the endpoint never touches a real LLM
    def _override_agent_init(self, db):  # noqa: ANN001
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
# Helpers
# ---------------------------------------------------------------------------


def _create_startup(client: TestClient) -> dict:
    """Create a startup via the API and return the parsed JSON body."""
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
# Tests
# ---------------------------------------------------------------------------


def test_assess_startup_successful(client: TestClient) -> None:
    """POST /assess on a valid startup returns 200 with a StartupAssessmentResult."""
    startup = _create_startup(client)
    startup_id = startup["id"]

    response = client.post(f"/api/v1/startups/{startup_id}/assess")

    assert response.status_code == 200, response.text
    body = response.json()

    # Top-level keys must all be present
    assert "profile" in body
    assert "rule_based_score" in body
    assert "ai_evaluation" in body


def test_assess_startup_profile_contains_startup_name(client: TestClient) -> None:
    """The profile section of the response should mention the startup name."""
    startup = _create_startup(client)
    startup_id = startup["id"]

    response = client.post(f"/api/v1/startups/{startup_id}/assess")

    assert response.status_code == 200
    profile = response.json()["profile"]
    assert "GridAI" in profile["executive_summary"]


def test_assess_startup_rule_based_score_shape(client: TestClient) -> None:
    """The rule_based_score section must include all score fields and a rationale list."""
    startup = _create_startup(client)
    startup_id = startup["id"]

    response = client.post(f"/api/v1/startups/{startup_id}/assess")

    assert response.status_code == 200
    score = response.json()["rule_based_score"]
    for field in ("innovation_score", "market_score", "execution_score", "overall_score", "rationale"):
        assert field in score, f"Missing field: {field}"
    assert isinstance(score["rationale"], list)


def test_assess_startup_ai_evaluation_shape(client: TestClient) -> None:
    """The ai_evaluation section must match the StartupEvaluationOutput contract."""
    startup = _create_startup(client)
    startup_id = startup["id"]

    response = client.post(f"/api/v1/startups/{startup_id}/assess")

    assert response.status_code == 200
    ai_eval = response.json()["ai_evaluation"]
    for field in (
        "executive_summary",
        "innovation_score",
        "market_score",
        "execution_score",
        "overall_score",
        "strengths",
        "weaknesses",
        "recommendations",
    ):
        assert field in ai_eval, f"Missing field: {field}"

    # Values should come from _FIXED_AI_RESPONSE (via MockAIGateway)
    assert ai_eval["innovation_score"] == 8
    assert ai_eval["market_score"] == 7
    assert ai_eval["overall_score"] == 67
    assert "Clear solution" in ai_eval["strengths"]


def test_assess_startup_not_found_returns_404(client: TestClient) -> None:
    """Requesting assessment for a non-existent startup_id must return 404."""
    missing_id = uuid4()
    response = client.post(f"/api/v1/startups/{missing_id}/assess")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_assess_startup_response_validates_against_schema(client: TestClient) -> None:
    """The full JSON response must deserialise cleanly into StartupAssessmentResult."""
    startup = _create_startup(client)
    startup_id = startup["id"]

    response = client.post(f"/api/v1/startups/{startup_id}/assess")

    assert response.status_code == 200
    # Pydantic validation: will raise if structure does not match
    parsed = StartupAssessmentResult.model_validate(response.json())
    assert parsed.rule_based_score.overall_score >= 0
    assert isinstance(parsed.ai_evaluation.strengths, list)
