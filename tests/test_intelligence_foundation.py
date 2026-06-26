from collections.abc import Generator
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.main import app
from app.modules.intelligence.events import Event, EventDispatcher
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
from app.modules.intelligence.repository import (
    FieldConflictRepository,
    FieldSourceRepository,
    FieldVersionRepository,
    KnowledgeFieldRegistryRepository,
    StartupClaimRepository,
    StartupEvidenceRepository,
    StartupIntelligenceProfileRepository,
    StartupIntelligenceProfileVersionRepository,
    StartupProcessingStatusRepository,
)
from app.modules.intelligence.service import IntelligenceService
from app.modules.startups.models import StartupApplication


# --- Fixtures ---
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
def db_session_intelligence(db_session: Session) -> Session:
    """Fixture that uses the locally defined db_session."""
    return db_session



@pytest.fixture()
def test_client() -> TestClient:
    return TestClient(app)


# --- Database Models & Relations Tests ---
def test_create_and_query_intelligence_models(db_session_intelligence: Session) -> None:
    session = db_session_intelligence

    # Create dummy StartupApplication
    startup = StartupApplication(
        startup_name="Test Intelligence Startup",
        stage="MVP",
        current_status="SUBMITTED"
    )
    session.add(startup)
    session.flush()

    # Create KnowledgeFieldRegistry entries
    field = KnowledgeFieldRegistry(
        field_key="trl",
        field_name="Technology Readiness Level",
        value_type="number"
    )
    session.add(field)
    session.flush()

    # Create StartupIntelligenceProfile
    profile = StartupIntelligenceProfile(startup_id=startup.id)
    session.add(profile)
    session.flush()

    # Create StartupClaim
    claim = StartupClaim(
        profile_id=profile.id,
        field_id=field.id,
        value_number=4.0,
        confidence_score=0.85,
        validation_status="UNVALIDATED",
        reasoning="Extracted from pitch deck page 5.",
        is_preferred=True
    )
    session.add(claim)
    session.flush()

    # Create StartupEvidence
    evidence = StartupEvidence(
        claim_id=claim.id,
        confidence_score=0.90,
        evidence_snippet="The product is currently at TRL 4 with pilot results.",
        validation_status="UNVALIDATED"
    )
    session.add(evidence)
    session.flush()

    # Verify relations
    assert len(profile.claims) == 1
    assert profile.claims[0].value_number == 4.0
    assert len(profile.claims[0].evidence) == 1
    assert profile.claims[0].evidence[0].evidence_snippet == "The product is currently at TRL 4 with pilot results."


# --- Event Dispatcher Infrastructure Tests ---
def test_event_dispatcher_register_and_publish() -> None:
    dispatcher = EventDispatcher()
    received_events = []

    def subscriber_one(event: Event) -> None:
        received_events.append(event)

    def subscriber_two(event: Event) -> None:
        received_events.append(event)

    # 1. Standard register and publish
    dispatcher.register("DocumentRegistered", subscriber_one)
    dispatcher.register("ClaimsMerged", subscriber_two)

    # Publish DocumentRegistered event
    event_payload = {"doc_id": "test-doc-id-123"}
    event1 = Event(event_name="DocumentRegistered", payload=event_payload)
    dispatcher.publish(event1)

    assert len(received_events) == 1
    assert received_events[0].event_name == "DocumentRegistered"
    assert received_events[0].payload == event_payload

    # Publish ClaimsMerged event
    event2 = Event(event_name="ClaimsMerged", payload={"profile_id": "test-profile-id"})
    dispatcher.publish(event2)

    assert len(received_events) == 2
    assert received_events[1].event_name == "ClaimsMerged"
    assert received_events[1].payload["profile_id"] == "test-profile-id"

    # 2. Prevent duplicate subscriptions
    dispatcher.register("DocumentRegistered", subscriber_one)
    received_events.clear()
    dispatcher.publish(event1)
    assert len(received_events) == 1  # Should only be called once, not twice

    # 3. Unregister subscription
    unregistered = dispatcher.unregister("DocumentRegistered", subscriber_one)
    assert unregistered is True
    received_events.clear()
    dispatcher.publish(event1)
    assert len(received_events) == 0

    # Try unregistering non-existent
    unregistered_fake = dispatcher.unregister("DocumentRegistered", subscriber_one)
    assert unregistered_fake is False

    # 4. Exception Handling
    def bad_subscriber(event: Event) -> None:
        raise ValueError("Simulated subscriber crash")

    dispatcher.register("CrashEvent", bad_subscriber)
    dispatcher.register("CrashEvent", subscriber_two)

    received_events.clear()
    # By default, should suppress exceptions but log them, and execute remaining subscribers
    dispatcher.publish(Event("CrashEvent", {}), propagate_exceptions=False)
    assert len(received_events) == 1  # subscriber_two still executes!

    # When propagate_exceptions=True, it should raise the exception
    with pytest.raises(ValueError, match="Simulated subscriber crash"):
        dispatcher.publish(Event("CrashEvent", {}), propagate_exceptions=True)



