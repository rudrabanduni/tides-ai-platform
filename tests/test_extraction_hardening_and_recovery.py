"""tests/test_extraction_hardening_and_recovery.py - Offline verification for extraction hardening,
sub-segmentation, checkpoint recovery, and budget safety for PETREVOLT evaluation 1a8036ae.
"""

import json
from pathlib import Path
import pytest

from app.modules.ai.orchestrator.startup_profile_extraction import (
    PatentEntry,
    SDGAlignmentEntry,
    ImpactMetricEntry,
    InnovationIpPatentsExtraction,
    ImpactStrategicAlignmentExtraction,
    InnovationImpactExtraction,
    merge_innovation_impact_subsegments,
    merge_domain_extractions_to_canonical_profile,
    CoverIntakeExtraction,
    ProblemNeedExtraction,
    SolutionProductExtraction,
    PrototypeTechnicalExtraction,
    MarketOpportunityExtraction,
    FounderCoreExtraction,
    TeamAdvisoryExtraction,
    CommercialisationExtraction,
    FinancialsSupportExtraction,
    EXTRACTION_OUTPUT_TOKEN_LIMITS,
)
from app.modules.ai.orchestrator.extraction_checkpoint import (
    EXTRACTION_STAGE_SPECS,
    STAGE_SPECS_BY_KEY,
    load_extraction_checkpoint,
    normalize_extraction_stage_name,
)
from scripts.run_one_time_live_eval import (
    get_launcher_config,
    validate_extraction_recovery_prerequisites,
    BUDGET_CEILING_USD,
)
from app.services.ai.cost_ledger import CostLedgerManager


PROJECT_ROOT = Path(__file__).resolve().parent.parent


def test_extraction_output_token_limits_hardened():
    """Verify financials_support is 4,096, innovation_impact is 2,400 with bounded sub-segments at 2,400."""
    assert EXTRACTION_OUTPUT_TOKEN_LIMITS["financials_support"] == 4096
    assert EXTRACTION_OUTPUT_TOKEN_LIMITS["innovation_impact"] == 2400
    assert EXTRACTION_OUTPUT_TOKEN_LIMITS["innovation_ip_patents"] == 2400
    assert EXTRACTION_OUTPUT_TOKEN_LIMITS["impact_strategic_alignment"] == 2400


def test_launcher_config_alignment():
    """Verify get_launcher_config reports 10 stages and 19 batches <= 900 tokens."""
    cfg = get_launcher_config()
    assert cfg["extraction_stages_count"] == 10
    assert "2,400-4,096" in cfg["extraction_token_cap_str"]
    assert "<= 900" in cfg["domain_token_caps_str"]
    assert "19 batches" in cfg["domain_token_caps_str"]
    assert cfg["budget_ceiling_usd"] == 0.35


