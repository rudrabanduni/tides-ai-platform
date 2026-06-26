import threading
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session
from app.modules.workflow.workflow_models import Workflow, WorkflowHistoryEntry
from app.modules.workflow.workflow_state_machine import WorkflowStateMachine

# Thread-safe global stores
_workflow_registry: Dict[str, Workflow] = {}
_history_registry: Dict[str, List[WorkflowHistoryEntry]] = {}
_registry_lock = threading.RLock()


def register_workflow(workflow: Workflow) -> None:
    """Store a workflow in the registry."""
    with _registry_lock:
        _workflow_registry[workflow.workflow_id] = workflow


def register_history_entry(workflow_id: str, entry: WorkflowHistoryEntry) -> None:
    """Append a history entry for a workflow."""
    with _registry_lock:
        if workflow_id not in _history_registry:
            _history_registry[workflow_id] = []
        _history_registry[workflow_id].append(entry)


def clear_workflow_registry() -> None:
    """Clear all workflow data (test helper)."""
    with _registry_lock:
        _workflow_registry.clear()
        _history_registry.clear()


# --- Query APIs ---

def create_workflow(
    startup_id: str,
    startup_name: str,
    created_by: str,
    state_machine: Optional[WorkflowStateMachine] = None,
    metadata: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None
) -> Workflow:
    """Create and register a new workflow. Delegates to WorkflowEngine."""
    from app.modules.workflow.workflow_engine import WorkflowEngine
    return WorkflowEngine.create_workflow(
        startup_id=startup_id,
        startup_name=startup_name,
        created_by=created_by,
        state_machine=state_machine,
        metadata=metadata,
        db=db
    )


def get_workflow(workflow_id: str) -> Optional[Workflow]:
    """Retrieve a workflow by ID from the global registry."""
    with _registry_lock:
        return _workflow_registry.get(workflow_id)


def get_current_state(workflow_id: str) -> Optional[str]:
    """Get the current state of a workflow."""
    with _registry_lock:
        wf = _workflow_registry.get(workflow_id)
        return wf.current_state if wf else None


def get_history(workflow_id: str) -> List[WorkflowHistoryEntry]:
    """Get history trail of transition entries for a workflow."""
    with _registry_lock:
        return list(_history_registry.get(workflow_id, []))


def list_workflows() -> List[Workflow]:
    """List all workflows in the registry."""
    with _registry_lock:
        return list(_workflow_registry.values())


def list_by_state(state_id: str) -> List[Workflow]:
    """List all workflows currently in the specified state."""
    with _registry_lock:
        return [w for w in _workflow_registry.values() if w.current_state == state_id]


def list_active_workflows(state_machine: WorkflowStateMachine) -> List[Workflow]:
    """List all workflows that are in active (non-terminal) states."""
    with _registry_lock:
        active = []
        for w in _workflow_registry.values():
            state = state_machine.get_state(w.current_state)
            if state and not state.terminal:
                active.append(w)
        return active


def list_completed_workflows(state_machine: WorkflowStateMachine) -> List[Workflow]:
    """List all workflows that are in completed (terminal) states."""
    with _registry_lock:
        completed = []
        for w in _workflow_registry.values():
            state = state_machine.get_state(w.current_state)
            if state and state.terminal:
                completed.append(w)
        return completed


def rollback_workflow(
    workflow_id: str,
    target_state: str,
    actor: str,
    role: str,
    reason: str,
    state_machine: WorkflowStateMachine,
    db: Optional[Session] = None
) -> Workflow:
    """Rollback a workflow to a previously visited state. Delegates to WorkflowEngine."""
    from app.modules.workflow.workflow_engine import WorkflowEngine
    return WorkflowEngine.rollback_workflow(
        workflow_id=workflow_id,
        target_state=target_state,
        actor=actor,
        role=role,
        reason=reason,
        state_machine=state_machine,
        db=db
    )


def validate_transition(
    workflow_id: str,
    to_state: str,
    actor_role: str,
    approval_metadata: Dict[str, Any],
    state_machine: WorkflowStateMachine,
    db: Optional[Session] = None
) -> List[str]:
    """Validate if a transition is permitted. Returns a list of error strings."""
    wf = get_workflow(workflow_id)
    if not wf:
        return [f"Workflow '{workflow_id}' does not exist."]
        
    from app.modules.workflow.workflow_validator import WorkflowValidator
    res = WorkflowValidator.validate_transition(
        workflow=wf,
        to_state=to_state,
        actor_role=actor_role,
        approval_metadata=approval_metadata,
        state_machine=state_machine,
        db=db
    )
    return res["errors"]
