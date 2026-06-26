import time
import uuid
import threading
import pytest
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.modules.startups.models import StartupApplication
from app.core.enums import StartupStatus, RoleName
from app.modules.intelligence.events import dispatcher
from app.security.audit import get_recent_events, clear_audit_ring
from app.modules.workflow import (
    Workflow,
    WorkflowState,
    WorkflowTransition,
    WorkflowHistoryEntry,
    WorkflowEngine,
    WorkflowStateMachine,
    WorkflowValidator,
    WorkflowValidationError,
    WorkflowSerializer,
    create_workflow,
    get_workflow,
    get_current_state,
    get_history,
    list_workflows,
    list_by_state,
    list_active_workflows,
    list_completed_workflows,
    rollback_workflow,
    validate_transition,
    clear_workflow_registry
)


@pytest.fixture(autouse=True)
def clean_registries():
    clear_workflow_registry()
    clear_audit_ring()
    yield
    clear_workflow_registry()
    clear_audit_ring()


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
    # Insert a dummy startup to check startup existence
    startup = StartupApplication(
        id=uuid.uuid4(),
        startup_name="Test Ventures",
        sector="SaaS",
        current_status=StartupStatus.DRAFT
    )
    db_session.add(startup)
    db_session.commit()
    db_session.refresh(startup)
    return startup


# --- Unit Tests ---

def test_workflow_creation(sample_startup, db_session) -> None:
    # Track published events
    event_names = []
    def track_event(ev):
        event_names.append(ev.event_name)

    dispatcher.register("WorkflowCreated", track_event)
    dispatcher.register("WorkflowStarted", track_event)

    try:
        wf = create_workflow(
            startup_id=str(sample_startup.id),
            startup_name=sample_startup.startup_name,
            created_by="user-1",
            db=db_session
        )

        assert wf is not None
        assert wf.current_state == "Draft"
        assert wf.previous_state is None
        assert wf.startup_id == str(sample_startup.id)
        assert wf.startup_name == "Test Ventures"
        assert wf.created_by == "user-1"
        assert wf.workflow_hash != ""

        # Query getters check
        retrieved = get_workflow(wf.workflow_id)
        assert retrieved == wf
        assert get_current_state(wf.workflow_id) == "Draft"

        # Events check
        assert "WorkflowCreated" in event_names
        assert "WorkflowStarted" in event_names

        # Audit logs check
        events = get_recent_events(10)
        assert any(e.action == "workflow.create" and wf.workflow_id in e.resource for e in events)

    finally:
        dispatcher.unregister("WorkflowCreated", track_event)
        dispatcher.unregister("WorkflowStarted", track_event)


def test_successful_transition(sample_startup, db_session) -> None:
    wf = create_workflow(
        startup_id=str(sample_startup.id),
        startup_name=sample_startup.startup_name,
        created_by="user-1",
        db=db_session
    )

    # Perform transition Draft -> Submitted
    # Target state 'Submitted' requires approval
    wf_updated = WorkflowEngine.execute_transition(
        workflow_id=wf.workflow_id,
        to_state="Submitted",
        actor="manager-1",
        role="incubation_manager",
        justification="Startup filled all details",
        metadata={"approved": True},
        db=db_session
    )

    assert wf_updated.current_state == "Submitted"
    assert wf_updated.previous_state == "Draft"
    assert wf_updated.last_modified_by == "manager-1"
    
    # Check history entries
    history = get_history(wf.workflow_id)
    assert len(history) == 1
    assert history[0].previous_state == "Draft"
    assert history[0].new_state == "Submitted"
    assert history[0].actor == "manager-1"
    assert history[0].role == "incubation_manager"
    assert history[0].reason == "Startup filled all details"


def test_invalid_transition(sample_startup, db_session) -> None:
    wf = create_workflow(
        startup_id=str(sample_startup.id),
        startup_name=sample_startup.startup_name,
        created_by="user-1",
        db=db_session
    )

    # Draft -> Incubation is invalid (not allowed in graph)
    with pytest.raises(WorkflowValidationError) as exc_info:
        WorkflowEngine.execute_transition(
            workflow_id=wf.workflow_id,
            to_state="Incubation",
            actor="manager-1",
            role="incubation_manager",
            justification="skip steps",
            db=db_session
        )
    assert "is not allowed in state machine" in exc_info.value.errors[0]


def test_rollback(sample_startup, db_session) -> None:
    wf = create_workflow(
        startup_id=str(sample_startup.id),
        startup_name=sample_startup.startup_name,
        created_by="user-1",
        db=db_session
    )

    # Transitions: Draft -> Submitted -> Document Verification
    WorkflowEngine.execute_transition(
        workflow_id=wf.workflow_id,
        to_state="Submitted",
        actor="manager-1",
        role="incubation_manager",
        justification="Step 1",
        metadata={"approved": True},
        db=db_session
    )

    WorkflowEngine.execute_transition(
        workflow_id=wf.workflow_id,
        to_state="Document Verification",
        actor="reviewer-1",
        role="reviewer",
        justification="Step 2",
        metadata={"approved": True},
        db=db_session
    )

    # Perform Rollback back to 'Submitted'
    wf_rolled = rollback_workflow(
        workflow_id=wf.workflow_id,
        target_state="Submitted",
        actor="manager-1",
        role="incubation_manager",
        reason="Missed verification checks",
        state_machine=WorkflowStateMachine(),
        db=db_session
    )

    assert wf_rolled.current_state == "Submitted"
    assert wf_rolled.previous_state == "Document Verification"

    # Rollback log in history
    history = get_history(wf.workflow_id)
    assert len(history) == 3 # 2 transitions + 1 rollback
    assert history[2].previous_state == "Document Verification"
    assert history[2].new_state == "Submitted"
    assert "ROLLBACK" in history[2].reason


