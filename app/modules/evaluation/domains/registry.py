"""registry.py - Authoritative Mapping of 87 Canonical Criteria to the 6 Evaluation Domains.

Strictly follows the LaunchIndex Pitch Deck Specification (18 slides across 6 domains + cover metadata).
Every criterion has exactly one primary evaluation domain owner.
"""

from typing import Dict, List, Any


CANONICAL_DOMAINS: Dict[str, Dict[str, Any]] = {
    "problem_solution": {
        "title": "Problem & Solution",
        "slides": [3, 4, 5],
        "prefix": "PS",
        "description": "Evaluates core problem severity, affected personas, workarounds, persistence barriers, solution, 3 features & benefits, UVP, TRL, architecture, and conditional prototype validation.",
    },
    "market_opportunity": {
        "title": "Market Opportunity & Competition",
        "slides": [6, 7],
        "prefix": "MO",
        "description": "Evaluates TAM/SAM/SOM, market growth CAGR & sources, key drivers, geographic focus, and dynamic competitor benchmarking (>=3 competitors including international).",
    },
    "founder_team": {
        "title": "Founder & Team Capability",
        "slides": [8, 9, 10],
        "prefix": "FT",
        "description": "Evaluates multi-founder backgrounds, education, experience, domain expertise, prior ventures, core team, skill gaps, hiring roadmap, named advisors, and institutional affiliations.",
    },
    "commercialisation": {
        "title": "Business Model & Commercialisation",
        "slides": [11, 12],
        "prefix": "BC",
        "description": "Evaluates business & revenue model, pricing unit metrics, GTM channels, CAC, margins, payback, first ₹10L roadmap, users vs paying customers, signed pilots vs LOIs, and awards.",
    },
    "innovation_impact": {
        "title": "Innovation, IP & Impact",
        "slides": [13, 14],
        "prefix": "II",
        "description": "Evaluates proprietary technology moat, data advantage, network effects, switching costs, brand moats, regulatory barriers, patent disclosures, and UN SDG alignment.",
    },
    "financials_support": {
        "title": "Financials & Incubation Support",
        "slides": [15, 16, 17, 18],
        "prefix": "FI",
        "description": "Evaluates 3-year forecasts, monthly burn, break-even timing, financial assumptions, operating costs, optional funding, TIDES lab/mentorship needs, and 6-quarter roadmaps.",
    },
}

INTAKE_METADATA_DOMAIN: str = "intake_completeness"

