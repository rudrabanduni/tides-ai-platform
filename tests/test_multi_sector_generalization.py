"""Multi-sector offline generalization & schema integrity suite across 6 distinct industries."""
from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from io import BytesIO
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.datastructures import UploadFile as StarletteUploadFile

from app.core.config import get_settings
from app.db.base import Base
from app.modules.ai.orchestrator.pipeline import coordinate_evaluation_pipeline
from app.modules.ai.orchestrator.startup_profile_extraction import (
    CompetitorEntry,
    FounderEntry,
    KeyFeatureBenefit,
    PatentEntry,
    PilotAgreementEntry,
    StartupProfileExtraction,
    ThreeYearMetric,
)
from app.modules.evaluation.domain_schemas import (
    CompactCriterionResult,
    CompactDomainAssessment,
    CompactDomainRisk,
    DomainCriterionBatchOutput,
    SupervisoryReviewOutput,
)
from app.modules.evaluation.domains.registry import CANONICAL_DOMAINS, CRITERIA_DIRECTORY, get_criteria_for_domain
from app.modules.evaluation.expert_agent import AgentAssessment
from app.modules.evaluation.graph.graph_serializer import from_json
from app.modules.evaluation.report.report_validator import ReportValidator
from app.services.ai.mock import MockAIGateway
from app.services.ai.real_pipeline import generate_assessment_from_context
from app.services.ai.schemas import AICompletionRequest


@dataclass(frozen=True)
class SectorScenario:
    startup_name: str
    sector: str
    stage: str
    tagline: str
    problem_statement: str
    solution: str
    technology: str
    market_size: str
    business_model: str
    founders: list[str]
    patent_title: str | None
    burn_rate: str | None
    current_revenue: str | None
    paying_customers: str | None
    has_signed_pilot: bool
    missing_criteria: frozenset[str] = field(default_factory=frozenset)
    non_fabricated_no_ip: bool = False
    expected_terms: tuple[str, ...] = ()
    forbidden_terms: tuple[str, ...] = ()


