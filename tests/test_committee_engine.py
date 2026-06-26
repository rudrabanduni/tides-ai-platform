import time
import json
import pytest
from datetime import datetime
from typing import List, Optional

from app.modules.evaluation.graph import (
    NodeType, DocumentNode, EvidenceNode, ClaimNode,
    ObservationNode, AssessmentNode, ConflictNode, RiskNode,
    QuestionNode, Edge, ObservationGraph, ObservationGraphBuilder
)
from app.modules.evaluation.investment.investment_models import InvestmentAssessment, InvestmentRecommendation
from app.modules.evaluation.executive.executive_models import ExecutiveAssessment, ExecutiveSummary
from app.modules.evaluation.portfolio.portfolio_models import PortfolioEntry
from app.modules.evaluation.committee import (
    InvestmentCommitteeDecision, Recommendation, Priority, DueDiligenceCategory,
    CommitteeDecisionEngine, CommitteeValidator, CommitteeSerializer,
    get_ready_for_incubation, get_high_priority, get_pending_dd,
    get_deferred, get_rejected, get_by_startup, statistics,
    committee_dashboard
)


# --- Mock Helper to build self-contained graphs ---

@pytest.fixture(autouse=True)
def mock_datetime_utcnow(monkeypatch):
    class MockDatetime:
        @classmethod
        def utcnow(cls):
            return datetime(2026, 6, 25, 12, 0, 0)
    monkeypatch.setattr("app.modules.evaluation.committee.committee_engine.datetime", MockDatetime)


