"""Tests for TIDES AI Batch Assessment and Ranking System."""
from collections.abc import Generator
from types import SimpleNamespace
from uuid import UUID, uuid4

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
from app.modules.startup_profiles.models import AIAssessmentRecord
from app.services.ai import MockAIGateway


# ---------------------------------------------------------------------------
# Response Factory for custom score testing
# ---------------------------------------------------------------------------

def _mock_response_factory(request) -> dict:
    prompt = request.user_prompt
    overall_score = 50
    innovation_score = 5
    market_score = 5
    execution_score = 5

    if "StartupA" in prompt:
        overall_score = 90
        innovation_score = 9
        market_score = 9
        execution_score = 9
    elif "StartupB" in prompt:
        overall_score = 75
        innovation_score = 7
        market_score = 8
        execution_score = 7
    elif "StartupC" in prompt:
        overall_score = 45
        innovation_score = 4
        market_score = 5
        execution_score = 4
    elif "FailStartup" in prompt:
        # Cause an exception to test failure handling
        raise ValueError("Simulated AI assessment failure")

    return {
        "executive_summary": "Mocked executive summary.",
        "innovation_score": innovation_score,
        "market_score": market_score,
        "execution_score": execution_score,
        "overall_score": overall_score,
        "strengths": ["Mock strength"],
        "weaknesses": ["Mock weakness"],
        "recommendations": ["Mock recommendation"],
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
    fake_user = SimpleNamespace(
        id=uuid4(),
        is_active=True,
        role=SimpleNamespace(name="admin"),
    )

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    def _override_get_current_user():
        return fake_user

    # Patch the AI gateway to use our dynamic mock factory
    def _override_agent_init(self, db):
        self.db = db
        self.gateway = MockAIGateway(response_factory=_mock_response_factory)

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

def _create_startup(client: TestClient, name: str) -> dict:
    response = client.post(
        "/api/v1/startups",
        json={
            "startup_name": name,
            "sector": "CleanTech",
            "stage": "MVP",
            "problem_statement": f"Problem description for {name}",
            "solution_summary": f"Solution summary for {name}",
            "target_market": f"Target market for {name}",
            "business_model": "SaaS",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_bulk_assessment_success(client: TestClient, db_session: Session) -> None:
    """POST /bulk-assess successfully processes multiple startups."""
    s1 = _create_startup(client, "StartupA")
    s2 = _create_startup(client, "StartupB")
    
    payload = {
        "startup_ids": [s1["id"], s2["id"]]
    }
    
    response = client.post("/api/v1/startups/bulk-assess", json=payload)
    assert response.status_code == 200, response.text
    
    body = response.json()
    assert body["processed"] == 2
    assert body["successful"] == 2
    assert body["failed"] == 0
    assert len(body["errors"]) == 0


def test_bulk_assessment_partial_failure(client: TestClient, db_session: Session) -> None:
    """POST /bulk-assess handles partial failures gracefully, processing valid ones."""
    s1 = _create_startup(client, "StartupA")
    s_fail = _create_startup(client, "FailStartup")
    s2 = _create_startup(client, "StartupB")

    payload = {
        "startup_ids": [s1["id"], s_fail["id"], s2["id"]]
    }

    response = client.post("/api/v1/startups/bulk-assess", json=payload)
    assert response.status_code == 200, response.text

    body = response.json()
    assert body["processed"] == 3
    assert body["successful"] == 2
    assert body["failed"] == 1
    assert len(body["errors"]) == 1
    assert body["errors"][0]["startup_id"] == s_fail["id"]
    assert "Simulated AI assessment failure" in body["errors"][0]["error"]


def test_recommendation_status_assignment(client: TestClient, db_session: Session) -> None:
    """Recommendation status is correctly assigned based on the overall score thresholds."""
    s1 = _create_startup(client, "StartupA")  # Score 90 -> recommended
    s2 = _create_startup(client, "StartupB")  # Score 75 -> review
    s3 = _create_startup(client, "StartupC")  # Score 45 -> rejected

    payload = {
        "startup_ids": [s1["id"], s2["id"], s3["id"]]
    }

    client.post("/api/v1/startups/bulk-assess", json=payload)

    # Check database records
    rec1 = db_session.query(AIAssessmentRecord).filter(AIAssessmentRecord.startup_id == UUID(s1["id"])).one()
    rec2 = db_session.query(AIAssessmentRecord).filter(AIAssessmentRecord.startup_id == UUID(s2["id"])).one()
    rec3 = db_session.query(AIAssessmentRecord).filter(AIAssessmentRecord.startup_id == UUID(s3["id"])).one()

    assert rec1.recommendation_status == "recommended"
    assert rec2.recommendation_status == "review"
    assert rec3.recommendation_status == "rejected"


def test_rankings_ordering(client: TestClient) -> None:
    """GET /rankings returns startups sorted descending by their latest assessment score."""
    s1 = _create_startup(client, "StartupA")  # Score 90
    s2 = _create_startup(client, "StartupB")  # Score 75
    s3 = _create_startup(client, "StartupC")  # Score 45

    payload = {
        "startup_ids": [s3["id"], s1["id"], s2["id"]]
    }
    client.post("/api/v1/startups/bulk-assess", json=payload)

    response = client.get("/api/v1/startups/rankings")
    assert response.status_code == 200, response.text

    rankings = response.json()
    assert len(rankings) == 3
    
    # Verify descending score sorting and ranking fields
    assert rankings[0]["startup_id"] == s1["id"]
    assert rankings[0]["rank"] == 1
    assert rankings[0]["overall_score"] == 90
    assert rankings[0]["recommendation_status"] == "recommended"

    assert rankings[1]["startup_id"] == s2["id"]
    assert rankings[1]["rank"] == 2
    assert rankings[1]["overall_score"] == 73
    assert rankings[1]["recommendation_status"] == "review"

    assert rankings[2]["startup_id"] == s3["id"]
    assert rankings[2]["rank"] == 3
    assert rankings[2]["overall_score"] == 43
    assert rankings[2]["recommendation_status"] == "rejected"


def test_top_startups_endpoint(client: TestClient) -> None:
    """GET /top return only the top-N startups sorted descending by score."""
    s1 = _create_startup(client, "StartupA")  # Score 90
    s2 = _create_startup(client, "StartupB")  # Score 75
    s3 = _create_startup(client, "StartupC")  # Score 45

    payload = {
        "startup_ids": [s3["id"], s1["id"], s2["id"]]
    }
    client.post("/api/v1/startups/bulk-assess", json=payload)

    # Default limit is 10, but we specify limit=2
    response = client.get("/api/v1/startups/top?limit=2")
    assert response.status_code == 200, response.text

    top_startups = response.json()
    assert len(top_startups) == 2
    assert top_startups[0]["startup_id"] == s1["id"]
    assert top_startups[0]["overall_score"] == 90
    assert top_startups[1]["startup_id"] == s2["id"]
    assert top_startups[1]["overall_score"] == 73


def test_dashboard_summary_counts(client: TestClient) -> None:
    """GET /dashboard/summary returns correct aggregate counts for latest assessments."""
    s1 = _create_startup(client, "StartupA")  # Score 90 -> recommended
    s2 = _create_startup(client, "StartupB")  # Score 75 -> review
    s3 = _create_startup(client, "StartupC")  # Score 45 -> rejected
    # s4 is never assessed
    s4 = _create_startup(client, "StartupD")

    payload = {
        "startup_ids": [s1["id"], s2["id"], s3["id"]]
    }
    client.post("/api/v1/startups/bulk-assess", json=payload)

    response = client.get("/api/v1/dashboard/summary")
    assert response.status_code == 200, response.text

    summary = response.json()
    assert summary["total_startups"] == 4
    assert summary["recommended"] == 1
    assert summary["review"] == 1
    assert summary["rejected"] == 1


def test_bulk_status_update(client: TestClient, db_session: Session) -> None:
    """POST /api/v1/startups/bulk-status successfully updates status for multiple startups and creates history."""
    s1 = _create_startup(client, "StartupX")
    s2 = _create_startup(client, "StartupY")
    
    payload = {
        "startup_ids": [s1["id"], s2["id"]],
        "new_status": "Under Review",
        "reason": "Moved to committee review by test"
    }
    
    response = client.post("/api/v1/startups/bulk-status", json=payload)
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "success"
    assert response.json()["count"] == 2
    
    # Check updated statuses in DB
    from app.modules.startups.models import StartupApplication
    from uuid import UUID
    startup1 = db_session.query(StartupApplication).filter(StartupApplication.id == UUID(s1["id"])).one()
    startup2 = db_session.query(StartupApplication).filter(StartupApplication.id == UUID(s2["id"])).one()
    assert startup1.current_status.value == "Under Review"
    assert startup2.current_status.value == "Under Review"


def test_delete_startup_forbidden_for_evaluator(db_session: Session) -> None:
    # Set up client with evaluator user
    fake_evaluator = SimpleNamespace(
        id=uuid4(),
        is_active=True,
        role=SimpleNamespace(name="evaluator"),
    )
    
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: fake_evaluator
    
    local_client = TestClient(app)
    
    try:
        # Create a startup
        startup = _create_startup(local_client, "StartupForbiddenTest")
        
        # Try to delete
        response = local_client.delete(f"/api/v1/startups/{startup['id']}")
        assert response.status_code == 403
        assert "Insufficient permissions" in response.text
    finally:
        app.dependency_overrides.clear()


def test_delete_startup_cascading_success(client: TestClient, db_session: Session) -> None:
    from app.modules.startups.models import StartupApplication, StartupStatusHistory
    from app.modules.startup_profiles.models import StartupProfile, StartupProfileVersion, AIAssessmentRecord
    from app.modules.founders.models import Founder
    from app.modules.company_profiles.models import CompanyProfile
    from app.modules.documents.models import Document, DocumentSource
    from app.modules.evaluations.models import Evaluation, EvaluationScore, EvaluationEvidence, EvaluationRubric
    from app.modules.reviews.models import ReviewerComment, CommitteeNote, ScoreOverride
    from uuid import UUID

    # 1. Create a startup
    startup = _create_startup(client, "StartupDeleteTest")
    startup_uuid = UUID(startup["id"])
    
    # 2. Add dependent models manually to DB session
    rubric = EvaluationRubric(name="Rubric1", version="1.0", is_active=True)
    db_session.add(rubric)
    db_session.flush()
    
    profile = StartupProfile(startup_id=startup_uuid, problem_statement="Problem")
    db_session.add(profile)
    db_session.flush()
    
    version = StartupProfileVersion(startup_profile_id=profile.id, version_number=1, profile_snapshot={})
    db_session.add(version)
    
    founder = Founder(startup_id=startup_uuid, name="Founder Name")
    db_session.add(founder)
    
    comp_profile = CompanyProfile(startup_id=startup_uuid, website="https://example.com")
    db_session.add(comp_profile)
    
    doc = Document(startup_id=startup_uuid, document_type="pitch_deck", original_filename="pitch.pdf", stored_filename="pitch.pdf", file_path="/tmp/pitch.pdf", file_size=123)
    db_session.add(doc)
    db_session.flush()
    
    source = DocumentSource(startup_id=startup_uuid, document_id=doc.id, source_name="Pitch Deck", source_type="pdf")
    db_session.add(source)
    db_session.flush()
    
    ai_record = AIAssessmentRecord(
        startup_id=startup_uuid, executive_summary="Summary",
        innovation_score=8, market_score=8, execution_score=8, overall_score=80,
        strengths=[], weaknesses=[], recommendations=[], recommendation_status="recommended"
    )
    db_session.add(ai_record)
    
    evaluation = Evaluation(startup_id=startup_uuid, rubric_id=rubric.id, startup_profile_version_id=version.id, status="created", overall_score=80.0)
    db_session.add(evaluation)
    db_session.flush()
    
    from app.modules.evaluations.models import EvaluationCriterion
    criterion = EvaluationCriterion(rubric_id=rubric.id, name="Innovation", weight=1.0, max_score=10)
    db_session.add(criterion)
    db_session.flush()
    
    score = EvaluationScore(evaluation_id=evaluation.id, criteria_id=criterion.id, ai_score=8.0, final_score=8.0)
    db_session.add(score)
    db_session.flush()
    
    evidence = EvaluationEvidence(evaluation_score_id=score.id, evidence_text="Evidence text", source_type="pdf", source_id=source.id, confidence=0.9)
    db_session.add(evidence)
    
    comment = ReviewerComment(startup_id=startup_uuid, evaluation_id=evaluation.id, comment="Good startup")
    note = CommitteeNote(startup_id=startup_uuid, evaluation_id=evaluation.id, note="Review note")
    db_session.add(comment)
    db_session.add(note)
    
    override = ScoreOverride(evaluation_score_id=score.id, original_score=8.0, overridden_score=9.0, reason="Reason")
    db_session.add(override)
    
    db_session.commit()
    
    # Verify records exist in DB
    assert db_session.query(StartupApplication).filter_by(id=startup_uuid).count() == 1
    assert db_session.query(StartupProfile).filter_by(startup_id=startup_uuid).count() == 1
    assert db_session.query(Founder).filter_by(startup_id=startup_uuid).count() == 1
    assert db_session.query(CompanyProfile).filter_by(startup_id=startup_uuid).count() == 1
    assert db_session.query(Document).filter_by(startup_id=startup_uuid).count() == 1
    assert db_session.query(DocumentSource).filter_by(startup_id=startup_uuid).count() == 1
    assert db_session.query(AIAssessmentRecord).filter_by(startup_id=startup_uuid).count() == 1
    assert db_session.query(Evaluation).filter_by(startup_id=startup_uuid).count() == 1
    assert db_session.query(ReviewerComment).filter_by(startup_id=startup_uuid).count() == 1
    assert db_session.query(CommitteeNote).filter_by(startup_id=startup_uuid).count() == 1
    assert db_session.query(StartupStatusHistory).filter_by(startup_id=startup_uuid).count() > 0
    
    # 3. Call delete endpoint
    response = client.delete(f"/api/v1/startups/{startup['id']}")
    assert response.status_code == 200, response.text
    assert response.json() == {"success": True, "message": "Startup deleted successfully"}
    
    # 4. Verify all records are deleted
    assert db_session.query(StartupApplication).filter_by(id=startup_uuid).count() == 0
    assert db_session.query(StartupProfile).filter_by(startup_id=startup_uuid).count() == 0
    assert db_session.query(StartupProfileVersion).filter_by(startup_profile_id=profile.id).count() == 0
    assert db_session.query(Founder).filter_by(startup_id=startup_uuid).count() == 0
    assert db_session.query(CompanyProfile).filter_by(startup_id=startup_uuid).count() == 0
    assert db_session.query(Document).filter_by(startup_id=startup_uuid).count() == 0
    assert db_session.query(DocumentSource).filter_by(startup_id=startup_uuid).count() == 0
    assert db_session.query(AIAssessmentRecord).filter_by(startup_id=startup_uuid).count() == 0
    assert db_session.query(Evaluation).filter_by(startup_id=startup_uuid).count() == 0
    assert db_session.query(EvaluationScore).filter_by(evaluation_id=evaluation.id).count() == 0
    assert db_session.query(EvaluationEvidence).filter_by(evaluation_score_id=score.id).count() == 0
    assert db_session.query(ReviewerComment).filter_by(startup_id=startup_uuid).count() == 0
    assert db_session.query(CommitteeNote).filter_by(startup_id=startup_uuid).count() == 0
    assert db_session.query(ScoreOverride).filter_by(evaluation_score_id=score.id).count() == 0
    assert db_session.query(StartupStatusHistory).filter_by(startup_id=startup_uuid).count() == 0


def test_bulk_delete_startups_success(client: TestClient, db_session: Session) -> None:
    from app.modules.startups.models import StartupApplication
    from uuid import UUID

    s1 = _create_startup(client, "StartupDelete1")
    s2 = _create_startup(client, "StartupDelete2")
    
    # Verify they exist
    assert db_session.query(StartupApplication).filter(StartupApplication.id.in_([UUID(s1["id"]), UUID(s2["id"])])).count() == 2
    
    # Bulk delete
    response = client.post("/api/v1/startups/bulk-delete", json={"startup_ids": [s1["id"], s2["id"]]})
    assert response.status_code == 200, response.text
    assert response.json() == {"success": True, "message": "Startups deleted successfully"}
    
    # Verify they are gone
    assert db_session.query(StartupApplication).filter(StartupApplication.id.in_([UUID(s1["id"]), UUID(s2["id"])])).count() == 0
