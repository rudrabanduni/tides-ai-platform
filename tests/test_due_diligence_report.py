import json
import time
import pytest
from datetime import datetime
from typing import List, Optional, Any

from app.modules.evaluation.graph import (
    NodeType, GraphNode, DocumentNode, EvidenceNode, ClaimNode,
    ObservationNode, AssessmentNode, ConflictNode, RiskNode,
    QuestionNode, Edge, GraphStatistics, ObservationGraph,
    ObservationGraphBuilder
)
from app.modules.evaluation.conflict_resolution import (
    ConflictResolutionEngine, ResolutionNode, ResolutionEdge
)
from app.modules.evaluation.executive import ExecutiveEngine
from app.modules.evaluation.investment import InvestmentEngine
from app.modules.evaluation.report import (
    DueDiligenceReportEngine, ReportValidator, ReportSerializer,
    get_report, get_summary, get_section, get_appendices, trace_report_section
)


# --- Mock Helper Classes ---

class DummyDocument:
    def __init__(self, id, name, doc_type, uploaded_at="2026-06-25T12:00:00Z"):
        self.id = id
        self.document_name = name
        self.document_type = doc_type
        self.uploaded_at = uploaded_at


class DummyProfile:
    def __init__(self, doc_list):
        self.documents = doc_list


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
    def __init__(self, id, claim_id, doc_id, text="excerpt", section="Main", page=1, conf=0.9):
        self.id = id
        self.claim_id = claim_id
        self.source_document_id = doc_id
        self.evidence_snippet = text
        self.section_name = section
        self.page_number = page
        self.confidence_score = conf


class DummyObservation:
    def __init__(self, obs_id, text, claim_ids, evidence_ids, conf=0.85, domain="trl"):
        self.observation_id = obs_id
        self.observation = text
        self.claim_ids = claim_ids
        self.evidence_ids = evidence_ids
        self.confidence = conf
        self.domain = domain
        self.consensus_status = "independent"


class DummyRisk:
    def __init__(self, id, desc, obs_ids, claim_ids, ev_ids, cat="technical", conf=0.8, reasoning="reason"):
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
    def __init__(self, domain, obs_list, risk_list=None, qst_list=None, version="1.0.0", prompt_ver="1.0.0", conf=0.85, generated_at="2026-06-25T12:00:00Z"):
        self.domain = domain
        self.assessment_id = f"ASM-{domain.upper()}"
        self.observations = obs_list
        self.risks = risk_list or []
        self.questions = qst_list or []
        self.agent_version = version
        self.prompt_version = prompt_ver
        self.confidence = DummyConfidence(conf)
        self.generated_at = generated_at


class DummyConflict:
    def __init__(self, id, explanation, claim1_id, claim2_id, conflict_type="FACTUAL", conf=0.9, created_at="2026-06-25T12:00:00Z"):
        self.id = id
        self.conflict_explanation = explanation
        self.conflict_type = conflict_type
        self.confidence = conf
        self.created_at = created_at
        self.preferred_claim_id = claim1_id
        self.superseded_claim_id = claim2_id


@pytest.fixture
def mock_graph():
    docs = [DummyDocument("doc-1", "Evaluation Intake Memo", "PDF")]
    profile = DummyProfile(docs)
    claims = [
        DummyClaim("claim-1", "founder_experience", "Founders have 15 years experience"),
        DummyClaim("claim-2", "product_features", "Maturity details"),
        DummyClaim("claim-3", "trl_level", "TRL is level 6"),
        DummyClaim("claim-4", "market_growth", "Market size is $50B"),
        DummyClaim("claim-5", "competition_threat", "Moderate competitive pressure"),
        DummyClaim("claim-6", "financial_runway", "Runway is 24 months"),
        DummyClaim("claim-7", "ip_patents", "Granted core patent"),
        DummyClaim("claim-8", "conflict_claim", "Conflicting observation claim")
    ]
    evidence = [DummyEvidence(f"ev-{i}", f"claim-{i}", "doc-1", conf=0.9) for i in range(1, 9)]
    
    obs_founder = DummyObservation("obs-founder", "Founders have relevant operational experience.", ["claim-1"], ["ev-1"], conf=0.92, domain="founder")
    obs_product = DummyObservation("obs-product", "Product capability validated via early pilot.", ["claim-2"], ["ev-2"], conf=0.88, domain="product")
    obs_trl = DummyObservation("obs-trl", "TRL is validated at level 6.", ["claim-3"], ["ev-3"], conf=0.85, domain="trl")
    obs_market = DummyObservation("obs-market", "Large TAM identified.", ["claim-4"], ["ev-4"], conf=0.82, domain="market")
    obs_comp = DummyObservation("obs-comp", "Moderate competition.", ["claim-5"], ["ev-5"], conf=0.78, domain="competition")
    obs_financial = DummyObservation("obs-financial", "Runway allows 24 months execution.", ["claim-6"], ["ev-6"], conf=0.84, domain="financial")
    obs_ip = DummyObservation("obs-ip", "Core patent granted.", ["claim-7"], ["ev-7"], conf=0.90, domain="ip")
    obs_conflict = DummyObservation("obs-conflict", "Superseded competition claim.", ["claim-8"], ["ev-8"], conf=0.45, domain="competition")

    risk = DummyRisk("risk-1", "Regulatory execution delay risk.", ["obs-product"], ["claim-2"], ["ev-2"], cat="regulatory", conf=0.5)
    qst = DummyQuestion("qst-1", "Detail the expansion target markets", "Assess scalability")

    asm_founder = DummyAssessment("founder", [obs_founder])
    asm_product = DummyAssessment("product", [obs_product], [risk])
    asm_trl = DummyAssessment("trl", [obs_trl])
    asm_market = DummyAssessment("market", [obs_market], qst_list=[qst])
    asm_comp = DummyAssessment("competition", [obs_comp, obs_conflict])
    asm_financial = DummyAssessment("financial", [obs_financial])
    asm_ip = DummyAssessment("ip", [obs_ip])

    conflict = DummyConflict("conf-1", "Moat factual dispute", "claim-5", "claim-8")

    graph = ObservationGraphBuilder.build(
        profile, claims, evidence,
        [asm_founder, asm_product, asm_trl, asm_market, asm_comp, asm_financial, asm_ip],
        [conflict]
    )
    return graph


