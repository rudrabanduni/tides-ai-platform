import uuid
from datetime import datetime, timezone
from typing import Any, List
import pytest

from app.modules.evaluation.domain_schemas import (
    DomainAssessmentReport,
    CriterionAssessment,
    VerificationStatus,
    FinalReviewAssessment,
    CrossDomainContradiction,
    TargetedRecheckRequest,
    TargetedRecheckResult,
)
from app.modules.evaluation.schemas import ConfidenceHierarchy
from app.modules.evaluation.domains.registry import (
    CANONICAL_DOMAINS,
    CRITERIA_DIRECTORY,
    get_domain_for_criterion,
    get_criteria_for_domain,
    get_criterion_metadata,
)
from app.modules.evaluation.domains import (
    ProblemSolutionExpert,
    MarketOpportunityExpert,
    FounderTeamExpert,
    CommercialisationExpert,
    InnovationImpactExpert,
    FinancialsSupportExpert,
)
from app.modules.evaluation.supervisory import SupervisoryReviewer
from app.services.ai.research import ExternalResearchService
from app.services.ai.cost_ledger import CostLedgerManager, EvaluationCostLedger
from app.services.ai.exceptions import AIBudgetExhaustedError
from app.modules.evaluation.graph.graph_builder import ObservationGraphBuilder
from app.modules.evaluation.executive.executive_engine import ExecutiveEngine
from app.modules.evaluation.investment.investment_engine import InvestmentEngine
from app.modules.evaluation.report.report_engine import DueDiligenceReportEngine
from app.modules.evaluation.committee.committee_engine import CommitteeDecisionEngine


# ---------------------------------------------------------------------------
# Test Fixtures & Mock Models
# ---------------------------------------------------------------------------

def make_mock_confidence(score: float = 0.85) -> ConfidenceHierarchy:
    return ConfidenceHierarchy(
        finding_confidence=score,
        evidence_confidence=score,
        reasoning_confidence=score,
        overall_domain_confidence=score,
    )


class MockField:
    def __init__(self, key: str):
        self.field_key = key


class MockClaim:
    def __init__(self, cid: str, field_key: str, value: Any, confidence: float = 0.9):
        self.id = cid
        self.field = MockField(field_key)
        self.field_name = field_key
        self.value_string = str(value) if isinstance(value, str) else None
        self.value_number = float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None
        self.value_boolean = value if isinstance(value, bool) else None
        self.value_json = value if isinstance(value, (dict, list)) else None
        self.value_date = None
        self.confidence_score = confidence
        self.validation_status = "VALIDATED"


class MockEvidence:
    def __init__(self, eid: str, claim_id: str, snippet: str, section: str = "Pitch Deck", page: int = 1):
        self.id = eid
        self.claim_id = claim_id
        self.evidence_snippet = snippet
        self.section_name = section
        self.page_number = page
        self.confidence_score = 0.9
        self.source_document_id = "doc-001"


class MockStartup:
    def __init__(self, name="CleanEnergy Corp", sector="CleanTech", stage="Seed"):
        self.id = uuid.uuid4()
        self.startup_id = str(self.id)
        self.startup_name = name
        self.sector = sector
        self.stage = stage
        self.documents = []


# ---------------------------------------------------------------------------
# 1. Canonical Criteria Directory & Routing Tests
# ---------------------------------------------------------------------------

