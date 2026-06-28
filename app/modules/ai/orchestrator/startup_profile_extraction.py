from pydantic import BaseModel, Field
from typing import List, Optional


class StartupProfileExtraction(BaseModel):
    """
    Atomic structured fields extracted from a startup pitch deck.
    Every field must be a single atomic value (a name, a sentence, a number).
    Never include raw paragraphs, OCR text dumps, slide text, bullet lists,
    roadmap text, email addresses, or phone numbers in any field.
    If information is not present, return null for that field.
    """

    # Company identity
    company_name: Optional[str] = Field(
        default=None,
        description="The legal or trading name of the startup. Example: 'PETREVOLT ENERGY SOLUTIONS PVT LTD'"
    )

    # Founders
    founders: List[str] = Field(
        default_factory=list,
        description=(
            "List of individual founder names only. Each entry is a single person's name. "
            "Example: ['Princya Polin S', 'Ashwin Kumar P']. Do NOT include titles, roles, or descriptions."
        )
    )
    founder_roles: List[str] = Field(
        default_factory=list,
        description=(
            "Roles corresponding to each founder in the same order as the founders list. "
            "Example: ['Co-Founder & CEO', 'Co-Founder & CTO']. One entry per founder."
        )
    )

    # Problem & Solution
    problem_statement: Optional[str] = Field(
        default=None,
        description=(
            "A single concise sentence describing the core problem the startup addresses. "
            "Example: 'India depends on imported lithium-ion batteries, creating high costs and supply chain risk.'"
        )
    )
    solution: Optional[str] = Field(
        default=None,
        description=(
            "A single concise sentence describing what the startup has built to solve the problem. "
            "Example: 'Solid-state sodium-ion batteries manufactured from recycled PET plastic waste.'"
        )
    )

    # Technology
    technology: Optional[str] = Field(
        default=None,
        description=(
            "A single sentence naming and describing the core technology. "
            "Example: 'Solid-state sodium-ion battery using disodium terephthalate derived from PET solvolysis.'"
        )
    )
    patents: Optional[str] = Field(
        default=None,
        description=(
            "A single sentence summarising patent or IP status. "
            "Example: 'Patent filed for PET-to-liquid-electrolyte conversion process.' "
            "Return null if no IP is mentioned."
        )
    )

    # Market
    market: Optional[str] = Field(
        default=None,
        description=(
            "A single sentence identifying the primary target market or customer segment. "
            "Example: 'Electric two-wheeler and three-wheeler manufacturers in India such as Ola Electric and Ather Energy.'"
        )
    )
    market_size: Optional[str] = Field(
        default=None,
        description=(
            "A single atomic value for the total addressable market, with unit. "
            "Example: '1.3 TWh India battery storage demand by 2047' or '$4.5 billion TAM'. "
            "Return null if not stated."
        )
    )

    # Business & Revenue
    business_model: Optional[str] = Field(
        default=None,
        description=(
            "A single sentence describing how the company makes money or plans to. "
            "Example: 'B2B battery cell sales to EV OEMs and stationary storage integrators.'"
        )
    )
    revenue_model: Optional[str] = Field(
        default=None,
        description=(
            "A single sentence describing the revenue model (e.g., subscription, per-unit, licensing). "
            "Example: 'Per-unit cell sales with long-term supply agreements.' Return null if not stated."
        )
    )

    # Competition
    competition: Optional[str] = Field(
        default=None,
        description=(
            "A single sentence naming key competitors or the competitive landscape. "
            "Example: 'Competes with imported lithium-ion battery suppliers and emerging domestic players like Log9 Materials.'"
        )
    )

    # Traction
    traction: Optional[str] = Field(
        default=None,
        description=(
            "A single sentence summarising the most significant traction milestone achieved. "
            "Example: 'Rechargeable PoC with reversible Na-ion intercalation demonstrated; patent applied.' "
            "Return null if no traction is mentioned."
        )
    )

    # Team
    team: Optional[str] = Field(
        default=None,
        description=(
            "A single sentence summarising the team's relevant background and expertise. "
            "Example: 'Founders from Military College of Telecommunication Engineering with domain expertise in electrochemistry.'"
        )
    )

    # Financials
    financial_information: Optional[str] = Field(
        default=None,
        description=(
            "A single sentence summarising the key financial data point from the deck. "
            "Example: 'Pre-revenue; seeking seed investment for Phase 2 R&D.'"
        )
    )
    funding_ask: Optional[str] = Field(
        default=None,
        description=(
            "The specific funding amount the startup is requesting in this round. "
            "Example: 'Rs 5 crore seed round' or '$500K pre-seed'. Return null if not stated."
        )
    )
    funding_raised: Optional[str] = Field(
        default=None,
        description=(
            "Total external funding raised to date. "
            "Example: '$1.2 million raised across two rounds'. Return null if not stated or pre-revenue."
        )
    )
    current_revenue: Optional[str] = Field(
        default=None,
        description=(
            "Current annual or monthly revenue. "
            "Example: '$250K ARR' or 'Pre-revenue'. Return null if not mentioned."
        )
    )
    burn_rate: Optional[str] = Field(
        default=None,
        description=(
            "Monthly cash burn. Example: '$40K/month'. Return null if not mentioned."
        )
    )
    runway: Optional[str] = Field(
        default=None,
        description=(
            "Remaining runway in months. Example: '18 months'. Return null if not mentioned."
        )
    )