SCENARIOS: list[SectorScenario] = [
    SectorScenario(
        startup_name="CardioSense Diagnostics",
        sector="MedTech",
        stage="Seed",
        tagline="Wearable dual-lead ECG patch for continuous clinical arrhythmia screening.",
        problem_statement="Paroxysmal atrial fibrillation is missed in 40% of single-visit outpatient clinics.",
        solution="Wireless dual-lead ECG patch paired with clinical arrhythmia triage software.",
        technology="Low-noise ambulatory biopotential ADC front-end and atrial fibrillation classifier.",
        market_size="$8.4 Billion global cardiac ambulatory telemetry market",
        business_model="B2B diagnostic per-study SaaS plus reusable patch hardware lease to cardiology clinics.",
        founders=["Dr. Meera Nair", "Rohan Kulkarni"],
        patent_title=None,  # Deliberate missing IP evidence
        burn_rate="Rs 4.2 Lakh per month",
        current_revenue="0",
        paying_customers="0",
        has_signed_pilot=False,  # Deliberate missing signed commercial pilot
        missing_criteria=frozenset({"BC-10"}),
        non_fabricated_no_ip=True,
        expected_terms=("CardioSense", "ECG", "arrhythmia"),
        forbidden_terms=("PETREVOLT", "STETHAIM", "CleanPower", "solvolysis", "LoRaWAN", "weld seam", "hydrogen"),
    ),
    SectorScenario(
        startup_name="HelioGrid Thermal Systems",
        sector="Clean Energy",
        stage="Series A",
        tagline="Modular concentrated solar thermal storage for textile dyeing steam.",
        problem_statement="Industrial textile process heat relies on costly high-emission coal boilers.",
        solution="High-temperature parabolic trough collectors with phase-change thermal storage tanks.",
        technology="Latent-heat nitrate salt storage modules delivering pressurized industrial steam at 220C.",
        market_size="$14.2 Billion industrial process heat decarbonization market",
        business_model="Heat-as-a-Service PPA contracts per metric tonne of steam delivered.",
        founders=["Arjun Deshmukh", "Kavita Bansal"],
        patent_title="Phase-Change Heat Exchanger Manifold for Dyeing Boilers",
        burn_rate="Rs 9.0 Lakh per month",
        current_revenue="Rs 1.4 Crore ARR",
        paying_customers="3 textile clusters",
        has_signed_pilot=True,
        expected_terms=("HelioGrid", "solar thermal", "steam"),
        forbidden_terms=("PETREVOLT", "STETHAIM", "CleanPower", "ECG", "SOC2", "orchard", "weld seam"),
    ),
    SectorScenario(
        startup_name="VoltCraft Solid-State Labs",
        sector="Battery Tech",
        stage="Pre-Seed",
        tagline="Ceramic-coated silicon-graphite composite separator for thermal runaway prevention.",
        problem_statement="Fast-charging commercial LFP packs face dendritic shorting and separator shrinkage.",
        solution="Alumina-ceramic coated microporous separator film compatible with commercial jelly-roll lines.",
        technology="Sub-micron ceramic slurry coating engineered for dimensional stability up to 210C.",
        market_size="$11.5 Billion specialty battery separator film market",
        business_model="Roll-to-roll specialty separator film supply agreements with cell manufacturers.",
        founders=["Siddharth Menon", "Pooja Krishnan"],
        patent_title="Ceramic-Reinforced Composite Separator Coating Formulation",
        burn_rate=None,  # Deliberate missing financial burn disclosure
        current_revenue=None,
        paying_customers=None,
        has_signed_pilot=False,
        missing_criteria=frozenset({"FI-05", "BC-09"}),
        expected_terms=("VoltCraft", "separator", "ceramic"),
        forbidden_terms=("PETREVOLT", "STETHAIM", "CleanPower", "solvolysis", "ECG", "LoRaWAN", "SOC2"),
    ),
    SectorScenario(
        startup_name="AuditFlow Compliance AI",
        sector="Enterprise SaaS",
        stage="Seed",
        tagline="Automated SOC2 Type II and RBI cybersecurity control evidence engine.",
        problem_statement="Fintech engineering teams lose 600+ developer hours annually collecting audit screenshots.",
        solution="Read-only API connectors generating cryptographic SOC2 and ISO27001 control attestations.",
        technology="Deterministic policy-as-code scanner across cloud IAM, CI/CD pipelines, and ticketers.",
        market_size="$9.6 Billion global compliance automation software market",
        business_model="Annual recurring B2B SaaS subscription tiered by cloud resource count.",
        founders=["Nikhil Joshi", "Tanya Arora"],
        patent_title=None,
        burn_rate="Rs 5.5 Lakh per month",
        current_revenue="Rs 6.5 Lakh MRR",
        paying_customers="9",
        has_signed_pilot=True,
        expected_terms=("AuditFlow", "SOC2", "compliance"),
        forbidden_terms=("PETREVOLT", "STETHAIM", "CleanPower", "ECG", "hydrogen", "LoRaWAN", "weld seam"),
    ),
    SectorScenario(
        startup_name="SoilPulse Precision Systems",
        sector="AgriTech",
        stage="Pre-Seed",
        tagline="Solar LoRaWAN root-zone moisture and NPK spectrometry telemetry for orchards.",
        problem_statement="Himalayan apple growers lose 25% fertilizer efficiency from unscheduled flood irrigation.",
        solution="Edge optical nitrate sensors transmitting automated irrigation schedules via LoRaWAN.",
        technology="Dual-depth dielectric moisture probe fused with microfluidic optical NPK sensing.",
        market_size="$6.8 Billion precision horticulture and smart irrigation market",
        business_model="Hardware kit sales plus seasonal agronomist advisory SaaS for cooperatives.",
        founders=["Harshvardhan Rawat", "Neha Chauhan"],
        patent_title="Optical Soil Nitrate Probe with Solar LoRaWAN Transceiver",
        burn_rate="Rs 2.1 Lakh per month",
        current_revenue="Rs 3.2 Lakh",
        paying_customers="4 grower FPOs",
        has_signed_pilot=True,
        expected_terms=("SoilPulse", "LoRaWAN", "orchards"),
        forbidden_terms=("PETREVOLT", "STETHAIM", "CleanPower", "ECG", "SOC2", "cobot", "hydrogen"),
    ),
    SectorScenario(
        startup_name="WeldGuard Robotics",
        sector="Manufacturing",
        stage="Seed",
        tagline="Structured-light 3D laser seam-inspection cobot for tier-1 chassis welding.",
        problem_statement="Manual ultrasonic weld sampling misses porosity defects in high-throughput auto lines.",
        solution="Inline cobot cell executing sub-millimeter 3D optical bead inspection on moving fixtures.",
        technology="High-speed laser triangulation profilometer with real-time spatter-invariant CNN classifier.",
        market_size="$7.9 Billion automated industrial machine vision and welding QA market",
        business_model="Turnkey inspection workcell capex plus annual metrology software license.",
        founders=["Vikramaditya Rao", "Shruti Patwardhan"],
        patent_title="Laser Triangulation Weld Seam Porosity Classifier Assembly",
        burn_rate="Rs 7.8 Lakh per month",
        current_revenue="Rs 48 Lakh",
        paying_customers="2 auto ancillaries",
        has_signed_pilot=True,
        expected_terms=("WeldGuard", "cobot", "seam"),
        forbidden_terms=("PETREVOLT", "STETHAIM", "CleanPower", "ECG", "SOC2", "LoRaWAN", "hydrogen"),
    ),
]