def test_innovation_impact_subsegment_schemas_and_deterministic_merge():
    """Verify sub-segments A (IP/Moats) and B (Impact/SDGs) merge deterministically into InnovationImpactExtraction."""
    sub_a = InnovationIpPatentsExtraction(
        proprietary_technology_moat="Solid-state sodium-ion battery from upcycled PET plastic",
        data_advantage="Degradation curve tracking across 50,000 charge cycles",
        network_effects="OEM reverse logistics hub integration",
        switching_costs="Certified off-take specifications with battery makers",
        brand_community_moat="Green Battery Passport compliance",
        regulatory_licensing_barriers="CPCB battery waste management authorization",
        patent_details=[
            PatentEntry(
                title="Method for upcycling PET plastic to solid-state carbon matrix",
                application_number="202441012345",
                status="Filed",
                jurisdiction="India",
            )
        ],
        source_attribution="Slide 7: Technical Moats & IP Portfolio",
    )

    sub_b = ImpactStrategicAlignmentExtraction(
        primary_impact="Eliminates toxic heavy metal landfill waste and virgin mining emissions",
        sdg_alignments=[
            SDGAlignmentEntry(
                sdg_number=7,
                sdg_name="Affordable and Clean Energy",
                explanation="Provides low-cost domestic energy storage",
            ),
            SDGAlignmentEntry(
                sdg_number=12,
                sdg_name="Responsible Consumption and Production",
                explanation="Circular battery manufacturing from plastic waste",
            ),
        ],
        impact_metrics=[
            ImpactMetricEntry(
                metric_name="CO2 abated annually",
                baseline="0 tonnes",
                target_3_year="12,000 tonnes",
            )
        ],
        potential_negative_effects_mitigation="Zero-liquid discharge closed-loop hydrometallurgy process",
        source_attribution="Slide 11: ESG & Strategic National Impact",
    )

    merged = merge_innovation_impact_subsegments(sub_a, sub_b)
    assert isinstance(merged, InnovationImpactExtraction)
    assert merged.proprietary_technology_moat == sub_a.proprietary_technology_moat
    assert merged.data_advantage == sub_a.data_advantage
    assert merged.network_effects == sub_a.network_effects
    assert merged.switching_costs == sub_a.switching_costs
    assert merged.brand_community_moat == sub_a.brand_community_moat
    assert merged.regulatory_licensing_barriers == sub_a.regulatory_licensing_barriers
    assert len(merged.patent_details) == 1
    assert merged.patent_details[0].application_number == "202441012345"
    assert merged.primary_impact == sub_b.primary_impact
    assert len(merged.sdg_alignments) == 2
    assert len(merged.impact_metrics) == 1
    assert merged.potential_negative_effects_mitigation == sub_b.potential_negative_effects_mitigation
    assert "Slide 7" in merged.source_attribution
    assert "Slide 11" in merged.source_attribution


def test_canonical_profile_merge_with_hardened_innovation_impact():
    """Verify merge_domain_extractions_to_canonical_profile accepts the merged innovation_impact output."""
    sub_a = InnovationIpPatentsExtraction(
        proprietary_technology_moat="Solid-state Na-ion",
        patent_details=[PatentEntry(title="Na-ion PET", application_number="123", status="Filed", jurisdiction="India")],
        source_attribution="Deck: IP Slide",
    )
    sub_b = ImpactStrategicAlignmentExtraction(
        primary_impact="Landfill diversion",
        sdg_alignments=[SDGAlignmentEntry(sdg_number=7, sdg_name="Energy", explanation="Clean")],
        source_attribution="Deck: Impact Slide",
    )
    ii = merge_innovation_impact_subsegments(sub_a, sub_b)

    cover = CoverIntakeExtraction(company_name="PETREVOLT ENERGY SOLUTIONS PVT LTD", sector="CleanTech", stage="Seed")
    problem = ProblemNeedExtraction(problem_statement="Lithium dependence")
    sol = SolutionProductExtraction(solution="Sodium-ion battery")
    proto = PrototypeTechnicalExtraction(current_trl=4, prototype_stage="Lab Prototype")
    mo = MarketOpportunityExtraction(market_size="10B USD")
    f_core = FounderCoreExtraction()
    t_adv = TeamAdvisoryExtraction()
    bc = CommercialisationExtraction(business_model="B2B OEM")
    fi = FinancialsSupportExtraction()

    profile = merge_domain_extractions_to_canonical_profile(
        cover=cover,
        problem=problem,
        solution_product=sol,
        prototype_technical=proto,
        mo=mo,
        founder_core=f_core,
        team_advisory=t_adv,
        bc=bc,
        ii=ii,
        fi=fi,
        default_company_name="PETREVOLT ENERGY SOLUTIONS PVT LTD",
    )

    assert profile.company_name == "PETREVOLT ENERGY SOLUTIONS PVT LTD"
    assert profile.proprietary_technology_moat == "Solid-state Na-ion"
    assert profile.patents == "1 patent(s) recorded"
    assert profile.primary_impact == "Landfill diversion"
    assert len(profile.sdg_alignments) == 1
    assert "Deck: IP Slide" in profile.source_attribution
    assert "Deck: Impact Slide" in profile.source_attribution


