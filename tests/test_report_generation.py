import time
import pytest
import uuid
from datetime import datetime
from app.modules.evaluation.graph import ObservationGraphBuilder, ObservationGraph, NodeType
from app.modules.reporting import (
    ReportBuilder,
    ReportValidator,
    ReportValidationError,
    ReportSerializer,
    MarkdownRenderer,
    HTMLRenderer,
    JSONRenderer,
    register_report,
    get_report,
    get_latest_report,
    clear_report_registry,
    Report,
)
from tests.test_explanation_engine import (
    DummyDocument,
    DummyProfile,
    DummyClaim,
    DummyEvidence,
    DummyObservation,
    DummyRisk,
    DummyQuestion,
    DummyAssessment,
)


@pytest.fixture(autouse=True)
def setup_teardown():
    clear_report_registry()
    yield
    clear_report_registry()


@pytest.fixture
def sample_graph():
    docs = [DummyDocument("doc-1", "Patent Log", "Patent")]
    profile = DummyProfile(docs)
    claims = [
        DummyClaim("claim-1", "technical_risk_claims", "TRL is unvalidated"),
        DummyClaim("claim-2", "market_risk_claims", "Target market is small")
    ]
    evidence = [
        DummyEvidence("ev-1", "claim-1", "doc-1"),
        DummyEvidence("ev-2", "claim-2", "doc-1")
    ]
    obs = [
        DummyObservation("obs-1", "No laboratory validation logs found.", ["claim-1"], ["ev-1"]),
        DummyObservation("obs-2", "Target addressable market is under 1 million.", ["claim-2"], ["ev-2"])
    ]
    risks = [
        DummyRisk("risk-1", "Unvalidated technology risk", ["obs-1"], ["claim-1"], ["ev-1"], "technical")
    ]
    questions = [
        DummyQuestion("qst-1", "Provide lab test receipt", "verify TRL", ["obs-1"], [])
    ]
    assessments = [
        DummyAssessment("technical", obs, risks, questions)
    ]
    
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    # Mock Executive assessment
    class DummySummary:
        overview = "High technical risk but clear IP moat."
        strengths = ["Strong IP barrier"]
        weaknesses = ["Unvalidated tech prototype"]
        opportunities = ["Niche defense contracts"]
        threats = ["Competitor patent filings"]

    class DummyExecutive:
        node_id = "exec-1"
        node_type = NodeType.EXECUTIVE
        confidence = 0.8
        readiness_level = 3
        key_observations = [graph.observations["obs-1"]]
        major_risks = [graph.risks["risk-1"]]
        summary = DummySummary()

    graph.executive_assessment = DummyExecutive()

    # Mock Investment assessment
    class DummyInvestment:
        node_id = "inv-1"
        node_type = NodeType.INVESTMENT
        recommendation = "WATCHLIST"
        investment_score = 62.5
        confidence = 0.75
        readiness_score = 30.0
        investment_rationale = "Wait for field test verification"

    graph.investment_assessment = DummyInvestment()

    # Mock Portfolio entry
    class DummyPortfolioEntry:
        rank = 4
        percentile = 75.0
        category = "Defense"
        ranking_reason = "Strong defense tech alignment"

    graph.portfolio_entry = DummyPortfolioEntry()

    # Mock Committee decision
    class DummyDDItem:
        category = "Technical DD"
        status = "PENDING"
        reason = "Verify TRL 3 prototype claims"
        blocking = True
        documents_required = ["Test logs"]

    class DummyDecision:
        node_id = "dec-1"
        decision_id = "dec-1"
        node_type = NodeType.DECISION
        recommendation = "PILOT_FIRST"
        decision_confidence = 0.82
        review_window = "3 Months"
        investment_priority = "MEDIUM"
        incubation_priority = "HIGH"
        pilot_priority = "CRITICAL"
        decision_reasoning = "Test prototype in lab environment first"
        committee_notes = "Coordinate with Technical Expert"
        blocking_risks = ["risk-1"]
        required_due_diligence = [DummyDDItem()]
        required_documents = ["lab_receipt.pdf"]
        follow_up_questions = ["qst-1"]

    graph.committee_decision = DummyDecision()

    return graph


