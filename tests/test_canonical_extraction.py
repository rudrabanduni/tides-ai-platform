import uuid
import pytest
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.modules.startups.models import StartupApplication
from app.modules.documents.models import Document
from app.core.enums import DocumentProcessingStatus, DocumentType
from app.modules.intelligence.models import StartupClaim, StartupEvidence, StartupIntelligenceProfile
from app.modules.intelligence.claim_engine import ClaimEngine
from app.modules.ai.orchestrator.startup_profile_extraction import (
    StartupProfileExtraction,
    KeyFeatureBenefit,
    CompetitorEntry,
    FounderEntry,
    TeamMemberEntry,
    HiringPlanEntry,
    AdvisorEntry,
    PilotAgreementEntry,
    PatentEntry,
    SDGAlignmentEntry,
    ImpactMetricEntry,
    ThreeYearMetric,
    SixQuarterRoadmap,
    ContactInfoEntry,
    ApplicantDeclarationEntry,
)
from app.services.ai.mock import MockAIGateway
from app.services.ai.schemas import AICompletionRequest
from app.services.ai.cost_ledger import CostLedgerManager
from app.services.ai.exceptions import AIBudgetExhaustedError


@pytest.fixture()
def db_session() -> Session:
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


def test_all_87_canonical_criteria_schema_instantiation():
    """Verifies that StartupProfileExtraction supports all 87 canonical criteria across 6 domains."""
    profile = StartupProfileExtraction(
        # Cover & Application Metadata (CM-01 to CM-06)
        company_name="Apex BioTech Labs",
        tagline="Next-generation biocatalysts for green industrial chemistry.",
        sector="DeepTech",
        stage="Prototype",
        geography="Roorkee, Uttarakhand, India",
        application_date="2026-10-18",

        # Domain 1: Problem & Solution (PS-01 to PS-13)
        problem_statement="Industrial chemical synthesis relies on heavy metal catalysts causing toxic effluent.",
        who_is_affected="Pharmaceutical and specialty chemical manufacturing plants globally.",
        current_workarounds="Precious metal catalysts with energy-intensive high-temperature batch processing.",
        evidence_of_problem="Over 40 million tonnes of hazardous solvent and heavy metal waste generated annually.",
        why_problem_persists="Natural enzymes degraded under industrial temperatures (>60C) and acidic pH.",
        solution="Thermostable engineered computational enzymes designed for ambient-temperature continuous flow.",
        key_features_benefits=[
            KeyFeatureBenefit(feature="Thermostable at 85C", benefit="Enables continuous industrial operations"),
            KeyFeatureBenefit(feature="Broad pH tolerance (3-11)", benefit="Eliminates neutralization steps"),
            KeyFeatureBenefit(feature="98% enantiomeric excess", benefit="Reduces downstream purification costs by 60%"),
        ],
        unique_value_proposition="10x longer enzyme half-life at 40% lower cost than Novozymes alternatives.",
        current_trl=4,
        trl_justification="Laboratory pilot continuous flow reactor validated over 500 operating hours.",
        demo_prototype_link="https://apexbiotech.test/demo",
        prototype_stage="Benchtop continuous flow reactor",
        technology="De novo protein design using generative AI diffusion models and directed evolution.",
        technical_validation_results="Over 95% yield in 100-liter bioreactor test runs.",

        # Domain 2: Market Opportunity (MO-01 to MO-10)
        market_size="$14.5 Billion globally",
        sam="$4.2 Billion specialty pharmaceutical biocatalysis",
        som_3_5_year="$180 Million target capture over 3-5 years",
        market_cagr="14.8%",
        cagr_source="MarketsandMarkets Biocatalysis Report 2025",
        key_market_drivers=["Green chemistry mandates", "Scope 3 emissions reduction", "Pharma cost pressures"],
        market="Indian and European pharmaceutical intermediate manufacturers.",
        competitor_details=[
            CompetitorEntry(name="Novozymes / Novonesis", country="Denmark", funding_raised="Publicly traded", approach="Traditional fungal expression", startup_advantage="Higher thermal stability at 85C"),
            CompetitorEntry(name="Codexis", country="USA", funding_raised="$200M+ Public", approach="Directed evolution screening", startup_advantage="De novo AI sequence design requires 10x fewer lab rounds"),
            CompetitorEntry(name="Enzene Biosciences", country="India", funding_raised="Subsidiary of Alkem", approach="Biosimilar mammalian expression", startup_advantage="Specialized focus on small-molecule flow synthesis"),
        ],
        competition="Incumbent multinational industrial enzyme producers and domestic CDMOs.",
        sustainable_competitive_advantage="Proprietary sequence-structure transformer model trained on custom extremophile metagenomic library.",

        # Domain 3: Founder & Team Capability (FT-01 to FT-13)
        founder_details=[
            FounderEntry(name="Dr. Aarav Patel", role="Co-Founder & CEO", equity_percentage="45%", linkedin_url="https://linkedin.com/in/aaravpatel", education_degree="Ph.D. Synthetic Biology", education_institution="IIT Roorkee", graduation_year="2016", relevant_experience="10 years enzyme protein engineering", domain_expertise="Computational structural biology", prior_entrepreneurship="Co-founded SynBio Diagnostics (incubated at TIDES)", key_achievement="Engineered 14 novel functional enzymes"),
            FounderEntry(name="Dr. Meera Iyer", role="Co-Founder & CTO", equity_percentage="45%", linkedin_url="https://linkedin.com/in/meeraiyer", education_degree="Ph.D. Chemical Engineering", education_institution="IISc Bangalore", graduation_year="2017", relevant_experience="8 years process scale-up in pharma", domain_expertise="Continuous flow biocatalysis", prior_entrepreneurship="Senior Scientist at Biocon", key_achievement="Scaled 5 enzymatic processes to 5,000L"),
        ],
        founders=["Dr. Aarav Patel", "Dr. Meera Iyer"],
        founder_roles=["Co-Founder & CEO", "Co-Founder & CTO"],
        team="Multi-disciplinary team of protein biochemists, bioinformaticians, and chemical engineers.",
        core_team=[
            TeamMemberEntry(name="Dr. Vikram Rao", role="Lead Computational Biologist", credentials="Ph.D. Bioinformatics, 6 papers in Nature Biotech"),
            TeamMemberEntry(name="Pooja Sen", role="Head of Bioprocess", credentials="M.Tech Bioprocess, ex-Dr. Reddy's Laboratories"),
        ],
        critical_skill_gaps=["High-volume enzyme crystallization", "European pharma regulatory filing"],
        hiring_plan=[
            HiringPlanEntry(role="Regulatory Affairs Director", timing_quarter="Q2", skill_requirements="CDSCO and EMA active substance filings"),
            HiringPlanEntry(role="Senior Fermentation Engineer", timing_quarter="Q3", skill_requirements="Pilot fermenter operation at 500L+"),
        ],
        advisors=[
            AdvisorEntry(name="Prof. R. Mukherjee", organization="IIT Roorkee", role="Academic Advisor", contribution="Weekly structural review of enzyme active sites"),
            AdvisorEntry(name="S. Sundaram", organization="Ex-Director Sun Pharma", role="Industry Advisor", contribution="Commercial CDMO partnership introductions"),
        ],
        primary_mentor_contribution="Guiding active-site pocket optimization and fermentation scale-up.",
        secondary_mentor_contribution="Advising on intellectual property defense and CDMO contracts.",
        institutional_affiliations=["TIDES IIT Roorkee", "DBT-BIRAC", "CSIR-CDRI"],

        # Domain 4: Business Model & Commercialisation (BC-01 to BC-13)
        business_model="B2B proprietary enzyme supply plus milestone-based custom biocatalyst development.",
        revenue_model="Per-kg enzyme supply contracts and milestone/royalty fees on active pharma APIs.",
        pricing_strategy_unit="$350 per kg of immobilized enzyme with annual supply minimums",
        customer_acquisition_channels=["Direct enterprise sales to Tier-1 Indian CDMOs", "Joint development agreements with European generics makers"],
        cac="$60,000 per signed enterprise CDMO partnership",
        expected_gross_margin="62% on commercial enzyme supply",
        payback_period_months="16 months",
        path_to_first_10l_10k="Deliver 50kg evaluation batch to Hyderabad CDMO under commercial pilot agreement.",
        current_users="6 pharmaceutical R&D labs running sample trials",
        paying_customers="1",
        current_revenue="₹18,50,000 ($22,000) from paid validation batch",
        pilot_agreements=[
            PilotAgreementEntry(partner_name="Aurobindo Pharma CDMO Unit", agreement_type="Signed Pilot", is_signed=True, contract_value="₹35 Lakh"),
            PilotAgreementEntry(partner_name="Lonza Specialty Ingredients", agreement_type="LOI", is_signed=False, contract_value="€150,000"),
        ],
        awards_grants_recognition=["BIRAC BIG Grant 2024 Winner (₹50 Lakh)", "National Bio-Innovation Award 2025"],
        research_validation=["Published in ACS Catalysis 2024", "Third-party validation report by CSIR-IICT"],
        customer_quotes=["The Apex enzyme exceeded our thermal stability benchmark by 15C in batch tests."],

        # Domain 5: Innovation, IP & Impact (II-01 to II-11)
        proprietary_technology_moat="Proprietary generative enzyme design platform capable of predicting thermostabilizing mutations with 92% accuracy.",
        data_advantage="Proprietary dataset of 5,000+ experimentally tested enzyme variants with enzymatic turnover kinetics.",
        network_effects="Every customer screening run enhances predictive active-site design algorithms.",
        switching_costs="Pharma regulatory filings lock in specific enzyme catalyst sources for 5-7 years.",
        brand_community_moat="Premier reputation among academic biochemistry researchers in India.",
        regulatory_licensing_barriers="Requires Drug Master File (DMF) filing with US FDA and CEP with EDQM.",
        patent_details=[
            PatentEntry(title="Engineered Thermostable Biocatalyst for Amide Synthesis", application_number="202511099887", status="Filed", jurisdiction="India"),
            PatentEntry(title="Method for Generative Directed Evolution of Enzymes", application_number="PCT/IN2025/050123", status="Filed", jurisdiction="PCT / WIPO"),
        ],
        patents="Two patent applications filed covering enzyme sequence and computational design method.",
        primary_impact="Eliminating 500 kg of heavy metal effluent per tonne of active pharmaceutical ingredient manufactured.",
        sdg_alignments=[
            SDGAlignmentEntry(sdg_number=9, sdg_name="Industry, Innovation and Infrastructure", explanation="Sustainable industrial chemical manufacturing"),
            SDGAlignmentEntry(sdg_number=12, sdg_name="Responsible Consumption and Production", explanation="Drastic reduction of toxic hazardous waste"),
            SDGAlignmentEntry(sdg_number=13, sdg_name="Climate Action", explanation="Ambient-temperature processing cuts thermal energy consumption by 45%"),
        ],
        impact_metrics=[
            ImpactMetricEntry(metric_name="Heavy metal waste prevented", baseline="0 tonnes", target_3_year="250 tonnes"),
            ImpactMetricEntry(metric_name="CO2 energy emissions abated", baseline="0 MT", target_3_year="15,000 MT"),
        ],
        potential_negative_effects_mitigation="Enzymes are biodegradable proteins; zero bioaccumulative persistence or ecotoxicity.",

        # Domain 6: Financials & Incubation Support (FI-01 to FI-21)
        three_year_revenue=ThreeYearMetric(year_1="₹1.2 Crore", year_2="₹6.5 Crore", year_3="₹24.0 Crore"),
        three_year_gross_margin=ThreeYearMetric(year_1="45%", year_2="58%", year_3="64%"),
        three_year_customers=ThreeYearMetric(year_1="3", year_2="12", year_3="35"),
        three_year_team_size=ThreeYearMetric(year_1="10", year_2="24", year_3="48"),
        burn_rate="₹7.5 Lakh per month",
        break_even_timing="Month 24",
        financial_assumptions=["Average contract size ₹50L in Year 1", "Raw material fermentation cost ₹80/kg", "Customer retention 95%"],
        funding_raised="₹50 Lakh BIRAC BIG Grant (No external equity dilution to date)",
        current_monthly_operating_costs="₹9.5 Lakh per month",
        lab_facilities_requirements=["BL-2 fermentation suite", "High-performance liquid chromatography (HPLC) rig", "Automated colony picker"],
        mentorship_expertise_needed=["Faculty in Biochemical Engineering", "Pharma regulatory export strategist"],
        industry_connections_needed=["Indian Chemical Council", "Bulk Drug Manufacturers Association of India (BDMAI)"],
        legal_ip_support_needed=["PCT national phase entry filing in US, Europe, and Japan"],
        market_access_pilot_support_needed=["Pilot validation with state pharmaceutical research testbeds"],
        training_skill_building_needed=["ISO 13485 / cGMP cleanroom protocols"],
        six_quarter_product_roadmap=SixQuarterRoadmap(q1="100L fermentation optimization", q2="Enzyme immobilization chemistry", q3="Continuous flow reactor integration", q4="Scale-up to 1,000L batch", q5="Regulatory DMF filing", q6="Commercial cGMP batch release"),
        six_quarter_market_roadmap=SixQuarterRoadmap(q1="Engage 5 Indian CDMOs", q2="Execute 2 paid evaluation pilots", q3="Convert 1 pilot to multi-year supply agreement", q4="Expand to European generics markets", q5="Showcase at CPHI Worldwide", q6="Scale to 10 active commercial supply clients"),
        six_quarter_team_roadmap=SixQuarterRoadmap(q1="Hire Senior Fermentation Engineer", q2="Hire Regulatory Affairs Lead", q3="Hire 2 Quality Assurance Analysts", q4="Hire Business Development Director", q5="Hire Process Scaling Manager", q6="Hire 4 Shift Operators"),
        six_quarter_funding_roadmap=SixQuarterRoadmap(q1="Deploy BIRAC grant", q2="Initiate ₹8 Crore Pre-Series A", q3="Close Pre-Series A round", q4="Procure pilot fermentation line", q5="Achieve commercial revenue milestone", q6="Prepare $5M Series A round"),
        contact_info=ContactInfoEntry(representative_name="Dr. Aarav Patel", email="aarav@apexbiotechlabs.com", phone="+91 9897011223", website="https://apexbiotechlabs.com", address="TIDES Centre, Multi-Activity Centre, IIT Roorkee, Uttarakhand - 247667"),
        applicant_declaration=ApplicantDeclarationEntry(is_signed=True, signatory_name="Dr. Aarav Patel", declaration_date="2026-10-18"),
    )

    # Test JSON serialization and deserialization
    json_str = profile.model_dump_json()
    assert "Apex BioTech Labs" in json_str
    assert "Dr. Aarav Patel" in json_str
    assert "Dr. Meera Iyer" in json_str
    assert "Novozymes" in json_str
    assert "Codexis" in json_str

    deserialized = StartupProfileExtraction.model_validate_json(json_str)
    assert deserialized.company_name == "Apex BioTech Labs"
    assert len(deserialized.founder_details) == 2
    assert len(deserialized.competitor_details) == 3
    assert len(deserialized.key_features_benefits) == 3
    assert len(deserialized.sdg_alignments) == 3
    assert deserialized.three_year_revenue.year_1 == "₹1.2 Crore"
    assert deserialized.six_quarter_product_roadmap.q1 == "100L fermentation optimization"
    assert deserialized.applicant_declaration.is_signed is True


