from typing import Any, Dict
from app.modules.intelligence.events import dispatcher, Event


def publish_committee_started(startup_id: str, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "startup_id": startup_id,
        **(payload or {})
    }
    dispatcher.publish(Event("CommitteeStarted", event_payload))


def publish_committee_completed(startup_id: str, report_id: str, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "startup_id": startup_id,
        "report_id": report_id,
        **(payload or {})
    }
    dispatcher.publish(Event("CommitteeCompleted", event_payload))


def publish_committee_failed(startup_id: str, error: str, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "startup_id": startup_id,
        "error": error,
        **(payload or {})
    }
    dispatcher.publish(Event("CommitteeFailed", event_payload))


def publish_committee_finding_created(report_id: str, finding_id: str, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "report_id": report_id,
        "finding_id": finding_id,
        **(payload or {})
    }
    dispatcher.publish(Event("CommitteeFindingCreated", event_payload))


def publish_committee_concern_created(report_id: str, concern_id: str, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "report_id": report_id,
        "concern_id": concern_id,
        **(payload or {})
    }
    dispatcher.publish(Event("CommitteeConcernCreated", event_payload))


def publish_committee_consensus_built(report_id: str, agreement_level: float, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "report_id": report_id,
        "agreement_level": agreement_level,
        **(payload or {})
    }
    dispatcher.publish(Event("CommitteeConsensusBuilt", event_payload))


def publish_committee_recommendation_generated(report_id: str, recommendation: str, payload: Dict[str, Any] | None = None) -> None:
    event_payload = {
        "report_id": report_id,
        "recommendation": recommendation,
        **(payload or {})
    }
    dispatcher.publish(Event("CommitteeRecommendationGenerated", event_payload))