def test_report_generation_success(sample_graph) -> None:
    report = ReportBuilder.build_report(sample_graph, generated_by="Test Suite")
    assert report is not None
    assert report.startup_id == sample_graph.startup_id
    assert report.startup_name == sample_graph.startup_name
    assert report.generated_by == "Test Suite"
    
    # Section presence checks
    assert "Strong IP barrier" in report.executive_summary
    assert "Unvalidated technology risk" in report.risk_analysis
    assert "PILOT_FIRST" in report.committee_decision
    assert "62.50" in report.investment_recommendation
    assert "**Rank:** #4" in report.portfolio_position
    
    # Audit details
    assert "obs-1" in report.explainability_appendix
    assert "ev-1" in report.evidence_appendix
    
    # Validator pass check
    validation_results = ReportValidator.validate_report(report, sample_graph)
    assert len(validation_results["errors"]) == 0
    
    # Queries / Registry checks
    register_report(report)
    retrieved = get_report(report.report_id)
    assert retrieved == report
    
    latest = get_latest_report(report.startup_id)
    assert latest == report


def test_report_generation_empty_graph() -> None:
    # Build clean empty graph
    graph = ObservationGraph()
    graph.startup_id = "empty-startup"
    graph.startup_name = "Empty Sandbox"
    graph.graph_hash = "dummy-graph-hash"
    graph.graph_version = "1.0.0"
    
    report = ReportBuilder.build_report(graph)
    assert report is not None
    assert report.startup_id == "empty-startup"
    
    # Stubs check
    assert "not been compiled" in report.executive_summary.lower() or "N/A" in report.executive_summary
    assert "not been compiled" in report.committee_decision.lower()
    
    # Validator should return validation errors because executive & committee are missing
    results = ReportValidator.validate_report(report, graph)
    assert len(results["errors"]) > 0
    assert any("Missing Executive Summary" in err for err in results["errors"])


def test_missing_sections_validation(sample_graph) -> None:
    report = ReportBuilder.build_report(sample_graph)
    
    # Intentionally empty out a required section
    report.founder_analysis = ""
    
    results = ReportValidator.validate_report(report, sample_graph)
    assert any("Missing Section: Section 'founder_analysis' is empty" in err for err in results["errors"])


def test_missing_evidence_validation(sample_graph) -> None:
    report = ReportBuilder.build_report(sample_graph)
    
    # Remove evidence ID 'ev-1' from evidence appendix text
    report.evidence_appendix = report.evidence_appendix.replace("ev-1", "ev-removed")
    
    results = ReportValidator.validate_report(report, sample_graph)
    assert any("Incomplete Evidence Appendix: Evidence 'ev-1'" in err for err in results["errors"])


def test_invalid_references_validation(sample_graph) -> None:
    # Add an observation referencing non-existent claim to active observations list
    class OrphanObservation:
        observation_id = "obs-orphan"
        observation = "Orphan observation text"
        domain = "founder"
        confidence = 0.9
        claim_ids = ["non-existent-claim"]
        evidence_ids = ["ev-1"]
        node_type = NodeType.OBSERVATION

    sample_graph.observations["obs-orphan"] = OrphanObservation()
    
    # Add a mock edge to trigger a broken claim reference check
    from app.modules.evaluation.graph.graph_models import Edge
    edge = Edge(
        source_id="obs-orphan",
        source_type=NodeType.OBSERVATION,
        target_id="non-existent-claim",
        target_type=NodeType.CLAIM,
        relationship="SUPPORTED_BY"
    )
    sample_graph.edges.append(edge)
    sample_graph.out_edges.setdefault("obs-orphan", []).append(edge)

    report = ReportBuilder.build_report(sample_graph)
    results = ReportValidator.validate_report(report, sample_graph)
    assert any("Broken Traceability Reference" in err for err in results["errors"])


