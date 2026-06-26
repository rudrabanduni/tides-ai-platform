import uuid
import hashlib
import json
from datetime import datetime
from typing import Any, Dict, List, Set

from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType
from app.modules.evaluation.prompts.manager import PromptManager
from app.modules.explainability.explanation_engine import ExplanationEngine
from app.modules.reporting.report_models import Report


class ReportBuilder:
    """Builder to compile evaluation graph inputs into a unified Report model."""

    @staticmethod
    def _compute_hash(report_data: dict) -> str:
        """Compute deterministic SHA-256 hash of report fields, ignoring report_id, generated_at, and report_hash."""
        data = report_data.copy()
        data.pop("report_hash", None)
        data.pop("report_id", None)
        data.pop("generated_at", None)
        # Convert any non-serializable objects to string
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    @staticmethod
    def build_report(graph: ObservationGraph, generated_by: str = "TIDES Intelligence Engine") -> Report:
        report_id = f"REP-{str(uuid.uuid4())[:8].upper()}"
        generated_at = datetime.utcnow().isoformat() + "Z"
        startup_id = graph.startup_id or graph.graph_id or "N/A"
        startup_name = graph.startup_name or "Unknown Startup"

        # 1. Identify Suppressed Observations due to Resolved Conflicts or Correlations
        suppressed_obs: Set[str] = set()
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
            if hasattr(corr, "correlation_type") and corr.correlation_type == "DUPLICATES":
                if corr_id not in graph.resolutions_by_conflict:
                    corr_edges = graph.out_edges.get(corr_id, [])
                    obs_ids = [e.target_id for e in corr_edges 
                               if e.target_type == NodeType.OBSERVATION and e.relationship == "RELATED_TO"]
                    if len(obs_ids) >= 2:
                        for oid in obs_ids[1:]:
                            suppressed_obs.add(oid)

        # Helpers
        def get_avg_confidence(items: List[Any], default: float = 1.0) -> float:
            if not items:
                return default
            return sum(getattr(i, "confidence", 1.0) for i in items) / len(items)

        def get_domain_obs(domain_name: str) -> List[Any]:
            return [o for o in graph.observations.values() 
                    if o.domain == domain_name and o.observation_id not in suppressed_obs]

        def format_obs_list(obs_list: List[Any]) -> str:
            if not obs_list:
                return "No observations recorded in this domain."
            lines = []
            for o in sorted(obs_list, key=lambda x: x.observation_id):
                lines.append(f"*   **[{o.observation_id}]** {o.observation} *(Confidence: {o.confidence:.2f})*")
            return "\n".join(lines)

        # --- Section 1: Executive Summary ---
        exec_node = graph.executive_assessment
        if exec_node:
            overview = exec_node.summary.overview if hasattr(exec_node, "summary") else ""
            strengths_list = exec_node.summary.strengths if hasattr(exec_node, "summary") else []
            weaknesses_list = exec_node.summary.weaknesses if hasattr(exec_node, "summary") else []
            opportunities_list = exec_node.summary.opportunities if hasattr(exec_node, "summary") else []
            threats_list = exec_node.summary.threats if hasattr(exec_node, "summary") else []
            readiness_level = exec_node.readiness_level if hasattr(exec_node, "readiness_level") else "N/A"
            
            strengths = "\n".join(f"* {s}" for s in strengths_list) if strengths_list else "None."
            weaknesses = "\n".join(f"* {w}" for w in weaknesses_list) if weaknesses_list else "None."
            opportunities = "\n".join(f"* {o}" for o in opportunities_list) if opportunities_list else "None."
            threats = "\n".join(f"* {t}" for t in threats_list) if threats_list else "None."
        else:
            overview = "Executive assessment has not been compiled."
            strengths = "N/A"
            weaknesses = "N/A"
            opportunities = "N/A"
            threats = "N/A"
            readiness_level = "N/A"

        exec_template = PromptManager.load_reporting_template("executive")
        executive_summary_str = exec_template.format(
            overview=overview,
            strengths=strengths,
            weaknesses=weaknesses,
            opportunities=opportunities,
            threats=threats,
            readiness_level=readiness_level
        )

        # --- Section 2-8: Domain Analyses ---
        domain_mappings = ["founder", "product", "market", "competition", "financial", "ip"]
        rendered_domains = {}
        for d in domain_mappings:
            obs = get_domain_obs(d)
            conf = get_avg_confidence(obs)
            d_template = PromptManager.load_reporting_template(d)
            rendered_domains[f"{d}_analysis"] = d_template.format(
                confidence=conf,
                observations=format_obs_list(obs)
            )

        # TRL (Special case with readiness score)
        trl_obs = get_domain_obs("trl")
        trl_conf = get_avg_confidence(trl_obs)
        readiness_score = getattr(graph.investment_assessment, "readiness_score", 0.0) if graph.investment_assessment else 0.0
        trl_template = PromptManager.load_reporting_template("trl")
        trl_analysis_str = trl_template.format(
            confidence=trl_conf,
            readiness_score=readiness_score,
            observations=format_obs_list(trl_obs)
        )

        # --- Section 9: Risk Analysis ---
        active_risks = []
        for r_id, r in graph.risks.items():
            ref_obs = [edge.target_id for edge in graph.out_edges.get(r_id, [])
                       if edge.target_type == NodeType.OBSERVATION and edge.relationship == "REFERENCES"]
            if ref_obs and all(oid in suppressed_obs for oid in ref_obs):
                continue
            active_risks.append(r)

        if active_risks:
            risk_lines = []
            for r in sorted(active_risks, key=lambda x: x.risk_id):
                risk_lines.append(f"*   **[{r.risk_id}]** *Category: {r.category}* - {r.description}\n    *Reasoning:* {r.reasoning} *(Confidence: {r.confidence:.2f})*")
            risks_content = "\n".join(risk_lines)
        else:
            risks_content = "No active risks identified."

        risk_template = PromptManager.load_reporting_template("risk")
        risk_analysis_str = risk_template.format(
            confidence=get_avg_confidence(active_risks),
            risks=risks_content
        )

        # --- Section 10: Committee Decision ---
        decision = graph.committee_decision
        if decision:
            # Format list values
            blocking_risks_val = "\n".join(f"* {r}" for r in decision.blocking_risks) if decision.blocking_risks else "None."
            required_documents_val = "\n".join(f"* {d}" for d in decision.required_documents) if decision.required_documents else "None."
            follow_up_questions_val = "\n".join(f"* {q}" for q in decision.follow_up_questions) if decision.follow_up_questions else "None."
            
            dd_lines = []
            for item in decision.required_due_diligence:
                blocking_str = " (Blocking)" if getattr(item, "blocking", False) else ""
                docs_req = getattr(item, "documents_required", [])
                docs_str = f" (Required docs: {', '.join(docs_req)})" if docs_req else ""
                dd_lines.append(f"*   **[{item.category}]** Status: {item.status}{blocking_str}{docs_str}\n    *Reason:* {item.reason}")
            required_due_diligence_val = "\n".join(dd_lines) if dd_lines else "None."
            
            committee_template = PromptManager.load_reporting_template("committee")
            committee_decision_str = committee_template.format(
                recommendation=decision.recommendation.value if hasattr(decision.recommendation, "value") else str(decision.recommendation),
                decision_confidence=decision.decision_confidence,
                review_window=decision.review_window,
                investment_priority=decision.investment_priority.value if hasattr(decision.investment_priority, "value") else str(decision.investment_priority),
                incubation_priority=decision.incubation_priority.value if hasattr(decision.incubation_priority, "value") else str(decision.incubation_priority),
                pilot_priority=decision.pilot_priority.value if hasattr(decision.pilot_priority, "value") else str(decision.pilot_priority),
                decision_reasoning=decision.decision_reasoning,
                committee_notes=decision.committee_notes,
                blocking_risks=blocking_risks_val,
                required_due_diligence=required_due_diligence_val,
                required_documents=required_documents_val,
                follow_up_questions=follow_up_questions_val
            )
        else:
            committee_decision_str = "Investment committee decision has not been compiled."

        # --- Section 11: Investment Recommendation ---
        inv = graph.investment_assessment
        if inv:
            inv_template = PromptManager.load_reporting_template("investment")
            investment_recommendation_str = inv_template.format(
                recommendation=inv.recommendation.value if hasattr(inv.recommendation, "value") else str(inv.recommendation),
                investment_score=inv.investment_score,
                confidence=inv.confidence,
                investment_rationale=inv.investment_rationale
            )
        else:
            investment_recommendation_str = "Investment recommendation summary has not been compiled."

        # --- Section 12: Portfolio Position ---
        port = graph.portfolio_entry
        if port:
            port_template = PromptManager.load_reporting_template("portfolio")
            portfolio_position_str = port_template.format(
                rank=port.rank,
                percentile=port.percentile,
                category=port.category,
                ranking_reason=port.ranking_reason
            )
        else:
            portfolio_position_str = "Portfolio position rankings have not been compiled."

        # --- Section 13: Explainability Appendix ---
        engine = ExplanationEngine()
        explanations = []
        
        # 1. Committee Decision
        if decision:
            try:
                exp_c = engine.explain_committee_decision(graph, decision.decision_id)
                explanations.append(("Committee Decision", exp_c))
            except Exception:
                pass
                
        # 2. Investment Recommendation
        if inv:
            try:
                exp_i = engine.explain_investment_decision(graph, inv.node_id)
                explanations.append(("Investment Recommendation", exp_i))
            except Exception:
                pass
                
        # 3. Portfolio Rank
        if port:
            try:
                exp_p = engine.explain_portfolio_ranking(graph, startup_id)
                explanations.append(("Portfolio Position Rank", exp_p))
            except Exception:
                pass

        exp_lines = []
        for title, exp in explanations:
            # Format lineage
            docs_traced = ", ".join(f"{d.get('document_name', 'Doc')} ({d.get('document_id', d.get('node_id'))})" for d in exp.lineage.documents) or "None"
            claims_traced = ", ".join(f"{c.get('claim_text', 'Claim')} ({c.get('claim_id', c.get('node_id'))})" for c in exp.lineage.claims) or "None"
            ev_traced = ", ".join(f"{e.get('excerpt', 'Evidence')[:40]}... ({e.get('evidence_id', e.get('node_id'))})" for e in exp.lineage.evidence) or "None"
            obs_traced = ", ".join(f"{o.get('observation', 'Observation')[:40]}... ({o.get('observation_id', o.get('node_id'))})" for o in exp.lineage.observations) or "None"
            asm_traced = ", ".join(f"{a.get('expert_name', 'Expert')} ({a.get('assessment_id', a.get('node_id'))})" for a in exp.lineage.assessments) or "None"
            
            exp_lines.append(
                f"### Traceability for {title}\n"
                f"*   **Summary:** {exp.summary}\n"
                f"*   **Trace Confidence:** {exp.confidence:.2f}\n"
                f"*   **Detailed Reasoning:** {exp.reasoning}\n"
                f"*   **Lineage Trace:**\n"
                f"    *   *Documents Traced:* {docs_traced}\n"
                f"    *   *Claims Traced:* {claims_traced}\n"
                f"    *   *Evidence Traced:* {ev_traced}\n"
                f"    *   *Observations Traced:* {obs_traced}\n"
                f"    *   *Expert Assessments Traced:* {asm_traced}\n"
            )
        
        appendix_template = PromptManager.load_reporting_template("appendix")
        explainability_appendix_str = appendix_template.format(
            title="Explainability & Traceability Appendix",
            content="\n".join(exp_lines) if exp_lines else "No decision nodes available for explainability tracing."
        )

        # --- Section 14: Evidence Appendix ---
        # Collect unique evidence IDs from active observations/risks via edges
        evidence_ids = set()
        for o in graph.observations.values():
            if o.observation_id not in suppressed_obs:
                for edge in graph.out_edges.get(o.observation_id, []):
                    if edge.target_type == NodeType.EVIDENCE:
                        evidence_ids.add(edge.target_id)
        
        for r in active_risks:
            for edge in graph.out_edges.get(r.risk_id, []):
                if edge.target_type == NodeType.EVIDENCE:
                    evidence_ids.add(edge.target_id)

        ev_lines = []
        for eid in sorted(list(evidence_ids)):
            ev_node = graph.evidence.get(eid)
            if ev_node:
                # Find document
                doc_name = "Unknown Document"
                for edge in graph.out_edges.get(eid, []):
                    if edge.relationship == "DERIVED_FROM" and edge.target_type == NodeType.DOCUMENT:
                        doc = graph.documents.get(edge.target_id)
                        if doc:
                            doc_name = f"{doc.document_name} ({doc.document_type})"
                            break
                            
                ev_lines.append(
                    f"### Evidence ID: {eid} (Confidence: {ev_node.confidence:.2f})\n"
                    f"*   **Source Document:** {doc_name}\n"
                    f"*   **Location:** {ev_node.location}\n"
                    f"*   **Excerpt:** *\"{ev_node.excerpt}\"*\n"
                )

        evidence_appendix_str = appendix_template.format(
            title="Evidence Audit Trail & Citations Appendix",
            content="\n".join(ev_lines) if ev_lines else "No source evidence referenced in active observations."
        )

        # Gather metadata
        metadata = {
            "graph_hash": graph.graph_hash,
            "graph_version": graph.graph_version,
            "observations_count": len(graph.observations),
            "suppressed_observations_count": len(suppressed_obs),
            "active_risks_count": len(active_risks),
            "total_evidence_referenced": len(evidence_ids),
            "generated_by": generated_by,
        }

        # Build initial report dictionary to compute hash
        report_data = {
            "report_id": report_id,
            "startup_id": startup_id,
            "startup_name": startup_name,
            "generated_at": generated_at,
            "generated_by": generated_by,
            "report_version": "1.0.0",
            "executive_summary": executive_summary_str,
            "founder_analysis": rendered_domains["founder_analysis"],
            "product_analysis": rendered_domains["product_analysis"],
            "market_analysis": rendered_domains["market_analysis"],
            "competition_analysis": rendered_domains["competition_analysis"],
            "financial_analysis": rendered_domains["financial_analysis"],
            "trl_analysis": trl_analysis_str,
            "ip_analysis": rendered_domains["ip_analysis"],
            "risk_analysis": risk_analysis_str,
            "committee_decision": committee_decision_str,
            "investment_recommendation": investment_recommendation_str,
            "portfolio_position": portfolio_position_str,
            "explainability_appendix": explainability_appendix_str,
            "evidence_appendix": evidence_appendix_str,
            "metadata": metadata
        }

        report_hash = ReportBuilder._compute_hash(report_data)
        report_data["report_hash"] = report_hash

        return Report(**report_data)
