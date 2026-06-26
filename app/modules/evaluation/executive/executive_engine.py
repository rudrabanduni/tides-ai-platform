import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType, Edge
from app.modules.evaluation.executive.executive_models import (
    ExecutiveFinding, ExecutiveSummary, ExecutiveMetrics, ExecutiveAssessment
)
from app.modules.evaluation.graph.graph_queries import trace_observation


class ExecutiveEngine:
    """Consumes the ObservationGraph and compiles a unified, deterministic ExecutiveAssessment."""

    @staticmethod
    def generate(graph: ObservationGraph) -> ObservationGraph:
        # Helper to get evidence supporting an observation
        def get_observation_evidence(obs_id: str) -> List[str]:
            return [edge.target_id for edge in graph.out_edges.get(obs_id, [])
                    if edge.target_type == NodeType.EVIDENCE and edge.relationship == "SUPPORTED_BY"]

        # Helper to get claims supporting an observation
        def get_observation_claims(obs_id: str) -> List[str]:
            return [edge.target_id for edge in graph.out_edges.get(obs_id, [])
                    if edge.target_type == NodeType.CLAIM and edge.relationship == "SUPPORTED_BY"]

        # 1. Identify Suppressed Observations due to Resolved Conflicts or Correlations
        suppressed_obs = set()
        for res in graph.resolutions.values():
            if res.preferred_observation_id:
                conflict_id = res.conflict_id
                obs_ids = []
                conflict_node = graph.conflicts.get(conflict_id) or graph.correlations.get(conflict_id)
                if conflict_node:
                    if getattr(conflict_node, "node_type", None) == NodeType.CONFLICT:
                        conflict_edges = graph.out_edges.get(conflict_id, [])
                        claim_ids = [e.target_id for e in conflict_edges 
                                     if e.target_type == NodeType.CLAIM and e.relationship == "CONFLICTS_WITH"]
                        for cid in claim_ids:
                            for edge in graph.in_edges.get(cid, []):
                                if edge.source_type == NodeType.OBSERVATION and edge.relationship == "SUPPORTED_BY":
                                    obs_ids.append(edge.source_id)
                    elif getattr(conflict_node, "node_type", None) == NodeType.CORRELATION:
                        corr_edges = graph.out_edges.get(conflict_id, [])
                        obs_ids = [e.target_id for e in corr_edges 
                                   if e.target_type == NodeType.OBSERVATION and e.relationship == "RELATED_TO"]
                for oid in obs_ids:
                    if oid != res.preferred_observation_id:
                        suppressed_obs.add(oid)

        # 2. De-duplicate unresolved correlations
        for corr_id, corr in graph.correlations.items():
            if corr.correlation_type == "DUPLICATES":
                if corr_id not in graph.resolutions_by_conflict:
                    corr_edges = graph.out_edges.get(corr_id, [])
                    obs_ids = [e.target_id for e in corr_edges 
                               if e.target_type == NodeType.OBSERVATION and e.relationship == "RELATED_TO"]
                    if len(obs_ids) >= 2:
                        for oid in obs_ids[1:]:
                            suppressed_obs.add(oid)

        # 3. Identify Unresolved Conflicts
        unresolved_conflicts = []
        for cid in graph.conflicts:
            if cid not in graph.resolutions_by_conflict:
                unresolved_conflicts.append(cid)

        # 4. Filter and Rank Observations by Evidence Strength
        ranked_obs = []
        for obs_id, obs in graph.observations.items():
            if obs_id not in suppressed_obs:
                ev_ids = get_observation_evidence(obs_id)
                strength = sum(graph.evidence[eid].confidence for eid in ev_ids if eid in graph.evidence)
                ranked_obs.append((strength, obs))

        # Sort descending by evidence strength
        ranked_obs.sort(key=lambda x: x[0], reverse=True)

        key_observations = []
        traceability = {}
        for idx, (strength, obs) in enumerate(ranked_obs):
            finding_id = f"EXEC-FIND-OBS-{obs.observation_id}"
            finding = ExecutiveFinding(
                finding_id=finding_id,
                finding_type="OBSERVATION",
                description=obs.observation,
                confidence=obs.confidence,
                supporting_observations=[obs.observation_id]
            )
            key_observations.append(finding)
            traceability[finding_id] = trace_observation(graph, obs.observation_id, visited=set())

        # 5. Filter and Rank Major Risks
        major_risks = []
        for risk_id, risk in graph.risks.items():
            # Only keep risk if it references non-suppressed observations (or if no references exist)
            ref_obs = [edge.target_id for edge in graph.out_edges.get(risk_id, [])
                       if edge.target_type == NodeType.OBSERVATION and edge.relationship == "REFERENCES"]
            
            # Check if all referenced observations are suppressed
            if ref_obs and all(oid in suppressed_obs for oid in ref_obs):
                continue

            finding_id = f"EXEC-FIND-RISK-{risk.risk_id}"
            finding = ExecutiveFinding(
                finding_id=finding_id,
                finding_type="RISK",
                description=risk.description,
                confidence=risk.confidence,
                supporting_observations=ref_obs
            )
            major_risks.append(finding)

            # Trace risk to its observations and build lineage
            obs_traces = []
            for oid in ref_obs:
                tr = trace_observation(graph, oid, visited=set())
                if tr:
                    obs_traces.append(tr)
            traceability[finding_id] = {
                "risk": risk.model_dump() if hasattr(risk, "model_dump") else risk,
                "observations": obs_traces
            }

        # Sort risks descending by confidence
        major_risks.sort(key=lambda x: x.confidence, reverse=True)

        # 6. Compute overall graph confidence & evidence strength
        total_key_obs = len(key_observations)
        avg_confidence = sum(f.confidence for f in key_observations) / total_key_obs if total_key_obs > 0 else 0.8
        avg_strength = sum(strength for strength, _ in ranked_obs) / total_key_obs if total_key_obs > 0 else 0.0

        # 7. Readiness Level (TRL) Heuristics
        import re
        trl_vals = []
        for obs in graph.observations.values():
            if obs.domain == "trl":
                match = re.search(r'\b([1-9])\b', obs.observation)
                if match:
                    trl_vals.append(int(match.group(1)))
        for claim in graph.claims.values():
            if "trl" in claim.claim_id.lower() or "trl" in claim.claim_text.lower():
                match = re.search(r'\b([1-9])\b', claim.claim_text)
                if match:
                    trl_vals.append(int(match.group(1)))
        readiness_level = f"TRL-{max(trl_vals)}" if trl_vals else "TRL-1"

        # 8. Deterministic Executive Summary
        overview = (f"Executive assessment compiled from {len(graph.documents)} documents across "
                    f"{len(graph.assessments)} expert assessments, yielding {total_key_obs} key observations "
                    f"and {len(major_risks)} major risks.")

        strengths = [f.description for f in key_observations[:3]]
        weaknesses = [f.description for f in major_risks[:3]]

        # Opportunities: high confidence observations in product/market
        opportunities = []
        for _, obs in ranked_obs:
            if obs.domain in ("product", "market") and obs.confidence >= 0.8:
                opportunities.append(f"Opportunity in {obs.domain}: {obs.observation}")
        if not opportunities:
            opportunities = [f"Validated finding: {f.description}" for f in key_observations[:2]]

        # Threats: severe risks or unresolved conflicts
        threats = []
        for f in major_risks:
            if f.confidence >= 0.8:
                threats.append(f"High Risk: {f.description}")
        for cid in unresolved_conflicts:
            c_node = graph.conflicts.get(cid)
            if c_node:
                threats.append(f"Unresolved Conflict: {c_node.description}")
        if not threats:
            threats = [f"Potential Risk: {f.description}" for f in major_risks[:2]]

        # Missing Information: Questions and missing evidence requests
        missing_information = []
        for q in graph.questions.values():
            missing_information.append(f"{q.question} (Purpose: {q.purpose})")
        if not missing_information:
            missing_information = ["No critical missing information identified."]

        summary = ExecutiveSummary(
            overview=overview,
            strengths=strengths,
            weaknesses=weaknesses,
            opportunities=opportunities,
            threats=threats,
            missing_information=missing_information
        )

        # 9. Create ExecutiveAssessment Node
        assessment_id = f"EXEC-ASSESSMENT-{str(uuid.uuid4())[:8]}"
        exec_node = ExecutiveAssessment(
            node_id=assessment_id,
            node_type=NodeType.EXECUTIVE,
            assessment_id=assessment_id,
            generated_at=datetime.utcnow().isoformat() + "Z",
            graph_version=graph.graph_version,
            summary=summary,
            key_observations=key_observations,
            major_risks=major_risks,
            unresolved_conflicts=unresolved_conflicts,
            evidence_strength=avg_strength,
            confidence=avg_confidence,
            readiness_level=readiness_level,
            traceability=traceability,
            metadata={
                "suppressed_observations_count": len(suppressed_obs),
                "total_risks_evaluated": len(graph.risks),
                "total_conflicts_evaluated": len(graph.conflicts)
            }
        )

        graph.executive_assessment = exec_node

        # 10. Populate Indexes
        graph.executive_indexes = {
            "findings_by_type": {
                "OBSERVATION": [f.finding_id for f in key_observations],
                "RISK": [f.finding_id for f in major_risks]
            },
            "findings_by_id": {f.finding_id: f.model_dump() for f in key_observations + major_risks}
        }

        # 11. Populate Statistics
        graph.executive_statistics = {
            "total_findings": len(key_observations) + len(major_risks),
            "total_key_observations": len(key_observations),
            "total_major_risks": len(major_risks),
            "total_unresolved_conflicts": len(unresolved_conflicts),
            "readiness_level": readiness_level
        }

        # Update general graph statistics
        from app.modules.evaluation.graph.graph_builder import ObservationGraphBuilder
        ObservationGraphBuilder._update_statistics(graph)

        # Recompute hash
        graph.graph_hash = ObservationGraphBuilder._compute_hash(graph)

        return graph
