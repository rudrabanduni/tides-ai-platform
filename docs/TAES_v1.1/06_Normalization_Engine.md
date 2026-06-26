# 06 — Normalization Engine

> **Document:** TAES v1.1 / Normalization Engine
> **Classification:** Internal Technical Standard
> **Version:** 1.1.0
> **Status:** Active
> **Related Documents:** TAES v1.0 / 06_Sector_Normalization_Standard.md, TAES v1.1 / 05_Benchmarking_Framework.md

---

## Introduction

The TAES Normalization Engine defines the mathematical and logical framework that ensures startup evaluation scores are fair, context-sensitive, and sector-appropriate. It is the mechanism by which the platform avoids the fundamental error of applying a single universal standard to a universe of fundamentally different businesses.

Without normalisation, the following failures occur:
- A DeepTech startup at TRL 5 with no revenue scores poorly on Financial and Commercial pillars, not because it is failing, but because revenue is structurally premature for its domain.
- A SaaS startup with modest technology differentiation scores highly on Technology simply because it ships a working product quickly, not because it has built anything technically defensible.
- A Biotech startup in clinical trials receives a low score for slow growth, penalising it for the mandatory regulatory cycle that governs its entire industry.
- A SpaceTech startup with a ten-year commercialisation horizon is evaluated against one-year revenue targets appropriate only for consumer apps.

Normalisation does not change what is evaluated. It changes how the results are interpreted relative to what is appropriate for that startup at that stage in that sector.

This document defines the normalisation philosophy, the weight adjustment logic, the score adjustment logic, the confidence adjustment logic, bias mitigation principles, and fairness standards.

**Normalisation is not a bias. It is the removal of a structural bias.** The bias being removed is the implicit assumption that all startups should look the same at the same point in time.

---

## Section 1: Normalisation Philosophy

### 1.1 Core Principle

The normalisation engine operates on the principle of **contextual equivalence**: two startups are evaluated as equivalent when they are achieving what is structurally appropriate for their sector, stage, and geography — not when they produce identical metric outputs.

A biotech startup at TRL 4 that has completed Phase 1 clinical safety trials with peer-reviewed results is, in its sector context, as commercially advanced as a SaaS startup that has achieved $100,000 ARR. Both have demonstrated equivalent progression relative to sector norms. The Normalization Engine recognises this equivalence and reflects it in the scores.

### 1.2 What Normalisation Does and Does Not Do

| Normalisation Does | Normalisation Does Not |
|---|---|
| Adjust the interpretation of scores relative to sector, stage, and geography | Change the raw evaluation findings |
| Apply sector-specific evidence weight adjustments | Fabricate positive findings |
| Adjust pillar weights to reflect sector priorities | Remove negative findings |
| Apply timeline adjustments for long-cycle sectors | Excuse poor execution relative to sector norms |
| Apply CAPEX adjustments for capital-intensive industries | Create artificial score inflation |
| Adjust confidence thresholds based on typical evidence availability by sector | Override the evidence standard |

### 1.3 Normalisation Layers

The Normalization Engine applies three distinct layers:

**Layer 1 — Weight Normalisation:** Adjusts the relative importance of each scoring pillar based on sector and stage. Example: the IP pillar carries higher weight for DeepTech and Biotech than for a consumer app startup.

**Layer 2 — Score Interpretation Normalisation:** Adjusts the score thresholds that define "good" performance on each criterion based on what is realistic for the sector and stage. Example: the Financial pillar criterion for "revenue growth" applies different benchmarks for a pre-revenue Biotech than for a Series A SaaS.

**Layer 3 — Confidence Normalisation:** Adjusts the confidence scoring rules based on what evidence is typically available for a sector and stage. Example: in a regulated sector like MedTech, the absence of commercial revenue at TRL 5 should not reduce financial confidence — it is structurally expected.

---

## Section 2: Sector Normalisation Profiles

Each sector has a Normalisation Profile that defines Layer 1, Layer 2, and Layer 3 adjustments. The profiles below describe the normalisation logic for each sector. All weight adjustments are directional (Higher/Lower/Standard) — precise weight values are configurable and not hardcoded.

