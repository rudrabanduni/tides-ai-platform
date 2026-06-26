from typing import Any
from app.modules.intelligence.events import dispatcher, Event


def publish_founder_assessment_started(startup_id: str) -> None:
    """Publishes a FounderAssessmentStarted event with startup metadata."""
    dispatcher.publish(Event(
        event_name="FounderAssessmentStarted",
        payload={"startup_id": startup_id}
    ))


def publish_founder_assessment_completed(startup_id: str, assessment_metadata: dict[str, Any] | None = None) -> None:
    """Publishes a FounderAssessmentCompleted event with startup and assessment details."""
    payload = {"startup_id": startup_id}
    if assessment_metadata:
        payload.update(assessment_metadata)
    dispatcher.publish(Event(
        event_name="FounderAssessmentCompleted",
        payload=payload
    ))


def publish_founder_assessment_failed(startup_id: str, error: str) -> None:
    """Publishes a FounderAssessmentFailed event with startup and error details."""
    dispatcher.publish(Event(
        event_name="FounderAssessmentFailed",
        payload={
            "startup_id": startup_id,
            "error": error
        }
    ))


def publish_product_assessment_started(startup_id: str) -> None:
    """Publishes a ProductAssessmentStarted event with startup metadata."""
    dispatcher.publish(Event(
        event_name="ProductAssessmentStarted",
        payload={"startup_id": startup_id}
    ))


def publish_product_assessment_completed(startup_id: str, assessment_metadata: dict[str, Any] | None = None) -> None:
    """Publishes a ProductAssessmentCompleted event with startup and assessment details."""
    payload = {"startup_id": startup_id}
    if assessment_metadata:
        payload.update(assessment_metadata)
    dispatcher.publish(Event(
        event_name="ProductAssessmentCompleted",
        payload=payload
    ))


def publish_product_assessment_failed(startup_id: str, error: str) -> None:
    """Publishes a ProductAssessmentFailed event with startup and error details."""
    dispatcher.publish(Event(
        event_name="ProductAssessmentFailed",
        payload={
            "startup_id": startup_id,
            "error": error
        }
    ))


def publish_expert_registered(expert_name: str, domain: str) -> None:
    """Publishes an ExpertRegistered event."""
    dispatcher.publish(Event(
        event_name="ExpertRegistered",
        payload={"expert_name": expert_name, "domain": domain}
    ))


def publish_expert_unregistered(expert_name: str) -> None:
    """Publishes an ExpertUnregistered event."""
    dispatcher.publish(Event(
        event_name="ExpertUnregistered",
        payload={"expert_name": expert_name}
    ))


def publish_expert_discovery_started(package_path: str) -> None:
    """Publishes an ExpertDiscoveryStarted event."""
    dispatcher.publish(Event(
        event_name="ExpertDiscoveryStarted",
        payload={"package_path": package_path}
    ))


def publish_expert_discovery_completed(discovered_count: int) -> None:
    """Publishes an ExpertDiscoveryCompleted event."""
    dispatcher.publish(Event(
        event_name="ExpertDiscoveryCompleted",
        payload={"discovered_count": discovered_count}
    ))


def publish_expert_discovery_failed(error: str) -> None:
    """Publishes an ExpertDiscoveryFailed event."""
    dispatcher.publish(Event(
        event_name="ExpertDiscoveryFailed",
        payload={"error": error}
    ))


def publish_market_assessment_started(startup_id: str) -> None:
    """Publishes a MarketAssessmentStarted event with startup metadata."""
    dispatcher.publish(Event(
        event_name="MarketAssessmentStarted",
        payload={"startup_id": startup_id}
    ))


def publish_market_assessment_completed(startup_id: str, assessment_metadata: dict[str, Any] | None = None) -> None:
    """Publishes a MarketAssessmentCompleted event with startup and assessment details."""
    payload = {"startup_id": startup_id}
    if assessment_metadata:
        payload.update(assessment_metadata)
    dispatcher.publish(Event(
        event_name="MarketAssessmentCompleted",
        payload=payload
    ))


def publish_market_assessment_failed(startup_id: str, error: str) -> None:
    """Publishes a MarketAssessmentFailed event with startup and error details."""
    dispatcher.publish(Event(
        event_name="MarketAssessmentFailed",
        payload={
            "startup_id": startup_id,
            "error": error
        }
    ))


def publish_financial_assessment_started(startup_id: str) -> None:
    """Publishes a FinancialAssessmentStarted event with startup metadata."""
    dispatcher.publish(Event(
        event_name="FinancialAssessmentStarted",
        payload={"startup_id": startup_id}
    ))


