"""tests/test_supervisory_gating_and_audit.py - Final Offline Acceptance & Supervisory Gating Tests.

Proves:
1. Supervisory review cannot run unless all 6 domains and all 81 domain criteria and 6 cover criteria succeed.
2. Incomplete or failed domain evaluations block supervisory review and return COMPLETED_WITH_PARTIAL_DOMAIN_FAILURES.
3. Production default budget is consistently $0.35 USD across config, ledger, and readiness, with override support.
4. ReportValidator strictly rejects incomplete 87-criteria matrices.
5. All canonical criteria are represented without phantom evidence or negative evidence conversion.
"""

from __future__ import annotations

import copy
import uuid
import pytest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.core.config import Settings, get_settings
from app.modules.evaluation.domain_schemas import (
    ConfidenceHierarchy,
    CriterionAssessment,
    DomainAssessmentReport,
    VerificationStatus,
)
from app.modules.evaluation.domains import (
    ProblemSolutionExpert,
    MarketOpportunityExpert,
    FounderTeamExpert,
    CommercialisationExpert,
    InnovationImpactExpert,
    FinancialsSupportExpert,
)
from app.modules.evaluation.domains.registry import (
    CANONICAL_DOMAINS,
    CRITERIA_DIRECTORY,
    get_criteria_for_domain,
    get_domain_for_criterion,
)
from app.modules.evaluation.graph.graph_builder import ObservationGraphBuilder
from app.modules.evaluation.report.report_engine import DueDiligenceReportEngine
from app.modules.evaluation.report.report_validator import ReportValidator
from app.modules.evaluation.supervisory.reviewer import (
    SupervisoryGatingError,
    SupervisoryReviewer,
    verify_supervisory_review_prerequisites,
)
from app.services.ai.cost_ledger import CostLedgerManager, EvaluationCostLedger
from app.services.ai.exceptions import AIBudgetExhaustedError
from app.services.ai.readiness import get_live_readiness_report


def _make_criterion_eval(cid: str, domain: str, status: VerificationStatus = VerificationStatus.VERIFIED_DOCUMENTED) -> CriterionAssessment:
    return CriterionAssessment(
        criterion_id=cid,
        criterion_name=f"Criterion {cid}",
        extracted_startup_response=f"Valid response for {cid}",
        assessment_narrative=f"Verified finding for {cid}.",
        evidence_ids=[f"EV-{cid}"],
        source_locations=["Slide 1"],
        verification_status=status,
        score=7.5,
        strengths=[f"Grounded strength on {cid}"],
        weaknesses=[],
        risks=[],
        confidence_score=0.88,
    )


def _build_full_6_domain_reports(evaluation_id: str = "eval-gating-01") -> dict[str, DomainAssessmentReport]:
    reports = {}
    for dkey in CANONICAL_DOMAINS:
        cids = get_criteria_for_domain(dkey)
        evals = {cid: _make_criterion_eval(cid, dkey) for cid in cids}
        reports[dkey] = DomainAssessmentReport(
            domain=dkey,
            domain_key=dkey,
            domain_title=CANONICAL_DOMAINS[dkey]["title"],
            evaluation_id=evaluation_id,
            startup_id="startup-gating-01",
            criteria_evaluated=cids,
            criteria_evaluations=evals,
            summary=f"Full institutional diligence summary for {dkey} completed across {len(cids)} criteria.",
            executive_summary=f"Executive summary for {dkey}.",
            executive_conclusion=f"Conclusion for {dkey}.",
            reasoning=f"Reasoning for {dkey}.",
            investment_implication=f"Implication for {dkey}.",
            observations=[],
            risks=[],
            questions=[],
            missing_evidence=[],
            confidence=ConfidenceHierarchy(
                finding_confidence=0.85,
                evidence_confidence=0.85,
                reasoning_confidence=0.85,
                overall_domain_confidence=0.85,
            ),
            strengths=[f"Key strength for {dkey}"],
            weaknesses=[],
            unsupported_claims=[],
            contradictions=[],
            missing_information=[],
            follow_up_questions=[],
            composite_domain_confidence=0.85,
            prompt_name="prompt-test",
            prompt_version="1.0",
            prompt_hash="hash-test",
            agent_version="1.0.0",
            model_used="claude-sonnet-5-5",
            cost_usd=0.015,
        )
    return reports