# --- Repositories Tests ---
def test_repositories_operations(db_session_intelligence: Session) -> None:
    session = db_session_intelligence

    # Startup application
    startup = StartupApplication(
        startup_name="Repo Test Startup",
        stage="Prototype",
        current_status="SUBMITTED"
    )
    session.add(startup)
    session.flush()

    # Field registry
    registry_repo = KnowledgeFieldRegistryRepository(session)
    field = KnowledgeFieldRegistry(
        field_key="revenue",
        field_name="Annual Revenue",
        value_type="number"
    )
    registry_repo.add(field)
    session.flush()

    fetched_field = registry_repo.get_by_key("revenue")
    assert fetched_field is not None
    assert fetched_field.field_name == "Annual Revenue"

    # Profile version repository
    profile = StartupIntelligenceProfile(startup_id=startup.id)
    session.add(profile)
    session.flush()

    version_repo = StartupIntelligenceProfileVersionRepository(session)
    version = version_repo.create_version(
        profile_id=profile.id,
        snapshot={"revenue": 100000}
    )
    assert version.version_number == 1
    assert version.profile_snapshot["revenue"] == 100000

    latest_ver = version_repo.latest_version(profile.id)
    assert latest_ver is not None
    assert latest_ver.version_number == 1

    # Processing status repository
    status_repo = StartupProcessingStatusRepository(session)
    status_record = status_repo.create_status(
        startup_id=startup.id,
        pipeline_name="intelligence_extraction",
        stage="DOCUMENT_REGISTRY"
    )
    assert status_record.status == PipelineStatus.QUEUED
    assert status_record.progress_percentage == 0

    status_repo.update_progress(status_record.id, "PARSING", 40, PipelineStatus.RUNNING)
    session.refresh(status_record)
    assert status_record.status == PipelineStatus.RUNNING
    assert status_record.current_stage == "PARSING"
    assert status_record.progress_percentage == 40

    status_repo.mark_completed(status_record.id, 1200)
    session.refresh(status_record)
    assert status_record.status == PipelineStatus.COMPLETED
    assert status_record.progress_percentage == 100
    assert status_record.processing_time_ms == 1200

    status_repo.retry(status_record.id, "RETRY_STAGE")
    session.refresh(status_record)
    assert status_record.status == PipelineStatus.RUNNING
    assert status_record.current_stage == "RETRY_STAGE"
    assert status_record.retry_count == 1

    status_repo.mark_failed(status_record.id, "Extraction timeout")
    session.refresh(status_record)
    assert status_record.status == PipelineStatus.FAILED
    assert status_record.last_error == "Extraction timeout"


# --- REST API Route Tests ---
def test_intelligence_routes_return_501(test_client: TestClient, db_session: Session) -> None:
    from app.db.session import get_db
    from app.modules.auth.dependencies import get_current_user
    
    class SimpleNamespace:
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            
    fake_user = SimpleNamespace(
        id=uuid4(),
        is_active=True,
        role=SimpleNamespace(name="viewer"),
    )
    
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: fake_user
    
    try:
        startup_id = uuid4()

        response = test_client.get(f"/api/v1/intelligence/{startup_id}")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

        response = test_client.get(f"/api/v1/intelligence/{startup_id}/claims")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

        response = test_client.get(f"/api/v1/intelligence/{startup_id}/evidence")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

        response = test_client.get(f"/api/v1/intelligence/{startup_id}/conflicts")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


# --- Intelligence Service Tests ---
def test_intelligence_service_bindings(db_session_intelligence: Session) -> None:
    session = db_session_intelligence
    service = IntelligenceService(session)
    assert service.field_registry is not None
    assert service.profiles is not None
    assert service.claims is not None
    assert service.evidence is not None
    assert service.versions is not None
    assert service.conflicts is not None
    assert service.sources is not None
    assert service.status is not None
    assert service.profile_versions is not None