def _make_8_stage_fixture(tmp_path: Path) -> tuple[Path, Path]:
    """Helper creating deterministic 8-stage checkpoint and report fixtures for preflight tests."""
    base_ckpt = PROJECT_ROOT / "uploads" / "extraction_checkpoints" / "1b5de317-6e56-4dcb-ada9-28ab9adf8c0c_1a8036ae-0e37-4fb0-b241-680d2bb62b8d.json"
    ckpt_data = json.loads(base_ckpt.read_text(encoding="utf-8"))
    expected_8_stages = [
        "cover_intake",
        "problem_need",
        "solution_product",
        "prototype_technical",
        "market_opportunity",
        "founder_core",
        "team_advisory",
        "commercialisation",
    ]
    ckpt_data["completed_stages"] = {k: v for k, v in ckpt_data["completed_stages"].items() if k in expected_8_stages}
    ckpt_data["subsegments"] = {}
    ckpt_data["failed_stage"] = "innovation_impact"
    ckpt_data["completed"] = False

    ckpt_file = tmp_path / "1b5de317-6e56-4dcb-ada9-28ab9adf8c0c_1a8036ae-0e37-4fb0-b241-680d2bb62b8d.json"
    ckpt_file.write_text(json.dumps(ckpt_data), encoding="utf-8")

    report_data = {
        "evaluation_id": "1a8036ae-0e37-4fb0-b241-680d2bb62b8d",
        "startup_id": "1b5de317-6e56-4dcb-ada9-28ab9adf8c0c",
        "total_operations": 8,
        "total_spent_usd": 0.010542,
        "carried_forward_spend_usd": 0.010542,
        "cost_observability": {
            "evaluation_id": "1a8036ae-0e37-4fb0-b241-680d2bb62b8d",
            "total_spent_usd": 0.010542,
            "remaining_budget_usd": 0.339458,
            "max_budget_usd": 0.35,
        },
    }
    report_file = tmp_path / "live_eval_run_report.json"
    report_file.write_text(json.dumps(report_data), encoding="utf-8")

    return ckpt_file, report_file


def test_checkpoint_1a8036ae_preserves_completed_stages_and_eval_id(tmp_path):
    """Verify PETREVOLT checkpoint loads cleanly and preserves all stages and evaluation ID."""
    ckpt_path = PROJECT_ROOT / "uploads" / "extraction_checkpoints" / "1b5de317-6e56-4dcb-ada9-28ab9adf8c0c_1a8036ae-0e37-4fb0-b241-680d2bb62b8d.json"
    assert ckpt_path.exists(), f"PETREVOLT checkpoint missing at {ckpt_path}"

    data = load_extraction_checkpoint(
        ckpt_path,
        expected_startup_id="1b5de317-6e56-4dcb-ada9-28ab9adf8c0c",
        expected_evaluation_id="1a8036ae-0e37-4fb0-b241-680d2bb62b8d",
    )

    assert data["exists"] is True
    completed = data["completed_stages"]
    # Production checkpoint has completed all 10 stages post-hardening
    assert len(completed) == 10
    assert data["completed"] is True
    assert "innovation_impact" in completed
    assert "financials_support" in completed

    # Also verify 8-stage partial checkpoint handling on fixture
    ckpt_8, _ = _make_8_stage_fixture(tmp_path)
    data_8 = load_extraction_checkpoint(
        ckpt_8,
        expected_startup_id="1b5de317-6e56-4dcb-ada9-28ab9adf8c0c",
        expected_evaluation_id="1a8036ae-0e37-4fb0-b241-680d2bb62b8d",
    )
    assert len(data_8["completed_stages"]) == 8
    assert data_8["failed_stage"] == "innovation_impact"
    assert data_8["completed"] is False