# Authoritative 87-criteria directory
CRITERIA_DIRECTORY: Dict[str, Dict[str, Any]] = {
    # ── Cover & Application Metadata (CM-01 to CM-06) ──
    # Handled by intake & completeness layer for application verification
    "CM-01": {"domain": "intake_completeness", "name": "Company Name", "slide": 1, "is_required": True},
    "CM-02": {"domain": "intake_completeness", "name": "Tagline / Value Statement", "slide": 1, "is_required": True},
    "CM-03": {"domain": "intake_completeness", "name": "Sector Classification", "slide": 1, "is_required": True},
    "CM-04": {"domain": "intake_completeness", "name": "Current Operational Stage", "slide": 1, "is_required": True},
    "CM-05": {"domain": "intake_completeness", "name": "Operating Geography", "slide": 1, "is_required": True},
    "CM-06": {"domain": "intake_completeness", "name": "Application Submission Date", "slide": 1, "is_required": True},

    # ── Domain 1: Problem & Solution (PS-01 to PS-13) ──
    "PS-01": {"domain": "problem_solution", "name": "Core Problem Statement", "slide": 3, "is_required": True},
    "PS-02": {"domain": "problem_solution", "name": "Who is Affected (Target Persona)", "slide": 3, "is_required": True},
    "PS-03": {"domain": "problem_solution", "name": "Current Workarounds & Inertia", "slide": 3, "is_required": True},
    "PS-04": {"domain": "problem_solution", "name": "Evidence of the Problem (Pain Metrics)", "slide": 3, "is_required": True},
    "PS-05": {"domain": "problem_solution", "name": "Why the Problem Persists (Barrier)", "slide": 3, "is_required": True},
    "PS-06": {"domain": "problem_solution", "name": "Solution Description & Core Offering", "slide": 4, "is_required": True},
    "PS-07": {"domain": "problem_solution", "name": "Three Key Features & Benefits", "slide": 4, "is_required": True},
    "PS-08": {"domain": "problem_solution", "name": "Unique Value Proposition (UVP)", "slide": 4, "is_required": True},
    "PS-09": {"domain": "problem_solution", "name": "Current TRL & Justification", "slide": 5, "is_required": True},
    "PS-10": {"domain": "problem_solution", "name": "Demo / Prototype Link", "slide": 5, "is_required": False, "is_conditional": True},
    "PS-11": {"domain": "problem_solution", "name": "Prototype Maturity Stage", "slide": 5, "is_required": True},
    "PS-12": {"domain": "problem_solution", "name": "Technical Architecture & Components", "slide": 5, "is_required": True},
    "PS-13": {"domain": "problem_solution", "name": "Technical Validation & Lab Test Results", "slide": 5, "is_required": True},

    # ── Domain 2: Market Opportunity (MO-01 to MO-10) ──
    "MO-01": {"domain": "market_opportunity", "name": "Total Addressable Market (TAM)", "slide": 6, "is_required": True},
    "MO-02": {"domain": "market_opportunity", "name": "Serviceable Addressable Market (SAM)", "slide": 6, "is_required": True},
    "MO-03": {"domain": "market_opportunity", "name": "Serviceable Obtainable Market (SOM)", "slide": 6, "is_required": True},
    "MO-04": {"domain": "market_opportunity", "name": "Market CAGR & Source Citation", "slide": 6, "is_required": True},
    "MO-05": {"domain": "market_opportunity", "name": "Key Market Drivers & Macro Tailwinds", "slide": 6, "is_required": True},
    "MO-06": {"domain": "market_opportunity", "name": "Geographic Launch Focus & Segment", "slide": 6, "is_required": True},
    "MO-07": {"domain": "market_opportunity", "name": "Competitor 1 (Direct Benchmark)", "slide": 7, "is_required": True},
    "MO-08": {"domain": "market_opportunity", "name": "Competitor 2 (Domestic Benchmark)", "slide": 7, "is_required": True},
    "MO-09": {"domain": "market_opportunity", "name": "Competitor 3 (International Benchmark)", "slide": 7, "is_required": True},
    "MO-10": {"domain": "market_opportunity", "name": "Sustainable Competitive Advantage (Moat)", "slide": 7, "is_required": True},

    # ── Domain 3: Founder & Team Capability (FT-01 to FT-13) ──
    "FT-01": {"domain": "founder_team", "name": "Founder 1 Identity, Role & Equity", "slide": 8, "is_required": True},
    "FT-02": {"domain": "founder_team", "name": "Founder 1 LinkedIn Profile URL", "slide": 8, "is_required": True},
    "FT-03": {"domain": "founder_team", "name": "Founder 1 Education, Degree & University", "slide": 8, "is_required": True},
    "FT-04": {"domain": "founder_team", "name": "Founder 1 Experience & Domain Expertise", "slide": 8, "is_required": True},
    "FT-05": {"domain": "founder_team", "name": "Founder 1 Prior Entrepreneurship & Exits", "slide": 8, "is_required": True},
    "FT-06": {"domain": "founder_team", "name": "Co-Founders Records (Full Parity)", "slide": 8, "is_required": True},
    "FT-07": {"domain": "founder_team", "name": "Core Team Members & Credentials", "slide": 9, "is_required": False},
    "FT-08": {"domain": "founder_team", "name": "Critical Self-Identified Skill Gaps", "slide": 9, "is_required": True},
    "FT-09": {"domain": "founder_team", "name": "Key Hiring Plan & Target Quarters", "slide": 9, "is_required": True},
    "FT-10": {"domain": "founder_team", "name": "Named Mentors & Advisors", "slide": 10, "is_required": True},
    "FT-11": {"domain": "founder_team", "name": "Primary Mentor Contribution & Cadence", "slide": 10, "is_required": True},
    "FT-12": {"domain": "founder_team", "name": "Secondary Mentor / Institutional Support", "slide": 10, "is_required": False},
    "FT-13": {"domain": "founder_team", "name": "Institutional Affiliations (Labs/Grants)", "slide": 10, "is_required": False},

    # ── Domain 4: Business Model & Commercialisation (BC-01 to BC-13) ──
    "BC-01": {"domain": "commercialisation", "name": "Business Model & Monetization Mechanics", "slide": 11, "is_required": True},
    "BC-02": {"domain": "commercialisation", "name": "Pricing Strategy Tiers & Unit Metric", "slide": 11, "is_required": True},
    "BC-03": {"domain": "commercialisation", "name": "Customer Acquisition Channels (GTM)", "slide": 11, "is_required": True},
    "BC-04": {"domain": "commercialisation", "name": "Customer Acquisition Cost (CAC)", "slide": 11, "is_required": False, "is_conditional": True},
    "BC-05": {"domain": "commercialisation", "name": "Expected Gross Margin (%)", "slide": 11, "is_required": True},
    "BC-06": {"domain": "commercialisation", "name": "CAC Payback Period in Months", "slide": 11, "is_required": False},
    "BC-07": {"domain": "commercialisation", "name": "Path to First ₹10 Lakh / $10,000", "slide": 11, "is_required": True},
    "BC-08": {"domain": "commercialisation", "name": "Current Users and Paying Customers", "slide": 12, "is_required": True},
    "BC-09": {"domain": "commercialisation", "name": "Revenue Achieved to Date", "slide": 12, "is_required": True},
    "BC-10": {"domain": "commercialisation", "name": "Pilot Agreements & LOIs (Signed vs Draft)", "slide": 12, "is_required": True},
    "BC-11": {"domain": "commercialisation", "name": "Awards, Grants & Recognition Won", "slide": 12, "is_required": False},
    "BC-12": {"domain": "commercialisation", "name": "Research Validation & Publications", "slide": 12, "is_required": False, "is_conditional": True},
    "BC-13": {"domain": "commercialisation", "name": "Customer Feedback & Direct Quotes", "slide": 12, "is_required": False},

    # ── Domain 5: Innovation, IP & Impact (II-01 to II-11) ──
    "II-01": {"domain": "innovation_impact", "name": "Proprietary Technology Moat & Non-Trivial Leap", "slide": 13, "is_required": True},
    "II-02": {"domain": "innovation_impact", "name": "Proprietary Data Advantage & Flywheel", "slide": 13, "is_required": False, "is_conditional": True},
    "II-03": {"domain": "innovation_impact", "name": "Platform Network Effects", "slide": 13, "is_required": False},
    "II-04": {"domain": "innovation_impact", "name": "Customer Switching Costs & Workflow Lock-in", "slide": 13, "is_required": True},
    "II-05": {"domain": "innovation_impact", "name": "Brand Equity & Developer Community Moat", "slide": 13, "is_required": False},
    "II-06": {"domain": "innovation_impact", "name": "Regulatory & Licensing Barriers (FDA/CDSCO)", "slide": 13, "is_required": False, "is_conditional": True},
    "II-07": {"domain": "innovation_impact", "name": "IP Status (Patents, Trademarks, Secrets)", "slide": 13, "is_required": True},
    "II-08": {"domain": "innovation_impact", "name": "Primary Social / Environmental / Economic Impact", "slide": 14, "is_required": True},
    "II-09": {"domain": "innovation_impact", "name": "UN SDG Alignment & Specific Rationale", "slide": 14, "is_required": True},
    "II-10": {"domain": "innovation_impact", "name": "Measurable Impact KPIs & 3-Year Targets", "slide": 14, "is_required": True},
    "II-11": {"domain": "innovation_impact", "name": "Negative Externality Risks & Mitigation", "slide": 14, "is_required": True},

    # ── Domain 6: Financials & Incubation Support (FI-01 to FI-21) ──
    "FI-01": {"domain": "financials_support", "name": "Three-Year Revenue Forecast (Y1-Y3)", "slide": 15, "is_required": True},
    "FI-02": {"domain": "financials_support", "name": "Three-Year Gross Margin Forecast (Y1-Y3)", "slide": 15, "is_required": True},
    "FI-03": {"domain": "financials_support", "name": "Three-Year Customer Count Forecast (Y1-Y3)", "slide": 15, "is_required": True},
    "FI-04": {"domain": "financials_support", "name": "Three-Year Headcount Forecast (Y1-Y3)", "slide": 15, "is_required": True},
    "FI-05": {"domain": "financials_support", "name": "Monthly Net Cash Burn Rate", "slide": 15, "is_required": True},
    "FI-06": {"domain": "financials_support", "name": "Break-Even Timing Projected Month/Year", "slide": 15, "is_required": True},
    "FI-07": {"domain": "financials_support", "name": "Core Financial & Unit Economic Assumptions", "slide": 15, "is_required": True},
    "FI-08": {"domain": "financials_support", "name": "External Funding Raised (Explicitly Optional)", "slide": 15, "is_required": False, "is_conditional": True},
    "FI-09": {"domain": "financials_support", "name": "Current Monthly Operating Costs Breakdown", "slide": 15, "is_required": True},
    "FI-10": {"domain": "financials_support", "name": "Lab & Facility Requirements (Cleanrooms/Labs)", "slide": 16, "is_required": True},
    "FI-11": {"domain": "financials_support", "name": "Faculty & Mentorship Technical Support Needed", "slide": 16, "is_required": True},
    "FI-12": {"domain": "financials_support", "name": "Corporate & PSU Industry Connections Needed", "slide": 16, "is_required": True},
    "FI-13": {"domain": "financials_support", "name": "Legal & Patent Drafting Support Needed", "slide": 16, "is_required": True},
    "FI-14": {"domain": "financials_support", "name": "Campus Trial Bed & Market Pilot Access Needed", "slide": 16, "is_required": True},
    "FI-15": {"domain": "financials_support", "name": "Training Workshops & Founder Coaching Needed", "slide": 16, "is_required": False},
    "FI-16": {"domain": "financials_support", "name": "Six-Quarter Product Roadmap (Q1–Q6)", "slide": 17, "is_required": True},
    "FI-17": {"domain": "financials_support", "name": "Six-Quarter Market & GTM Roadmap (Q1–Q6)", "slide": 17, "is_required": True},
    "FI-18": {"domain": "financials_support", "name": "Six-Quarter Team Hiring Roadmap (Q1–Q6)", "slide": 17, "is_required": True},
    "FI-19": {"domain": "financials_support", "name": "Six-Quarter Capital Deployment Roadmap (Q1–Q6)", "slide": 17, "is_required": True},
    "FI-20": {"domain": "financials_support", "name": "Authorized Representative Contact Details", "slide": 18, "is_required": True},
    "FI-21": {"domain": "financials_support", "name": "Applicant Declaration, Signatory & Date", "slide": 18, "is_required": True},
}


