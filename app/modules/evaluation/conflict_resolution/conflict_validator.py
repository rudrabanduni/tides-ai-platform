from typing import List
from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType


class ConflictResolutionValidator:
    """Performs validation checks on ResolutionNodes and ResolutionEdges in an ObservationGraph."""

    @staticmethod
    def validate(graph: ObservationGraph) -> List[str]:
        errors = []
        valid_types = {"FACTUAL", "NUMERICAL", "TEMPORAL", "SOURCE_PRIORITY", "CONSENSUS", "INSUFFICIENT_EVIDENCE"}

        # Gather all nodes to check existence and NodeType
        all_nodes = {}
        for coll in [graph.documents, graph.evidence, graph.claims, graph.observations,
                     graph.assessments, graph.conflicts, graph.risks, graph.questions,
                     graph.correlations, graph.resolutions]:
            for nid, node in coll.items():
                if nid in all_nodes:
                    errors.append(f"Duplicate Node ID: '{nid}' exists in multiple collections.")
                all_nodes[nid] = node

        # 1. Validate ResolutionNodes
        for res_id, res in graph.resolutions.items():
            # Rule: ID matches
            if res.resolution_id != res_id:
                errors.append(f"ID Mismatch: ResolutionNode key '{res_id}' does not match resolution_id '{res.resolution_id}'")

            # Rule: Type matches
            if res.node_type != NodeType.RESOLUTION:
                errors.append(f"NodeType Mismatch: ResolutionNode '{res_id}' has node_type '{res.node_type}' instead of RESOLUTION")

            # Rule: Valid resolution type
            if res.resolution_type not in valid_types:
                errors.append(f"Invalid Resolution Type: '{res.resolution_type}' on '{res_id}'")

            # Rule: Conflict exists
            if res.conflict_id not in graph.conflicts and res.conflict_id not in graph.correlations:
                errors.append(f"Dangling Reference: Conflict ID '{res.conflict_id}' on resolution '{res_id}' does not exist in graph conflicts or correlations.")

            # Rule: Preferred observation exists if defined
            if res.preferred_observation_id:
                if res.preferred_observation_id not in graph.observations:
                    errors.append(f"Dangling Reference: Preferred observation '{res.preferred_observation_id}' on resolution '{res_id}' does not exist in graph observations.")

            # Rule: Supporting evidence exist
            for eid in res.supporting_evidence:
                if eid not in graph.evidence:
                    errors.append(f"Dangling Reference: Supporting evidence '{eid}' on resolution '{res_id}' does not exist in graph evidence.")

            # Rule: Supporting assessments exist
            for aid in res.supporting_assessments:
                if aid not in graph.assessments:
                    errors.append(f"Dangling Reference: Supporting assessment '{aid}' on resolution '{res_id}' does not exist in graph assessments.")

            # Rule: Supporting claims exist
            for cid in res.supporting_claims:
                if cid not in graph.claims:
                    errors.append(f"Dangling Reference: Supporting claim '{cid}' on resolution '{res_id}' does not exist in graph claims.")

            # Rule: Confidence bounds
            if not (0.0 <= res.confidence <= 1.0):
                errors.append(f"Invalid Confidence: {res.confidence} on resolution '{res_id}' must be between 0.0 and 1.0.")

            # Rule: No orphan resolutions
            # Every resolution node must have at least one resolves edge
            resolves_edges = [e for e in graph.resolution_edges 
                              if e.source_id == res_id and e.relationship == "RESOLVES"]
            if not resolves_edges:
                errors.append(f"Orphan Resolution: Resolution '{res_id}' has no RESOLVES relationship.")

        # 2. Validate ResolutionEdges
        for edge in graph.resolution_edges:
            # Rule: No self references
            if edge.source_id == edge.target_id:
                errors.append(f"Self-Reference: Edge has identical source and target '{edge.source_id}'")

            source_node = all_nodes.get(edge.source_id)
            target_node = all_nodes.get(edge.target_id)

            # Rule: Dangling reference check
            if not source_node:
                errors.append(f"Broken Edge Source: Edge references non-existent source node '{edge.source_id}'")
            else:
                # Rule: NodeType consistency (source)
                if source_node.node_type != edge.source_type:
                    errors.append(f"NodeType Mismatch: Source node '{edge.source_id}' is actual type '{source_node.node_type}' but edge specifies '{edge.source_type}'")

            if not target_node:
                errors.append(f"Broken Edge Target: Edge references non-existent target node '{edge.target_id}'")
            else:
                # Rule: NodeType consistency (target)
                if target_node.node_type != edge.target_type:
                    errors.append(f"NodeType Mismatch: Target node '{edge.target_id}' is actual type '{target_node.node_type}' but edge specifies '{edge.target_type}'")

        return errors
