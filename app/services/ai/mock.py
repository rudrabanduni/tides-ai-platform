from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ValidationError

from app.core.config import get_settings
from app.services.ai.cost_ledger import CostLedgerManager, EvaluationCostLedger
from app.services.ai.exceptions import AIBudgetExhaustedError, AIResponseParseError
from app.services.ai.pricing import get_pricing_catalog, resolve_cache_attribution
from app.services.ai.router import ModelRouter
from app.services.ai.schemas import AICompletionMetadata, AICompletionRequest, AICompletionResult

ResponseFactory = Callable[[AICompletionRequest], dict[str, Any] | BaseModel]

MOCK_RATIONALE_PREFIX = "MOCK:"

#: Numbered groups in a synthetic deck ("Founder 1 Name: ...") -> list fields of StartupProfileExtraction
_MOCK_GROUPS = {
    "founder": "founder_details",
    "competitor": "competitor_details",
    "patent": "patent_details",
    "pilot": "pilot_agreements",
    "advisor": "advisors",
    "team_member": "core_team",
    "hire": "hiring_plan",
    "sdg": "sdg_alignments",
    "impact_metric": "impact_metrics",
    "feature": "key_features_benefits",
}
_MIN_GROUNDED_FIELDS = 10


def _mock_profile_from_document_text(prompt: str) -> Any | None:
    """Deterministic document-grounded extraction for offline demonstrations.

    Parses "Field Label: value" lines from the document text embedded in the extraction prompt.
    Labels map onto StartupProfileExtraction field names (case/space-insensitive); numbered
    groups ("Founder 2 Role: ...") populate nested lists; "Three Year Revenue Year 1:" and
    "Six Quarter Product Roadmap Q3:" populate nested models; list fields are ";"-separated.
    Returns None when the text does not look like a labelled synthetic document, so legacy
    fixtures keep their previous behaviour.
    """
    import re
    import typing

    from pydantic import BaseModel as _BM

    from app.modules.ai.orchestrator.startup_profile_extraction import StartupProfileExtraction

    def _norm(label: str) -> str:
        return re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")

    def _inner(annotation: Any) -> tuple[Any, bool]:
        """Returns (inner_type, is_list) for Optional[...] / List[...] annotations."""
        args = typing.get_args(annotation)
        origin = typing.get_origin(annotation)
        if origin in (list, typing.List):
            return (args[0] if args else str), True
        for a in args:
            if a is type(None):
                continue
            t, is_list = _inner(a)
            return t, is_list
        return annotation, False

    fields = StartupProfileExtraction.model_fields
    values: dict[str, Any] = {}
    nested: dict[str, dict[str, Any]] = {}
    groups: dict[str, dict[int, dict[str, Any]]] = {}

    for raw_line in prompt.splitlines():
        line = raw_line.strip()
        if ":" not in line or len(line) > 600:
            continue
        label, _, value = line.partition(":")
        value = value.strip()
        key = _norm(label)
        if not value or not key or len(key) > 60:
            continue
        gm = re.match(r"^(" + "|".join(_MOCK_GROUPS) + r")_(\d+)_(.+)$", key)
        if gm:
            groups.setdefault(_MOCK_GROUPS[gm.group(1)], {}).setdefault(int(gm.group(2)), {})[gm.group(3)] = value
            continue
        if key in fields:
            values[key] = value
            continue
        for fname in fields:
            if key.startswith(fname + "_"):
                inner, is_list = _inner(fields[fname].annotation)
                if isinstance(inner, type) and issubclass(inner, _BM) and not is_list:
                    sub = key[len(fname) + 1:]
                    if sub in inner.model_fields:
                        nested.setdefault(fname, {})[sub] = value
                break

    if len(values) + len(nested) + len(groups) < _MIN_GROUNDED_FIELDS:
        return None

    def _coerce(target: Any, raw: str) -> Any:
        if target is int:
            m = re.search(r"\d+", raw)
            return int(m.group(0)) if m else None
        if target is bool:
            return raw.strip().lower() in ("yes", "true", "signed", "y")
        return raw

    payload: dict[str, Any] = {}
    for fname, raw in values.items():
        inner, is_list = _inner(fields[fname].annotation)
        if is_list and inner is str:
            payload[fname] = [x.strip() for x in raw.split(";") if x.strip()]
        elif not is_list:
            payload[fname] = _coerce(inner, raw)
    for fname, sub in nested.items():
        inner, _ = _inner(fields[fname].annotation)
        payload[fname] = inner(**{k: _coerce(_inner(inner.model_fields[k].annotation)[0], v) for k, v in sub.items()})
    for fname, entries in groups.items():
        inner, _ = _inner(fields[fname].annotation)
        items = []
        for _, sub in sorted(entries.items()):
            kwargs = {k: _coerce(_inner(inner.model_fields[k].annotation)[0], v) for k, v in sub.items() if k in inner.model_fields}
            try:
                items.append(inner(**kwargs))
            except Exception:
                continue
        payload[fname] = items
    if "founder_details" in payload and "founders" not in payload:
        payload["founders"] = [f.name for f in payload["founder_details"] if getattr(f, "name", None)]
        payload["founder_roles"] = [f.role or "Founder" for f in payload["founder_details"] if getattr(f, "name", None)]
    return StartupProfileExtraction(**payload)