def create_mock_graph(
    startup_id: str,
    name: str,
    category: str,
    investment_score: float,
    confidence: float,
    overall_consensus: float = 0.8,
    active_risks_count: int = 1,
    evidence_count: int = 5,
    executive_confidence: float = 0.9,
    evidence_strength: float = 0.9,
    question_count: int = 2,
    unresolved_conflicts: int = 0
) -> ObservationGraph:
    graph = ObservationGraph()
    graph.startup_id = startup_id
    graph.graph_id = startup_id
    graph.startup_name = name
    graph.category = category
    graph.created_at = "2026-06-25T12:00:00Z"
    
    static_time = datetime(2026, 6, 25, 12, 0, 0)
    
    # 1. Documents
    doc = DocumentNode(
        node_id="doc-1", node_type=NodeType.DOCUMENT,
        document_id="doc-1", document_name="Pitch Deck",
        document_type="PDF", uploaded_at=static_time
    )
    graph.documents["doc-1"] = doc
    
    # 2. Evidence
    for i in range(evidence_count):
        ev_id = f"ev-{i}"
        ev = EvidenceNode(
            node_id=ev_id, node_type=NodeType.EVIDENCE,
            evidence_id=ev_id, excerpt="Excerpt",
            location="p.1", confidence=evidence_strength
        )
        graph.evidence[ev_id] = ev
        graph.edges.append(Edge(source_id=ev_id, source_type=NodeType.EVIDENCE, target_id="doc-1", target_type=NodeType.DOCUMENT, relationship="DERIVED_FROM"))
        
    # 3. Claims
    claim = ClaimNode(node_id="claim-1", node_type=NodeType.CLAIM, claim_id="claim-1", claim_text="Detail")
    graph.claims["claim-1"] = claim
    
    # 4. Observations
    total_obs = 10
    corroborated_target = int(total_obs * overall_consensus)
    for i in range(total_obs):
        obs_id = f"obs-{i}"
        status = "corroborated" if i < corroborated_target else "independent"
        obs = ObservationNode(
            node_id=obs_id, node_type=NodeType.OBSERVATION,
            observation_id=obs_id, domain="product",
            observation=f"Obs {i}", confidence=confidence,
            consensus_status=status
        )
        graph.observations[obs_id] = obs
        graph.edges.append(Edge(source_id=obs_id, source_type=NodeType.OBSERVATION, target_id="claim-1", target_type=NodeType.CLAIM, relationship="SUPPORTED_BY"))
        
    # 5. Risks
    for i in range(active_risks_count):
        r_id = f"risk-{i}"
        risk = RiskNode(
            node_id=r_id, node_type=NodeType.RISK,
            risk_id=r_id, category="technical",
            description=f"Risk {i}", confidence=0.7, reasoning="Reason"
        )
        graph.risks[r_id] = risk
        
    # 6. Questions
    for i in range(question_count):
        q_id = f"qst-{i}"
        qst = QuestionNode(
            node_id=q_id, node_type=NodeType.QUESTION,
            question_id=q_id, question=f"Follow up {i}?", purpose="Audit"
        )
        graph.questions[q_id] = qst
        
    # 7. Conflicts
    for i in range(unresolved_conflicts):
        conf_id = f"conf-{i}"
        conflict = ConflictNode(
            node_id=conf_id, node_type=NodeType.CONFLICT,
            conflict_id=conf_id, description=f"Conflict {i}",
            conflict_type="FACTUAL", confidence=0.8, created_at=static_time
        )
        graph.conflicts[conf_id] = conflict
        
    # 8. Executive Assessment
    exec_summary = ExecutiveSummary(overview="Exec Overview", strengths=[], weaknesses=[], opportunities=[], threats=[], missing_information=[])
    exec_asm = ExecutiveAssessment(
        node_id="exec-assessment", node_type=NodeType.EXECUTIVE,
        assessment_id="exec-assessment", generated_at=static_time.isoformat() + "Z",
        summary=exec_summary, confidence=executive_confidence
    )
    graph.executive_assessment = exec_asm
    
    # 9. Investment Assessment
    if investment_score < 40:
        rec = InvestmentRecommendation.DO_NOT_INVEST
    elif investment_score < 55:
        rec = InvestmentRecommendation.REVIEW
    elif investment_score < 70:
        rec = InvestmentRecommendation.WATCHLIST
    elif investment_score < 85:
        rec = InvestmentRecommendation.INVEST
    else:
        rec = InvestmentRecommendation.STRONG_INVEST
        
    metrics = {
        "overall_consensus": overall_consensus,
        "evidence_strength": evidence_strength,
        "document_coverage": 1.0,
        "graph_confidence": confidence
    }
    
    inv = InvestmentAssessment(
        node_id="inv-assessment", node_type=NodeType.INVESTMENT,
        assessment_id="inv-assessment", generated_at=static_time.isoformat() + "Z",
        recommendation=rec, confidence=confidence,
        investment_score=investment_score, readiness_score=80.0,
        risk_score=40.0, technology_score=75.0, market_score=75.0,
        founder_score=75.0, financial_score=75.0, competition_score=75.0,
        ip_score=75.0, executive_summary="Summary", strengths=[], weaknesses=[],
        major_risks=[], investment_rationale="Rationale", metadata={"metrics": metrics}
    )
    graph.investment_assessment = inv
    graph.investment_statistics = {
        "active_risks_count": active_risks_count,
        "overall_consensus": overall_consensus
    }
    
    # Setup portfolio_entry mock
    port_entry = PortfolioEntry(
        startup_id=startup_id,
        startup_name=name,
        category=category,
        rank=1,
        ranking_reason="Top performer",
        investment_assessment_id="inv-assessment",
        executive_summary_id="exec-assessment",
        overall_consensus=overall_consensus,
        graph_confidence=confidence,
        evidence_strength=evidence_strength,
        document_coverage=1.0,
        active_risk_count=active_risks_count,
        corroborated_observation_count=corroborated_target,
        disputed_observation_count=0,
        created_at=graph.created_at,
        investment_score=investment_score,
        recommendation=rec.value,
        confidence=confidence,
        percentile=100.0,
        strengths=[],
        risks=[],
        executive_summary="Summary",
        graph_hash="clean_hash"
    )
    object.__setattr__(port_entry, "portfolio_hash", "mock_portfolio_hash")
    graph.portfolio_entry = port_entry
    
    ObservationGraphBuilder._update_statistics(graph)
    graph.graph_hash = ObservationGraphBuilder._compute_hash(graph)
    
    # Set clean graph_hash on portfolio_entry
    port_entry.graph_hash = graph.graph_hash
    
    return graph


# --- Unit Tests ---

def test_committee_decision_build():
    g = create_mock_graph("S-1", "Startup One", "SaaS", 85.5, 0.9, overall_consensus=0.85, active_risks_count=1)
    
    # Generate decision
    graph_out = CommitteeDecisionEngine.generate(g)
    
    decision = graph_out.committee_decision
    assert decision is not None
    assert decision.node_type == NodeType.DECISION
    assert decision.decision_id == "DEC-S-1"
    assert decision.startup_name == "Startup One"
    assert decision.recommendation == Recommendation.INCUBATE
    assert decision.investment_priority == Priority.CRITICAL
    assert decision.incubation_priority == Priority.CRITICAL
    assert len(decision.required_documents) > 0
    assert len(decision.required_due_diligence) == 6
    assert decision.executive_summary_id == "exec-assessment"
    assert decision.investment_assessment_id == "inv-assessment"