def publish_financial_assessment_completed(startup_id: str, assessment_metadata: dict[str, Any] | None = None) -> None:
    """Publishes a FinancialAssessmentCompleted event with startup and assessment details."""
    payload = {"startup_id": startup_id}
    if assessment_metadata:
        payload.update(assessment_metadata)
    dispatcher.publish(Event(
        event_name="FinancialAssessmentCompleted",
        payload=payload
    ))


def publish_financial_assessment_failed(startup_id: str, error: str) -> None:
    """Publishes a FinancialAssessmentFailed event with startup and error details."""
    dispatcher.publish(Event(
        event_name="FinancialAssessmentFailed",
        payload={
            "startup_id": startup_id,
            "error": error
        }
    ))


def publish_trl_assessment_started(startup_id: str) -> None:
    """Publishes a TRLAssessmentStarted event with startup metadata."""
    dispatcher.publish(Event(
        event_name="TRLAssessmentStarted",
        payload={"startup_id": startup_id}
    ))


def publish_trl_assessment_completed(startup_id: str, assessment_metadata: dict[str, Any] | None = None) -> None:
    """Publishes a TRLAssessmentCompleted event with startup and assessment details."""
    payload = {"startup_id": startup_id}
    if assessment_metadata:
        payload.update(assessment_metadata)
    dispatcher.publish(Event(
        event_name="TRLAssessmentCompleted",
        payload=payload
    ))


def publish_trl_assessment_failed(startup_id: str, error: str) -> None:
    """Publishes a TRLAssessmentFailed event with startup and error details."""
    dispatcher.publish(Event(
        event_name="TRLAssessmentFailed",
        payload={
            "startup_id": startup_id,
            "error": error
        }
    ))


def publish_competition_assessment_started(startup_id: str) -> None:
    """Publishes a CompetitionAssessmentStarted event with startup metadata."""
    dispatcher.publish(Event(
        event_name="CompetitionAssessmentStarted",
        payload={"startup_id": startup_id}
    ))


def publish_competition_assessment_completed(startup_id: str, assessment_metadata: dict[str, Any] | None = None) -> None:
    """Publishes a CompetitionAssessmentCompleted event with startup and assessment details."""
    payload = {"startup_id": startup_id}
    if assessment_metadata:
        payload.update(assessment_metadata)
    dispatcher.publish(Event(
        event_name="CompetitionAssessmentCompleted",
        payload=payload
    ))


def publish_competition_assessment_failed(startup_id: str, error: str) -> None:
    """Publishes a CompetitionAssessmentFailed event with startup and error details."""
    dispatcher.publish(Event(
        event_name="CompetitionAssessmentFailed",
        payload={
            "startup_id": startup_id,
            "error": error
        }
    ))


def publish_ip_assessment_started(startup_id: str) -> None:
    """Publishes an IPAssessmentStarted event with startup metadata."""
    dispatcher.publish(Event(
        event_name="IPAssessmentStarted",
        payload={"startup_id": startup_id}
    ))


def publish_ip_assessment_completed(startup_id: str, assessment_metadata: dict[str, Any] | None = None) -> None:
    """Publishes an IPAssessmentCompleted event with startup and assessment details."""
    payload = {"startup_id": startup_id}
    if assessment_metadata:
        payload.update(assessment_metadata)
    dispatcher.publish(Event(
        event_name="IPAssessmentCompleted",
        payload=payload
    ))


def publish_ip_assessment_failed(startup_id: str, error: str) -> None:
    """Publishes an IPAssessmentFailed event with startup and error details."""
    dispatcher.publish(Event(
        event_name="IPAssessmentFailed",
        payload={
            "startup_id": startup_id,
            "error": error
        }
    ))


def publish_risk_assessment_started(startup_id: str) -> None:
    """Publishes a RiskAssessmentStarted event with startup metadata."""
    dispatcher.publish(Event(
        event_name="RiskAssessmentStarted",
        payload={"startup_id": startup_id}
    ))


def publish_risk_assessment_completed(startup_id: str, assessment_metadata: dict[str, Any] | None = None) -> None:
    """Publishes a RiskAssessmentCompleted event with startup and assessment details."""
    payload = {"startup_id": startup_id}
    if assessment_metadata:
        payload.update(assessment_metadata)
    dispatcher.publish(Event(
        event_name="RiskAssessmentCompleted",
        payload=payload
    ))


def publish_risk_assessment_failed(startup_id: str, error: str) -> None:
    """Publishes a RiskAssessmentFailed event with startup and error details."""
    dispatcher.publish(Event(
        event_name="RiskAssessmentFailed",
        payload={
            "startup_id": startup_id,
            "error": error
        }
    ))