def _mock_criterion_from_prompt(cid: str, user_prompt: str) -> Any:
    """Deterministic, evidence-aware synthetic criterion result for offline demonstrations.

    Reads only what the batch prompt actually showed: cited evidence handles ("E3") under the
    criterion heading, a bare claim, or "<none extracted>". Never cites a handle that was not shown.
    Scores are a stable function of the criterion ID (no randomness), and every rationale is
    explicitly prefixed "MOCK:" so synthetic output can never be mistaken for a real assessment.
    """
    import hashlib
    import re

    from app.modules.evaluation.domain_schemas import BatchCriterionResult

    block = ""
    match = re.search(rf"^\[{re.escape(cid)}\][^\n]*\n((?:  [^\n]*\n?)*)", user_prompt, flags=re.MULTILINE)
    if match:
        block = match.group(1)
    handles = list(dict.fromkeys(re.findall(r"Evidence \[(E\d+)\]", block)))
    has_claim = bool(re.search(r"Claim \(", block))
    seed = int(hashlib.sha256(cid.encode("utf-8")).hexdigest()[:8], 16)

    if handles:
        return BatchCriterionResult(
            criterion_id=cid,
            verification_status="VERIFIED_DOCUMENTED",
            score=round(6.0 + (seed % 26) / 10.0, 1),  # 6.0-8.5
            evidence_ids=handles[:3],
            rationale=f"{MOCK_RATIONALE_PREFIX} synthetic reading of cited deck evidence for {cid}.",
            missing_information=None,
        )
    if has_claim:
        return BatchCriterionResult(
            criterion_id=cid,
            verification_status="SELF_REPORTED_ONLY",
            score=round(4.5 + (seed % 21) / 10.0, 1),  # 4.5-6.5
            evidence_ids=[],
            rationale=f"{MOCK_RATIONALE_PREFIX} applicant statement for {cid} without a supporting document.",
            missing_information="Supporting document or third-party record.",
        )
    return BatchCriterionResult(
        criterion_id=cid,
        verification_status="MISSING_INFORMATION",
        score=None,
        evidence_ids=[],
        rationale=f"{MOCK_RATIONALE_PREFIX} no applicant data found for {cid}.",
        missing_information="Applicant to provide this information.",
    )


