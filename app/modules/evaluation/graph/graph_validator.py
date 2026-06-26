from typing import List
from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType


class GraphValidator:
    """Performs structural, referential, and NodeType consistency audits on an ObservationGraph."""

    @staticmethod
    def validate(graph: ObservationGraph) -> List[str]:
        errors = []

        # Gather all nodes to check existence and NodeType
        all_nodes = {}
        for coll in [graph.documents, graph.evidence, graph.claims, graph.observations,
                     graph.assessments, graph.conflicts, graph.risks, graph.questions, graph.correlations]:
            for nid, node in coll.items():
                all_nodes[nid] = node

        # 1. Resolve References & Validate NodeType Consistency (Rules 6, 7, 8, 9)
        for edge in graph.edges:
            # Rule 7: No node may directly reference itself
            if edge.source_id == edge.target_id:
                errors.append(f"Direct self-reference: node '{edge.source_id}' has an edge pointing to itself.")

            # Rule 6: Source and target must exist
            source_node = all_nodes.get(edge.source_id)
            target_node = all_nodes.get(edge.target_id)

            if not source_node:
                errors.append(f"Broken Reference: Edge references non-existent source node '{edge.source_id}'")
            else:
                # Rule 9: NodeType consistency (source)
                if source_node.node_type != edge.source_type:
                    errors.append(f"NodeType Mismatch: Node '{edge.source_id}' is of type {source_node.node_type}, but edge specifies source_type {edge.source_type}")

            if not target_node:
                errors.append(f"Broken Reference: Edge references non-existent target node '{edge.target_id}'")
            else:
                # Rule 9: NodeType consistency (target)
                if target_node.node_type != edge.target_type:
                    errors.append(f"NodeType Mismatch: Node '{edge.target_id}' is of type {target_node.node_type}, but edge specifies target_type {edge.target_type}")

        # 2. Rule 5: No orphan nodes allowed
        for nid, node in all_nodes.items():
            has_out = len(graph.out_edges.get(nid, [])) > 0
            has_in = len(graph.in_edges.get(nid, [])) > 0
            if not has_out and not has_in:
                errors.append(f"Orphan Node: Node '{nid}' of type {node.node_type} has no incoming or outgoing connections.")

        # 3. Rule 1: Observation must have at least one valid upstream provenance path
        for obs_id, obs in graph.observations.items():
            if not GraphValidator._check_observation_provenance(graph, obs_id, all_nodes):
                errors.append(f"Traceability Breach: Observation '{obs_id}' lacks a valid upstream provenance lineage path.")

        # 4. Rule 2: Assessment must have generated at least one Observation
        for asm_id in graph.assessments:
            generated_obs = False
            for edge in graph.out_edges.get(asm_id, []):
                if edge.relationship == "GENERATED" and edge.target_type == NodeType.OBSERVATION:
                    generated_obs = True
                    break
            if not generated_obs:
                errors.append(f"Provenance Error: Assessment '{asm_id}' did not generate any observations.")

        # 5. Rule 3: Risk must reference at least one Observation
        for risk_id in graph.risks:
            has_obs_ref = False
            for edge in graph.out_edges.get(risk_id, []):
                if edge.relationship == "REFERENCES" and edge.target_type == NodeType.OBSERVATION:
                    has_obs_ref = True
                    break
            if not has_obs_ref:
                errors.append(f"Referential Breach: Risk '{risk_id}' does not reference any supporting observations.")

        # 6. Rule 4: Question must reference Observation or Risk
        for qst_id in graph.questions:
            has_ref = False
            for edge in graph.out_edges.get(qst_id, []):
                if edge.relationship == "QUESTIONS" and edge.target_type in (NodeType.OBSERVATION, NodeType.RISK):
                    has_ref = True
                    break
            if not has_ref:
                errors.append(f"Referential Breach: Question '{qst_id}' does not reference any observation or risk.")

        return errors

    @staticmethod
    def _check_observation_provenance(graph: ObservationGraph, obs_id: str, all_nodes: dict) -> bool:
        """BFS/DFS tracing to verify the observation reaches at least one Claim, Evidence, Document, or Assessment."""
        visited = set()
        queue = [obs_id]

        while queue:
            curr = queue.pop(0)
            if curr in visited:
                continue
            visited.add(curr)

            curr_node = all_nodes.get(curr)
            if not curr_node:
                continue

            if curr_node.node_type in (NodeType.CLAIM, NodeType.EVIDENCE, NodeType.ASSESSMENT):
                return True

            # Outgoing paths (e.g. Observation -> Claim (SUPPORTED_BY))
            for edge in graph.out_edges.get(curr, []):
                if edge.relationship in ("SUPPORTED_BY", "RELATED_TO") and edge.target_id not in visited:
                    queue.append(edge.target_id)

            # Incoming paths (e.g. Assessment -> Observation (GENERATED))
            for edge in graph.in_edges.get(curr, []):
                if edge.relationship in ("GENERATED", "RELATED_TO") and edge.source_id not in visited:
                    queue.append(edge.source_id)

        return False
