"""test_phase3_frontend_backend_integration.py - Verification for Phase 3 Frontend Integration and End-to-End MVP.

Tests:
1. Canonical 6 domain reports and Supervisory Review serialization on DueDiligenceReport.
2. Duck-type compatibility with legacy report structures.
3. Report persistence and retrieval across isolated service restart.
4. Export endpoints for Markdown and PDF with complete supervisory review synthesis.
"""

import tempfile
import os
import pytest
from datetime import datetime

from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType
from app.modules.evaluation.domain_schemas import (
    VerificationStatus,
    CriterionAssessment,
    DomainAssessmentReport,
    SupervisoryReviewOutput,
    FinalReviewAssessment,
    CrossDomainContradiction,
    TargetedRecheckResult,
)
from app.modules.evaluation.report.report_engine import DueDiligenceReportEngine
from app.modules.evaluation.report.report_serializer import ReportSerializer
from app.modules.evaluation.report.report_models import DueDiligenceReport


def build_sample_phase3_graph() -> ObservationGraph:
    """Builds an ObservationGraph populated with the 6 canonical domains and supervisory review."""
    graph = ObservationGraph()
    graph.graph_id = "EVAL-PHASE3-TEST-001"
    graph.startup_name = "AeroVolt SpaceTech"
    graph.sector = "SpaceTech"
    graph.stage = "MVP"

    # 1. Populate 6 Canonical Domains
    domains = [
        ("problem_solution", "Problem & Solution", "PS-01", "Severe satellite thermal throttling", VerificationStatus.VERIFIED_DOCUMENTED),
        ("market_opportunity", "Market Opportunity & Competition", "MO-01", "$4.2B SmallSat constellation market", VerificationStatus.PLAUSIBLE_ESTIMATE),
        ("founder_team", "Founder & Team Capability", "FT-01", "ISRO and IIT alumni with aerospace credentials", VerificationStatus.VERIFIED_DOCUMENTED),
        ("commercialisation", "Business Model & Commercialisation", "BC-01", "B2B SaaS tiered licensing model", VerificationStatus.VERIFIED_DOCUMENTED),
        ("innovation_impact", "Innovation, IP & Impact", "II-01", "2 provisional patents filed for thermal coating", VerificationStatus.VERIFIED_DOCUMENTED),
        ("financials_support", "Financials & Incubation Support", "FI-01", "18-month runway at $25k monthly burn", VerificationStatus.SELF_REPORTED_ONLY),
    ]

    domain_reports = {}
    for dkey, dtitle, crit_id, crit_resp, vstatus in domains:
        crit = CriterionAssessment(
            criterion_id=crit_id,
            criterion_name=f"{dtitle} Criterion 1",
            extracted_startup_response=crit_resp,
            assessment_narrative=f"Specialist rigorous assessment of {crit_id}.",
            source_locations=["Slide 4", "PitchDeck.pdf"],
            evidence_ids=[f"EV-{crit_id}"],
            verification_status=vstatus,
            strengths=[f"Strong documentation for {crit_id}"],
            weaknesses=[],
            risks=[],
            confidence_score=0.90,
        )
        rep = DomainAssessmentReport(
            domain=dkey,
            domain_key=dkey,
            domain_title=dtitle,
            evaluation_id="EVAL-PHASE3-TEST-001",
            startup_id="STARTUP-001",
            criteria_evaluated=[crit_id],
            criteria_evaluations={crit_id: crit},
            summary=f"Domain summary for {dtitle}.",
            executive_summary=f"Executive synthesis narrative for {dtitle}.",
            strengths=[f"Primary strength for {dtitle}"],
            weaknesses=[],
            unsupported_claims=[],
            contradictions=[],
            composite_domain_confidence=0.88,
            cost_usd=0.045,
            model_used="claude-3-5-sonnet",
        )
        domain_reports[dkey] = rep
        graph.domain_assessments[dkey] = rep

    graph.domain_reports = domain_reports

    # 2. Populate Supervisory Review
    final_review = FinalReviewAssessment(
        report_id="DD-AEROVOLT-2026",
        evaluation_id="EVAL-PHASE3-TEST-001",
        startup_id="STARTUP-001",
        startup_name="AeroVolt SpaceTech",
        sector="SpaceTech",
        stage="MVP",
        executive_summary="AeroVolt demonstrates exceptional thermal dissipation technology suitable for deep orbital satellites.",
        recommendation_rationale="Strong TRL-5 validation and deep domain expertise justify strategic incubation.",
        overall_recommendation="INCUBATE",
        incubation_conditions=[
            "Execute thermal vacuum test milestone verification within 90 days.",
            "Complete key hire for guidance systems software engineer.",
        ],
        recommended_tranches=[
            {"tranche_name": "Tranche 1", "milestone": "Incubation Onboarding", "amount": 1000000, "currency": "INR"},
            {"tranche_name": "Tranche 2", "milestone": "Vacuum Chamber Validation", "amount": 1500000, "currency": "INR"},
        ],
        domain_reports=domain_reports,
        cross_domain_findings=[
            "Thermal patent directly protects unit economics from incumbent duplication.",
        ],
        identified_contradictions=[
            CrossDomainContradiction(
                contradiction_id="CONTRA-01",
                domain_a="commercialisation",
                criterion_a="TRL-01",
                claim_a_summary="Sub-assembly ready for flight testing Q3.",
                domain_b="financials_support",
                criterion_b="FS-01",
                claim_b_summary="Flight qualification budget scheduled for Q4.",
                nature_of_conflict="TIMING_DISCREPANCY",
                resolution_status="RESOLVED",
                resolution_rationale="Founders clarified flight tests occur in Q4 with sub-assembly testing in Q3.",
            )
        ],
        rechecks_triggered=[
            TargetedRecheckResult(
                recheck_id="RC-001",
                domain_key="commercialisation",
                criterion_id="TRL-01",
                original_verification_status="SELF_REPORTED_ONLY",
                updated_verification_status="VERIFIED_DOCUMENTED",
                original_finding_summary="Lab test report unverified.",
                updated_finding_summary="Confirmed lab test chamber report from Slide 4.",
                recheck_reasoning="Evidence re-verified against raw document annexure.",
                evidence_confirmed=True,
                unresolved_disagreement=False,
                cost_usd=0.012,
            )
        ],
        unresolved_disagreements=[],
        investment_score=86.5,
        confidence_score=0.91,
        reviewer_agent_version="2.0.0",
        cost_summary={"total_cost_usd": 0.28, "total_cost_inr": 26.88},
    )

    graph.final_review = final_review
    graph.supervisory_review = final_review
    return graph


