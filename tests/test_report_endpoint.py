"""Tests for GET /api/v1/startups/{startup_id}/report (PDF download)."""
from __future__ import annotations

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
from app.services.ai import MockAIGateway

# ---------------------------------------------------------------------------
# Fixed AI response (identical to other test modules for consistency)
# ---------------------------------------------------------------------------

_FIXED_AI_RESPONSE = {
    "executive_summary": "GridAI is a strong AI-driven cleantech startup.",
    "innovation_score": 8,
    "market_score": 7,
    "execution_score": 5,
    "overall_score": 20,
    "strengths": ["Clear solution", "Defined market"],
    "weaknesses": ["No traction data"],
    "recommendations": ["Run a pilot programme"],
}

# ---------------------------------------------------------------------------
# Fixtures (same pattern as test_evaluate_persistence.py)
# ---------------------------------------------------------------------------


@pytest.fixture()
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine, autoflush=False, autocommit=False, expire_on_commit=False
    )
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
        id=uuid4(), is_active=True, role=SimpleNamespace(name="admin")
    )

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
# Helpers
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


def _assess(client: TestClient, startup_id: str) -> None:
    resp = client.post(f"/api/v1/startups/{startup_id}/assess")
    assert resp.status_code == 200, resp.text


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_report_returns_pdf_content_type(client: TestClient) -> None:
    """GET /report after an assessment returns a PDF content-type header."""
    startup = _create_startup(client)
    _assess(client, startup["id"])

    response = client.get(f"/api/v1/startups/{startup['id']}/report")

    assert response.status_code == 200, response.text
    assert response.headers["content-type"] == "application/pdf"


def test_report_response_is_non_empty_bytes(client: TestClient) -> None:
    """The downloaded PDF must contain actual bytes."""
    startup = _create_startup(client)
    _assess(client, startup["id"])

    response = client.get(f"/api/v1/startups/{startup['id']}/report")

    assert response.status_code == 200
    assert len(response.content) > 0


def test_report_content_disposition_header(client: TestClient) -> None:
    """Content-Disposition must be attachment with the startup_id filename."""
    startup = _create_startup(client)
    _assess(client, startup["id"])

    response = client.get(f"/api/v1/startups/{startup['id']}/report")

    assert response.status_code == 200
    disposition = response.headers.get("content-disposition", "")
    assert "attachment" in disposition
    assert startup["id"] in disposition


def test_report_pdf_starts_with_pdf_magic_bytes(client: TestClient) -> None:
    """The returned bytes must begin with the PDF magic header %%PDF."""
    startup = _create_startup(client)
    _assess(client, startup["id"])

    response = client.get(f"/api/v1/startups/{startup['id']}/report")

    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"


def test_report_returns_404_when_no_assessment_exists(client: TestClient) -> None:
    """GET /report before any assessment must return 404."""
    startup = _create_startup(client)

    response = client.get(f"/api/v1/startups/{startup['id']}/report")

    assert response.status_code == 404
    assert "assessment" in response.json()["detail"].lower()


def test_report_returns_404_for_unknown_startup(client: TestClient) -> None:
    """GET /report for a non-existent startup must return 404."""
    missing_id = uuid4()
    response = client.get(f"/api/v1/startups/{missing_id}/report")

    assert response.status_code == 404


def test_report_uses_latest_assessment(client: TestClient) -> None:
    """Calling /assess twice then /report should always return a valid PDF."""
    startup = _create_startup(client)
    _assess(client, startup["id"])
    _assess(client, startup["id"])  # second assessment

    response = client.get(f"/api/v1/startups/{startup['id']}/report")

    assert response.status_code == 200
    assert response.content[:4] == b"%PDF"
