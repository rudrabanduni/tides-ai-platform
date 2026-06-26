import pytest
import time
from datetime import datetime
from typing import Any
from app.modules.evaluation.graph import (
    NodeType, GraphNode, DocumentNode, EvidenceNode, ClaimNode,
    ObservationNode, AssessmentNode, ConflictNode, RiskNode,
    QuestionNode, Edge, GraphStatistics, ObservationGraph,
    ObservationGraphBuilder, GraphValidator, get_document, get_evidence,
    get_claim, get_observation, get_assessment, get_conflict, get_risk,
    get_question, trace_observation, trace_claim, trace_evidence,
    trace_assessment, trace_risk, trace_question, get_assessment_outputs,
    to_json, from_json, export_traceability
)

# --- Mock Context Helpers ---

class DummyDocument:
    def __init__(self, id, name, doc_type):
        self.id = id
        self.document_name = name
        self.document_type = doc_type
        self.uploaded_at = "2026-06-24T12:00:00Z"

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
    def __init__(self, id, claim_id, doc_id, text="excerpt", section="Moat", page=1):
        self.id = id
        self.claim_id = claim_id
        self.source_document_id = doc_id
        self.evidence_snippet = text
        self.section_name = section
        self.page_number = page
        self.confidence_score = 0.9

class DummyObservation:
    def __init__(self, obs_id, text, claim_ids, evidence_ids, conf=0.85):
        self.observation_id = obs_id
        self.observation = text
        self.claim_ids = claim_ids
        self.evidence_ids = evidence_ids
        self.confidence = conf

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
def sample_graph_data():
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
    
    return profile, claims, evidence, assessments


def test_graph_build_success(sample_graph_data):
    profile, claims, evidence, assessments = sample_graph_data
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    assert graph is not None
    assert graph.graph_id != ""
    assert graph.graph_hash != ""
    assert len(graph.documents) == 1
    assert len(graph.evidence) == 2
    assert len(graph.claims) == 2
    assert len(graph.observations) == 2
    assert len(graph.assessments) == 1
    
    # Check node models inherit from GraphNode and use NodeType
    assert graph.documents["doc-1"].node_type == NodeType.DOCUMENT
    assert graph.observations["obs-1"].node_type == NodeType.OBSERVATION
    
    # Check graph statistics
    stats = graph.graph_stats
    assert stats.document_count == 1
    assert stats.evidence_count == 2
    assert stats.claim_count == 2
    assert stats.observation_count == 2
    assert stats.assessment_count == 1
    assert stats.edge_count > 0


def test_graph_validation_success(sample_graph_data):
    profile, claims, evidence, assessments = sample_graph_data
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    errors = GraphValidator.validate(graph)
    assert len(errors) == 0, f"Expected no validation errors, got: {errors}"


def test_orphan_node_detection(sample_graph_data):
    profile, claims, evidence, assessments = sample_graph_data
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    # Add a disconnected DocumentNode
    orphan = DocumentNode(
        node_id="orphan-doc",
        node_type=NodeType.DOCUMENT,
        document_id="orphan-doc",
        document_name="Orphaned",
        document_type="PDF",
        uploaded_at=datetime.utcnow()
    )
    graph.documents[orphan.node_id] = orphan
    
    # Re-calc stats (stats don't fail validation, but node existence does)
    errors = GraphValidator.validate(graph)
    assert any("Orphan Node: Node 'orphan-doc'" in err for err in errors)


def test_missing_provenance_path(sample_graph_data):
    profile, claims, evidence, assessments = sample_graph_data
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    # Add an Observation with NO claims/evidence/assessment connections
    isolated_obs = ObservationNode(
        node_id="isolated-obs",
        node_type=NodeType.OBSERVATION,
        observation_id="isolated-obs",
        domain="ip",
        observation="Isolated finding without connections.",
        confidence=0.8
    )
    graph.observations[isolated_obs.node_id] = isolated_obs
    
    # Force some edge connection so it isn't flagged as an orphan, but has no upstream provenance
    edge = Edge(
        source_id=isolated_obs.node_id,
        source_type=NodeType.OBSERVATION,
        target_id="doc-1",
        target_type=NodeType.DOCUMENT,
        relationship="RELATED_TO"
    )
    graph.edges.append(edge)
    graph.out_edges.setdefault(isolated_obs.node_id, []).append(edge)
    graph.in_edges.setdefault("doc-1", []).append(edge)
    
    errors = GraphValidator.validate(graph)
    assert any("lacks a valid upstream provenance lineage path" in err for err in errors)