def get_domain_for_criterion(criterion_id: str) -> str:
    """Returns the primary owning domain for a canonical criterion ID."""
    cid = criterion_id.upper()
    if cid in CRITERIA_DIRECTORY:
        return CRITERIA_DIRECTORY[cid]["domain"]
    if cid.startswith("PS"):
        return "problem_solution"
    if cid.startswith("MO"):
        return "market_opportunity"
    if cid.startswith("FT"):
        return "founder_team"
    if cid.startswith("BC"):
        return "commercialisation"
    if cid.startswith("II"):
        return "innovation_impact"
    if cid.startswith("FI"):
        return "financials_support"
    if cid.startswith("CM"):
        return "intake_completeness"
    return "problem_solution"


def get_criteria_for_domain(domain_key: str) -> List[str]:
    """Returns all canonical criteria IDs owned by a specific domain."""
    return [cid for cid, info in CRITERIA_DIRECTORY.items() if info["domain"] == domain_key]


def get_criterion_metadata(criterion_id: str) -> Dict[str, Any]:
    """Returns the metadata dictionary for a criterion ID."""
    return CRITERIA_DIRECTORY.get(criterion_id.upper(), {
        "domain": get_domain_for_criterion(criterion_id),
        "name": criterion_id,
        "slide": 1,
        "is_required": True
    })
