import pytest
import time
import uuid
from datetime import datetime
from typing import Any
from app.modules.evaluation.graph import (
    NodeType, GraphNode, DocumentNode, EvidenceNode, ClaimNode,
    ObservationNode, AssessmentNode, ConflictNode, RiskNode,
    QuestionNode, Edge, GraphStatistics, ObservationGraph,
    ObservationGraphBuilder, GraphValidator
)
from app.modules.evaluation.correlation import (
    CorrelationNode, CorrelationEngine, CorrelationValidator,
    get_correlation, get_observation_correlations, get_corroborations,
    get_contradictions, get_dependencies, to_json, from_json
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

class DummyConflict:
    def __init__(self, id, explanation, claim1_id, claim2_id):
        self.id = id
        self.conflict_explanation = explanation
        self.conflict_type = "FACTUAL"
        self.confidence = 0.9
        self.created_at = "2026-06-24T12:00:00Z"
        self.preferred_claim_id = claim1_id
        self.superseded_claim_id = claim2_id


@pytest.fixture
def base_graph():
    docs = [DummyDocument("doc-1", "Standard Patent", "Patent")]
    profile = DummyProfile(docs)
    claims = [
        DummyClaim("claim-1", "technical_risk_claims", "TRL is unvalidated"),
        DummyClaim("claim-2", "market_risk_claims", "Target market is small"),
        DummyClaim("claim-3", "competition_claims", "Competitors have high market share"),
        DummyClaim("claim-4", "ip_claims", "IP is fully protected and registered")
    ]
    evidence = [
        DummyEvidence("ev-1", "claim-1", "doc-1"),
        DummyEvidence("ev-2", "claim-2", "doc-1"),
        DummyEvidence("ev-3", "claim-3", "doc-1"),
        DummyEvidence("ev-4", "claim-4", "doc-1")
    ]
    
    # 1. TRL / Product observations
    obs_trl = DummyObservation("obs-trl-1", "TRL level is low and unvalidated.", ["claim-1"], ["ev-1"])
    obs_prod = DummyObservation("obs-prod-1", "Product development has started.", ["claim-1"], ["ev-1"])
    asm_trl = DummyAssessment("trl", [obs_trl], [], [])
    asm_prod = DummyAssessment("product", [obs_prod], [], [])
    
    # 2. IP / Competition observations
    obs_ip = DummyObservation("obs-ip-1", "IP is fully registered.", ["claim-4"], ["ev-4"])
    obs_comp = DummyObservation("obs-comp-1", "Competitors dominate market.", ["claim-3"], ["ev-3"])
    asm_ip = DummyAssessment("ip", [obs_ip], [], [])
    asm_comp = DummyAssessment("competition", [obs_comp], [], [])

    # 3. Risk observation
    obs_risk = DummyObservation("obs-risk-1", "Founder commitment risk is high.", ["claim-2"], ["ev-2"])
    obs_founder = DummyObservation("obs-founder-1", "Founder works part-time.", ["claim-2"], ["ev-2"])
    asm_risk = DummyAssessment("risk", [obs_risk], [], [])
    asm_founder = DummyAssessment("founder", [obs_founder], [], [])
    
    assessments = [asm_trl, asm_prod, asm_ip, asm_comp, asm_risk, asm_founder]
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    return graph


def test_correlation_build_success(base_graph):
    # Correlate the graph
    graph = CorrelationEngine.correlate(base_graph)
    
    assert graph is not None
    assert len(graph.correlations) > 0
    
    # Verify via validator
    errors = CorrelationValidator.validate(graph)
    assert len(errors) == 0, f"Expected no correlation errors, got: {errors}"
    
    # Ensure stats are updated
    assert graph.graph_stats.correlation_count == len(graph.correlations)


def test_corroboration_detection():
    # Observations with semantic Jaccard similarity >= 0.90 across different domains
    docs = [DummyDocument("doc-1", "Doc 1", "PDF")]
    profile = DummyProfile(docs)
    claims = [
        DummyClaim("c-1", "claim", "Same claim content"),
        DummyClaim("c-2", "claim", "Same claim content")
    ]
    evidence = [
        DummyEvidence("e-1", "c-1", "doc-1"),
        DummyEvidence("e-2", "c-2", "doc-1")
    ]
    obs1 = DummyObservation("obs-1", "Founder is highly experienced in startup operations.", ["c-1"], ["e-1"])
    obs2 = DummyObservation("obs-2", "Founder is highly experienced in startup operations.", ["c-2"], ["e-2"])
    
    asm1 = DummyAssessment("founder", [obs1], [], [])
    asm2 = DummyAssessment("market", [obs2], [], [])
    
    graph = ObservationGraphBuilder.build(profile, claims, evidence, [asm1, asm2])
    graph = CorrelationEngine.correlate(graph)
    
    corrs = [c for c in graph.correlations.values() if c.correlation_type == "CORROBORATES"]
    assert len(corrs) >= 1
    assert any("obs-1" in c.description and "obs-2" in c.description for c in corrs)


def test_contradiction_detection():
    # Set up contradicting observations by conflicting claims via ConflictNode
    docs = [DummyDocument("doc-1", "Doc 1", "PDF")]
    profile = DummyProfile(docs)
    claims = [
        DummyClaim("c-1", "moat", "Moat is strong"),
        DummyClaim("c-2", "moat", "Moat is weak")
    ]
    evidence = [
        DummyEvidence("e-1", "c-1", "doc-1"),
        DummyEvidence("e-2", "c-2", "doc-1")
    ]
    obs1 = DummyObservation("obs-1", "Startup has a validated technology moat.", ["c-1"], ["e-1"])
    obs2 = DummyObservation("obs-2", "Startup has no technology moat.", ["c-2"], ["e-2"])
    
    asm1 = DummyAssessment("ip", [obs1], [], [])
    asm2 = DummyAssessment("competition", [obs2], [], [])
    
    conflict = DummyConflict("conf-1", "Factual conflict regarding moat existence", "c-1", "c-2")
    
    graph = ObservationGraphBuilder.build(profile, claims, evidence, [asm1, asm2], [conflict])
    graph = CorrelationEngine.correlate(graph)
    
    contradictions = [c for c in graph.correlations.values() if c.correlation_type == "CONTRADICTS"]
    assert len(contradictions) >= 1
    
    # Text-based contradiction detection (using positive/negative word mappings)
    # E.g. obs-1 ("validated ... moat") vs obs-2 ("no ... moat")
    assert any("obs-1" in c.description and "obs-2" in c.description for c in contradictions)


def test_dependency_detection(base_graph):
    graph = CorrelationEngine.correlate(base_graph)
    
    # trl + product => DEPENDS_ON
    depends = [c for c in graph.correlations.values() if c.correlation_type == "DEPENDS_ON"]
    assert len(depends) >= 1
    assert any("TRL Observation depends on Product validation" in c.description for c in depends)


def test_support_detection(base_graph):
    graph = CorrelationEngine.correlate(base_graph)
    
    # ip + competition => SUPPORTS
    supports = [c for c in graph.correlations.values() if c.correlation_type == "SUPPORTS"]
    assert len(supports) >= 1
    assert any("IP Observation supports competitive moat" in c.description for c in supports)


def test_weakening_detection(base_graph):
    graph = CorrelationEngine.correlate(base_graph)
    
    # risk + founder => WEAKENS
    weakens = [c for c in graph.correlations.values() if c.correlation_type == "WEAKENS"]
    assert len(weakens) >= 1
    assert any("Risk Observation weakens founder viability" in c.description for c in weakens)


def test_duplicate_detection():
    # Observations with semantic Jaccard similarity >= 0.90 in SAME domain
    docs = [DummyDocument("doc-1", "Doc 1", "PDF")]
    profile = DummyProfile(docs)
    claims = [
        DummyClaim("c-1", "founder", "Details on founder"),
        DummyClaim("c-2", "founder", "Details on founder")
    ]
    evidence = [
        DummyEvidence("e-1", "c-1", "doc-1"),
        DummyEvidence("e-2", "c-2", "doc-1")
    ]
    obs1 = DummyObservation("obs-1", "Founder is highly experienced.", ["c-1"], ["e-1"])
    obs2 = DummyObservation("obs-2", "Founder is highly experienced.", ["c-2"], ["e-2"])
    
    asm1 = DummyAssessment("founder", [obs1, obs2], [], [])
    
    graph = ObservationGraphBuilder.build(profile, claims, evidence, [asm1])
    graph = CorrelationEngine.correlate(graph)
    
    duplicates = [c for c in graph.correlations.values() if c.correlation_type == "DUPLICATES"]
    assert len(duplicates) >= 1


def test_invalid_correlation_type(base_graph):
    graph = CorrelationEngine.correlate(base_graph)
    
    # Manually inject invalid correlation type
    bad_corr = CorrelationNode(
        node_id="bad-corr",
        node_type=NodeType.CORRELATION,
        correlation_id="bad-corr",
        correlation_type="INVALID_TYPE",
        description="Bad correlation type.",
        confidence=0.8,
        created_at=datetime.utcnow().isoformat() + "Z"
    )
    graph.correlations["bad-corr"] = bad_corr
    
    # Inject 2 edges so cardinality checks pass, but type check fails
    edge1 = Edge(source_id="bad-corr", source_type=NodeType.CORRELATION, target_id="obs-trl-1", target_type=NodeType.OBSERVATION, relationship="RELATED_TO")
    edge2 = Edge(source_id="bad-corr", source_type=NodeType.CORRELATION, target_id="obs-prod-1", target_type=NodeType.OBSERVATION, relationship="RELATED_TO")
    graph.edges.extend([edge1, edge2])
    graph.out_edges.setdefault("bad-corr", []).extend([edge1, edge2])
    
    errors = CorrelationValidator.validate(graph)
    assert any("Invalid Correlation Type: 'INVALID_TYPE'" in err for err in errors)


def test_missing_observation(base_graph):
    graph = CorrelationEngine.correlate(base_graph)
    
    bad_corr = CorrelationNode(
        node_id="missing-obs-corr",
        node_type=NodeType.CORRELATION,
        correlation_id="missing-obs-corr",
        correlation_type="CORROBORATES",
        description="Bad reference.",
        confidence=0.8,
        created_at=datetime.utcnow().isoformat() + "Z"
    )
    graph.correlations["missing-obs-corr"] = bad_corr
    
    edge1 = Edge(source_id="missing-obs-corr", source_type=NodeType.CORRELATION, target_id="obs-trl-1", target_type=NodeType.OBSERVATION, relationship="RELATED_TO")
    edge2 = Edge(source_id="missing-obs-corr", source_type=NodeType.CORRELATION, target_id="non-existent-obs", target_type=NodeType.OBSERVATION, relationship="RELATED_TO")
    graph.edges.extend([edge1, edge2])
    graph.out_edges.setdefault("missing-obs-corr", []).extend([edge1, edge2])
    
    errors = CorrelationValidator.validate(graph)
    assert any("Broken Reference: Correlation 'missing-obs-corr' references non-existent observation 'non-existent-obs'" in err for err in errors)


def test_self_correlation(base_graph):
    graph = CorrelationEngine.correlate(base_graph)
    
    self_corr = CorrelationNode(
        node_id="self-corr",
        node_type=NodeType.CORRELATION,
        correlation_id="self-corr",
        correlation_type="CORROBORATES",
        description="Self correlation.",
        confidence=0.8,
        created_at=datetime.utcnow().isoformat() + "Z"
    )
    graph.correlations["self-corr"] = self_corr
    
    edge1 = Edge(source_id="self-corr", source_type=NodeType.CORRELATION, target_id="obs-trl-1", target_type=NodeType.OBSERVATION, relationship="RELATED_TO")
    edge2 = Edge(source_id="self-corr", source_type=NodeType.CORRELATION, target_id="obs-trl-1", target_type=NodeType.OBSERVATION, relationship="RELATED_TO")
    graph.edges.extend([edge1, edge2])
    graph.out_edges.setdefault("self-corr", []).extend([edge1, edge2])
    
    errors = CorrelationValidator.validate(graph)
    assert any("Self-Correlation: Correlation 'self-corr' references observation 'obs-trl-1' twice." in err for err in errors)


def test_get_correlations(base_graph):
    graph = CorrelationEngine.correlate(base_graph)
    
    # Retrieve using query helpers
    all_corrs = get_observation_correlations(graph, "obs-trl-1")
    assert len(all_corrs) > 0
    
    # Get specific correlation node
    corr_node = all_corrs[0]
    fetched = get_correlation(graph, corr_node.correlation_id)
    assert fetched == corr_node
    
    # Get corroborations, contradictions, dependencies
    corrobs = get_corroborations(graph, "obs-trl-1")
    contras = get_contradictions(graph, "obs-trl-1")
    deps = get_dependencies(graph, "obs-trl-1")
    
    assert isinstance(corrobs, list)
    assert isinstance(contras, list)
    assert isinstance(deps, list)


def test_correlation_serialization(base_graph):
    graph = CorrelationEngine.correlate(base_graph)
    
    json_str = to_json(graph)
    assert json_str != ""
    
    rebuilt = from_json(json_str)
    assert rebuilt is not None
    assert len(rebuilt.correlations) == len(graph.correlations)
    
    # Verify cached provenance and edges
    for cid in rebuilt.correlations:
        assert rebuilt.correlations[cid].node_type == NodeType.CORRELATION
        assert len(rebuilt.out_edges[cid]) == 2


def test_large_graph_correlation_performance():
    # Build large scale dataset:
    # 500 observations, 100 assessments
    docs = [DummyDocument(f"doc-1", f"Doc-1", "PDF")]
    profile = DummyProfile(docs)
    claims = [DummyClaim(f"claim-{i}", "domain", f"Value-{i}") for i in range(5)]
    evidence = [DummyEvidence(f"ev-{i}", f"claim-{i}", "doc-1") for i in range(5)]
    
    assessments = []
    for a in range(100):
        obs = [DummyObservation(f"obs-{a}-{o}", f"Observation test description {o}", [f"claim-{o}"], [f"ev-{o}"]) for o in range(5)]
        assessments.append(DummyAssessment(f"domain-{a}", obs, [], []))
        
    graph = ObservationGraphBuilder.build(profile, claims, evidence, assessments)
    
    start_time = time.time()
    graph = CorrelationEngine.correlate(graph)
    correlate_time = time.time() - start_time
    
    # Correlation Generation < 5 seconds
    assert correlate_time < 5.0, f"Correlation generation took {correlate_time:.4f} seconds"
    
    # Correlation traversal queries < 250 ms
    start_time = time.time()
    for obs_id in list(graph.observations.keys())[:50]:
        get_observation_correlations(graph, obs_id)
    traversal_time = time.time() - start_time
    assert traversal_time < 0.25, f"Correlation traversal query took {traversal_time * 1000:.2f} ms"