def test_recommendation_logic():
    # Test cases mapping inputs to expected recommendations
    
    # 1. Reject cases (score < 40)
    g_rej = create_mock_graph("S-Rej", "Startup Rej", "SaaS", 35.0, 0.9)
    g_rej = CommitteeDecisionEngine.generate(g_rej)
    assert g_rej.committee_decision.recommendation == Recommendation.REJECT
    assert g_rej.committee_decision.investment_priority == Priority.LOW
    assert g_rej.committee_decision.incubation_priority == Priority.LOW
    
    # 2. Seek More Information (question_count >= 5)
    g_seek = create_mock_graph("S-Seek", "Startup Seek", "SaaS", 75.0, 0.9, question_count=5)
    g_seek = CommitteeDecisionEngine.generate(g_seek)
    assert g_seek.committee_decision.recommendation == Recommendation.SEEK_MORE_INFORMATION
    assert g_seek.committee_decision.review_window == "14 Days"
    
    # 3. Defer cases (score < 55)
    g_def = create_mock_graph("S-Def", "Startup Def", "SaaS", 50.0, 0.9)
    g_def = CommitteeDecisionEngine.generate(g_def)
    assert g_def.committee_decision.recommendation == Recommendation.DEFER
    assert g_def.committee_decision.review_window == "6 Months"
    
    # 4. Incubate (score >= 80, consensus >= 0.8, risks <= 1)
    g_inc = create_mock_graph("S-Inc", "Startup Inc", "SaaS", 85.0, 0.9, overall_consensus=0.9, active_risks_count=1)
    g_inc = CommitteeDecisionEngine.generate(g_inc)
    assert g_inc.committee_decision.recommendation == Recommendation.INCUBATE
    
    # 5. Incubate After DD (score >= 70 but not matching INCUBATE, e.g. active_risks_count=3)
    g_dd = create_mock_graph("S-DD", "Startup DD", "SaaS", 78.0, 0.9, overall_consensus=0.9, active_risks_count=3)
    g_dd = CommitteeDecisionEngine.generate(g_dd)
    assert g_dd.committee_decision.recommendation == Recommendation.INCUBATE_AFTER_DD
    
    # 6. Pilot First (score 55-70)
    g_pilot = create_mock_graph("S-Pilot", "Startup Pilot", "SaaS", 65.0, 0.9)
    g_pilot = CommitteeDecisionEngine.generate(g_pilot)
    assert g_pilot.committee_decision.recommendation == Recommendation.PILOT_FIRST


def test_validation_rules():
    g = create_mock_graph("S-1", "Startup One", "SaaS", 82.0, 0.9)
    g = CommitteeDecisionEngine.generate(g)
    
    # Validation success
    errors = CommitteeValidator.validate(g)
    assert len(errors) == 0, f"Validator errors: {errors}"
    
    # 1. Induce confidence out of bounds
    g.committee_decision.decision_confidence = 1.8
    errors2 = CommitteeValidator.validate(g)
    assert any("confidence" in e and "outside" in e for e in errors2)
    
    # Reset
    g.committee_decision.decision_confidence = 0.9
    
    # 2. Induce reasoning empty
    g.committee_decision.decision_reasoning = "   "
    errors3 = CommitteeValidator.validate(g)
    assert any("reasoning" in e and "empty" in e for e in errors3)


def test_broken_references():
    g = create_mock_graph("S-1", "Startup One", "SaaS", 82.0, 0.9)
    g = CommitteeDecisionEngine.generate(g)
    
    # Induce broken investment reference
    g.committee_decision.investment_assessment_id = "BROKEN-ID"
    errors = CommitteeValidator.validate(g)
    assert any("Investment assessment ID mismatch" in e for e in errors)


def test_serialization():
    g = create_mock_graph("S-1", "Startup One", "SaaS", 85.0, 0.9)
    g = CommitteeDecisionEngine.generate(g)
    
    dec = g.committee_decision
    
    # JSON round-trip
    json_str = CommitteeSerializer.to_json(dec)
    rebuilt = CommitteeSerializer.from_json(json_str)
    assert rebuilt.decision_id == dec.decision_id
    assert rebuilt.recommendation == dec.recommendation
    assert rebuilt.graph_hash == dec.graph_hash
    
    # CSV export
    csv_str = CommitteeSerializer.to_csv([dec])
    assert "decision_id,startup_id,startup_name" in csv_str
    assert dec.decision_id in csv_str
    
    # Excel export
    xls_bytes = CommitteeSerializer.to_excel([dec])
    assert isinstance(xls_bytes, bytes)
    assert len(xls_bytes) > 0
    
    # Dashboard export
    dash_json = CommitteeSerializer.to_dashboard_json([dec])
    dash_data = json.loads(dash_json)
    assert dash_data["summary"]["total_decisions"] == 1
    assert len(dash_data["top_startups"]) == 1
    
    # Markdown export
    md_str = CommitteeSerializer.to_markdown(dec)
    assert "# Investment Committee Decision:" in md_str
    assert dec.decision_id in md_str
    assert dec.startup_name in md_str