def test_due_diligence_report_engine_embeds_canonical_domains_and_supervisory_review():
    """Verifies that DueDiligenceReportEngine attaches both final_review and domain_reports."""
    graph = build_sample_phase3_graph()
    graph = DueDiligenceReportEngine.generate(graph)

    report = graph.report
    assert isinstance(report, DueDiligenceReport)
    assert report.final_review is not None
    assert report.final_review.overall_recommendation == "INCUBATE"
    assert report.final_review.investment_score == 86.5

    # Check 6 canonical domains presence
    assert report.domain_reports is not None
    assert "problem_solution" in report.domain_reports
    assert "commercialisation" in report.domain_reports
    assert "market_opportunity" in report.domain_reports
    assert "founder_team" in report.domain_reports
    assert "financials_support" in report.domain_reports
    assert "innovation_impact" in report.domain_reports

    # Check metadata serialization
    assert report.metadata["final_review"]["overall_recommendation"] == "INCUBATE"
    assert "problem_solution" in report.metadata["domain_reports"]


def test_report_serializer_markdown_and_pdf_exports():
    """Verifies that export_markdown and export_pdf include the Supervisory Review and 6 domains."""
    graph = build_sample_phase3_graph()
    graph = DueDiligenceReportEngine.generate(graph)
    report = graph.report

    # Export Markdown
    md = ReportSerializer.export_markdown(report)
    assert "# Final Supervisory AI Review & Due Diligence Synthesis" in md
    assert "INCUBATE" in md
    assert "AeroVolt SpaceTech" in md or "Thermal patent" in md
    assert "TIMING_DISCREPANCY" in md
    assert "Institutional Incubation Conditions" in md

    # Export PDF
    pdf_bytes = ReportSerializer.export_pdf_data(report)
    assert pdf_bytes.startswith(b"%PDF")
    assert len(pdf_bytes) > 2000


def test_report_persistence_and_retrieval_simulation():
    """Simulates saving a graph to JSON, tearing down, and reconstructing it."""
    graph = build_sample_phase3_graph()
    graph = DueDiligenceReportEngine.generate(graph)

    # Serialize to JSON string
    json_str = ReportSerializer.to_json(graph)
    assert len(json_str) > 500

    # Simulate fresh process restart by deserializing from JSON string
    reconstructed_graph = ReportSerializer.from_json(json_str)
    assert reconstructed_graph.report is not None
    rec_rep = reconstructed_graph.report

    # Verify report ID and sections
    assert rec_rep.report_id == graph.report.report_id
    assert "Executive Summary" in rec_rep.executive_summary.title

    # Verify Supervisory Review and Canonical Domains survived deserialization
    assert rec_rep.metadata is not None
    assert rec_rep.metadata.get("final_review") is not None
    assert rec_rep.metadata["final_review"]["overall_recommendation"] == "INCUBATE"
    assert "problem_solution" in rec_rep.metadata["domain_reports"]
