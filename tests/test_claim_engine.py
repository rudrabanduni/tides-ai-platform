import pytest
from uuid import uuid4
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient

from app.db.base import Base
from app.main import app
from app.db.session import get_db
from app.core.enums import DocumentProcessingStatus, DocumentType
from app.modules.auth.dependencies import get_current_user
from app.modules.documents.models import Document
from app.modules.startups.models import StartupApplication
from app.modules.intelligence.models import StartupIntelligenceProfile, StartupClaim, StartupEvidence, FieldConflict, StartupIntelligenceProfileVersion
from app.modules.intelligence.claim_engine import ClaimEngine, ConfidenceEngine
from app.modules.intelligence.ai.schemas import DocumentExtraction, ExtractedString, ExtractedInt, ExtractedFloat


# --- Mock authentication user for routing tests ---
class SimpleNamespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture()
def db_session() -> Session:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture()
def test_client(db_session: Session) -> TestClient:
    fake_user = SimpleNamespace(
        id=uuid4(),
        is_active=True,
        role=SimpleNamespace(name="viewer"),
    )
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: fake_user
    return TestClient(app)


def test_confidence_calculations() -> None:
    # 1. Pitch deck with evidence
    score, reason = ConfidenceEngine.calculate(0.9, "Pitch Deck", True, "Short evidence")
    assert 0.0 <= score <= 1.0
    assert "Pitch Deck" in reason

    # 2. Financial statement with long evidence
    score_fin, _ = ConfidenceEngine.calculate(0.8, "Financial Statement", True, "A" * 150)
    # 3. Financial statement with no evidence
    score_no_ev, _ = ConfidenceEngine.calculate(0.8, "Financial Statement", False)
    assert score_fin > score_no_ev


def test_claim_evidence_engine(db_session: Session) -> None:
    # 1. Setup startup applications
    startup = StartupApplication(startup_name="Claim Engine Startup", stage="MVP", current_status="Submitted")
    db_session.add(startup)
    db_session.flush()

    # 2. Setup document
    doc = Document(
        startup_id=startup.id,
        document_type=DocumentType.PITCH_DECK,
        original_filename="deck.pdf",
        stored_filename="deck.pdf",
        file_path="mock/deck.pdf",
        file_size=1024,
        processing_status=DocumentProcessingStatus.PARSED
    )
    db_session.add(doc)
    db_session.flush()

    # 3. Setup extraction payload
    extraction = DocumentExtraction()
    extraction.founder.founder_names = ExtractedString(
        value="John Doe", confidence_score=0.9, why_extracted="Relevance", supporting_evidence="John Doe description", document_section="Introduction"
    )
    extraction.technology.trl_level = ExtractedInt(
        value=6, confidence_score=0.8, why_extracted="Technology assessment", supporting_evidence="TRL 6 assessment details", document_section="Technology"
    )
    extraction.financial.revenue_model = ExtractedString(
        value="B2B SaaS", confidence_score=0.85, why_extracted="Financial plan", supporting_evidence="SaaS subscription basis", document_section="Business Model"
    )

    # Execute claim engine
    engine = ClaimEngine(db_session)
    engine.process_extraction(startup.id, extraction, doc.id)

    # Assert profile creation
    profile = engine.profiles.get_by_startup(startup.id)
    assert profile is not None

    # Assert claims are created and validated preferred
    claims = list(engine.claims.list_for_profile(profile.id))
    assert len(claims) == 3
    for claim in claims:
        assert claim.is_preferred is True
        assert claim.validation_status == "VALIDATED"

    # Assert evidence is linked
    trl_claim = next(c for c in claims if c.field.field_key == "trl_level")
    assert trl_claim.value_number == 6.0
    evidences = list(engine.evidence.list_for_claim(trl_claim.id))
    assert len(evidences) == 1
    assert evidences[0].section_name == "Technology"
    assert evidences[0].evidence_snippet == "TRL 6 assessment details"

    # Assert profile version snapshot is created
    version = engine.profile_versions.latest_version(profile.id)
    assert version is not None
    assert version.profile_snapshot["trl_level"] == 6.0
    assert version.profile_snapshot["founder_names"] == "John Doe"


