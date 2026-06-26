import uuid
from datetime import datetime
from typing import List, Optional, Any
from app.modules.evaluation.graph.graph_models import ObservationGraph, Edge, NodeType
from app.modules.evaluation.conflict_resolution.conflict_models import ResolutionNode, ResolutionEdge


class ConflictResolutionEngine:
    """Orchestrates resolution of factual, numerical, temporal, and consensus conflicts on an ObservationGraph."""

    @staticmethod
    def resolve(graph: ObservationGraph) -> ObservationGraph:
        # Helper to parse datetime strings/objects
        def parse_date(date_val) -> datetime:
            if isinstance(date_val, datetime):
                return date_val
            if isinstance(date_val, str):
                try:
                    if date_val.endswith("Z"):
                        date_val = date_val[:-1]
                    return datetime.fromisoformat(date_val)
                except Exception:
                    pass
            return datetime.min

        # Helper to get assessments generating an observation
        def get_observation_assessments(obs_id: str) -> List[str]:
            asm_ids = []
            for edge in graph.in_edges.get(obs_id, []):
                if edge.source_type == NodeType.ASSESSMENT and edge.relationship == "GENERATED":
                    asm_ids.append(edge.source_id)
            return asm_ids

        # Helper to get claims supporting an observation
        def get_observation_claims(obs_id: str) -> List[str]:
            return [edge.target_id for edge in graph.out_edges.get(obs_id, [])
                    if edge.target_type == NodeType.CLAIM and edge.relationship == "SUPPORTED_BY"]

        # Helper to get evidence supporting an observation
        def get_observation_evidence(obs_id: str) -> List[str]:
            return [edge.target_id for edge in graph.out_edges.get(obs_id, [])
                    if edge.target_type == NodeType.EVIDENCE and edge.relationship == "SUPPORTED_BY"]

        # 1. Resolve standard conflicts in graph.conflicts
        for conflict_id, conflict in list(graph.conflicts.items()):
            # Find conflicting claims
            conflict_edges = graph.out_edges.get(conflict_id, [])
            claim_ids = [e.target_id for e in conflict_edges 
                         if e.target_type == NodeType.CLAIM and e.relationship == "CONFLICTS_WITH"]
            
            if len(claim_ids) < 2:
                continue

            claim1_id, claim2_id = claim_ids[0], claim_ids[1]

            # Find observations pointing to each claim
            obs1_ids = [e.source_id for e in graph.in_edges.get(claim1_id, [])
                        if e.source_type == NodeType.OBSERVATION and e.relationship == "SUPPORTED_BY"]
            obs2_ids = [e.source_id for e in graph.in_edges.get(claim2_id, [])
                        if e.source_type == NodeType.OBSERVATION and e.relationship == "SUPPORTED_BY"]

            if not obs1_ids or not obs2_ids:
                continue

            obs1 = graph.observations[obs1_ids[0]]
            obs2 = graph.observations[obs2_ids[0]]
            oid1, oid2 = obs1.observation_id, obs2.observation_id

            evidence1 = get_observation_evidence(oid1)
            evidence2 = get_observation_evidence(oid2)

            res_type = conflict.conflict_type
            pref_obs_id = None
            reasoning = ""
            confidence = 0.8

            # Rule 5: Insufficient Evidence
            if len(evidence1) == 0 and len(evidence2) == 0:
                res_type = "INSUFFICIENT_EVIDENCE"
                pref_obs_id = None
                reasoning = f"Neither observation '{oid1}' nor '{oid2}' contains supporting evidence references."
                confidence = 0.5
            else:
                # Factual conflict resolution
                if conflict.conflict_type in ("FACTUAL", "SOURCE_DISAGREEMENT"):
                    ev_nodes1 = [graph.evidence[eid] for eid in evidence1 if eid in graph.evidence]
                    ev_nodes2 = [graph.evidence[eid] for eid in evidence2 if eid in graph.evidence]

                    score1 = (
                        len(evidence1),
                        sum(e.confidence for e in ev_nodes1),
                        len(get_observation_assessments(oid1))
                    )
                    score2 = (
                        len(evidence2),
                        sum(e.confidence for e in ev_nodes2),
                        len(get_observation_assessments(oid2))
                    )

                    if score1 > score2:
                        pref_obs_id = oid1
                        reasoning = f"Observation '{oid1}' preferred: stronger evidence support score."
                    elif score2 > score1:
                        pref_obs_id = oid2
                        reasoning = f"Observation '{oid2}' preferred: stronger evidence support score."
                    else:
                        # Fallback to observation confidence
                        if obs1.confidence >= obs2.confidence:
                            pref_obs_id = oid1
                            reasoning = f"Observation '{oid1}' preferred: higher confidence fallback."
                        else:
                            pref_obs_id = oid2
                            reasoning = f"Observation '{oid2}' preferred: higher confidence fallback."
                    confidence = 0.9

                # Numerical conflict resolution
                elif conflict.conflict_type == "NUMERICAL":
                    asm1_nodes = [graph.assessments[aid] for aid in get_observation_assessments(oid1) if aid in graph.assessments]
                    asm2_nodes = [graph.assessments[aid] for aid in get_observation_assessments(oid2) if aid in graph.assessments]

                    t1 = max([parse_date(a.generated_at) for a in asm1_nodes]) if asm1_nodes else datetime.min
                    t2 = max([parse_date(a.generated_at) for a in asm2_nodes]) if asm2_nodes else datetime.min

                    score1 = (
                        t1,
                        len(evidence1) + len(get_observation_claims(oid1)),
                        obs1.confidence
                    )
                    score2 = (
                        t2,
                        len(evidence2) + len(get_observation_claims(oid2)),
                        obs2.confidence
                    )

                    if score1 > score2:
                        pref_obs_id = oid1
                        reasoning = f"Observation '{oid1}' preferred: latest validated value / strongest provenance."
                    else:
                        pref_obs_id = oid2
                        reasoning = f"Observation '{oid2}' preferred: latest validated value / strongest provenance."
                    confidence = 0.85

                # Temporal conflict resolution
                elif conflict.conflict_type == "TEMPORAL":
                    asm1_nodes = [graph.assessments[aid] for aid in get_observation_assessments(oid1) if aid in graph.assessments]
                    asm2_nodes = [graph.assessments[aid] for aid in get_observation_assessments(oid2) if aid in graph.assessments]

                    t1 = max([parse_date(a.generated_at) for a in asm1_nodes]) if asm1_nodes else datetime.min
                    t2 = max([parse_date(a.generated_at) for a in asm2_nodes]) if asm2_nodes else datetime.min

                    if t1 > t2:
                        pref_obs_id = oid1
                        reasoning = f"Observation '{oid1}' preferred: newest validated timestamp ({t1.isoformat()})."
                    elif t2 > t1:
                        pref_obs_id = oid2
                        reasoning = f"Observation '{oid2}' preferred: newest validated timestamp ({t2.isoformat()})."
                    else:
                        if obs1.confidence >= obs2.confidence:
                            pref_obs_id = oid1
                            reasoning = f"Observation '{oid1}' preferred: higher confidence fallback."
                        else:
                            pref_obs_id = oid2
                            reasoning = f"Observation '{oid2}' preferred: higher confidence fallback."
                    confidence = 0.95
                else:
                    # Fallback to factual rules
                    pref_obs_id = oid1 if obs1.confidence >= obs2.confidence else oid2
                    reasoning = f"Conflict resolved using confidence fallback."

            # Create the ResolutionNode
            res_id = f"RES-{res_type[:4]}-{conflict_id}"
            supporting_claims = list(set(get_observation_claims(oid1) + get_observation_claims(oid2)))
            supporting_evidence = list(set(evidence1 + evidence2))
            supporting_assessments = list(set(get_observation_assessments(oid1) + get_observation_assessments(oid2)))

            res_node = ResolutionNode(
                node_id=res_id,
                node_type=NodeType.RESOLUTION,
                resolution_id=res_id,
                conflict_id=conflict_id,
                resolution_type=res_type,
                preferred_observation_id=pref_obs_id,
                confidence=confidence,
                reasoning=reasoning,
                supporting_claims=supporting_claims,
                supporting_evidence=supporting_evidence,
                supporting_assessments=supporting_assessments,
                created_at=datetime.utcnow().isoformat() + "Z"
            )
            graph.resolutions[res_id] = res_node

            # Indexing
            graph.resolutions_by_conflict.setdefault(conflict_id, []).append(res_id)
            if pref_obs_id:
                graph.resolutions_by_observation.setdefault(pref_obs_id, []).append(res_id)

            # Create Edges
            # Edge 1: ResolutionNode --RESOLVES--> ConflictNode
            edge_resolves = ResolutionEdge(
                source_id=res_id,
                source_type=NodeType.RESOLUTION,
                target_id=conflict_id,
                target_type=NodeType.CONFLICT,
                relationship="RESOLVES"
            )
            graph.resolution_edges.append(edge_resolves)

            # Edge 2: ResolutionNode --PREFERS--> ObservationNode (if any)
            if pref_obs_id:
                edge_prefers = ResolutionEdge(
                    source_id=res_id,
                    source_type=NodeType.RESOLUTION,
                    target_id=pref_obs_id,
                    target_type=NodeType.OBSERVATION,
                    relationship="PREFERS"
                )
                graph.resolution_edges.append(edge_prefers)

            # Edge 3: ResolutionNode --SUPPORTED_BY--> claims, evidence, assessments
            for cid in supporting_claims:
                graph.resolution_edges.append(ResolutionEdge(
                    source_id=res_id, source_type=NodeType.RESOLUTION,
                    target_id=cid, target_type=NodeType.CLAIM,
                    relationship="SUPPORTED_BY"
                ))
            for eid in supporting_evidence:
                graph.resolution_edges.append(ResolutionEdge(
                    source_id=res_id, source_type=NodeType.RESOLUTION,
                    target_id=eid, target_type=NodeType.EVIDENCE,
                    relationship="SUPPORTED_BY"
                ))
            for aid in supporting_assessments:
                graph.resolution_edges.append(ResolutionEdge(
                    source_id=res_id, source_type=NodeType.RESOLUTION,
                    target_id=aid, target_type=NodeType.ASSESSMENT,
                    relationship="SUPPORTED_BY"
                ))

        # 2. Resolve duplicates in graph.correlations (CorrelationType == DUPLICATES)
        for corr_id, corr in list(graph.correlations.items()):
            if corr.correlation_type == "DUPLICATES":
                # Find target observations
                corr_edges = graph.out_edges.get(corr_id, [])
                obs_ids = [e.target_id for e in corr_edges 
                           if e.target_type == NodeType.OBSERVATION and e.relationship == "RELATED_TO"]

                if len(obs_ids) < 2:
                    continue

                obs1_id, obs2_id = obs_ids[0], obs_ids[1]

                res_type = "CONSENSUS"
                pref_obs_id = obs1_id  # Selecting first observation as consensus preferred
                reasoning = f"Duplicate observations '{obs1_id}' and '{obs2_id}' resolved via consensus."
                confidence = corr.confidence

                res_id = f"RES-CONS-{corr_id}"
                supporting_claims = list(set(get_observation_claims(obs1_id) + get_observation_claims(obs2_id)))
                supporting_evidence = list(set(get_observation_evidence(obs1_id) + get_observation_evidence(obs2_id)))
                supporting_assessments = list(set(get_observation_assessments(obs1_id) + get_observation_assessments(obs2_id)))

                res_node = ResolutionNode(
                    node_id=res_id,
                    node_type=NodeType.RESOLUTION,
                    resolution_id=res_id,
                    conflict_id=corr_id,
                    resolution_type=res_type,
                    preferred_observation_id=pref_obs_id,
                    confidence=confidence,
                    reasoning=reasoning,
                    supporting_claims=supporting_claims,
                    supporting_evidence=supporting_evidence,
                    supporting_assessments=supporting_assessments,
                    created_at=datetime.utcnow().isoformat() + "Z"
                )
                graph.resolutions[res_id] = res_node

                # Indexing
                graph.resolutions_by_conflict.setdefault(corr_id, []).append(res_id)
                graph.resolutions_by_observation.setdefault(pref_obs_id, []).append(res_id)

                # Create Edges
                # Edge 1: ResolutionNode --RESOLVES--> CorrelationNode
                edge_resolves = ResolutionEdge(
                    source_id=res_id,
                    source_type=NodeType.RESOLUTION,
                    target_id=corr_id,
                    target_type=NodeType.CORRELATION,
                    relationship="RESOLVES"
                )
                graph.resolution_edges.append(edge_resolves)

                # Edge 2: ResolutionNode --PREFERS--> ObservationNode
                edge_prefers = ResolutionEdge(
                    source_id=res_id,
                    source_type=NodeType.RESOLUTION,
                    target_id=pref_obs_id,
                    target_type=NodeType.OBSERVATION,
                    relationship="PREFERS"
                )
                graph.resolution_edges.append(edge_prefers)

                # Edge 3: ResolutionNode --SUPPORTED_BY--> claims, evidence, assessments
                for cid in supporting_claims:
                    graph.resolution_edges.append(ResolutionEdge(
                        source_id=res_id, source_type=NodeType.RESOLUTION,
                        target_id=cid, target_type=NodeType.CLAIM,
                        relationship="SUPPORTED_BY"
                    ))
                for eid in supporting_evidence:
                    graph.resolution_edges.append(ResolutionEdge(
                        source_id=res_id, source_type=NodeType.RESOLUTION,
                        target_id=eid, target_type=NodeType.EVIDENCE,
                        relationship="SUPPORTED_BY"
                    ))
                for aid in supporting_assessments:
                    graph.resolution_edges.append(ResolutionEdge(
                        source_id=res_id, source_type=NodeType.RESOLUTION,
                        target_id=aid, target_type=NodeType.ASSESSMENT,
                        relationship="SUPPORTED_BY"
                    ))

        # 3. Update stats
        from app.modules.evaluation.graph.graph_builder import ObservationGraphBuilder
        ObservationGraphBuilder._update_statistics(graph)

        # 4. Recompute integrity hash
        graph.graph_hash = ObservationGraphBuilder._compute_hash(graph)

        return graph