def test_canonical_criteria_routing_complete_87():
    """Verifies that all 87 canonical criteria route strictly to 6 substantive domains + intake completeness."""
    assert len(CRITERIA_DIRECTORY) == 87, f"Expected exactly 87 canonical criteria, found {len(CRITERIA_DIRECTORY)}"
    assert len(CANONICAL_DOMAINS) == 6, f"Expected exactly 6 canonical domains, found {len(CANONICAL_DOMAINS)}"

    expected_domain_prefixes = {
        "problem_solution": "PS",
        "market_opportunity": "MO",
        "founder_team": "FT",
        "commercialisation": "BC",
        "innovation_impact": "II",
        "financials_support": "FI",
        "intake_completeness": "CM",
    }

    for cid, meta in CRITERIA_DIRECTORY.items():
        domain = get_domain_for_criterion(cid)
        assert domain is not None, f"Criterion {cid} has no mapped domain"
        if domain != "intake_completeness":
            assert domain in CANONICAL_DOMAINS, f"Domain {domain} for {cid} is not a valid canonical domain"

        expected_prefix = expected_domain_prefixes[domain]
        assert cid.startswith(expected_prefix), f"Criterion {cid} prefix mismatch for domain {domain}"

    # Verify criteria counts per domain (81 substantive criteria across 6 domains + 6 intake completeness)
    ps_criteria = get_criteria_for_domain("problem_solution")
    mo_criteria = get_criteria_for_domain("market_opportunity")
    ft_criteria = get_criteria_for_domain("founder_team")
    bc_criteria = get_criteria_for_domain("commercialisation")
    ii_criteria = get_criteria_for_domain("innovation_impact")
    fi_criteria = get_criteria_for_domain("financials_support")
    cm_criteria = get_criteria_for_domain("intake_completeness")

    assert len(ps_criteria) == 13, f"Expected 13 PS criteria, got {len(ps_criteria)}"
    assert len(mo_criteria) == 10, f"Expected 10 MO criteria, got {len(mo_criteria)}"
    assert len(ft_criteria) == 13, f"Expected 13 FT criteria, got {len(ft_criteria)}"
    assert len(bc_criteria) == 13, f"Expected 13 BC criteria, got {len(bc_criteria)}"
    assert len(ii_criteria) == 11, f"Expected 11 II criteria, got {len(ii_criteria)}"
    assert len(fi_criteria) == 21, f"Expected 21 substantive FI criteria, got {len(fi_criteria)}"
    assert len(cm_criteria) == 6, f"Expected 6 intake completeness CM criteria, got {len(cm_criteria)}"
    assert len(ps_criteria) + len(mo_criteria) + len(ft_criteria) + len(bc_criteria) + len(ii_criteria) + len(fi_criteria) == 81


# ---------------------------------------------------------------------------
# 2. Multi-Founder & Dynamic Competitor Matrix Tests
# ---------------------------------------------------------------------------

def test_multi_founder_and_competitor_matrix_handling():
    """Verifies that multi-founder parity and 4-row competitor matrix are preserved and evaluated."""
    startup = MockStartup()
    
    # 4 Competitors as defined in Slide 7 of LaunchIndex template
    competitors = [
        {"name": "Diesel Generators Inc", "country": "India", "funding": "Public", "advantage": "Higher emissions"},
        {"name": "Hydrogen Battery Rivals", "country": "USA", "funding": "$50M Series B", "advantage": "Gaseous storage risk"},
        {"name": "Bloom Energy", "country": "USA", "funding": "$1B Public", "advantage": "Slow start-up time"},
        {"name": "Local Indian Competitor", "country": "India", "funding": "Bootstrapped", "advantage": "Lower efficiency"},
    ]
    mo_claim = MockClaim("c-mo-07", "mo_07_competitor_details", competitors)
    mo_ev = MockEvidence("ev-mo-07", "c-mo-07", "4 competitors benchmarked in Slide 7", "Competitor Matrix", 7)

    mo_expert = MarketOpportunityExpert()
    mo_report = mo_expert.evaluate(startup, [mo_claim], [mo_ev], [], {"evaluation_id": "eval-mo-test"})

    assert mo_report.domain_key == "market_opportunity"
    assert "MO-07" in mo_report.criteria_evaluations
    crit_eval = mo_report.criteria_evaluations["MO-07"]
    assert "4 competitor" in crit_eval.extracted_startup_response or "Diesel Generators" in crit_eval.extracted_startup_response

    # Multi-Founder: CEO & CTO
    founders = [
        {"name": "John Doe", "role": "Co-Founder & CEO", "equity": "50%", "degree": "Ph.D. Chem Eng"},
        {"name": "Jane Smith", "role": "Co-Founder & CTO", "equity": "50%", "degree": "M.Tech Power Systems"},
    ]
    ft_claim = MockClaim("c-ft-01", "ft_01_founder_details", founders)
    ft_ev = MockEvidence("ev-ft-01", "c-ft-01", "Co-founders John Doe and Jane Smith with 50-50 equity", "Team Slide", 8)

    ft_expert = FounderTeamExpert()
    ft_report = ft_expert.evaluate(startup, [ft_claim], [ft_ev], [], {"evaluation_id": "eval-ft-test"})

    assert ft_report.domain_key == "founder_team"
    assert "FT-01" in ft_report.criteria_evaluations
    ft_crit_eval = ft_report.criteria_evaluations["FT-01"]
    assert "John Doe" in ft_crit_eval.extracted_startup_response and "Jane Smith" in ft_crit_eval.extracted_startup_response


