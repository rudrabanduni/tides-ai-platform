import pytest
import copy
from app.modules.reporting import ReportBuilder, ReportValidator, ReportValidationError
from tests.test_report_builder import complex_graph, DummyObservation


def test_successful_validation(complex_graph):
    report = ReportBuilder.build_due_diligence_report(complex_graph)
    # Validates without error
    res = ReportValidator.validate_report(report, complex_graph)
    assert len(res["errors"]) == 0


def test_empty_section_failure(complex_graph):
    report = ReportBuilder.build_due_diligence_report(complex_graph)
    report.executive_summary = ""
    # Should report error
    res = ReportValidator.validate_report(report, complex_graph)
    assert any("Empty" in err or "Missing" in err for err in res["errors"])
    
    with pytest.raises(ReportValidationError):
        ReportValidator.validate_and_raise(report, complex_graph)


def test_duplicate_observations_failure(complex_graph):
    report = ReportBuilder.build_due_diligence_report(complex_graph)
    # Inject duplicate observation in founder section
    report.founder_assessment.observations.append({
        "id": "obs-1",
        "text": "Duplicate obs reference",
        "confidence": 0.8
    })
    # obs-1 is already in product section, so this should trigger a duplicate error
    res = ReportValidator.validate_report(report, complex_graph)
    assert any("Duplicate" in err for err in res["errors"])


def test_missing_reference_failure(complex_graph):
    report = ReportBuilder.build_due_diligence_report(complex_graph)
    # Reference a missing observation id
    report.product_assessment.observations.append({
        "id": "non_existent_obs_id",
        "text": "Ghost observation",
        "confidence": 0.8
    })
    res = ReportValidator.validate_report(report, complex_graph)
    assert any("Missing Reference" in err for err in res["errors"])


def test_unbacked_recommendations_failure(complex_graph):
    report = ReportBuilder.build_due_diligence_report(complex_graph)
    # Clear observations and evidence but add a recommendation
    report.product_assessment.observations = []
    report.product_assessment.supporting_evidence = []
    report.product_assessment.recommendations = ["Invest in cyber security"]
    res = ReportValidator.validate_report(report, complex_graph)
    assert any("Unbacked Recommendations" in err for err in res["errors"])


def test_hash_mismatch_failure(complex_graph):
    report = ReportBuilder.build_due_diligence_report(complex_graph)
    # Mutate value without recalculating hash
    report.startup_name = "Tampered Startup Name"
    res = ReportValidator.validate_report(report, complex_graph)
    assert any("Invalid Report Hash" in err for err in res["errors"])


def test_graph_hash_mismatch_failure(complex_graph):
    report = ReportBuilder.build_due_diligence_report(complex_graph)
    # Change graph hash
    complex_graph.graph_hash = "MUTATED-GRAPH-HASH"
    res = ReportValidator.validate_report(report, complex_graph)
    assert any("Invalid Graph Hash" in err for err in res["errors"])