def test_queries_and_statistics():
    g1 = create_mock_graph("S-1", "Startup One", "SaaS", 85.0, 0.9)
    g1 = CommitteeDecisionEngine.generate(g1)
    
    g2 = create_mock_graph("S-2", "Startup Two", "BioTech", 62.0, 0.8)
    g2 = CommitteeDecisionEngine.generate(g2)
    
    g3 = create_mock_graph("S-3", "Startup Three", "CleanTech", 35.0, 0.7)
    g3 = CommitteeDecisionEngine.generate(g3)
    
    decisions = [g1.committee_decision, g2.committee_decision, g3.committee_decision]
    
    # get_ready_for_incubation
    ready = get_ready_for_incubation(decisions)
    assert len(ready) == 1
    assert ready[0].startup_id == "S-1"
    
    # get_high_priority
    high_prio = get_high_priority(decisions)
    assert len(high_prio) == 1
    assert high_prio[0].startup_id == "S-1"
    
    # get_deferred
    deferred = get_deferred(decisions)
    assert len(deferred) == 0  # score < 40 triggers REJECT first
    
    # get_rejected
    rejected = get_rejected(decisions)
    assert len(rejected) == 1
    assert rejected[0].startup_id == "S-3"
    
    # get_by_startup
    s2_dec = get_by_startup(decisions, "S-2")
    assert s2_dec is not None
    assert s2_dec.recommendation == Recommendation.PILOT_FIRST
    
    # statistics
    stats = statistics(decisions)
    assert stats["total_decisions"] == 3
    assert stats["ready_for_incubation"] == 1
    assert stats["recommendation_distribution"]["INCUBATE"] == 1
    assert stats["recommendation_distribution"]["REJECT"] == 1


def test_determinism_and_shuffle():
    # Deterministic output verification
    g1 = create_mock_graph("S-1", "Startup One", "SaaS", 82.0, 0.9)
    g1_copy = create_mock_graph("S-1", "Startup One", "SaaS", 82.0, 0.9)
    
    graph_out1 = CommitteeDecisionEngine.generate(g1)
    graph_out2 = CommitteeDecisionEngine.generate(g1_copy)
    
    assert graph_out1.committee_decision.recommendation == graph_out2.committee_decision.recommendation
    assert graph_out1.committee_decision.graph_hash == graph_out2.committee_decision.graph_hash
    assert graph_out1.graph_hash == graph_out2.graph_hash


def test_hash_propagation():
    g = create_mock_graph("S-1", "Startup One", "SaaS", 82.0, 0.9)
    orig_hash = g.graph_hash
    
    g = CommitteeDecisionEngine.generate(g)
    
    # Generating the decision must update the graph hash
    assert g.committee_decision is not None
    assert g.graph_hash != orig_hash
    
    # Decision's internal graph_hash must equal the clean graph hash
    orig_dec = g.committee_decision
    g.committee_decision = None
    clean_hash = ObservationGraphBuilder._compute_hash(g)
    g.committee_decision = orig_dec
    
    assert g.committee_decision.graph_hash == clean_hash