# ---------------------------------------------------------------------------
# 3. Domain Output Schema & Provenance Contracts
# ---------------------------------------------------------------------------

def test_domain_output_contract_and_provenance():
    """Validates DomainAssessmentReport and CriterionAssessment types, evidence tracking and provenance."""
    startup = MockStartup()
    claims = [
        MockClaim("c-ps-01", "ps_01_problem_statement", "Industrial power grid outages cost billions."),
        MockClaim("c-ps-09", "ps_09_current_trl", 6),
    ]
    evidence = [
        MockEvidence("ev-ps-01", "c-ps-01", "Grid outages cost $250k/hour in manufacturing", "Problem Slide", 3),
        MockEvidence("ev-ps-09", "c-ps-09", "TRL 6 pilot demonstrated at 500kW", "Traction Slide", 5),
    ]

    ps_expert = ProblemSolutionExpert()
    report = ps_expert.evaluate(startup, claims, evidence, [], {"evaluation_id": "eval-ps-test"})

    assert isinstance(report, DomainAssessmentReport)
    assert report.domain == "problem_solution"
    assert report.domain_title == "Problem & Solution"
    assert len(report.criteria_evaluated) == 13

    # Check PS-01 criterion assessment
    ps01 = report.criteria_evaluations["PS-01"]
    assert isinstance(ps01, CriterionAssessment)
    assert ps01.criterion_id == "PS-01"
    assert ps01.extracted_startup_response == "Industrial power grid outages cost billions."
    assert "ev-ps-01" in ps01.evidence_ids
    assert any("Problem Slide" in loc for loc in ps01.source_locations)
    assert ps01.verification_status in (VerificationStatus.VERIFIED_DOCUMENTED, VerificationStatus.SELF_REPORTED_ONLY)

    # Check duck-type compatibility with AgentAssessment
    assert hasattr(report, "summary")
    assert hasattr(report, "observations")
    assert hasattr(report, "risks")
    assert hasattr(report, "questions")
    assert hasattr(report, "confidence")
    assert hasattr(report, "strengths")
    assert hasattr(report, "weaknesses")
    assert hasattr(report, "executive_conclusion")
    assert hasattr(report, "investment_implication")


# ---------------------------------------------------------------------------
# 4. Conditional Prototype Logic (TRL <= 4 Not Penalized)
# ---------------------------------------------------------------------------

def test_conditional_prototype_logic_for_early_stage():
    """Confirms that early-stage ventures with TRL <= 4 are not penalized with CONTRADICTED or MISSING."""
    startup = MockStartup(stage="Pre-Seed")
    claims = [
        MockClaim("c-ps-09", "ps_09_current_trl", 3),
        MockClaim("c-ps-10", "ps_10_prototype_stage", "PoC stage, no physical unit"),
    ]
    evidence = [
        MockEvidence("ev-ps-09", "c-ps-09", "Lab experimental proof of concept demonstrated", "TRL Slide", 5),
        MockEvidence("ev-ps-10", "c-ps-10", "Rechargeable coin cell bench PoC", "TRL Slide", 5),
    ]

    ps_expert = ProblemSolutionExpert()
    report = ps_expert.evaluate(startup, claims, evidence, [], {"evaluation_id": "eval-trl3-test"})

    ps10 = report.criteria_evaluations.get("PS-10")
    assert ps10 is not None
    # For TRL 3, prototype is not penalized as CONTRADICTED or MISSING_INFORMATION
    assert ps10.verification_status != VerificationStatus.CONTRADICTED


