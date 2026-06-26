import json
from typing import Dict, Any, Optional
from app.modules.evaluation.graph.graph_models import ObservationGraph
from app.modules.evaluation.graph.graph_serializer import to_json as graph_to_json, from_json as graph_from_json


class InvestmentSerializer:
    """Handles JSON serialization, deserialization, and exporting reports for TIE Investment Assessments."""

    @staticmethod
    def to_json(graph: ObservationGraph) -> str:
        """Serializes the entire ObservationGraph, including investment assessment components, to JSON."""
        return graph_to_json(graph)

    @staticmethod
    def from_json(json_str: str) -> ObservationGraph:
        """Reconstructs the ObservationGraph, including investment assessment components, from JSON."""
        return graph_from_json(json_str)

    @staticmethod
    def export_investment_report(graph: ObservationGraph) -> Dict[str, Any]:
        """Compiles a comprehensive investment-facing audit report of the graph."""
        node = graph.investment_assessment
        if not node:
            return {
                "graph_id": graph.graph_id,
                "graph_version": graph.graph_version,
                "graph_hash": graph.graph_hash,
                "status": "Investment assessment has not been generated."
            }

        # Form metrics
        metrics = node.metadata.get("metrics", {}) if node.metadata else {}

        return {
            "graph_id": graph.graph_id,
            "graph_version": graph.graph_version,
            "graph_hash": graph.graph_hash,
            "generated_at": str(node.generated_at),
            "assessment_id": node.assessment_id,
            "recommendation": node.recommendation.value,
            "investment_score": node.investment_score,
            "confidence": node.confidence,
            "readiness_score": node.readiness_score,
            "risk_score": node.risk_score,
            "technology_score": node.technology_score,
            "market_score": node.market_score,
            "founder_score": node.founder_score,
            "financial_score": node.financial_score,
            "competition_score": node.competition_score,
            "executive_summary": node.executive_summary,
            "strengths": list(node.strengths),
            "weaknesses": list(node.weaknesses),
            "major_risks": list(node.major_risks),
            "investment_rationale": node.investment_rationale,
            "missing_information": list(node.missing_information),
            "follow_up_questions": list(node.follow_up_questions),
            "metrics": metrics
        }
