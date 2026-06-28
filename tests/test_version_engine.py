import os
import json
import time
import uuid
import shutil
import pytest
from datetime import datetime, timezone
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.modules.startups.models import StartupApplication
from app.core.enums import StartupStatus
from app.modules.intelligence.models import (
    StartupIntelligenceProfile, StartupClaim, StartupEvidence, FieldConflict, KnowledgeFieldRegistry
)
from app.modules.workflow.workflow_models import Workflow
from app.modules.workflow.workflow_queries import register_workflow, clear_workflow_registry, create_workflow, get_workflow
from app.security.audit import get_recent_events, clear_audit_ring
from app.modules.intelligence.events import dispatcher

# Versioning imports
from app.modules.evaluation.versioning.version_models import StartupVersion, VersionSnapshot, DeltaReport, DeltaItem
from app.modules.evaluation.versioning.version_validator import VersionValidator, VersionValidationError
from app.modules.evaluation.versioning.version_serializer import VersionSerializer
from app.modules.evaluation.versioning.delta_engine import DeltaEngine
from app.modules.evaluation.versioning.version_engine import VersionEngine
from app.modules.evaluation.versioning.version_queries import (
    create_version, get_version, list_versions, trace_version_history,
    compare_versions, generate_delta, rollback_version, export_version
)
from app.api.dependencies import EvaluationService
from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType, ObservationNode, RiskNode, Edge
from tests.test_committee_engine import create_mock_graph
from app.modules.evaluation.committee.committee_engine import CommitteeDecisionEngine
from app.modules.evaluation.committee import Recommendation


@pytest.fixture(autouse=True)
def clean_registries():
    clear_workflow_registry()
    clear_audit_ring()
    # Clean up test directories under uploads
    for d in [os.path.join("uploads", "versions"), os.path.join("uploads", "graphs")]:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)
    yield
    clear_workflow_registry()
    clear_audit_ring()
    for d in [os.path.join("uploads", "versions"), os.path.join("uploads", "graphs")]:
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)


@pytest.fixture()
def db_session():
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
def sample_startup(db_session: Session) -> StartupApplication:
    startup = StartupApplication(
        id=uuid.uuid4(),
        startup_name="Acme Biotech",
        sector="Biotech",
        current_status=StartupStatus.DRAFT
    )
    db_session.add(startup)
    db_session.commit()
    db_session.refresh(startup)
    return startup


@pytest.fixture()
def setup_intelligence_profile(db_session: Session, sample_startup: StartupApplication):
    # Insert knowledge field registries
    field1 = KnowledgeFieldRegistry(
        id=uuid.uuid4(),
        field_key="founder_experience",
        field_name="Founder Experience",
        value_type="string"
    )
    field2 = KnowledgeFieldRegistry(
        id=uuid.uuid4(),
        field_key="trl_level",
        field_name="TRL Level",
        value_type="number"
    )
    db_session.add(field1)
    db_session.add(field2)
    db_session.commit()

    profile = StartupIntelligenceProfile(
        id=uuid.uuid4(),
        startup_id=sample_startup.id
    )
    db_session.add(profile)
    db_session.commit()

    claim1 = StartupClaim(
        id=uuid.uuid4(),
        profile_id=profile.id,
        field_id=field1.id,
        value_string="10 years in biotech",
        confidence_score=0.9,
        is_preferred=True,
        validation_status="VALIDATED"
    )
    claim2 = StartupClaim(
        id=uuid.uuid4(),
        profile_id=profile.id,
        field_id=field2.id,
        value_number=5.0,
        confidence_score=0.85,
        is_preferred=True,
        validation_status="VALIDATED"
    )
    db_session.add(claim1)
    db_session.add(claim2)
    db_session.commit()

    evidence1 = StartupEvidence(
        id=uuid.uuid4(),
        claim_id=claim1.id,
        evidence_snippet="Founder was CTO at Genentech for a decade.",
        confidence_score=0.95,
        validation_status="VALIDATED"
    )
    db_session.add(evidence1)
    db_session.commit()

    conflict1 = FieldConflict(
        id=uuid.uuid4(),
        profile_id=profile.id,
        field_id=field1.id,
        resolved=False
    )
    db_session.add(conflict1)
    db_session.commit()

    return profile, claim1, claim2, evidence1, conflict1