class MockAIGateway:
    """Deterministic AI gateway for development, tests, and cost guard verification."""

    provider_name = "mock"

    def __init__(
        self,
        *,
        model: str = "mock-model",
        response_factory: ResponseFactory | None = None,
        fixed_response: dict[str, Any] | BaseModel | None = None,
        latency_ms: float = 0.0,
    ) -> None:
        self._model = model
        self._response_factory = response_factory
        self._fixed_response = fixed_response
        self._latency_ms = latency_ms
        self._router = ModelRouter()

    def complete_json(
        self,
        request: AICompletionRequest,
        response_model: type[BaseModel],
    ) -> AICompletionResult[BaseModel]:
        started = time.perf_counter()
        settings = get_settings()

        # 1. Resolve model via router or request
        model = self._router.resolve_model(request) or self._model

        # Fail-closed pricing verification: reject unpriced model before dispatch
        pricing_catalog = get_pricing_catalog(settings.ai_pricing_catalog_version)
        pricing_catalog.get_pricing(model, allow_fallback=False)

        # 2. Token estimation
        est_input_tokens = request.estimated_input_tokens or (len(request.system_prompt) + len(request.user_prompt)) // 4
        planned_output_tokens = request.max_output_tokens or 1000

        # 3. Budget reservation (if evaluation_id provided)
        ledger: EvaluationCostLedger | None = None
        reservation_id: str | None = None
        if request.evaluation_id:
            ledger = CostLedgerManager.get_instance().get_or_create_ledger(
                evaluation_id=request.evaluation_id,
                startup_id=request.startup_id,
                max_budget_usd=settings.ai_max_evaluation_budget_usd,
                exchange_rate=settings.ai_inr_exchange_rate,
                buffer_multiplier=settings.ai_inr_buffer_multiplier,
            )

            planned_cost = pricing_catalog.estimate_max_cost(
                model=model,
                estimated_prompt_tokens=est_input_tokens,
                max_completion_tokens=planned_output_tokens,
            )

            # Enforces hard ceiling (raises AIBudgetExhaustedError if remaining < planned)
            reservation_id = ledger.reserve_budget(
                estimated_cost_usd=planned_cost,
                agent_name=request.agent_name,
            )

        # 4. Generate deterministic mock response
        schema_name = response_model.__name__
        staged_extraction_schemas = {
            "StartupProfileExtraction",
            "CoverIntakeExtraction",
            "ProblemNeedExtraction",
            "SolutionProductExtraction",
            "PrototypeTechnicalExtraction",
            "MarketOpportunityExtraction",
            "FounderCoreExtraction",
            "TeamAdvisoryExtraction",
            "CommercialisationExtraction",
            "InnovationImpactExtraction",
            "FinancialsSupportExtraction",
        }
        if schema_name in staged_extraction_schemas and self._response_factory is None and self._fixed_response is None:
            from app.modules.ai.orchestrator.startup_profile_extraction import (
                StartupProfileExtraction,
                KeyFeatureBenefit, CompetitorEntry, FounderEntry, TeamMemberEntry,
                HiringPlanEntry, AdvisorEntry, PilotAgreementEntry, PatentEntry,
                SDGAlignmentEntry, ImpactMetricEntry, ThreeYearMetric, SixQuarterRoadmap,
                ContactInfoEntry, ApplicantDeclarationEntry
            )
            user_prompt_lower = request.user_prompt.lower()
            grounded_profile = _mock_profile_from_document_text(request.user_prompt or "")
            if grounded_profile is not None:
                # Offline demonstration path: values are read from the submitted document text
                # ("Label: value" lines), never invented, so every claim can be traced to the deck.
                full_profile = grounded_profile
            elif "cleanenergy" in user_prompt_lower or "hydrogen" in user_prompt_lower:
                full_profile = StartupProfileExtraction(
                    company_name="CleanEnergy Corp",
                    tagline="Modular hydrogen fuel cells for zero-emission industrial backup power.",
                    sector="CleanTech",
                    stage="Seed",
                    geography="Roorkee, Uttarakhand, India",
                    application_date="2026-10-15",
                    problem_statement="Industrial power grid outages cost billions.",
                    who_is_affected="Grid utility companies and datacenter operators",
                    current_workarounds="Legacy diesel generators with high emissions and fuel storage hazards",
                    evidence_of_problem="Survey of 50 industrial plants showed average outage cost of $250k/hour",
                    why_problem_persists="Battery storage lacked energy density and fuel cells were prohibitively expensive",
                    solution="Modular hydrogen fuel cells for backup industrial power.",
                    key_features_benefits=[
                        KeyFeatureBenefit(feature="Modular cell stack", benefit="99.999% reliability backup"),
                        KeyFeatureBenefit(feature="Zero-emission operation", benefit="100% compliance with ESG standards"),
                        KeyFeatureBenefit(feature="Rapid start-up in <10 seconds", benefit="Zero interruption for critical computing loads")
                    ],
                    unique_value_proposition="Clean, 99.999% reliable backup power with 50% higher efficiency than rivals",
                    current_trl=6,
                    trl_justification="TRL 6 readiness level validated in industrial pilot",
                    demo_prototype_link="https://cleanenergy.internal/demo",
                    prototype_stage="Pilot-ready prototype",
                    technology="Proprietary hydrogen fuel cell stack.",
                    technical_validation_results="Over 10,000 hours of continuous testbed operation at 65% electrical efficiency",
                    market_size="$12 Billion globally",
                    sam="$3.5 Billion in APAC & EMEA industrial backup",
                    som_3_5_year="$150 Million over 3-5 years",
                    market_cagr="18.5%",
                    cagr_source="BloombergNEF Hydrogen Outlook 2025",
                    key_market_drivers=["Decarbonization mandates", "Grid instability", "Data center capacity expansion"],
                    market="Clean energy storage and backup power market.",
                    competitor_details=[
                        CompetitorEntry(name="Legacy Diesel Generators", country="Global", funding_raised="Publicly traded", approach="Fossil fuel internal combustion", startup_advantage="Zero emissions, lower maintenance"),
                        CompetitorEntry(name="Hydrogen Battery Rivals", country="USA", funding_raised="$50M Series B", approach="High-pressure gaseous storage", startup_advantage="50% higher energy density"),
                        CompetitorEntry(name="Bloom Energy", country="USA", funding_raised="$1B+ Public", approach="Solid oxide stationary fuel cells", startup_advantage="Faster cold start (<10s vs 2 hours)")
                    ],
                    competition="Legacy diesel generators and hydrogen battery rivals.",
                    sustainable_competitive_advantage="Hydrogen fuel cells are 50% more efficient than rivals.",
                    founder_details=[
                        FounderEntry(name="John Doe", role="Co-Founder & CEO", equity_percentage="50%", linkedin_url="https://linkedin.com/in/johndoe", education_degree="Ph.D. Chemical Engineering", education_institution="IIT Roorkee", graduation_year="2015", relevant_experience="Founders have 15 years experience in clean technology.", domain_expertise="Hydrogen systems engineering", prior_entrepreneurship="Previously co-founded FuelCell Tech (acquired)", key_achievement="Scaled fuel cell pilot to 500kW"),
                        FounderEntry(name="Jane Smith", role="Co-Founder & CTO", equity_percentage="50%", linkedin_url="https://linkedin.com/in/janesmith", education_degree="M.Tech Power Systems", education_institution="IIT Delhi", graduation_year="2017", relevant_experience="Founders have 15 years experience in clean technology.", domain_expertise="Membrane electrode assembly", prior_entrepreneurship="Senior Research Scientist at CSIR", key_achievement="Holds core patents in electrochemistry")
                    ],
                    founders=["John Doe", "Jane Smith"],
                    founder_roles=["Co-Founder & CEO", "Co-Founder & CTO"],
                    team="Founders have 15 years experience in clean technology.",
                    core_team=[
                        TeamMemberEntry(name="Dr. R. Sharma", role="Chief Scientist", credentials="Ph.D. Electrochemistry, 8 publications"),
                        TeamMemberEntry(name="Anita Verma", role="Head of Manufacturing", credentials="Ex-Tata Motors, 10 years production ops")
                    ],
                    critical_skill_gaps=["High-volume robotic manufacturing", "Defense sales & regulatory compliance"],
                    hiring_plan=[
                        HiringPlanEntry(role="Lead Power Electronics Engineer", timing_quarter="Q1", skill_requirements="Inverter design, grid-tie synchronization"),
                        HiringPlanEntry(role="VP Enterprise Sales", timing_quarter="Q2", skill_requirements="Data center and telecom sales experience")
                    ],
                    advisors=[
                        AdvisorEntry(name="Prof. K. Sen", organization="IIT Roorkee", role="Faculty Technical Advisor", contribution="Bi-weekly review of fuel cell stack performance")
                    ],
                    primary_mentor_contribution="Technical validation of electrochemical membrane durability and stack architecture",
                    institutional_affiliations=["TIDES IIT Roorkee", "Department of Science and Technology (DST)"],
                    business_model="Hardware sales plus maintenance contracts.",
                    revenue_model="High margin hardware sales.",
                    pricing_strategy_unit="$1,200 per kW installed plus $50/kW annual maintenance SLA",
                    customer_acquisition_channels=["Direct enterprise sales to telecom and hyperscalers", "Channel partnerships with EPC contractors"],
                    cac="$45,000 per enterprise account",
                    expected_gross_margin="42% initial, expanding to 58% at scale",
                    payback_period_months="14 months",
                    path_to_first_10l_10k="Closing 2 telecom tower backup pilot contracts currently under commercial NDA",
                    current_users="12 trial users",
                    paying_customers="0",
                    current_revenue="$0.0",
                    pilot_agreements=[
                        PilotAgreementEntry(partner_name="State Power Grid Corp", agreement_type="Signed Pilot", is_signed=True, contract_value="$250,000"),
                        PilotAgreementEntry(partner_name="Apex Data Centers", agreement_type="LOI", is_signed=False, contract_value="$500,000")
                    ],
                    awards_grants_recognition=["National CleanTech Challenge Winner 2025", "DST Seed Grant ₹50 Lakh"],
                    research_validation=["Published in Journal of Power Sources (2024)", "Validated by National Renewable Energy Lab"],
                    customer_quotes=["The CleanEnergy stack delivered continuous power through our 8-hour grid blackout test flawlessly."],
                    proprietary_technology_moat="Proprietary non-precious metal catalyst reducing stack cost by 40%",
                    data_advantage="Over 100,000 sensor telemetry hours optimizing predictive fuel flow",
                    network_effects="Fleet operational telemetry trains centralized predictive degradation models",
                    switching_costs="High capital re-tooling cost once integrated into industrial power substation",
                    brand_community_moat="Trusted research partnership with premier Indian technical institutions",
                    regulatory_licensing_barriers="ISO 16110 and PESO statutory safety certifications for hydrogen handling",
                    patent_details=[
                        PatentEntry(title="Electrode Assembly for Fuel Cell Stack", application_number="202511012345", status="Filed", jurisdiction="India"),
                        PatentEntry(title="Thermal Management System in Modular Cells", application_number="202511054321", status="Filed", jurisdiction="India")
                    ],
                    patents="Two patents filed for cell stack design.",
                    primary_impact="Abating 1,200 metric tonnes of CO2 per installed MW annually by replacing diesel generation",
                    sdg_alignments=[
                        SDGAlignmentEntry(sdg_number=7, sdg_name="Affordable and Clean Energy", explanation="Directly provides clean hydrogen backup power"),
                        SDGAlignmentEntry(sdg_number=9, sdg_name="Industry, Innovation and Infrastructure", explanation="Builds resilient zero-emission industrial power infrastructure")
                    ],
                    impact_metrics=[
                        ImpactMetricEntry(metric_name="Metric tonnes of CO2 abated", baseline="0", target_3_year="50,000 MT"),
                        ImpactMetricEntry(metric_name="Diesel fuel displaced (litres)", baseline="0", target_3_year="18,000,000 L")
                    ],
                    potential_negative_effects_mitigation="Safe hydrogen venting and zero water toxicity through closed-loop recombination",
                    three_year_revenue=ThreeYearMetric(year_1="₹2.5 Crore", year_2="₹12.0 Crore", year_3="₹45.0 Crore"),
                    three_year_gross_margin=ThreeYearMetric(year_1="38%", year_2="48%", year_3="56%"),
                    three_year_customers=ThreeYearMetric(year_1="4", year_2="18", year_3="65"),
                    three_year_team_size=ThreeYearMetric(year_1="8", year_2="22", year_3="50"),
                    burn_rate="Not specified",
                    break_even_timing="Month 22",
                    financial_assumptions=["Raw material cost decreases 15% with volume", "Average contract duration 5 years"],
                    funding_raised="$2.5 Million",
                    current_monthly_operating_costs="₹12 Lakh per month",
                    lab_facilities_requirements=["Hydrogen safety testing bunker", "Scanning electron microscope access"],
                    mentorship_expertise_needed=["Advanced materials characterization faculty", "International CE/UL compliance advisor"],
                    industry_connections_needed=["Power Grid Corporation of India", "Bharat Petroleum Corporation Limited"],
                    legal_ip_support_needed=["PCT international patent filing support", "Cross-border IP assignment structuring"],
                    market_access_pilot_support_needed=["Deployment on IIT Roorkee campus substation as living laboratory"],
                    training_skill_building_needed=["Global export controls compliance", "Government tender bid preparation"],
                    six_quarter_product_roadmap=SixQuarterRoadmap(q1="Bench testing of 10kW stack", q2="Industrial pilot deployment", q3="Field endurance validation", q4="50kW multi-module integration", q5="Commercial certification batch", q6="Full volume manufacturing start"),
                    six_quarter_market_roadmap=SixQuarterRoadmap(q1="Sign 3 commercial LOIs", q2="Deploy first telecom pilot", q3="Convert pilot to signed contract", q4="Expand to 5 enterprise clients", q5="Enter Middle East export market", q6="Scale to 20 active installations"),
                    six_quarter_team_roadmap=SixQuarterRoadmap(q1="Hire Lead Power Electronics Engineer", q2="Hire Senior Chemical Engineer", q3="Hire VP Enterprise Sales", q4="Hire 4 Assembly Technicians", q5="Hire Regulatory Manager", q6="Hire Regional Sales Leads"),
                    six_quarter_funding_roadmap=SixQuarterRoadmap(q1="Close ₹50L seed grant", q2="Deploy seed capital into tooling", q3="Achieve pilot milestone", q4="Initiate Series A round", q5="Close $5M Series A", q6="Deploy capital into factory scaling"),
                    contact_info=ContactInfoEntry(representative_name="John Doe", email="contact@cleanenergycorp.com", phone="+91 9876543210", website="https://cleanenergycorp.com", address="TIDES Incubation Centre, IIT Roorkee, Uttarakhand - 247667"),
                    applicant_declaration=ApplicantDeclarationEntry(is_signed=True, signatory_name="John Doe", declaration_date="2026-10-15"),
                    traction="TRL 6 readiness level validated in pilot.",
                    financial_information="Pre-revenue; raised $2.5 Million seed funding.",
                    funding_ask="$2.5 Million seed",
                    runway="24 months",
                )
            elif "petrevolt" in user_prompt_lower or "sodium" in user_prompt_lower or "battery" in user_prompt_lower or "solvolysis" in user_prompt_lower or "pet plastic" in user_prompt_lower:
                full_profile = StartupProfileExtraction(
                    company_name="PETREVOLT ENERGY SOLUTIONS PVT LTD",
                    tagline="Solid-state sodium-ion batteries from upcycled PET plastic waste.",
                    sector="CleanTech / Energy Storage",
                    stage="Seed",
                    geography="Coimbatore, Tamil Nadu, India",
                    application_date="2026-07-20",
                    problem_statement="India depends on imported lithium-ion batteries, creating high costs, supply chain vulnerability, and defence cold-start readiness gaps.",
                    who_is_affected="Electric 2W and 3W OEMs, grid storage integrators, and defence forces requiring extreme-cold battery operation",
                    current_workarounds="Imported Chinese lithium iron phosphate cells with volatile pricing, thermal fire risk, and Siachen/Ladakh cold-start failure",
                    evidence_of_problem="Over 80% of India's cell requirements are imported, creating a permanent strategic vulnerability while 3.4M tonnes of PET plastic are downcycled annually",
                    why_problem_persists="Domestic sodium chemistry lacked high cycle life, sustainable anode precursor sourcing, and non-flammable solid-state electrolytes",
                    solution="Solid-state sodium-ion batteries manufactured from recycled PET plastic waste via chemical solvolysis.",
                    key_features_benefits=[
                        KeyFeatureBenefit(feature="One Bottle Battery single-source engineering", benefit="Anode, electrolyte, and salts all derived from PET bottles, disrupting precursor cost by 100x"),
                        KeyFeatureBenefit(feature="Cold-start operational resilience (-70°C to +45°C)", benefit="Maintains 92% capacity at -40°C for Siachen and Ladakh defence deployment"),
                        KeyFeatureBenefit(feature="Non-flammable solid electrolyte chemistry", benefit="Zero thermal runaway risk and ballistic safety under extreme conditions")
                    ],
                    unique_value_proposition="Single-source circular battery engineering with 100x precursor cost disruption and cold-start resilience down to -70°C",
                    current_trl=4,
                    trl_justification="Rechargeable PoC demonstrating reversible Na-ion intercalation built and patent applied for liquid electrolyte conversion",
                    demo_prototype_link="https://petrevolt.internal/lab-demo",
                    prototype_stage="Laboratory pouch cell prototype",
                    technology="Solid-state sodium-ion battery using disodium terephthalate (DST) and hard carbon derived from PET solvolysis.",
                    technical_validation_results="Over 800 cycles demonstrated at 1C with 85% capacity retention; 92% capacity maintained at -40°C in laboratory half-cells",
                    market_size="1.3 TWh India battery storage demand by 2047; Rs 3,400 Cr+ opportunity",
                    sam="45 GWh target 2W/3W and stationary energy storage market in South Asia by 2030",
                    som_3_5_year="1.2 GWh annual manufacturing capacity target across defence and EV sectors",
                    market_cagr="18.1%",
                    cagr_source="Global SIB EV Market 2026-2034",
                    key_market_drivers=["PM E-DRIVE subsidies", "National Critical Mineral Mission", "Plastic waste EPR mandates", "Defence Atmanirbhar Bharat initiative"],
                    market="Electric 2W and 3W OEMs, renewable BESS, and defence micro-grids.",
                    competitor_details=[
                        CompetitorEntry(name="CATL", country="China", funding_raised="Publicly traded", approach="1st Gen Sodium-ion liquid electrolyte", startup_advantage="Solid-state non-flammable safety and circular PET upcycling"),
                        CompetitorEntry(name="Faradion", country="UK", funding_raised="Acquired by Reliance", approach="Stratified oxide sodium chemistry", startup_advantage="100x lower precursor cost via waste plastic upcycling"),
                        CompetitorEntry(name="Altris", country="Sweden", funding_raised="€25M Series A", approach="Prussian white cathode", startup_advantage="Fully domestic Indian sovereign supply chain")
                    ],
                    competition="Imported lithium-ion battery suppliers and emerging domestic SIB players.",
                    sustainable_competitive_advantage="Proprietary PET waste solvolysis yielding high-purity disodium terephthalate (DST) salts and hard carbon anodes from near-zero-cost feedstock.",
                    founder_details=[
                        FounderEntry(name="Princya Polin S", role="Co-Founder & CEO", equity_percentage="50%", linkedin_url="https://linkedin.com/in/princyapolin", education_degree="M.Tech Nanotechnology", education_institution="Anna University", graduation_year="2018", relevant_experience="Domain expertise in electrochemistry and battery prototype validation.", domain_expertise="Materials science and battery engineering", prior_entrepreneurship="First-time founder, published battery patents", key_achievement="Developed proprietary PET depolymerization protocol and first alkaline cell"),
                        FounderEntry(name="Ashwin Kumar P", role="Co-Founder & COO", equity_percentage="50%", linkedin_url="https://linkedin.com/in/ashwinkumar", education_degree="M.S. Chemical Engineering", education_institution="IIT Madras", graduation_year="2019", relevant_experience="Domain expertise in manufacturing protocols and pouch cell packaging.", domain_expertise="Electrochemical impedance spectroscopy and pilot manufacturing", prior_entrepreneurship="Former Lead Engineer at Ather Energy cell R&D", key_achievement="Engineered 1Ah pouch cell prototype and solvolysis yield optimization")
                    ],
                    founders=["Princya Polin S", "Ashwin Kumar P"],
                    founder_roles=["Co-Founder & CEO", "Co-Founder & COO"],
                    team="Founders have domain expertise in electrochemistry, battery prototype validation, and pilot production operations.",
                    core_team=[
                        TeamMemberEntry(name="M. Selvam", role="Lead Battery Design Engineer", credentials="M.Tech Vellore Institute of Technology")
                    ],
                    critical_skill_gaps=["High-volume roll-to-roll electrode coating", "ARAI/ICAT automotive qualification"],
                    hiring_plan=[
                        HiringPlanEntry(role="Senior Slurry Formulations Chemist", timing_quarter="Q1", skill_requirements="Binder and conductive additive optimization"),
                        HiringPlanEntry(role="Battery Thermal Management Engineer", timing_quarter="Q2", skill_requirements="Pouch cell thermal modeling and pack design")
                    ],
                    advisors=[
                        AdvisorEntry(name="Dr. Prof. Rajesh M. Bodade", organization="Military College Of Telecommunication Engineering, Mhow", role="Senior Professor & Mentor", contribution="Technical advisory on extreme-cold defence applications and telecommunications backup")
                    ],
                    primary_mentor_contribution="Electrochemical architecture and defence operational qualification advisory under extreme-cold conditions",
                    institutional_affiliations=["EDII Tamil Nadu", "TIDES IIT Roorkee"],
                    business_model="B2B battery cell sales to EV OEMs, stationary BESS integrators, and defence procurement.",
                    revenue_model="Multi-year cell supply agreements and technology licensing.",
                    pricing_strategy_unit="$65 per kWh pack-level target with volume tiering",
                    customer_acquisition_channels=["Direct OEM qualification testing with 2W/3W hubs in Tamil Nadu and Karnataka", "Defence procurement channels"],
                    cac="₹1.5 Lakh per qualified OEM trial",
                    expected_gross_margin="34% gross margin per cell batch at pilot scale",
                    payback_period_months="18 months",
                    path_to_first_10l_10k="Securing paid pilot sample batch evaluation with domestic EV OEMs",
                    current_users="4 EV OEMs testing evaluation cells",
                    paying_customers="0",
                    current_revenue="0.0",
                    pilot_agreements=[
                        PilotAgreementEntry(partner_name="E-Rickshaw OEM Consortium", agreement_type="LOI", is_signed=False, contract_value="₹1.2 Crore")
                    ],
                    awards_grants_recognition=["EDII Tamil Nadu Innovation Voucher Program grant", "TN Government Recognition"],
                    research_validation=["PoC validated in laboratory test cells demonstrating reversible Na-ion intercalation"],
                    customer_quotes=["The pouch cell exhibited negligible heat generation during high-rate discharge tests."],
                    proprietary_technology_moat="Patent-applied chemical solvolysis converting waste PET into battery-grade DST salts and hard carbon anodes",
                    data_advantage="Proprietary cycling and degradation data across 50+ electrolyte formulations and extreme-cold environments",
                    network_effects="Supply partnerships with regional municipal plastic aggregators ensure zero-cost feedstock dominance",
                    switching_costs="Custom cell form factor and thermal profile integrated into OEM battery pack enclosures",
                    brand_community_moat="Pioneer in circular economy energy storage technology in India",
                    regulatory_licensing_barriers="ARAI / ICAT automotive certification and AIS-156 / UN 38.3 battery transport compliance",
                    patent_details=[
                        PatentEntry(title="Conversion of Waste PET Plastic to Electrolyte Salts for Sodium-Ion Batteries", application_number="202441098765", status="Filed", jurisdiction="India")
                    ],
                    patents="Patent applied for PET plastic to liquid electrolyte conversion mechanism.",
                    primary_impact="Diverting 500 tonnes of single-use PET plastic from landfills per GWh of cell production; eliminating lithium import dependency",
                    sdg_alignments=[
                        SDGAlignmentEntry(sdg_number=12, sdg_name="Responsible Consumption and Production", explanation="Upcycling plastic waste into high-value energy storage devices"),
                        SDGAlignmentEntry(sdg_number=13, sdg_name="Climate Action", explanation="Enabling domestic zero-emission clean energy storage"),
                        SDGAlignmentEntry(sdg_number=7, sdg_name="Affordable and Clean Energy", explanation="Cost-disruptive domestic sodium battery alternative to imported lithium")
                    ],
                    impact_metrics=[
                        ImpactMetricEntry(metric_name="Tonnes of PET plastic upcycled", baseline="0", target_3_year="1,500 Tonnes"),
                        ImpactMetricEntry(metric_name="Carbon abatement (MT CO2e)", baseline="0", target_3_year="25,000 MT")
                    ],
                    potential_negative_effects_mitigation="Closed-loop solvolysis solvent recycling system with zero hazardous effluent discharge",
                    three_year_revenue=ThreeYearMetric(year_1="₹50 Lakh", year_2="₹4.5 Crore", year_3="₹18.0 Crore"),
                    three_year_gross_margin=ThreeYearMetric(year_1="25%", year_2="32%", year_3="38%"),
                    three_year_customers=ThreeYearMetric(year_1="2", year_2="8", year_3="25"),
                    three_year_team_size=ThreeYearMetric(year_1="5", year_2="14", year_3="35"),
                    burn_rate="Not specified",
                    break_even_timing="Month 28",
                    financial_assumptions=["Plastic feedstock cost ₹35/kg", "Solvolysis yield efficiency 82%"],
                    funding_raised="None",
                    current_monthly_operating_costs="₹3.5 Lakh per month",
                    lab_facilities_requirements=["Argon glove box", "Electrode slot-die coater", "Multi-channel battery cycler", "XRD / SEM characterization access"],
                    mentorship_expertise_needed=["Advanced solid-state electrochemistry", "High-volume battery pilot manufacturing"],
                    industry_connections_needed=["ARAI / ICAT certification body", "Domestic EV 2W/3W OEMs (Ola, Ather, Hero MotoCorp)"],
                    legal_ip_support_needed=["PCT international patent filing support and Indian patent office prosecution"],
                    market_access_pilot_support_needed=["Field trial deployment with institutional electric utility fleet"],
                    training_skill_building_needed=["ISO 9001 and automotive IATF 16949 quality management systems"],
                    six_quarter_product_roadmap=SixQuarterRoadmap(q1="1Ah pouch cell prototyping", q2="NASICON solid electrolyte synthesis", q3="Full PoC battery assembly (2-5 Ah)", q4="ARAI certification testing", q5="Pilot line setup", q6="Commercial cell manufacturing"),
                    six_quarter_market_roadmap=SixQuarterRoadmap(q1="Engage 5 EV 2W OEMs", q2="Deliver evaluation sample batches", q3="Complete pilot validation", q4="Secure first supply agreement", q5="Commercial delivery to initial customer", q6="Expand customer roster to 5 OEMs"),
                    six_quarter_team_roadmap=SixQuarterRoadmap(q1="Hire Slurry Formulations Chemist", q2="Hire Battery Pack Designer", q3="Hire Quality Control Lead", q4="Hire 3 Cell Assembly Operators", q5="Hire Production Manager", q6="Hire Supply Chain Specialist"),
                    six_quarter_funding_roadmap=SixQuarterRoadmap(q1="Secure EDII-TN and grant funding", q2="Raise angel funding round", q3="Build 2-5 Ah prototype", q4="Initiate Rs 5 crore seed round", q5="Close seed round", q6="Deploy capital into pilot line equipment"),
                    contact_info=ContactInfoEntry(representative_name="Princya Polin S", email="[redacted-applicant-email]", phone="[redacted-applicant-phone]", website="https://petrevolt.internal", address="[redacted-applicant-address], Coimbatore, Tamil Nadu"),
                    applicant_declaration=ApplicantDeclarationEntry(is_signed=True, signatory_name="Princya Polin S", declaration_date="2026-07-20"),
                    traction="Working alkaline prototype and rechargeable PoC built; grant received under EDII-TN Innovation Voucher Program; patent applied.",
                    financial_information="Pre-revenue; seeking seed funding for Phase 2 solid-state R&D.",
                    funding_ask="Rs 5 crore seed round",
                    runway="Not specified",
                )
            else:
                from app.modules.ai.gateway.provider import generate_mock_pydantic
                full_profile = generate_mock_pydantic(StartupProfileExtraction)

            if schema_name == "StartupProfileExtraction":
                data = full_profile
            else:
                fields = {k: getattr(full_profile, k) for k in response_model.model_fields.keys() if hasattr(full_profile, k)}
                data = response_model(**fields)
            raw_text = data.model_dump_json()
        elif schema_name == "AgentAssessment" and self._response_factory is None and self._fixed_response is None:
            domain = "founder"
            if request.metadata and request.metadata.get("domain") and request.metadata.get("domain") != "evaluation":
                domain = request.metadata.get("domain")
            elif request.system_prompt:
                sys_prompt_lower = request.system_prompt.lower()
                if "problem" in sys_prompt_lower or "solution" in sys_prompt_lower:
                    domain = "problem_solution"
                elif "commercial" in sys_prompt_lower:
                    domain = "commercialisation"
                elif "innovation" in sys_prompt_lower or "impact" in sys_prompt_lower:
                    domain = "innovation_impact"
                elif "financial" in sys_prompt_lower:
                    domain = "financials_support"
                elif "founder" in sys_prompt_lower or "team" in sys_prompt_lower:
                    domain = "founder_team"
                elif "market" in sys_prompt_lower or "competition" in sys_prompt_lower:
                    domain = "market_opportunity"
                elif "trl" in sys_prompt_lower:
                    domain = "trl"
                elif "ip" in sys_prompt_lower:
                    domain = "ip"
                elif "risk" in sys_prompt_lower:
                    domain = "risk"
                elif "product" in sys_prompt_lower:
                    domain = "product"
            from app.services.ai.real_pipeline import generate_assessment_from_context
            data = generate_assessment_from_context(request.user_prompt, domain, response_model)
            raw_text = data.model_dump_json()
        elif schema_name == "DomainCriterionBatchOutput" and self._response_factory is None and self._fixed_response is None:
            import re
            from app.modules.evaluation.domain_schemas import DomainCriterionBatchOutput, CompactCriterionResult
            from app.modules.evaluation.domains.registry import get_criteria_for_domain

            domain_key = "problem_solution"
            if request.metadata and request.metadata.get("domain") and request.metadata.get("domain") != "evaluation":
                domain_key = request.metadata.get("domain")
            elif request.system_prompt:
                sys_prompt_lower = request.system_prompt.lower()
                if "problem" in sys_prompt_lower or "solution" in sys_prompt_lower:
                    domain_key = "problem_solution"
                elif "commercial" in sys_prompt_lower:
                    domain_key = "commercialisation"
                elif "innovation" in sys_prompt_lower or "impact" in sys_prompt_lower:
                    domain_key = "innovation_impact"
                elif "financial" in sys_prompt_lower:
                    domain_key = "financials_support"
                elif "founder" in sys_prompt_lower or "team" in sys_prompt_lower:
                    domain_key = "founder_team"
                elif "market" in sys_prompt_lower or "competition" in sys_prompt_lower:
                    domain_key = "market_opportunity"

            batch_index = int((request.metadata or {}).get("batch_index", 0))
            crit_ids = list((request.metadata or {}).get("batch_criterion_ids") or [])
            if not crit_ids and request.user_prompt:
                crit_ids = re.findall(r"\[([A-Z]{2}-\d{2})\]", request.user_prompt)
            if not crit_ids:
                crit_ids = get_criteria_for_domain(domain_key)[:5]

            results = [
                _mock_criterion_from_prompt(cid, request.user_prompt or "")
                for cid in crit_ids
            ]

            data = DomainCriterionBatchOutput(
                domain=domain_key,
                batch_index=batch_index,
                criteria=results,
            )
            raw_text = data.model_dump_json()
        elif schema_name == "CompactDomainAssessment" and self._response_factory is None and self._fixed_response is None:
            from app.modules.evaluation.domain_schemas import CompactDomainAssessment, CompactCriterionResult, CompactDomainRisk
            from app.modules.evaluation.domains.registry import get_criteria_for_domain

            domain_key = "problem_solution"
            if request.metadata and request.metadata.get("domain") and request.metadata.get("domain") != "evaluation":
                domain_key = request.metadata.get("domain")
            elif request.system_prompt:
                sys_prompt_lower = request.system_prompt.lower()
                if "problem" in sys_prompt_lower or "solution" in sys_prompt_lower:
                    domain_key = "problem_solution"
                elif "commercial" in sys_prompt_lower:
                    domain_key = "commercialisation"
                elif "innovation" in sys_prompt_lower or "impact" in sys_prompt_lower:
                    domain_key = "innovation_impact"
                elif "financial" in sys_prompt_lower:
                    domain_key = "financials_support"
                elif "founder" in sys_prompt_lower or "team" in sys_prompt_lower:
                    domain_key = "founder_team"
                elif "market" in sys_prompt_lower or "competition" in sys_prompt_lower:
                    domain_key = "market_opportunity"

            crit_ids = get_criteria_for_domain(domain_key)
            results = []
            for cid in crit_ids:
                results.append(CompactCriterionResult(
                    criterion_id=cid,
                    verification_status="VERIFIED_DOCUMENTED",
                    score=7.5,
                    evidence_ids=[],
                    rationale="Verified from application submission.",
                ))

            data = CompactDomainAssessment(
                domain=domain_key,
                domain_conclusion=f"Deterministic assessment for {domain_key} meets institutional criteria.",
                criteria=results,
                strengths=[f"Strong validation on primary {domain_key} metrics"],
                risks=[CompactDomainRisk(id="R1", severity="Medium", description="Initial scaling dependencies", mitigation="Phased rollout")],
                information_requests=["Provide audited operating telemetry"],
                unknowns=[],
                contradictions=[],
                confidence_score=0.85,
            )
            raw_text = data.model_dump_json()
        elif schema_name == "SupervisoryReviewOutput" and self._response_factory is None and self._fixed_response is None:
            from app.modules.evaluation.domain_schemas import SupervisoryReviewOutput
            user_prompt_lower = (request.user_prompt or "").lower()
            if "petrevolt" in user_prompt_lower or "sodium" in user_prompt_lower or "battery" in user_prompt_lower:
                data = SupervisoryReviewOutput(
                    executive_summary="Due diligence across all 6 canonical domains indicates high technological differentiation in waste-PET solvolysis for solid-state sodium batteries, backed by working alkaline and rechargeable PoC cells and an applied conversion patent. Critical commercialization risks center on ARAI/ICAT certification timelines, pilot pouch cell yield at scale, and high-volume roll-to-roll electrode manufacturing gaps.",
                    recommendation_rationale="The venture presents a compelling circular economy thesis with national strategic relevance for energy storage sovereignty and Siachen/Ladakh extreme-cold defence deployment (-70°C to +45°C). Conditional incubation is recommended subject to milestone tranches tied to pilot cell ARAI testing and binding OEM qualification contracts.",
                    overall_recommendation="CONDITIONAL",
                    identified_contradictions=[],
                    missing_domains=[],
                    priority_diligence_questions=[
                        "Confirm timeline and testing facility for ARAI/ICAT automotive battery certification under AIS-156",
                        "Provide empirical cycling degradation data for full pouch cells under extreme-cold conditions (-40°C)",
                        "Clarify patent prosecution status and institutional assignment with university/mentor",
                        "Verify chemical solvolysis yield efficiency and purity reports from standardized post-consumer PET flake batches",
                    ],
                    incubation_conditions=[
                        "Execution of formal TIDES incubation and IP disclosure agreement",
                        "Milestone tranche reviews tied to 2-5 Ah pouch cell testing and ARAI submission",
                        "Quarterly review of OEM evaluation agreements and grant disbursements",
                    ],
                    recommended_tranches=[
                        {"tranche": 1, "description": "Phase 2 onboarding, laboratory sandbox access, and characterization facility access (XRD/SEM)"},
                        {"tranche": 2, "description": "Disbursement contingent upon successful 2-5 Ah pouch cell assembly and formal ARAI certification submission"},
                    ],
                    investment_score=71.5,
                    confidence_score=0.88,
                )
            else:
                data = SupervisoryReviewOutput(
                    executive_summary="Holistic due diligence across all 6 domains demonstrates grounded commercial readiness and defensible technical architecture.",
                    recommendation_rationale="Core problem-solution alignment and founder depth justify selective incubation with milestone tranches.",
                    overall_recommendation="CONDITIONAL",
                    identified_contradictions=["Minor revenue timing vs early forecast variance"],
                    missing_domains=[],
                    priority_diligence_questions=["Confirm PESO statutory safety certification timeline", "Provide binding pilot contract terms"],
                    incubation_conditions=["Complete formal TIDES onboarding agreements", "Establish monthly KPI governance cadence"],
                    recommended_tranches=[
                        {"tranche": 1, "description": "Initial incubation sandbox access & faculty mentorship onboarding"},
                        {"tranche": 2, "description": "Capital disbursement contingent on pilot contract execution & TRL milestone"},
                    ],
                    investment_score=72.0,
                    confidence_score=0.88,
                )
            raw_text = data.model_dump_json()
        else:
            try:
                payload = self._resolve_payload(request)
                raw_text = self._serialize_payload(payload)
                if isinstance(payload, BaseModel):
                    data = response_model.model_validate(payload.model_dump())
                else:
                    if not payload and response_model.model_fields:
                        from app.modules.ai.gateway.provider import generate_mock_pydantic
                        data = generate_mock_pydantic(response_model)
                    else:
                        data = response_model.model_validate(payload)
            except ValidationError as exc:
                if ledger and reservation_id:
                    ledger.release_reservation(reservation_id)
                raise AIResponseParseError("Response does not match the expected schema") from exc
            except Exception:
                if ledger and reservation_id:
                    ledger.release_reservation(reservation_id)
                raise

        elapsed_ms = self._latency_ms or ((time.perf_counter() - started) * 1000)

        # 5. Token Calculation & Reconciliation
        completion_tokens = max(10, len(raw_text) // 4)
        input_tokens = est_input_tokens
        cached_tokens = int(request.metadata.get("cached_tokens", 0)) if request.metadata else 0

        # Resolve cache write breakdown and TTL attribution hierarchy
        w_5m, w_1h, w_total, resolved_ttl = resolve_cache_attribution(
            usage=request.metadata,
            request_metadata=request.metadata,
            default_ttl=settings.ai_default_cache_write_ttl,
            pricing_policy=settings.ai_cache_pricing_policy,
        )

        cost_usd = 0.0
        cost_inr = 0.0
        buffered_inr = 0.0

        if ledger:
            operation_id = (
                str(request.metadata["operation_id"]).strip()
                if request.metadata and request.metadata.get("operation_id")
                else None
            )
            record = ledger.reconcile_operation(
                reservation_id=reservation_id,
                agent_name=request.agent_name,
                provider=self.provider_name,
                model=model,
                input_tokens=input_tokens,
                output_tokens=completion_tokens,
                cached_tokens=cached_tokens,
                cache_write_tokens=w_total,
                cache_write_5m_tokens=w_5m,
                cache_write_1h_tokens=w_1h,
                cache_write_ttl=resolved_ttl,
                latency_ms=elapsed_ms,
                status="SUCCESS",
                operation_id=operation_id,
            )
            cost_usd = record.final_cost_usd
            cost_inr = record.cost_inr
            buffered_inr = record.buffered_cost_inr
            cumulative_cost_usd = ledger.spent_usd
        else:
            cost_usd = pricing_catalog.calculate_cost(
                model=model,
                prompt_tokens=input_tokens,
                completion_tokens=completion_tokens,
                cached_tokens=cached_tokens,
                cache_write_tokens=w_total,
                cache_write_5m_tokens=w_5m,
                cache_write_1h_tokens=w_1h,
                cache_write_ttl=resolved_ttl,
            )
            cost_inr, buffered_inr = pricing_catalog.convert_to_inr(
                cost_usd=cost_usd,
                exchange_rate=settings.ai_inr_exchange_rate,
                buffer_multiplier=settings.ai_inr_buffer_multiplier,
            )
            cumulative_cost_usd = cost_usd

        budget_limit = ledger.max_budget_usd if ledger else settings.ai_max_evaluation_budget_usd
        if cumulative_cost_usd > round(budget_limit, 6):
            raise AIBudgetExhaustedError(
                f"Evaluation aborted: Cumulative cost of ${cumulative_cost_usd:.4f} "
                f"exceeds the budget safety limit of ${budget_limit:.4f}."
            )

        metadata = AICompletionMetadata(
            model=model,
            provider=self.provider_name,
            latency_ms=round(elapsed_ms, 3),
            prompt_version=request.prompt_version,
            input_tokens=input_tokens,
            output_tokens=completion_tokens,
            cached_tokens=cached_tokens,
            cost_usd=cost_usd,
            cost_inr=cost_inr,
            buffered_cost_inr=buffered_inr,
            evaluation_id=request.evaluation_id,
            cumulative_cost_usd=cumulative_cost_usd,
            cumulative_cost_inr=round(cumulative_cost_usd * settings.ai_inr_exchange_rate, 4),
            pricing_version=pricing_catalog.version,
        )
        return AICompletionResult(data=data, metadata=metadata, raw_text=raw_text)

    def _resolve_payload(self, request: AICompletionRequest) -> dict[str, Any] | BaseModel:
        if self._response_factory is not None:
            return self._response_factory(request)
        if self._fixed_response is not None:
            return self._fixed_response
        return {}

    @staticmethod
    def _serialize_payload(payload: dict[str, Any] | BaseModel) -> str:
        if isinstance(payload, BaseModel):
            return payload.model_dump_json()
        return json.dumps(payload)
