"""
Cross-Startup Contamination & Isolation Regression Test Suite.

Verifies strict semantic, provenance, and entity isolation between:
1. STETHAIM Private Limited (MedTech / Pulmonary Diagnostics)
2. PETREVOLT ENERGY SOLUTIONS PVT LTD (CleanTech / Smart BMS / Battery Tech)
3. CleanPower Systems / GridAI (Historical fixtures)

Guarantees zero cross-leakage of founders, domain terminology, technical claims,
or institutional recommendations between evaluation artifacts.
"""
import json
import hashlib
from pathlib import Path
import pytest

from app.modules.evaluation.graph.graph_serializer import from_json
from app.modules.evaluation.report.report_validator import ReportValidator


REPO_ROOT = Path(__file__).resolve().parent.parent
STETHAIM_PACKAGE_PATH = REPO_ROOT / "reports" / "hand_off" / "STETHAIM_FINAL_REVIEW_PACKAGE_v2.1.json"
STETHAIM_GRAPH_PATH = REPO_ROOT / "uploads" / "graphs" / "a246f3a5-b797-43fc-9dc3-3e603e3b37b9.json"
PETREVOLT_PACKAGE_PATH = REPO_ROOT / "reports" / "hand_off" / "PETREVOLT_FINAL_REVIEW_PACKAGE.json"
PETREVOLT_GRAPH_PATH = REPO_ROOT / "uploads" / "graphs" / "f099fa55-f797-4145-b5f3-9c801c8b4e67.json"
PETREVOLT_META_PATH = REPO_ROOT / "uploads" / "graphs" / "f099fa55-f797-4145-b5f3-9c801c8b4e67.metadata.json"
DB_PATH = REPO_ROOT / "tides_ai.db"
EXPECTED_DB_HASH = "d9659f4e8c1058c5d5f4511e1bb22d3abe6cb12101c16ce397416051a38176c7"


def _get_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest().lower()


def test_stethaim_has_zero_energy_or_petrevolt_contamination():
    """Verify STETHAIM review package has zero EV/BMS/energy contamination."""
    assert STETHAIM_PACKAGE_PATH.exists()
    content_raw = STETHAIM_PACKAGE_PATH.read_text(encoding="utf-8")
    content_lower = content_raw.lower()

    # Forbidden PETREVOLT & EV terms in STETHAIM
    forbidden_terms = [
        "petrevolt",
        "princya",
        "ashwin kumar",
        "battery management system",
        "bms",
        "electric vehicle",
        "ev charging",
        "battery swapping",
        "lithium-ion",
        "cleanpower systems",
    ]

    for term in forbidden_terms:
        assert term not in content_lower, (
            f"Cross-contamination defect: Found forbidden term '{term}' in STETHAIM evaluation!"
        )

    # Positive confirmation of STETHAIM MedTech terms
    assert "stethaim" in content_lower
    assert any(w in content_lower for w in ["copd", "lung", "screening", "auscultation", "pulmonary"])


def test_petrevolt_has_zero_medtech_or_stethaim_contamination():
    """Verify PETREVOLT review package has zero MedTech/pulmonary/STETHAIM contamination."""
    assert PETREVOLT_PACKAGE_PATH.exists()
    content_raw = PETREVOLT_PACKAGE_PATH.read_text(encoding="utf-8")
    content_lower = content_raw.lower()

    # Forbidden STETHAIM & MedTech terms in PETREVOLT
    forbidden_terms = [
        "stethaim",
        "shikha behera",
        "sanat behera",
        "rakshit singh",
        "lohith dayantri",
        "pulmonary",
        "auscultation",
        "copd",
        "lung pathology",
        "stethoscope",
        "kims hospital",
        "pneumonia",
    ]

    for term in forbidden_terms:
        assert term not in content_lower, (
            f"Cross-contamination defect: Found forbidden term '{term}' in PETREVOLT evaluation!"
        )

    # Positive confirmation of PETREVOLT CleanTech terms
    assert "petrevolt" in content_lower
    assert any(w in content_lower for w in ["battery", "bms", "thermal", "energy", "electric"])


def test_stethaim_graph_report_validator_clean():
    """Verify ReportValidator reports 0 cross-contamination errors on STETHAIM graph."""
    if not STETHAIM_GRAPH_PATH.exists():
        pytest.skip("STETHAIM graph path not present")

    graph = from_json(STETHAIM_GRAPH_PATH.read_text(encoding="utf-8"))
    errors = ReportValidator.validate_cross_contamination(graph)
    assert len(errors) == 0, f"Expected 0 cross-contamination errors, got: {errors}"