def create_test_graph_node(startup_id: str, name: str, trl_score: int = 5) -> ObservationGraph:
    # Use create_mock_graph which builds fully populated typed nodes
    graph = create_mock_graph(startup_id, name, "Biotech", investment_score=80.0, confidence=0.9)
    graph = CommitteeDecisionEngine.generate(graph)

    # Set investment technology score
    if graph.investment_assessment:
        graph.investment_assessment.technology_score = trl_score

    # Add custom observations for test comparisons
    obs_trl = ObservationNode(
        node_id="obs-trl", node_type=NodeType.OBSERVATION,
        observation_id="obs-trl", domain="trl",
        observation=f"TRL level evaluated as {trl_score}", confidence=0.85
    )
    graph.observations["obs-trl"] = obs_trl

    return graph


def test_version_creation(db_session, sample_startup, setup_intelligence_profile) -> None:
    startup_id = str(sample_startup.id)
    profile, claim1, claim2, evidence1, conflict1 = setup_intelligence_profile

    # Save active graph file on disk
    graph = create_test_graph_node(startup_id, sample_startup.startup_name)
    eval_service = EvaluationService(db_session)
    eval_service.save_graph(graph)

    # Register workflow using query helper to avoid Pydantic missing fields
    wf = create_workflow(
        startup_id=startup_id,
        startup_name=sample_startup.startup_name,
        created_by="user-1",
        db=db_session
    )

    # Track published events
    events_published = []
    def on_event(ev):
        events_published.append(ev.event_name)

    dispatcher.register("VersionCreated", on_event)

    try:
        ver = create_version(
            startup_id=startup_id,
            db=db_session,
            actor="user-1",
            workflow_id=wf.workflow_id,
            metadata={"request_id": "REQ-123", "user": "user-1"}
        )

        assert ver is not None
        assert ver.version_number == 1
        assert ver.startup_id == startup_id
        assert ver.startup_name == "Acme Biotech"
        assert ver.created_by == "user-1"
        assert ver.workflow_id == wf.workflow_id
        assert ver.committee_report_id == graph.committee_decision.decision_id
        assert ver.executive_report_id == graph.executive_assessment.assessment_id
        assert ver.investment_report_id == graph.investment_assessment.assessment_id

        # Check file persisted on disk
        versions = list_versions(startup_id)
        assert len(versions) == 1
        assert versions[0].version_id == ver.version_id

        # Load version and snapshot
        loaded_ver, snapshot = get_version(startup_id, 1)
        assert loaded_ver.version_id == ver.version_id
        assert len(snapshot.claims) == 2
        assert len(snapshot.evidence) == 1
        assert len(snapshot.conflicts) == 1
        assert snapshot.committee_report is not None
        assert snapshot.workflow_state is not None
        assert snapshot.workflow_state["workflow_id"] == wf.workflow_id

        # Check published events
        assert "VersionCreated" in events_published

        # Check security audit logs
        audit_events = get_recent_events(10)
        assert any(e.action == "version.create" and ver.version_id in e.resource for e in audit_events)

    finally:
        dispatcher.unregister("VersionCreated", on_event)


