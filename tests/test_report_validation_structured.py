"""Phase 7, 8 & 9 tests: Domain-agnostic report generation, dynamic contamination guards, and structured validator."""

import copy
from app.modules.evaluation.conflict_resolution import ConflictResolutionEngine
from app.modules.evaluation.executive import ExecutiveEngine
from app.modules.evaluation.graph.graph_builder import ObservationGraphBuilder
from app.modules.evaluation.investment import InvestmentEngine
from app.modules.evaluation.report.report_engine import DueDiligenceReportEngine
from app.modules.evaluation.report.report_validator import ReportValidator
from tests.test_due_diligence_report import (
    DummyAssessment,
    DummyClaim,
    DummyDocument,
    DummyEvidence,
    DummyObservation,
    DummyProfile,
    mock_graph,  # noqa: F401
)


def test_report_engine_is_domain_agnostic_when_optional_fields_omitted():
    """Generated reports must not fabricate STETHAIM/MedTech fallbacks ('68.44', '42.0', '4.0', 'Device sales', etc.)."""
    docs = [DummyDocument("doc-agri-1", "AgriTech Pitch.pdf", "PDF")]
    profile = DummyProfile(docs)
    profile.startup_id = "agri-saas-01"
    profile.startup_name = "CropPulse Analytics"
    profile.sector = "AgriTech SaaS"
    profile.stage = "Pre-Seed"
    profile.description = "Satellite soil moisture SaaS dashboard for smallholder cooperatives."
    profile.problem_solved = "Irrigation water waste and unpredictable yield drops across fragmented farms."
    profile.business_model = "Annual B2G/B2B SaaS subscriptions"
    profile.funding_ask = "₹50 Lakh"

    claims = [DummyClaim("c-1", "ps_01_problem_statement", profile.problem_solved)]
    ev = [DummyEvidence("ev-1", "c-1", "doc-agri-1", "Irrigation waste exceeds 40% across fragmented farms.")]
    obs = DummyObservation(
        "obs-agri-1",
        "SaaS telemetry dashboard processes multispectral imagery.",
        ["c-1"],
        ["ev-1"],
        domain="product",
    )
    asm = DummyAssessment("product", [obs])
    graph = ObservationGraphBuilder.build(profile, claims, ev, [asm], [])
    graph = DueDiligenceReportEngine.generate(graph)

    assert graph.report is not None
    all_prose = "\n".join(
        getattr(getattr(graph.report, s, None), "content", "") or ""
        for s in ReportValidator.REQUIRED_SECTIONS
    )
    assert "68.44" not in all_prose
    assert "42.0" not in all_prose
    assert "TRL 4.0" not in all_prose
    assert "Device sales and diagnostic fees" not in all_prose
    assert "Stage 4 (Agreement Signing)" not in all_prose
    assert "14-day diligence sprint" not in all_prose
    assert "Patent application filed" not in all_prose
    assert "Not disclosed in application" in all_prose

    structured = ReportValidator.validate_structured(graph)
    assert structured["valid"] is True, f"Unexpected errors: {structured['errors']}"
    assert structured["error_count"] == 0


def test_structured_validator_catches_contamination_identity_and_phantom_criteria(mock_graph):
    """ReportValidator.validate_structured must classify errors, warnings, and info notices cleanly."""
    graph = ConflictResolutionEngine.resolve(mock_graph)
    graph = ExecutiveEngine.generate(graph)
    graph = InvestmentEngine.generate(graph)
    graph = DueDiligenceReportEngine.generate(graph)
    graph.report.metadata["evaluation_mode"] = "MOCK_SIMULATED_OFFLINE"
    base_result = ReportValidator.validate_structured(graph)
    assert base_result["valid"] is True, f"Base errors: {base_result['errors']}"
    assert any(i["code"] == "EVALUATION_MODE_INFO" and i["severity"] == "INFORMATIONAL" for i in base_result["informational"])

    # 1. Foreign sector contamination in non-MedTech startup
    bad_sector = copy.deepcopy(graph)
    bad_sector.startup_profile.sector = "Enterprise SaaS"
    bad_sector.report.product_technology.content += " Also uses pulmonary lung screening auscultation and PET solvolysis."
    res_cc = ReportValidator.validate_structured(bad_sector)
    assert res_cc["valid"] is False
    assert any("auscultation" in e["message"].lower() for e in res_cc["errors"])
    assert any("solvolysis" in e["message"].lower() for e in res_cc["errors"])

    # 2. Identity mismatch
    bad_id = copy.deepcopy(graph)
    bad_id.report.metadata["startup_name"] = "OtherVenture Ltd"
    res_id = ReportValidator.validate_structured(bad_id)
    assert any(e["code"] == "STARTUP_NAME_MISMATCH" for e in res_id["errors"])

    # 3. Phantom VERIFIED_DOCUMENTED criterion without evidence and without extracted value
    bad_crit = copy.deepcopy(graph)
    bad_crit.domain_reports = {
        "problem_solution": {
            "criteria_evaluations": {
                "PS-01": {
                    "verification_status": "VERIFIED_DOCUMENTED",
                    "evidence_ids": [],
                    "extracted_startup_response": None,
                },
                "PS-02": {
                    "verification_status": "VERIFIED_DOCUMENTED",
                    "evidence_ids": [],
                    "extracted_startup_response": "Mid-sized logistics fleets",
                },
            }
        }
    }
    res_crit = ReportValidator.validate_structured(bad_crit)
    assert any(e["code"] == "PHANTOM_VERIFIED_CRITERION" and e["severity"] == "ERROR" for e in res_crit["errors"])
    assert any(w["code"] == "UNLINKED_VERIFIED_CRITERION" and w["severity"] == "WARNING" for w in res_crit["warnings"])
    assert any(w["code"] == "INCOMPLETE_DOMAIN_CRITERIA" and w["severity"] == "WARNING" for w in res_crit["warnings"])

    # 4. Generalized certified TRL violation (e.g., TRL 5 when PS-09 is not verified)
    bad_trl = copy.deepcopy(graph)
    bad_trl.report.executive_summary.content += " Independently certified TRL 5 achieved."
    res_trl = ReportValidator.validate_structured(bad_trl)
    assert any("Unsupported TRL Claim" in e["message"] for e in res_trl["errors"])
