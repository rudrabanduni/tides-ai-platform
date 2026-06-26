import time
from datetime import datetime
import uuid
from typing import Optional, Any, List, Dict

from sqlalchemy.orm import Session
from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType, Edge
from app.modules.evaluation.graph.graph_builder import ObservationGraphBuilder
from app.modules.evaluation.committee.committee_models import (
    InvestmentCommitteeDecision, Recommendation, Priority,
    DueDiligenceCategory, DueDiligenceItem,
    CommitteeDecision, CommitteeFinding, CommitteeConcern,
    CommitteeConsensus, CommitteeRecommendation, CommitteeReport
)



class CommitteeDecisionEngine:
    """Deterministic Investment Committee Decision Engine."""

    @staticmethod
    def generate(graph: ObservationGraph, portfolio: Optional[Any] = None) -> ObservationGraph:
        """Generates a deterministic committee decision and links it into the ObservationGraph."""
        t_start = time.perf_counter()
        
        # 1. Fetch dependencies from graph or portfolio argument
        portfolio_entry = getattr(graph, "portfolio_entry", None)
        if portfolio is not None:
            # Look up by startup_id
            sid = graph.startup_id or graph.graph_id
            for entry in getattr(portfolio, "entries", []):
                if entry.startup_id == sid:
                    portfolio_entry = entry
                    break
        
        # 2. Extract metrics
        inv_asm = graph.investment_assessment
        exec_asm = graph.executive_assessment
        
        score = inv_asm.investment_score if inv_asm else 50.0
        confidence = inv_asm.confidence if inv_asm else 0.5
        exec_confidence = exec_asm.confidence if exec_asm else 0.5
        
        # Fallbacks for portfolio entry metrics
        overall_consensus = getattr(portfolio_entry, "overall_consensus", 0.5)
        graph_confidence = getattr(portfolio_entry, "graph_confidence", confidence)
        evidence_strength = getattr(portfolio_entry, "evidence_strength", 0.5)
        active_risk_count = getattr(portfolio_entry, "active_risk_count", len(graph.risks))
        corroborated_count = getattr(portfolio_entry, "corroborated_observation_count", 0)
        disputed_count = getattr(portfolio_entry, "disputed_observation_count", 0)
        portfolio_rank = getattr(portfolio_entry, "rank", 1)
        document_coverage = getattr(portfolio_entry, "document_coverage", 1.0)
        
        # Additional statistics
        total_claims = max(1, graph.graph_stats.claim_count)
        unresolved_conflicts = graph.graph_stats.unresolved_conflicts
        conflict_density = unresolved_conflicts / total_claims
        
        total_obs = max(1, graph.graph_stats.observation_count)
        question_density = len(graph.questions) / total_obs
        
        # 3. Decision Logic for Recommendation
        if score < 40.0 or disputed_count > corroborated_count or (active_risk_count >= 5 and score < 55.0):
            recommendation = Recommendation.REJECT
        elif document_coverage < 0.6 or len(graph.questions) >= 5 or unresolved_conflicts >= 3:
            recommendation = Recommendation.SEEK_MORE_INFORMATION
        elif score < 55.0 or overall_consensus < 0.5:
            recommendation = Recommendation.DEFER
        elif score >= 80.0 and active_risk_count <= 1 and document_coverage >= 0.85 and overall_consensus >= 0.8 and disputed_count == 0:
            recommendation = Recommendation.INCUBATE
        elif score >= 70.0:
            recommendation = Recommendation.INCUBATE_AFTER_DD
        else:
            recommendation = Recommendation.PILOT_FIRST

        # 4. Deterministic Priorities
        if recommendation == Recommendation.INCUBATE:
            inv_prio = Priority.CRITICAL
            inc_prio = Priority.CRITICAL
            grant_prio = Priority.MEDIUM
            pilot_prio = Priority.HIGH
        elif recommendation == Recommendation.INCUBATE_AFTER_DD:
            inv_prio = Priority.HIGH
            inc_prio = Priority.HIGH
            grant_prio = Priority.MEDIUM
            pilot_prio = Priority.HIGH
        elif recommendation == Recommendation.PILOT_FIRST:
            inv_prio = Priority.MEDIUM
            inc_prio = Priority.HIGH
            grant_prio = Priority.HIGH if score >= 60.0 else Priority.MEDIUM
            pilot_prio = Priority.CRITICAL
        elif recommendation == Recommendation.SEEK_MORE_INFORMATION:
            inv_prio = Priority.MEDIUM
            inc_prio = Priority.MEDIUM
            grant_prio = Priority.LOW
            pilot_prio = Priority.MEDIUM
        elif recommendation == Recommendation.DEFER:
            inv_prio = Priority.LOW
            inc_prio = Priority.LOW
            grant_prio = Priority.LOW
            pilot_prio = Priority.LOW
        else:  # REJECT
            inv_prio = Priority.LOW
            inc_prio = Priority.LOW
            grant_prio = Priority.LOW
            pilot_prio = Priority.LOW

        # 5. Deterministic Review Window
        if recommendation == Recommendation.INCUBATE:
            review_window = "1 Month"
        elif recommendation == Recommendation.INCUBATE_AFTER_DD:
            review_window = "2 Months"
        elif recommendation == Recommendation.PILOT_FIRST:
            review_window = "3 Months"
        elif recommendation == Recommendation.SEEK_MORE_INFORMATION:
            review_window = "14 Days"
        elif recommendation == Recommendation.DEFER:
            review_window = "6 Months"
        else:  # REJECT
            review_window = "12 Months"

        # 6. Due Diligence Checklist
        dd_items = []
        
        # Financial DD
        fin_blocking = active_risk_count >= 3 or score < 60.0
        dd_items.append(DueDiligenceItem(
            category=DueDiligenceCategory.FINANCIAL_DD,
            status="PENDING",
            reason="Verify operating cash flows, historical expenditure consistency, and capital runway safety.",
            blocking=fin_blocking,
            documents_required=["Audited Financial Statements", "Recent Tax Returns", "Cap Table Snapshot"]
        ))
        
        # Legal DD
        leg_blocking = unresolved_conflicts > 0 or recommendation == Recommendation.INCUBATE_AFTER_DD
        dd_items.append(DueDiligenceItem(
            category=DueDiligenceCategory.LEGAL_DD,
            status="PENDING",
            reason="Inspect incorporation filings, shareholder agreements, and director resolutions to check liability exposure.",
            blocking=leg_blocking,
            documents_required=["Articles of Incorporation", "Corporate Bylaws", "Shareholder Agreements"]
        ))
        
        # Technical DD
        tech_blocking = score < 70.0 or active_risk_count > 2
        dd_items.append(DueDiligenceItem(
            category=DueDiligenceCategory.TECHNICAL_DD,
            status="PENDING",
            reason="Validate technology architecture validity, codebase health, and external API dependencies.",
            blocking=tech_blocking,
            documents_required=["Architecture Diagram", "API Documentation", "Security Audit Report"]
        ))
        
        # Market DD
        mkt_blocking = score < 65.0 or document_coverage < 0.7
        dd_items.append(DueDiligenceItem(
            category=DueDiligenceCategory.MARKET_DD,
            status="PENDING",
            reason="Verify market size (TAM/SAM) assumptions and analyze documented pilot customer feedback.",
            blocking=mkt_blocking,
            documents_required=["Customer Pipeline List", "Competitor Matrix Analysis", "TAM Model Workbook"]
        ))
        
        # IP DD
        ip_blocking = disputed_count > 0 or "ip" in graph.observations_by_domain
        dd_items.append(DueDiligenceItem(
            category=DueDiligenceCategory.IP_DD,
            status="PENDING",
            reason="Confirm IP ownership agreements and check freedom to operate (FTO) parameters.",
            blocking=ip_blocking,
            documents_required=["Patent Filing Receipts", "IP Assignment Agreements", "FTO Analysis Report"]
        ))
        
        # Founder DD
        fnd_blocking = overall_consensus < 0.7 or "founder" in graph.risks_by_category
        dd_items.append(DueDiligenceItem(
            category=DueDiligenceCategory.FOUNDER_DD,
            status="PENDING",
            reason="Audit management track record, verify employment agreements, and conduct background checks.",
            blocking=fnd_blocking,
            documents_required=["Executive References", "Background Check Consent", "Founder Employment Contracts"]
        ))

        # 7. Aggregate Required Documents
        required_docs = []
        for item in dd_items:
            for doc in item.documents_required:
                if doc not in required_docs:
                    required_docs.append(doc)

        # 8. Follow-up Questions
        follow_ups = []
        if graph.questions:
            for qnode in graph.questions.values():
                follow_ups.append(qnode.question)
        else:
            # Fallback defaults
            if recommendation in (Recommendation.INCUBATE, Recommendation.INCUBATE_AFTER_DD):
                follow_ups.append("What are the key milestones for the next 6 months of incubation?")
                follow_ups.append("Can you provide the final IP assignment agreements for all core team members?")
            elif recommendation == Recommendation.PILOT_FIRST:
                follow_ups.append("What are the success criteria and timelines for the proposed pilot?")
            else:
                follow_ups.append("What steps are being taken to address the highlighted technical and market risks?")

        # 9. Committee Notes
        comm_notes = (
            f"Decision compiled for {graph.startup_name or 'Startup'}. "
            f"Investment priority is set to {inv_prio.value} based on the overall score of {score:.1f}. "
            f"Review window is {review_window}."
        )

        # 10. Decision Reasoning
        reasoning = (
            f"Recommendation set to {recommendation.value} with confidence {min(confidence, exec_confidence):.2f}. "
            f"This is derived from an investment score of {score:.1f}, consensus rating of {overall_consensus:.2f}, "
            f"and active risk count of {active_risk_count}. Evidence strength is evaluated at {evidence_strength:.2f}."
        )

        # 11. Blocking Risks
        blocking_risks = []
        for rnode in graph.risks.values():
            if rnode.confidence >= 0.6:
                blocking_risks.append(f"{rnode.category.upper()}: {rnode.description}")
        if not blocking_risks:
            # Fallback if no high confidence risk is listed
            blocking_risks = [r.description for r in graph.risks.values()][:3]

        # 12. Create Model
        decision_id = f"DEC-{graph.startup_id or graph.graph_id}"
        inv_id = inv_asm.assessment_id if inv_asm else "N/A"
        exec_id = exec_asm.assessment_id if exec_asm else "N/A"
        generated_at = datetime.utcnow().isoformat() + "Z"
        port_hash = getattr(portfolio, "portfolio_hash", getattr(portfolio_entry, "portfolio_hash", "N/A"))

        decision = InvestmentCommitteeDecision(
            node_id=decision_id,
            node_type=NodeType.DECISION,
            decision_id=decision_id,
            startup_id=graph.startup_id,
            startup_name=graph.startup_name,
            portfolio_rank=portfolio_rank,
            recommendation=recommendation,
            decision_confidence=round(min(confidence, exec_confidence), 4),
            decision_reasoning=reasoning,
            investment_priority=inv_prio,
            incubation_priority=inc_prio,
            grant_priority=grant_prio,
            pilot_priority=pilot_prio,
            review_window=review_window,
            committee_notes=comm_notes,
            blocking_risks=blocking_risks,
            required_due_diligence=dd_items,
            required_documents=required_docs,
            follow_up_questions=follow_ups,
            graph_hash="",  # will be computed below
            portfolio_hash=port_hash,
            executive_summary_id=exec_id,
            investment_assessment_id=inv_id,
            generated_at=generated_at,
            engine_version="1.0.0"
        )
        
        # 13. Update Graph
        graph.committee_decision = decision
        
        # 14. Establish Lineage Traceability Edges
        # Decision --REFERENCES--> InvestmentAssessment
        if inv_asm:
            edge_inv = Edge(
                source_id=decision_id,
                source_type=NodeType.DECISION,
                target_id=inv_asm.node_id,
                target_type=NodeType.INVESTMENT,
                relationship="REFERENCES"
            )
            graph.edges.append(edge_inv)
            graph.out_edges.setdefault(decision_id, []).append(edge_inv)
            graph.in_edges.setdefault(inv_asm.node_id, []).append(edge_inv)
            
        # Decision --REFERENCES--> ExecutiveAssessment
        if exec_asm:
            edge_exec = Edge(
                source_id=decision_id,
                source_type=NodeType.DECISION,
                target_id=exec_asm.node_id,
                target_type=NodeType.EXECUTIVE,
                relationship="REFERENCES"
            )
            graph.edges.append(edge_exec)
            graph.out_edges.setdefault(decision_id, []).append(edge_exec)
            graph.in_edges.setdefault(exec_asm.node_id, []).append(edge_exec)

        # Traceability: Link to key observations or active risks
        for obs_id in list(graph.observations.keys())[:5]:
            edge_obs = Edge(
                source_id=decision_id,
                source_type=NodeType.DECISION,
                target_id=obs_id,
                target_type=NodeType.OBSERVATION,
                relationship="REFERENCES"
            )
            graph.edges.append(edge_obs)
            graph.out_edges.setdefault(decision_id, []).append(edge_obs)
            graph.in_edges.setdefault(obs_id, []).append(edge_obs)

        # 15. Update statistics first so that graph_stats reflect all node/edge counts (including the new lineage edges)
        ObservationGraphBuilder._update_statistics(graph)

        # Temporarily detach committee_decision to calculate clean graph hash (which includes the lineage edges!)
        graph.committee_decision = None
        clean_graph_hash = ObservationGraphBuilder._compute_hash(graph)
        
        # Set clean hash and re-attach
        decision.graph_hash = clean_graph_hash
        graph.committee_decision = decision

        # 16. Re-compute Hashing (no need to update stats again as they are already correct)
        graph.graph_hash = ObservationGraphBuilder._compute_hash(graph)
        
        return graph

    @staticmethod
    def generate_committee_report(
        graph: ObservationGraph,
        workflow_reference: str,
        metadata: Optional[Dict[str, Any]] = None,
        db: Optional[Session] = None
    ) -> CommitteeReport:
        return generate_committee_report(graph, workflow_reference, metadata, db)

    @staticmethod
    def collect_assessments(graph: ObservationGraph) -> List[Any]:
        return collect_assessments(graph)

    @staticmethod
    def merge_observations(graph: ObservationGraph) -> List[Dict[str, Any]]:
        return merge_observations(graph)

    @staticmethod
    def resolve_conflicts(graph: ObservationGraph) -> List[Dict[str, Any]]:
        return resolve_conflicts(graph)

    @staticmethod
    def aggregate_findings(graph: ObservationGraph) -> List[CommitteeFinding]:
        return aggregate_findings(graph)

    @staticmethod
    def aggregate_risks(graph: ObservationGraph) -> List[CommitteeConcern]:
        return aggregate_risks(graph)

    @staticmethod
    def aggregate_questions(graph: ObservationGraph) -> List[str]:
        return aggregate_questions(graph)

    @staticmethod
    def build_consensus(graph: ObservationGraph, findings: List[CommitteeFinding]) -> CommitteeConsensus:
        return build_consensus(graph, findings)

    @staticmethod
    def generate_recommendations(
        graph: ObservationGraph,
        consensus: CommitteeConsensus,
        concerns: List[CommitteeConcern],
        overall_confidence: float
    ) -> CommitteeRecommendation:
        return generate_recommendations(graph, consensus, concerns, overall_confidence)

    @staticmethod
    def generate_summary(
        graph: ObservationGraph,
        recommendation: CommitteeRecommendation,
        overall_confidence: float
    ) -> str:
        return generate_summary(graph, recommendation, overall_confidence)

    @staticmethod
    def calculate_overall_confidence(graph: ObservationGraph) -> float:
        return calculate_overall_confidence(graph)

    @staticmethod
    def persist_committee_report(graph: ObservationGraph, report: CommitteeReport) -> None:
        persist_committee_report(graph, report)


