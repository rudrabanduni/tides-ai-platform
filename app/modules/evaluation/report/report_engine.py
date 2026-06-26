import uuid
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType, Edge
from app.modules.evaluation.graph.graph_queries import (
    trace_observation, trace_risk, trace_claim, trace_evidence
)
from app.modules.evaluation.report.report_models import (
    ReportSection, Appendix, DueDiligenceReport
)


class DueDiligenceReportEngine:
    """Consumes the ObservationGraph and deterministically compiles a DueDiligenceReport."""

    @staticmethod
    def generate(graph: ObservationGraph) -> ObservationGraph:
        report_id = f"REPORT-{str(uuid.uuid4())[:8]}"
        generated_at = datetime.utcnow().isoformat() + "Z"

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

        # 2. Extract active risks
        active_risks = []
        for r_id, risk in graph.risks.items():
            ref_obs = [edge.target_id for edge in graph.out_edges.get(r_id, [])
                       if edge.target_type == NodeType.OBSERVATION and edge.relationship == "REFERENCES"]
            if ref_obs and all(oid in suppressed_obs for oid in ref_obs):
                continue
            active_risks.append(risk)

        # Helper to average confidences of a list of items
        def get_avg_confidence(items: List[Any], default: float = 0.8) -> float:
            if not items:
                return default
            return sum(getattr(i, "confidence", 0.8) for i in items) / len(items)

        # Helper to gather non-suppressed observations for a domain
        def get_domain_obs(domain_name: str) -> List[Any]:
            return [o for o in graph.observations.values() 
                    if o.domain == domain_name and o.observation_id not in suppressed_obs]

        # Helper to format list of observations into a markdown block
        def format_obs_list(obs_list: List[Any]) -> str:
            if not obs_list:
                return "No observations recorded in this domain."
            lines = []
            for o in sorted(obs_list, key=lambda x: x.observation_id):
                lines.append(f"*   **[{o.observation_id}]** {o.observation} *(Confidence: {o.confidence:.2f})*")
            return "\n".join(lines)

        # --- Section 1: Executive Summary ---
        exec_node = graph.executive_assessment
        exec_content = "Executive assessment has not been compiled."
        exec_conf = 0.8
        exec_nodes = []
        if exec_node:
            exec_conf = exec_node.confidence
            exec_nodes = [f.finding_id for f in exec_node.key_observations + exec_node.major_risks]
            
            summary = exec_node.summary
            exec_content = (
                f"**Overview:**\n{summary.overview}\n\n"
                f"**Strengths:**\n" + "\n".join(f"*   {s}" for s in summary.strengths) + "\n\n"
                f"**Weaknesses/Risks:**\n" + "\n".join(f"*   {w}" for w in summary.weaknesses) + "\n\n"
                f"**Opportunities:**\n" + "\n".join(f"*   {o}" for o in summary.opportunities) + "\n\n"
                f"**Threats:**\n" + "\n".join(f"*   {t}" for t in summary.threats)
            )

        section_executive = ReportSection(
            section_id="executive_summary",
            title="Executive Summary",
            content=exec_content,
            supporting_nodes=exec_nodes,
            confidence=exec_conf
        )

        # --- Section 2: Investment Summary ---
        inv_node = graph.investment_assessment
        inv_content = "Investment assessment has not been compiled."
        inv_conf = 0.8
        inv_nodes = []
        if inv_node:
            inv_conf = inv_node.confidence
            inv_nodes = [inv_node.node_id]
            metrics = inv_node.metadata.get("metrics", {}) if inv_node.metadata else {}
            inv_content = (
                f"**Recommendation:** {inv_node.recommendation.value}\n\n"
                f"**Investment Score:** {inv_node.investment_score:.2f} / 100\n\n"
                f"**Rationale:**\n{inv_node.investment_rationale}\n\n"
                f"**Key Metrics:**\n"
                f"*   Weighted Score: {metrics.get('weighted_score', 0.0):.2f}\n"
                f"*   Evidence Strength: {metrics.get('evidence_strength', 0.0):.2f}\n"
                f"*   Consensus Level: {metrics.get('overall_consensus', 0.0)*100.0:.1f}%\n"
                f"*   Document Coverage: {metrics.get('document_coverage', 0.0)*100.0:.1f}%\n"
                f"*   Resolved Conflicts: {metrics.get('resolved_conflicts', 0)}\n"
                f"*   Unresolved Conflicts: {metrics.get('unresolved_conflicts', 0)}"
            )

        section_investment = ReportSection(
            section_id="investment_summary",
            title="Investment Recommendation Summary",
            content=inv_content,
            supporting_nodes=inv_nodes,
            confidence=inv_conf
        )

        # --- Section 3-9: Domain Analyses ---
        # Founder
        founder_obs = get_domain_obs("founder")
        section_founder = ReportSection(
            section_id="founder_analysis",
            title="Founder & Management Team Analysis",
            content=format_obs_list(founder_obs),
            supporting_nodes=[o.observation_id for o in founder_obs],
            confidence=get_avg_confidence(founder_obs)
        )

        # Product
        product_obs = get_domain_obs("product")
        section_product = ReportSection(
            section_id="product_analysis",
            title="Product & Technology Capability Analysis",
            content=format_obs_list(product_obs),
            supporting_nodes=[o.observation_id for o in product_obs],
            confidence=get_avg_confidence(product_obs)
        )

        # TRL
        trl_obs = get_domain_obs("trl")
        readiness_score_str = f"Readiness Score: {inv_node.readiness_score:.1f} / 100" if inv_node else "Readiness Score: N/A"
        section_trl = ReportSection(
            section_id="trl_analysis",
            title="Technology Readiness Level (TRL) Maturity Analysis",
            content=f"**Maturity Level:** {readiness_score_str}\n\n**Observations:**\n" + format_obs_list(trl_obs),
            supporting_nodes=[o.observation_id for o in trl_obs],
            confidence=get_avg_confidence(trl_obs)
        )

        # Market
        market_obs = get_domain_obs("market")
        section_market = ReportSection(
            section_id="market_analysis",
            title="Market Size & Customer Segment Analysis",
            content=format_obs_list(market_obs),
            supporting_nodes=[o.observation_id for o in market_obs],
            confidence=get_avg_confidence(market_obs)
        )

        # Competition
        comp_obs = get_domain_obs("competition")
        section_competition = ReportSection(
            section_id="competition_analysis",
            title="Competitor Landscape & Tech Defensibility Analysis",
            content=format_obs_list(comp_obs),
            supporting_nodes=[o.observation_id for o in comp_obs],
            confidence=get_avg_confidence(comp_obs)
        )

        # Financial
        financial_obs = get_domain_obs("financial")
        section_financial = ReportSection(
            section_id="financial_analysis",
            title="Financial Projection & Capital runway Analysis",
            content=format_obs_list(financial_obs),
            supporting_nodes=[o.observation_id for o in financial_obs],
            confidence=get_avg_confidence(financial_obs)
        )

        # IP
        ip_obs = get_domain_obs("ip")
        section_ip = ReportSection(
            section_id="ip_analysis",
            title="Intellectual Property (IP) Protection & Freedom-to-Operate Analysis",
            content=format_obs_list(ip_obs),
            supporting_nodes=[o.observation_id for o in ip_obs],
            confidence=get_avg_confidence(ip_obs)
        )

        # Risk
        risk_content = "No active risks identified."
        if active_risks:
            risk_content = "\n".join(
                f"*   **[{r.risk_id}]** *Category: {r.category}* - {r.description}\n"
                f"    *Reasoning:* {r.reasoning} *(Confidence: {r.confidence:.2f})*"
                for r in sorted(active_risks, key=lambda x: x.risk_id)
            )
        section_risk = ReportSection(
            section_id="risk_analysis",
            title="Risk Analysis & Exposure Directory",
            content=risk_content,
            supporting_nodes=[r.risk_id for r in active_risks],
            confidence=get_avg_confidence(active_risks)
        )

        # --- Section 10-15: Graph Data Listings ---
        # Observations Directory
        all_active_obs = [o for o in graph.observations.values() if o.observation_id not in suppressed_obs]
        obs_dir_lines = []
        for domain in sorted(list({o.domain for o in all_active_obs})):
            dom_obs = [o for o in all_active_obs if o.domain == domain]
            obs_dir_lines.append(f"### {domain.capitalize()} Observations")
            obs_dir_lines.append(format_obs_list(dom_obs) + "\n")
        section_observations = ReportSection(
            section_id="observations",
            title="Full Observations Directory",
            content="\n".join(obs_dir_lines) if obs_dir_lines else "No active observations in the graph.",
            supporting_nodes=[o.observation_id for o in all_active_obs],
            confidence=get_avg_confidence(all_active_obs)
        )

        # Risks Directory
        section_risks = ReportSection(
            section_id="risks",
            title="Full Risks Directory",
            content=risk_content,
            supporting_nodes=[r.risk_id for r in active_risks],
            confidence=get_avg_confidence(active_risks)
        )

        # Conflicts Directory
        unresolved_conflicts = [c for c_id, c in graph.conflicts.items() if c_id not in graph.resolutions_by_conflict]
        conflict_lines = []
        conflict_lines.append("### Unresolved Conflicts")
        if unresolved_conflicts:
            for c in sorted(unresolved_conflicts, key=lambda x: x.conflict_id):
                conflict_lines.append(f"*   **[{c.conflict_id}]** {c.description} *(Confidence: {c.confidence:.2f})*")
        else:
            conflict_lines.append("All conflicts in the graph have been resolved.")
        conflict_lines.append("\n### Resolved Conflicts")
        resolved_conflicts = [c for c_id, c in graph.conflicts.items() if c_id in graph.resolutions_by_conflict]
        if resolved_conflicts:
            for c in sorted(resolved_conflicts, key=lambda x: x.conflict_id):
                conflict_lines.append(f"*   **[{c.conflict_id}]** {c.description}")
        else:
            conflict_lines.append("No resolved conflicts in the graph.")

        section_conflicts = ReportSection(
            section_id="conflicts",
            title="Factual and Logic Conflicts Directory",
            content="\n".join(conflict_lines),
            supporting_nodes=list(graph.conflicts.keys()),
            confidence=get_avg_confidence(list(graph.conflicts.values()))
        )

        # Resolutions Directory
        res_lines = []
        for res in sorted(graph.resolutions.values(), key=lambda x: x.resolution_id):
            res_lines.append(
                f"*   **[{res.resolution_id}]** Resolves conflict **{res.conflict_id}**\n"
                f"    *Preferred Observation:* {res.preferred_observation_id or 'None (Insufficient Evidence)'}\n"
                f"    *Resolution Type:* {res.resolution_type}\n"
                f"    *Reasoning:* {res.reasoning} *(Confidence: {res.confidence:.2f})*"
            )
        section_resolutions = ReportSection(
            section_id="resolutions",
            title="Conflict Resolutions Log",
            content="\n".join(res_lines) if res_lines else "No conflicts have been resolved in the graph.",
            supporting_nodes=list(graph.resolutions.keys()),
            confidence=get_avg_confidence(list(graph.resolutions.values()))
        )

        # Missing Information
        missing_lines = []
        for q in sorted(graph.questions.values(), key=lambda x: x.question_id):
            if "purpose" in q.__dict__ and q.purpose:
                missing_lines.append(f"*   Missing Evidence: {q.question} (Purpose: {q.purpose})")
        section_missing = ReportSection(
            section_id="missing_information",
            title="Missing Information & Evidence Gaps",
            content="\n".join(missing_lines) if missing_lines else "No critical missing evidence gaps identified.",
            supporting_nodes=list(graph.questions.keys()),
            confidence=1.0
        )

        # Follow-up Questions
        q_lines = []
        for q in sorted(graph.questions.values(), key=lambda x: x.question_id):
            q_lines.append(f"*   **[{q.question_id}]** {q.question}")
        section_questions = ReportSection(
            section_id="follow_up_questions",
            title="Follow-up Questions List",
            content="\n".join(q_lines) if q_lines else "No follow-up questions registered.",
            supporting_nodes=list(graph.questions.keys()),
            confidence=1.0
        )

        # --- Appendices ---
        appendices = []
        
        # Appendix A: Document Inventory
        doc_inv_lines = ["The following source documents were used to populate this evaluation graph:"]
        for d in sorted(graph.documents.values(), key=lambda x: x.document_id):
            doc_inv_lines.append(
                f"*   **[{d.document_id}]** {d.document_name} ({d.document_type}) "
                f"- Uploaded: {d.uploaded_at}"
            )
        appendices.append(Appendix(
            appendix_id="appendix_a",
            title="Appendix A: Document Inventory",
            content="\n".join(doc_inv_lines)
        ))

        # Appendix B: Expert Assessments Metadata
        asm_lines = ["The following expert assessments were executed:"]
        for a in sorted(graph.assessments.values(), key=lambda x: x.assessment_id):
            asm_lines.append(
                f"*   **[{a.assessment_id}]** {a.expert_name} (Domain: {a.domain}) "
                f"- Version: {a.agent_version} - Confidence: {a.confidence:.2f} - Prompt Version: {a.prompt_version}"
            )
        appendices.append(Appendix(
            appendix_id="appendix_b",
            title="Appendix B: Expert Assessments Registry",
            content="\n".join(asm_lines)
        ))

        # Appendix C: Graph Statistics & Integrity Hash
        stats = graph.graph_stats
        stat_lines = [
            "Evaluation Graph statistics:",
            f"*   Document Count: {stats.document_count}",
            f"*   Evidence Count: {stats.evidence_count}",
            f"*   Claim Count: {stats.claim_count}",
            f"*   Observation Count: {stats.observation_count}",
            f"*   Assessment Count: {stats.assessment_count}",
            f"*   Conflict Count: {stats.conflict_count}",
            f"*   Resolution Count: {stats.resolution_count}",
            f"*   Edge Count: {stats.edge_count}",
            f"*   Resolved Conflicts: {stats.resolved_conflicts}",
            f"*   Unresolved Conflicts: {stats.unresolved_conflicts}",
            "",
            f"**Graph Hash (SHA-256):** `{graph.graph_hash}`"
        ]
        appendices.append(Appendix(
            appendix_id="appendix_c",
            title="Appendix C: Graph Statistics & Integrity Hash",
            content="\n".join(stat_lines)
        ))

        # --- Traceability Map ---
        traceability = {}
        # We trace each ReportSection's supporting nodes
        sections_list = [
            section_executive, section_investment, section_founder, section_product,
            section_trl, section_market, section_competition, section_financial,
            section_ip, section_risk, section_observations, section_risks,
            section_conflicts, section_resolutions, section_missing, section_questions
        ]
        for sec in sections_list:
            sec_trace = {}
            for nid in sec.supporting_nodes:
                node = graph.get_node(nid)
                if node:
                    if node.node_type == NodeType.OBSERVATION:
                        sec_trace[nid] = trace_observation(graph, nid, visited=set())
                    elif node.node_type == NodeType.RISK:
                        sec_trace[nid] = trace_risk(graph, nid, visited=set())
                    elif node.node_type == NodeType.CLAIM:
                        sec_trace[nid] = trace_claim(graph, nid, visited=set())
                    elif node.node_type == NodeType.EVIDENCE:
                        sec_trace[nid] = trace_evidence(graph, nid, visited=set())
                    else:
                        sec_trace[nid] = node.model_dump() if hasattr(node, "model_dump") else node
            traceability[sec.section_id] = sec_trace

        # 3. Compile report
        report_node = DueDiligenceReport(
            node_id=report_id,
            node_type=NodeType.REPORT,
            report_id=report_id,
            generated_at=generated_at,
            graph_version=graph.graph_version,
            executive_summary=section_executive,
            investment_summary=section_investment,
            founder_analysis=section_founder,
            product_analysis=section_product,
            trl_analysis=section_trl,
            market_analysis=section_market,
            competition_analysis=section_competition,
            financial_analysis=section_financial,
            ip_analysis=section_ip,
            risk_analysis=section_risk,
            observations=section_observations,
            risks=section_risks,
            conflicts=section_conflicts,
            resolutions=section_resolutions,
            missing_information=section_missing,
            follow_up_questions=section_questions,
            appendices=appendices,
            traceability=traceability,
            metadata={
                "unresolved_conflicts_count": len(unresolved_conflicts),
                "resolved_conflicts_count": len(resolved_conflicts),
                "suppressed_observations_count": len(suppressed_obs),
                "active_risks_count": len(active_risks)
            }
        )

        graph.report = report_node

        # 4. Populate indexes
        graph.report_indexes = {
            "sections": {s.section_id: s.section_id for s in sections_list},
            "appendices": {a.appendix_id: a.appendix_id for a in appendices}
        }

        # 5. Populate statistics
        graph.report_statistics = {
            "report_id": report_id,
            "section_count": len(sections_list),
            "appendix_count": len(appendices),
            "generated_at": generated_at
        }

        # Update stats
        from app.modules.evaluation.graph.graph_builder import ObservationGraphBuilder
        ObservationGraphBuilder._update_statistics(graph)

        # Re-compute hash
        graph.graph_hash = ObservationGraphBuilder._compute_hash(graph)

        return graph