def test_validate_extraction_recovery_resumes_in_place_for_1a8036ae(tmp_path):
    """Verify that validate_extraction_recovery_prerequisites selects CHECKPOINT_RESUME
    and preserves evaluation ID 1a8036ae without creating a new evaluation."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    dev_db_path = PROJECT_ROOT / "tides_dev.db"
    assert dev_db_path.exists()

    engine = create_engine(f"sqlite:///{dev_db_path}")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    ckpt_path, report_path = _make_8_stage_fixture(tmp_path)

    with SessionLocal() as db:
        meta = validate_extraction_recovery_prerequisites(
            db=db,
            evaluation_id="1a8036ae-0e37-4fb0-b241-680d2bb62b8d",
            startup_id_str="1b5de317-6e56-4dcb-ada9-28ab9adf8c0c",
            target_stage="innovation_impact",
            report_path=report_path,
            checkpoint_path=ckpt_path,
        )

        assert meta["recovery_mode"] == "CHECKPOINT_RESUME"
        assert meta["evaluation_id"] == "1a8036ae-0e37-4fb0-b241-680d2bb62b8d"
        assert meta["parent_evaluation_id"] is None
        assert len(meta["reused_stages"]) == 8
        assert meta["remaining_stages"] == ["innovation_impact", "financials_support"]
        assert meta["prior_spent_usd"] == pytest.approx(0.010542, abs=1e-5)
        assert meta["remaining_budget_usd"] == pytest.approx(0.339458, abs=1e-5)
        assert meta["cumulative_projected_usd"] < BUDGET_CEILING_USD
        # Exact request counting & output token caps: 3 Haiku + 19 Sonnet domain batches + 1 Reviewer = 23 calls
        assert meta["total_planned_requests"] == 23
        assert len(meta["planned_extraction_calls"]) == 3
        assert meta["planned_extraction_calls"][0]["segment"] == "9A"
        assert meta["planned_extraction_calls"][0]["output_cap"] == 1200
        assert meta["planned_extraction_calls"][1]["segment"] == "9B"
        assert meta["planned_extraction_calls"][1]["output_cap"] == 1200
        assert meta["planned_extraction_calls"][2]["segment"] == "10"
        assert meta["planned_extraction_calls"][2]["output_cap"] == 4096
        # Reconciled cost figures
        assert meta["haiku_worst_rem_usd"] == pytest.approx(0.005698, abs=1e-5)
        assert meta["haiku_typ_rem_usd"] == pytest.approx(0.004165, abs=1e-5)
        assert meta["sonnet_worst_rem_usd"] == pytest.approx(0.296000, abs=1e-5)
        assert meta["sonnet_typ_rem_usd"] == pytest.approx(0.129100, abs=1e-5)
        assert meta["worst_case_rem_usd"] == pytest.approx(0.301698, abs=1e-5)
        assert meta["typical_rem_usd"] == pytest.approx(0.133265, abs=1e-5)
        assert meta["cumulative_projected_usd"] == pytest.approx(0.312240, abs=1e-5)
        assert meta["cumulative_typical_projected_usd"] == pytest.approx(0.143807, abs=1e-5)


def test_validate_extraction_recovery_auto_stage_selection(tmp_path):
    """Verify that target_stage='auto' automatically identifies innovation_impact as the resume point."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    dev_db_path = PROJECT_ROOT / "tides_dev.db"
    engine = create_engine(f"sqlite:///{dev_db_path}")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    ckpt_path, report_path = _make_8_stage_fixture(tmp_path)

    with SessionLocal() as db:
        meta = validate_extraction_recovery_prerequisites(
            db=db,
            evaluation_id="1a8036ae-0e37-4fb0-b241-680d2bb62b8d",
            startup_id_str="1b5de317-6e56-4dcb-ada9-28ab9adf8c0c",
            target_stage="auto",
            report_path=report_path,
            checkpoint_path=ckpt_path,
        )

        assert meta["recovery_mode"] == "CHECKPOINT_RESUME"
        assert meta["evaluation_id"] == "1a8036ae-0e37-4fb0-b241-680d2bb62b8d"
        assert meta["target_stage"] == "innovation_impact"
        assert len(meta["reused_stages"]) == 8
        assert meta["remaining_stages"] == ["innovation_impact", "financials_support"]