def generate_committee_report(
    graph: ObservationGraph,
    workflow_reference: str,
    metadata: Optional[Dict[str, Any]] = None,
    db: Optional[Session] = None
) -> CommitteeReport:
    t_start = time.perf_counter()
    startup_id = graph.startup_id or graph.graph_id
    
    # Publish CommitteeStarted event
    from app.modules.evaluation.committee.committee_events import (
        publish_committee_started,
        publish_committee_completed,
        publish_committee_failed,
        publish_committee_finding_created,
        publish_committee_concern_created,
        publish_committee_consensus_built,
        publish_committee_recommendation_generated
    )
    publish_committee_started(startup_id)
    
    try:
        meta = metadata or {}
        
        # 1. Collect Assessments
        assessments = collect_assessments(graph)
        
        # 2. Aggregate Findings (with corroborations)
        findings = aggregate_findings(graph)
        report_id = f"REP-COMM-{startup_id}"
        for f in findings:
            publish_committee_finding_created(report_id, f.finding_id)
            
        # 3. Aggregate Risks/Concerns
        concerns = aggregate_risks(graph)
        for c in concerns:
            publish_committee_concern_created(report_id, c.concern_id)
            
        # 4. Build Consensus
        consensus = build_consensus(graph, findings)
        publish_committee_consensus_built(report_id, consensus.agreement_level)
        
        # 5. Calculate Overall Confidence
        overall_confidence = calculate_overall_confidence(graph)
        
        # 6. Generate Recommendations
        recommendation = generate_recommendations(graph, consensus, concerns, overall_confidence)
        publish_committee_recommendation_generated(report_id, recommendation.recommendation)
        
        # 7. Generate Summary & Reasoning
        summary = generate_summary(graph, recommendation, overall_confidence)
        
        # Compute clean graph hash
        # We can temporarily detach committee_decision/committee_report to compute graph hash
        orig_dec = graph.committee_decision
        orig_rep = getattr(graph, "committee_report", None)
        graph.committee_decision = None
        if hasattr(graph, "committee_report"):
            graph.committee_report = None
        clean_graph_hash = ObservationGraphBuilder._compute_hash(graph)
        graph.committee_decision = orig_dec
        if hasattr(graph, "committee_report"):
            graph.committee_report = orig_rep
            
        # Create CommitteeDecision model
        decision = CommitteeDecision(
            decision_id=f"DEC-{startup_id}",
            startup_id=startup_id,
            startup_name=graph.startup_name or "Unknown Startup",
            created_at=datetime.utcnow(),
            committee_version="1.0.0",
            overall_confidence=round(overall_confidence, 4),
            overall_reasoning=summary,
            executive_summary=summary,
            graph_hash=clean_graph_hash,
            workflow_reference=workflow_reference,
            metadata=meta
        )
        
        # Setup Traceability dictionary
        traceability = {
            "findings_count": len(findings),
            "concerns_count": len(concerns),
            "unresolved_conflicts_count": len(consensus.unresolved_conflicts),
            "dependencies_count": len(consensus.cross_domain_dependencies),
            "generation_time_ms": round((time.perf_counter() - t_start) * 1000, 2)
        }
        
        report = CommitteeReport(
            decision=decision,
            findings=findings,
            concerns=concerns,
            consensus=consensus,
            recommendations=recommendation,
            traceability=traceability
        )
        
        # Persist report
        persist_committee_report(graph, report)
        
        # Create Audit Entry
        from app.security.audit import SecurityAuditService
        actor = meta.get("user") or meta.get("actor") or "system"
        req_id = meta.get("request_id") or "N/A"
        
        audit_service = SecurityAuditService(db)
        audit_service.log(
            actor=actor,
            action="committee.report_generated",
            resource=f"/committee/report/{report_id}",
            status="success",
            details={
                "startup": graph.startup_name or "Unknown",
                "graph_hash": clean_graph_hash,
                "workflow_id": workflow_reference,
                "generated_report_id": decision.decision_id,
                "request_id": req_id
            }
        )
        
        publish_committee_completed(startup_id, report_id)
        return report
        
    except Exception as e:
        publish_committee_failed(startup_id, str(e))
        raise e