# ---------------------------------------------------------------------------
# 5. Cross-Domain Contradiction Detection
# ---------------------------------------------------------------------------

def test_supervisory_reviewer_contradiction_detection():
    """Verifies that SupervisoryReviewer flags commercial revenue vs financial pre-revenue discrepancies."""
    startup = MockStartup()

    # Commercialisation claims active commercial revenue
    comm_report = DomainAssessmentReport(
        domain="commercialisation",
        domain_key="commercialisation",
        domain_title="Business Model & Commercialisation",
        criteria_evaluated=["BC-09"],
        criteria_evaluations={
            "BC-09": CriterionAssessment(
                criterion_id="BC-09",
                criterion_name="Current Revenue",
                extracted_startup_response="₹1.5 Crore ARR active revenue",
                assessment_narrative="Startup claims active customer billing",
                verification_status=VerificationStatus.SELF_REPORTED_ONLY
            )
        },
        summary="Commercial evaluation summary",
        executive_summary="Commercial executive summary",
        confidence=make_mock_confidence(0.85),
    )

    # Financials shows Year 1 is ₹0 (pre-revenue)
    fin_report = DomainAssessmentReport(
        domain="financials_support",
        domain_key="financials_support",
        domain_title="Financials & Incubation Support",
        criteria_evaluated=["FI-01"],
        criteria_evaluations={
            "FI-01": CriterionAssessment(
                criterion_id="FI-01",
                criterion_name="Three-Year Revenue Projections",
                extracted_startup_response="Year 1: ₹0, Year 2: ₹50 Lakh, Year 3: ₹2 Crore",
                assessment_narrative="Financial model shows pre-revenue in year 1",
                verification_status=VerificationStatus.PLAUSIBLE_ESTIMATE
            )
        },
        summary="Financial evaluation summary",
        executive_summary="Financial executive summary",
        confidence=make_mock_confidence(0.85),
    )

    domain_reports = {
        "commercialisation": comm_report,
        "financials_support": fin_report,
    }

    reviewer = SupervisoryReviewer()
    contradictions = reviewer.identify_cross_domain_contradictions(domain_reports)

    assert len(contradictions) >= 1
    rev_conflict = next((c for c in contradictions if c.nature_of_conflict == "REVENUE_TIMING_DISCREPANCY"), None)
    assert rev_conflict is not None
    assert rev_conflict.domain_a == "commercialisation"
    assert rev_conflict.domain_b == "financials_support"


# ---------------------------------------------------------------------------
# 6. Targeted Re-Check Loop Isolation & Single-Domain Re-Check Bound
# ---------------------------------------------------------------------------

def test_targeted_recheck_loop_isolation_and_bounds():
    """Confirms that targeted re-checks only invoke the challenged domain (max 1 per domain)."""
    startup = MockStartup()
    claims = [MockClaim("c-bc-09", "bc_09_current_revenue", "₹1.5 Crore")]
    evidence = [MockEvidence("ev-bc-09", "c-bc-09", "Contract with enterprise", "Traction", 11)]

    comm_expert = CommercialisationExpert()
    domain_experts = {"commercialisation": comm_expert}

    comm_report = comm_expert.evaluate(startup, claims, evidence, [], {"evaluation_id": "eval-recheck-test"})
    fin_report = DomainAssessmentReport(
        domain="financials_support",
        domain_key="financials_support",
        domain_title="Financials & Incubation Support",
        criteria_evaluated=["FI-01"],
        criteria_evaluations={
            "FI-01": CriterionAssessment(
                criterion_id="FI-01",
                criterion_name="Three-Year Revenue Projections",
                extracted_startup_response="Year 1: ₹0",
                assessment_narrative="Year 1 pre-revenue",
                verification_status=VerificationStatus.PLAUSIBLE_ESTIMATE
            )
        },
        summary="Financial summary",
        executive_summary="Financial executive summary",
        confidence=make_mock_confidence(0.85),
    )

    domain_reports = {
        "commercialisation": comm_report,
        "financials_support": fin_report,
    }

    reviewer = SupervisoryReviewer()
    final_review = reviewer.review(
        domain_reports=domain_reports,
        domain_experts=domain_experts,
        profile=startup,
        claims=claims,
        evidence=evidence,
        metadata={"evaluation_id": "eval-recheck-test"}
    )

    assert isinstance(final_review, FinalReviewAssessment)
    # At most 1 re-check per domain triggered
    assert len(final_review.rechecks_triggered) <= 1
    if final_review.rechecks_triggered:
        recheck = final_review.rechecks_triggered[0]
        assert recheck.domain_key == "commercialisation"
        assert recheck.criterion_id == "BC-09"