def test_terminal_state(sample_startup, db_session) -> None:
    wf = create_workflow(
        startup_id=str(sample_startup.id),
        startup_name=sample_startup.startup_name,
        created_by="user-1",
        db=db_session
    )

    # Draft -> Archived (valid transition)
    wf_archived = WorkflowEngine.execute_transition(
        workflow_id=wf.workflow_id,
        to_state="Archived",
        actor="admin-1",
        role="admin",
        justification="Spam application",
        metadata={"approved": True},
        db=db_session
    )

    assert wf_archived.current_state == "Archived"

    # Archived is terminal, so any further transition out must fail
    with pytest.raises(WorkflowValidationError) as exc_info:
        WorkflowEngine.execute_transition(
            workflow_id=wf.workflow_id,
            to_state="Draft",
            actor="admin-1",
            role="admin",
            justification="revive",
            db=db_session
        )
    assert "cannot initiate transitions" in exc_info.value.errors[0]


def test_permission_denied(sample_startup, db_session) -> None:
    wf = create_workflow(
        startup_id=str(sample_startup.id),
        startup_name=sample_startup.startup_name,
        created_by="user-1",
        db=db_session
    )

    # Transition to Submitted: only admin, incubation_manager, evaluator, reviewer, analyst are allowed.
    # If a 'viewer' tries to trigger it:
    with pytest.raises(WorkflowValidationError) as exc_info:
        WorkflowEngine.execute_transition(
            workflow_id=wf.workflow_id,
            to_state="Submitted",
            actor="viewer-1",
            role="viewer",
            justification="submit check",
            metadata={"approved": True},
            db=db_session
        )
    assert "is not authorized" in exc_info.value.errors[0]


def test_approval_required(sample_startup, db_session) -> None:
    wf = create_workflow(
        startup_id=str(sample_startup.id),
        startup_name=sample_startup.startup_name,
        created_by="user-1",
        db=db_session
    )

    # Transitioning to 'Submitted' requires approval.
    # Fails if metadata lacks approved=True.
    with pytest.raises(WorkflowValidationError) as exc_info:
        WorkflowEngine.execute_transition(
            workflow_id=wf.workflow_id,
            to_state="Submitted",
            actor="manager-1",
            role="incubation_manager",
            justification="submit without gate approval",
            metadata={"approved": False},
            db=db_session
        )
    assert "Approval gate requirements not satisfied" in exc_info.value.errors[0]


def test_duplicate_workflow(sample_startup, db_session) -> None:
    wf = create_workflow(
        startup_id=str(sample_startup.id),
        startup_name=sample_startup.startup_name,
        created_by="user-1",
        db=db_session
    )

    # Try registering the exact same workflow object
    with pytest.raises(WorkflowValidationError):
        WorkflowEngine.create_workflow(
            startup_id=str(sample_startup.id),
            startup_name=sample_startup.startup_name,
            created_by="user-1",
            db=db_session
        )


def test_history_generation(sample_startup, db_session) -> None:
    wf = create_workflow(
        startup_id=str(sample_startup.id),
        startup_name=sample_startup.startup_name,
        created_by="user-1",
        db=db_session
    )

    WorkflowEngine.execute_transition(
        workflow_id=wf.workflow_id,
        to_state="Submitted",
        actor="manager-1",
        role="incubation_manager",
        justification="Submit valid app",
        metadata={"approved": True},
        db=db_session
    )

    history = get_history(wf.workflow_id)
    assert len(history) == 1
    assert history[0].transition_id.startswith("TR-")
    assert history[0].actor == "manager-1"
    assert history[0].role == "incubation_manager"
    assert history[0].previous_state == "Draft"
    assert history[0].new_state == "Submitted"
    assert isinstance(history[0].timestamp, datetime)
    assert history[0].reason == "Submit valid app"
    assert history[0].audit_reference.startswith("audit:TR-")