def test_cost_ledger_restoration_from_telemetry(tmp_path):
    """Verify that restoring ledger from eval_1a8036ae telemetry restores spend and remaining headroom accurately."""
    from app.modules.ai.orchestrator.pipeline import _restore_evaluation_cost_ledger

    # 1. Verify restoration from current production report ($0.251895 actual live spend)
    ledger = _restore_evaluation_cost_ledger(
        evaluation_id="1a8036ae-0e37-4fb0-b241-680d2bb62b8d",
        startup_id="1b5de317-6e56-4dcb-ada9-28ab9adf8c0c",
        max_budget_usd=0.35,
        project_root=PROJECT_ROOT,
        report_path=PROJECT_ROOT / "reports" / "live_eval_run_report.json",
    )

    assert ledger.spent_usd == pytest.approx(0.251895, abs=1e-5)
    assert ledger.remaining_budget_usd == pytest.approx(0.098105, abs=1e-5)
    assert ledger.is_exhausted is False

    # 2. Verify restoration from 8-stage partial report ($0.010542 prior spend)
    _, report_path = _make_8_stage_fixture(tmp_path)
    ledger_partial = _restore_evaluation_cost_ledger(
        evaluation_id="1a8036ae-0e37-4fb0-b241-680d2bb62b8d",
        startup_id="1b5de317-6e56-4dcb-ada9-28ab9adf8c0c",
        max_budget_usd=0.35,
        project_root=PROJECT_ROOT,
        report_path=report_path,
    )
    assert ledger_partial.spent_usd == pytest.approx(0.010542, abs=1e-5)
    assert ledger_partial.remaining_budget_usd == pytest.approx(0.339458, abs=1e-5)
    assert ledger_partial.is_exhausted is False


def test_recovery_request_count_with_subsegment_partial_checkpoint(tmp_path):
    """Verify that if Segment 9A is already checkpointed, only Segment 9B + Stage 10 are dispatched (22 calls)."""
    import json
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    dev_db_path = PROJECT_ROOT / "tides_dev.db"
    engine = create_engine(f"sqlite:///{dev_db_path}")
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    ckpt_path, report_path = _make_8_stage_fixture(tmp_path)
    ckpt_data = json.loads(ckpt_path.read_text(encoding="utf-8"))
    ckpt_data["subsegments"] = {
        "innovation_ip_patents": {
            "proprietary_technology_moat": "Solid-state Na-ion",
            "source_attribution": "Slide 7",
        }
    }
    tmp_ckpt = tmp_path / "1b5de317-6e56-4dcb-ada9-28ab9adf8c0c_1a8036ae-0e37-4fb0-b241-680d2bb62b8d.json"
    tmp_ckpt.write_text(json.dumps(ckpt_data), encoding="utf-8")

    with SessionLocal() as db:
        meta = validate_extraction_recovery_prerequisites(
            db=db,
            evaluation_id="1a8036ae-0e37-4fb0-b241-680d2bb62b8d",
            startup_id_str="1b5de317-6e56-4dcb-ada9-28ab9adf8c0c",
            target_stage="auto",
            report_path=report_path,
            checkpoint_path=tmp_ckpt,
        )

        assert meta["recovery_mode"] == "CHECKPOINT_RESUME"
        # 2 Haiku calls (9B and 10) + 19 Sonnet domain batches + 1 Reviewer = 22 total calls
        assert meta["total_planned_requests"] == 22
        assert len(meta["planned_extraction_calls"]) == 2
        assert meta["planned_extraction_calls"][0]["segment"] == "9B"
        assert meta["planned_extraction_calls"][0]["output_cap"] == 1200
        assert meta["planned_extraction_calls"][1]["segment"] == "10"
        assert meta["planned_extraction_calls"][1]["output_cap"] == 4096