def _build_profile_for_scenario(s: SectorScenario) -> StartupProfileExtraction:
    return StartupProfileExtraction(
        company_name=s.startup_name,
        tagline=s.tagline,
        sector=s.sector,
        stage=s.stage,
        geography="India",
        application_date="2026-10-20",
        problem_statement=s.problem_statement,
        who_is_affected=f"Enterprise & institutional buyers in {s.sector}",
        current_workarounds="Manual legacy workflows with high operational overhead",
        evidence_of_problem=f"Field interviews across 20 {s.sector} operators confirmed recurring bottlenecks.",
        why_problem_persists="High integration cost and lack of domain-tuned automation.",
        solution=s.solution,
        key_features_benefits=[
            KeyFeatureBenefit(feature=f"{s.sector} core architecture", benefit="Measurable efficiency improvement"),
            KeyFeatureBenefit(feature="Turnkey deployment workflow", benefit="Rapid commissioning without downtime"),
            KeyFeatureBenefit(feature="Diagnostic telemetry dashboard", benefit="Auditable operational visibility"),
        ],
        unique_value_proposition=s.tagline,
        current_trl=5,
        trl_justification=f"Validated in {s.sector} lab and bench environment.",
        technology=s.technology,
        market_size=s.market_size,
        sam="25% domestic serviceable footprint",
        som_3_5_year="5% regional share in 3-5 years",
        market_cagr="16.0%",
        cagr_source="Sector Benchmark Outlook 2026",
        key_market_drivers=[f"{s.sector} digitization", "Unit cost reduction pressure"],
        market=f"Target buyers across {s.sector}",
        competitor_details=[
            CompetitorEntry(name=f"Incumbent {s.sector} Vendor A", country="Germany", approach="Legacy hardware"),
            CompetitorEntry(name=f"Regional Rival B", country="India", approach="Manual services"),
            CompetitorEntry(name=f"Global Challenger C", country="USA", approach="Enterprise suite"),
        ],
        competition="Incumbent vendors lacking modular automation.",
        founder_details=[
            FounderEntry(name=s.founders[0], role="Co-Founder & CEO", relevant_experience=f"8 years in {s.sector}"),
            FounderEntry(name=s.founders[1], role="Co-Founder & CTO", relevant_experience=f"Engineering lead in {s.sector}"),
        ],
        founders=list(s.founders),
        founder_roles=["Co-Founder & CEO", "Co-Founder & CTO"],
        team=f"{s.founders[0]} and {s.founders[1]} bring domain engineering depth in {s.sector}.",
        business_model=s.business_model,
        revenue_model=s.business_model,
        current_revenue=s.current_revenue,
        paying_customers=s.paying_customers,
        pilot_agreements=[
            PilotAgreementEntry(
                partner_name=f"{s.sector} Anchor Partner",
                agreement_type="Signed Pilot",
                is_signed=True,
                contract_value="Rs 25 Lakh",
            )
        ]
        if s.has_signed_pilot
        else [],
        patent_details=[PatentEntry(title=s.patent_title, application_number="202611000123", status="Filed", jurisdiction="India")]
        if s.patent_title
        else [],
        patents=s.patent_title,
        three_year_revenue=ThreeYearMetric(year_1="Rs 1 Cr", year_2="Rs 4 Cr", year_3="Rs 12 Cr")
        if s.current_revenue is not None
        else None,
        burn_rate=s.burn_rate,
        traction=f"{s.startup_name} validated core workflow in {s.sector}.",
    )


