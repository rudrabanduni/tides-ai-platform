from typing import List, Any
from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType
from app.modules.evaluation.correlation.correlation_models import CorrelationNode


def get_correlation(graph: ObservationGraph, correlation_id: str) -> CorrelationNode | None:
    """O(1) retrieval of correlation node by ID."""
    return graph.correlations.get(correlation_id)


def get_observation_correlations(graph: ObservationGraph, observation_id: str) -> List[CorrelationNode]:
    """Retrieves all correlation nodes linked to the observation in O(1) time."""
    if hasattr(graph, "correlations_by_observation") and observation_id in graph.correlations_by_observation:
        return graph.correlations_by_observation[observation_id]
    corrs = []
    # Incoming edges point from CorrelationNode to ObservationNode via RELATED_TO
    for edge in graph.in_edges.get(observation_id, []):
        if edge.source_type == NodeType.CORRELATION and edge.relationship == "RELATED_TO":
            corr = graph.correlations.get(edge.source_id)
            if corr and corr not in corrs:
                corrs.append(corr)
    return corrs


def get_corroborations(graph: ObservationGraph, observation_id: str) -> List[CorrelationNode]:
    """Retrieves CORROBORATES correlation nodes linked to the observation."""
    return [c for c in get_observation_correlations(graph, observation_id) if c.correlation_type == "CORROBORATES"]


def get_contradictions(graph: ObservationGraph, observation_id: str) -> List[CorrelationNode]:
    """Retrieves CONTRADICTS correlation nodes linked to the observation."""
    return [c for c in get_observation_correlations(graph, observation_id) if c.correlation_type == "CONTRADICTS"]


def get_dependencies(graph: ObservationGraph, observation_id: str) -> List[CorrelationNode]:
    """Retrieves DEPENDS_ON correlation nodes linked to the observation."""
    return [c for c in get_observation_correlations(graph, observation_id) if c.correlation_type == "DEPENDS_ON"]
