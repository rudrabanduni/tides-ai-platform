"""
Regression test suite for STETHAIM Report Integrity and Multi-Body Governance Reconciliation.
"""
import os
import json
import hashlib
from pathlib import Path
import pytest

from app.modules.evaluation.graph.graph_serializer import from_json
from app.modules.evaluation.report.report_validator import ReportValidator


REPO_ROOT = Path(__file__).resolve().parent.parent
TARGET_GRAPH_PATH = REPO_ROOT / "uploads" / "graphs" / "a246f3a5-b797-43fc-9dc3-3e603e3b37b9.json"
OLDER_ARTIFACT_PATH = REPO_ROOT / "uploads" / "graphs" / "REPORT-BBD93B93.json"
METADATA_PATH = REPO_ROOT / "uploads" / "graphs" / "a246f3a5-b797-43fc-9dc3-3e603e3b37b9.metadata.json"
DB_PATH = REPO_ROOT / "tides_ai.db"
EXPECTED_DB_HASH = "d9659f4e8c1058c5d5f4511e1bb22d3abe6cb12101c16ce397416051a38176c7"


def _get_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def test_stethaim_report_clean_and_domain_accurate():
    """Verify STETHAIM report has zero forbidden energy terms and contains genuine MedTech claims."""
    assert TARGET_GRAPH_PATH.exists()
    with open(TARGET_GRAPH_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = from_json(json.dumps(data))
    assert graph.report is not None

    # Run ReportValidator
    errors = ReportValidator.validate(graph)
    assert len(errors) == 0, f"Expected 0 validation errors, got: {errors}"

    # Verify absence of all forbidden energy terms in all report sections
    sections = [
        graph.report.executive_summary,
        graph.report.investment_recommendation,
        graph.report.founder_assessment,
        graph.report.product_technology,
        graph.report.market_opportunity,
        graph.report.business_model,
        graph.report.competition,
        graph.report.financial_overview,
        graph.report.risks,
        graph.report.investment_thesis,
        graph.report.follow_up_questions,
    ]
    forbidden_terms = ReportValidator.FORBIDDEN_ENERGY_TERMS
    for sec in sections:
        content_lower = sec.content.lower()
        for term in forbidden_terms:
            assert term.lower() not in content_lower, (
                f"Forbidden term '{term}' found in section '{sec.section_id}'"
            )

    # Verify MedTech product claims exist
    exec_content = graph.report.executive_summary.content
    assert "MedTech" in exec_content
    assert "4.0" in exec_content
    assert any(w in exec_content.lower() for w in ["copd", "lung", "screening", "multimodal"])


def test_cross_contamination_detection():
    """Verify ReportValidator correctly detects artificially injected cross-startup contamination."""
    with open(TARGET_GRAPH_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = from_json(json.dumps(data))

    # Inject forbidden energy term into executive summary
    graph.report.executive_summary.content += " Initial testing de-risks basic electrochemical feasibility."
    errors = ReportValidator.validate_cross_contamination(graph)
    assert any("electrochemical" in err.lower() for err in errors)

    # Inject foreign entity CleanPower
    graph.report.executive_summary.content += " CleanPower Systems provides technical cell architecture."
    errors = ReportValidator.validate_cross_contamination(graph)
    assert any("foreign startup" in err.lower() for err in errors)


def test_recommendation_reconciliation():
    """Verify multi-body recommendations and unified operational policy."""
    with open(TARGET_GRAPH_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = from_json(json.dumps(data))

    # Supervisory review check
    sr = graph.supervisory_review
    assert sr is not None
    sr_rec = sr.get("overall_recommendation") if isinstance(sr, dict) else getattr(sr, "overall_recommendation")
    assert sr_rec == "CONDITIONAL"

    # Rationale consistency check
    rationale = sr.get("recommendation_rationale") if isinstance(sr, dict) else getattr(sr, "recommendation_rationale")
    assert "defer is not warranted" in rationale.lower()

    # Investment Assessment check
    ia = graph.investment_assessment
    assert ia is not None
    assert "WATCH" in ia.recommendation.upper()
    assert abs(ia.investment_score - 68.4) < 0.5

    # Committee Decision check
    cd = graph.committee_decision
    assert cd is not None
    cd_rec = cd.recommendation if hasattr(cd, "recommendation") else cd.get("recommendation")
    assert "SEEK_MORE_INFORMATION" in str(cd_rec)

    # Executive Summary and Investment Recommendation Governance reconciliation
    exec_text = graph.report.executive_summary.content
    inv_text = graph.report.investment_recommendation.content

    assert "CONDITIONAL" in exec_text
    assert "SEEK_MORE_INFORMATION" in exec_text
    assert "SEEK MORE INFORMATION with CONDITIONAL MILESTONE-GATED EXECUTION" in exec_text

    assert "CONDITIONAL" in inv_text
    assert "SEEK_MORE_INFORMATION" in inv_text
    assert "Institutional Recommendation & Governance Reconciliation" in inv_text
    assert "SEEK MORE INFORMATION with CONDITIONAL MILESTONE-GATED EXECUTION" in inv_text


def test_older_artifact_preservation():
    """Verify older artifact REPORT-BBD93B93.json is intact, unchanged, and not overwritten."""
    assert OLDER_ARTIFACT_PATH.exists()
    with open(OLDER_ARTIFACT_PATH, "r", encoding="utf-8") as f:
        old_data = json.load(f)

    assert old_data.get("startup_name") == "CleanPower Systems"
    old_report_id = old_data.get("report", {}).get("report_id")
    assert old_report_id == "REPORT-BBD93B93"

    with open(TARGET_GRAPH_PATH, "r", encoding="utf-8") as f:
        current_data = json.load(f)

    current_report_id = current_data.get("report", {}).get("report_id")
    assert current_report_id != "REPORT-BBD93B93"
    assert current_report_id != "REPORT-B8A3B351"
    assert current_data.get("startup_name") == "STETHAIM Pvt. Ltd."


def test_historical_cost_telemetry_intact():
    """Verify historical spend of $0.269917 USD and operations ledger remain intact."""
    assert METADATA_PATH.exists()
    with open(METADATA_PATH, "r", encoding="utf-8") as f:
        meta = json.load(f)

    cost_obs = meta.get("cost_observability", {})
    assert cost_obs.get("total_spent_usd") == 0.269917
    assert cost_obs.get("max_budget_usd") == 0.35
    assert cost_obs.get("total_operations") == 19


def test_database_integrity():
    """Verify tides_ai.db has not been modified and matches expected SHA-256."""
    assert DB_PATH.exists()
    current_hash = _get_sha256(DB_PATH)
    assert current_hash == EXPECTED_DB_HASH, (
        f"Database hash mismatch! Expected {EXPECTED_DB_HASH}, got {current_hash}"
    )


def test_mandatory_sections_populated():
    """Verify that all 5 previously empty sections have substantive, non-trivial content."""
    assert TARGET_GRAPH_PATH.exists()
    with open(TARGET_GRAPH_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = from_json(json.dumps(data))
    report = graph.report
    assert report is not None

    mandatory_sections = {
        "founder_assessment": report.founder_assessment,
        "product_technology": report.product_technology,
        "market_opportunity": report.market_opportunity,
        "competition": report.competition,
        "investment_thesis": report.investment_thesis,
    }

    for name, sec in mandatory_sections.items():
        assert sec is not None, f"Section {name} is None"
        assert sec.content is not None, f"Section {name} content is None"
        content_stripped = sec.content.strip()
        assert len(content_stripped) > 100, f"Section {name} is too short ({len(content_stripped)} chars)"
        # Verify markdown tables and structured content
        assert "|" in content_stripped, f"Section {name} missing tabular structured evidence"


def test_factual_mapping_and_no_unsupported_claims():
    """Verify correct mapping of ps_06, ps_08, TRL qualification, no clean cap table, and no clinical validation claims."""
    with open(TARGET_GRAPH_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = from_json(json.dumps(data))
    report = graph.report

    # 1. ps_06 solution description in product_technology and executive_summary
    prod_text = report.product_technology.content
    exec_text = report.executive_summary.content
    thesis_text = report.investment_thesis.content
    assert "Non-invasive multimodal device for lung pathology detection and screening" in prod_text
    assert "Non-invasive multimodal device for lung pathology detection and screening" in exec_text
    assert "Non-invasive multimodal device for lung pathology detection and screening" in thesis_text

    # 2. ps_08 unique value proposition used strictly for differentiation
    assert "Claimed first multimodal lung disease detection and screening device in segment" in prod_text
    assert "Differentiation" in prod_text or "differentiates" in exec_text.lower()

    # 3. No "clean cap table" claim anywhere in the entire report
    all_sections = [
        report.executive_summary, report.investment_recommendation, report.founder_assessment,
        report.product_technology, report.market_opportunity, report.business_model,
        report.competition, report.financial_overview, report.risks,
        report.investment_thesis, report.follow_up_questions
    ]
    for sec in all_sections:
        assert "clean cap table" not in sec.content.lower(), f"Unsupported 'clean cap table' found in {sec.section_id}"

    # 4. TRL 4 explicitly qualified as applicant-reported / pending independent verification
    assert "TRL 4.0 (Applicant-reported" in prod_text or "applicant-reported" in prod_text.lower()
    assert "PS-09 is SELF_REPORTED_ONLY" in prod_text or "self-reported" in prod_text.lower()

    # 5. Clinical validation: unevidenced in application (ICBHI dataset benchmark only)
    assert "ICBHI" in prod_text
    assert "No sensitivity/specificity metrics, hospital trial data" in prod_text or "unevidenced" in prod_text.lower()


def test_appendix_c_and_metadata_assessment_counts():
    """Verify Appendix C and metadata report 6 Expert Assessments, matching graph.domain_reports."""
    with open(TARGET_GRAPH_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = from_json(json.dumps(data))
    report = graph.report

    # Metadata domain assessments count must be 6
    assert report.metadata.get("domain_assessments_count") == 6

    # Appendix C must report Expert Assessments: 6
    app_c = next((a for a in report.appendices if a.appendix_id == "appendix_c"), None)
    assert app_c is not None
    assert "Expert Assessments: 6" in app_c.content
    assert "Documents: 1" in app_c.content
    assert "Evidence Nodes: 77" in app_c.content
    assert "Claims: 77" in app_c.content
    assert "Risks Identified: 12" in app_c.content


def test_dual_scoring_reconciliation_in_thesis():
    """Verify dual scoring reconciliation table in investment thesis and executive summary."""
    with open(TARGET_GRAPH_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = from_json(json.dumps(data))
    thesis = graph.report.investment_thesis.content
    exec_summary = graph.report.executive_summary.content

    # Check presence of both Commercial Viability and Evidence Review scores
    assert "68.44" in thesis
    assert "42.0" in thesis or "42.00" in thesis
    assert "Commercial Viability Score" in thesis
    assert "Evidence Verification Score" in thesis or "Evidence Review Score" in thesis

    assert "68.44" in exec_summary
    assert "42.0" in exec_summary


def test_final_review_consistency_and_reconciliation():
    """Verify final review recommendation is CONDITIONAL and reconciles with supervisory review."""
    with open(TARGET_GRAPH_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = from_json(json.dumps(data))

    sr = graph.supervisory_review
    sr_rec = sr.get("overall_recommendation") if isinstance(sr, dict) else getattr(sr, "overall_recommendation")
    assert sr_rec == "CONDITIONAL"

    fr = graph.final_review
    fr_rec = fr.get("overall_recommendation") if isinstance(fr, dict) else getattr(fr, "overall_recommendation")
    assert fr_rec == "CONDITIONAL"

    rep_fr = graph.report.final_review
    rep_fr_rec = rep_fr.get("overall_recommendation") if isinstance(rep_fr, dict) else getattr(rep_fr, "overall_recommendation")
    assert rep_fr_rec == "CONDITIONAL"


def test_report_validator_catches_empty_mandatory_section():
    """Verify ReportValidator rejects a report if any mandatory section is empty."""
    with open(TARGET_GRAPH_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = from_json(json.dumps(data))
    graph.report.founder_assessment.content = ""
    errors = ReportValidator.validate(graph)
    assert any("Empty Section" in err and "founder_assessment" in err for err in errors)


def test_report_validator_catches_stale_final_review():
    """Verify ReportValidator rejects a stale final_review recommendation mismatching supervisory review."""
    with open(TARGET_GRAPH_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = from_json(json.dumps(data))
    if isinstance(graph.final_review, dict):
        graph.final_review["overall_recommendation"] = "DEFER"
    else:
        graph.final_review.overall_recommendation = "DEFER"

    errors = ReportValidator.validate(graph)
    assert any("Stale Final Review" in err for err in errors)


def test_report_validator_catches_unsupported_cap_table_claim():
    """Verify ReportValidator rejects an unsupported clean cap table claim."""
    with open(TARGET_GRAPH_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = from_json(json.dumps(data))
    graph.report.financial_overview.content += " The startup exhibits a clean cap table with 100% founder ownership."
    errors = ReportValidator.validate(graph)
    assert any("Unsupported Cap Table Claim" in err for err in errors)


def test_report_validator_catches_unverified_trl_claim():
    """Verify ReportValidator rejects an assertively certified/proven TRL claim."""
    with open(TARGET_GRAPH_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    graph = from_json(json.dumps(data))
    graph.report.product_technology.content += " The device is verified TRL 4 with full test proof."
    errors = ReportValidator.validate(graph)
    assert any("Unsupported TRL Claim" in err for err in errors)