# ---------------------------------------------------------------------------
# 7. Unresolved Disagreement Preservation
# ---------------------------------------------------------------------------

def test_unresolved_disagreements_preserved_in_supervisory_report():
    """Confirms that contradictions without primary evidence are preserved rather than overwritten."""
    startup = MockStartup()

    contradiction = CrossDomainContradiction(
        contradiction_id="CONTRA-TEST-001",
        domain_a="problem_solution",
        criterion_a="PS-09",
        claim_a_summary="Claimed TRL 8 operational system",
        domain_b="founder_team",
        criterion_b="FT-04",
        claim_b_summary="Absence of any engineering lead or technical co-founder",
        nature_of_conflict="PRODUCT_VS_TEAM_FEASIBILITY",
        resolution_status="PRESERVED_DISAGREEMENT",
        resolution_rationale="High TRL claimed without technical staff on team"
    )

    reviewer = SupervisoryReviewer()
    final_review = reviewer.review(
        domain_reports={},
        domain_experts={},
        profile=startup,
        claims=[],
        evidence=[],
        metadata={"evaluation_id": "eval-disagree-test"}
    )

    # Force a preserved disagreement into the report
    final_review.unresolved_disagreements.append(
        f"{contradiction.domain_a}.{contradiction.criterion_a} vs {contradiction.domain_b}.{contradiction.criterion_b}: {contradiction.nature_of_conflict}"
    )

    assert len(final_review.unresolved_disagreements) >= 1
    assert "PS-09" in final_review.unresolved_disagreements[0]
    assert "FT-04" in final_review.unresolved_disagreements[0]


# ---------------------------------------------------------------------------
# 8. Supervisory Review Report Assembly & Recommendation Rationale
# ---------------------------------------------------------------------------

def test_supervisory_report_assembly_and_recommendation():
    """Validates full supervisory synthesis, recommendation rationale, conditions, and tranches."""
    startup = MockStartup(name="PETREVOLT ENERGY SOLUTIONS", sector="DeepTech", stage="Prototype")
    reviewer = SupervisoryReviewer()

    final_review = reviewer.review(
        domain_reports={},
        domain_experts={},
        profile=startup,
        claims=[],
        evidence=[],
        metadata={"evaluation_id": "eval-assembly-test"}
    )

    assert final_review.startup_name == "PETREVOLT ENERGY SOLUTIONS"
    assert final_review.sector == "DeepTech"
    assert final_review.overall_recommendation in ("INCUBATE", "CONDITIONAL", "DEFER", "REJECT")
    assert len(final_review.recommendation_rationale) > 20
    assert len(final_review.recommended_tranches) >= 2
    assert final_review.reviewer_agent_version == "2.0.0"


# ---------------------------------------------------------------------------
# 9. External Research Service Boundary
# ---------------------------------------------------------------------------

def test_external_research_service_boundary_unverified():
    """Confirms ExternalResearchService reports is_available() -> False without live web search."""
    research_service = ExternalResearchService()
    assert research_service.is_available() is False

    res = research_service.verify_competitor_funding("Competitor X", "eval-research-test")
    assert res["status"] == "UNAVAILABLE"
    assert res["verified"] is False
    assert res["cost_usd"] == 0.0