def collect_assessments(graph: ObservationGraph) -> List[Any]:
    assessments = list(graph.assessments.values())
    if graph.executive_assessment:
        assessments.append(graph.executive_assessment)
    if graph.investment_assessment:
        assessments.append(graph.investment_assessment)
    return assessments


def merge_observations(graph: ObservationGraph) -> List[Dict[str, Any]]:
    from app.modules.evaluation.committee.committee_rules import Jaccard_similarity
    
    observations = list(graph.observations.values())
    groups = []
    visited = set()
    
    for i, o1 in enumerate(observations):
        if o1.observation_id in visited:
            continue
            
        group = [o1]
        visited.add(o1.observation_id)
        
        for o2 in observations[i+1:]:
            if o2.observation_id in visited:
                continue
            
            similar = False
            # Check edge relationship in graph edges
            for edge in graph.edges:
                if (edge.source_id == o1.observation_id and edge.target_id == o2.observation_id) or \
                   (edge.source_id == o2.observation_id and edge.target_id == o1.observation_id):
                    similar = True
                    break
            
            if not similar:
                similar = Jaccard_similarity(o1.observation, o2.observation) >= 0.35
                
            if similar:
                group.append(o2)
                visited.add(o2.observation_id)
                
        groups.append(group)
        
    merged = []
    for idx, group in enumerate(groups):
        domains = sorted(list(set(o.domain for o in group)))
        best_obs = max(group, key=lambda o: o.confidence)
        
        title = f"Corroborated Finding on {', '.join(domains).title()} - {best_obs.observation}" if len(domains) > 1 else f"{best_obs.domain.title()} Finding - {best_obs.observation}"

        desc = best_obs.observation
        if len(group) > 1:
            desc = " | ".join(o.observation for o in group)
            
        claims = set()
        evidence = set()
        for obs in group:
            for edge in graph.out_edges.get(obs.observation_id, []):
                if edge.target_type == NodeType.CLAIM:
                    claims.add(edge.target_id)
                elif edge.target_type == NodeType.EVIDENCE:
                    evidence.add(edge.target_id)
            for edge in graph.in_edges.get(obs.observation_id, []):
                if edge.source_type == NodeType.CLAIM:
                    claims.add(edge.source_id)
                elif edge.source_type == NodeType.EVIDENCE:
                    evidence.add(edge.source_id)
                    
        merged.append({
            "finding_id": f"FIND-{best_obs.domain.upper()}-{idx:03d}",
            "title": title,
            "description": desc,
            "domains": domains,
            "supporting_observations": [o.observation_id for o in group],
            "supporting_claims": sorted(list(claims)),
            "supporting_evidence": sorted(list(evidence)),
            "confidence": round(sum(o.confidence for o in group) / len(group), 4)
        })
    return merged