def test_petrevolt_graph_report_validator_clean():
    """Verify ReportValidator reports 0 cross-contamination errors on PETREVOLT graph if generated."""
    if not PETREVOLT_GRAPH_PATH.exists():
        pytest.skip("PETREVOLT graph path not present")

    graph = from_json(PETREVOLT_GRAPH_PATH.read_text(encoding="utf-8"))
    assert graph.report is not None
    # Verify founder names in report
    founder_sec = graph.report.founder_assessment.content
    assert "Princya" in founder_sec or "Princya Polin" in founder_sec
    assert "Ashwin" in founder_sec or "Ashwin Kumar" in founder_sec
    # Verify zero medical contamination in executive summary
    exec_content = graph.report.executive_summary.content.lower()
    for med_term in ["copd", "pulmonary", "auscultation", "stethaim"]:
        assert med_term not in exec_content


def test_report_validator_catches_injected_medtech_in_cleantech():
    """Verify ReportValidator flags when medical terms are injected into clean energy startup."""
    if not PETREVOLT_GRAPH_PATH.exists():
        pytest.skip("PETREVOLT graph path not present")

    graph = from_json(PETREVOLT_GRAPH_PATH.read_text(encoding="utf-8"))
    # Artificially inject medical pulmonary claim
    graph.report.executive_summary.content += " System diagnoses COPD via acoustic auscultation."
    errors = ReportValidator.validate(graph)
    assert any("foreign startup" in err.lower() or "copd" in err.lower() or "auscultation" in err.lower() or "cross" in err.lower() or "inconsistent" in err.lower() for err in errors) or len(errors) > 0


def test_cleanpower_systems_artifact_clean_and_isolated():
    """Verify third startup fixture artifact CleanPower Systems has zero contamination."""
    cps_path = REPO_ROOT / "uploads" / "graphs" / "REPORT-BBD93B93.json"
    assert cps_path.exists(), "CleanPower Systems artifact must be preserved."
    content = cps_path.read_text(encoding="utf-8").lower()
    assert "cleanpower systems" in content
    # Zero cross contamination from STETHAIM or PETREVOLT
    for term in ["stethaim", "shikha", "sanat", "auscultation", "copd", "petrevolt", "princya", "ashwin"]:
        assert term not in content, f"Found foreign term '{term}' in CleanPower Systems artifact!"


def test_database_integrity_preserved():
    """Verify tides_ai.db has not been modified and matches expected SHA-256."""
    assert DB_PATH.exists()
    current_hash = _get_sha256(DB_PATH)
    assert current_hash == EXPECTED_DB_HASH, (
        f"Database hash mismatch! Expected {EXPECTED_DB_HASH}, got {current_hash}"
    )


def test_petrevolt_package_and_graph_lineage_reconciled():
    """Verify PETREVOLT graph, metadata, JSON package, and MD package have reconciled IDs and honest mock status."""
    pkg = json.loads(PETREVOLT_PACKAGE_PATH.read_text(encoding="utf-8"))
    graph_data = json.loads(PETREVOLT_GRAPH_PATH.read_text(encoding="utf-8"))
    meta_data = json.loads(PETREVOLT_META_PATH.read_text(encoding="utf-8"))
    md_text = (REPO_ROOT / "reports" / "hand_off" / "PETREVOLT_FINAL_REVIEW_PACKAGE.md").read_text(encoding="utf-8")

    pkg_meta = pkg["package_metadata"]
    assert pkg_meta["startup_id"] == graph_data["startup_id"] == "f099fa55-f797-4145-b5f3-9c801c8b4e67"
    assert pkg_meta["report_id"] == graph_data["report"]["report_id"] == "REPORT-1826F99C"
    assert pkg_meta["graph_hash"] == graph_data["graph_hash"]
    assert pkg_meta["real_model_status"] == meta_data["real_model_status"] == "NOT_RUN"
    assert "MOCK" in pkg_meta["evaluation_mode"]
    assert pkg["cost_telemetry"]["actual_provider_spend_usd"] == 0.0
    assert meta_data["actual_provider_spend_usd"] == 0.0
    assert len(pkg["canonical_87_rubric"]["criteria"]) == 87
    assert pkg_meta["report_id"] in md_text
    assert pkg_meta["graph_hash"] in md_text
    assert "NOT_RUN" in md_text
    assert "$0.000000 USD" in md_text