def test_multi_founder_parity_and_details():
    """Verifies that multiple co-founders each have complete parity of extracted information."""
    profile = StartupProfileExtraction(
        company_name="DualFounders Corp",
        founder_details=[
            FounderEntry(
                name="Founder Alpha",
                role="Chief Executive Officer",
                equity_percentage="60%",
                linkedin_url="https://linkedin.com/in/founderalpha",
                education_degree="B.Tech Computer Science",
                education_institution="IIT Roorkee",
                graduation_year="2018",
                relevant_experience="6 years distributed systems",
                domain_expertise="Cloud infrastructure",
                prior_entrepreneurship="Former VP Engineering at SaaS Unicorn",
                key_achievement="Built system processing 1M RPS"
            ),
            FounderEntry(
                name="Founder Beta",
                role="Chief Technology Officer",
                equity_percentage="40%",
                linkedin_url="https://linkedin.com/in/founderbeta",
                education_degree="Ph.D. Machine Learning",
                education_institution="Stanford University",
                graduation_year="2020",
                relevant_experience="5 years deep learning research",
                domain_expertise="Generative sequence modeling",
                prior_entrepreneurship="Research Fellow at DeepMind",
                key_achievement="Authored top-cited NeurIPS paper"
            )
        ]
    )
    assert len(profile.founder_details) == 2
    assert profile.founder_details[0].name == "Founder Alpha"
    assert profile.founder_details[1].name == "Founder Beta"
    assert profile.founder_details[0].equity_percentage == "60%"
    assert profile.founder_details[1].equity_percentage == "40%"
    assert "Stanford" in profile.founder_details[1].education_institution
    assert "IIT Roorkee" in profile.founder_details[0].education_institution


