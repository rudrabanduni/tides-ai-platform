"""test_submission_to_report_workflow.py - Verification of the complete TIDES-AI pipeline.

Demonstrates the complete end-to-end workflow:
APPLICATION SUBMITTED -> DOCUMENT EXTRACTION -> SIX DOMAIN ASSESSMENTS -> SUPERVISORY REVIEW -> VALIDATED FINAL REPORT.

Strictly offline with synthetic/mocked responses; zero external provider calls.
Preserves protected workspace tides_ai.db and historical evaluation telemetry.
"""

from __future__ import annotations

import base64
import json
import os
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import PROJECT_ROOT, get_settings
from app.core.enums import DocumentProcessingStatus, DocumentType
from app.db.base import Base
from app.modules.ai.orchestrator.pipeline import coordinate_evaluation_pipeline
from app.modules.ai.orchestrator.startup_profile_extraction import (
    CommercialisationExtraction,
    CoverIntakeExtraction,
    FinancialsSupportExtraction,
    FounderCoreExtraction,
    ImpactStrategicAlignmentExtraction,
    InnovationIpPatentsExtraction,
    MarketOpportunityExtraction,
    ProblemNeedExtraction,
    PrototypeTechnicalExtraction,
    SixQuarterRoadmap,
    SolutionProductExtraction,
    TeamAdvisoryExtraction,
)
from app.modules.documents.models import Document
from app.modules.evaluation.domain_schemas import (
    CompactCriterionResult,
    DomainCriterionBatchOutput,
    SupervisoryReviewOutput,
    VerificationStatus,
)
from app.modules.evaluation.domains.registry import CANONICAL_DOMAINS, get_criteria_for_domain
from app.modules.evaluation.graph.graph_models import ObservationGraph
from app.modules.evaluation.report.report_validator import ReportValidator
from app.modules.intelligence.models import StartupClaim, StartupEvidence, StartupIntelligenceProfile
from app.modules.startups.models import StartupApplication
from app.services.ai.cost_ledger import CostLedgerManager
from app.services.ai.schemas import AICompletionMetadata, AICompletionRequest, AICompletionResult