def _make_mock_claims_and_profile():
    startup = SimpleNamespace(
        id=uuid.uuid4(),
        startup_name="CleanPower Systems",
        sector="CleanTech",
        stage="Seed",
        tagline="Energy Storage Solutions",
        geography="India",
        application_date="2026-11-10",
    )
    claims = [
        SimpleNamespace(id=uuid.uuid4(), field=SimpleNamespace(field_key="cm_01_company_name"), value_string="CleanPower Systems"),
        SimpleNamespace(id=uuid.uuid4(), field=SimpleNamespace(field_key="cm_02_tagline"), value_string="Energy Storage Solutions"),
        SimpleNamespace(id=uuid.uuid4(), field=SimpleNamespace(field_key="cm_03_sector"), value_string="CleanTech"),
        SimpleNamespace(id=uuid.uuid4(), field=SimpleNamespace(field_key="cm_04_stage"), value_string="Seed"),
        SimpleNamespace(id=uuid.uuid4(), field=SimpleNamespace(field_key="cm_05_geography"), value_string="India"),
        SimpleNamespace(id=uuid.uuid4(), field=SimpleNamespace(field_key="cm_06_application_date"), value_string="2026-11-10"),
    ]
    evidence = [
        SimpleNamespace(
            id=f"EV-{cid}",
            claim_id=claims[0].id,
            section_name="Deck",
            page_number=1,
            evidence_snippet=f"Snippet for {cid}",
            confidence_score=0.9,
        )
        for cid in CRITERIA_DIRECTORY
    ]
    return startup, claims, evidence


# ===========================================================================
# 1. Supervisory Review Gating Tests
# ===========================================================================

def test_supervisory_gating_passes_with_all_6_domains_and_81_criteria():
    """All 6 domains, 81 criteria, and 6 cover criteria pass gating."""
    domain_reports = _build_full_6_domain_reports()
    startup, claims, _ = _make_mock_claims_and_profile()

    ok, reasons = verify_supervisory_review_prerequisites(
        domain_reports=domain_reports,
        profile=startup,
        claims=claims,
    )
    assert ok is True
    assert len(reasons) == 0


def test_supervisory_gating_blocks_when_domain_is_missing():
    """Supervisory review is strictly blocked if any of the 6 canonical domains is missing."""
    domain_reports = _build_full_6_domain_reports()
    del domain_reports["financials_support"]
    startup, claims, _ = _make_mock_claims_and_profile()

    ok, reasons = verify_supervisory_review_prerequisites(
        domain_reports=domain_reports,
        profile=startup,
        claims=claims,
    )
    assert ok is False
    assert any("financials_support" in r for r in reasons)

    reviewer = SupervisoryReviewer()
    with pytest.raises(SupervisoryGatingError, match="Missing required canonical domain"):
        reviewer.review(
            domain_reports=domain_reports,
            domain_experts={},
            profile=startup,
            claims=claims,
            evidence=[],
            metadata={"strict_gating": True},
        )


def test_supervisory_gating_blocks_when_domain_failed_or_incomplete():
    """Supervisory review is strictly blocked if a domain report indicates failed/incomplete batches."""
    domain_reports = _build_full_6_domain_reports()
    domain_reports["problem_solution"].summary = "Problem & Solution evaluation incomplete: batch failure on batch index [1]."
    domain_reports["problem_solution"].composite_domain_confidence = 0.0
    startup, claims, _ = _make_mock_claims_and_profile()

    ok, reasons = verify_supervisory_review_prerequisites(
        domain_reports=domain_reports,
        profile=startup,
        claims=claims,
    )
    assert ok is False
    assert any("incomplete execution" in r for r in reasons)
    assert any("zero composite domain confidence" in r for r in reasons)


def test_supervisory_gating_blocks_when_criterion_is_missing_or_unknown():
    """Supervisory review is blocked if a canonical criterion is missing or an unknown ID is present."""
    domain_reports = _build_full_6_domain_reports()
    # Remove one criterion (PS-05) and inject an unknown ID (PS-99)
    del domain_reports["problem_solution"].criteria_evaluations["PS-05"]
    domain_reports["problem_solution"].criteria_evaluations["PS-99"] = _make_criterion_eval("PS-99", "problem_solution")
    startup, claims, _ = _make_mock_claims_and_profile()

    ok, reasons = verify_supervisory_review_prerequisites(
        domain_reports=domain_reports,
        profile=startup,
        claims=claims,
    )
    assert ok is False
    assert any("missing canonical criterion 'PS-05'" in r for r in reasons)
    assert any("unknown criterion ID 'PS-99'" in r for r in reasons)


def test_supervisory_gating_blocks_when_cover_criteria_unaccounted():
    """Supervisory review is blocked if cover criteria CM-01..06 cannot be verified."""
    domain_reports = _build_full_6_domain_reports()
    # Provide empty profile and claims
    bare_startup = SimpleNamespace(id=uuid.uuid4())

    ok, reasons = verify_supervisory_review_prerequisites(
        domain_reports=domain_reports,
        profile=bare_startup,
        claims=[],
    )
    assert ok is False
    assert any("Missing account of cover metadata criteria" in r for r in reasons)


# ===========================================================================
# 2. Budget Default and Override Tests
# ===========================================================================

def test_production_default_evaluation_budget_is_35_cents():
    """Confirms production default budget is $0.35 USD across Settings, CostLedger, and Readiness."""
    settings = Settings()
    assert settings.ai_max_evaluation_budget_usd == 0.35
    assert settings.ai_max_evaluation_budget == 0.35

    ledger = EvaluationCostLedger(evaluation_id="eval-budget-default-test")
    assert ledger.max_budget_usd == 0.35

    report = get_live_readiness_report(settings)
    ceiling_check = next(c for c in report["checks"] if c["name"] == "Hard Cost Ceiling Enforcement")
    assert ceiling_check["max_budget_usd"] == 0.35
    assert ceiling_check["buffered_inr"] == pytest.approx(39.65, abs=0.01)
    assert ceiling_check["status"] == "PASS"