def test_competitor_matrix_with_international_requirement():
    """Enforces requirement for at least 3 competitors including an international rival."""
    profile = StartupProfileExtraction(
        competitor_details=[
            CompetitorEntry(name="Domestic Player A", country="India", approach="Low-cost assembly", startup_advantage="Proprietary software"),
            CompetitorEntry(name="Domestic Player B", country="India", approach="Enterprise services", startup_advantage="Self-serve PLG"),
            CompetitorEntry(name="International Leader C", country="Germany / Global", funding_raised="$150M", approach="High-end hardware", startup_advantage="50% lower TCO"),
        ]
    )
    assert len(profile.competitor_details) >= 3
    countries = [c.country for c in profile.competitor_details]
    assert any("global" in c.lower() or "germany" in c.lower() or "usa" in c.lower() for c in countries)


def test_explicit_zero_and_conditional_evidence_handling():
    """Verifies that bootstrapped zero funding, 0 paying customers, and no patents are not penalized."""
    profile = StartupProfileExtraction(
        company_name="Bootstrapped Early Stage AI",
        funding_raised="0",  # FI-08: Explicitly optional
        current_users="1,500 free trial users",
        paying_customers="0",  # BC-08: Strictly separate paying from free
        patent_details=[],  # II-07: Explicitly no patents filed
        patents=None,
        demo_prototype_link=None,  # PS-10: Conditional prototype evidence
        pilot_agreements=[
            PilotAgreementEntry(partner_name="Prospective Client A", agreement_type="LOI", is_signed=False),
            PilotAgreementEntry(partner_name="Committed Pilot B", agreement_type="Signed Pilot", is_signed=True, contract_value="₹5 Lakh")
        ]
    )

    # BC-08 distinction
    assert profile.paying_customers == "0"
    assert "free" in profile.current_users

    # BC-10 distinction
    assert profile.pilot_agreements[0].is_signed is False
    assert profile.pilot_agreements[1].is_signed is True

    # FI-08 optional
    assert profile.funding_raised == "0"


