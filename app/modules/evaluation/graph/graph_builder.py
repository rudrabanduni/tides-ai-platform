import hashlib
import json
import uuid
from datetime import datetime
from typing import Any, List
from app.modules.evaluation.graph.graph_models import (
    ObservationGraph, DocumentNode, EvidenceNode, ClaimNode,
    ObservationNode, AssessmentNode, ConflictNode, RiskNode,
    QuestionNode, Edge, NodeType, GraphStatistics
)
from app.modules.evaluation.graph.graph_queries import (
    trace_observation, trace_assessment, trace_risk, trace_question
)


class ObservationGraphBuilder:
    """Builds, links, validates, hashes, and indexes an ObservationGraph from startup profiles, claims, and assessments."""

    @staticmethod
    def build(
        profile: Any,
        claims: List[Any],
        evidence: List[Any],
        assessments: List[Any],
        conflicts: List[Any] | None = None
    ) -> ObservationGraph:
        graph = ObservationGraph()
        # Populate startup info
        graph.startup_id = str(getattr(profile, "id", getattr(profile, "startup_id", str(uuid.uuid4()))))
        graph.graph_id = graph.startup_id
        graph.startup_name = str(getattr(profile, "startup_name", getattr(profile, "name", f"Startup-{graph.graph_id[:8]}")))
        graph.category = str(getattr(profile, "sector", getattr(profile, "category", "Unknown")))
        graph.created_at = datetime.utcnow().isoformat() + "Z"
        graph.graph_version = "1.0.0"

        # 1. Populate Documents (either from profile or inferred from evidence)
        doc_ids = set()
        if profile and hasattr(profile, "documents") and profile.documents:
            for doc in profile.documents:
                doc_node = DocumentNode(
                    node_id=str(doc.id),
                    node_type=NodeType.DOCUMENT,
                    document_id=str(doc.id),
                    document_name=getattr(doc, "document_name", f"Doc-{doc.id}"),
                    document_type=getattr(doc, "document_type", "Unknown"),
                    uploaded_at=getattr(doc, "uploaded_at", datetime.utcnow())
                )
                graph.documents[doc_node.node_id] = doc_node
                doc_ids.add(doc_node.node_id)
        
        # Fallback: Infer Documents from Evidence
        for ev in evidence or []:
            doc_id = str(getattr(ev, "source_document_id", getattr(ev, "document_id", "unknown")))
            if doc_id not in graph.documents:
                doc_node = DocumentNode(
                    node_id=doc_id,
                    node_type=NodeType.DOCUMENT,
                    document_id=doc_id,
                    document_name=f"Inferred Doc {doc_id}",
                    document_type="Unknown",
                    uploaded_at=datetime.utcnow()
                )
                graph.documents[doc_id] = doc_node

        # 2. Populate Evidence
        for ev in evidence or []:
            ev_id = str(ev.id)
            doc_id = str(getattr(ev, "source_document_id", getattr(ev, "document_id", "unknown")))
            
            ev_node = EvidenceNode(
                node_id=ev_id,
                node_type=NodeType.EVIDENCE,
                evidence_id=ev_id,
                excerpt=getattr(ev, "evidence_snippet", getattr(ev, "excerpt", "No snippet")),
                location=f"{getattr(ev, 'section_name', 'Unknown')} p.{getattr(ev, 'page_number', '1')}",
                confidence=getattr(ev, "confidence_score", 1.0)
            )
            graph.evidence[ev_id] = ev_node
            
            # Relation: Evidence --DERIVED_FROM--> Document
            edge = Edge(
                source_id=ev_id,
                source_type=NodeType.EVIDENCE,
                target_id=doc_id,
                target_type=NodeType.DOCUMENT,
                relationship="DERIVED_FROM"
            )
            graph.edges.append(edge)
            graph.out_edges.setdefault(ev_id, []).append(edge)
            graph.in_edges.setdefault(doc_id, []).append(edge)

        # Index evidence by claim_id
        evidence_by_claim = {}
        for ev in evidence or []:
            ev_claim_id = str(getattr(ev, "claim_id", ""))
            evidence_by_claim.setdefault(ev_claim_id, []).append(ev)

        # 3. Populate Claims
        for claim in claims or []:
            claim_id = str(claim.id)
            field_key = getattr(claim.field, "field_key", "claim") if hasattr(claim, "field") and claim.field else "claim"
            val = (getattr(claim, "value_string", None) or 
                   getattr(claim, "value_number", None) or 
                   getattr(claim, "value_boolean", None) or 
                   getattr(claim, "value_json", None) or "")
            
            claim_node = ClaimNode(
                node_id=claim_id,
                node_type=NodeType.CLAIM,
                claim_id=claim_id,
                claim_text=f"{field_key}: {val}"
            )
            graph.claims[claim_id] = claim_node

            # Link Claim --SUPPORTED_BY--> Evidence
            for ev in evidence_by_claim.get(claim_id, []):
                edge = Edge(
                    source_id=claim_id,
                    source_type=NodeType.CLAIM,
                    target_id=str(ev.id),
                    target_type=NodeType.EVIDENCE,
                    relationship="SUPPORTED_BY"
                )
                graph.edges.append(edge)
                graph.out_edges.setdefault(claim_id, []).append(edge)
                graph.in_edges.setdefault(str(ev.id), []).append(edge)

        # 4. Populate Assessment output nodes (Assessments, Observations, Risks, Questions)
        for asm in assessments or []:
            asm_id = str(getattr(asm, "assessment_id", f"ASM-{asm.domain.upper()}"))
            
            asm_node = AssessmentNode(
                node_id=asm_id,
                node_type=NodeType.ASSESSMENT,
                assessment_id=asm_id,
                domain=asm.domain,
                expert_name=f"{asm.domain.capitalize()}Expert",
                agent_version=getattr(asm, "agent_version", "1.0.0"),
                prompt_version=getattr(asm, "prompt_version", "1.0.0"),
                confidence=getattr(asm.confidence, "overall_domain_confidence", getattr(asm, "confidence", 1.0)),
                generated_at=getattr(asm, "generated_at", datetime.utcnow())
            )
            graph.assessments[asm_id] = asm_node

            # Indexing: Assessment by Domain
            graph.assessments_by_domain.setdefault(asm.domain, []).append(asm_id)

            # Generate Observations
            for obs in getattr(asm, "observations", []):
                obs_id = str(obs.observation_id)
                obs_node = ObservationNode(
                    node_id=obs_id,
                    node_type=NodeType.OBSERVATION,
                    observation_id=obs_id,
                    domain=asm.domain,
                    observation=obs.observation,
                    confidence=obs.confidence,
                    consensus_status="independent"
                )
                graph.observations[obs_id] = obs_node

                # Indexing: Observation by Domain
                graph.observations_by_domain.setdefault(asm.domain, []).append(obs_id)

                # Relation: Assessment --GENERATED--> Observation
                edge = Edge(
                    source_id=asm_id,
                    source_type=NodeType.ASSESSMENT,
                    target_id=obs_id,
                    target_type=NodeType.OBSERVATION,
                    relationship="GENERATED"
                )
                graph.edges.append(edge)
                graph.out_edges.setdefault(asm_id, []).append(edge)
                graph.in_edges.setdefault(obs_id, []).append(edge)

                # Relations: Observation --SUPPORTED_BY--> Claims
                for cid in getattr(obs, "claim_ids", []):
                    edge = Edge(
                        source_id=obs_id,
                        source_type=NodeType.OBSERVATION,
                        target_id=str(cid),
                        target_type=NodeType.CLAIM,
                        relationship="SUPPORTED_BY"
                    )
                    graph.edges.append(edge)
                    graph.out_edges.setdefault(obs_id, []).append(edge)
                    graph.in_edges.setdefault(str(cid), []).append(edge)

                # Relations: Observation --SUPPORTED_BY--> Evidence
                for eid in getattr(obs, "evidence_ids", []):
                    edge = Edge(
                        source_id=obs_id,
                        source_type=NodeType.OBSERVATION,
                        target_id=str(eid),
                        target_type=NodeType.EVIDENCE,
                        relationship="SUPPORTED_BY"
                    )
                    graph.edges.append(edge)
                    graph.out_edges.setdefault(obs_id, []).append(edge)
                    graph.in_edges.setdefault(str(eid), []).append(edge)

            # Generate Risks
            for risk in getattr(asm, "risks", []):
                risk_id = str(risk.id)
                risk_cat = getattr(risk, "category", asm.domain)
                
                risk_node = RiskNode(
                    node_id=risk_id,
                    node_type=NodeType.RISK,
                    risk_id=risk_id,
                    category=risk_cat,
                    description=risk.description,
                    confidence=getattr(risk, "confidence", 1.0),
                    reasoning=getattr(risk, "reasoning", "")
                )
                graph.risks[risk_id] = risk_node

                # Indexing: Risk by Category
                graph.risks_by_category.setdefault(risk_cat, []).append(risk_id)

                # Relation: Assessment --GENERATED--> Risk
                edge = Edge(
                    source_id=asm_id,
                    source_type=NodeType.ASSESSMENT,
                    target_id=risk_id,
                    target_type=NodeType.RISK,
                    relationship="GENERATED"
                )
                graph.edges.append(edge)
                graph.out_edges.setdefault(asm_id, []).append(edge)
                graph.in_edges.setdefault(risk_id, []).append(edge)

                # Relations: Risk --REFERENCES--> Observations
                for obs_id in getattr(risk, "supporting_observations", []):
                    edge = Edge(
                        source_id=risk_id,
                        source_type=NodeType.RISK,
                        target_id=str(obs_id),
                        target_type=NodeType.OBSERVATION,
                        relationship="REFERENCES"
                    )
                    graph.edges.append(edge)
                    graph.out_edges.setdefault(risk_id, []).append(edge)
                    graph.in_edges.setdefault(str(obs_id), []).append(edge)

                # Relations: Risk --REFERENCES--> Claims
                for cid in getattr(risk, "supporting_claims", []):
                    edge = Edge(
                        source_id=risk_id,
                        source_type=NodeType.RISK,
                        target_id=str(cid),
                        target_type=NodeType.CLAIM,
                        relationship="REFERENCES"
                    )
                    graph.edges.append(edge)
                    graph.out_edges.setdefault(risk_id, []).append(edge)
                    graph.in_edges.setdefault(str(cid), []).append(edge)

                # Relations: Risk --REFERENCES--> Evidence
                for eid in getattr(risk, "supporting_evidence", []):
                    edge = Edge(
                        source_id=risk_id,
                        source_type=NodeType.RISK,
                        target_id=str(eid),
                        target_type=NodeType.EVIDENCE,
                        relationship="REFERENCES"
                    )
                    graph.edges.append(edge)
                    graph.out_edges.setdefault(risk_id, []).append(edge)
                    graph.in_edges.setdefault(str(eid), []).append(edge)

            # Generate Questions
            for qst in getattr(asm, "questions", []):
                qst_id = str(qst.id)
                qst_node = QuestionNode(
                    node_id=qst_id,
                    node_type=NodeType.QUESTION,
                    question_id=qst_id,
                    question=qst.question,
                    purpose=qst.purpose
                )
                graph.questions[qst_id] = qst_node

                # Relation: Assessment --GENERATED--> Question
                edge = Edge(
                    source_id=asm_id,
                    source_type=NodeType.ASSESSMENT,
                    target_id=qst_id,
                    target_type=NodeType.QUESTION,
                    relationship="GENERATED"
                )
                graph.edges.append(edge)
                graph.out_edges.setdefault(asm_id, []).append(edge)
                graph.in_edges.setdefault(qst_id, []).append(edge)

                # Relations: Question --QUESTIONS--> Observations/Risks
                # Map to related observations or fallback to assessment observations
                related_obs = getattr(qst, "related_observation_ids", [])
                related_risks = getattr(qst, "related_risk_ids", [])
                
                if not related_obs and not related_risks:
                    # Fallback to map to observations in the same assessment
                    related_obs = [obs.observation_id for obs in getattr(asm, "observations", [])]
                    if not related_obs:
                        related_risks = [risk.id for risk in getattr(asm, "risks", [])]

                for obs_id in related_obs:
                    edge = Edge(
                        source_id=qst_id,
                        source_type=NodeType.QUESTION,
                        target_id=str(obs_id),
                        target_type=NodeType.OBSERVATION,
                        relationship="QUESTIONS"
                    )
                    graph.edges.append(edge)
                    graph.out_edges.setdefault(qst_id, []).append(edge)
                    graph.in_edges.setdefault(str(obs_id), []).append(edge)

                for risk_id in related_risks:
                    edge = Edge(
                        source_id=qst_id,
                        source_type=NodeType.QUESTION,
                        target_id=str(risk_id),
                        target_type=NodeType.RISK,
                        relationship="QUESTIONS"
                    )
                    graph.edges.append(edge)
                    graph.out_edges.setdefault(qst_id, []).append(edge)
                    graph.in_edges.setdefault(str(risk_id), []).append(edge)

        # 5. Populate Conflicts
        for conflict in conflicts or []:
            conflict_id = str(conflict.id)
            conflict_node = ConflictNode(
                node_id=conflict_id,
                node_type=NodeType.CONFLICT,
                conflict_id=conflict_id,
                description=getattr(conflict, "conflict_explanation", "Contradiction"),
                conflict_type=getattr(conflict, "conflict_type", "FACTUAL"),
                confidence=getattr(conflict, "confidence", 1.0),
                created_at=getattr(conflict, "created_at", datetime.utcnow())
            )
            graph.conflicts[conflict_id] = conflict_node

            # Link ConflictNode --CONFLICTS_WITH--> Claims
            for cid in [getattr(conflict, "preferred_claim_id", None), getattr(conflict, "superseded_claim_id", None)]:
                if cid:
                    edge = Edge(
                        source_id=conflict_id,
                        source_type=NodeType.CONFLICT,
                        target_id=str(cid),
                        target_type=NodeType.CLAIM,
                        relationship="CONFLICTS_WITH"
                    )
                    graph.edges.append(edge)
                    graph.out_edges.setdefault(conflict_id, []).append(edge)
                    graph.in_edges.setdefault(str(cid), []).append(edge)

        # 6. Observation Relationship Classification (Deduplication via linking)
        ObservationGraphBuilder._classify_observation_relationships(graph)

        # 7. Update Graph Statistics
        ObservationGraphBuilder._update_statistics(graph)

        # 8. Pre-populate Provenance Cache for O(1) Queries
        ObservationGraphBuilder._populate_provenance_cache(graph)

        # 9. Compute Graph Integrity Hash
        graph.graph_hash = ObservationGraphBuilder._compute_hash(graph)

        return graph

    @staticmethod
    def _classify_observation_relationships(graph: ObservationGraph) -> None:
        """Finds observations with similar metadata or semantic similarity and links them as duplicates/related."""
        obs_list = list(graph.observations.values())
        
        # Precompute target sets & words to optimize performance
        obs_claims = {}
        obs_evidence = {}
        obs_words = {}
        
        for obs in obs_list:
            oid = obs.observation_id
            obs_claims[oid] = {edge.target_id for edge in graph.out_edges.get(oid, []) if edge.target_type == NodeType.CLAIM}
            obs_evidence[oid] = {edge.target_id for edge in graph.out_edges.get(oid, []) if edge.target_type == NodeType.EVIDENCE}
            obs_words[oid] = set(obs.observation.lower().split())

        def Jaccard_set(words1: set[str], words2: set[str]) -> float:
            if not words1 and not words2:
                return 1.0
            return len(words1 & words2) / len(words1 | words2)

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

                sim = Jaccard_set(obs_words[oid1], obs_words[oid2])
                
                is_dup = False
                is_related = False

                if claims1 and claims2 and claims1 == claims2:
                    is_dup = True
                elif evidence1 and evidence2 and evidence1 == evidence2:
                    is_dup = True
                elif sim >= 0.90:
                    is_dup = True
                elif sim >= 0.50 or (claims1 & claims2) or (evidence1 & evidence2):
                    is_related = True

                if is_dup:
                    # Create Edge: ObservationA --RELATED_TO--> ObservationB (state: DUPLICATE)
                    edge = Edge(
                        source_id=oid1,
                        source_type=NodeType.OBSERVATION,
                        target_id=oid2,
                        target_type=NodeType.OBSERVATION,
                        relationship="RELATED_TO",
                        state="DUPLICATE"
                    )
                    graph.edges.append(edge)
                    graph.out_edges.setdefault(oid1, []).append(edge)
                    graph.in_edges.setdefault(oid2, []).append(edge)

                    # Update consensus status
                    obs1.consensus_status = "corroborated"
                    obs2.consensus_status = "corroborated"

                elif is_related:
                    # Create Edge: ObservationA --RELATED_TO--> ObservationB (state: RELATED)
                    edge = Edge(
                        source_id=oid1,
                        source_type=NodeType.OBSERVATION,
                        target_id=oid2,
                        target_type=NodeType.OBSERVATION,
                        relationship="RELATED_TO",
                        state="RELATED"
                    )
                    graph.edges.append(edge)
                    graph.out_edges.setdefault(oid1, []).append(edge)
                    graph.in_edges.setdefault(oid2, []).append(edge)

    @staticmethod
    def _update_statistics(graph: ObservationGraph) -> None:
        stats = graph.graph_stats
        stats.document_count = len(graph.documents)
        stats.evidence_count = len(graph.evidence)
        stats.claim_count = len(graph.claims)
        stats.observation_count = len(graph.observations)
        stats.assessment_count = len(graph.assessments)
        stats.conflict_count = len(graph.conflicts)
        stats.risk_count = len(graph.risks)
        stats.question_count = len(graph.questions)
        stats.correlation_count = len(graph.correlations)
        stats.edge_count = len(graph.edges)
        
        # Sprint 3.0C statistics
        stats.resolution_count = len(graph.resolutions)
        resolved = 0
        for cid in graph.conflicts:
            if cid in graph.resolutions_by_conflict:
                resolved += 1
        stats.resolved_conflicts = resolved
        stats.unresolved_conflicts = len(graph.conflicts) - resolved

    @staticmethod
    def _populate_provenance_cache(graph: ObservationGraph) -> None:
        """Traces and caches lineage mapping for all nodes, ensuring O(1) retrieval."""
        for obs_id in graph.observations:
            trace_observation(graph, obs_id)
        for asm_id in graph.assessments:
            trace_assessment(graph, asm_id)
        for risk_id in graph.risks:
            trace_risk(graph, risk_id)
        for qst_id in graph.questions:
            trace_question(graph, qst_id)
        for res_id in list(graph.resolutions.keys()):
            from app.modules.evaluation.conflict_resolution.conflict_queries import trace_resolution
            trace_resolution(graph, res_id)

    @staticmethod
    def _compute_hash(graph: ObservationGraph) -> str:
        """SHA-256 integrity hash of version, node payloads, edges, and graph stats."""
        import json
        import hashlib
        from datetime import datetime
        from enum import Enum
        
        def fast_dump(node):
            if hasattr(node, "model_dump"):
                res = node.model_dump()
            elif hasattr(node, "__dict__"):
                res = node.__dict__.copy()
            else:
                return node
                
            for k, v in list(res.items()):
                if isinstance(v, datetime):
                    res[k] = v.isoformat() + "Z"
                elif isinstance(v, dict):
                    # convert nested dict datetimes
                    for nk, nv in list(v.items()):
                        if isinstance(nv, datetime):
                            v[nk] = nv.isoformat() + "Z"
                elif isinstance(v, list):
                    res[k] = [fast_dump(x) if hasattr(x, "model_dump") or hasattr(x, "__dict__") else x for x in v]
                    
            # Handle enums and Pydantic models only for specific nodes to optimize performance
            node_type = getattr(node, "node_type", None)
            if node_type in (NodeType.INVESTMENT, NodeType.REPORT, NodeType.DECISION):
                for k, v in list(res.items()):
                    if isinstance(v, Enum):
                        res[k] = v.value
            if node_type in (NodeType.REPORT, NodeType.DECISION):
                for k, v in list(res.items()):
                    if hasattr(v, "model_dump"):
                        res[k] = v.model_dump()
                    elif isinstance(v, list):
                        res[k] = [x.model_dump() if hasattr(x, "model_dump") else x for x in v]
            if "summary" in res and hasattr(res["summary"], "model_dump"):
                res["summary"] = res["summary"].model_dump()
            if "key_observations" in res:
                res["key_observations"] = [o.model_dump() if hasattr(o, "model_dump") else o for o in res["key_observations"]]
            if "major_risks" in res:
                res["major_risks"] = [r.model_dump() if hasattr(r, "model_dump") else r for r in res["major_risks"]]
            if "traceability" in res:
                def format_trace(item):
                    if isinstance(item, list):
                        return [format_trace(x) for x in item]
                    if isinstance(item, dict):
                        return {k: format_trace(v) for k, v in item.items()}
                    if isinstance(item, Enum):
                        return item.value
                    if isinstance(item, (str, int, float, bool, type(None))):
                        return item
                    if hasattr(item, "__dict__"):
                        return fast_dump(item)
                    return item
                res["traceability"] = format_trace(res["traceability"])
            return res

        hash_list = []
        hash_list.append(graph.graph_version)

        # 2. Node payloads (deterministic order sorted by ID)
        payloads = []
        for coll in [graph.documents, graph.evidence, graph.claims, graph.observations,
                     graph.assessments, graph.conflicts, graph.risks, graph.questions, 
                     graph.correlations, graph.resolutions]:
            for nid in sorted(coll.keys()):
                node = coll[nid]
                payloads.append(fast_dump(node))
        hash_list.append(json.dumps(payloads, sort_keys=True))

        # 3. Edge contents (deterministic sort by source, target, relationship)
        edges_dump = sorted(
            [edge.__dict__ for edge in graph.edges],
            key=lambda x: (x["source_id"], x["target_id"], x["relationship"])
        )
        hash_list.append(json.dumps(edges_dump, sort_keys=True))

        # 4. Resolution Edges (deterministic sort by source, target, relationship)
        res_edges_dump = sorted(
            [edge.__dict__ for edge in graph.resolution_edges],
            key=lambda x: (x["source_id"], x["target_id"], x["relationship"])
        )
        hash_list.append(json.dumps(res_edges_dump, sort_keys=True))

        # 5. Graph indexes
        idx_dump = {
            "resolutions_by_conflict": {k: sorted(v) for k, v in sorted(graph.resolutions_by_conflict.items())},
            "resolutions_by_observation": {k: sorted(v) for k, v in sorted(graph.resolutions_by_observation.items())}
        }
        hash_list.append(json.dumps(idx_dump, sort_keys=True))

        # 6. Graph statistics
        hash_list.append(json.dumps(graph.graph_stats.__dict__, sort_keys=True))

        # 7. Executive Layer
        if getattr(graph, "executive_assessment", None):
            hash_list.append(json.dumps(fast_dump(graph.executive_assessment), sort_keys=True))
        hash_list.append(json.dumps(getattr(graph, "executive_indexes", {}), sort_keys=True))
        hash_list.append(json.dumps(getattr(graph, "executive_statistics", {}), sort_keys=True))

        # 8. Investment Layer
        if getattr(graph, "investment_assessment", None):
            hash_list.append(json.dumps(fast_dump(graph.investment_assessment), sort_keys=True))
        hash_list.append(json.dumps(getattr(graph, "investment_indexes", {}), sort_keys=True))
        hash_list.append(json.dumps(getattr(graph, "investment_statistics", {}), sort_keys=True))

        # 9. Report Layer
        if getattr(graph, "report", None):
            hash_list.append(json.dumps(fast_dump(graph.report), sort_keys=True))
        hash_list.append(json.dumps(getattr(graph, "report_indexes", {}), sort_keys=True))
        hash_list.append(json.dumps(getattr(graph, "report_statistics", {}), sort_keys=True))

        # 10. Portfolio Layer
        if getattr(graph, "portfolio_entry", None):
            hash_list.append(json.dumps(fast_dump(graph.portfolio_entry), sort_keys=True))
        if getattr(graph, "portfolio_statistics", None):
            hash_list.append(json.dumps(fast_dump(graph.portfolio_statistics), sort_keys=True))
        hash_list.append(json.dumps(getattr(graph, "startup_id", ""), sort_keys=True))
        hash_list.append(json.dumps(getattr(graph, "startup_name", ""), sort_keys=True))
        hash_list.append(json.dumps(getattr(graph, "category", ""), sort_keys=True))

        # 11. Committee Decision Layer
        if getattr(graph, "committee_decision", None):
            hash_list.append(json.dumps(fast_dump(graph.committee_decision), sort_keys=True))

        # Final SHA-256 hash
        hasher = hashlib.sha256()
        for item in hash_list:
            hasher.update(item.encode("utf-8"))
        return hasher.hexdigest()