def test_hash_stability(sample_graph) -> None:
    report1 = ReportBuilder.build_report(sample_graph)
    report2 = ReportBuilder.build_report(sample_graph)
    assert report1.report_hash == report2.report_hash
    
    # Hash changes when content changes
    report1.executive_summary = "Modified summary content"
    recomputed = ReportBuilder._compute_hash(report1.model_dump())
    assert recomputed != report2.report_hash


def test_serialization(sample_graph) -> None:
    report = ReportBuilder.build_report(sample_graph)
    
    # 1. Serialize to JSON
    json_str = ReportSerializer.to_json(report)
    assert json_str != ""
    assert report.report_id in json_str
    
    # 2. Deserialize
    rebuilt = ReportSerializer.from_json(json_str)
    assert rebuilt is not None
    assert rebuilt.report_id == report.report_id
    assert rebuilt.report_hash == report.report_hash
    assert rebuilt.metadata == report.metadata


def test_rendering_formats(sample_graph) -> None:
    report = ReportBuilder.build_report(sample_graph)
    
    # Markdown
    md_str = ReportSerializer.export_markdown(report)
    assert "# Due Diligence Report:" in md_str
    assert "# Executive Summary" in md_str
    
    # HTML
    html_str = ReportSerializer.export_html(report)
    assert "<!DOCTYPE html>" in html_str
    assert f"<title>Due Diligence Report - {report.startup_name}</title>" in html_str
    assert "<h1>" in html_str


def test_metadata_validation(sample_graph) -> None:
    report = ReportBuilder.build_report(sample_graph)
    meta = report.metadata
    assert meta["graph_hash"] == sample_graph.graph_hash
    assert meta["active_risks_count"] == 1
    assert meta["total_evidence_referenced"] == 2


def test_large_dataset_performance() -> None:
    # Build large scale dataset:
    # 1000 claims, 5000 evidence, 500 obs, 200 risks, 100 assessments
    docs = [DummyDocument(f"doc-{i}", f"Doc-{i}", "PDF") for i in range(10)]
    profile = DummyProfile(docs)
    
    claims = [DummyClaim(f"claim-{i}", "market", f"val-{i}") for i in range(1000)]
    evidence = [DummyEvidence(f"ev-{i}", f"claim-{i % 1000}", f"doc-{i % 10}") for i in range(5000)]
    
    assessments = []
    for a in range(100):
        obs = [DummyObservation(f"obs-{a}-{o}", f"Observation test {o}", [f"claim-{o}"], [f"ev-{o}"]) for o in range(5)]
        risks = [DummyRisk(f"risk-{a}-{r}", f"Risk test {r}", [f"obs-{a}-{r}"], [f"claim-{r}"], [f"ev-{r}"]) for r in range(2)]
        questions = [DummyQuestion(f"qst-{a}-{q}", f"Q-{q}", "purpose", [f"obs-{a}-{q}"]) for q in range(2)]
        assessments.append(DummyAssessment(f"domain-{a}", obs, risks, questions))
        
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    # 1. Build Report Benchmark (< 1 second)
    t0 = time.perf_counter()
    report = ReportBuilder.build_report(graph)
    build_time = time.perf_counter() - t0
    assert build_time < 1.0, f"Report build took {build_time:.2f} seconds (Target: < 1 second)"
    
    # 2. Markdown Render Benchmark (< 300 ms)
    t0 = time.perf_counter()
    md_str = MarkdownRenderer().render(report)
    md_time = (time.perf_counter() - t0) * 1000.0
    assert md_time < 300.0, f"Markdown render took {md_time:.2f} ms (Target: < 300 ms)"
    
    # 3. HTML Render Benchmark (< 500 ms)
    t0 = time.perf_counter()
    html_str = HTMLRenderer().render(report)
    html_time = (time.perf_counter() - t0) * 1000.0
    assert html_time < 500.0, f"HTML render took {html_time:.2f} ms (Target: < 500 ms)"
    
    # 4. JSON Export Benchmark (< 200 ms)
    t0 = time.perf_counter()
    json_str = JSONRenderer().render(report)
    json_time = (time.perf_counter() - t0) * 1000.0
    assert json_time < 200.0, f"JSON export took {json_time:.2f} ms (Target: < 200 ms)"