def test_serialization(sample_startup, db_session) -> None:
    wf = create_workflow(
        startup_id=str(sample_startup.id),
        startup_name=sample_startup.startup_name,
        created_by="user-1",
        db=db_session
    )

    WorkflowEngine.execute_transition(
        workflow_id=wf.workflow_id,
        to_state="Submitted",
        actor="manager-1",
        role="incubation_manager",
        justification="Serialize test",
        metadata={"approved": True},
        db=db_session
    )

    history = get_history(wf.workflow_id)

    # 1. JSON Roundtrip
    json_str = WorkflowSerializer.to_json(wf, history)
    assert json_str != ""
    assert wf.workflow_id in json_str

    rebuilt_wf, rebuilt_hist = WorkflowSerializer.from_json(json_str)
    assert rebuilt_wf.workflow_id == wf.workflow_id
    assert rebuilt_wf.workflow_hash == wf.workflow_hash
    assert rebuilt_wf.current_state == wf.current_state
    assert len(rebuilt_hist) == 1
    assert rebuilt_hist[0].transition_id == history[0].transition_id

    # 2. Markdown
    md_str = WorkflowSerializer.export_markdown(wf, history)
    assert "# Startup Workflow Lifecycle:" in md_str
    assert "## Workflow History" in md_str
    assert "manager-1" in md_str

    # 3. HTML
    html_str = WorkflowSerializer.export_html(wf, history)
    assert "<!DOCTYPE html>" in html_str
    assert "Workflow Lifecycle:" in html_str


def test_hash_stability(sample_startup, db_session) -> None:
    wf1 = create_workflow(
        startup_id=str(sample_startup.id),
        startup_name=sample_startup.startup_name,
        created_by="user-1",
        db=db_session
    )

    # Clean registry to generate a duplicate workflow ID
    clear_workflow_registry()

    wf2 = create_workflow(
        startup_id=str(sample_startup.id),
        startup_name=sample_startup.startup_name,
        created_by="user-1",
        db=db_session
    )

    # Should be identical
    assert wf1.workflow_hash == wf2.workflow_hash

    # If mutated, hash must change
    wf2.current_state = "Submitted"
    new_hash = WorkflowEngine._compute_hash(wf2.model_dump())
    assert new_hash != wf1.workflow_hash


def test_concurrent_transitions(sample_startup, db_session) -> None:
    wf = create_workflow(
        startup_id=str(sample_startup.id),
        startup_name=sample_startup.startup_name,
        created_by="user-1",
        db=db_session
    )

    # Run multiple parallel transitions. Since they check from_state in Draft,
    # only one should succeed to change state, and others should fail validation.
    success_count = 0
    failure_count = 0
    lock = threading.Lock()

    def worker():
        nonlocal success_count, failure_count
        try:
            WorkflowEngine.execute_transition(
                workflow_id=wf.workflow_id,
                to_state="Submitted",
                actor="manager-worker",
                role="incubation_manager",
                justification="Concurrent trigger",
                metadata={"approved": True},
                db=db_session
            )
            with lock:
                success_count += 1
        except Exception:
            with lock:
                failure_count += 1

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(worker) for _ in range(20)]
        for f in futures:
            f.result()

    assert success_count == 1
    assert failure_count == 19
    assert get_current_state(wf.workflow_id) == "Submitted"


def test_performance_benchmarks(sample_startup, db_session) -> None:
    startup_id = str(sample_startup.id)
    startup_name = sample_startup.startup_name

    # 1. Creation speed benchmark (< 10 ms)
    t0 = time.perf_counter()
    wf = create_workflow(
        startup_id=startup_id,
        startup_name=startup_name,
        created_by="user-perf",
        db=db_session
    )
    creation_time = (time.perf_counter() - t0) * 1000.0
    assert creation_time < 10.0, f"Workflow creation took {creation_time:.2f} ms (Target: < 10 ms)"

    # 2. Validation speed benchmark (< 5 ms)
    state_machine = WorkflowStateMachine()
    t0 = time.perf_counter()
    errors = validate_transition(
        workflow_id=wf.workflow_id,
        to_state="Submitted",
        actor_role="incubation_manager",
        approval_metadata={"approved": True},
        state_machine=state_machine,
        db=db_session
    )
    validation_time = (time.perf_counter() - t0) * 1000.0
    assert not errors
    assert validation_time < 5.0, f"Workflow validation took {validation_time:.2f} ms (Target: < 5 ms)"

    # 3. Transition speed benchmark (< 20 ms)
    t0 = time.perf_counter()
    wf_updated = WorkflowEngine.execute_transition(
        workflow_id=wf.workflow_id,
        to_state="Submitted",
        actor="user-perf",
        role="incubation_manager",
        justification="Benchmark test",
        metadata={"approved": True},
        state_machine=state_machine,
        db=db_session
    )
    transition_time = (time.perf_counter() - t0) * 1000.0
    assert transition_time < 20.0, f"Transition execution took {transition_time:.2f} ms (Target: < 20 ms)"

    # 4. History lookup speed benchmark (< 10 ms)
    t0 = time.perf_counter()
    history = get_history(wf.workflow_id)
    lookup_time = (time.perf_counter() - t0) * 1000.0
    assert len(history) == 1
    assert lookup_time < 10.0, f"History lookup took {lookup_time:.2f} ms (Target: < 10 ms)"

    # 5. Serialization speed benchmark (< 100 ms)
    t0 = time.perf_counter()
    json_str = WorkflowSerializer.to_json(wf_updated, history)
    serialization_time = (time.perf_counter() - t0) * 1000.0
    assert json_str != ""
    assert serialization_time < 100.0, f"Serialization took {serialization_time:.2f} ms (Target: < 100 ms)"