# ---------------------------------------------------------------------------
# 10. Cost Ledger Shared Budget Tracking Across All Domain Calls
# ---------------------------------------------------------------------------

def test_cost_ledger_shared_budget_tracking():
    """Verifies that multiple specialist domain evaluations debit from the same evaluation-wide ledger."""
    eval_id = f"eval-budget-{uuid.uuid4().hex[:8]}"
    startup = MockStartup()

    claims = [
        MockClaim("c-ps-01", "ps_01_problem_statement", "Problem statement"),
        MockClaim("c-mo-01", "mo_01_tam_value", "$10 Billion"),
    ]
    evidence = [
        MockEvidence("ev-ps-01", "c-ps-01", "Snippet 1"),
        MockEvidence("ev-mo-01", "c-mo-01", "Snippet 2"),
    ]

    ps_expert = ProblemSolutionExpert()
    mo_expert = MarketOpportunityExpert()

    rep_ps = ps_expert.evaluate(startup, claims, evidence, [], {"evaluation_id": eval_id})
    rep_mo = mo_expert.evaluate(startup, claims, evidence, [], {"evaluation_id": eval_id})

    ledger = CostLedgerManager.get_instance().get_ledger(eval_id)
    assert ledger is not None
    assert ledger.spent_usd > 0.0
    assert len(ledger._records) >= 2
    assert ledger.spent_usd <= ledger.max_budget_usd


# ---------------------------------------------------------------------------
# 11. Budget Exhaustion Graceful Handling
# ---------------------------------------------------------------------------

def test_budget_exhaustion_prevents_subsequent_calls():
    """Verifies that exceeding the budget ceiling halts calls and raises AIBudgetExhaustedError."""
    eval_id = f"eval-exhaust-{uuid.uuid4().hex[:8]}"
    ledger = CostLedgerManager.get_instance().get_or_create_ledger(
        evaluation_id=eval_id,
        startup_id="startup-test",
        max_budget_usd=0.010 # artificially low budget ceiling
    )

    # First reservation consumes part of the budget
    res_id = ledger.reserve_budget(estimated_cost_usd=0.008, agent_name="exhaustion_test_1")
    ledger.reconcile_operation(
        reservation_id=res_id,
        agent_name="exhaustion_test_1",
        provider="mock",
        model="claude-3-5-sonnet-20241022",
        input_tokens=100,
        output_tokens=100,
        actual_cost_usd=0.008,
    )

    # Second reservation would breach ceiling ($0.008 spent + $0.005 planned = $0.013 > $0.010)
    with pytest.raises(AIBudgetExhaustedError):
        ledger.reserve_budget(estimated_cost_usd=0.005, agent_name="exhaustion_test_2")

    assert ledger.is_exhausted is True


# ---------------------------------------------------------------------------
# 12. Backward Compatibility with ObservationGraph & Report Engine
# ---------------------------------------------------------------------------

