import threading
from typing import Dict, Optional

from app.modules.evaluation.graph.graph_models import ObservationGraph
from app.modules.explainability.explanation_models import ExplanationNode
from app.modules.explainability.explanation_engine import ExplanationEngine

# Process-global thread-safe storage for generated ExplanationNodes
_explanation_registry: Dict[str, ExplanationNode] = {}
_registry_lock = threading.RLock()

_engine = ExplanationEngine()


def register_explanation(explanation: ExplanationNode) -> None:
    """Store an explanation in the global registry."""
    with _registry_lock:
        _explanation_registry[explanation.explanation_id] = explanation


def get_explanation(explanation_id: str) -> Optional[ExplanationNode]:
    """Retrieve an explanation by ID from the global registry."""
    with _registry_lock:
        return _explanation_registry.get(explanation_id)


def explain_observation(graph: ObservationGraph, observation_id: str) -> ExplanationNode:
    """Generate and register an explanation for an ObservationNode."""
    exp = _engine.explain_observation(graph, observation_id)
    register_explanation(exp)
    return exp


def explain_assessment(graph: ObservationGraph, assessment_id: str) -> ExplanationNode:
    """Generate and register an explanation for an AssessmentNode."""
    exp = _engine.explain_assessment(graph, assessment_id)
    register_explanation(exp)
    return exp


def explain_risk(graph: ObservationGraph, risk_id: str) -> ExplanationNode:
    """Generate and register an explanation for a RiskNode."""
    exp = _engine.explain_risk(graph, risk_id)
    register_explanation(exp)
    return exp


def explain_committee_decision(graph: ObservationGraph, decision_id: str) -> ExplanationNode:
    """Generate and register an explanation for a Committee Decision Node."""
    exp = _engine.explain_committee_decision(graph, decision_id)
    register_explanation(exp)
    return exp


def explain_portfolio_rank(graph: ObservationGraph, startup_id: str) -> ExplanationNode:
    """Generate and register an explanation for a Portfolio Entry Ranking."""
    exp = _engine.explain_portfolio_ranking(graph, startup_id)
    register_explanation(exp)
    return exp


def explain_investment(graph: ObservationGraph, investment_id: str) -> ExplanationNode:
    """Generate and register an explanation for an Investment Decision Node."""
    exp = _engine.explain_investment_decision(graph, investment_id)
    register_explanation(exp)
    return exp


def clear_explanation_registry() -> None:
    """Clear all stored explanations (test helper)."""
    with _registry_lock:
        _explanation_registry.clear()