def _make_sector_gateway(scenario: SectorScenario) -> MockAIGateway:
    profile = _build_profile_for_scenario(scenario)
    profile_dump = profile.model_dump()

    def response_factory(request: AICompletionRequest) -> dict[str, Any]:
        if request.operation_type == "extraction":
            return profile_dump

        if request.agent_name == "supervisory_review":
            return SupervisoryReviewOutput(
                executive_summary=(
                    f"{scenario.startup_name} operates in {scenario.sector} ({scenario.stage}) delivering {scenario.solution} "
                    f"Using {scenario.technology} against {scenario.market_size}."
                ),
                recommendation_rationale=(
                    f"{scenario.startup_name} shows clear {scenario.sector} differentiation under {scenario.founders[0]}; "
                    f"tranches gate on pilot and verification milestones."
                ),
                overall_recommendation="CONDITIONAL",
                identified_contradictions=[],
                missing_domains=[],
                priority_diligence_questions=[f"Verify {scenario.sector} deployment metrics for {scenario.startup_name}."],
                incubation_conditions=[f"Track {scenario.sector} milestone KPIs quarterly."],
                recommended_tranches=[{"tranche": 1, "description": f"{scenario.sector} pilot verification"}],
                investment_score=74.0 if not scenario.missing_criteria else 67.5,
                confidence_score=0.84,
            ).model_dump()

        if request.agent_name.startswith("domain_") or request.operation_type == "expert_evaluation":
            domain_key = (request.metadata or {}).get("domain") or request.agent_name.replace("domain_", "", 1)
            batch_cids = (request.metadata or {}).get("batch_criterion_ids")
            crit_ids = list(batch_cids) if batch_cids else get_criteria_for_domain(domain_key)
            results = []
            unknowns = []
            for cid in crit_ids:
                if cid in scenario.missing_criteria or (scenario.non_fabricated_no_ip and cid == "II-07"):
                    results.append(
                        CompactCriterionResult(
                            criterion_id=cid,
                            verification_status="MISSING_INFORMATION",
                            score=None,
                            evidence_ids=[],
                            rationale="Evidence not submitted in dossier.",
                        )
                    )
                    unknowns.append(f"{cid} documentation not provided")
                else:
                    results.append(
                        CompactCriterionResult(
                            criterion_id=cid,
                            verification_status="VERIFIED_DOCUMENTED",
                            score=7.6,
                            evidence_ids=[],
                            rationale=f"Verified {scenario.sector} dossier submission.",
                        )
                    )
            if batch_cids is not None:
                return DomainCriterionBatchOutput(
                    domain=domain_key,
                    batch_index=int((request.metadata or {}).get("batch_index", 0)),
                    criteria=results,
                ).model_dump()
            return CompactDomainAssessment(
                domain=domain_key,
                domain_conclusion=f"{scenario.startup_name} {domain_key} assessment completed for {scenario.sector}.",
                criteria=results,
                strengths=[f"Clear {scenario.sector} technical fit for {scenario.startup_name}."],
                risks=[CompactDomainRisk(id="R1", severity="Medium", description=f"{scenario.sector} scale-up validation pending.", mitigation="Milestone gating")],
                information_requests=[f"Submit updated {scenario.sector} audit records."],
                unknowns=unknowns[:3],
                contradictions=[],
                confidence_score=0.82,
            ).model_dump()

        # Legacy AIOrchestrator AgentAssessment branch
        domain = (request.metadata or {}).get("domain", "founder")
        return generate_assessment_from_context(request.user_prompt, domain, AgentAssessment).model_dump()

    return MockAIGateway(response_factory=response_factory)