def test_snapshot_integrity(db_session, sample_startup, setup_intelligence_profile) -> None:
    startup_id = str(sample_startup.id)
    profile, claim1, claim2, evidence1, conflict1 = setup_intelligence_profile

    # Save active graph
    graph = create_test_graph_node(startup_id, sample_startup.startup_name)
    eval_service = EvaluationService(db_session)
    eval_service.save_graph(graph)

    # First creation should succeed
    ver = create_version(startup_id=startup_id, db=db_session, actor="user-1", metadata={"user": "user-1", "request_id": "REQ-1"})

    # Check duplicate versions rule
    loaded_ver, snapshot = get_version(startup_id, 1)
    errors = VersionValidator.validate_version(
        version=loaded_ver,
        snapshot=snapshot,
        existing_versions=[loaded_ver],
        active_workflow_ids=[]
    )
    assert any("Duplicate version" in e for e in errors)

    # Check graph hash mismatch
    bad_ver = loaded_ver.model_copy(update={"graph_hash": "different_hash"})
    errors = VersionValidator.validate_version(
        version=bad_ver,
        snapshot=snapshot,
        existing_versions=[],
        active_workflow_ids=[]
    )
    assert any("Graph hash mismatch" in e for e in errors)

    # Check workflow missing check
    bad_ver = loaded_ver.model_copy(update={"workflow_id": "WF-MISSING"})
    errors = VersionValidator.validate_version(
        version=bad_ver,
        snapshot=snapshot,
        existing_versions=[],
        active_workflow_ids=["WF-EXISTING"]
    )
    assert any("Workflow ID 'WF-MISSING' does not exist" in e for e in errors)

    # Check metadata completeness rule
    bad_ver = loaded_ver.model_copy(update={"metadata": {}})
    errors = VersionValidator.validate_version(
        version=bad_ver,
        snapshot=snapshot,
        existing_versions=[],
        active_workflow_ids=[]
    )
    assert any("Version metadata is empty" in e or "metadata completeness" in e for e in errors)


def test_rollback_restoration(db_session, sample_startup, setup_intelligence_profile) -> None:
    startup_id = str(sample_startup.id)
    profile, claim1, claim2, evidence1, conflict1 = setup_intelligence_profile

    # Save initial graph
    graph = create_test_graph_node(startup_id, sample_startup.startup_name, trl_score=5)
    eval_service = EvaluationService(db_session)
    eval_service.save_graph(graph)

    # Create workflow using query helper
    wf = create_workflow(
        startup_id=startup_id,
        startup_name=sample_startup.startup_name,
        created_by="user-1",
        db=db_session
    )
    wf.current_state = "Submitted"
    register_workflow(wf)

    # 1. Create Version 1
    ver1 = create_version(startup_id=startup_id, db=db_session, actor="user-1", workflow_id=wf.workflow_id)

    # Modify values in DB
    claim1.value_string = "MUTATED CLAIMS VALUE"
    evidence1.evidence_snippet = "MUTATED EVIDENCE SNIPPET"
    conflict1.resolved = True
    conflict1.resolution_reason = "Manual override"
    db_session.commit()

    # Modify graph on disk
    graph_mutated = create_test_graph_node(startup_id, sample_startup.startup_name, trl_score=8)
    eval_service.save_graph(graph_mutated)

    # Modify workflow state
    wf.current_state = "Incubation"
    register_workflow(wf)

    # Track published events
    events_published = []
    def on_event(ev):
        events_published.append(ev.event_name)
    dispatcher.register("RollbackStarted", on_event)
    dispatcher.register("RollbackCompleted", on_event)

    try:
        # Perform rollback
        rolled = rollback_version(
            startup_id=startup_id,
            version_number=1,
            db=db_session,
            actor="admin-1",
            role="admin",
            reason="Corrupt latest run"
        )

        assert rolled.version_number == 1

        # Check DB values restored
        restored_claims = db_session.query(StartupClaim).filter(StartupClaim.profile_id == profile.id).all()
        assert len(restored_claims) == 2
        claim_map = {c.field.field_key: c for c in restored_claims}
        assert claim_map["founder_experience"].value_string == "10 years in biotech"

        restored_ev = db_session.query(StartupEvidence).join(StartupClaim).filter(StartupClaim.profile_id == profile.id).all()
        assert len(restored_ev) == 1
        assert restored_ev[0].evidence_snippet == "Founder was CTO at Genentech for a decade."

        restored_conflicts = db_session.query(FieldConflict).filter(FieldConflict.profile_id == profile.id).all()
        assert len(restored_conflicts) == 1
        assert restored_conflicts[0].resolved is False

        # Check graph restored
        restored_graph = eval_service.get_graph(startup_id)
        assert restored_graph.observations["obs-trl"].observation == "TRL level evaluated as 5"

        # Check workflow restored
        restored_wf = get_workflow(wf.workflow_id)
        assert restored_wf.current_state == "Submitted"

        # Check events
        assert "RollbackStarted" in events_published
        assert "RollbackCompleted" in events_published

        # Check security audit
        audit_events = get_recent_events(10)
        assert any(e.action == "version.rollback" and "rollback" in e.resource for e in audit_events)

    finally:
        dispatcher.unregister("RollbackStarted", on_event)
        dispatcher.unregister("RollbackCompleted", on_event)