def test_all_other_repositories(db_session_intelligence: Session) -> None:
    session = db_session_intelligence

    # Startup application
    startup = StartupApplication(
        startup_name="More Repo Test Startup",
        stage="Prototype",
        current_status="SUBMITTED"
    )
    session.add(startup)
    session.flush()

    # Knowledge Registry
    registry_repo = KnowledgeFieldRegistryRepository(session)
    field1 = KnowledgeFieldRegistry(field_key="key1", field_name="Name 1", value_type="string", is_active=True)
    field2 = KnowledgeFieldRegistry(field_key="key2", field_name="Name 2", value_type="string", is_active=False)
    registry_repo.add(field1)
    registry_repo.add(field2)
    session.flush()

    active_fields = registry_repo.list_active()
    assert len(active_fields) >= 1
    assert any(f.field_key == "key1" for f in active_fields)
    assert not any(f.field_key == "key2" for f in active_fields)

    # Profile
    profile_repo = StartupIntelligenceProfileRepository(session)
    profile = StartupIntelligenceProfile(startup_id=startup.id)
    profile_repo.add(profile)
    session.flush()

    assert profile_repo.get_by_startup(startup.id).id == profile.id

    # Claims
    claim_repo = StartupClaimRepository(session)
    claim1 = StartupClaim(
        profile_id=profile.id, field_id=field1.id, value_string="v1", confidence_score=0.9, is_preferred=True
    )
    claim2 = StartupClaim(
        profile_id=profile.id, field_id=field1.id, value_string="v2", confidence_score=0.7, is_preferred=False
    )
    claim_repo.add(claim1)
    claim_repo.add(claim2)
    session.flush()

    claims = claim_repo.list_for_profile(profile.id)
    assert len(claims) == 2
    preferred = claim_repo.list_preferred_for_profile(profile.id)
    assert len(preferred) == 1
    assert preferred[0].value_string == "v1"

    field_claims = claim_repo.get_for_field(profile.id, field1.id)
    assert len(field_claims) == 2

    # Evidence & Source (requires dummy document or None for doc relation)
    evidence_repo = StartupEvidenceRepository(session)
    evidence = StartupEvidence(claim_id=claim1.id, confidence_score=0.95, validation_status="VALIDATED")
    evidence_repo.add(evidence)
    session.flush()

    evidences = evidence_repo.list_for_claim(claim1.id)
    assert len(evidences) == 1
    assert evidences[0].confidence_score == 0.95

    # Versions
    version_repo = FieldVersionRepository(session)
    v1 = FieldVersion(claim_id=claim1.id, version_number=1, value_string="old")
    v2 = FieldVersion(claim_id=claim1.id, version_number=2, value_string="new")
    version_repo.add(v1)
    version_repo.add(v2)
    session.flush()

    versions = version_repo.list_for_claim(claim1.id)
    assert len(versions) == 2
    assert versions[0].version_number == 2  # ordered desc
    assert version_repo.get_latest_version_number(claim1.id) == 2

    # Conflicts
    conflict_repo = FieldConflictRepository(session)
    conflict = FieldConflict(profile_id=profile.id, field_id=field1.id, resolved=False)
    conflict_repo.add(conflict)
    session.flush()

    conflicts = conflict_repo.list_unresolved_for_profile(profile.id)
    assert len(conflicts) == 1
    assert conflicts[0].field_id == field1.id

    # Profile version load_version & list_versions
    profile_ver_repo = StartupIntelligenceProfileVersionRepository(session)
    pv1 = profile_ver_repo.create_version(profile.id, {"a": 1})
    pv2 = profile_ver_repo.create_version(profile.id, {"a": 2})
    session.flush()

    assert profile_ver_repo.load_version(profile.id, 1).profile_snapshot == {"a": 1}
    assert len(profile_ver_repo.list_versions(profile.id)) == 2

    # Service helpers
    service = IntelligenceService(session)
    assert service.get_profile(startup.id).id == profile.id

    # Processing Status Helper
    status_repo = StartupProcessingStatusRepository(session)
    status_record = status_repo.create_status(startup_id=startup.id, pipeline_name="p1", stage="s1")
    session.flush()
    assert service.get_processing_status(startup.id, "p1").id == status_record.id