def test_large_dataset_performance():
    # Generate 1000 startup graphs to benchmark limits
    # Generation < 2 seconds, Queries < 50ms, Serialization < 500ms
    graphs = []
    for i in range(1000):
        score = float(30 + (i % 65))
        conf = 0.5 + ((i % 10) / 20.0)
        consensus = 0.6 + ((i % 5) / 10.0)
        category = "SaaS" if i % 2 == 0 else "BioTech"
        
        g = create_mock_graph(
            startup_id=f"SCALE-{i}",
            name=f"Scale Startup {i}",
            category=category,
            investment_score=score,
            confidence=conf,
            overall_consensus=consensus,
            active_risks_count=i % 4,
            evidence_count=(i % 5) + 1,
            executive_confidence=conf,
            question_count=i % 3
        )
        graphs.append(g)

    # 1. Benchmark Committee Decision Generation
    t_start = time.perf_counter()
    for g in graphs:
        CommitteeDecisionEngine.generate(g)
    t_end = time.perf_counter()
    gen_duration = t_end - t_start
    print(f"Committee decision generation duration (1000 startups): {gen_duration:.4f} seconds")
    assert gen_duration < 2.0, f"Committee decision generation took {gen_duration:.4f} seconds (Limit: 2.0s)"

    decisions = [g.committee_decision for g in graphs]

    # 2. Benchmark Queries
    t_q_start = time.perf_counter()
    ready = get_ready_for_incubation(decisions)
    prio = get_high_priority(decisions)
    stats = statistics(decisions)
    dash = committee_dashboard(decisions)
    t_q_end = time.perf_counter()
    query_duration = t_q_end - t_q_start
    print(f"Queries execution duration (1000 startups): {query_duration * 1000.0:.4f} ms")
    assert query_duration < 0.050, f"Queries took {query_duration * 1000.0:.4f} ms (Limit: 50ms)"

    # 3. Benchmark Serialization
    t_s_start = time.perf_counter()
    # Serialize first decision
    json_str = CommitteeSerializer.to_json(decisions[0])
    # Serialize list to CSV
    csv_str = CommitteeSerializer.to_csv(decisions[:100])
    # Serialize to Excel
    xls_bytes = CommitteeSerializer.to_excel(decisions[:100])
    t_s_end = time.perf_counter()
    serial_duration = t_s_end - t_s_start
    print(f"Serialization duration (100 startups): {serial_duration * 1000.0:.4f} ms")
    assert serial_duration < 0.500, f"Serialization took {serial_duration * 1000.0:.4f} ms (Limit: 500ms)"


# --- Sprint 4.1A Committee Decision Engine Tests ---

from app.modules.evaluation.committee.committee_models import (
    CommitteeReport, CommitteeDecision, CommitteeFinding, CommitteeConcern,
    CommitteeConsensus, CommitteeRecommendation
)
from app.modules.evaluation.committee import (
    generate_committee_report, build_consensus, resolve_conflicts,
    collect_assessments, merge_observations, aggregate_findings,
    aggregate_risks, aggregate_questions, generate_recommendations,
    generate_summary, calculate_overall_confidence, persist_committee_report,
    get_report, list_reports, list_reports_by_startup, list_reports_by_decision,
    get_committee_findings, get_committee_concerns, get_committee_recommendations,
    get_traceability, export_report
)

def test_committee_report_generation_success():
    # Setup mock graph
    g = create_mock_graph("REP-1", "Startup Report", "SaaS", 88.0, 0.95, active_risks_count=1)
    
    # Inject observations in multiple domains to trigger dependency detection
    g.observations["obs-trl"] = ObservationNode(
        node_id="obs-trl", node_type=NodeType.OBSERVATION,
        observation_id="obs-trl", domain="trl",
        observation="TRL 6 validation complete.", confidence=0.85
    )
    g.observations["obs-fin"] = ObservationNode(
        node_id="obs-fin", node_type=NodeType.OBSERVATION,
        observation_id="obs-fin", domain="financial",
        observation="Company runway is secure.", confidence=0.9
    )
    g.observations["obs-mkt"] = ObservationNode(
        node_id="obs-mkt", node_type=NodeType.OBSERVATION,
        observation_id="obs-mkt", domain="market",
        observation="Market demand is validated.", confidence=0.8
    )
    
    # Generate report
    report = generate_committee_report(g, workflow_reference="wf-ref-123", metadata={"user": "admin_user", "request_id": "req-999"})
    
    # 1. Decision check
    assert report.decision.startup_id == "REP-1"
    assert report.decision.startup_name == "Startup Report"
    assert report.decision.overall_confidence > 0.8
    assert report.decision.workflow_reference == "wf-ref-123"
    assert report.decision.metadata == {"user": "admin_user", "request_id": "req-999"}
    
    # 2. Recommendations check
    assert report.recommendations.recommendation == "Ready for Incubation"
    assert report.recommendations.priority == "CRITICAL"
    assert len(report.recommendations.required_documents) > 0
    assert len(report.recommendations.required_followups) > 0
    
    # 3. Consensus check
    assert report.consensus.agreement_level >= 0.8
    assert len(report.consensus.cross_domain_dependencies) > 0
    
    # 4. Persistence check
    assert getattr(g, "committee_report", None) == report
    assert get_report(report.decision.decision_id) == report