def resolve_conflicts(graph: ObservationGraph) -> List[Dict[str, Any]]:
    contradictions = []
    for conflict_id, conflict in graph.conflicts.items():
        affected = set()
        for edge in graph.edges:
            if edge.source_id == conflict_id or edge.target_id == conflict_id:
                other_id = edge.target_id if edge.source_id == conflict_id else edge.source_id
                if other_id in graph.observations:
                    affected.add(graph.observations[other_id].domain)
                    
        contradictions.append({
            "conflict_id": conflict_id,
            "description": conflict.description,
            "affected_domains": sorted(list(affected)) if affected else ["unknown"],
            "severity": "CRITICAL" if conflict.confidence >= 0.7 else "MEDIUM",
            "confidence": conflict.confidence,
            "linked_risks": [],
            "linked_questions": []
        })
    return contradictions


def aggregate_findings(graph: ObservationGraph) -> List[CommitteeFinding]:
    merged = merge_observations(graph)
    return [CommitteeFinding(**f) for f in merged]


def aggregate_risks(graph: ObservationGraph) -> List[CommitteeConcern]:
    from app.modules.evaluation.committee.committee_rules import merge_risks_logic
    
    merged = merge_risks_logic(list(graph.risks.values()), graph.out_edges)
    concerns = []
    for r in merged:
        linked_questions = []
        for q_id, q_node in graph.questions.items():
            is_linked = False
            for edge in graph.out_edges.get(q_id, []):
                if edge.target_id == r["risk_id"]:
                    is_linked = True
                    break
            if is_linked:
                linked_questions.append(q_id)
                
        severity = "MEDIUM"
        for risk_node in graph.risks.values():
            if risk_node.risk_id == r["risk_id"]:
                severity = getattr(risk_node, "severity", "MEDIUM")
                break
                
        concerns.append(CommitteeConcern(
            concern_id=f"CONCERN-{r['risk_id']}",
            description=r["description"],
            affected_domains=[r["category"]],
            severity=severity,
            confidence=r["confidence"],
            linked_risks=[r["risk_id"]],
            linked_questions=linked_questions
        ))
    return concerns


