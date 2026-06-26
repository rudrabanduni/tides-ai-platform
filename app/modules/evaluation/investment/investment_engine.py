import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType, Edge
from app.modules.evaluation.graph.graph_queries import trace_observation, trace_risk
from app.modules.evaluation.investment.investment_models import (
    InvestmentRecommendation, InvestmentMetrics, InvestmentAssessment
)


class InvestmentEngine:
    """Deterministic Investment Decision Engine for the TIDES Intelligence Engine (TIE)."""

    @staticmethod
    def generate(graph: ObservationGraph) -> ObservationGraph:
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

        # De-duplicate unresolved correlations
        for corr_id, corr in graph.correlations.items():
            if corr.correlation_type == "DUPLICATES":
                if corr_id not in graph.resolutions_by_conflict:
                    corr_edges = graph.out_edges.get(corr_id, [])
                    obs_ids = [e.target_id for e in corr_edges 
                               if e.target_type == NodeType.OBSERVATION and e.relationship == "RELATED_TO"]
                    if len(obs_ids) >= 2:
                        for oid in obs_ids[1:]:
                            suppressed_obs.add(oid)

        # 2. Extract Executive Assessment
        exec_node = graph.executive_assessment
        executive_score = 70.0
        exec_conf = 0.8
        exec_summary_text = "No executive summary available."
        
        if exec_node:
            executive_score = exec_node.confidence * 100.0
            exec_conf = exec_node.confidence
            if exec_node.summary and exec_node.summary.overview:
                exec_summary_text = exec_node.summary.overview

        # 3. Compute Domain Scores based on non-suppressed observations or fallback to assessment confidence
        def get_domain_score_and_conf(domain_name: str, default_score: float = 70.0) -> (float, float):
            obs_list = [obs for obs in graph.observations.values() 
                        if obs.domain == domain_name and obs.observation_id not in suppressed_obs]
            if obs_list:
                avg_conf = sum(o.confidence for o in obs_list) / len(obs_list)
                return avg_conf * 100.0, avg_conf
            
            # Fallback to AssessmentNode
            asm_ids = graph.assessments_by_domain.get(domain_name, [])
            if asm_ids:
                asm_node = graph.assessments.get(asm_ids[0])
                if asm_node:
                    return asm_node.confidence * 100.0, asm_node.confidence
            
            return default_score, 0.8

        founder_score, founder_conf = get_domain_score_and_conf("founder")
        technology_score, technology_conf = get_domain_score_and_conf("product")  # product expert maps to technology
        market_score, market_conf = get_domain_score_and_conf("market")
        competition_score, competition_conf = get_domain_score_and_conf("competition")
        financial_score, financial_conf = get_domain_score_and_conf("financial")
        ip_score, ip_conf = get_domain_score_and_conf("ip")

        # 4. TRL Readiness Score
        trl_vals = []
        if exec_node and exec_node.readiness_level:
            match = re.search(r'\b([1-9])\b', exec_node.readiness_level)
            if match:
                trl_vals.append(int(match.group(1)))
        
        # Scan observations/claims for TRL if needed
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
        
        trl_val = max(trl_vals) if trl_vals else 1
        readiness_score = (trl_val / 9.0) * 100.0
        readiness_conf = 0.9  # High confidence since TRL is deterministic / standard

        # 5. Risk Score (average confidence of non-suppressed risks)
        active_risks = []
        for r_id, risk in graph.risks.items():
            ref_obs = [edge.target_id for edge in graph.out_edges.get(r_id, [])
                       if edge.target_type == NodeType.OBSERVATION and edge.relationship == "REFERENCES"]
            if ref_obs and all(oid in suppressed_obs for oid in ref_obs):
                continue
            active_risks.append(risk)

        if active_risks:
            risk_conf = sum(r.confidence for r in active_risks) / len(active_risks)
            risk_score = risk_conf * 100.0
        else:
            risk_conf = 0.0
            risk_score = 0.0

        # 6. Calculate Weighted Score
        # Founder: 20%, Product: 15%, TRL: 10%, Market: 15%, Competition: 10%, Financial: 15%, IP: 5%, Risk: -10%, Executive: 20%
        weighted_score = (
            (0.20 * founder_score) +
            (0.15 * technology_score) +
            (0.10 * readiness_score) +
            (0.15 * market_score) +
            (0.10 * competition_score) +
            (0.15 * financial_score) +
            (0.05 * ip_score) +
            (0.20 * executive_score) -
            (0.10 * risk_score)
        )
        
        # Clamp to [0, 100]
        investment_score = max(0.0, min(100.0, weighted_score))

        # 7. Map Recommendation
        if investment_score < 40.0:
            recommendation = InvestmentRecommendation.DO_NOT_INVEST
        elif investment_score < 55.0:
            recommendation = InvestmentRecommendation.REVIEW
        elif investment_score < 70.0:
            recommendation = InvestmentRecommendation.WATCHLIST
        elif investment_score < 85.0:
            recommendation = InvestmentRecommendation.INVEST
        else:
            recommendation = InvestmentRecommendation.STRONG_INVEST

        # 8. Compute Overall Investment Confidence
        # Absolute weights: Founder 20%, Product 15%, TRL 10%, Market 15%, Competition 10%, Financial 15%, IP 5%, Risk 10%, Executive 20%
        # Sum of absolute weights = 1.20
        overall_confidence = (
            (0.20 * founder_conf) +
            (0.15 * technology_conf) +
            (0.10 * readiness_conf) +
            (0.15 * market_conf) +
            (0.10 * competition_conf) +
            (0.15 * financial_conf) +
            (0.05 * ip_conf) +
            (0.10 * risk_conf) +
            (0.20 * exec_conf)
        ) / 1.20

        # 9. Gather Strengths, Weaknesses, and Major Risks
        # Strengths: Top non-suppressed observations
        non_suppressed_obs = [obs for obs in graph.observations.values() if obs.observation_id not in suppressed_obs]
        non_suppressed_obs.sort(key=lambda x: x.confidence, reverse=True)
        strengths = [obs.observation for obs in non_suppressed_obs[:3]]
        
        # Weaknesses/Risks
        active_risks.sort(key=lambda x: x.confidence, reverse=True)
        weaknesses = [r.description for r in active_risks[:3]]
        major_risks_list = [r.description for r in active_risks]

        # 10. Generate Deterministic Rationale
        investment_rationale = (
            f"Deterministic investment evaluation completed with score {investment_score:.2f} "
            f"resulting in a recommendation of {recommendation.value}. Key contributors: "
            f"Founder score {founder_score:.1f}, Technology score {technology_score:.1f}, "
            f"Market score {market_score:.1f}, TRL Readiness score {readiness_score:.1f}. "
            f"A risk penalty of {risk_score:.1f} was applied based on {len(active_risks)} active risks."
        )

        # 11. Missing information and follow-up questions
        missing_info = []
        follow_up_qs = []
        for q in graph.questions.values():
            missing_info.append(f"{q.question} (Purpose: {q.purpose})")
            follow_up_qs.append(q.question)
        if not missing_info:
            missing_info = ["No critical missing information identified."]
            follow_up_qs = ["No immediate follow-up questions."]

        # 12. Traceability Map
        traceability = {}
        # Trace every strength back to its observation
        for obs in non_suppressed_obs[:3]:
            str_id = f"STRENGTH-{obs.observation_id}"
            traceability[str_id] = trace_observation(graph, obs.observation_id, visited=set())
        
        # Trace every active risk
        for r in active_risks:
            r_id = f"RISK-{r.risk_id}"
            traceability[r_id] = trace_risk(graph, r.risk_id, visited=set())

        # Include score details in traceability
        traceability["RECOMMENDATION"] = {
            "investment_score": investment_score,
            "weighted_score_raw": weighted_score,
            "domain_scores": {
                "founder": founder_score,
                "technology": technology_score,
                "readiness": readiness_score,
                "market": market_score,
                "competition": competition_score,
                "financial": financial_score,
                "ip": ip_score,
                "risk": risk_score,
                "executive": executive_score
            },
            "recommendation": recommendation.value,
            "confidence": overall_confidence
        }

        # 13. Metrics calculation
        # Duplicate observations: count RELATED_TO edges with state == "DUPLICATE"
        duplicate_count = 0
        for edge in graph.edges:
            if edge.relationship == "RELATED_TO" and edge.state == "DUPLICATE":
                duplicate_count += 1

        # Consensus: corroborated vs total observations
        total_obs_count = len(graph.observations)
        corroborated_obs = sum(1 for o in graph.observations.values() if getattr(o, "consensus_status", "independent") == "corroborated")
        overall_consensus = corroborated_obs / total_obs_count if total_obs_count > 0 else 1.0

        # Document coverage: percentage of documents covered by evidence
        total_docs = len(graph.documents)
        covered_docs = set()
        for edge in graph.edges:
            if edge.target_type == NodeType.DOCUMENT and edge.relationship == "DERIVED_FROM":
                covered_docs.add(edge.target_id)
        doc_coverage = len(covered_docs) / total_docs if total_docs > 0 else 1.0

        # Evidence strength
        total_evidence_conf = sum(ev.confidence for ev in graph.evidence.values())
        avg_evidence_strength = total_evidence_conf / len(graph.evidence) if graph.evidence else 0.0

        metrics = InvestmentMetrics(
            weighted_score=investment_score,
            evidence_strength=avg_evidence_strength,
            graph_confidence=overall_confidence,
            resolved_conflicts=graph.graph_stats.resolved_conflicts,
            unresolved_conflicts=graph.graph_stats.unresolved_conflicts,
            duplicate_observations=duplicate_count,
            overall_consensus=overall_consensus,
            document_coverage=doc_coverage
        )

        # 14. Create InvestmentAssessment node
        assessment_id = f"INVEST-ASSESSMENT-{str(uuid.uuid4())[:8]}"
        invest_node = InvestmentAssessment(
            node_id=assessment_id,
            node_type=NodeType.INVESTMENT,
            assessment_id=assessment_id,
            generated_at=datetime.utcnow().isoformat() + "Z",
            graph_version=graph.graph_version,
            recommendation=recommendation,
            confidence=overall_confidence,
            investment_score=investment_score,
            readiness_score=readiness_score,
            risk_score=risk_score,
            technology_score=technology_score,
            market_score=market_score,
            founder_score=founder_score,
            financial_score=financial_score,
            competition_score=competition_score,
            ip_score=ip_score,
            executive_summary=exec_summary_text,
            strengths=strengths,
            weaknesses=weaknesses,
            major_risks=major_risks_list,
            investment_rationale=investment_rationale,
            missing_information=missing_info,
            follow_up_questions=follow_up_qs,
            traceability=traceability,
            metadata={
                "metrics": metrics.model_dump(),
                "suppressed_observations_count": len(suppressed_obs),
                "total_risks_evaluated": len(graph.risks),
                "total_conflicts_evaluated": len(graph.conflicts)
            }
        )

        graph.investment_assessment = invest_node

        # 15. Populate Indexes
        graph.investment_indexes = {
            "strengths": [f"STRENGTH-{obs.observation_id}" for obs in non_suppressed_obs[:3]],
            "risks": [f"RISK-{r.risk_id}" for r in active_risks]
        }

        # 16. Populate Statistics
        graph.investment_statistics = {
            "investment_score": investment_score,
            "recommendation": recommendation.value,
            "confidence": overall_confidence,
            "active_risks_count": len(active_risks),
            "duplicate_observations_count": duplicate_count,
            "document_coverage": doc_coverage,
            "overall_consensus": overall_consensus
        }

        # Re-update graph statistics
        from app.modules.evaluation.graph.graph_builder import ObservationGraphBuilder
        ObservationGraphBuilder._update_statistics(graph)

        # Recompute hash
        graph.graph_hash = ObservationGraphBuilder._compute_hash(graph)

        return graph