def test_claim_engine_canonical_mapping_and_backward_compatibility(db_session: Session):
    """Verifies that ClaimEngine maps all 87 canonical criteria and maintains 100% legacy compatibility."""
    startup = StartupApplication(startup_name="Canonical Test Startup", stage="MVP", current_status="Submitted")
    db_session.add(startup)
    db_session.flush()

    doc = Document(
        startup_id=startup.id,
        document_type=DocumentType.PITCH_DECK,
        original_filename="canonical_pitch_deck.pdf",
        stored_filename="canonical_pitch_deck.pdf",
        file_path="mock/canonical_pitch_deck.pdf",
        file_size=2048,
        processing_status=DocumentProcessingStatus.PARSED,
        # v1.1 evidence grounding: snippets are stored only for values found in document text.
        parsed_text=(
            "NanoFlow Technologies\n"
            "Microfluidic lab-on-a-chip diagnostic cartridges.\n"
            "Point-of-care blood diagnostics take hours and require cold-chain transport.\n"
            "Handheld microfluidic analyzer providing 12 blood parameters in 5 minutes.\n"
            "$8.5 Billion global point-of-care diagnostics market\n"
        ),
    )
    db_session.add(doc)
    db_session.flush()

    profile_data = StartupProfileExtraction(
        company_name="NanoFlow Technologies",
        tagline="Microfluidic lab-on-a-chip diagnostic cartridges.",
        sector="HealthTech",
        stage="Prototype",
        geography="Roorkee, Uttarakhand, India",
        problem_statement="Point-of-care blood diagnostics take hours and require cold-chain transport.",
        who_is_affected="Rural primary healthcare centers and emergency response paramedics.",
        solution="Handheld microfluidic analyzer providing 12 blood parameters in 5 minutes.",
        current_trl=5,
        trl_justification="TRL 5 validated in simulated clinical environment.",
        market_size="$8.5 Billion global point-of-care diagnostics market",
        revenue_model="Consumable cartridge sales and hardware device placement.",
        current_revenue="0.0",
        funding_raised="₹25 Lakh seed grant",
        burn_rate="₹3 Lakh per month",
        founders=["Dr. Ritu Verma", "Karan Dave"],
        founder_roles=["Co-Founder & CEO", "Co-Founder & COO"],
        founder_details=[
            FounderEntry(name="Dr. Ritu Verma", role="Co-Founder & CEO", education_degree="Ph.D. Biomedical Engineering", education_institution="IIT Roorkee"),
            FounderEntry(name="Karan Dave", role="Co-Founder & COO", education_degree="MBA", education_institution="IIM Ahmedabad")
        ],
        competitor_details=[
            CompetitorEntry(name="Abbott i-STAT", country="USA", funding_raised="Public", approach="Cartridge-based electrochemical", startup_advantage="4x lower cartridge cost"),
            CompetitorEntry(name="Siemens Epoc", country="Germany", funding_raised="Public", approach="Optical card", startup_advantage="Room temperature stable without refrigeration"),
            CompetitorEntry(name="Achira Labs", country="India", funding_raised="$10M Series A", approach="Fabric-based microfluidics", startup_advantage="Broader biomarker test panel")
        ],
        three_year_revenue=ThreeYearMetric(year_1="₹50 Lakh", year_2="₹3 Crore", year_3="₹12 Crore"),
        six_quarter_product_roadmap=SixQuarterRoadmap(q1="Lab validation", q2="Alpha prototype", q3="Clinical trial batch", q4="CDSCO certification", q5="Commercial launch", q6="Scale manufacturing"),
        patent_details=[
            PatentEntry(title="Passive Capillary Microfluidic Valve", application_number="202511044556", status="Filed", jurisdiction="India")
        ],
        patents="One patent filed for capillary microfluidic valve.",
        contact_info=ContactInfoEntry(representative_name="Dr. Ritu Verma", email="ritu@nanoflow.in", phone="+91 9876500000"),
        applicant_declaration=ApplicantDeclarationEntry(is_signed=True, signatory_name="Dr. Ritu Verma", declaration_date="2026-10-18")
    )

    claim_engine = ClaimEngine(db_session)
    claim_engine.process_canonical_profile(startup.id, profile_data, doc.id)

    # 1. Verify profile created
    intel_profile = db_session.query(StartupIntelligenceProfile).filter_by(startup_id=startup.id).first()
    assert intel_profile is not None

    # 2. Verify canonical claims populated
    claims = db_session.query(StartupClaim).filter_by(profile_id=intel_profile.id).all()
    assert len(claims) > 30

    field_keys = {c.field.field_key for c in claims if c.field}

    # Verify canonical keys exist
    assert "cm_01_company_name" in field_keys
    assert "ps_01_problem_statement" in field_keys
    assert "ps_09_current_trl" in field_keys
    assert "mo_01_tam" in field_keys
    assert "mo_07_competitor_details" in field_keys
    assert "ft_01_founder_details" in field_keys
    assert "fi_01_three_year_revenue" in field_keys
    assert "fi_16_six_quarter_product_roadmap" in field_keys
    assert "ii_07_patent_details" in field_keys

    # Verify legacy keys exist for backward compatibility
    assert "founder_names" in field_keys
    assert "problem_solved" in field_keys
    assert "solution_value_prop" in field_keys
    assert "target_market" in field_keys
    assert "market_size" in field_keys
    assert "competitors" in field_keys
    assert "revenue_model" in field_keys
    assert "trl_level" in field_keys
    assert "ip_status" in field_keys

    # 3. Verify evidence linked
    evidence = db_session.query(StartupEvidence).all()
    assert len(evidence) > 30
    assert any("NanoFlow Technologies" in e.evidence_snippet for e in evidence if e.evidence_snippet)


