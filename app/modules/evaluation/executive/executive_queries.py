from typing import List, Optional, Any, Dict
from app.modules.evaluation.graph.graph_models import ObservationGraph
from app.modules.evaluation.executive.executive_models import (
    ExecutiveAssessment, ExecutiveSummary, ExecutiveFinding
)


def get_executive_assessment(graph: ObservationGraph) -> Optional[ExecutiveAssessment]:
    """Retrieves the ExecutiveAssessment from the graph in O(1) time."""
    return graph.executive_assessment


def get_executive_summary(graph: ObservationGraph) -> Optional[ExecutiveSummary]:
    """Retrieves the ExecutiveSummary from the graph's executive assessment in O(1) time."""
    exec_node = graph.executive_assessment
    return exec_node.summary if exec_node else None


def get_key_risks(graph: ObservationGraph) -> List[ExecutiveFinding]:
    """Retrieves all major risks identified in the executive assessment in O(1) time."""
    exec_node = graph.executive_assessment
    return exec_node.major_risks if exec_node else []


def get_unresolved_conflicts(graph: ObservationGraph) -> List[str]:
    """Retrieves list of unresolved conflict IDs in the executive assessment in O(1) time."""
    exec_node = graph.executive_assessment
    return exec_node.unresolved_conflicts if exec_node else []


def trace_executive_finding(graph: ObservationGraph, finding_id: str) -> Optional[Any]:
    """Retrieves the complete pedigree provenance trace mapping for a specific finding in O(1) time."""
    exec_node = graph.executive_assessment
    if exec_node and finding_id in exec_node.traceability:
        return exec_node.traceability[finding_id]
    return None


def get_readiness_level(graph: ObservationGraph) -> str:
    """Retrieves readiness level (TRL) string from the graph's executive assessment in O(1) time."""
    exec_node = graph.executive_assessment
    return exec_node.readiness_level if exec_node else "TRL-1"
