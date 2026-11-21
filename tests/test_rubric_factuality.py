"""Phase 5 & Phase 6 tests: Canonical 87-criterion registry coverage and evidence factuality guards."""

from unittest.mock import MagicMock

from app.modules.evaluation.domain_schemas import CompactCriterionResult, VerificationStatus
from app.modules.evaluation.domains import (
    CommercialisationExpert,
    FinancialsSupportExpert,
    FounderTeamExpert,
    InnovationImpactExpert,
    MarketOpportunityExpert,
    ProblemSolutionExpert,
)
from app.modules.evaluation.domains.registry import (
    CANONICAL_DOMAINS,
    CRITERIA_DIRECTORY,
    INTAKE_METADATA_DOMAIN,
    get_criteria_for_domain,
    get_criterion_metadata,
)
from app.modules.intelligence.claim_engine import ClaimEngine
from tests.test_phase2_domains_and_supervisory import MockClaim, MockEvidence


def test_all_87_canonical_criteria_map_to_claim_engine_fields():
    """Every canonical criterion (6 CM + 81 Domain) must have matching ClaimEngine field definitions."""
    assert len(CRITERIA_DIRECTORY) == 87
    cm_ids = get_criteria_for_domain(INTAKE_METADATA_DOMAIN)
    assert len(cm_ids) == 6
    domain_ids = [cid for d in CANONICAL_DOMAINS for cid in get_criteria_for_domain(d)]
    assert len(domain_ids) == 81
    assert set(cm_ids) | set(domain_ids) == set(CRITERIA_DIRECTORY.keys())

    # Instantiate ClaimEngine with empty extraction and inspect canonical mapping keys
    from app.modules.ai.orchestrator.startup_profile_extraction import StartupProfileExtraction

    engine = ClaimEngine.__new__(ClaimEngine)
    profile = StartupProfileExtraction(company_name="ParityCheck Corp")
    gathered = engine._gather_canonical_profile_fields(profile)

    # Every canonical criterion ID prefix (e.g. "cm_01", "ps_01", ..., "fi_21") must exist in ClaimEngine mapping
    for cid in CRITERIA_DIRECTORY:
        prefix = cid.lower().replace("-", "_")
        assert any(k.startswith(prefix) for k in gathered), f"Canonical criterion {cid} missing from ClaimEngine mapping"

    # Verify missing TRL / funding / paying customers are NOT fabricated into synthetic zeroes or defaults
    assert gathered["ps_09_current_trl"]["value"] is None
    assert gathered["fi_08_funding_raised"]["value"] is None
    assert gathered["bc_08_current_users_and_paying_customers"]["value"] is None
    assert gathered["ft_06_co_founders"]["value"] is None

    meta = get_criterion_metadata("FT-08")
    assert "skill gaps" in meta["name"].lower()