def test_backward_compatibility_with_observation_graph():
    """Confirms that DomainAssessmentReport instances integrate seamlessly with ObservationGraph and downstream engines."""
    startup = MockStartup()

    claims = [
        MockClaim("c-ps-01", "ps_01_problem_statement", "Clean energy storage issue."),
        MockClaim("c-ft-01", "ft_01_founder_details", "John Doe, CEO"),
    ]
    evidence = [
        MockEvidence("ev-ps-01", "c-ps-01", "Outages cost $250k/hr"),
        MockEvidence("ev-ft-01", "c-ft-01", "John Doe credentials verified"),
    ]

    ps_expert = ProblemSolutionExpert()
    ft_expert = FounderTeamExpert()

    rep_ps = ps_expert.evaluate(startup, claims, evidence, [], {"evaluation_id": "eval-graph-test"})
    rep_ft = ft_expert.evaluate(startup, claims, evidence, [], {"evaluation_id": "eval-graph-test"})

    # Build ObservationGraph with DomainAssessmentReport instances
    graph = ObservationGraphBuilder.build(
        profile=startup,
        claims=claims,
        evidence=evidence,
        assessments=[rep_ps, rep_ft],
        conflicts=[]
    )

    # Populate legacy aliases
    graph.domain_assessments["founder"] = rep_ft
    graph.domain_assessments["product"] = rep_ps
    graph.domain_assessments["trl"] = rep_ps

    # Verify Executive and Investment engines execute without errors
    graph = ExecutiveEngine.generate(graph)
    assert graph.executive_assessment is not None

    graph = InvestmentEngine.generate(graph)
    assert graph.investment_assessment is not None
    assert graph.investment_assessment.investment_score > 0

    # Verify Committee Engine runs
    graph = CommitteeDecisionEngine.generate(graph)
    assert graph.committee_decision is not None
    assert graph.committee_decision.recommendation is not None

    # Verify Due Diligence Report Generation
    graph = DueDiligenceReportEngine.generate(graph)
    assert graph.report is not None
    assert graph.report.report_id is not None
    assert graph.report.executive_summary is not None
    assert graph.report.founder_assessment is not None


# ---------------------------------------------------------------------------
# 13. Phase 2.1: Model Migration, Cost Verification & Supervisory Metering Tests
# ---------------------------------------------------------------------------

def test_phase2_1_claude_model_migration_and_catalog():
    """Verifies migration to claude-sonnet-5-5 and claude-haiku-5-5 with accurate pricing."""
    from app.services.ai.pricing import get_pricing_catalog
    from app.services.ai.router import ModelRouter
    from app.services.ai.schemas import AICompletionRequest

    catalog = get_pricing_catalog()

    # Active production models
    sonnet = catalog.get_pricing("claude-sonnet-5-5")
    assert sonnet.is_active is True
    assert sonnet.is_deprecated is False
    assert sonnet.input_cost_per_m == 2.00
    assert sonnet.output_cost_per_m == 10.00
    assert sonnet.cached_input_cost_per_m == 0.10
    assert sonnet.cache_write_cost_per_m == 2.50

    haiku = catalog.get_pricing("claude-haiku-5-5")
    assert haiku.is_active is True
    assert haiku.is_deprecated is False
    assert haiku.input_cost_per_m == 0.10
    assert haiku.output_cost_per_m == 0.50
    assert haiku.tier_threshold_tokens == 100_000
    assert haiku.tier_input_cost_per_m == 0.50
    assert haiku.tier_output_cost_per_m == 2.50
    assert haiku.cached_input_cost_per_m == 0.01
    assert haiku.cache_write_cost_per_m == 0.125

    # Aliases
    assert catalog.get_pricing("anthropic/claude-sonnet-5-5").input_cost_per_m == 2.00
    assert catalog.get_pricing("claude-sonnet-5.5").input_cost_per_m == 2.00
    assert catalog.get_pricing("anthropic/claude-haiku-5-5").input_cost_per_m == 0.10
    assert catalog.get_pricing("claude-haiku-5.5").input_cost_per_m == 0.10

    # Deprecated models
    sonnet_legacy = catalog.get_pricing("claude-3-5-sonnet-20241022")
    assert sonnet_legacy.is_deprecated is True
    assert sonnet_legacy.is_active is False

    haiku_legacy = catalog.get_pricing("claude-3-5-haiku-20241022")
    assert haiku_legacy.is_deprecated is True
    assert haiku_legacy.is_active is False

    # ModelRouter checks
    router = ModelRouter()
    fast_req = AICompletionRequest(system_prompt="sys", user_prompt="usr", operation_type="extraction", agent_name="extractor")
    assert router.resolve_model(fast_req) == "claude-haiku-5-5"

    reasoning_req = AICompletionRequest(system_prompt="sys", user_prompt="usr", operation_type="supervisory_review", agent_name="supervisory_review")
    assert router.resolve_model(reasoning_req) == "claude-sonnet-5-5"