def test_conflict_resolution_strategies(db_session: Session) -> None:
    startup = StartupApplication(startup_name="Conflict Startup", stage="MVP", current_status="Submitted")
    db_session.add(startup)
    db_session.flush()

    doc1 = Document(
        startup_id=startup.id, document_type=DocumentType.PITCH_DECK,
        original_filename="deck1.pdf", stored_filename="deck1.pdf",
        file_path="mock/deck1.pdf", file_size=500,
        processing_status=DocumentProcessingStatus.PARSED
    )
    doc2 = Document(
        startup_id=startup.id, document_type=DocumentType.PITCH_DECK,
        original_filename="deck2.pdf", stored_filename="deck2.pdf",
        file_path="mock/deck2.pdf", file_size=500,
        processing_status=DocumentProcessingStatus.PARSED
    )
    db_session.add(doc1)
    db_session.add(doc2)
    db_session.flush()

    engine = ClaimEngine(db_session)

    # 1. Process first extraction: TRL level = 4 (Confidence 0.6)
    ext1 = DocumentExtraction()
    ext1.technology.trl_level = ExtractedInt(value=4, confidence_score=0.6)
    engine.process_extraction(startup.id, ext1, doc1.id)

    profile = engine.profiles.get_by_startup(startup.id)
    claims1 = list(engine.claims.list_for_profile(profile.id))
    assert len(claims1) == 1
    assert claims1[0].value_number == 4.0
    assert claims1[0].is_preferred is True

    # 2. Process second extraction for same field: TRL level = 6 (Confidence 0.9)
    # Higher confidence should override TRL 4 (ConfidenceMergeStrategy)
    ext2 = DocumentExtraction()
    ext2.technology.trl_level = ExtractedInt(value=6, confidence_score=0.9)
    engine.process_extraction(startup.id, ext2, doc2.id)

    claims2 = list(engine.claims.list_for_profile(profile.id))
    assert len(claims2) == 2
    
    preferred_claim = next(c for c in claims2 if c.is_preferred)
    assert preferred_claim.value_number == 6.0
    
    superseded_claim = next(c for c in claims2 if not c.is_preferred)
    assert superseded_claim.value_number == 4.0
    assert superseded_claim.validation_status == "CONFLICTING"

    # Assert conflict history log is recorded
    conflicts = list(engine.conflicts.list_unresolved_for_profile(profile.id))
    # Automatically resolved, so should not be unresolved
    assert len(conflicts) == 0
    all_conflicts = db_session.query(FieldConflict).filter(FieldConflict.profile_id == profile.id).all()
    assert len(all_conflicts) == 1
    assert all_conflicts[0].resolved is True


def test_conflict_recency_strategy(db_session: Session) -> None:
    startup = StartupApplication(startup_name="Recency Startup", stage="MVP", current_status="Submitted")
    db_session.add(startup)
    db_session.flush()

    doc1 = Document(
        startup_id=startup.id, document_type=DocumentType.COMPANY_DOCUMENT,
        original_filename="financials1.xlsx", stored_filename="financials1.xlsx",
        file_path="mock/financials1.xlsx", file_size=500,
        processing_status=DocumentProcessingStatus.PARSED
    )
    doc2 = Document(
        startup_id=startup.id, document_type=DocumentType.COMPANY_DOCUMENT,
        original_filename="financials2.xlsx", stored_filename="financials2.xlsx",
        file_path="mock/financials2.xlsx", file_size=500,
        processing_status=DocumentProcessingStatus.PARSED
    )
    db_session.add(doc1)
    db_session.add(doc2)
    db_session.flush()

    engine = ClaimEngine(db_session)

    # 1. First financials extraction: funding = 100,000 (Confidence 0.9)
    ext1 = DocumentExtraction()
    ext1.financial.funding_received = ExtractedFloat(value=100000.0, confidence_score=0.9)
    engine.process_extraction(startup.id, ext1, doc1.id)

    # 2. Second financials extraction: funding = 150,000 (Confidence 0.7)
    # RecencyMergeStrategy: newer document overrides older, even if confidence is lower!
    ext2 = DocumentExtraction()
    ext2.financial.funding_received = ExtractedFloat(value=150000.0, confidence_score=0.7)
    engine.process_extraction(startup.id, ext2, doc2.id)

    profile = engine.profiles.get_by_startup(startup.id)
    claims = list(engine.claims.list_for_profile(profile.id))
    assert len(claims) == 2
    preferred = next(c for c in claims if c.is_preferred)
    assert preferred.value_number == 150000.0


def test_routes_queries(db_session: Session, test_client: TestClient) -> None:
    # 1. Setup profile data
    startup = StartupApplication(startup_name="Router Startup", stage="MVP", current_status="Submitted")
    db_session.add(startup)
    db_session.flush()

    doc = Document(
        startup_id=startup.id, document_type=DocumentType.PITCH_DECK,
        original_filename="deck.pdf", stored_filename="deck.pdf",
        file_path="mock/deck.pdf", file_size=500,
        processing_status=DocumentProcessingStatus.PARSED
    )
    db_session.add(doc)
    db_session.flush()

    extraction = DocumentExtraction()
    extraction.technology.trl_level = ExtractedInt(value=4, confidence_score=0.8)
    
    engine = ClaimEngine(db_session)
    engine.process_extraction(startup.id, extraction, doc.id)
    profile = engine.profiles.get_by_startup(startup.id)
    claim = list(engine.claims.list_for_profile(profile.id))[0]

    # 2. Query endpoints
    # Profile snapshots
    response = test_client.get(f"/api/v1/intelligence/{startup.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(profile.id)

    # List claims
    response = test_client.get(f"/api/v1/intelligence/{startup.id}/claims")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == str(claim.id)

    # Retrieve specific claim
    response = test_client.get(f"/api/v1/intelligence/{startup.id}/claims/{claim.id}")
    assert response.status_code == 200
    assert response.json()["id"] == str(claim.id)

    # List evidence
    response = test_client.get(f"/api/v1/intelligence/{startup.id}/evidence")
    assert response.status_code == 200
    assert len(response.json()) == 1

    # List conflicts (0 unresolved conflicts)
    response = test_client.get(f"/api/v1/intelligence/{startup.id}/conflicts")
    assert response.status_code == 200
    assert len(response.json()) == 0

    # List versions
    response = test_client.get(f"/api/v1/intelligence/{startup.id}/versions")
    assert response.status_code == 200
    assert len(response.json()) == 1