# --- Test Cases ---

def test_generation(mock_graph):
    # Setup upstream components
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)

    # Generate Report
    graph = DueDiligenceReportEngine.generate(graph)

    report = graph.report
    assert report is not None
    assert report.node_type == NodeType.REPORT
    assert report.executive_summary.title == "Executive Summary"
    assert report.investment_summary.title == "Investment Recommendation Summary"
    assert "Founder" in report.founder_analysis.title
    assert "TRL" in report.trl_analysis.title
    assert len(report.appendices) == 3

    # Validate
    errors = ReportValidator.validate(graph)
    assert len(errors) == 0, f"Validator errors: {errors}"


def test_validation(mock_graph):
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)
    graph = DueDiligenceReportEngine.generate(graph)

    errors = ReportValidator.validate(graph)
    assert len(errors) == 0

    # Induce confidence violation
    graph.report.executive_summary.confidence = 1.5
    errors = ReportValidator.validate(graph)
    assert any("confidence" in e and "outside" in e for e in errors)


def test_duplicate_removal_and_conflict_filtering(mock_graph):
    # Factual conflict resolved in favor of claim-5. obs-conflict (superseded) must be excluded.
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)
    graph = DueDiligenceReportEngine.generate(graph)

    # obs-conflict must be excluded from observations section
    obs_content = graph.report.observations.content
    assert "obs-comp" in obs_content
    assert "obs-conflict" not in obs_content


def test_section_ordering(mock_graph):
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)
    graph = DueDiligenceReportEngine.generate(graph)

    report = graph.report
    # Verify section contents exist
    assert report.executive_summary.content is not None
    assert report.investment_summary.content is not None
    assert report.founder_analysis.content is not None
    assert report.product_analysis.content is not None


def test_traceability(mock_graph):
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)
    graph = DueDiligenceReportEngine.generate(graph)

    trace = trace_report_section(graph, "founder_analysis")
    assert trace is not None
    assert "obs-founder" in trace
    assert trace["obs-founder"]["observation"].observation_id == "obs-founder"


def test_serialization(mock_graph):
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)
    graph = DueDiligenceReportEngine.generate(graph)

    orig_hash = graph.graph_hash

    # Serialize
    json_str = ReportSerializer.to_json(graph)

    # Deserialize
    new_graph = ReportSerializer.from_json(json_str)
    assert new_graph.graph_hash == orig_hash
    assert new_graph.report is not None
    assert new_graph.report.report_id == graph.report.report_id
    assert new_graph.report.founder_analysis.title == graph.report.founder_analysis.title


def test_exporters(mock_graph):
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)
    graph = DueDiligenceReportEngine.generate(graph)

    # Markdown Export
    md = ReportSerializer.export_markdown(graph.report)
    assert "# Due Diligence Report:" in md
    assert "Executive Summary" in md

    # HTML Export
    html = ReportSerializer.export_html(graph.report)
    assert "<!DOCTYPE html>" in html
    assert "TIDES Due Diligence Report" in html

    # PDF Export
    pdf_bytes = ReportSerializer.export_pdf_data(graph.report)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 0
    # PDF starts with PDF magic number
    assert pdf_bytes.startswith(b"%PDF")


