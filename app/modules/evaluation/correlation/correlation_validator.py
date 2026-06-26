from typing import List
from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType


class CorrelationValidator:
    """Performs integrity audits on correlation nodes and relationship edges inside an ObservationGraph."""

    @staticmethod
    def validate(graph: ObservationGraph) -> List[str]:
        errors = []
        valid_types = {"CORROBORATES", "CONTRADICTS", "DEPENDS_ON", "SUPPORTS", "WEAKENS", "DUPLICATES"}

        for corr_id, corr in graph.correlations.items():
            # Rule 2: Correlation type must be valid
            if corr.correlation_type not in valid_types:
                errors.append(f"Invalid Correlation Type: '{corr.correlation_type}' on '{corr_id}'")

            # Rule 5: Confidence must be within [0.0, 1.0]
            if not (0.0 <= corr.confidence <= 1.0):
                errors.append(f"Invalid Correlation Confidence: {corr.confidence} on '{corr_id}'")

            # Rule 1: Every correlation references exactly two observations
            related_edges = graph.out_edges.get(corr_id, [])
            target_ids = []
            for edge in related_edges:
                if edge.relationship == "RELATED_TO":
                    # NodeType consistency checks
                    if edge.source_type != NodeType.CORRELATION:
                        errors.append(f"NodeType Mismatch: Edge source '{edge.source_id}' must be NodeType.CORRELATION, but got {edge.source_type}")
                    if edge.target_type != NodeType.OBSERVATION:
                        errors.append(f"NodeType Mismatch: Edge target '{edge.target_id}' must be NodeType.OBSERVATION, but got {edge.target_type}")
                    
                    target_ids.append(edge.target_id)

            if len(target_ids) != 2:
                errors.append(f"Cardinality Violation: Correlation '{corr_id}' must reference exactly two observations, but got {len(target_ids)}: {target_ids}")

            # Rule 3: No self-correlation
            if len(target_ids) >= 2 and target_ids[0] == target_ids[1]:
                errors.append(f"Self-Correlation: Correlation '{corr_id}' references observation '{target_ids[0]}' twice.")

            # Rule 4: Referenced observations must exist in the graph
            for tid in target_ids:
                if tid not in graph.observations:
                    errors.append(f"Broken Reference: Correlation '{corr_id}' references non-existent observation '{tid}'")

        return errors