def aggregate_questions(graph: ObservationGraph) -> List[str]:
    return [q.question for q in graph.questions.values()]


def build_consensus(graph: ObservationGraph, findings: List[CommitteeFinding]) -> CommitteeConsensus:
    from app.modules.evaluation.committee.committee_rules import detect_dependencies
    
    contradictions = resolve_conflicts(graph)
    unresolved_conflicts = [c.conflict_id for c in graph.conflicts.values() if c.conflict_id not in graph.resolutions]
    
    corroborated = [
        {
            "finding_id": f.finding_id,
            "title": f.title,
            "domains": f.domains,
            "confidence": f.confidence
        }
        for f in findings if len(f.domains) > 1
    ]
    
    dependencies = detect_dependencies(graph)
    
    total_findings = len(findings)
    unresolved_count = len(unresolved_conflicts)
    contradictions_count = len(contradictions)
    
    agreement_level = 1.0
    if total_findings > 0:
        agreement_level = max(0.0, 1.0 - (contradictions_count * 0.15) - (unresolved_count * 0.1))
        
    return CommitteeConsensus(
        agreement_level=round(agreement_level, 4),
        corroborated_findings=corroborated,
        contradictions=contradictions,
        unresolved_conflicts=unresolved_conflicts,
        cross_domain_dependencies=dependencies
    )