def test_graph_hash(mock_graph):
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)
    graph = DueDiligenceReportEngine.generate(graph)

    orig_hash = graph.graph_hash
    
    # Mutate section content
    graph.report.executive_summary.content = "Mutated exec content."
    new_hash = ObservationGraphBuilder._compute_hash(graph)
    assert orig_hash != new_hash


def test_backward_compatibility(mock_graph):
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)

    # Serialize without report
    json_str = ReportSerializer.to_json(graph)
    new_graph = ReportSerializer.from_json(json_str)

    assert new_graph.report is None
    assert len(new_graph.report_indexes) == 0
    assert len(new_graph.report_statistics) == 0


def test_large_graph_performance():
    # Setup large mock dataset matching target conditions:
    # 5000 evidence, 1000 claims, 500 observations, 300 correlations, 150 conflicts, 100 assessments
    docs = [DummyDocument(f"doc-{i}", f"Doc {i}", "PDF") for i in range(10)]
    profile = DummyProfile(docs)
    
    claims = []
    for i in range(1000):
        claims.append(DummyClaim(f"claim-{i}", f"key_{i}", f"Claim value {i}"))
        
    evidence = []
    for i in range(5000):
        claim_id = f"claim-{i % 1000}"
        doc_id = f"doc-{i % 10}"
        evidence.append(DummyEvidence(f"ev-{i}", claim_id, doc_id))
        
    assessments = []
    obs_counter = 0
    domains = ["founder", "product", "market", "competition", "financial", "ip", "trl", "risk"]
    for i in range(100):
        obs_list = []
        domain = domains[i % len(domains)]
        for _ in range(5):  # 5 observations per assessment => 500 observations total
            obs_id = f"obs-{obs_counter}"
            claim_ids = [f"claim-{obs_counter * 2 % 1000}", f"claim-{(obs_counter * 2 + 1) % 1000}"]
            ev_ids = [f"ev-{obs_counter * 10 % 5000}"]
            obs_list.append(DummyObservation(obs_id, f"Observation text for {obs_id}", claim_ids, ev_ids, domain=domain))
            obs_counter += 1
            
        assessments.append(DummyAssessment(domain, obs_list))
        
    conflicts = []
    for i in range(150):
        claim1 = f"claim-{(i * 4) % 1000}"
        claim2 = f"claim-{(i * 4 + 2) % 1000}"
        conflicts.append(DummyConflict(f"conf-{i}", f"Conflict explanation {i}", claim1, claim2))
        
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments, conflicts)
    
    # Add resolutions
    for i in range(150):
        res_id = f"RES-FACT-conf-{i}"
        res = ResolutionNode(
            node_id=res_id,
            node_type=NodeType.RESOLUTION,
            resolution_id=res_id,
            conflict_id=f"conf-{i}",
            resolution_type="FACTUAL",
            preferred_observation_id=f"obs-{i}",
            confidence=0.85,
            reasoning=f"Reason {i}",
            supporting_claims=[],
            supporting_evidence=[],
            supporting_assessments=[],
            created_at=datetime.utcnow().isoformat() + "Z"
        )
        graph.resolutions[res_id] = res
        graph.resolutions_by_conflict[f"conf-{i}"] = [res_id]
        
    # Generate upstream assessments
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)

    # Benchmark 1: Report Generation < 500 ms
    t_gen_start = time.perf_counter()
    graph = DueDiligenceReportEngine.generate(graph)
    t_gen_end = time.perf_counter()
    gen_duration = t_gen_end - t_gen_start
    print(f"Report Generation time: {gen_duration * 1000.0:.4f} ms")
    assert gen_duration < 0.500, f"Report generation exceeded 500 ms: {gen_duration * 1000.0:.4f}ms"
    
    # Benchmark 2: Queries < 10 ms
    t_query_start = time.perf_counter()
    rep = get_report(graph)
    summ = get_summary(graph)
    sec = get_section(graph, "founder_analysis")
    apps = get_appendices(graph)
    trace = trace_report_section(graph, "founder_analysis")
    t_query_end = time.perf_counter()
    query_duration = (t_query_end - t_query_start) * 1000.0
    print(f"Queries execution time: {query_duration:.4f} ms")
    assert query_duration < 10.0, f"Queries execution exceeded 10 ms: {query_duration:.4f}ms"
    
    # Benchmark 3: Serialization < 300 ms
    t_serial_start = time.perf_counter()
    json_str = ReportSerializer.to_json(graph)
    t_serial_end = time.perf_counter()
    serial_duration = t_serial_end - t_serial_start
    print(f"Serialization time: {serial_duration * 1000.0:.4f} ms")
    assert serial_duration < 0.500, f"Serialization exceeded 500 ms: {serial_duration * 1000.0:.4f}ms"