### 2.1 DeepTech (Hardware-Intensive, Non-Biotech)

**Sector characteristics:** Long development cycles, high capital requirements before commercialisation, technology differentiation is primary value driver, revenue premature until hardware is proven.

| Pillar | Weight Direction | Rationale |
|--------|-----------------|-----------|
| Technology | Higher | The entire value proposition rests on technical differentiation |
| IP | Higher | Hardware innovations require patent protection; unprotected hardware is easily copied |
| Founder | Higher | Domain expertise is irreplaceable in deep technical domains |
| Financial | Lower | Pre-revenue is structurally normal until TRL 7+ |
| Business Model | Lower | Business model clarity expected later in lifecycle |
| Market | Standard | Market must still be validated |

**Score Interpretation Adjustments:**
- Financial criterion "revenue": expected to be zero until TRL 7; score against fundraising quality instead
- Financial criterion "burn rate": high burn is acceptable if matched to development milestones
- Technology criterion "deployment evidence": expected in controlled environments (not consumer deployment) until TRL 7

**CAPEX Adjustment:** High capital expenditure on equipment, lab facilities, and manufacturing infrastructure is expected and should not reduce the Financial score when it is proportionate to the development stage and evidenced by budget plans.

**Confidence Adjustment:** Lower evidence availability is expected because hardware startups rarely have the document volume of SaaS companies. Confidence thresholds are adjusted downward by 15% before triggering a low-confidence flag.

---

### 2.2 Biotech

**Sector characteristics:** Regulatory approval is the primary development gateway, clinical trial timelines are legally mandated and not compressible, commercialisation may be 10+ years from founding, partnerships and licensing are common exit/revenue models.

| Pillar | Weight Direction | Rationale |
|--------|-----------------|-----------|
| Technology | Higher | Scientific validity of the therapeutic or biological approach is foundational |
| IP | Higher | Biotech companies live and die by patent protection and freedom to operate |
| Legal | Higher | Regulatory pathway clarity is existential |
| Financial | Standard | Fundraising discipline matters even without revenue |
| Business Model | Lower | Licensing and partnership models are structurally different; standard GTM expectations do not apply |
| Market | Standard | Market size and patient/customer population still must be validated |

**Score Interpretation Adjustments:**
- Financial criterion "revenue": not expected at TRL ≤ 6; evaluate grant success and institutional funding quality instead
- Product criterion "user adoption": not applicable pre-clinical; evaluate preclinical data quality instead
- Commercial criterion "customers": applies to licensing partners and clinical trial investigators, not consumers
- Risk criterion "regulatory risk": must always be present; the question is whether the startup has a credible regulatory strategy, not whether the risk is absent

**Timeline Adjustment:** Scoring expectations for "traction" and "commercial progress" are shifted forward by 3–5 years relative to standard. A Biotech startup at Year 3 is expected to have completed Phase 1 trials, not to have paying customers.

**Confidence Adjustment:** Confidence in TRL assessment is higher when peer-reviewed publications or regulatory pre-submission meeting records are available; these are sector-standard evidence. Absence of paying customers does not reduce Financial confidence.

---

### 2.3 MedTech

**Sector characteristics:** Regulatory approval required but cycle shorter than Biotech (12–48 months rather than 10+ years), clinical validation essential, hospital and clinic procurement cycles are long, reimbursement pathway is often as important as regulatory approval.

| Pillar | Weight Direction | Rationale |
|--------|-----------------|-----------|
| Technology | Higher | Clinical safety and efficacy are non-negotiable |
| Legal | Higher | CE mark, FDA 510(k) or PMA pathway clarity is critical |
| Market | Standard | Reimbursement pathway is part of market analysis |
| Financial | Standard | Revenue possible post-clearance but limited before |
| IP | Higher | Device patents and software patents both apply |
| Go-To-Market | Standard | Hospital procurement GTM is different but evaluatable |