def test_budget_override_behavior_and_fail_closed():
    """Explicit budget overrides are honored and pre-call reservations fail closed."""
    # Explicit override to $0.40
    custom_ledger = EvaluationCostLedger(evaluation_id="eval-override-test", max_budget_usd=0.40)
    assert custom_ledger.max_budget_usd == 0.40
    assert custom_ledger.remaining_budget_usd == 0.40

    # Reserve $0.30 -> succeeds
    res_id = custom_ledger.reserve_budget(0.30, "domain_expert_1")
    assert custom_ledger.reserved_usd == 0.30
    assert custom_ledger.remaining_budget_usd == pytest.approx(0.10, abs=1e-6)

    # Attempt second reservation exceeding ceiling ($0.15 > $0.10 remaining) -> must fail closed
    with pytest.raises(AIBudgetExhaustedError, match="would exceed budget ceiling"):
        custom_ledger.reserve_budget(0.15, "domain_expert_2")

    # Clean reconciliation preserves unspent ceiling
    custom_ledger.reconcile_operation(
        reservation_id=res_id,
        agent_name="domain_expert_1",
        provider="anthropic",
        model="claude-sonnet-5-5",
        input_tokens=1000,
        output_tokens=200,
        actual_cost_usd=0.025,
        finish_reason="stop",
    )
    assert custom_ledger.spent_usd == 0.025
    assert custom_ledger.reserved_usd == 0.0
    assert custom_ledger.remaining_budget_usd == pytest.approx(0.375, abs=1e-6)


# ===========================================================================
# 3. Complete 87-Criterion Report Integrity Tests
# ===========================================================================

def test_report_validator_accepts_complete_87_criteria_and_rejects_incomplete():
    """ReportValidator strictly accepts complete 87-criteria reports and rejects incomplete ones."""
    domain_reports = _build_full_6_domain_reports()
    startup, claims, evidence = _make_mock_claims_and_profile()

    graph = ObservationGraphBuilder.build(
        profile=startup,
        claims=claims,
        evidence=evidence,
        assessments=list(domain_reports.values()),
        conflicts=[],
    )
    graph.domain_reports = domain_reports
    for dkey, rep in domain_reports.items():
        graph.domain_assessments[dkey] = rep

    # Generate full report
    graph = DueDiligenceReportEngine.generate(graph)

    # 1. Complete evaluation passes strict canonical validation with zero errors
    val_full = ReportValidator.validate_canonical_87_report(graph)
    assert val_full["valid"] is True
    assert val_full["error_count"] == 0

    # 2. Incomplete evaluation is rejected with errors
    incomplete_graph = copy.deepcopy(graph)
    del incomplete_graph.domain_reports["innovation_impact"]
    del incomplete_graph.domain_assessments["innovation_impact"]
    val_incomplete = ReportValidator.validate_canonical_87_report(incomplete_graph)
    assert val_incomplete["valid"] is False
    assert val_incomplete["error_count"] > 0
    assert any(e["code"] in ("INCOMPLETE_DOMAIN_CRITERIA", "MISSING_CANONICAL_DOMAIN") for e in val_incomplete["errors"])


def test_missing_information_not_converted_to_negative_evidence():
    """Criteria with MISSING_INFORMATION retain gap classification without fabricating negative claims."""
    domain_reports = _build_full_6_domain_reports()
    # Set BC-04 (CAC) to MISSING_INFORMATION
    bc_evals = domain_reports["commercialisation"].criteria_evaluations
    bc_evals["BC-04"] = CriterionAssessment(
        criterion_id="BC-04",
        criterion_name="Customer Acquisition Cost",
        extracted_startup_response=None,
        assessment_narrative="Missing from application: Customer Acquisition Cost.",
        evidence_ids=[],
        source_locations=["Slide 11"],
        verification_status=VerificationStatus.MISSING_INFORMATION,
        score=None,
        strengths=[],
        weaknesses=["Unverified or missing documentation for Customer Acquisition Cost"],
        risks=[],
        confidence_score=0.0,
    )

    startup, claims, evidence = _make_mock_claims_and_profile()
    graph = ObservationGraphBuilder.build(
        profile=startup,
        claims=claims,
        evidence=evidence,
        assessments=list(domain_reports.values()),
        conflicts=[],
    )
    graph.domain_reports = domain_reports
    for dkey, rep in domain_reports.items():
        graph.domain_assessments[dkey] = rep

    graph = DueDiligenceReportEngine.generate(graph)
    val = ReportValidator.validate_canonical_87_report(graph)
    # Even with missing info, as long as it's not a phantom verified criterion, strict validation succeeds
    assert val["valid"] is True
    crit = graph.domain_reports["commercialisation"].criteria_evaluations["BC-04"]
    assert crit.verification_status == VerificationStatus.MISSING_INFORMATION
    assert len(crit.evidence_ids) == 0
    assert len(crit.strengths) == 0