def test_consensus_logic_corroborations_and_contradictions():
    g = create_mock_graph("CONS-1", "Consensus Startup", "SaaS", 75.0, 0.9)
    
    # Add manual observations with high similarity to test corroboration
    obs_fin = ObservationNode(
        node_id="obs-fin-1", node_type=NodeType.OBSERVATION,
        observation_id="obs-fin-1", domain="financial",
        observation="Capital runway is verified and stable for next 18 months.", confidence=0.9
    )
    obs_mkt = ObservationNode(
        node_id="obs-mkt-1", node_type=NodeType.OBSERVATION,
        observation_id="obs-mkt-1", domain="market",
        observation="Market runway is verified and stable for next 18 months.", confidence=0.85
    )
    g.observations["obs-fin-1"] = obs_fin
    g.observations["obs-mkt-1"] = obs_mkt
    
    # Add manual conflict to test contradictions
    conf = ConflictNode(
        node_id="conf-manual", node_type=NodeType.CONFLICT,
        conflict_id="conf-manual", description="Factual contradiction on paying clients count.",
        conflict_type="FACTUAL", confidence=0.75, created_at=datetime.utcnow()
    )
    g.conflicts["conf-manual"] = conf
    
    # Build findings
    findings = aggregate_findings(g)
    
    # Find the corroborated finding containing both runway observations
    corroborated = None
    for f in findings:
        if "obs-fin-1" in f.supporting_observations and "obs-mkt-1" in f.supporting_observations:
            corroborated = f
            break
            
    assert corroborated is not None, "Similarity-based observation merging failed"
    assert "financial" in corroborated.domains
    assert "market" in corroborated.domains
    assert corroborated.confidence == 0.875  # (0.9 + 0.85) / 2
    
    # Build consensus
    consensus = build_consensus(g, findings)
    
    # Assert contradictions contains our conflict
    assert any(c["conflict_id"] == "conf-manual" for c in consensus.contradictions)
    assert consensus.agreement_level < 1.0


def test_risk_aggregation_and_concern_mapping():
    g = create_mock_graph("RISK-AGG-1", "Risk Agg Startup", "SaaS", 70.0, 0.9)
    
    # Add duplicate risks with very similar text to ensure Jaccard similarity >= 0.5
    r1 = RiskNode(
        node_id="risk-manual-1", node_type=NodeType.RISK,
        risk_id="risk-manual-1", category="financial",
        description="financial cash runway is insufficient under aggressive hiring plans.", confidence=0.8, reasoning=""
    )
    r2 = RiskNode(
        node_id="risk-manual-2", node_type=NodeType.RISK,
        risk_id="risk-manual-2", category="financial",
        description="financial cash runway is insufficient under high hiring plans.", confidence=0.7, reasoning=""
    )
    g.risks["risk-manual-1"] = r1
    g.risks["risk-manual-2"] = r2
    
    # Add a mock edge linking risk to observation to test provenance
    g.out_edges["risk-manual-1"] = [Edge(source_id="risk-manual-1", source_type=NodeType.RISK, target_id="obs-1", target_type=NodeType.OBSERVATION, relationship="REFERENCES")]
    g.out_edges["risk-manual-2"] = [Edge(source_id="risk-manual-2", source_type=NodeType.RISK, target_id="obs-2", target_type=NodeType.OBSERVATION, relationship="REFERENCES")]
    
    concerns = aggregate_risks(g)
    
    # Assert that they were merged
    financial_concerns = [c for c in concerns if "financial" in c.affected_domains]
    # Check that a merged concern exists with a combined description or higher confidence
    merged = None
    for c in financial_concerns:
        if "aggressive" in c.description.lower() or "runway" in c.description.lower():
            merged = c
            
    assert merged is not None
    assert merged.confidence == 0.8  # max confidence
    assert len(merged.linked_risks) > 0



def test_validator_rules_for_report():
    g = create_mock_graph("VAL-1", "Validation Startup", "SaaS", 80.0, 0.9)
    report = generate_committee_report(g, workflow_reference="wf-ref-123")
    
    # 1. Success case
    errors = CommitteeValidator.validate_report(report, g)
    assert len(errors) == 0, f"Expected 0 errors, got: {errors}"
    
    # 2. Out of bounds confidence
    report.decision.overall_confidence = 1.5
    errors = CommitteeValidator.validate_report(report, g)
    assert any("overall_confidence" in e or "confidence" in e for e in errors)
    report.decision.overall_confidence = 0.9
    
    # 3. Missing workflow reference
    report.decision.workflow_reference = ""
    errors = CommitteeValidator.validate_report(report, g)
    assert any("Workflow reference" in e for e in errors)
    report.decision.workflow_reference = "wf-ref-123"
    
    # 4. Orphan finding (remove all supporting observations)
    original_obs = report.findings[0].supporting_observations
    report.findings[0].supporting_observations = []
    errors = CommitteeValidator.validate_report(report, g)
    assert any("orphan" in e for e in errors)
    report.findings[0].supporting_observations = original_obs
    
    # 5. Broken graph hash reference
    report.decision.graph_hash = "INCORRECT_HASH"
    errors = CommitteeValidator.validate_report(report, g)
    assert any("graph hash" in e or "clean graph hash" in e for e in errors)


