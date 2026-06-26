from typing import Any, Dict
from app.modules.intelligence.events import dispatcher, Event


def publish_version_created(startup_id: str, version_number: int, version_id: str, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "startup_id": startup_id,
        "version_number": version_number,
        "version_id": version_id,
        **(payload or {})
    }
    dispatcher.publish(Event("VersionCreated", event_payload))


def publish_version_loaded(startup_id: str, version_number: int, version_id: str, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "startup_id": startup_id,
        "version_number": version_number,
        "version_id": version_id,
        **(payload or {})
    }
    dispatcher.publish(Event("VersionLoaded", event_payload))


def publish_version_compared(startup_id: str, from_version: int, to_version: int, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "startup_id": startup_id,
        "from_version": from_version,
        "to_version": to_version,
        **(payload or {})
    }
    dispatcher.publish(Event("VersionCompared", event_payload))


def publish_delta_generated(delta_id: str, from_version: int, to_version: int, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "delta_id": delta_id,
        "from_version": from_version,
        "to_version": to_version,
        **(payload or {})
    }
    dispatcher.publish(Event("DeltaGenerated", event_payload))


def publish_rollback_started(startup_id: str, target_version: int, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "startup_id": startup_id,
        "target_version": target_version,
        **(payload or {})
    }
    dispatcher.publish(Event("RollbackStarted", event_payload))


def publish_rollback_completed(startup_id: str, target_version: int, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "startup_id": startup_id,
        "target_version": target_version,
        **(payload or {})
    }
    dispatcher.publish(Event("RollbackCompleted", event_payload))


def publish_version_validation_failed(startup_id: str, version_number: int, error: str, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "startup_id": startup_id,
        "version_number": version_number,
        "error": error,
        **(payload or {})
    }
    dispatcher.publish(Event("VersionValidationFailed", event_payload))