**Score Interpretation Adjustments:**
- Revenue expected post-regulatory clearance only (CE/FDA)
- Pilot and early commercial sales to hospitals under research agreements are strong commercial evidence at pre-clearance stage
- Reimbursement code (CPT/DRGS in US, ASMR in France) status is evaluated as part of commercial readiness

---

### 2.4 SaaS / Enterprise Software

**Sector characteristics:** Fast deployment cycles, network effects possible, recurring revenue expected relatively early, unit economics are primary value indicator, customer churn is a critical metric.

| Pillar | Weight Direction | Rationale |
|--------|-----------------|-----------|
| Financial | Higher | MRR, churn, LTV:CAC are primary value indicators; expected earlier than other sectors |
| Business Model | Higher | Revenue model clarity and unit economics health are primary |
| Market | Standard | Market size still matters |
| Technology | Standard | Technical differentiation matters but is not always the primary moat |
| IP | Lower | Code copyright is baseline; strong IP moat is unusual and not expected |

**Score Interpretation Adjustments:**
- Revenue expected by MVP stage (not prototype)
- Customer churn below 5% monthly for SME SaaS, below 2% annual for Enterprise SaaS: strong indicator
- NPS above 50: strong product indicator
- Technology criterion for "deployment evidence" applies from MVP; working product in production is expected, not exceptional

**CAPEX Adjustment:** SaaS businesses should not have significant CAPEX. Large CAPEX expenditure is a red flag unless the SaaS product has an underlying hardware or infrastructure component.

---

### 2.5 AI / Machine Learning

**Sector characteristics:** Rapid capability expansion, data moats are primary defensibility, compute costs are significant, model performance benchmarks are evaluatable, commoditisation risk is high.

| Pillar | Weight Direction | Rationale |
|--------|-----------------|-----------|
| Technology | Higher | Model quality, data strategy, and architecture differentiation are primary |
| IP | Standard | Data licensing and model ownership are evaluated; traditional patents less applicable |
| Financial | Standard | Revenue expected but compute costs significantly affect margins |
| Competition | Higher | AI sector moves extremely fast; competitive moat erosion is a material risk |
| Market | Standard | Market validation required |

**Score Interpretation Adjustments:**
- Technology criterion: "proprietary training data" or "proprietary fine-tuning dataset" is strong evidence of defensibility
- Technology criterion: "built on a third-party foundation model" without proprietary layer scores as Q2 differentiation evidence
- Financial criterion: "gross margin" must account for inference compute costs; margins below 30% in AI SaaS are a warning sign
- Competition criterion: startup must demonstrate awareness of and response to the rapid pace of model capability improvement by competitors (including foundation model providers themselves entering the application layer)

---

### 2.6 ClimateTech / CleanTech

**Sector characteristics:** Long asset lifetimes, project-based revenue structures, regulatory incentives central to unit economics, government and institutional procurement dominant, impact measurement required.

| Pillar | Weight Direction | Rationale |
|--------|-----------------|-----------|
| ESG | Higher | The sector's core value proposition is environmental impact; this must be measurable |
| Market | Higher | Policy landscape and regulatory tailwinds are primary market drivers |
| Technology | Higher | Physical or chemistry-based innovation is often the core |
| Financial | Lower | Project finance structures are different from SaaS metrics |
| Business Model | Standard | Project-based, subscription, and licensing models all valid |

**Score Interpretation Adjustments:**
- Financial criterion: revenue from government grants, carbon credits, and energy certificates is legitimate revenue; evaluated differently from product sales
- Market criterion: regulatory tailwinds (e.g., net-zero mandates, renewable energy targets) are a primary market driver and must be included in market assessment
- ESG criterion: validated impact metrics (tonnes of CO2 avoided, litres of water saved, etc.) are primary evidence, not optional
- Revenue premature until first project deployment; evaluate project pipeline instead

**Timeline Adjustment:** Project development, permitting, and construction cycles mean commercial revenue may lag the product by 2–4 years even at TRL 7+.

---

### 2.7 SpaceTech

