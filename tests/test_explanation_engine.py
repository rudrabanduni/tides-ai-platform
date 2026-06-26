import time
import pytest
from datetime import datetime
from app.modules.evaluation.graph import ObservationGraphBuilder, ObservationGraph, NodeType
from app.modules.evaluation.graph.graph_models import DocumentNode
from app.modules.explainability import (
    ExplanationEngine,
    ExplanationValidator,
    ExplanationSerializer,
    ExplanationValidationError,
    explain_observation,
    explain_assessment,
    explain_risk,
    explain_committee_decision,
    explain_portfolio_rank,
    explain_investment,
    get_explanation,
    clear_explanation_registry,
)
from tests.test_observation_graph import (
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
    clear_explanation_registry()
    yield
    clear_explanation_registry()


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
    return graph


def test_observation_explanations(sample_graph) -> None:
    exp = explain_observation(sample_graph, "obs-1")
    assert exp is not None
    assert exp.target_type == "OBSERVATION"
    assert exp.target_id == "obs-1"
    assert exp.confidence == 0.85
    assert len(exp.lineage.documents) == 1
    assert exp.lineage.documents[0]["node_id"] == "doc-1"
    assert len(exp.lineage.claims) == 1
    assert exp.lineage.claims[0]["node_id"] == "claim-1"
    
    # Registry check
    retrieved = get_explanation(exp.explanation_id)
    assert retrieved == exp
    
    # Validation check
    ExplanationValidator.validate_and_raise(exp, sample_graph)


def test_assessment_explanations(sample_graph) -> None:
    exp = explain_assessment(sample_graph, "ASM-TECHNICAL")
    assert exp is not None
    assert exp.target_type == "ASSESSMENT"
    assert exp.target_id == "ASM-TECHNICAL"
    
    # Lineage check
    assert len(exp.lineage.assessments) == 1
    assert exp.lineage.assessments[0]["node_id"] == "ASM-TECHNICAL"
    assert len(exp.lineage.observations) == 2
    
    ExplanationValidator.validate_and_raise(exp, sample_graph)


def test_risk_explanations(sample_graph) -> None:
    exp = explain_risk(sample_graph, "risk-1")
    assert exp is not None
    assert exp.target_type == "RISK"
    assert exp.target_id == "risk-1"
    
    # Supporting observation in lineage
    assert len(exp.lineage.observations) > 0
    assert any(o["node_id"] == "obs-1" for o in exp.lineage.observations)
    
    ExplanationValidator.validate_and_raise(exp, sample_graph)


def test_committee_decision_explanations(sample_graph) -> None:
    # Setup dummy committee decision on the graph
    class DummyDecision:
        node_id = "dec-1"
        node_type = NodeType.DECISION
        recommendation = "INCUBATE"
        confidence = 0.9
        reasoning = "Strong team and product fit"
        
    sample_graph.committee_decision = DummyDecision()
    
    exp = explain_committee_decision(sample_graph, "dec-1")
    assert exp is not None
    assert exp.target_type == "DECISION"
    assert exp.target_id == "dec-1"
    assert exp.confidence == 0.9
    
    ExplanationValidator.validate_and_raise(exp, sample_graph)


def test_investment_decision_explanations(sample_graph) -> None:
    # Setup dummy investment assessment
    class DummyInvestment:
        node_id = "inv-1"
        node_type = NodeType.INVESTMENT
        recommendation = "Recommended"
        confidence = 0.8
        
    sample_graph.investment_assessment = DummyInvestment()
    
    exp = explain_investment(sample_graph, "inv-1")
    assert exp is not None
    assert exp.target_type == "INVESTMENT"
    assert exp.target_id == "inv-1"
    
    ExplanationValidator.validate_and_raise(exp, sample_graph)


def test_portfolio_ranking_explanations(sample_graph) -> None:
    # Setup dummy portfolio entry
    class DummyPortfolioEntry:
        startup_id = "startup-1"
        investment_assessment_id = "inv-1"
        rank = 1
        
    class DummyInvestment:
        node_id = "inv-1"
        node_type = NodeType.INVESTMENT
        confidence = 0.95
        
    sample_graph.portfolio_entry = DummyPortfolioEntry()
    sample_graph.investment_assessment = DummyInvestment()
    
    exp = explain_portfolio_rank(sample_graph, "startup-1")
    assert exp is not None
    assert exp.target_type == "PORTFOLIO"
    assert exp.target_id == "startup-1"
    
    ExplanationValidator.validate_and_raise(exp, sample_graph)


def test_broken_lineage_detection(sample_graph) -> None:
    exp = explain_observation(sample_graph, "obs-1")
    
    # 1. Modify the lineage to introduce a broken reference
    exp.lineage.documents[0]["node_id"] = "broken-doc-id"
    
    # Validation should fail
    result = ExplanationValidator.validate_explanation(exp, sample_graph)
    assert len(result["errors"]) > 0
    assert any("broken-doc-id" in err for err in result["errors"])
    
    with pytest.raises(ExplanationValidationError):
        ExplanationValidator.validate_and_raise(exp, sample_graph)

    # 2. Test out of bounds confidence
    exp.confidence = 1.5
    result_bounds = ExplanationValidator.validate_explanation(exp, sample_graph)
    assert any("out of bounds" in err for err in result_bounds["errors"])


def test_serialization(sample_graph) -> None:
    exp = explain_observation(sample_graph, "obs-1")
    
    # 1. Serialize to JSON
    json_str = ExplanationSerializer.to_json(exp)
    assert json_str != ""
    assert "obs-1" in json_str
    
    # 2. Deserialize
    rebuilt = ExplanationSerializer.from_json(json_str)
    assert rebuilt is not None
    assert rebuilt.explanation_id == exp.explanation_id
    assert rebuilt.target_id == exp.target_id
    assert rebuilt.confidence == exp.confidence
    
    # 3. Export to audit format
    audit_data = ExplanationSerializer.to_audit_format(exp)
    assert isinstance(audit_data, dict)
    assert audit_data["explanation_id"] == exp.explanation_id
    assert "Patent Log" in audit_data["documents_referenced"]
    assert any("TRL is unvalidated" in c for c in audit_data["claims"])


def test_performance_and_large_graph() -> None:
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
    
    # Test generation performance < 100ms
    engine = ExplanationEngine()
    
    t0 = time.perf_counter()
    exp = engine.generate_explanation(graph, "obs-0-0", "OBSERVATION")
    gen_time_ms = (time.perf_counter() - t0) * 1000.0
    assert gen_time_ms < 100.0, f"Explanation generation took {gen_time_ms:.2f} ms (Target: < 100ms)"
    
    # Test lookup performance < 25ms
    t0 = time.perf_counter()
    get_explanation(exp.explanation_id)
    lookup_time_ms = (time.perf_counter() - t0) * 1000.0
    assert lookup_time_ms < 25.0, f"Explanation lookup took {lookup_time_ms:.2f} ms (Target: < 25ms)"
    
    # Test serialization performance < 500ms
    t0 = time.perf_counter()
    json_str = ExplanationSerializer.to_json(exp)
    ser_time_ms = (time.perf_counter() - t0) * 1000.0
    assert ser_time_ms < 500.0, f"Explanation serialization took {ser_time_ms:.2f} ms (Target: < 500ms)"
