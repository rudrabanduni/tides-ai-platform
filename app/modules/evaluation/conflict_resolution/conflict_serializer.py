import json
from typing import Any, Dict
from app.modules.evaluation.graph.graph_models import ObservationGraph
from app.modules.evaluation.graph.graph_serializer import to_json as graph_to_json, from_json as graph_from_json


class ConflictSerializer:
    """Handles JSON serialization, deserialization, and generation of reports for TIE Conflict Resolutions."""

    @staticmethod
    def to_json(graph: ObservationGraph) -> str:
        """Serializes the entire ObservationGraph, including conflict resolution components, to JSON."""
        return graph_to_json(graph)

    @staticmethod
    def from_json(json_str: str) -> ObservationGraph:
        """Reconstructs the ObservationGraph, including conflict resolution components, from JSON."""
        return graph_from_json(json_str)

    @staticmethod
    def export_resolution_report(graph: ObservationGraph) -> Dict[str, Any]:
        """Compiles a detailed conflict resolution report including stats, resolutions, and integrity hashes."""
        resolutions_list = []
        for res_id, res in graph.resolutions.items():
            resolutions_list.append({
                "resolution_id": res.resolution_id,
                "conflict_id": res.conflict_id,
                "resolution_type": res.resolution_type,
                "preferred_observation_id": res.preferred_observation_id,
                "confidence": res.confidence,
                "reasoning": res.reasoning,
                "supporting_claims": res.supporting_claims,
                "supporting_evidence": res.supporting_evidence,
                "supporting_assessments": res.supporting_assessments,
                "created_at": str(res.created_at)
            })

        edges_list = []
        for edge in graph.resolution_edges:
            edges_list.append({
                "source_id": edge.source_id,
                "source_type": str(edge.source_type),
                "target_id": edge.target_id,
                "target_type": str(edge.target_type),
                "relationship": edge.relationship
            })

        stats = graph.graph_stats
        return {
            "graph_id": graph.graph_id,
            "graph_version": graph.graph_version,
            "graph_hash": graph.graph_hash,
            "statistics": {
                "resolution_count": stats.resolution_count,
                "resolved_conflicts": stats.resolved_conflicts,
                "unresolved_conflicts": stats.unresolved_conflicts,
                "total_conflicts": stats.conflict_count,
                "total_correlations": stats.correlation_count
            },
            "resolutions": resolutions_list,
            "resolution_edges": edges_list
        }