**Sector characteristics:** Extremely long development and commercialisation cycles, very high capital requirements, regulatory (launch licensing) mandatory, government contracts are often the primary revenue model, dual-use considerations common.

| Pillar | Weight Direction | Rationale |
|--------|-----------------|-----------|
| Technology | Higher | Technical capability is the primary differentiator |
| IP | Higher | Launch system, satellite, and antenna patents are defensible |
| Legal | Higher | Launch licensing, spectrum licensing, and export control are existential |
| Financial | Lower | Revenue 5–10 years after founding is structurally normal |
| Business Model | Lower | Government contracts and anchor customers are primary; standard GTM metrics do not apply |

**Score Interpretation Adjustments:**
- Revenue expected only post-first-launch; pre-launch stage is measured by technical progress and government/anchor customer engagement
- A government letter of intent or a space agency evaluation contract is strong commercial evidence
- Financial criterion: CAPEX normalised heavily upward; per-kilogram-to-orbit cost trajectories are relevant financial metrics

**Timeline Adjustment:** Scoring expectations for commercial traction shifted forward by 5–10 years relative to standard technology startups.

---

### 2.8 AgriTech

**Sector characteristics:** Highly seasonal business cycles, farmer adoption is slow and relationship-dependent, regulatory requirements for biologicals and chemicals, hardware and software both common, impact on food security is measurable.

| Pillar | Weight Direction | Rationale |
|--------|-----------------|-----------|
| Market | Higher | Farmer segment sizes, crop economics, and adoption curves are critical |
| Technology | Standard | Hardware (drones, sensors) and software (precision agriculture) both common |
| Go-To-Market | Higher | Farmer distribution channels are complex and relationship-intensive |
| ESG | Higher | Environmental impact of agriculture technology is measurable and material |
| Financial | Standard | Revenue possible but seasonal; annual rather than monthly metrics are appropriate |

**Score Interpretation Adjustments:**
- Revenue measured annually or seasonally, not monthly
- Customer acquisition cycles measured in seasons (3–12 months), not weeks
- Pilot evidence from named farming cooperatives or agribusinesses is strong commercial evidence
- Government and development bank partnerships are strong GTM evidence in developing market contexts

---

### 2.9 FinTech

**Sector characteristics:** Regulatory licensing is primary gate, data privacy obligations are highest in the sector, incumbent relationships are double-edged (partnership opportunity and competition threat), unit economics must reach profitability quickly post-licensing.

| Pillar | Weight Direction | Rationale |
|--------|-----------------|-----------|
| Legal | Higher | Regulatory licence (NBFC, payment aggregator, banking licence, etc.) is required for the core product in most segments |
| Financial | Higher | Revenue expected earlier than most sectors; unit economics central |
| Technology | Standard | Security and compliance architecture are technology requirements |
| Risk | Higher | Regulatory, financial, and fraud risk are all elevated in FinTech |
| Market | Standard | Market must still be validated |

**Score Interpretation Adjustments:**
- Operating without required regulatory licence is a Critical Risk flag, not a minor concern
- Financial criterion: expected to have revenue at MVP stage in most FinTech subsectors
- Risk criterion: AML, KYC, and fraud prevention frameworks must be present as part of operational evidence

---

### 2.10 Manufacturing / Industry 4.0

**Sector characteristics:** High CAPEX, long production lead times, customer validation requires physical installation, supply chain complexity is a primary operational risk, enterprise procurement cycles are long.

| Pillar | Weight Direction | Rationale |
|--------|-----------------|-----------|
| Technology | Higher | Manufacturing innovation must be technically defensible |
| Operations | Higher | Manufacturing capability and supply chain are primary operational risks |
| Financial | Standard | CAPEX normalised; operating efficiency metrics relevant |
| IP | Higher | Process patents and manufacturing innovations are primary moats |
| Go-To-Market | Standard | Enterprise B2B sales with long cycles |

