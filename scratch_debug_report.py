import sys
import os
# Add TIDES-AI project path to sys.path
sys.path.insert(0, r"c:\Users\HP\Documents\AI aUTOMATION\TIDES-AI")

from app.modules.evaluation.graph import ObservationGraphBuilder, NodeType
from app.modules.reporting import ReportBuilder
from app.modules.explainability import ExplanationEngine
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

# Inlined sample_graph function
def get_sample_graph():
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

g = get_sample_graph()

print("Graph assessments keys:", list(g.assessments.keys()))
print("Graph observations keys:", list(g.observations.keys()))
print("Graph out_edges keys:", list(g.out_edges.keys()))

engine = ExplanationEngine()
exp_c = engine.explain_committee_decision(g, g.committee_decision.decision_id)
print("Lineage trace documents:", len(exp_c.lineage.documents))
print("Lineage trace claims:", len(exp_c.lineage.claims))
print("Lineage trace evidence:", len(exp_c.lineage.evidence))
print("Lineage trace observations:", len(exp_c.lineage.observations))
print("Lineage trace assessments:", len(exp_c.lineage.assessments))