def generate_recommendations(
    graph: ObservationGraph,
    consensus: CommitteeConsensus,
    concerns: List[CommitteeConcern],
    overall_confidence: float
) -> CommitteeRecommendation:
    from app.modules.evaluation.committee.committee_rules import classify_decision
    
    score = 50.0
    if graph.investment_assessment and hasattr(graph.investment_assessment, "investment_score"):
        score = graph.investment_assessment.investment_score
        
    category, justification = classify_decision(
        investment_score=score,
        active_risk_count=len(concerns),
        unresolved_conflicts=len(consensus.unresolved_conflicts),
        overall_confidence=overall_confidence
    )
    
    if category == "Ready for Incubation":
        priority = "CRITICAL"
    elif category == "Promising but Requires Clarification":
        priority = "HIGH"
    elif category == "Requires Significant Validation":
        priority = "MEDIUM"
    else:
        priority = "LOW"
        
    required_documents = []
    for concern in concerns:
        for domain in concern.affected_domains:
            if domain == "financial":
                required_documents.extend(["Audited Financials", "Cap Table"])
            elif domain == "ip":
                required_documents.extend(["Patent certificates", "IP assignment agreement"])
            elif domain == "trl":
                required_documents.extend(["Technical documentation"])
                
    required_documents = sorted(list(set(required_documents)))
    if not required_documents:
        required_documents = ["Pitch Deck", "Business Plan"]
        
    required_followups = [q.question for q in graph.questions.values()]
    if not required_followups:
        required_followups = ["Clarify next milestones."]
        
    return CommitteeRecommendation(
        recommendation_id=f"REC-{graph.startup_id or graph.graph_id}",
        recommendation=category,
        justification=justification,
        required_followups=required_followups,
        required_documents=required_documents,
        priority=priority
    )


def generate_summary(graph: ObservationGraph, recommendation: CommitteeRecommendation, overall_confidence: float) -> str:
    return (
        f"Summary for {graph.startup_name or 'Startup'}: The committee has analyzed the startup across domains. "
        f"The recommendation is '{recommendation.recommendation}' (Priority: {recommendation.priority}). "
        f"Verdict Justification: {recommendation.justification} "
        f"Overall evaluation confidence is evaluated at {overall_confidence:.2f}."
    )


def calculate_overall_confidence(graph: ObservationGraph) -> float:
    confidences = []
    for asm in graph.assessments.values():
        confidences.append(asm.confidence)
    if graph.executive_assessment and hasattr(graph.executive_assessment, "confidence"):
        confidences.append(graph.executive_assessment.confidence)
    if graph.investment_assessment and hasattr(graph.investment_assessment, "confidence"):
        confidences.append(graph.investment_assessment.confidence)
        
    return sum(confidences) / len(confidences) if confidences else 0.5


def persist_committee_report(graph: ObservationGraph, report: CommitteeReport) -> None:
    from app.modules.evaluation.committee.committee_queries import register_report
    register_report(report)
    graph.committee_report = report

