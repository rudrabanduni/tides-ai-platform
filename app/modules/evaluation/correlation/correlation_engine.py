import uuid
from datetime import datetime
from app.modules.evaluation.graph.graph_models import ObservationGraph, Edge, NodeType
from app.modules.evaluation.correlation.correlation_models import CorrelationNode


class CorrelationEngine:
    """Discovers and establishes cross-expert observations corroborations, contradictions, and dependencies."""

    @staticmethod
    def correlate(graph: ObservationGraph) -> ObservationGraph:
        obs_list = list(graph.observations.values())

        # Precompute target sets, word sets, and negation/positivity flags to optimize performance
        obs_claims = {}
        obs_evidence = {}
        obs_words = {}
        obs_has_neg = {}
        obs_has_pos = {}
        
        neg_words = {"not", "no", "missing", "unsupported", "lack", "ambiguity", "unclear", "weak", "disputed", "contradicts"}
        pos_words = {"validated", "has", "strong", "granted", "clear", "corroborated", "exists"}

        for obs in obs_list:
            oid = obs.observation_id
            obs_claims[oid] = {edge.target_id for edge in graph.out_edges.get(oid, []) if edge.target_type == NodeType.CLAIM}
            obs_evidence[oid] = {edge.target_id for edge in graph.out_edges.get(oid, []) if edge.target_type == NodeType.EVIDENCE}
            obs_words[oid] = set(obs.observation.lower().split())
            
            text_lower = obs.observation.lower()
            obs_has_neg[oid] = any(w in text_lower for w in neg_words)
            obs_has_pos[oid] = any(w in text_lower for w in pos_words)

        # Precompute conflicting claims pairs
        conflicting_claims_pairs = set()
        for conflict_id, conflict in graph.conflicts.items():
            targets = tuple(sorted([edge.target_id for edge in graph.out_edges.get(conflict_id, []) if edge.target_type == NodeType.CLAIM]))
            if len(targets) >= 2:
                for idx1 in range(len(targets)):
                    for idx2 in range(idx1 + 1, len(targets)):
                        conflicting_claims_pairs.add((targets[idx1], targets[idx2]))

        def Jaccard_set(words1: set[str], words2: set[str]) -> float:
            intersection_len = len(words1 & words2)
            if not intersection_len:
                return 0.0
            return intersection_len / len(words1 | words2)

        for i in range(len(obs_list)):
            for j in range(i + 1, len(obs_list)):
                obs1 = obs_list[i]
                obs2 = obs_list[j]
                oid1 = obs1.observation_id
                oid2 = obs2.observation_id

                claims1 = obs_claims[oid1]
                claims2 = obs_claims[oid2]
                
                evidence1 = obs_evidence[oid1]
                evidence2 = obs_evidence[oid2]

                # Check if observations reference conflicting claims via precomputed conflicting pairs
                has_claim_conflict = False
                for c1 in claims1:
                    for c2 in claims2:
                        pair = tuple(sorted([c1, c2]))
                        if pair in conflicting_claims_pairs:
                            has_claim_conflict = True
                            break
                    if has_claim_conflict:
                        break

                sim = Jaccard_set(obs_words[oid1], obs_words[oid2])

                # Text-based contradiction detection
                text_conflict = False
                if (claims1 & claims2) or (evidence1 & evidence2) or sim > 0.4:
                    if (obs_has_neg[oid1] and obs_has_pos[oid2]) or (obs_has_neg[oid2] and obs_has_pos[oid1]):
                        text_conflict = True

                corr_type = None
                description = ""
                confidence = 0.8

                if has_claim_conflict or text_conflict:
                    corr_type = "CONTRADICTS"
                    description = f"Observation '{oid1}' contradicts '{oid2}' due to conflicting details."
                    confidence = 0.9
                    
                elif sim >= 0.90:
                    if obs1.domain == obs2.domain:
                        corr_type = "DUPLICATES"
                        description = f"Observation '{oid1}' duplicates '{oid2}' in domain '{obs1.domain}'."
                        confidence = 0.95
                    else:
                        corr_type = "CORROBORATES"
                        description = f"Observation '{oid1}' corroborates '{oid2}' across domains."
                        confidence = 0.95
                        
                elif (obs1.domain == "trl" and obs2.domain == "product") or (obs2.domain == "trl" and obs1.domain == "product"):
                    corr_type = "DEPENDS_ON"
                    description = f"TRL Observation depends on Product validation."
                    confidence = 0.8
                elif (obs1.domain == "ip" and obs2.domain == "competition") or (obs2.domain == "ip" and obs1.domain == "competition"):
                    corr_type = "SUPPORTS"
                    description = f"IP Observation supports competitive moat."
                    confidence = 0.85
                elif (obs1.domain == "risk" and obs2.domain in ("founder", "product", "market", "financial")) or (obs2.domain == "risk" and obs1.domain in ("founder", "product", "market", "financial")):
                    target_domain = obs2.domain if obs1.domain == "risk" else obs1.domain
                    corr_type = "WEAKENS"
                    description = f"Risk Observation weakens {target_domain} viability."
                    confidence = 0.75
                elif (claims1 & claims2) or (evidence1 & evidence2):
                    if obs1.domain != obs2.domain:
                        corr_type = "CORROBORATES"
                        description = f"Observation '{oid1}' and '{oid2}' share sources."
                        confidence = 0.9

                if corr_type:
                    corr_id = f"CORR-{corr_type[:4]}-{oid1}-{oid2}"
                    corr_node = CorrelationNode(
                        node_id=corr_id,
                        node_type=NodeType.CORRELATION,
                        correlation_id=corr_id,
                        correlation_type=corr_type,
                        description=description,
                        confidence=confidence,
                        created_at=datetime.utcnow().isoformat() + "Z"
                    )
                    graph.correlations[corr_id] = corr_node

                    # Create Relation: CorrelationNode --RELATED_TO--> ObservationA
                    edge_a = Edge(
                        source_id=corr_id,
                        source_type=NodeType.CORRELATION,
                        target_id=oid1,
                        target_type=NodeType.OBSERVATION,
                        relationship="RELATED_TO"
                    )
                    graph.edges.append(edge_a)
                    graph.out_edges.setdefault(corr_id, []).append(edge_a)
                    graph.in_edges.setdefault(oid1, []).append(edge_a)

                    # Create Relation: CorrelationNode --RELATED_TO--> ObservationB
                    edge_b = Edge(
                        source_id=corr_id,
                        source_type=NodeType.CORRELATION,
                        target_id=oid2,
                        target_type=NodeType.OBSERVATION,
                        relationship="RELATED_TO"
                    )
                    graph.edges.append(edge_b)
                    graph.out_edges.setdefault(corr_id, []).append(edge_b)
                    graph.in_edges.setdefault(oid2, []).append(edge_b)
                    # Index correlation by observation ID
                    graph.correlations_by_observation.setdefault(oid1, []).append(corr_node)
                    graph.correlations_by_observation.setdefault(oid2, []).append(corr_node)
        # Update stats
        from app.modules.evaluation.graph.graph_builder import ObservationGraphBuilder
        ObservationGraphBuilder._update_statistics(graph)

        # Re-compute integrity hash
        graph.graph_hash = ObservationGraphBuilder._compute_hash(graph)

        return graph
