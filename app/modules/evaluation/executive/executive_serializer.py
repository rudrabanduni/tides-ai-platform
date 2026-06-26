import json
from typing import Dict, Any, Optional
from app.modules.evaluation.graph.graph_models import ObservationGraph
from app.modules.evaluation.graph.graph_serializer import to_json as graph_to_json, from_json as graph_from_json


class ExecutiveSerializer:
    """Handles JSON serialization, deserialization, and generating audit reports for TIE Executive Assessments."""

    @staticmethod
    def to_json(graph: ObservationGraph) -> str:
        """Serializes the entire ObservationGraph, including executive assessment components, to JSON."""
        return graph_to_json(graph)

    @staticmethod
    def from_json(json_str: str) -> ObservationGraph:
        """Reconstructs the ObservationGraph, including executive assessment components, from JSON."""
        return graph_from_json(json_str)

    @staticmethod
    def export_executive_report(graph: ObservationGraph) -> Dict[str, Any]:
        """Compiles a comprehensive executive-facing audit report of the graph."""
        exec_node = graph.executive_assessment
        if not exec_node:
            return {
                "graph_id": graph.graph_id,
                "graph_version": graph.graph_version,
                "graph_hash": graph.graph_hash,
                "status": "Executive assessment has not been generated."
            }

        # Format summary
        summary = exec_node.summary
        formatted_summary = {
            "overview": summary.overview,
            "strengths": list(summary.strengths),
            "weaknesses": list(summary.weaknesses),
            "opportunities": list(summary.opportunities),
            "threats": list(summary.threats),
            "missing_information": list(summary.missing_information)
        }

        # Format findings
        observations = []
        for o in exec_node.key_observations:
            observations.append({
                "finding_id": o.finding_id,
                "description": o.description,
                "confidence": o.confidence,
                "supporting_observations": list(o.supporting_observations)
            })

        risks = []
        for r in exec_node.major_risks:
            risks.append({
                "finding_id": r.finding_id,
                "description": r.description,
                "confidence": r.confidence,
                "supporting_observations": list(r.supporting_observations)
            })

        stats = graph.graph_stats
        metrics = {
            "total_documents": stats.document_count,
            "total_claims": stats.claim_count,
            "total_evidence": stats.evidence_count,
            "total_observations": stats.observation_count,
            "total_assessments": stats.assessment_count,
            "total_correlations": stats.correlation_count,
            "total_conflicts": stats.conflict_count,
            "total_resolutions": stats.resolution_count,
            "graph_confidence": exec_node.confidence
        }

        return {
            "graph_id": graph.graph_id,
            "graph_version": graph.graph_version,
            "graph_hash": graph.graph_hash,
            "generated_at": str(exec_node.generated_at),
            "assessment_id": exec_node.assessment_id,
            "readiness_level": exec_node.readiness_level,
            "confidence": exec_node.confidence,
            "evidence_strength": exec_node.evidence_strength,
            "summary": formatted_summary,
            "key_observations": observations,
            "major_risks": risks,
            "unresolved_conflicts": list(exec_node.unresolved_conflicts),
            "metrics": metrics
        }
