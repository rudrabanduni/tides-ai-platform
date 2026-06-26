from typing import Any, Dict
from app.modules.intelligence.events import dispatcher, Event


def publish_workflow_created(workflow_id: str, startup_id: str, startup_name: str, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "workflow_id": workflow_id,
        "startup_id": startup_id,
        "startup_name": startup_name,
        **(payload or {})
    }
    dispatcher.publish(Event("WorkflowCreated", event_payload))


def publish_workflow_started(workflow_id: str, startup_id: str, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "workflow_id": workflow_id,
        "startup_id": startup_id,
        **(payload or {})
    }
    dispatcher.publish(Event("WorkflowStarted", event_payload))


def publish_workflow_transition_started(workflow_id: str, from_state: str, to_state: str, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "workflow_id": workflow_id,
        "from_state": from_state,
        "to_state": to_state,
        **(payload or {})
    }
    dispatcher.publish(Event("WorkflowTransitionStarted", event_payload))


def publish_workflow_transition_completed(workflow_id: str, from_state: str, to_state: str, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "workflow_id": workflow_id,
        "from_state": from_state,
        "to_state": to_state,
        **(payload or {})
    }
    dispatcher.publish(Event("WorkflowTransitionCompleted", event_payload))


def publish_workflow_transition_failed(workflow_id: str, from_state: str, to_state: str, error: str, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "workflow_id": workflow_id,
        "from_state": from_state,
        "to_state": to_state,
        "error": error,
        **(payload or {})
    }
    dispatcher.publish(Event("WorkflowTransitionFailed", event_payload))


def publish_workflow_rolled_back(workflow_id: str, from_state: str, to_state: str, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "workflow_id": workflow_id,
        "from_state": from_state,
        "to_state": to_state,
        **(payload or {})
    }
    dispatcher.publish(Event("WorkflowRolledBack", event_payload))


def publish_workflow_completed(workflow_id: str, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "workflow_id": workflow_id,
        **(payload or {})
    }
    dispatcher.publish(Event("WorkflowCompleted", event_payload))


def publish_workflow_archived(workflow_id: str, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "workflow_id": workflow_id,
        **(payload or {})
    }
    dispatcher.publish(Event("WorkflowArchived", event_payload))