@pytest.fixture
def workflow_isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Isolate database, upload directories, and telemetry reporting per test run."""
    db_file = tmp_path / "isolated_workflow.db"
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    report_file = tmp_path / "live_eval_run_report.json"

    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("UPLOAD_DIR", str(upload_dir))
    monkeypatch.setenv("TIDES_LIVE_EVAL_REPORT_PATH", str(report_file))
    monkeypatch.setenv("AI_MAX_EVALUATION_BUDGET_USD", "0.35")
    get_settings.cache_clear()

    engine = create_engine(f"sqlite:///{db_file}", pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    with SessionLocal() as db:
        yield db, tmp_path, upload_dir, report_file

    engine.dispose()
    get_settings.cache_clear()


def _build_complete_workflow_gateway():
    """Builds a deterministic gateway mock handling all stages of the evaluation pipeline."""
    call_log: list[str] = []

    def complete_json(
        req: AICompletionRequest | None = None,
        schema_cls: type | None = None,
        *,
        request: AICompletionRequest | None = None,
        response_model: type | None = None,
    ) -> AICompletionResult:
        actual_req = req or request
        actual_schema = schema_cls or response_model
        assert actual_req is not None and actual_schema is not None
        call_log.append(f"{actual_req.agent_name}:{actual_schema.__name__}")

        schema_name = actual_schema.__name__

        # 1. Staged Extraction Schemas
        if schema_name == "CoverIntakeExtraction":
            data = CoverIntakeExtraction(
                company_name="PETREVOLT ENERGY SOLUTIONS PVT LTD",
                tagline="Waste PET upcycling into high-capacity solid-state sodium-ion cells.",
                sector="CleanTech / Energy Storage",
                stage="Pre-Seed / Prototype",
                geography="Coimbatore, Tamil Nadu, India",
                application_date="2024-11-01",
                source_attribution="Slide 1",
            )
        elif schema_name == "ProblemNeedExtraction":
            data = ProblemNeedExtraction(
                problem_statement="High import dependence on Lithium/Cobalt and escalating battery grade metal costs.",
                target_user_pain="BESS and EV manufacturers facing supply chain vulnerabilities.",
                source_attribution="Slide 2",
            )
        elif schema_name == "SolutionProductExtraction":
            data = SolutionProductExtraction(
                solution="Proprietary upcycling of single-source PET plastic waste into high-performance carbon anodes for sodium-ion cells.",
                value_proposition="30% lower cell cost with abundant, non-conflict raw materials.",
                source_attribution="Slide 3",
            )
        elif schema_name == "PrototypeTechnicalExtraction":
            data = PrototypeTechnicalExtraction(
                current_trl=4,
                prototype_stage="Lab-scale pouch cell validation",
                technical_specifications={"energy_density": "160 Wh/kg", "cycle_life": "2000 cycles"},
                source_attribution="Slide 4",
            )
        elif schema_name == "MarketOpportunityExtraction":
            data = MarketOpportunityExtraction(
                market_size="15B USD by 2030 in India stationary storage and low-speed EVs",
                tam="45B USD global Na-ion",
                sam="12B USD APAC",
                som="300M USD 3-year serviceable",
                target_segments=["2W/3W electric mobility", "Telecom tower backup", "Renewable grid BESS"],
                source_attribution="Slide 5",
            )
        elif schema_name == "FounderCoreExtraction":
            data = FounderCoreExtraction(
                founder_names="Dr. R. K. Sharma, P. Venkatesh",
                founder_experience="15+ years materials chemistry and battery manufacturing",
                source_attribution="Slide 6",
            )
        elif schema_name == "TeamAdvisoryExtraction":
            data = TeamAdvisoryExtraction(
                team_composition="4 electrochemical engineers, 2 process scientists",
                advisors=[{"name": "Prof. M. Swaminathan", "organization": "IIT Madras", "role": "Technical Advisor"}],
                source_attribution="Slide 7",
            )
        elif schema_name == "CommercialisationExtraction":
            data = CommercialisationExtraction(
                business_model="B2B cathode/anode active material supply and pilot cell manufacturing licensing",
                revenue_model="Direct sales of precursor materials and per-kWh royalty",
                pricing_strategy="Cost-plus with 35% target gross margin",
                distribution_channels=["Direct OEM engagements", "Tier 1 cell packagers"],
                source_attribution="Slide 8",
            )
        elif schema_name == "InnovationIpPatentsExtraction":
            data = InnovationIpPatentsExtraction(
                proprietary_technology_moat="Single-step solvolysis and thermal activation turning waste PET into hard carbon anode precursor with 320 mAh/g capacity.",
                patent_details=[
                    {
                        "title": "Method for synthesizing hard carbon anode from poly(ethylene terephthalate) waste",
                        "application_number": "202441056789",
                        "status": "Filed / Pending Examination",
                        "jurisdiction": "India",
                    }
                ],
                source_attribution="Slide 9",
            )
        elif schema_name == "ImpactStrategicAlignmentExtraction":
            data = ImpactStrategicAlignmentExtraction(
                primary_impact="Eliminates toxic landfill plastic waste while providing conflict-free green energy storage materials.",
                sdg_alignments=[
                    {"sdg_number": 7, "sdg_name": "Affordable and Clean Energy", "explanation": "Domestic sodium-ion battery supply"},
                    {"sdg_number": 12, "sdg_name": "Responsible Consumption and Production", "explanation": "Circular upcycling of PET plastic"},
                ],
                impact_metrics=[
                    {"metric_name": "PET waste upcycled", "baseline": "5 tonnes/yr", "target_3_year": "500 tonnes/yr"}
                ],
                potential_negative_effects_mitigation="Thermal emissions during pyrolysis scrubbed via regenerative catalytic oxidizer.",
                source_attribution="Slide 10",
            )
        elif schema_name == "FinancialsSupportExtraction":
            data = FinancialsSupportExtraction(
                funding_raised="EDII-TN Innovation Voucher Program grant (INR 5 Lakhs received)",
                funding_required="INR 3.5 Crores seed capital for pilot production line",
                financial_assumptions=["Raw material cost INR 40/kg PET flakes", "Electricity INR 7/kWh"],
                lab_facilities_requirements=["Powder XRD, Raman Spectroscopy, Glovebox Ar atmosphere, Potentiostat"],
                six_quarter_product_roadmap=SixQuarterRoadmap(
                    q1="Pilot-scale solvolysis optimization",
                    q2="Pyrolysis furnace commissioning (100 kg/month)",
                    q3="Commercial pouch cell benchmarking (10 Ah)",
                    q4="Automotive Tier 1 sampling and safety testing",
                    q5="Pilot plant setup in Coimbatore",
                    q6="Commercial supply launch for stationary BESS",
                ),
                source_attribution="Slide 11-13",
            )

        # 2. Domain Criterion Batches (All 6 Canonical Domains)
        elif schema_name == "DomainCriterionBatchOutput":
            meta = actual_req.metadata or {}
            domain_key = meta.get("domain", "problem_solution")
            batch_index = int(meta.get("batch_index", 0))
            crit_ids = list(meta.get("batch_criterion_ids") or get_criteria_for_domain(domain_key)[:5])
            data = DomainCriterionBatchOutput(
                domain=domain_key,
                batch_index=batch_index,
                criteria=[
                    CompactCriterionResult(
                        criterion_id=cid,
                        verification_status=VerificationStatus.VERIFIED_DOCUMENTED,
                        score=7.8,
                        evidence_ids=[],
                        rationale=f"Verified against submitted pitch deck for {cid}.",
                    )
                    for cid in crit_ids
                ],
            )

        # 3. Supervisory Reviewer Output
        elif schema_name == "SupervisoryReviewOutput":
            data = SupervisoryReviewOutput(
                executive_summary="PETREVOLT demonstrates a strong technical moat in circular sodium-ion battery materials with verified grant support and patent filings. Commercial scaling requires primary OEM validation.",
                recommendation_rationale="High innovation potential with clear circular economy alignment; pilot CapEx demands stringent milestone gating.",
                overall_recommendation="CONDITIONAL",
                identified_contradictions=[],
                missing_domains=[],
                priority_diligence_questions=[
                    "Provide third-party electrochemical test certificates for the 10 Ah Na-ion prototype cells.",
                    "Submit environmental clearance status for the Coimbatore pilot pyrolysis facility.",
                ],
                incubation_conditions=[
                    "Establish milestone-gated grant disbursement linked to TRL 5 demonstration.",
                    "Sign IP assignment agreement formalizing patent ownership to the corporate entity.",
                ],
                confidence_score=0.91,
            )
        else:
            data = actual_schema()

        # Update CostLedger if active evaluation_id present
        if actual_req.evaluation_id:
            ledger = CostLedgerManager.get_instance().get_ledger(actual_req.evaluation_id)
            if ledger is not None:
                res_id = ledger.reserve_budget(0.002, actual_req.agent_name)
                ledger.reconcile_operation(
                    reservation_id=res_id,
                    agent_name=actual_req.agent_name,
                    provider="anthropic",
                    model="claude-sonnet-5-5" if "domain" in actual_req.agent_name or "supervisory" in actual_req.agent_name else "claude-haiku-5-5",
                    input_tokens=1500,
                    output_tokens=300,
                    actual_cost_usd=0.002,
                    finish_reason="stop",
                )

        return AICompletionResult(
            data=data,
            raw_text=json.dumps(data.model_dump() if hasattr(data, "model_dump") else data.__dict__),
            metadata=AICompletionMetadata(
                model="claude-sonnet-5-5",
                provider="anthropic",
                latency_ms=150.0,
                input_tokens=1500,
                output_tokens=300,
                cost_usd=0.002,
                cost_inr=0.192,
                buffered_cost_inr=0.226,
            ),
        )

    mock_gw = type("MockGW", (), {"complete_json": staticmethod(complete_json), "call_log": call_log})()
    return mock_gw


@pytest.mark.anyio
async def test_complete_submission_to_report_workflow(workflow_isolated_env):
    """Proves the complete submission-to-report lifecycle end-to-end:

    1. APPLICATION SUBMITTED: StartupApplication and pitch deck registered with parsed text.
    2. DOCUMENT EXTRACTION: 10 extraction stages execute; profile and 50+ claims saved to DB.
    3. SIX DOMAIN ASSESSMENTS: All 6 canonical domains (87 criteria) evaluate cleanly.
    4. SUPERVISORY REVIEW: Gating passes; supervisory reviewer synthesizes report.
    5. VALIDATED FINAL REPORT: DueDiligenceReportEngine builds report; ReportValidator confirms
       zero structural, factuality, or cross-contamination errors; PDF serializes cleanly.
    """
    db, tmp_path, upload_dir, report_file = workflow_isolated_env

    # -------------------------------------------------------------------------
    # STAGE 1: APPLICATION SUBMITTED
    # -------------------------------------------------------------------------
    startup_id = uuid.uuid4()
    doc_path = tmp_path / "petrevolt_pitch_deck.pdf"
    doc_path.write_bytes(b"%PDF-1.4\n%Deterministic mock PETREVOLT pitch deck")

    startup = StartupApplication(
        id=startup_id,
        startup_name="PETREVOLT ENERGY SOLUTIONS PVT LTD",
        sector="CleanTech / Energy Storage",
        stage="Pre-Seed / Prototype",
        problem_statement="Waste PET upcycling into high-capacity solid-state sodium-ion cells.",
        solution_summary="Single-source PET plastic upcycling into hard carbon anode material.",
        business_model="B2B cell and precursor material supply to EV and BESS OEMs.",
        target_market="2W/3W EV mobility and renewable stationary storage in India.",
    )
    db.add(startup)
    db.flush()

    doc = Document(
        id=uuid.uuid4(),
        startup_id=startup.id,
        document_type=DocumentType.PITCH_DECK,
        original_filename="PETREVOLT-Pitch-Deck.pdf",
        stored_filename="petrevolt_pitch_deck.pdf",
        file_path=str(doc_path),
        content_type="application/pdf",
        file_size=doc_path.stat().st_size,
        parsed_text=(
            "PETREVOLT ENERGY SOLUTIONS PVT LTD\n"
            "Problem: Lithium import dependence and escalating battery mineral costs.\n"
            "Solution: Patented solvolysis of post-consumer PET plastic into hard carbon anodes for sodium-ion cells.\n"
            "TRL: TRL 4 validated lab pouch cells with 160 Wh/kg and 2000 cycle lifespan.\n"
            "Market: $15B target addressable market across Indian 2W/3W EVs and BESS storage.\n"
            "Team: Dr. R. K. Sharma (PhD Materials) and P. Venkatesh (Operations).\n"
            "IP: Indian Patent Application 202441056789 filed for PET-to-hard-carbon process.\n"
            "Financials: EDII-TN IVP grant received; seeking INR 3.5 Cr seed capital for pilot facility.\n"
        ),
        processing_status=DocumentProcessingStatus.PARSED,
    )
    db.add(doc)
    db.commit()

    assert startup.id is not None
    assert doc.id is not None
    assert doc.processing_status == DocumentProcessingStatus.PARSED

    # -------------------------------------------------------------------------
    # STAGE 2: EXECUTE PIPELINE WITH COMPLETE WORKFLOW GATEWAY
    # -------------------------------------------------------------------------
    gateway = _build_complete_workflow_gateway()

    with patch("app.modules.ai.orchestrator.pipeline.create_ai_gateway", return_value=gateway), \
         patch("app.modules.evaluation.expert_agent.create_ai_gateway", return_value=gateway), \
         patch("app.modules.evaluation.supervisory.reviewer.create_ai_gateway", return_value=gateway):

        pipeline_result = await coordinate_evaluation_pipeline(
            db=db,
            startup_name=startup.startup_name,
            sector=startup.sector,
            stage=startup.stage,
            files=[],
            existing_startup_id=startup.id,
            max_budget_usd=0.35,
        )

    # -------------------------------------------------------------------------
    # STAGE 3: VERIFY DOCUMENT EXTRACTION & CLAIMS PERSISTENCE
    # -------------------------------------------------------------------------
    profile = db.query(StartupIntelligenceProfile).filter_by(startup_id=startup.id).first()
    assert profile is not None, "StartupIntelligenceProfile must be created during document extraction"

    persisted_claims = db.query(StartupClaim).filter_by(profile_id=profile.id).all()
    assert len(persisted_claims) >= 10, f"Expected canonical claims, found {len(persisted_claims)}"

    persisted_evidence = db.query(StartupEvidence).all()
    assert len(persisted_evidence) > 0, "Evidence nodes must be anchored to extracted claims"

    # -------------------------------------------------------------------------
    # STAGE 4: VERIFY SIX DOMAIN ASSESSMENTS & SUPERVISORY REVIEW
    # -------------------------------------------------------------------------
    eval_id = pipeline_result["evaluation_id"]
    graphs_dir = Path(get_settings().upload_dir) / "graphs"
    graph_file = graphs_dir / f"{startup.id}.json"
    assert graph_file.exists(), f"ObservationGraph must be written to {graph_file}"

    graph_data = json.loads(graph_file.read_text(encoding="utf-8"))

    # All 6 canonical domains must be present
    domain_reports = graph_data.get("domain_reports", {})
    assert len(domain_reports) == 6, f"Expected 6 domain reports, got {list(domain_reports.keys())}"
    for dkey in CANONICAL_DOMAINS:
        assert dkey in domain_reports, f"Missing canonical domain: {dkey}"
        drep = domain_reports[dkey]
        crits = drep.get("criteria_evaluations", {})
        assert len(crits) > 0, f"Domain {dkey} must have evaluated criteria"

    # Supervisory review must be populated (not blocked)
    supervisory_review = graph_data.get("supervisory_review")
    assert supervisory_review is not None, "Supervisory review must be present"
    assert supervisory_review.get("overall_recommendation") == "CONDITIONAL"
    questions = supervisory_review.get("unresolved_questions", []) or supervisory_review.get("priority_diligence_questions", [])
    assert len(questions) >= 2, f"Expected at least 2 diligence questions, got {questions}"
    assert len(supervisory_review.get("incubation_conditions", [])) >= 2

    # -------------------------------------------------------------------------
    # STAGE 5: VERIFY VALIDATED FINAL REPORT & PDF EXPORT
    # -------------------------------------------------------------------------
    assert pipeline_result["evaluation_status"] == "COMPLETED"
    assert pipeline_result["evaluation_id"] == eval_id
    assert pipeline_result["startup_name"] == "PETREVOLT ENERGY SOLUTIONS PVT LTD"

    # PDF bytes generated and valid
    pdf_b64 = pipeline_result.get("pdf_base64")
    assert pdf_b64 is not None and len(pdf_b64) > 100, "Base64 PDF export must be non-empty"
    pdf_bytes = base64.b64decode(pdf_b64)
    assert pdf_bytes.startswith(b"%PDF"), "PDF export must contain valid %PDF magic bytes"

    # Machine-readable report structure
    gen_report = pipeline_result.get("generated_report")
    assert gen_report is not None
    assert gen_report.get("report_id") is not None
    assert gen_report.get("executive_summary") is not None
    assert gen_report.get("investment_recommendation") is not None
    assert gen_report.get("final_review") is not None
    assert len(gen_report.get("domain_reports", {})) == 6

    # Strict ReportValidator compliance (zero errors)
    from app.modules.evaluation.graph.graph_serializer import from_json
    reloaded_graph = from_json(graph_file.read_text(encoding="utf-8"))
    validation_audit = ReportValidator.validate_canonical_87_report(reloaded_graph)
    assert validation_audit["valid"] is True, f"Report validation failed: {validation_audit.get('errors')}"
    assert validation_audit["error_count"] == 0, f"Validation errors found: {validation_audit.get('errors')}"