def test_missing_observation_reference(sample_graph_data):
    profile, claims, evidence, assessments = sample_graph_data
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    # Create a risk with no connections
    isolated_risk = RiskNode(
        node_id="isolated-risk",
        node_type=NodeType.RISK,
        risk_id="isolated-risk",
        category="technical",
        description="Isolated risk",
        confidence=0.9,
        reasoning="reasons"
    )
    graph.risks[isolated_risk.node_id] = isolated_risk
    
    # Make it not orphan
    edge = Edge(
        source_id="ASM-TECHNICAL",
        source_type=NodeType.ASSESSMENT,
        target_id=isolated_risk.node_id,
        target_type=NodeType.RISK,
        relationship="GENERATED"
    )
    graph.edges.append(edge)
    graph.out_edges.setdefault("ASM-TECHNICAL", []).append(edge)
    graph.in_edges.setdefault(isolated_risk.node_id, []).append(edge)
    
    errors = GraphValidator.validate(graph)
    assert any("does not reference any supporting observations" in err for err in errors)


def test_invalid_question_reference(sample_graph_data):
    profile, claims, evidence, assessments = sample_graph_data
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    # Create question with no reference to obs/risk
    isolated_qst = QuestionNode(
        node_id="isolated-qst",
        node_type=NodeType.QUESTION,
        question_id="isolated-qst",
        question="Is it correct?",
        purpose="audit"
    )
    graph.questions[isolated_qst.node_id] = isolated_qst
    
    # Make it not orphan
    edge = Edge(
        source_id="ASM-TECHNICAL",
        source_type=NodeType.ASSESSMENT,
        target_id=isolated_qst.node_id,
        target_type=NodeType.QUESTION,
        relationship="GENERATED"
    )
    graph.edges.append(edge)
    graph.out_edges.setdefault("ASM-TECHNICAL", []).append(edge)
    graph.in_edges.setdefault(isolated_qst.node_id, []).append(edge)
    
    errors = GraphValidator.validate(graph)
    assert any("does not reference any observation or risk" in err for err in errors)


def test_bidirectional_traversal(sample_graph_data):
    profile, claims, evidence, assessments = sample_graph_data
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    # Traversal from obs-1 to assessment (Assessment -> Observation)
    in_edges = graph.in_edges.get("obs-1", [])
    assert len(in_edges) > 0
    assert in_edges[0].source_id == "ASM-TECHNICAL"
    assert in_edges[0].relationship == "GENERATED"
    
    # Traversal from assessment to obs-1
    out_edges = graph.out_edges.get("ASM-TECHNICAL", [])
    assert any(e.target_id == "obs-1" and e.relationship == "GENERATED" for e in out_edges)


def test_trace_observation(sample_graph_data):
    profile, claims, evidence, assessments = sample_graph_data
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    # Lineage trace observation
    lineage = trace_observation(graph, "obs-1")
    assert lineage is not None
    assert lineage["observation"].observation_id == "obs-1"
    assert len(lineage["claims"]) == 1
    assert lineage["claims"][0]["claim"].claim_id == "claim-1"
    assert len(lineage["claims"][0]["evidence"]) == 1
    assert lineage["claims"][0]["evidence"][0]["evidence"].evidence_id == "ev-1"
    assert lineage["claims"][0]["evidence"][0]["document"].document_id == "doc-1"


def test_trace_assessment(sample_graph_data):
    profile, claims, evidence, assessments = sample_graph_data
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    lineage = trace_assessment(graph, "ASM-TECHNICAL")
    assert lineage is not None
    assert lineage["assessment"].assessment_id == "ASM-TECHNICAL"
    assert len(lineage["observations"]) == 2


def test_trace_risk(sample_graph_data):
    profile, claims, evidence, assessments = sample_graph_data
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    lineage = trace_risk(graph, "risk-1")
    assert lineage is not None
    assert lineage["risk"].risk_id == "risk-1"
    assert len(lineage["observations"]) == 1
    assert lineage["observations"][0]["observation"].observation_id == "obs-1"


def test_trace_question(sample_graph_data):
    profile, claims, evidence, assessments = sample_graph_data
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    lineage = trace_question(graph, "qst-1")
    assert lineage is not None
    assert lineage["question"].question_id == "qst-1"
    assert len(lineage["observations"]) == 1
    assert lineage["observations"][0]["observation"].observation_id == "obs-1"


def test_assessment_node_creation(sample_graph_data):
    profile, claims, evidence, assessments = sample_graph_data
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    asm_node = graph.assessments["ASM-TECHNICAL"]
    assert asm_node.expert_name == "TechnicalExpert"
    assert asm_node.domain == "technical"
    assert asm_node.agent_version == "1.0.0"
    
    # Generated relationship exists
    out_edges = graph.out_edges.get("ASM-TECHNICAL", [])
    assert len(out_edges) >= 4 # 2 observations + 1 risk + 1 question
    assert all(e.relationship == "GENERATED" for e in out_edges)