def test_mock_gateway_extraction_with_budget_reservation_and_tracking():
    """Verifies that MockAIGateway tracks tokens, reconciles budget, and enriches extraction metadata."""
    eval_id = str(uuid.uuid4())
    cost_manager = CostLedgerManager.get_instance()
    ledger = cost_manager.get_or_create_ledger(
        evaluation_id=eval_id,
        startup_id=str(uuid.uuid4()),
        max_budget_usd=0.55
    )

    gateway = MockAIGateway()
    req = AICompletionRequest(
        system_prompt="You are a VC analyst.",
        user_prompt="Pitch deck text from CleanEnergy Corp with hydrogen fuel cell technology.",
        evaluation_id=eval_id,
        agent_name="document_extraction",
        task_type="extraction"
    )

    result = gateway.complete_json(req, StartupProfileExtraction)
    extracted: StartupProfileExtraction = result.data

    # Check extracted data
    assert extracted.company_name == "CleanEnergy Corp"
    assert len(extracted.founder_details) == 2
    assert len(extracted.competitor_details) == 3
    assert extracted.current_trl == 6
    assert extracted.three_year_revenue is not None

    # Check cost observability in metadata
    assert result.metadata.evaluation_id == eval_id
    assert result.metadata.input_tokens > 0
    assert result.metadata.output_tokens > 0
    assert result.metadata.cost_usd > 0.0
    assert result.metadata.cost_inr > 0.0
    assert result.metadata.buffered_cost_inr > 0.0

    # Verify ledger spent was reconciled
    assert ledger.spent_usd > 0.0
    assert ledger.spent_usd <= 0.55
    assert ledger.remaining_budget_usd > 0.0


