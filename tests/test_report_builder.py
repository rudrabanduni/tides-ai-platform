import pytest
import uuid
from datetime import datetime
from app.modules.evaluation.graph import ObservationGraphBuilder, NodeType
from app.modules.reporting import ReportBuilder, DueDiligenceReport

# --- Mock Context Helpers ---

class DummyDocument:
    def __init__(self, id, name, doc_type):
        self.id = id
        self.document_name = name
        self.document_type = doc_type
        self.uploaded_at = "2026-06-24T12:00:00Z"

class DummyProfile:
    def __init__(self, doc_list, name="Test Startup", id="startup-123"):
        self.documents = doc_list
        self.startup_name = name
        self.startup_id = id
        self.sector = "Fintech"

class DummyField:
    def __init__(self, key):
        self.field_key = key

class DummyClaim:
    def __init__(self, id, key, val):
        self.id = id
        self.field = DummyField(key)
        self.value_string = val if isinstance(val, str) else None
        self.value_number = val if isinstance(val, (int, float)) else None
        self.value_boolean = val if isinstance(val, bool) else None
        self.value_json = val if isinstance(val, (dict, list)) else None

class DummyEvidence:
    def __init__(self, id, claim_id, doc_id, text="excerpt", section="Moat", page=1):
        self.id = id
        self.claim_id = claim_id
        self.source_document_id = doc_id
        self.evidence_snippet = text
        self.section_name = section
        self.page_number = page
        self.confidence_score = 0.9

class DummyObservation:
    def __init__(self, obs_id, text, claim_ids, evidence_ids, domain="product", conf=0.85):
        self.observation_id = obs_id
        self.observation = text
        self.claim_ids = claim_ids
        self.evidence_ids = evidence_ids
        self.domain = domain
        self.confidence = conf

class DummyRisk:
    def __init__(self, id, desc, obs_ids, claim_ids, ev_ids, cat="product", conf=0.8, reasoning="mitigate"):
        self.id = id
        self.category = cat
        self.description = desc
        self.supporting_observations = obs_ids
        self.supporting_claims = claim_ids
        self.supporting_evidence = ev_ids
        self.confidence = conf
        self.reasoning = reasoning

class DummyQuestion:
    def __init__(self, id, qst, purpose, obs_ids=None, risk_ids=None):
        self.id = id
        self.question = qst
        self.purpose = purpose
        self.related_observation_ids = obs_ids or []
        self.related_risk_ids = risk_ids or []

class DummyConfidence:
    def __init__(self, conf=0.85):
        self.overall_domain_confidence = conf

class DummyAssessment:
    def __init__(self, domain, obs_list, risk_list, qst_list, version="1.0.0", prompt_ver="1.0.0", conf=0.85):
        self.domain = domain
        self.assessment_id = f"ASM-{domain.upper()}"
        self.observations = obs_list
        self.risks = risk_list
        self.questions = qst_list
        self.agent_version = version
        self.prompt_version = prompt_ver
        self.confidence = DummyConfidence(conf)
        self.generated_at = "2026-06-24T12:00:00Z"


@pytest.fixture
def complex_graph():
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
        DummyObservation("obs-1", "No laboratory validation logs found.", ["claim-1"], ["ev-1"], "product"),
        DummyObservation("obs-2", "Target addressable market is under 1 million.", ["claim-2"], ["ev-2"], "market")
    ]
    risks = [
        DummyRisk("risk-1", "Unvalidated technology risk", ["obs-1"], ["claim-1"], ["ev-1"], "product")
    ]
    questions = [
        DummyQuestion("qst-1", "Provide lab test receipt", "verify TRL", ["obs-1"], [])
    ]
    assessments = [
        DummyAssessment("product", obs, risks, questions)
    ]
    
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    # Mock Executive and Investment Assessment
    class DummySummary:
        overview = "Sleek software product with some IP constraints."
        strengths = ["Strong core engineering"]
        weaknesses = ["Unvalidated hardware component"]
        opportunities = ["Enterprise partnerships"]
        threats = ["Competitor patent filings"]

    class DummyExecutive:
        node_id = "exec-1"
        node_type = NodeType.EXECUTIVE
        confidence = 0.82
        readiness_level = "TRL-4"
        key_observations = [graph.observations["obs-1"]]
        major_risks = [graph.risks["risk-1"]]
        summary = DummySummary()

    graph.executive_assessment = DummyExecutive()

    class DummyInvestment:
        node_id = "inv-1"
        node_type = NodeType.INVESTMENT
        recommendation = "WATCHLIST"
        investment_score = 65.0
        confidence = 0.8
        readiness_score = 45.0
        investment_rationale = "Wait for tech audit confirmation"
        missing_information = ["Detailed financials"]
        follow_up_questions = ["Clarify patent claim boundaries"]

    graph.investment_assessment = DummyInvestment()
    graph.graph_hash = "TEST-HASH-12345"
    return graph


def test_successful_report_generation(complex_graph):
    report = ReportBuilder.build_due_diligence_report(complex_graph)
    assert isinstance(report, DueDiligenceReport)
    assert report.startup_name == "Test Startup"
    assert report.overall_score == 65.0
    assert report.overall_confidence > 0.0
    assert report.graph_hash == "TEST-HASH-12345"
    assert "WATCHLIST" in report.investment_summary.recommendation
    assert report.product_assessment.confidence == 0.85
    assert len(report.product_assessment.observations) == 2


def test_empty_profile():
    profile = DummyProfile([], name="Empty Startup")
    graph = ObservationGraphBuilder.build(profile, [], [], [])
    graph.graph_hash = "EMPTY-HASH"
    report = ReportBuilder.build_due_diligence_report(graph)
    assert report.startup_name == "Empty Startup"
    assert report.overall_score == 50.0  # default score
    assert report.overall_confidence == 0.8  # default confidence


def test_missing_evidence(complex_graph):
    # Strip evidence nodes
    complex_graph.evidence = {}
    report = ReportBuilder.build_due_diligence_report(complex_graph)
    assert report.startup_name == "Test Startup"
    assert len(report.product_assessment.supporting_evidence) == 0


def test_missing_observations(complex_graph):
    complex_graph.observations = {}
    report = ReportBuilder.build_due_diligence_report(complex_graph)
    assert len(report.product_assessment.observations) == 0
    assert report.product_assessment.confidence == 0.8  # fallback confidence


def test_missing_risks(complex_graph):
    complex_graph.risks = {}
    report = ReportBuilder.build_due_diligence_report(complex_graph)
    assert len(report.product_assessment.weaknesses) == 0
    assert report.risk_matrix.technical.severity == "LOW"


def test_traceability(complex_graph):
    report = ReportBuilder.build_due_diligence_report(complex_graph)
    assert "graph_hash" in report.traceability
    assert "profile_version" in report.traceability
    assert len(report.traceability["referenced_observations"]) > 0