def test_delta_generation(db_session, sample_startup, setup_intelligence_profile) -> None:
    startup_id = str(sample_startup.id)
    profile, claim1, claim2, evidence1, conflict1 = setup_intelligence_profile

    # Save active graph
    graph1 = create_test_graph_node(startup_id, sample_startup.startup_name, trl_score=5)
    eval_service = EvaluationService(db_session)
    eval_service.save_graph(graph1)

    # Create Version 1
    create_version(startup_id=startup_id, db=db_session, actor="user-1")

    # Modify values for Version 2
    # 1. Modify TRL level claim value
    claim2.value_number = 6.0
    # 2. Add a new claim
    field3 = KnowledgeFieldRegistry(
        id=uuid.uuid4(),
        field_key="market_size",
        field_name="Market Size",
        value_type="string"
    )
    db_session.add(field3)
    db_session.commit()
    claim3 = StartupClaim(
        id=uuid.uuid4(),
        profile_id=profile.id,
        field_id=field3.id,
        value_string="$5B market",
        confidence_score=0.8,
        is_preferred=True
    )
    db_session.add(claim3)
    db_session.commit()

    # Modify graph: update observations, risks, committee report
    graph2 = create_test_graph_node(startup_id, sample_startup.startup_name, trl_score=6)
    # Add new observation under market domain
    obs3 = ObservationNode(
        node_id="obs-999", node_type=NodeType.OBSERVATION,
        observation_id="obs-999", domain="market",
        observation="Large market size potential", confidence=0.8
    )
    graph2.observations["obs-999"] = obs3

    # Add a risk
    r1 = RiskNode(
        node_id="risk-1-custom", node_type=NodeType.RISK,
        risk_id="risk-1-custom", description="Regulatory approval delays",
        category="regulatory", confidence=0.75, reasoning="Reason"
    )
    graph2.risks["risk-1-custom"] = r1

    # Modify committee verdict
    graph2.committee_decision.recommendation = Recommendation.DEFER
 
    eval_service.save_graph(graph2)
 
    # Create Version 2
    create_version(startup_id=startup_id, db=db_session, actor="user-1")
 
    # Run Delta Comparison
    delta = compare_versions(startup_id, 1, 2)
 
    assert delta.from_version == 1
    assert delta.to_version == 2
    assert delta.overall_change_confidence > 0.0
 
    # Verify category changes
    # 1. Claims: Modified claim2, Added claim3
    added_claims = [item for item in delta.added_items if item.category == "Claims"]
    modified_claims = [item for item in delta.modified_items if item.category == "Claims"]
    assert len(added_claims) == 1
    assert len(modified_claims) == 1
 
    # 2. Risk Added
    added_risks = [item for item in delta.added_items if item.category == "Risk"]
    assert len(added_risks) >= 1
 
    # 3. Market changes caught
    market_items = [item for item in delta.added_items if item.category == "Market"]
    assert len(market_items) == 1
 
    # 4. TRL progressive changes caught
    trl_items = [item for item in delta.modified_items if item.category == "TRL"]
    assert len(trl_items) == 2
    tech_score_delta = [item for item in trl_items if item.field == "technology_score"][0]
    assert tech_score_delta.previous_value == 5
    assert tech_score_delta.current_value == 6
    assert "progressed from 5.0 to 6.0" in tech_score_delta.reasoning

    # 5. Committee changes caught
    comm_items = [item for item in delta.modified_items if item.category == "Committee Decision"]
    assert len(comm_items) == 1
    assert comm_items[0].field == "recommendation"
    assert comm_items[0].previous_value == "INCUBATE"
    assert comm_items[0].current_value == "DEFER"