def test_serialization_roundtrip_and_export():
    g = create_mock_graph("SER-1", "Ser Startup", "SaaS", 85.0, 0.9)
    report = generate_committee_report(g, workflow_reference="wf-ref-123")
    
    # 1. JSON Roundtrip
    json_str = CommitteeSerializer.to_json(report)
    rebuilt = CommitteeSerializer.from_json(json_str, CommitteeReport)
    assert rebuilt.decision.decision_id == report.decision.decision_id
    assert rebuilt.decision.startup_name == report.decision.startup_name
    assert rebuilt.consensus.agreement_level == report.consensus.agreement_level
    
    # 2. Markdown Export
    md = export_report(report.decision.decision_id, "markdown")
    assert md is not None
    assert "# Incubation Committee Report:" in md
    assert report.decision.startup_name in md
    assert report.recommendations.recommendation in md
    
    # 3. HTML Export
    html = export_report(report.decision.decision_id, "html")
    assert html is not None
    assert "<!DOCTYPE html>" in html
    assert report.decision.startup_name in html
    assert report.recommendations.recommendation in html
    
    # 4. PDF-ready dictionary export
    pdf_ready = export_report(report.decision.decision_id, "pdf")
    assert isinstance(pdf_ready, dict)
    assert pdf_ready["decision"]["decision_id"] == report.decision.decision_id


def test_events_publication_verification():
    from app.modules.intelligence.events import dispatcher
    
    events_captured = []
    def capture(event):
        events_captured.append(event)
        
    event_names = [
        "CommitteeStarted", "CommitteeCompleted", "CommitteeFindingCreated",
        "CommitteeConcernCreated", "CommitteeConsensusBuilt", "CommitteeRecommendationGenerated"
    ]
    for name in event_names:
        dispatcher.register(name, capture)
        
    try:
        g = create_mock_graph("EVENT-1", "Event Startup", "SaaS", 80.0, 0.9)
        generate_committee_report(g, workflow_reference="wf-ref-123")
        
        # Check captured events
        captured_names = [e.event_name for e in events_captured]
        for name in event_names:
            assert name in captured_names, f"Event {name} was not published"
    finally:
        for name in event_names:
            dispatcher.unregister(name, capture)



def test_audit_logging_entry_creation():
    from app.security.audit import get_recent_events
    
    g = create_mock_graph("AUDIT-1", "Audit Startup", "SaaS", 85.0, 0.9)
    report = generate_committee_report(g, workflow_reference="wf-ref-123", metadata={"user": "committee_chair", "request_id": "req-12345"})
    
    events = get_recent_events(limit=5)
    matching = [e for e in events if e.action == "committee.report_generated" and e.actor == "committee_chair"]
    assert len(matching) > 0, "No audit log entry created for committee report generation"
    
    entry = matching[0]
    assert entry.details["startup"] == "Audit Startup"
    assert entry.details["workflow_id"] == "wf-ref-123"
    assert entry.details["generated_report_id"] == report.decision.decision_id
    assert entry.details["request_id"] == "req-12345"


def test_queries_report_lookup():
    from app.modules.evaluation.committee.committee_queries import clear_report_registry
    clear_report_registry()
    
    g1 = create_mock_graph("Q-1", "Query Startup One", "SaaS", 85.0, 0.9)
    r1 = generate_committee_report(g1, workflow_reference="wf-1")
    
    g2 = create_mock_graph("Q-2", "Query Startup Two", "Hardware", 50.0, 0.8)
    r2 = generate_committee_report(g2, workflow_reference="wf-2")
    
    # 1. list_reports
    all_reports = list_reports()
    assert len(all_reports) == 2
    
    # 2. list_reports_by_startup
    s1_reports = list_reports_by_startup("Q-1")
    assert len(s1_reports) == 1
    assert s1_reports[0] == r1
    
    # 3. list_reports_by_decision
    dec_reports = list_reports_by_decision(r2.decision.decision_id)
    assert len(dec_reports) == 1
    assert dec_reports[0] == r2
    
    # 4. get_committee_findings/concerns/recommendations
    findings = get_committee_findings(r1.decision.decision_id)
    assert len(findings) == len(r1.findings)
    
    concerns = get_committee_concerns(r1.decision.decision_id)
    assert len(concerns) == len(r1.concerns)
    
    rec = get_committee_recommendations(r1.decision.decision_id)
    assert rec == r1.recommendations
    
    trace = get_traceability(r1.decision.decision_id)
    assert trace == r1.traceability


