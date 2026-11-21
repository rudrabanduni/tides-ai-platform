"""Generates the synthetic CleanPower Systems pitch deck used by the offline demonstration.

Every company, person, number and contact detail in this document is FICTIONAL. Each slide uses
"Field Label: value" lines so the offline MockAIGateway can extract values directly from the
document text (and the evidence locator can cite the exact line and page).

Usage:
    .venv\\Scripts\\python.exe scripts\\generate_synthetic_deck.py [output.pdf]
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = PROJECT_ROOT / "demo_fixtures" / "cleanpower_systems_pitch_deck.pdf"

BANNER = "SYNTHETIC DEMONSTRATION DOCUMENT - FICTIONAL COMPANY - NOT A REAL APPLICATION"

SLIDES: list[tuple[str, list[str]]] = [
    ("CleanPower Systems - Incubation Application Deck", [
        "Company Name: CleanPower Systems Pvt Ltd",
        "Tagline: Modular hydrogen fuel-cell backup power for telecom towers and edge data centres",
        "Sector: CleanTech",
        "Stage: Seed",
        "Geography: Roorkee, Uttarakhand, India",
        "Application Date: 2026-11-20",
    ]),
    ("Problem", [
        "Problem Statement: Grid outages force telecom towers and edge data centres onto diesel generators",
        "Who Is Affected: Telecom tower operators and edge data-centre operators in North India",
        "Current Workarounds: Diesel gensets with fuel theft, noise, high emissions and 30-second start delays",
        "Evidence Of Problem: Survey of 42 tower sites found an average of 6.5 outage hours per day",
        "Why Problem Persists: Batteries lack multi-hour autonomy and earlier fuel cells cost over INR 3 lakh per kW",
    ]),
    ("Solution & Product", [
        "Solution: Containerised 10 kW PEM fuel-cell units with remote monitoring and swappable hydrogen cylinders",
        "Feature 1 Feature: Cold start in under 10 seconds",
        "Feature 1 Benefit: No interruption for critical radio and compute loads",
        "Feature 2 Feature: Remote telemetry and predictive maintenance",
        "Feature 2 Benefit: Fewer site visits for operators",
        "Unique Value Proposition: Zero-emission backup at diesel-equivalent cost per kWh within three years",
    ]),
    ("Technology & Prototype", [
        "Current TRL: 5",
        "TRL Justification: 10 kW prototype validated for 1,200 hours in a relevant field environment",
        "Prototype Stage: Field-tested pre-commercial prototype",
        "Technology: Low-platinum PEM stack with in-house power electronics and controller firmware",
        "Technical Validation Results: 1,200 field hours at 52% electrical efficiency at the Haridwar test site",
    ]),
    ("Market Opportunity", [
        "Market Size: INR 9,800 crore Indian backup power market for telecom and edge data centres",
        "SAM: INR 2,100 crore for sites in North India with more than 4 outage hours per day",
        "SOM 3 5 Year: INR 85 crore within five years",
        "Market CAGR: 14%",
        "CAGR Source: Applicant estimate based on public industry reports (not independently verified)",
        "Key Market Drivers: Diesel phase-out targets; 5G densification; data-centre growth in Tier-2 cities",
    ]),
    ("Competition", [
        "Competitor 1 Name: Diesel genset OEMs",
        "Competitor 1 Approach: Diesel internal-combustion backup",
        "Competitor 1 Startup Advantage: Zero emissions and lower fuel logistics",
        "Competitor 2 Name: Lithium battery backup integrators",
        "Competitor 2 Approach: Lithium-ion battery banks",
        "Competitor 2 Startup Advantage: Multi-hour autonomy without oversized battery banks",
        "Sustainable Competitive Advantage: In-house low-platinum stack and controller firmware",
    ]),
    ("Founders & Team", [
        "Founder 1 Name: Dr. Arjun Sharma",
        "Founder 1 Role: Co-Founder & CEO",
        "Founder 1 Education Degree: PhD Electrochemical Engineering",
        "Founder 1 Relevant Experience: 14 years in electrochemical energy systems",
        "Founder 2 Name: Priya Mehta",
        "Founder 2 Role: Co-Founder & CTO",
        "Founder 2 Education Degree: M.Tech Power Electronics",
        "Founder 2 Relevant Experience: 9 years designing power conversion systems",
        "Team: Two full-time founders and three engineers",
        "Critical Skill Gaps: Enterprise sales; hydrogen safety certification",
        "Advisor 1 Name: Prof. K. Rao",
        "Advisor 1 Role: Faculty technical advisor",
    ]),
    ("Business Model & Commercialisation", [
        "Business Model: Power-as-a-service contracts plus outright hardware sales",
        "Revenue Model: Monthly service fee per site with hydrogen supply included",
        "Pricing Strategy Unit: INR 38,000 per site per month for a 10 kW unit",
        "Customer Acquisition Channels: Direct sales to tower companies; EPC partners",
        "Expected Gross Margin: 31% in year one rising to 44% at scale",
        "Current Users: 3 pilot sites",
        "Paying Customers: 0",
        "Current Revenue: INR 0",
        "Pilot 1 Partner Name: Fictional TowerCo North",
        "Pilot 1 Agreement Type: Letter of intent",
        "Pilot 1 Is Signed: No",
    ]),
    ("Innovation, IP & Impact", [
        "Proprietary Technology Moat: Low-platinum catalyst coating process developed in-house",
        "Patent 1 Title: Low-platinum catalyst coating for PEM electrodes",
        "Patent 1 Status: Provisional application filed (applicant-reported, not verified)",
        "Patent 1 Jurisdiction: India",
        "Primary Impact: Displacing diesel generation at telecom sites",
        "SDG 1 SDG Number: 7",
        "SDG 1 SDG Name: Affordable and Clean Energy",
        "Impact Metric 1 Metric Name: Diesel displaced (litres per year)",
        "Impact Metric 1 Target 3 Year: 1,500,000",
    ]),
    ("Financial Projections", [
        "Three Year Revenue Year 1: INR 1.2 crore",
        "Three Year Revenue Year 2: INR 6.5 crore",
        "Three Year Revenue Year 3: INR 21 crore",
        "Three Year Gross Margin Year 1: 31%",
        "Three Year Gross Margin Year 2: 38%",
        "Three Year Gross Margin Year 3: 44%",
        "Break Even Timing: Month 30",
        "Financial Assumptions: Hydrogen at INR 320 per kg; 85% site uptime billing",
        "Funding Raised: INR 25 lakh grant",
        "Current Monthly Operating Costs: INR 6 lakh",
        "Funding Ask: INR 2 crore seed round",
    ]),
    ("Incubation Support Requested", [
        "Lab Facilities Requirements: Hydrogen-safe test bay; environmental chamber",
        "Mentorship Expertise Needed: Hydrogen safety certification; enterprise sales",
        "Industry Connections Needed: Tower companies; industrial gas suppliers",
        "Legal IP Support Needed: Complete specification for the provisional patent",
        "Market Access Pilot Support Needed: Campus substation trial site",
        "Six Quarter Product Roadmap Q1: Second-generation 10 kW stack",
        "Six Quarter Product Roadmap Q2: Safety certification testing",
        "Six Quarter Market Roadmap Q1: Convert letter of intent to paid pilot",
        "Six Quarter Market Roadmap Q2: Five commercial sites",
    ]),
    ("Contact & Declaration (fictional)", [
        "Contact Info Representative Name: Dr. Arjun Sharma",
        "Contact Info Email: founders@cleanpower.example",
        "Contact Info Website: https://cleanpower.example",
        "Applicant Declaration Is Signed: Yes",
        "Applicant Declaration Signatory Name: Dr. Arjun Sharma",
        "Applicant Declaration Declaration Date: 2026-11-20",
    ]),
]


def build(out_path: Path = DEFAULT_OUT) -> Path:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.pdfgen import canvas

    out_path.parent.mkdir(parents=True, exist_ok=True)
    w, h = landscape(A4)
    c = canvas.Canvas(str(out_path), pagesize=(w, h))
    c.setTitle("CleanPower Systems - Synthetic Demonstration Pitch Deck")
    c.setAuthor("TIDES-AI offline demonstration fixture")
    c.setSubject(BANNER)
    for idx, (title, lines) in enumerate(SLIDES, start=1):
        c.setFillColor(colors.HexColor("#14284B"))
        c.rect(0, h - 70, w, 70, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 22)
        c.drawString(40, h - 45, title)
        c.setFillColor(colors.HexColor("#B45309"))
        c.setFont("Helvetica-Bold", 9)
        c.drawString(40, h - 88, BANNER)
        c.setFillColor(colors.HexColor("#1F2937"))
        c.setFont("Helvetica", 12)
        y = h - 120
        for line in lines:
            c.drawString(50, y, line)
            y -= 24
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.HexColor("#6B7280"))
        c.drawRightString(w - 30, 20, f"Slide {idx} of {len(SLIDES)}")
        c.showPage()
    c.save()
    return out_path


if __name__ == "__main__":
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    print(build(target))
