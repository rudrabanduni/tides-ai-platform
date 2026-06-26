from typing import List, Optional, Any, Dict
from app.modules.evaluation.graph.graph_models import ObservationGraph
from app.modules.evaluation.investment.investment_models import (
    InvestmentAssessment, InvestmentRecommendation
)


def get_investment_assessment(graph: ObservationGraph) -> Optional[InvestmentAssessment]:
    """Retrieves the InvestmentAssessment from the graph in O(1) time."""
    return graph.investment_assessment


def get_investment_score(graph: ObservationGraph) -> Optional[float]:
    """Retrieves the investment score from the graph's investment assessment in O(1) time."""
    node = graph.investment_assessment
    return node.investment_score if node else None


def get_recommendation(graph: ObservationGraph) -> Optional[str]:
    """Retrieves the recommendation string from the graph's investment assessment in O(1) time."""
    node = graph.investment_assessment
    return node.recommendation.value if node else None


def get_strengths(graph: ObservationGraph) -> List[str]:
    """Retrieves list of key strengths in the investment assessment in O(1) time."""
    node = graph.investment_assessment
    return node.strengths if node else []


def get_major_risks(graph: ObservationGraph) -> List[str]:
    """Retrieves list of major risks in the investment assessment in O(1) time."""
    node = graph.investment_assessment
    return node.major_risks if node else []


def trace_investment_decision(graph: ObservationGraph) -> Optional[Dict[str, Any]]:
    """Retrieves the complete pedigree provenance trace mapping for the investment decision in O(1) time."""
    node = graph.investment_assessment
    return node.traceability if node else None