def test_budget_exhaustion_ceiling_enforcement_in_mock():
    """Enforces that an evaluation with exceeded budget throws AIBudgetExhaustedError."""
    eval_id = str(uuid.uuid4())
    cost_manager = CostLedgerManager.get_instance()
    ledger = cost_manager.get_or_create_ledger(
        evaluation_id=eval_id,
        max_budget_usd=0.000001  # Ultra-low ceiling to force exhaustion
    )

    gateway = MockAIGateway()
    req = AICompletionRequest(
        system_prompt="Analyze startup.",
        user_prompt="Some startup content.",
        evaluation_id=eval_id,
        agent_name="test_operation"
    )

    with pytest.raises(AIBudgetExhaustedError) as exc_info:
        gateway.complete_json(req, StartupProfileExtraction)

    assert "would exceed budget ceiling" in str(exc_info.value)
    assert ledger.is_exhausted is True


def test_provenance_tracking_across_all_claims_and_evidence(db_session: Session):
    """Verifies that ClaimEngine establishes explicit provenance (page_number, section_name,

    confidence_score, supporting_evidence) across all generated claims.
    """
    startup = StartupApplication(startup_name="Provenance Startup", stage="Prototype", current_status="Submitted")
    db_session.add(startup)
    db_session.flush()

    doc = Document(
        startup_id=startup.id,
        document_type=DocumentType.PITCH_DECK,
        original_filename="provenance_deck.pdf",
        stored_filename="provenance_deck.pdf",
        file_path="mock/provenance_deck.pdf",
        file_size=4096,
        processing_status=DocumentProcessingStatus.PARSED,
        parsed_text=(
            "Provenance AI - Verified audit trail AI\n"
            "Problem: Unverifiable claims lead to bad venture investments.\n"
            "Solution: Automated evidence-grounded claim extraction engine.\n"
            "TRL 6 pilot demonstrated in sandbox.\n"
            "Market: $5 Billion verification market\n"
            "Competitor: LegacyAuditor Inc (USA) - Manual spreadsheets; we are 100x faster automated provenance\n"
            "Founder: Dr. Proof, Chief Scientist, Ph.D. IIT Roorkee\n"
            "Revenue plan: year 1 ₹50L, year 2 ₹2Cr, year 3 ₹8Cr\n"
            "Current revenue ₹10 Lakh\n"
            "Patent: Evidence Graph Verification System, application 202611001122, Filed, India\n"
        ),
    )
    db_session.add(doc)
    db_session.flush()

    profile_data = StartupProfileExtraction(
        company_name="Provenance AI",
        tagline="Verified audit trail AI",
        problem_statement="Unverifiable claims lead to bad venture investments.",
        solution="Automated evidence-grounded claim extraction engine.",
        current_trl=6,
        trl_justification="TRL 6 pilot demonstrated in sandbox.",
        market_size="$5 Billion verification market",
        competitor_details=[
            CompetitorEntry(name="LegacyAuditor Inc", country="USA", approach="Manual spreadsheets", startup_advantage="100x faster automated provenance")
        ],
        founder_details=[
            FounderEntry(name="Dr. Proof", role="Chief Scientist", education_degree="Ph.D.", education_institution="IIT Roorkee")
        ],
        three_year_revenue=ThreeYearMetric(year_1="₹50L", year_2="₹2Cr", year_3="₹8Cr"),
        current_revenue="₹10 Lakh",
        funding_raised="0",
        patent_details=[
            PatentEntry(title="Evidence Graph Verification System", application_number="202611001122", status="Filed", jurisdiction="India")
        ]
    )

    claim_engine = ClaimEngine(db_session)
    claim_engine.process_canonical_profile(startup.id, profile_data, doc.id)

    intel_profile = db_session.query(StartupIntelligenceProfile).filter_by(startup_id=startup.id).first()
    assert intel_profile is not None

    claims = db_session.query(StartupClaim).filter_by(profile_id=intel_profile.id).all()
    assert len(claims) > 10

    evidence_records = db_session.query(StartupEvidence).all()
    assert len(evidence_records) >= len(claims)

    # Verify provenance fields across all claims and evidence
    for claim in claims:
        assert claim.confidence_score > 0.0
        assert claim.confidence_score <= 1.0
        assert claim.reasoning is not None
        assert claim.confidence_reason is not None

        # Evidence must link to parent claim and document
        claim_evidence = [e for e in evidence_records if e.claim_id == claim.id]
        assert len(claim_evidence) >= 1
        for ev in claim_evidence:
            assert ev.source_document_id == doc.id
            assert ev.section_name is not None
            assert ev.confidence_score > 0.0
            assert ev.confidence_score <= 1.0
            # Stronger invariant than before: a stored snippet must be a real document passage.
            if ev.evidence_snippet is not None:
                assert len(ev.evidence_snippet) > 0
                for part in ev.evidence_snippet.split(" / "):
                    # Passages may span consecutive lines; compare with whitespace normalised.
                    assert " ".join(part.split()) in " ".join(doc.parsed_text.split())
    grounded = [e for e in evidence_records if e.evidence_snippet]
    assert len(grounded) >= 8, "most disclosed values must be grounded in the document text"

    # Specifically check parsed page numbers from section names
    problem_claim = next(c for c in claims if c.field.field_key == "ps_01_problem_statement")
    problem_ev = next(e for e in evidence_records if e.claim_id == problem_claim.id)
    assert problem_ev.section_name == "Slide 3"
    assert problem_ev.page_number == 3

    revenue_claim = next(c for c in claims if c.field.field_key == "fi_01_three_year_revenue")
    revenue_ev = next(e for e in evidence_records if e.claim_id == revenue_claim.id)
    assert revenue_ev.section_name == "Slide 15"
    assert revenue_ev.page_number == 15


