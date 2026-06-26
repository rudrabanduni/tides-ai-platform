import uuid
from datetime import datetime
from typing import Any, Set

from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType
from app.modules.explainability.explanation_models import ExplanationNode, LineageTrace


def _serialize_node(node: Any) -> dict[str, Any]:
    if hasattr(node, "model_dump"):
        return node.model_dump()
    if hasattr(node, "dict"):
        return node.dict()
    if isinstance(node, dict):
        return node
    return getattr(node, "__dict__", {})


class ExplanationBuilder:
    """Helper to traverse the ObservationGraph and construct ExplanationNodes."""

    @staticmethod
    def build_explanation(
        graph: ObservationGraph,
        target_id: str,
        target_type: str,
        summary: str = "",
        reasoning: str = ""
    ) -> ExplanationNode:
        # 1. Collect all related nodes in the graph via traversal
        visited: Set[str] = set()
        
        # Start node lookup
        start_nodes = [target_id]
        
        # Look for explicit domain attributes if the target is not a standard graph node
        if target_type.upper() == "PORTFOLIO" or target_type.upper() == "PORTFOLIO_RANK":
            if graph.portfolio_entry:
                start_nodes.append(getattr(graph.portfolio_entry, "investment_assessment_id", ""))
            if graph.investment_assessment:
                start_nodes.append(getattr(graph.investment_assessment, "node_id", ""))
        elif target_type.upper() == "INVESTMENT" or target_type.upper() == "INVESTMENT_DECISION":
            if graph.investment_assessment:
                start_nodes.append(getattr(graph.investment_assessment, "node_id", ""))
            # Also trace all assessments
            start_nodes.extend(graph.assessments.keys())
        elif target_type.upper() == "EXECUTIVE" or target_type.upper() == "EXECUTIVE_SUMMARY":
            if graph.executive_assessment:
                start_nodes.append(getattr(graph.executive_assessment, "node_id", ""))
            # Also trace all assessments
            start_nodes.extend(graph.assessments.keys())
        elif target_type.upper() == "DECISION" or target_type.upper() == "COMMITTEE_DECISION":
            if graph.committee_decision:
                start_nodes.append(getattr(graph.committee_decision, "node_id", ""))
            if graph.investment_assessment:
                start_nodes.append(getattr(graph.investment_assessment, "node_id", ""))
            start_nodes.extend(graph.assessments.keys())

        # Determine if we should expand assessments
        expand_assessments = target_type.upper() in (
            "ASSESSMENT",
            "DECISION",
            "COMMITTEE_DECISION",
            "INVESTMENT",
            "INVESTMENT_DECISION",
            "EXECUTIVE",
            "EXECUTIVE_SUMMARY",
            "PORTFOLIO",
            "PORTFOLIO_RANK"
        )

        # Queue for traversal
        queue = [n for n in start_nodes if n]
        queued = set(queue)
        
        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            visited.add(current_id)

            # Get node in graph
            node = graph.get_node(current_id)
            if not node:
                # Also check correlation nodes directly
                if current_id in graph.correlations:
                    node = graph.correlations[current_id]
                elif current_id in graph.resolutions:
                    node = graph.resolutions[current_id]

            if node:
                node_type = getattr(node, "node_type", "")
                
                # If it's an assessment and we don't want to expand it,
                # we do NOT queue its neighbors
                if node_type == NodeType.ASSESSMENT and not expand_assessments:
                    continue

                # Add adjacent nodes via edges
                for edge in graph.out_edges.get(current_id, []):
                    # For observations/risks/questions/conflicts/correlations, we do not want to cross
                    # over to sibling duplicate observations or other assessments unless expanding assessments
                    if edge.relationship == "RELATED_TO" and not expand_assessments:
                        continue
                    if edge.target_id not in queued:
                        queue.append(edge.target_id)
                        queued.add(edge.target_id)
                for edge in graph.in_edges.get(current_id, []):
                    # We only traverse in-edges to find generating assessments or referencing nodes
                    if edge.relationship == "GENERATED" and edge.source_type == NodeType.ASSESSMENT:
                        if edge.source_id not in queued:
                            queue.append(edge.source_id)
                            queued.add(edge.source_id)
                    elif edge.relationship == "REFERENCES" or edge.relationship == "QUESTIONS":
                        if edge.source_id not in queued:
                            queue.append(edge.source_id)
                            queued.add(edge.source_id)

                # Special linkages by attributes (e.g. Observation claim_ids)
                if hasattr(node, "claim_ids") and node.claim_ids:
                    for cid in node.claim_ids:
                        if cid not in queued:
                            queue.append(cid)
                            queued.add(cid)
                if hasattr(node, "evidence_ids") and node.evidence_ids:
                    for eid in node.evidence_ids:
                        if eid not in queued:
                            queue.append(eid)
                            queued.add(eid)
                if hasattr(node, "supporting_observations") and node.supporting_observations:
                    for oid in node.supporting_observations:
                        if oid not in queued:
                            queue.append(oid)
                            queued.add(oid)
                if hasattr(node, "supporting_claims") and node.supporting_claims:
                    for cid in node.supporting_claims:
                        if cid not in queued:
                            queue.append(cid)
                            queued.add(cid)
                if hasattr(node, "supporting_evidence") and node.supporting_evidence:
                    for eid in node.supporting_evidence:
                        if eid not in queued:
                            queue.append(eid)
                            queued.add(eid)

        # 2. Map visited IDs to lineage nodes
        lineage = LineageTrace()
        
        for vid in visited:
            node = graph.get_node(vid)
            if not node:
                if vid in graph.correlations:
                    node = graph.correlations[vid]
                elif vid in graph.resolutions:
                    node = graph.resolutions[vid]
                    
            if not node:
                continue

            node_type = getattr(node, "node_type", "")
            node_dict = _serialize_node(node)

            if node_type == NodeType.DOCUMENT:
                lineage.documents.append(node_dict)
            elif node_type == NodeType.EVIDENCE:
                lineage.evidence.append(node_dict)
            elif node_type == NodeType.CLAIM:
                lineage.claims.append(node_dict)
            elif node_type == NodeType.OBSERVATION:
                lineage.observations.append(node_dict)
            elif node_type == NodeType.ASSESSMENT:
                lineage.assessments.append(node_dict)

        # Determine target summary and reasoning default details
        target_node = graph.get_node(target_id)
        if not target_node:
            if target_id in graph.correlations:
                target_node = graph.correlations[target_id]
            elif target_id in graph.resolutions:
                target_node = graph.resolutions[target_id]

        # Inferred summary and reasoning
        if not summary:
            if target_node:
                summary = f"Explanation of {target_type} node '{target_id}'"
                if hasattr(target_node, "observation"):
                    summary = f"Observation: {target_node.observation}"
                elif hasattr(target_node, "description"):
                    summary = f"Risk/Conflict: {target_node.description}"
                elif hasattr(target_node, "summary"):
                    summary = f"Summary: {target_node.summary}"
            else:
                summary = f"Explanation of target {target_id}"

        if not reasoning:
            if target_node and hasattr(target_node, "reasoning") and target_node.reasoning:
                reasoning = target_node.reasoning
            elif target_node and hasattr(target_node, "excerpt") and target_node.excerpt:
                reasoning = f"Based on excerpt: {target_node.excerpt}"
            else:
                reasoning = f"Deterministically traced {len(visited)} supporting nodes in the evaluation graph."

        # Compute confidence (either average of lineage or specific to target)
        confidence = 1.0
        if target_node and hasattr(target_node, "confidence") and target_node.confidence is not None:
            confidence = float(target_node.confidence)
        elif lineage.observations:
            # Average confidence of observations
            conf_vals = [float(o["confidence"]) for o in lineage.observations if "confidence" in o]
            if conf_vals:
                confidence = sum(conf_vals) / len(conf_vals)

        # Make sure confidence is within 0.0 and 1.0 bounds
        confidence = max(0.0, min(1.0, confidence))

        # Metadata
        metadata = {
            "traced_nodes_count": len(visited),
            "graph_version": graph.graph_version,
            "startup_id": graph.startup_id,
            "startup_name": graph.startup_name,
        }

        return ExplanationNode(
            explanation_id=str(uuid.uuid4()),
            target_type=target_type,
            target_id=target_id,
            summary=summary,
            confidence=confidence,
            reasoning=reasoning,
            generated_at=datetime.utcnow(),
            lineage=lineage,
            metadata=metadata
        )