def test_serialization(db_session, sample_startup, setup_intelligence_profile) -> None:
    startup_id = str(sample_startup.id)
    profile, claim1, claim2, evidence1, conflict1 = setup_intelligence_profile

    # Save active graph
    graph = create_test_graph_node(startup_id, sample_startup.startup_name)
    eval_service = EvaluationService(db_session)
    eval_service.save_graph(graph)

    create_version(startup_id=startup_id, db=db_session, actor="user-1")

    # Load version/snapshot
    version, snapshot = get_version(startup_id, 1)

    # 1. JSON
    json_str = VersionSerializer.to_json(version)
    assert json_str != ""
    assert version.version_id in json_str

    rebuilt_ver = VersionSerializer.from_json(json_str, StartupVersion)
    assert rebuilt_ver.version_id == version.version_id

    # 2. Markdown
    md_report = export_version(startup_id, 1, "markdown")
    assert "# Startup Evaluation Version Report:" in md_report
    assert "## Version Details" in md_report
    assert "Acme Biotech" in md_report

    # 3. HTML
    html_report = export_version(startup_id, 1, "html")
    assert "<!DOCTYPE html>" in html_report
    assert "Version Report: Acme Biotech" in html_report

    # 4. PDF ready dict
    pdf_dict = export_version(startup_id, 1, "pdf")
    assert "version" in pdf_dict
    assert "snapshot" in pdf_dict
    assert pdf_dict["version"]["version_id"] == version.version_id


def test_performance_benchmarks(db_session, sample_startup, setup_intelligence_profile) -> None:
    startup_id = str(sample_startup.id)
    profile, claim1, claim2, evidence1, conflict1 = setup_intelligence_profile

    # Save initial graph
    graph1 = create_test_graph_node(startup_id, sample_startup.startup_name, trl_score=5)
    eval_service = EvaluationService(db_session)
    eval_service.save_graph(graph1)

    # Create workflow
    wf = create_workflow(
        startup_id=startup_id,
        startup_name=sample_startup.startup_name,
        created_by="user-1",
        db=db_session
    )

    # Warm-up run
    create_version(startup_id=startup_id, db=db_session, actor="user-1", workflow_id=wf.workflow_id)
    
    # 1. Creation speed benchmark (< 50 ms)
    # Modify profile to force another version creation
    claim1.value_string = "Warm up mutate"
    db_session.commit()
    
    t0 = time.perf_counter()
    create_version(startup_id=startup_id, db=db_session, actor="user-1", workflow_id=wf.workflow_id)
    creation_time = (time.perf_counter() - t0) * 1000.0
    assert creation_time < 50.0, f"Version creation took {creation_time:.2f} ms (Target: < 50 ms)"

    # 2. History lookup speed benchmark (< 20 ms)
    t0 = time.perf_counter()
    history = list_versions(startup_id)
    lookup_time = (time.perf_counter() - t0) * 1000.0
    assert len(history) >= 2
    assert lookup_time < 20.0, f"History lookup took {lookup_time:.2f} ms (Target: < 20 ms)"

    # 3. Delta generation speed benchmark (< 100 ms)
    t0 = time.perf_counter()
    delta = compare_versions(startup_id, 1, 2)
    delta_time = (time.perf_counter() - t0) * 1000.0
    assert delta_time < 100.0, f"Delta generation took {delta_time:.2f} ms (Target: < 100 ms)"

    # 4. Rollback speed benchmark (< 50 ms)
    t0 = time.perf_counter()
    rollback_version(
        startup_id=startup_id,
        version_number=1,
        db=db_session,
        actor="admin-1",
        role="admin",
        reason="Performance test"
    )
    rollback_time = (time.perf_counter() - t0) * 1000.0
    assert rollback_time < 50.0, f"Version rollback took {rollback_time:.2f} ms (Target: < 50 ms)"

    # 5. Serialization speed benchmark (< 250 ms)
    version, snapshot = get_version(startup_id, 1)
    t0 = time.perf_counter()
    json_str = VersionSerializer.to_json(snapshot)
    serialization_time = (time.perf_counter() - t0) * 1000.0
    assert json_str != ""
    assert serialization_time < 250.0, f"Serialization took {serialization_time:.2f} ms (Target: < 250 ms)"