def test_missing_evidence_is_never_turned_into_verified_zero():
    """Missing BC-08, II-07, FI-08, and FT-03..05 claims must never elevate to VERIFIED_DOCUMENTED or SELF_REPORTED_ONLY."""
    bc_expert = CommercialisationExpert(gateway=MagicMock())
    ii_expert = InnovationImpactExpert(gateway=MagicMock())
    fi_expert = FinancialsSupportExpert(gateway=MagicMock())
    ft_expert = FounderTeamExpert(gateway=MagicMock())

    # 1. Missing BC-08 paying customers
    assert bc_expert.refine_verification_status("BC-08", None, VerificationStatus.VERIFIED_DOCUMENTED, []) == VerificationStatus.MISSING_INFORMATION
    assert bc_expert.refine_verification_status("BC-08", "Missing from application", VerificationStatus.MISSING_INFORMATION, []) == VerificationStatus.MISSING_INFORMATION

    # Empty claim value_string=None, value_number=None must not coerce to "0"
    empty_paying_claim = MockClaim("c-empty", "bc_08_paying_customers", None)
    assert bc_expert.refine_verification_status("BC-08", None, VerificationStatus.VERIFIED_DOCUMENTED, [empty_paying_claim]) == VerificationStatus.MISSING_INFORMATION

    # Explicitly documented "0" with evidence snippet preserves VERIFIED_DOCUMENTED; without snippet stays SELF_REPORTED_ONLY
    zero_paying_claim = MockClaim("c-zero", "bc_08_paying_customers", "0")
    assert bc_expert.refine_verification_status("BC-08", "0", VerificationStatus.VERIFIED_DOCUMENTED, [zero_paying_claim]) == VerificationStatus.VERIFIED_DOCUMENTED
    assert bc_expert.refine_verification_status("BC-08", "0", VerificationStatus.SELF_REPORTED_ONLY, [zero_paying_claim]) == VerificationStatus.SELF_REPORTED_ONLY

    # 2. Missing II-07 IP status vs explicit No IP filed
    assert ii_expert.refine_verification_status("II-07", None, VerificationStatus.VERIFIED_DOCUMENTED, []) == VerificationStatus.MISSING_INFORMATION
    assert ii_expert.refine_verification_status("II-07", "None disclosed (conditional field)", VerificationStatus.VERIFIED_DOCUMENTED, []) == VerificationStatus.MISSING_INFORMATION
    assert ii_expert.refine_verification_status("II-07", "No IP filed", VerificationStatus.VERIFIED_DOCUMENTED, []) == VerificationStatus.VERIFIED_DOCUMENTED
    assert ii_expert.refine_verification_status("II-07", "No IP filed", VerificationStatus.CONTRADICTED, []) == VerificationStatus.SELF_REPORTED_ONLY

    # 3. Missing FI-08 optional funding vs explicit bootstrapped
    assert fi_expert.refine_verification_status("FI-08", None, VerificationStatus.VERIFIED_DOCUMENTED, []) == VerificationStatus.NOT_APPLICABLE
    assert fi_expert.refine_verification_status("FI-08", "None disclosed (conditional field)", VerificationStatus.VERIFIED_DOCUMENTED, []) == VerificationStatus.NOT_APPLICABLE
    assert fi_expert.refine_verification_status("FI-08", "Bootstrapped", VerificationStatus.VERIFIED_DOCUMENTED, []) == VerificationStatus.VERIFIED_DOCUMENTED
    assert fi_expert.refine_verification_status("FI-08", "₹0", VerificationStatus.SELF_REPORTED_ONLY, []) == VerificationStatus.SELF_REPORTED_ONLY

    # 4. Missing FT-03/04/05 must NOT promote "Missing from application" to SELF_REPORTED_ONLY
    assert ft_expert.refine_verification_status("FT-03", "Missing from application", VerificationStatus.MISSING_INFORMATION, []) == VerificationStatus.MISSING_INFORMATION
    assert ft_expert.refine_verification_status("FT-05", "Optional field not provided", VerificationStatus.NOT_APPLICABLE, []) == VerificationStatus.NOT_APPLICABLE
    assert ft_expert.refine_verification_status("FT-03", "B.Tech IIT Roorkee", VerificationStatus.SELF_REPORTED_ONLY, []) == VerificationStatus.SELF_REPORTED_ONLY
    assert ft_expert.refine_verification_status("FT-03", "B.Tech IIT Roorkee", VerificationStatus.VERIFIED_DOCUMENTED, []) == VerificationStatus.VERIFIED_DOCUMENTED


def test_compact_verified_without_any_evidence_downgrades():
    """If an AI specialist claims VERIFIED_DOCUMENTED with zero evidence IDs and no linked evidence, fail closed."""
    ps_expert = ProblemSolutionExpert(gateway=MagicMock())
    claims = [MockClaim("c-ps-01", "ps_01_problem_statement", "High grid outages hurt MSME factories.")]
    compact = [
        CompactCriterionResult(
            criterion_id="PS-01",
            verification_status="VERIFIED_DOCUMENTED",
            score=8.5,
            evidence_ids=[],
            rationale="Model claimed verified without citing evidence.",
        ),
        CompactCriterionResult(
            criterion_id="PS-02",
            verification_status="VERIFIED_DOCUMENTED",
            score=7.0,
            evidence_ids=[],
            rationale="Model fabricated verification on completely missing field.",
        ),
    ]
    assessments = ps_expert.build_criterion_assessments_from_compact(claims=claims, evidence=[], compact_criteria=compact)
    assert assessments["PS-01"].verification_status == VerificationStatus.SELF_REPORTED_ONLY
    assert assessments["PS-02"].verification_status == VerificationStatus.MISSING_INFORMATION


def test_conditional_ps10_respects_high_vs_low_trl():
    """PS-10 missing is NOT_APPLICABLE at TRL<=4 and UNSUPPORTED_ASSUMPTION at TRL>=5."""
    ps_expert = ProblemSolutionExpert(gateway=MagicMock())
    low_trl = [MockClaim("c-low", "ps_09_current_trl", 3)]
    high_trl = [MockClaim("c-high", "ps_09_current_trl", 6)]

    assert ps_expert.refine_verification_status("PS-10", None, VerificationStatus.NOT_APPLICABLE, low_trl) == VerificationStatus.NOT_APPLICABLE
    assert ps_expert.refine_verification_status("PS-10", "Missing from application", VerificationStatus.MISSING_INFORMATION, high_trl) == VerificationStatus.UNSUPPORTED_ASSUMPTION