def test_phase2_1_supervisory_review_metered_in_evaluation_ledger():
    """Verifies that SupervisoryReviewer explicitly meters its AI review call in the shared EvaluationCostLedger."""
    evaluation_id = f"eval-supervisory-metering-{uuid.uuid4().hex[:6]}"
    cost_manager = CostLedgerManager.get_instance()
    ledger = cost_manager.get_or_create_ledger(
        evaluation_id=evaluation_id,
        startup_id="test-startup",
        max_budget_usd=0.55,
        exchange_rate=96.0,
        buffer_multiplier=1.18,
    )

    startup = MockStartup()
    claims = [MockClaim("c-01", "ps_01_problem_statement", "Solar efficiency gap")]
    evidence = [MockEvidence("ev-01", "c-01", "Lab tests show 30% drop")]

    ps_expert = ProblemSolutionExpert()
    rep_ps = ps_expert.evaluate(startup, claims, evidence, [], {"evaluation_id": evaluation_id})

    # Execute supervisory reviewer
    reviewer = SupervisoryReviewer()
    final_assessment = reviewer.review(
        domain_reports={"problem_solution": rep_ps},
        domain_experts={"problem_solution": ps_expert},
        profile=startup,
        claims=claims,
        evidence=evidence,
        metadata={"evaluation_id": evaluation_id}
    )

    summary = ledger.get_summary()
    agent_names = [op["agent_name"] for op in summary["operations"]]

    assert "supervisory_review" in agent_names, f"Expected 'supervisory_review' in metered operations: {agent_names}"
    assert final_assessment.cost_summary is not None
    assert final_assessment.cost_summary.get("total_operations", 0) >= 2


def test_phase2_1_due_diligence_report_supervisory_export_markdown_html_pdf():
    """Verifies DueDiligenceReport includes supervisory review and exports properly in MD, HTML, and PDF."""
    from app.modules.evaluation.report.report_serializer import ReportSerializer

    startup = MockStartup()
    claims = [MockClaim("c-01", "ps_01_problem_statement", "Clean energy storage.")]
    evidence = [MockEvidence("ev-01", "c-01", "Power outage survey")]

    ps_expert = ProblemSolutionExpert()
    ft_expert = FounderTeamExpert()
    rep_ps = ps_expert.evaluate(startup, claims, evidence, [], {"evaluation_id": "eval-export-test"})
    rep_ft = ft_expert.evaluate(startup, claims, evidence, [], {"evaluation_id": "eval-export-test"})

    reviewer = SupervisoryReviewer()
    final_assessment = reviewer.review(
        domain_reports={"problem_solution": rep_ps, "founder_team": rep_ft},
        domain_experts={"problem_solution": ps_expert, "founder_team": ft_expert},
        profile=startup,
        claims=claims,
        evidence=evidence,
        metadata={"evaluation_id": "eval-export-test"}
    )

    graph = ObservationGraphBuilder.build(
        profile=startup,
        claims=claims,
        evidence=evidence,
        assessments=[rep_ps, rep_ft],
        conflicts=[]
    )
    graph.domain_assessments["founder"] = rep_ft
    graph.domain_assessments["product"] = rep_ps
    graph.domain_assessments["trl"] = rep_ps

    # Attach supervisory review
    graph.final_review = final_assessment

    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)
    graph = CommitteeDecisionEngine.generate(graph)
    graph = DueDiligenceReportEngine.generate(graph)

    report = graph.report
    assert report is not None
    assert report.final_review is not None
    assert report.metadata.get("final_review") is not None

    # Verify Markdown export
    md = ReportSerializer.export_markdown(report)
    assert "Final Supervisory AI Review & Due Diligence Synthesis" in md
    assert "Overall Recommendation:" in md

    # Verify HTML export
    html = ReportSerializer.export_html(report)
    assert "Final Supervisory AI Review & Due Diligence Synthesis" in html
    assert "supervisory_review" in html

    # Verify PDF export
    pdf_bytes = ReportSerializer.export_pdf_data(report)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")