**Score Interpretation Adjustments:**
- Revenue expected but from enterprise customers with long procurement cycles; pipeline with named prospects is acceptable early-stage evidence
- CAPEX up to 40–60% of total funding is normal; this should not reduce the Financial score
- Technology criterion: manufacturing process IP, not just product IP, is a primary evidence category

---

### 2.11 Consumer Tech and D2C

**Sector characteristics:** Fast adoption cycles, brand differentiation matters, viral growth possible, unit economics must reach profitability quickly, high customer acquisition cost risk, low IP moat typical.

| Pillar | Weight Direction | Rationale |
|--------|-----------------|-----------|
| Market | Higher | Consumer market sizing and behavioural validation are critical |
| Financial | Higher | Revenue and unit economics expected early; LTV:CAC is primary |
| Product | Higher | User experience and retention are primary value indicators |
| IP | Lower | Consumer brand IP is trademark-based; not a primary technology moat |
| Technology | Lower | Technology is usually enabling, not differentiating |
| Go-To-Market | Higher | Consumer acquisition channels, CAC, and retention are primary |

**Score Interpretation Adjustments:**
- Revenue expected at MVP stage
- Monthly retention rate >40% at 30 days: strong product evidence
- NPS > 50: strong customer satisfaction evidence
- LTV:CAC ratio < 2 at Series A: Financial red flag

---

## Section 3: Stage Normalisation

In addition to sector normalisation, the engine applies lifecycle stage adjustments. These are applied on top of the sector profile.

### 3.1 Stage-Based Evidence Expectations

| Stage | Primary Evidence Focus | Pillar Weight Emphasis |
|-------|----------------------|----------------------|
| Idea | Problem articulation, founder quality, initial research | Founder, Market |
| Research | Evidence of technical feasibility, problem validation | Founder, Technology, Market |
| Prototype | Technical proof of concept, early design | Technology, Product |
| MVP | Functioning product, first users or customers | Product, Market, Financial |
| Pilot | Controlled deployment evidence, feedback loop | Product, Commercial, Financial |
| Early Revenue | Revenue quality, unit economics, growth rate | Financial, Business Model |
| Product Market Fit | Retention, NPS, organic growth | Product, Market, Financial |
| Growth | Growth rate, scalability, CAC efficiency | Financial, Operations, Scalability |
| Scale | Margin improvement, international expansion, market share | Financial, Market, Operations |

### 3.2 Revenue Normalisation by Stage

The single most common source of unfair scoring is applying revenue expectations to pre-revenue stages. The following rules govern revenue interpretation:

- **Idea, Research, Prototype:** Revenue is not expected. The financial score at these stages is evaluated entirely against fundraising quality, financial discipline, and financial planning rigour.
- **MVP, Pilot:** Revenue is emerging. The financial score accounts for early transaction volume, pricing validation, and unit economics groundwork. Zero revenue is acceptable but pipeline with named prospects is expected.
- **Early Revenue, PMF:** Revenue quality, not just revenue volume, is the primary metric. Revenue from a single customer is a concentration risk; revenue from ten or more customers demonstrates demand breadth.
- **Growth, Scale:** Revenue growth rate, margin trajectory, and scalability of revenue model are the primary financial metrics.

---

## Section 4: Bias Mitigation

### 4.1 Identified Structural Biases

The Normalization Engine is designed to mitigate the following structural biases identified through the design of the platform:

| Bias | Description | Mitigation |
|------|-------------|-----------|
| **Revenue Bias** | Scoring systems that reward early revenue penalise capital-intensive and regulated sectors | Stage + sector normalisation of financial pillar |
| **Speed Bias** | Scoring systems that reward fast execution penalise sectors with mandatory long cycles | Timeline adjustment by sector |
| **Documentation Bias** | Scoring systems that reward rich documentation penalise hardware and science sectors that generate fewer business documents | Confidence threshold adjustment by sector |
| **English-Language Bias** | Evidence submitted in non-English languages is harder to evaluate and may be underweighted | Evidence quality rules do not penalise non-English evidence; translation is required before evaluation |
| **Geography Bias** | Startups from emerging markets may have smaller addressable markets locally, lower benchmark revenue, and less access to audited accounts | Benchmark peer groups are filtered by geography; revenue benchmarks use regional norms |
| **Team Size Bias** | Small founding teams score lower on Team Completeness by default | Team completeness is evaluated relative to stage and sector, not absolute headcount |
| **Prestige Bias** | Founders from elite universities or prominent companies score higher regardless of startup-specific evidence | Founder evaluation requires startup-specific evidence, not credential-based scoring |