def test_cross_domain_traceability(sample_graph_data):
    profile, claims, evidence, assessments = sample_graph_data
    
    # Add a second assessment in the ip domain
    obs_ip = [DummyObservation("obs-ip-1", "IP patent claims corroborated.", ["claim-1"], ["ev-1"])]
    assessments.append(DummyAssessment("ip", obs_ip, [], []))
    
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    # Verify that obs-1 is linked to ASM-TECHNICAL, and obs-ip-1 is linked to ASM-IP
    assert "ASM-TECHNICAL" in graph.assessments
    assert "ASM-IP" in graph.assessments
    
    trace_tech = trace_assessment(graph, "ASM-TECHNICAL")
    trace_ip = trace_assessment(graph, "ASM-IP")
    
    assert len(trace_tech["observations"]) == 2
    assert len(trace_ip["observations"]) == 1


def test_duplicate_observation_linking(sample_graph_data):
    profile, claims, evidence, assessments = sample_graph_data
    
    # Create two semantically identical observations to trigger related linking
    obs1 = DummyObservation("obs-dup-1", "Founders own 100% equity.", ["claim-1"], ["ev-1"])
    obs2 = DummyObservation("obs-dup-2", "Founders own 100% equity.", ["claim-1"], ["ev-1"])
    assessments.append(DummyAssessment("ip", [obs1, obs2], [], []))
    
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    # Verify both remain distinct in the graph
    assert "obs-dup-1" in graph.observations
    assert "obs-dup-2" in graph.observations
    
    # Verify RELATED_TO edge is created between them
    edges = graph.out_edges.get("obs-dup-1", [])
    dup_edge = next((e for e in edges if e.target_id == "obs-dup-2" and e.relationship == "RELATED_TO" and e.state == "DUPLICATE"), None)
    assert dup_edge is not None
    
    # Verify consensus status
    assert graph.observations["obs-dup-1"].consensus_status == "corroborated"
    assert graph.observations["obs-dup-2"].consensus_status == "corroborated"


def test_graph_serialization(sample_graph_data):
    profile, claims, evidence, assessments = sample_graph_data
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    json_str = to_json(graph)
    assert json_str != ""
    
    rebuilt = from_json(json_str)
    assert rebuilt is not None
    assert rebuilt.graph_id == graph.graph_id
    assert len(rebuilt.documents) == 1
    assert len(rebuilt.evidence) == 2
    assert len(rebuilt.edges) == len(graph.edges)
    
    # Check cache pre-population
    assert len(rebuilt.provenance_cache) == len(graph.provenance_cache)


def test_large_graph_export(sample_graph_data):
    profile, claims, evidence, assessments = sample_graph_data
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    audit_trail = export_traceability(graph)
    assert isinstance(audit_trail, dict)
    assert "document" in audit_trail
    assert "evidence" in audit_trail
    assert "claim" in audit_trail
    assert "observation" in audit_trail
    assert "assessment" in audit_trail
    assert "risk" in audit_trail
    
    assert len(audit_trail["document"]) == 1
    assert len(audit_trail["evidence"]) == 2


def test_graph_integrity_hash(sample_graph_data):
    profile, claims, evidence, assessments = sample_graph_data
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    initial_hash = graph.graph_hash
    assert initial_hash != ""
    
    # Add a node, hash must change
    graph.documents["new-doc"] = DocumentNode(
        node_id="new-doc",
        node_type=NodeType.DOCUMENT,
        document_id="new-doc",
        document_name="New Doc",
        document_type="Deck",
        uploaded_at=datetime.utcnow()
    )
    
    new_hash = ObservationGraphBuilder._compute_hash(graph)
    assert new_hash != initial_hash


def test_assessment_outputs_query(sample_graph_data):
    profile, claims, evidence, assessments = sample_graph_data
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    outputs = get_assessment_outputs(graph, "ASM-TECHNICAL")
    assert outputs is not None
    assert len(outputs["observations"]) == 2
    assert len(outputs["risks"]) == 1
    assert len(outputs["questions"]) == 1


def test_domain_indexes(sample_graph_data):
    profile, claims, evidence, assessments = sample_graph_data
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    # Check O(1) lookups
    obs_ids = graph.observations_by_domain.get("technical")
    assert obs_ids is not None
    assert len(obs_ids) == 2
    assert "obs-1" in obs_ids
    
    asm_ids = graph.assessments_by_domain.get("technical")
    assert asm_ids == ["ASM-TECHNICAL"]
    
    risk_ids = graph.risks_by_category.get("technical")
    assert risk_ids == ["risk-1"]


def test_large_graph_performance():
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
        
    start_time = time.time()
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    build_time = time.time() - start_time
    
    # Graph Build Time < 2 seconds
    assert build_time < 2.0, f"Graph build took {build_time:.4f} seconds"
    
    # Traversal Performance < 100 ms
    start_time = time.time()
    for obs_id in list(graph.observations.keys())[:50]:
        trace_observation(graph, obs_id)
    traversal_time = time.time() - start_time
    assert traversal_time < 0.1, f"Lineage traversal took {traversal_time * 1000:.2f} ms"
    
    # Serialization Performance < 500 ms
    start_time = time.time()
    json_str = to_json(graph)
    serialization_time = time.time() - start_time
    assert serialization_time < 0.5, f"Serialization took {serialization_time * 1000:.2f} ms"