@pytest.fixture()
def isolated_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s.sector for s in SCENARIOS])
def test_multi_sector_pipeline_generalization(
    scenario: SectorScenario,
    isolated_db: Session,
    tmp_path: Path,
) -> None:
    """Verify full offline pipeline across 6 distinct industries with zero cross-sector contamination or fabricated missing evidence."""
    upload_dir = tmp_path / "uploads"
    graphs_dir = upload_dir / "graphs"
    upload_dir.mkdir(parents=True, exist_ok=True)
    graphs_dir.mkdir(parents=True, exist_ok=True)

    dossier_lines = [
        f"Company Name: {scenario.startup_name}",
        f"Sector: {scenario.sector}",
        f"Stage: {scenario.stage}",
        f"Tagline: {scenario.tagline}",
        f"Problem: {scenario.problem_statement}",
        f"Solution: {scenario.solution}",
        f"Technology: {scenario.technology}",
        f"Market Size: {scenario.market_size}",
        f"Business Model: {scenario.business_model}",
        f"Founders: {', '.join(scenario.founders)}",
    ]
    if scenario.patent_title:
        dossier_lines.append(f"Patent: {scenario.patent_title}")
    if scenario.burn_rate:
        dossier_lines.append(f"Monthly Burn Rate: {scenario.burn_rate}")
    if scenario.current_revenue:
        dossier_lines.append(f"Current Revenue: {scenario.current_revenue}")

    dossier_bytes = "\n".join(dossier_lines).encode("utf-8")
    slug = scenario.startup_name.lower().replace(" ", "_")
    upload_file = StarletteUploadFile(filename=f"{slug}_dossier.txt", file=BytesIO(dossier_bytes))

    gateway = _make_sector_gateway(scenario)
    factory_targets = (
        "app.services.ai.gateway.create_ai_gateway",
        "app.modules.ai.orchestrator.pipeline.create_ai_gateway",
        "app.modules.evaluation.expert_agent.create_ai_gateway",
        "app.modules.evaluation.domains.base.create_ai_gateway",
        "app.modules.evaluation.supervisory.reviewer.create_ai_gateway",
        "app.modules.intelligence.ai.extractor.create_ai_gateway",
    )

    settings = get_settings()
    with (
        patch.object(settings, "upload_dir", str(upload_dir)),
        patch.object(settings, "ai_provider", "mock"),
        patch(factory_targets[0], return_value=gateway),
        patch(factory_targets[1], return_value=gateway),
        patch(factory_targets[2], return_value=gateway),
        patch(factory_targets[3], return_value=gateway),
        patch(factory_targets[4], return_value=gateway),
        patch(factory_targets[5], return_value=gateway),
    ):
        result = asyncio.run(
            coordinate_evaluation_pipeline(
                db=isolated_db,
                startup_name=scenario.startup_name,
                sector=scenario.sector,
                stage=scenario.stage,
                files=[upload_file],
            )
        )

    assert result["evaluation_status"] == "COMPLETED"
    assert result["evaluation_mode"] == "MOCK_SIMULATED_OFFLINE"
    startup_id = result["startup_id"]

    graph_path = graphs_dir / f"{startup_id}.json"
    assert graph_path.exists(), f"Missing serialized graph at {graph_path}"
    loaded_graph = from_json(graph_path.read_text(encoding="utf-8"))

    def _crit_evals(rep: Any) -> dict[str, Any]:
        return rep.get("criteria_evaluations", {}) if isinstance(rep, dict) else rep.criteria_evaluations

    # 1. All 6 canonical domains and canonical criteria coverage
    assert set(loaded_graph.domain_reports.keys()) == set(CANONICAL_DOMAINS.keys())
    total_domain_criteria = sum(len(_crit_evals(rep)) for rep in loaded_graph.domain_reports.values())
    expected_domain_criteria = sum(len(get_criteria_for_domain(d)) for d in CANONICAL_DOMAINS)
    assert total_domain_criteria == expected_domain_criteria
    assert len(CRITERIA_DIRECTORY) == 87

    # 2. ReportValidator.validate_structured must pass with zero errors
    validation = ReportValidator.validate_structured(loaded_graph)
    assert validation["errors"] == [], f"Unexpected ReportValidator errors for {scenario.sector}: {validation['errors']}"
    assert validation["valid"] is True

    # 3. Sector-faithful grounding and zero cross-sector contamination
    serialized_report = json.dumps(result["generated_report"], default=str).lower()
    for expected in scenario.expected_terms:
        assert expected.lower() in serialized_report, (
            f"Expected term '{expected}' missing from {scenario.sector} report"
        )
    for forbidden in scenario.forbidden_terms:
        assert forbidden.lower() not in serialized_report, (
            f"Cross-sector contamination: forbidden term '{forbidden}' appeared in {scenario.sector} report"
        )

    # 4. Missing evidence and non-patent disclosures must never be fabricated
    if scenario.missing_criteria or scenario.non_fabricated_no_ip:
        all_evals = {}
        for rep in loaded_graph.domain_reports.values():
            all_evals.update(_crit_evals(rep))
        for missing_cid in scenario.missing_criteria:
            crit = all_evals[missing_cid]
            ver_status = crit.get("verification_status") if isinstance(crit, dict) else crit.verification_status
            score = crit.get("score") if isinstance(crit, dict) else crit.score
            assert str(ver_status).endswith("MISSING_INFORMATION")
            assert score is None
        if scenario.non_fabricated_no_ip:
            ip_crit = all_evals["II-07"]
            ip_status = ip_crit.get("verification_status") if isinstance(ip_crit, dict) else ip_crit.verification_status
            ip_score = ip_crit.get("score") if isinstance(ip_crit, dict) else ip_crit.score
            ip_resp = str(ip_crit.get("extracted_startup_response") if isinstance(ip_crit, dict) else ip_crit.extracted_startup_response)
            assert str(ip_status) == "SELF_REPORTED_ONLY"
            assert ip_score is None
            assert "no ip" in ip_resp.lower()