### 4.2 Bias Audit Process

The platform must maintain a bias audit mechanism that:
- Tracks average pillar scores by sector and identifies statistically significant sector disparities
- Flags criteria where one sector consistently scores 20%+ lower than others without an evidence-based justification
- Reports bias audit results to the evaluation committee on a quarterly basis
- Triggers a normalisation profile review when a systematic bias is detected

---

## Section 5: Confidence Normalisation

The engine also adjusts confidence scoring based on sector-typical evidence availability. Some sectors structurally produce more evidence than others.

### 5.1 Confidence Baseline by Sector

| Sector | Evidence Availability | Confidence Adjustment |
|--------|----------------------|-----------------------|
| SaaS | High (MRR, churn, DAU, customer list, financial model) | No adjustment |
| Consumer / D2C | High (app analytics, transaction records, NPS) | No adjustment |
| FinTech | Medium-High (regulated disclosures, customer data) | No adjustment |
| AI / ML | Medium (technical demos, model benchmarks, data descriptions) | +5% confidence threshold relief |
| AgriTech | Medium (seasonal data, pilot reports, farmer testimonials) | +5% confidence threshold relief |
| DeepTech | Low-Medium (technical documentation heavy, commercial evidence light) | +10% confidence threshold relief |
| SpaceTech | Low (pre-commercial, government contracts, technical reports) | +15% confidence threshold relief |
| Biotech | Low-Medium (publications, trial reports, regulatory correspondence) | +10% confidence threshold relief |
| MedTech | Medium (clinical data, regulatory filings, hospital evaluations) | +5% confidence threshold relief |
| ClimateTech | Medium (project data, environmental impact reports, pilot installations) | +5% confidence threshold relief |
| Defence | Low (limited public disclosure, classified elements) | +15% confidence threshold relief |
| Manufacturing | Medium (production data, quality certifications, supply chain records) | No adjustment |

The Confidence Adjustment means: before triggering a "low confidence" flag, the engine allows the specified amount of headroom for sectors where evidence is structurally scarcer. This is not a license to score confidently from absent evidence — it is a recognition that the absence of a specific evidence type is normal and expected in some sectors.

---

## Section 6: Normalisation Governance

### 6.1 Normalisation Profile Versioning
Each sector Normalisation Profile carries a version number. When a profile is updated, all future evaluations use the new profile. Historical evaluations are not retroactively updated; they retain the profile version active at the time of evaluation.

### 6.2 Profile Review Cycle
Each Normalisation Profile must be reviewed annually by the Evaluation Committee. Reviews consider:
- Bias audit results from the previous year
- Changes in sector maturity expectations (e.g., if the AI sector matures such that revenue is expected earlier)
- Feedback from mentors and committee members with sector expertise
- Comparison against external sector benchmarks and industry norms

### 6.3 Custom Profiles
For organisations deploying TIDES for a specific sector or geography, custom Normalisation Profiles may be created by the platform administrator. Custom profiles must be documented, versioned, and applied consistently across all evaluations in that deployment context. Custom profiles must not override the core bias mitigation rules defined in Section 4.

### 6.4 Transparency
Every evaluation report must declare:
- Which Normalisation Profile version was applied
- Which sectors and stages were detected and used for normalisation
- A brief statement explaining what adjustments were made and why

This ensures that both the startup and the human reviewer understand how the score was contextualised.

---

*This document governs all normalisation decisions within the TIDES platform. Any scoring system, AI agent, or human reviewer applying a universal standard without normalisation is operating outside the TAES standard.*