def test_negative_zero_missing_optional_conditional_handling(db_session: Session):
    """Verifies that negative numbers, explicit zeroes, empty lists, and missing optional

    fields are safely processed without schema validation or claim extraction errors.
    """
    startup = StartupApplication(startup_name="Negative Zero Startup", stage="Ideation", current_status="Submitted")
    db_session.add(startup)
    db_session.flush()

    doc = Document(
        startup_id=startup.id,
        document_type=DocumentType.APPLICATION_FORM,
        original_filename="app_form.pdf",
        stored_filename="app_form.pdf",
        file_path="mock/app_form.pdf",
        file_size=1024,
        processing_status=DocumentProcessingStatus.PARSED
    )
    db_session.add(doc)
    db_session.flush()

    # Create profile with negative margins, explicit zeroes, empty optional lists, None values
    profile_data = StartupProfileExtraction(
        company_name="Zero-Negative Dynamics",
        tagline="Testing edge cases in evaluation",
        problem_statement="Startups with zero revenue and negative early margins get improperly flagged.",
        solution="Robust boundary handling in canonical evaluation.",
        current_trl=2,
        expected_gross_margin="-15.5%",  # Negative gross margin
        current_users="0",  # Zero users
        paying_customers="0",  # Zero paying customers
        current_revenue="0.0",  # Zero revenue
        funding_raised="0",  # Zero funding / bootstrapped
        burn_rate="-₹4.5 Lakh",  # Explicit negative cash outflow representation
        competitor_details=[],  # Empty list of competitors
        founder_details=[
            FounderEntry(name="Solo Founder", role="Sole Proprietor")
        ],
        advisors=None,  # Missing optional list
        key_features_benefits=[],  # Empty optional list
        patent_details=[],  # Empty patent list
        patents=None,  # None patent string
        demo_prototype_link=None,  # Conditional field absent
    )

    # Verification: Pydantic accepts the edge values
    assert profile_data.expected_gross_margin == "-15.5%"
    assert profile_data.paying_customers == "0"
    assert profile_data.funding_raised == "0"
    assert profile_data.demo_prototype_link is None
    assert profile_data.competitor_details == []

    # Verification: ClaimEngine safely processes negative, zero, and empty values
    claim_engine = ClaimEngine(db_session)
    claim_engine.process_canonical_profile(startup.id, profile_data, doc.id)

    intel_profile = db_session.query(StartupIntelligenceProfile).filter_by(startup_id=startup.id).first()
    assert intel_profile is not None

    claims = db_session.query(StartupClaim).filter_by(profile_id=intel_profile.id).all()
    assert len(claims) > 0

    field_map = {c.field.field_key: c for c in claims if c.field}

    # Zero funding claim must exist and be recorded properly
    assert "fi_08_funding_raised" in field_map
    funding_claim = field_map["fi_08_funding_raised"]
    assert funding_claim.value_string == "0"

    # Paying customers zero must exist
    assert "bc_08_paying_customers" in field_map
    assert field_map["bc_08_paying_customers"].value_string == "0"

    # Negative margin must exist and preserve negative string
    assert "bc_05_expected_gross_margin" in field_map
    margin_claim = field_map["bc_05_expected_gross_margin"]
    assert margin_claim.value_string == "-15.5%"

    # TRL number extraction
    assert "ps_09_current_trl" in field_map
    trl_claim = field_map["ps_09_current_trl"]
    assert trl_claim.value_number == 2.0

    # II-07 patents summary should reflect zero IP without error
    assert "ii_07_patents_summary" in field_map
    assert field_map["ii_07_patents_summary"].value_string == "No IP filed"