def test_new_committee_engine_performance_benchmarks():
    # Build large scale graph
    # Dataset targets: 10 expert assessments, 500 observations, 300 risks, 200 questions.
    g = ObservationGraph()
    g.startup_id = "SCALE-BENCH-1"
    g.graph_id = "SCALE-BENCH-1"
    g.startup_name = "Scale Performance Startup"
    g.created_at = "2026-06-25T12:00:00Z"
    
    static_time = datetime(2026, 6, 25, 12, 0, 0)
    
    # Add 10 Expert assessments
    for i in range(10):
        asm_id = f"asm-{i}"
        g.assessments[asm_id] = AssessmentNode(
            node_id=asm_id, node_type=NodeType.ASSESSMENT,
            assessment_id=asm_id, domain=f"domain-{i}",
            expert_name=f"Expert {i}", agent_version="1.0", prompt_version="1.0",
            confidence=0.85, generated_at=static_time
        )
        
    # Add 500 observations (50 per domain)
    for i in range(500):
        obs_id = f"obs-{i}"
        domain = f"domain-{i % 10}"
        # Make some observations highly similar to group them (similar description strings)
        # e.g., index % 10 will create a lot of overlaps
        g.observations[obs_id] = ObservationNode(
            node_id=obs_id, node_type=NodeType.OBSERVATION,
            observation_id=obs_id, domain=domain,
            observation=f"Observation description text for index {i % 25}", confidence=0.8
        )
        
    # Add 300 risks
    for i in range(300):
        r_id = f"risk-{i}"
        category = f"domain-{i % 10}"
        g.risks[r_id] = RiskNode(
            node_id=r_id, node_type=NodeType.RISK,
            risk_id=r_id, category=category,
            description=f"Risk factor description for performance test number {i % 20}", confidence=0.75, reasoning=""
        )
        
    # Add 200 questions
    for i in range(200):
        q_id = f"qst-{i}"
        g.questions[q_id] = QuestionNode(
            node_id=q_id, node_type=NodeType.QUESTION,
            question_id=q_id, question=f"How does the team plan to mitigate the risks in domain {i % 10}?", purpose="Performance test"
        )
        
    # Add 5 conflicts
    for i in range(5):
        c_id = f"conf-{i}"
        g.conflicts[c_id] = ConflictNode(
            node_id=c_id, node_type=NodeType.CONFLICT,
            conflict_id=c_id, description=f"Conflict {i}",
            conflict_type="FACTUAL", confidence=0.8, created_at=static_time
        )
        
    # 1. Benchmark Consensus Build (<100 ms)
    # Collect findings first
    t_start = time.perf_counter()
    findings = aggregate_findings(g)
    consensus = build_consensus(g, findings)
    t_end = time.perf_counter()
    consensus_duration = (t_end - t_start) * 1000.0
    print(f"NEW ENGINE: Consensus build duration: {consensus_duration:.2f} ms")
    assert consensus_duration < 100.0, f"Consensus build took {consensus_duration:.2f} ms (Limit: 100ms)"
    
    # 2. Benchmark Committee Generation (<500 ms)
    t_start = time.perf_counter()
    report = generate_committee_report(g, workflow_reference="wf-bench")
    t_end = time.perf_counter()
    gen_duration = (t_end - t_start) * 1000.0
    print(f"NEW ENGINE: Report generation duration: {gen_duration:.2f} ms")
    assert gen_duration < 500.0, f"Committee generation took {gen_duration:.2f} ms (Limit: 500ms)"
    
    # 3. Benchmark Serialization (<250 ms)
    t_start = time.perf_counter()
    json_str = CommitteeSerializer.to_json(report)
    md_str = CommitteeSerializer.to_markdown(report)
    html_str = CommitteeSerializer.to_html(report)
    t_end = time.perf_counter()
    serialization_duration = (t_end - t_start) * 1000.0
    print(f"NEW ENGINE: Serialization duration (JSON + MD + HTML): {serialization_duration:.2f} ms")
    assert serialization_duration < 250.0, f"Serialization took {serialization_duration:.2f} ms (Limit: 250ms)"
    
    # 4. Benchmark Queries (<20 ms)
    t_start = time.perf_counter()
    r = get_report(report.decision.decision_id)
    f_list = get_committee_findings(report.decision.decision_id)
    c_list = get_committee_concerns(report.decision.decision_id)
    t_end = time.perf_counter()
    query_duration = (t_end - t_start) * 1000.0
    print(f"NEW ENGINE: Queries lookup duration: {query_duration:.2f} ms")
    assert query_duration < 20.0, f"Queries took {query_duration:.2f} ms (Limit: 20ms)"