def test_partial_evaluation_budget_exhaustion_pipeline_handling():
    """Verifies that an evaluation pipeline catches AIBudgetExhaustedError and marks the evaluation

    as partially completed with budget exhaustion state, without corrupting previous records.
    """
    eval_id = str(uuid.uuid4())
    cost_manager = CostLedgerManager.get_instance()
    ledger = cost_manager.get_or_create_ledger(
        evaluation_id=eval_id,
        startup_id=str(uuid.uuid4()),
        max_budget_usd=0.03  # Low budget sufficient for extraction but exhausted for subsequent calls
    )

    gateway = MockAIGateway()

    # Step 1: Extraction call succeeds
    req_extraction = AICompletionRequest(
        system_prompt="Extract startup deck.",
        user_prompt="Pitch deck text from CleanEnergy Corp with hydrogen fuel cell technology.",
        evaluation_id=eval_id,
        agent_name="document_extraction",
        operation_type="extraction"
    )
    result = gateway.complete_json(req_extraction, StartupProfileExtraction)
    assert result.data.company_name == "CleanEnergy Corp"
    assert ledger.spent_usd > 0.0
    assert ledger.is_exhausted is False

    # Step 2: Next expensive call causes exhaustion
    req_expensive_review = AICompletionRequest(
        system_prompt="Full supervisory evaluation.",
        user_prompt="Run heavy reasoning evaluation.",
        evaluation_id=eval_id,
        agent_name="supervisory_review",
        operation_type="expert_evaluation",
        max_output_tokens=4000
    )

    pipeline_status = "IN_PROGRESS"
    partial_results = {"extraction": result.data}

    try:
        gateway.complete_json(req_expensive_review, StartupProfileExtraction)
        pipeline_status = "COMPLETED"
    except AIBudgetExhaustedError:
        pipeline_status = "PARTIAL_BUDGET_EXHAUSTED"

    # Verify pipeline handled budget exhaustion gracefully
    assert pipeline_status == "PARTIAL_BUDGET_EXHAUSTED"
    assert "extraction" in partial_results
    assert partial_results["extraction"].company_name == "CleanEnergy Corp"
    assert ledger.is_exhausted is True
    summary = ledger.get_summary()
    assert summary["total_operations"] == 1
    assert summary["under_max_usd_ceiling"] is True

