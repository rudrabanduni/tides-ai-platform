> **Document:** TAES v1.1 / Benchmarking Framework
> **Classification:** Internal Technical Standard
> **Version:** 1.1.0
> **Status:** Ratified
> **Maintained By:** TIDES Evaluation Standards Committee
> **Last Reviewed:** 2026-06-24
> **Next Scheduled Review:** 2027-01-01
> **Supersedes:** TAES v1.0 / Benchmarking Framework

---

# 05 — Benchmarking Framework

## Table of Contents

1. [Introduction](#introduction)
2. [Section 1: Benchmark Dimensions](#section-1-benchmark-dimensions)
3. [Section 2: Peer Selection Methodology](#section-2-peer-selection-methodology)
4. [Section 3: Similarity Scoring](#section-3-similarity-scoring)
5. [Section 4: Competitor Comparison](#section-4-competitor-comparison)
6. [Section 5: Market Percentile](#section-5-market-percentile)
7. [Section 6: Expected Maturity by Dimension](#section-6-expected-maturity-by-dimension)
8. [Section 7: Expected Funding](#section-7-expected-funding)
9. [Section 8: Expected Team Size](#section-8-expected-team-size)
10. [Section 9: Expected Valuation](#section-9-expected-valuation)
11. [Section 10: Benchmark Confidence](#section-10-benchmark-confidence)
12. [Benchmark Governance](#benchmark-governance)
13. [Benchmark Data Sources](#benchmark-data-sources)
14. [Anonymisation](#anonymisation)

---

## Introduction

### What Benchmarking Means in Startup Evaluation

Benchmarking, as defined within TAES, is the act of placing a startup's observed characteristics within a reference frame of comparable entities. It is emphatically **not** ranking. Ranking orders all startups along a single linear dimension, implying that one is objectively better than another without regard to context. Benchmarking does the opposite: it asks whether a startup is performing appropriately, given what similar startups in similar circumstances typically achieve.

A startup operating in Sub-Saharan Africa at Seed stage with a TRL of 4 and three months of revenue is not well-served by comparison against a Silicon Valley Series B SaaS company with 18 months of growth metrics. Both may have identical raw TAES scores on a particular pillar; but the meaning of that score — what it signals about the startup's actual condition, risk profile, and developmental trajectory — differs fundamentally. Benchmarking provides the interpretive layer that makes that distinction legible.

In practice, benchmarking within TAES operates as a contextualisation mechanism. After evaluation scores are computed across all five pillars (Team & Founders, Technology & IP, Market & Business Model, Execution & Traction, and Ethical Readiness), those scores are situated within a curated reference population — the peer group — to determine whether the startup's performance is typical, exceptional, or deficient relative to comparable entities at a comparable stage of development. This contextualisation is surfaced in evaluation reports as percentile positions, maturity gap flags, and funding credibility assessments.

Benchmarking also carries an epistemic function: it makes explicit what we do not know. When a peer group is too small, when data on comparable startups is stale, or when a startup's profile is sufficiently unusual that no clean peer set can be constructed, the framework does not suppress that uncertainty. It surfaces it, assigns a benchmark confidence score, and adjusts the weight given to comparative conclusions accordingly.

### Why Benchmarking Is Essential to Fair Scoring

A score without context is meaningless. This principle is foundational to the design of TAES.

Consider a Team & Founders pillar score of 62 out of 100. Is this good? Is this a warning sign? The answer is entirely dependent on what 62 means within the space of startups like this one. If the median team score for Seed-stage DeepTech startups in South Asia is 58, then 62 represents above-median performance — a sign of relative strength. If the median is 74, then 62 is a significant shortfall — a flag warranting deeper scrutiny. Without the benchmark, both situations would appear identical on the face of the report.

Benchmarking addresses five specific fairness risks that arise when scores are interpreted in isolation:

**1. Regional disparity.** Access to capital, talent density, infrastructure maturity, and regulatory environments vary dramatically by geography. A startup in Lagos or Dhaka operates in a structurally different environment than one in London or San Francisco. Applying universal absolute thresholds without regional normalisation systematically disadvantages startups in emerging ecosystems, regardless of their actual quality.

**2. Stage disparity.** Pre-seed startups are expected to have thin execution evidence, early-stage technology, and no revenue. Applying the same traction thresholds used for Series A startups to a pre-seed company produces false negatives — it flags as weak something that is developmentally normal.

**3. Sector disparity.** A biotech startup at TRL 5 is in a completely different operational reality than a SaaS startup at TRL 5. Hardware development timelines, regulatory pathways, and capital intensity are sector-specific. Benchmarks that ignore sector produce distorted comparisons.

**4. Model disparity.** B2C and B2B companies operate on different sales cycles, retention curves, and growth economics. A monthly active user count that would be exceptional for an enterprise platform startup might be unremarkable for a consumer app.

**5. Recency disparity.** Macro conditions — interest rate environments, venture capital availability, geopolitical disruption — shift what is achievable at a given stage. Benchmarks calibrated only on historical data from boom periods may flag healthy startups operating in a constrained environment as underperforming.

By situating every score within a relevant reference population, TAES ensures that evaluation conclusions reflect actual performance relative to genuine comparators — not against an abstract, universal ideal that ignores the structural conditions shaping startup outcomes.

### Absolute Scoring and Relative Scoring: How TAES Uses Both

TAES employs a dual-layer scoring architecture. The first layer is **absolute scoring**: evaluators and analytical agents score startups on defined rubrics that produce numerical pillar scores on a 0–100 scale. These scores are internally consistent and comparable across all evaluations within TAES. They are grounded in evidence-linked criteria, and a score of 75 on the Technology pillar means the same thing in terms of the criteria satisfied regardless of which startup earns it.

The second layer is **relative scoring**: the benchmark engine takes those absolute scores and situates them within the peer group to produce percentile positions, maturity gap assessments, and comparative flags. These relative outputs are specific to the peer group and carry the confidence level of the underlying benchmark.

The two layers serve different purposes and address different audiences:

| Layer | Output Type | Interpretation | Primary Audience |
|---|---|---|---|
| Absolute Scoring | Pillar scores (0–100) | What the startup has demonstrated against defined criteria | Internal evaluators, standards reviewers |
| Relative Scoring | Percentile, gap flags, benchmark alerts | How the startup compares against comparable peers | Investors, grant bodies, institutional decision-makers |

TAES does not replace absolute scores with relative scores, nor does it blend them into a single metric. The two are maintained separately and presented in combination. An investor reading a TAES report sees both: the absolute score (grounding), and the percentile within the peer group (contextualisation).

Critically, benchmarking in TAES **adjusts the interpretation of a score, not the score itself**. A startup's absolute pillar score is never modified by benchmark outputs. What changes is how that score is narrated — whether it is characterised as above-peer, at-peer, or below-peer — and whether the report flags it as a signal requiring further attention.

### How Benchmarks Are Constructed, Maintained, and Versioned

Benchmarks within TAES are constructed from a combination of internal evaluation history and curated external data (see Section: Benchmark Data Sources). The construction process follows a defined lifecycle:

**1. Population definition.** A benchmark population is defined by one or more benchmark dimensions (see Section 1). For a benchmark to be constructed, the population must contain a minimum number of valid, recent records (see: Minimum Dataset Size, below).

**2. Metric distribution mapping.** For each population, the distribution of pillar scores, team sizes, funding amounts, revenue levels, and valuation claims across the population is mapped. Distributions are characterised by their median, interquartile range (IQR), and the positions of the 10th and 90th percentiles.

**3. Temporal weighting.** Records in the benchmark population are weighted by recency. Records from the most recent 18 months receive full weight. Records from 18–36 months prior receive reduced weight. Records older than 36 months are included only when the population is otherwise too small to be statistically valid, and their presence is flagged as a benchmark confidence reducer.

**4. Validation.** Each constructed benchmark undergoes internal validation before activation. Validation checks include: confirming that the population size meets minimums, verifying that no single entity constitutes more than 10% of the population (to prevent outlier domination), and checking that distribution parameters are stable (i.e., not driven by a single data spike).

**5. Versioning.** Benchmarks are versioned at the framework level (e.g., TAES v1.1) and at the data level (e.g., Benchmark Dataset v2026-Q2). When the underlying data is refreshed — through new evaluations, updated external sources, or periodic audits — a new data version is issued. When the benchmark methodology itself changes, the framework version is incremented. Reports always record both the framework version and the benchmark dataset version used at the time of evaluation, ensuring reproducibility.

**6. Deprecation.** A benchmark is deprecated when its underlying population falls below the minimum size due to data aging, or when the sector/model it covers has been restructured into more granular classifications. Deprecated benchmarks are flagged in reports. Evaluations conducted under a deprecated benchmark are not retroactively rescored; they are annotated.

### Minimum Dataset Size for Statistical Reliability

A benchmark is considered **statistically reliable** when the following minimum conditions are simultaneously met:

| Condition | Minimum Requirement |
|---|---|
| Total peer records in population | 30 valid, non-duplicated records |
| Records from within the last 18 months | At least 15 of the 30 total |
| Maximum share held by any single entity | No more than 10% of population (≤3 records for n=30) |
| Pillar score coverage | At least 80% of records have scores on all five pillars |
| Geographic dispersion (where applicable) | At least 3 distinct originating countries or regions |

When these conditions are not fully met, the benchmark is assigned a **reduced confidence tier** (see Section 10). The benchmark may still be used, but its conclusions are presented with explicit uncertainty, and decision-makers are advised to weight comparative outputs accordingly.

For sparse benchmark populations (fewer than 15 valid records), TAES applies **composite peer group construction** (see Section 2), which relaxes one or more secondary dimension requirements to expand the population. This expansion is always disclosed in the report.

### How Benchmarks Are Applied

Benchmarks are applied at the report generation stage, after all pillar scores have been finalised. The application is interpretive, not computational: benchmarks do not alter raw scores. Instead, they perform three functions:

**1. Percentile positioning.** The startup's absolute score on each pillar is mapped to a percentile within its peer group distribution. This percentile is reported alongside the absolute score.

**2. Gap flagging.** The startup's scores, team size, funding amount, and revenue level are compared against expected values for its benchmark dimensions. Significant deviations — either above or below expectations — are surfaced as contextual flags in the report narrative.

**3. Confidence annotation.** The report records the benchmark confidence score, the peer group size, the benchmark dataset version, and any dimension relaxations that were applied during peer group construction. This allows readers to calibrate how much weight to place on comparative conclusions.

Benchmarks are never applied silently or without disclosure. Every comparative conclusion in a TAES report is traceable to a specific benchmark population, a specific dataset version, and a specific confidence level.

---

## Section 1: Benchmark Dimensions

Benchmark dimensions are the axes along which peer groups are defined. Each dimension classifies a startup into one of a defined set of categories. The combination of dimension values for a given startup defines the multi-dimensional space in which its peers are sought.

There are 12 benchmark dimensions in TAES v1.1. Each is described below in full.

---

### Dimension 1: Sector

**What the dimension captures:**
Sector captures the primary domain in which the startup operates. It is the most consequential single dimension for benchmarking because it determines capital intensity norms, technology timelines, regulatory context, team composition expectations, and market size assumptions. A startup's sector shapes nearly every other aspect of its evaluation profile.

**How startups are classified:**
Startups are assigned a primary sector and, where applicable, a secondary sector. The primary sector is used for peer group construction. The secondary sector is used in composite peer group expansion when the primary sector population is insufficient. Classification is based on the startup's core technology and revenue-generating activity, not its stated industry label. A company building AI tools for drug discovery is classified as DeepTech or Biotech (whichever better characterises the core value chain), not simply as AI.

Defined sector categories:

| Sector Label | Classification Criteria |
|---|---|
| AI | Core product is an AI/ML model, inference system, or AI-native platform |
| SaaS | Software product delivered as a subscription service; no hardware dependency |
| DeepTech | Foundational technology development requiring 5+ year R&D cycles (materials science, quantum, robotics, photonics) |
| Biotech | Biological process engineering, synthetic biology, genetic technologies |
| MedTech | Medical devices, diagnostics, health IT products subject to medical regulation |
| AgriTech | Agricultural technology including precision farming, agri-supply chain, crop science |
| ClimateTech | Technologies addressing climate change mitigation, adaptation, or resilience |
| FinTech | Financial products, payment infrastructure, lending, insurance technology |
| SpaceTech | Satellite technology, launch systems, space data, in-orbit services |
| Defence | Dual-use or defence-specific technology, systems, and services |
| Manufacturing | Industrial process technology, automation, smart manufacturing |
| Consumer | Consumer-facing products and services not categorised above |
| D2C | Direct-to-consumer brand or product companies |

**Data needed to benchmark along this dimension:**
- Confirmed sector classification from evaluation intake form
- Technology stack characterisation from Technology pillar assessment
- Revenue source characterisation from Business Model pillar assessment

**Minimum peer group size:** 20 validated records within the primary sector classification.

**Confidence expression:** When fewer than 20 records are available, confidence is reduced to Tier 2 (Moderate). When fewer than 10 records are available, confidence is Tier 3 (Low). When fewer than 5 records exist, the sector benchmark is suspended and a composite peer group is constructed.

---

### Dimension 2: Country

**What the dimension captures:**
Country captures the startup's country of primary operation and legal registration. It is distinct from the startup's target market. A startup registered in Kenya targeting East African markets is benchmarked against other Kenya-registered startups, not against all East African startups (which would fall under the Region dimension). Country-level benchmarking reflects the specific regulatory, talent, capital, and infrastructure environment in which the startup is operating day-to-day.

**How startups are classified:**
Startups are classified by their country of primary legal incorporation AND their country of primary operational presence (where the founding team and core operations are located). When these differ — for example, a Delaware-incorporated company with operations in India — both are recorded, and the country of primary operational presence takes precedence for benchmarking.

**Data needed to benchmark along this dimension:**
- Legal registration country (from incorporation documents submitted at intake)
- Primary operational country (from team location data and physical presence disclosures)
- Investor domicile data (secondary indicator used for validation only)

**Minimum peer group size:** 15 validated records for the country to constitute a standalone country-level benchmark. Countries with fewer than 15 records are folded into the regional benchmark (Dimension 3).

**Confidence expression:** Country-level benchmarks carry High confidence when n ≥ 30, Moderate confidence when 15 ≤ n < 30, and are replaced by regional benchmarks when n < 15. The substitution is always disclosed.

---

### Dimension 3: Region

**What the dimension captures:**
Region captures the macro-geographic cluster to which the startup belongs. Regional benchmarking is the fallback when country-level peer groups are too small, and the primary frame when comparing startups across similar-maturity ecosystems that span political boundaries. It also captures the structural similarities in ecosystem development, capital availability, and regulatory philosophy that tend to cluster by region rather than by individual country.

**How startups are classified:**
Startups are assigned to one of the following macro-regions based on their country of primary operational presence:

| Region Label | Countries Included |
|---|---|
| South Asia | India, Pakistan, Bangladesh, Sri Lanka, Nepal, Bhutan, Maldives |
| Southeast Asia | Indonesia, Vietnam, Thailand, Philippines, Malaysia, Singapore, Myanmar, Cambodia, Laos, Brunei, Timor-Leste |
| East Asia | China, Japan, South Korea, Taiwan, Mongolia |
| Central Asia | Kazakhstan, Uzbekistan, Kyrgyzstan, Tajikistan, Turkmenistan, Azerbaijan, Georgia, Armenia |
| Middle East & North Africa | UAE, Saudi Arabia, Egypt, Jordan, Israel, Qatar, Bahrain, Kuwait, Oman, Lebanon, Morocco, Tunisia, Algeria |
| Sub-Saharan Africa | Nigeria, Kenya, South Africa, Ghana, Ethiopia, Rwanda, Tanzania, Uganda, Senegal, and all other sub-Saharan nations |
| Western Europe | UK, Germany, France, Netherlands, Sweden, Switzerland, Denmark, Norway, Finland, Austria, Belgium, Ireland, and Western European nations |
| Central & Eastern Europe | Poland, Czech Republic, Romania, Hungary, Bulgaria, Slovakia, Ukraine, Baltic states, and CEE nations |
| North America | United States, Canada |
| Latin America & Caribbean | Brazil, Mexico, Colombia, Argentina, Chile, Peru, and all LAC nations |
| Oceania & Pacific | Australia, New Zealand, Pacific island nations |
| Global / Distributed | Startups with no single country constituting >60% of operational presence |

**Data needed to benchmark along this dimension:**
- Country of primary operational presence (see Dimension 2)
- Mapping to region via the defined country-to-region table above

**Minimum peer group size:** 25 validated records for a regional benchmark to be considered statistically reliable.

**Confidence expression:** Regional benchmarks carry full confidence when n ≥ 50. Moderate confidence when 25 ≤ n < 50. Low confidence when n < 25, in which case a global benchmark is used with explicit disclosure.

---

### Dimension 4: Funding Stage

**What the dimension captures:**
Funding stage captures the point in the startup's capital formation journey at which the evaluation is conducted. It is one of the most operationally significant dimensions because it determines what level of evidence, traction, team scale, and product maturity can reasonably be expected. Expectations are calibrated entirely differently for a pre-seed startup than for one that has raised a Series B.

**How startups are classified:**

| Stage Label | Classification Criteria |
|---|---|
| Pre-seed | No institutional investment raised; may have angel investment ≤ USD 250,000 |
| Seed | Institutional or angel funding of USD 250,001 – USD 3,000,000 raised |
| Series A | Institutional funding of USD 3,000,001 – USD 15,000,000 raised |
| Series B+ | Institutional funding exceeding USD 15,000,000 raised |
| Grant-only | No equity investment; operating exclusively on grant funding regardless of grant amount |
| Bootstrapped | No external investment of any kind; self-funded from founder capital or revenue |

When a startup has raised across multiple rounds, the stage corresponds to its most recent and highest completed funding event. Startups that have received convertible instruments but no completed priced round are classified at the stage corresponding to the notional amount committed.

**Data needed to benchmark along this dimension:**
- Confirmed funding history from founder disclosure and, where available, cross-referenced against public venture databases
- Type of each funding instrument (equity, SAFE, convertible note, grant, loan)
- Valuation cap or post-money valuation from most recent round (for stage calibration and valuation benchmarking)

**Minimum peer group size:** 20 validated records per stage classification.

**Confidence expression:** Stage is one of the highest-quality dimensions because funding records are relatively reliable and well-documented. Stage benchmarks typically achieve High confidence. Confidence drops to Moderate only when combined with highly specific sector or country classifications that reduce the overlapping population.

---

### Dimension 5: Technology Readiness Level (TRL)

**What the dimension captures:**
TRL captures the maturity of the startup's core technology. The TAES TRL scale follows the convention established by NASA and adopted by the European Commission, ranging from TRL 1 (basic principles observed) to TRL 9 (actual system proven in operational environment). TRL benchmarking ensures that technology maturity expectations are calibrated against what is achievable and typical at the startup's current development stage, not against an abstract ideal.

**How startups are classified:**
TRL is assessed during the Technology & IP pillar evaluation. The Technology evaluation agent assigns a TRL level based on evidence review. Classification is grouped into three benchmark bands:

| TRL Band | TRL Levels Included | Typical Characteristics |
|---|---|---|
| Early-Stage (TRL 1–3) | TRL 1, 2, 3 | Basic research, concept formulation, proof-of-concept in laboratory conditions |
| Development-Stage (TRL 4–6) | TRL 4, 5, 6 | Technology validated in lab, demonstrated in relevant environment, prototype demonstrated |
| Deployment-Ready (TRL 7–9) | TRL 7, 8, 9 | System prototype demonstrated in operational environment, system complete and qualified, actual system proven |

**Data needed to benchmark along this dimension:**
- Technology evaluation evidence package (patents, prototypes, publications, pilot results, deployment records)
- TRL assessment from Technology pillar evaluator
- Sector context (because TRL norms differ significantly by sector: a SaaS product at TRL 8 is typical for a Series A company, whereas a biotech product at TRL 8 may represent 15+ years of development)

**Minimum peer group size:** 15 validated records per TRL band. Because TRL band is almost always combined with sector and stage in peer group construction, the effective minimum is the intersection of those populations.

**Confidence expression:** TRL assignment carries an inherent confidence level derived from the quality and completeness of evidence reviewed. Low-evidence TRL assignments (where the evaluator estimated TRL with limited documentation) reduce the dimension's confidence contribution.

---

### Dimension 6: Revenue Stage

**What the dimension captures:**
Revenue stage captures the startup's position on the revenue development curve. It distinguishes startups that have not yet generated meaningful commercial revenue from those in early monetisation, and from those that have achieved growth-scale revenue. Revenue stage is distinct from funding stage: a startup can be Seed-funded and generating significant ARR, or Series A-funded and pre-revenue (common in deep technology development tracks).

**How startups are classified:**

| Revenue Stage Label | Classification Criteria |
|---|---|
| Pre-revenue | No recurring commercial revenue; may have grant income, pilot payments, or one-time consulting fees ≤ USD 10,000 |
| Early Revenue | ARR or equivalent annualised recurring revenue between USD 10,001 and USD 100,000 |
| Growth Revenue | ARR exceeding USD 100,000 |

Revenue figures are based on verified disclosure from founder-submitted financial data. Where verified financials are unavailable, revenue stage is estimated from payment evidence, bank statement summaries, or platform transaction records and assigned a disclosure quality flag.

**Data needed to benchmark along this dimension:**
- ARR or MRR from most recent confirmed reporting period
- Revenue model type (subscription, transaction, licensing, services) for ARR equivalence calculation
- Disclosure quality indicator (audited, management accounts, founder assertion)

**Minimum peer group size:** 20 validated records per revenue stage band.

**Confidence expression:** Revenue stage confidence is moderated by disclosure quality. When more than 40% of the peer population's revenue stage classification is based on unverified founder assertions, the revenue dimension confidence is capped at Moderate.

---

### Dimension 7: Company Age

**What the dimension captures:**
Company age captures how long the startup has been in existence as a legal entity. It is used to calibrate expectations for team development, technology maturity, market penetration, and operational systems against what is achievable within a given time frame, independent of capital raised. A startup that is three months old cannot reasonably be expected to have the same operational depth as one that is three years old.

**How startups are classified:**

| Age Band | Range | Benchmark Expectation Context |
|---|---|---|
| Nascent | 0–1 year | Idea validation, team formation, initial product development; evidence base is necessarily thin |
| Early | 1–3 years | Initial product launch, first customers, team growth; execution evidence beginning to accumulate |
| Established | 3–6 years | Product maturity, revenue scaling, team institutionalisation; significant execution evidence expected |
| Mature | 6+ years | Full operational maturity, multiple product iterations, defensible market position |

Company age is measured from the date of legal incorporation, not from the date of the idea or founding team formation.

**Data needed to benchmark along this dimension:**
- Legal incorporation date (from registration certificates submitted at intake)
- Operational commencement date (secondary indicator; used where incorporation date and operational launch are significantly separated)

**Minimum peer group size:** 15 validated records per age band (typically exceeded in practice, as age band is a broad category).

**Confidence expression:** Age is a high-reliability dimension as it is factual and document-verified. Confidence is reduced only when age is combined with highly specific sector/country/stage combinations that reduce the peer population.

---

### Dimension 8: Business Model

**What the dimension captures:**
Business model captures the structural mechanism by which the startup generates revenue and delivers value. Different business models have fundamentally different economic characteristics — margin profiles, sales cycles, customer acquisition costs, and retention curves — that make cross-model comparisons misleading. A marketplace's GMV growth tells a different story than a SaaS company's ARR growth, even at identical nominal values.

**How startups are classified:**

| Business Model Label | Classification Criteria |
|---|---|
| B2B SaaS | Software subscription sold to businesses; recurring revenue; per-seat, per-usage, or flat-fee pricing |
| B2C | Product or service sold directly to individual consumers |
| B2B2C | Product sold to businesses, which deliver it to their end consumers |
| Marketplace | Platform connecting buyers and sellers; revenue via commission, listing fees, or take-rate |
| Hardware | Physical product as the primary revenue vehicle; may include software components |
| Platform | Infrastructure or developer-facing platform; revenue via API access, licensing, or usage |
| Services | Professional services, consulting, implementation; typically time-and-materials billing |

When a startup operates across multiple models, the primary model (generating >50% of revenue or intended to generate >50% of revenue within 12 months) is used for benchmarking. Secondary model is recorded for composite peer group construction.

**Data needed to benchmark along this dimension:**
- Revenue model description from intake questionnaire
- Revenue breakdown by source from financial disclosure
- Go-to-market strategy from Business Model pillar assessment

**Minimum peer group size:** 20 validated records per business model classification.

**Confidence expression:** Business model classification confidence is high when revenue data is available, and Moderate when classification is based solely on stated model without revenue verification.

---

### Dimension 9: Technology Type

**What the dimension captures:**
Technology type captures the fundamental nature of the startup's core technology. This dimension is distinct from sector: it characterises what the technology physically or computationally does, rather than the market it serves. It is used primarily to benchmark TRL progression expectations and team composition norms, since hardware development timelines, regulatory pathways, and technical risk profiles differ fundamentally from purely software-based approaches.

**How startups are classified:**

| Technology Type | Classification Criteria |
|---|---|
| Software-only | Core product is entirely software; no physical hardware component in the value chain |
| Hardware + Software | Core product involves both physical hardware development and software systems |
| Biology / Chemistry | Core technology involves living organisms, biological processes, chemical synthesis, or molecular engineering |
| Physical Systems | Core technology involves mechanical, structural, optical, or energy systems without biological or chemical components |

**Data needed to benchmark along this dimension:**
- Technology stack characterisation from Technology pillar evaluation
- Bill of materials or technology description (for hardware classification)
- Patent or IP filing classifications (supporting indicator)

**Minimum peer group size:** 15 validated records per technology type classification.

**Confidence expression:** Technology type is a moderate-reliability dimension. The primary risk of misclassification arises with AI-enabled hardware products or bioinformatics tools, where the technology type boundary is genuinely ambiguous. Ambiguous cases are flagged and both candidate types are noted in the peer group construction record.

---

### Dimension 10: Customer Segment

**What the dimension captures:**
Customer segment captures the type of buyer the startup primarily serves. Customer segment determines sales cycle length, contract size expectations, support requirements, and the relevant metrics for traction benchmarking. A startup serving government procurement bodies operates in a fundamentally different commercial environment than one selling consumer subscriptions, even if both have the same ARR.

**How startups are classified:**

| Customer Segment | Classification Criteria |
|---|---|
| Enterprise | Large organisations (typically >500 employees or >USD 50M revenue); typically multi-month sales cycles and contract-led commercial relationships |
| SME | Small and medium enterprises (typically 10–499 employees); shorter sales cycles, mix of contract and self-serve |
| Consumer | Individual end-users purchasing for personal use |
| Government | National, regional, or local government bodies; procurement-driven; regulatory and compliance-heavy |
| Research | Academic institutions, research laboratories, NGOs; grant-funded procurement; long evaluation cycles |

**Data needed to benchmark along this dimension:**
- Customer profile from Business Model pillar evaluation
- Customer list summary (tier, not individual names) from founder disclosure
- Average contract value and sales cycle length (supporting indicators)

**Minimum peer group size:** 15 validated records per customer segment classification.

**Confidence expression:** Customer segment classification is reliable when customer data is disclosed. Confidence drops to Moderate when classification is based solely on founder-stated target market without supporting customer evidence.

---

### Dimension 11: Geography of Operation

**What the dimension captures:**
Geography of operation captures the market footprint of the startup — not where it is based, but how many markets it is actively serving customers in. This dimension captures operational ambition and complexity, and is distinct from the country and region dimensions which describe origin. A startup serving customers in five countries faces different operational challenges, regulatory compliance burdens, and scaling requirements than one focused on a single domestic market.

**How startups are classified:**

| Geography Classification | Classification Criteria |
|---|---|
| Single-market | All customers in one country; no active market expansion underway |
| Multi-market | Customers in 2–5 countries; active cross-border operations |
| Global-from-day-1 | Customers in 6+ countries, or explicit global go-to-market from launch; no single market >60% of revenue |

**Data needed to benchmark along this dimension:**
- Customer location data from founder disclosure
- Revenue by geography (where available)
- Go-to-market strategy from Business Model evaluation

**Minimum peer group size:** 15 validated records per geography classification.

**Confidence expression:** Confidence is Moderate-to-High when customer distribution is verified. Self-reported global reach without customer evidence is flagged as a low-confidence classification.

---

### Dimension 12: Team Size

**What the dimension captures:**
Team size captures the number of full-time equivalent (FTE) people working in the startup at the time of evaluation. It is used to benchmark team completeness expectations, operational capacity, and the plausibility of claimed execution milestones. A team of two cannot credibly claim to have simultaneously built a commercial product, completed enterprise sales, and obtained a patent within 18 months without extraordinary clarification.

**How startups are classified:**

| Team Size Band | FTE Range | Benchmark Context |
|---|---|---|
| Solo / Duo | 1–2 FTE (founders only) | Concept and early build; very limited execution bandwidth |
| Small | 3–5 FTE | Initial team formation; first hires added to founding team |
| Growing | 6–20 FTE | Early scaling; functional specialisation beginning |
| Scaled | 21+ FTE | Organisation formation; structured teams; management layer emerging |

FTE count includes paid full-time employees and paid full-time contractors. Part-time contributors (advisors, interns, fractional roles) are excluded from FTE count but noted separately.

**Data needed to benchmark along this dimension:**
- Team roster from founder disclosure
- LinkedIn cross-reference (automated, for validation)
- Payroll record summary (where available, as a verification indicator)

**Minimum peer group size:** 15 validated records per team size band.

**Confidence expression:** Team size is a high-reliability dimension when roster is disclosed. Reliability degrades when team size is stated without supporting verification, particularly for larger team claims.

---

## Section 2: Peer Selection Methodology

### Overview

Peer selection is the process by which the benchmark engine identifies the set of startups most comparable to the startup being evaluated. The peer group is not selected manually; it is constructed algorithmically from the benchmark database by matching on the 12 benchmark dimensions defined in Section 1, applying a tiered matching logic that distinguishes between essential matches and desirable matches.

Peer selection is designed to be:
- **Reproducible:** The same startup profile, evaluated at the same point in time against the same dataset version, will always produce the same peer group.
- **Transparent:** Every peer group construction decision — including any dimension relaxations applied — is recorded and disclosed in the evaluation report.
- **Conservative:** When peer group quality is uncertain, the framework errs toward disclosing uncertainty rather than constructing spurious comparisons.

### Primary Selection Criteria (Must Match)

Primary criteria are mandatory. A startup must match a peer on all primary criteria for that peer to qualify for inclusion in the peer group. Failure to match on any single primary criterion disqualifies the peer, regardless of how closely it matches on secondary criteria.

The primary selection criteria are:

| Dimension | Matching Rule |
|---|---|
| Sector (Dimension 1) | Must match primary sector classification exactly |
| Funding Stage (Dimension 4) | Must match within one adjacent stage (e.g., a Seed startup can match Seed or Pre-Seed peers, but not Series A) |
| TRL Band (Dimension 5) | Must match TRL band exactly (Early, Development, or Deployment-Ready) |
| Revenue Stage (Dimension 6) | Must match revenue stage exactly |

These four dimensions form the non-negotiable foundation of peer comparability. Without alignment on sector, stage, TRL, and revenue, the comparison is structurally misleading regardless of other similarities.

### Secondary Selection Criteria (Should Match)

Secondary criteria are desirable but not mandatory. Peers are scored on how well they match secondary criteria, and that score influences their weight within the peer group (see Section 3: Similarity Scoring). Failing to match on secondary criteria does not disqualify a peer, but it does reduce that peer's contribution weight.

The secondary selection criteria are:

| Dimension | Weight in Secondary Matching |
|---|---|
| Region (Dimension 3) | High |
| Business Model (Dimension 8) | High |
| Technology Type (Dimension 9) | Medium |
| Customer Segment (Dimension 10) | Medium |
| Company Age (Dimension 7) | Medium |
| Team Size (Dimension 12) | Low |
| Country (Dimension 2) | Low (used for regional tie-breaking) |
| Geography of Operation (Dimension 11) | Low |

### Minimum Peer Group Size

The minimum valid peer group size for benchmark application is **15 matched peers**. This minimum is calibrated to ensure that no single outlier entity dominates the distribution, and that the interquartile range can be meaningfully computed.

**When the peer group falls below 15:**
The benchmark engine applies the following escalation protocol in sequence:

1. **Relax one secondary criterion** (beginning with the lowest-weight secondary dimension) and re-query the population. If n ≥ 15, proceed with relaxed peer group and record the relaxation.
2. **Relax a second secondary criterion** if step 1 does not reach the minimum. Record both relaxations.
3. **Expand the adjacent funding stage window** from one adjacent stage to two adjacent stages (e.g., a Seed startup now includes both Pre-seed and Series A peers). Record the expansion.
4. **Replace country-level benchmarking with region-level benchmarking** if n is still below 15 after steps 1–3.
5. **Apply composite peer group construction** (see below) if n is still below 15.
6. **Suspend the benchmark** if n < 5 after all relaxation steps. The evaluation report includes the note: "Benchmarking not available for this startup profile due to insufficient peer data. Scores are reported as absolute values only."

Each relaxation step reduces the benchmark confidence tier by one level. Multiple relaxations compound: a peer group constructed after steps 1, 2, and 3 will carry Tier 3 (Low) confidence.

### Composite Peer Group Construction

Composite peer group construction is applied when strict multi-dimensional matching yields insufficient peers. In this approach, the requirement for matching on a primary sector classification is partially relaxed: the startup is matched against peers in **adjacent or thematically related sectors** rather than its primary sector only.

Adjacent sector pairings used in TAES v1.1:

| Primary Sector | Adjacent Sectors for Composite Construction |
|---|---|
| AI | SaaS, DeepTech |
| Biotech | MedTech, DeepTech |
| MedTech | Biotech, ClimateTech (for diagnostics/environmental health) |
| AgriTech | ClimateTech, Biotech |
| ClimateTech | AgriTech, DeepTech, Manufacturing |
| SpaceTech | Defence, DeepTech |
| Defence | SpaceTech, DeepTech, Manufacturing |
| FinTech | SaaS, Consumer |
| D2C | Consumer |

Composite peer group construction is always disclosed in the report with the statement: *"Peer group includes [n] startups from [primary sector] and [n] startups from [adjacent sector(s)] due to insufficient primary-sector peer data."*

### Peer Group Confidence

Peer group confidence is a separate attribute from benchmark confidence (see Section 10). Peer group confidence specifically measures how well-matched the selected peers are to the target startup. It is computed from:

- The proportion of peers matching all primary criteria (should be 100%; any relaxation reduces this)
- The median secondary similarity score across all selected peers (see Section 3)
- The recency profile of the peer group (proportion of peers evaluated within the last 18 months)
- Whether composite construction was applied and how many sector relaxations were made

Peer group confidence is expressed on a three-tier scale:

| Tier | Label | Meaning |
|---|---|---|
| Tier 1 | High | Peer group is well-matched on all primary criteria and majority of secondary criteria; n ≥ 25; ≥60% of peers evaluated within 18 months |
| Tier 2 | Moderate | One or more secondary relaxations applied, or 15 ≤ n < 25, or composite construction applied with one adjacent sector |
| Tier 3 | Low | Multiple relaxations applied, or n < 15 (accepted via exception), or composite construction with multiple adjacent sectors, or >50% of peers evaluated more than 18 months ago |

---

## Section 3: Similarity Scoring

### Overview

Once the peer group is constructed, each peer in the group is assigned a **similarity score** relative to the startup being evaluated. Similarity scoring serves two purposes: it determines whether a peer is sufficiently similar to be a valid contributor to the benchmark, and it determines the weight each peer contributes to the distribution calculations.

Similarity scoring does not affect which peers are initially selected — that is determined by the primary and secondary matching criteria. Rather, it determines the influence weight of each peer within the final peer group calculations.

### The Similarity Scoring Logic

Similarity between two startups is computed as a weighted composite across the 12 benchmark dimensions. For each dimension, a dimension-level similarity value is determined based on how closely the two startups match within that dimension. The similarity value for each dimension is binary (exact match = full credit), ordinal (adjacent match = partial credit, non-adjacent = no credit), or continuous (for dimensions with numeric ranges, similarity decays as the numeric distance increases).

**Binary dimensions** (match is either exact or absent):
- Sector (primary): exact match = full credit; adjacent sector = partial credit (used only in composite peer groups); no match = disqualified
- Technology Type: exact match = full credit; adjacent type = partial credit; no match = no credit

**Ordinal dimensions** (credit is awarded based on proximity within the ordinal scale):
- Funding Stage: same stage = full credit; one stage adjacent = partial credit; two stages distant = no credit
- TRL Band: same band = full credit; one band adjacent = partial credit; two bands distant = no credit
- Revenue Stage: same stage = full credit; adjacent stage = partial credit
- Company Age: same band = full credit; adjacent band = partial credit; two or more bands distant = no credit

**Proximity dimensions** (credit decays smoothly with distance):
- Team Size: credit peaks at exact same band and decays as band distance increases; within one band = partial credit; two or more bands = minimal credit
- Country / Region: same country = full credit; same region = high credit; different region = low credit; different macro-region = minimal credit

**Alignment dimensions** (credit based on categorical match):
- Business Model: exact match = full credit; closely related model = partial credit (e.g., B2B SaaS vs. Platform); unrelated model = no credit
- Customer Segment: exact match = full credit; adjacent segment = partial credit
- Geography of Operation: exact match = full credit; adjacent category = partial credit

### Dimension Weighting in Similarity

The 12 dimensions do not contribute equally to the overall similarity score. The weighting reflects their relative importance in determining genuine comparability:

| Dimension | Similarity Weight |
|---|---|
| Sector (primary) | 25% |
| Funding Stage | 20% |
| Revenue Stage | 15% |
| TRL Band | 10% |
| Business Model | 10% |
| Region | 8% |
| Customer Segment | 5% |
| Technology Type | 3% |
| Company Age | 2% |
| Team Size | 1% |
| Country | 1% (tie-breaking only) |
| Geography of Operation | 0% (recorded, not weighted; used for report flags only) |

**Total weights sum to 100%.** The overall similarity score for a peer is the weighted average of its dimension-level similarity values, expressed as a percentage.

### Similarity Score Thresholds

Not every peer selected by the primary/secondary matching criteria will be a valid contributor to the benchmark. Similarity score thresholds determine whether a peer's contribution is accepted, accepted at reduced weight, or excluded from distribution calculations:

| Similarity Score | Contribution Status |
|---|---|
| ≥ 80% | Full contributor — peer is included at full weight |
| 60% – 79% | Partial contributor — peer is included at 50% weight |
| 40% – 59% | Marginal contributor — peer is included at 25% weight (only when peer group n < 20) |
| < 40% | Excluded — peer is not included in distribution calculations; may be disclosed as "extended comparison" in report |

The effective peer group size (n_effective) used in benchmark confidence calculations accounts for contribution weights. A peer at 50% weight counts as 0.5 toward n_effective. This prevents artificially inflated peer group sizes when many marginal contributors are present.

### Similarity Score Decay Over Time

A peer's similarity score is subject to temporal decay to reflect the fact that data about a peer becomes less relevant as it ages. The decay mechanism operates as follows:

- **0–12 months** since peer evaluation: No decay. Similarity score applies at full value.
- **12–24 months** since peer evaluation: Similarity score is reduced by 15%.
- **24–36 months** since peer evaluation: Similarity score is reduced by 35%.
- **36–48 months** since peer evaluation: Similarity score is reduced by 55%. Peer may still be included if peer group would otherwise fall below minimum, but inclusion is flagged.
- **>48 months** since peer evaluation: Peer is excluded from all distribution calculations. May be referenced in contextual narrative only, with explicit age disclosure.

The rationale for temporal decay is that startup ecosystems evolve. The funding environment, technology expectations, and market benchmarks that characterised peers evaluated three or four years ago may not reflect the current landscape. Recent comparators carry more predictive relevance.

---

## Section 4: Competitor Comparison

### Direct Competitors vs. Benchmark Peers

Benchmark peers and direct competitors are distinct categories within TAES, and they serve different analytical functions. Understanding this distinction is essential for correct interpretation of evaluation reports.

**Benchmark peers** are startups that are comparable in terms of their development profile — sector, stage, model, region, and maturity. They are not necessarily competing for the same customers or operating in the same market niche. They serve as a reference class: what does a startup like this typically look like?

**Direct competitors** are companies — which may include established incumbents, not just startups — that are competing for the same customers with similar or overlapping products in the same or adjacent market. Direct competitors are identified through competitive intelligence analysis, not through the benchmark database's dimension-matching logic.

The difference has immediate practical implications:

| Attribute | Benchmark Peers | Direct Competitors |
|---|---|---|
| Selection basis | Structural similarity (stage, sector, model) | Market overlap (product, customer, geography) |
| Typical company type | Other startups | Startups, scale-ups, established companies |
| Function in report | Contextualise scores and expectations | Assess competitive position and differentiation |
| Source of data | Internal evaluation database | Competitive intelligence, public market data |
| Anonymisation | Fully anonymised | Named (where publicly available) |
| Confidence dependency | Benchmark confidence score | Competitive intelligence data quality |

### Competitor Comparison Dimensions

The competition analysis component of TAES evaluates a startup against its direct competitors across five structured dimensions:

**1. Product Dimension**
Compares the feature set, user experience quality, deployment maturity, and value proposition of the startup's product against competitor products. Assessment covers: product parity (does the startup's product reach feature parity with competitors?), differentiation (does it offer capabilities that competitors do not?), and product maturity (is the product at a comparable stage of development for comparable investment?).

**2. Technology Dimension**
Compares the underlying technology architecture, IP position, and technical differentiation of the startup against competitors. Assessment covers: proprietary technology claims vs. competitor technology claims, patent positions, technology generation (is the startup using comparable, older, or newer technology approaches than competitors?), and technical moat plausibility.

**3. Market Dimension**
Compares market positioning, target segment clarity, pricing strategy, and go-to-market approach. Assessment covers: market segment overlap (are the startup and competitor targeting the same buyers?), pricing competitiveness, distribution channel differentiation, and market share evidence (where available).

**4. Team Dimension**
Compares founding team credentials, domain expertise depth, and operational experience against known competitor leadership. Assessment covers: relevant domain experience, prior venture experience, technical depth of founding team, and advisory network quality relative to competitors.

**5. Funding Dimension**
Compares the funding trajectory, investor quality, and capital efficiency of the startup against competitors. Assessment covers: total capital raised vs. competitor capital raised, investor brand and network value, funding-to-milestone efficiency (how much capital was required to reach comparable milestones?), and burn rate sustainability relative to competitive positioning.

### How the Competition Analysis Agent Uses Benchmarking Data

The competition analysis agent draws on the benchmarking framework in three specific ways:

**1. Calibration of expectations.** Before characterising a startup as "behind competitors," the competition analysis agent checks the benchmark data to confirm whether the gap is actually unusual for a startup at this stage. A startup that is ahead of peers but behind its largest competitor may be in a stronger position than one that is behind both peers and competitors.

**2. Peer-adjusted differentiation assessment.** The agent compares the startup's differentiation claims against what comparable peers in the benchmark database have claimed. This prevents the report from treating as unique a differentiation claim that is, in fact, standard practice for startups of this type.

**3. Competitive landscape benchmarking.** Where multiple competitors are identified and evaluated, the agent places the target startup's scores (on product, technology, and team dimensions) within the distribution of competitor scores. This produces a within-competition percentile that is separate from and complementary to the peer group percentile.

### Presenting Competitor Comparison in the Report

Competitor comparison results are presented in the Competitive Landscape section of the TAES evaluation report. The presentation follows a structured format:

**a. Competitor identification table:** Names, stages, founding dates, funding raised, and primary markets of identified direct competitors. Limited to publicly available information; inferred or unverified competitor data is clearly labelled.

**b. Comparative dimension matrix:** A structured table comparing the startup against up to five identified competitors across the five competitor comparison dimensions. Each cell contains a qualitative assessment (Ahead / At Parity / Behind) and a brief evidence-grounded rationale.

**c. Within-competition percentile:** Where multiple competitor evaluation records exist in the TAES database, the startup's position within the competitive distribution is reported with appropriate confidence annotation.

**d. Differentiation summary:** A narrative summary of the startup's key differentiators and competitive risks, grounded in the dimensional comparison and calibrated against the peer benchmark.

**e. Competitive risk flags:** Explicit flags for high-priority competitive risks — such as a well-funded competitor with a shorter time-to-market, or a technology-superior competitor entering the same customer segment.

---

## Section 5: Market Percentile

### What a Market Percentile Means in TAES

A market percentile within TAES expresses where a startup's score on a given pillar ranks within the distribution of pillar scores across its peer group. A startup in the 75th percentile on the Technology pillar has a Technology score equal to or higher than 75% of the startups in its peer group. It does not mean the startup is in the top 25% of all startups evaluated by TAES — only the top 25% of comparable peers.

This distinction is operationally important. Market percentiles are context-specific, not universal. They answer the question: "Among startups that look like this one, how does this startup perform?" — not "Among all startups, how does this startup perform?"

Market percentiles are computed separately for each pillar, not for the composite TAES score. This is intentional: aggregating into a composite percentile obscures meaningful variation across pillars. A startup in the 90th percentile on Technology and the 30th percentile on Execution represents a very different investment thesis than one at the 60th percentile across all pillars.

### Converting Pillar Scores to Percentiles

For each pillar, the peer group distribution is characterised by the scores of all valid peer group members, weighted by their contribution status (full, partial, or marginal) and temporal similarity decay factor. The target startup's pillar score is then placed within this weighted distribution to determine its percentile rank.

The conversion process:

1. Collect all valid peer pillar scores for the dimension (e.g., Team & Founders pillar scores across the peer group).
2. Apply temporal decay weights and contribution weights to each peer's score.
3. Rank the weighted distribution from lowest to highest.
4. Determine the percentile at which the target startup's score falls within the weighted distribution.
5. Report the percentile, rounded to the nearest whole number, alongside the peer group n_effective.

When the weighted distribution contains fewer than 15 effective peers, the percentile is reported with a low-confidence annotation. Percentiles computed from n_effective < 10 are flagged as indicative only and are not used as decision-determinative comparisons.

### Score Bands and Percentile Ranges

TAES reports communicate percentile positions using five standard score bands. These bands apply uniformly across all five pillars:

| Score Band Label | Percentile Range | Interpretation |
|---|---|---|
| Outstanding | 91st percentile and above (top 10%) | Startup demonstrates significantly above-peer performance on this pillar; represents a comparative strength |
| Strong | 76th – 90th percentile (top 25% excluding top 10%) | Startup performs above the majority of peers; represents a moderate comparative advantage |
| Peer-Median | 41st – 75th percentile | Startup performs at or near the expected level for comparable peers; neither a flag nor a distinction |
| Developing | 26th – 40th percentile | Startup performs below the majority of peers; warrants attention and may indicate an addressable gap |
| Below Peer | 25th percentile and below (bottom 25%) | Startup performs significantly below comparable peers; represents a material comparative weakness requiring specific analysis |

The bottom 10% (10th percentile and below) within the Below Peer band is further flagged in reports as **"Materially Below Peer"** to draw particular attention to severe underperformance relative to the comparison population.

### How Percentiles Are Communicated in Reports

Percentiles are presented in TAES evaluation reports in three complementary forms:

**1. Pillar percentile summary table.** A table listing each pillar, the startup's absolute score, its peer group percentile, and its score band label. This table appears in the Executive Summary section of the report.

**2. Percentile narrative.** For each pillar, a one-to-two paragraph narrative contextualising the percentile position: what it means, what evidence drove it, and — for below-peer positions — what the primary contributing factors are.

**3. Comparative flags.** Score bands of Developing or Below Peer trigger a structured flag in the report: a labelled box identifying the pillar, the percentile, the primary gap areas, and a directional recommendation for how the gap might be addressed.

Percentile positions are always presented alongside:
- The peer group n_effective
- The benchmark dataset version
- The benchmark confidence tier
- Any dimension relaxations applied

This context is mandatory. Percentiles presented without this accompanying information are considered incomplete TAES outputs.

### Limitations and Caveats of Percentile Reporting with Small Peer Groups

Percentile reporting is subject to significant interpretation risk when peer group sizes are small. TAES v1.1 enforces the following mandatory caveats in all reports where peer group limitations apply:

**When n_effective < 20:**
The report includes the statement: *"Percentile estimates are based on a limited peer group (n_effective = [value]). Small peer group sizes increase sensitivity to individual outliers and reduce the stability of percentile boundaries. These percentiles should be interpreted as directional indicators, not precise comparative measures."*

**When n_effective < 10:**
The report includes the statement: *"Peer group size is below the minimum recommended for reliable percentile computation. Percentile positions are provided for orientation only and should not be used as a primary basis for evaluation conclusions. Absolute pillar scores are the preferred basis for comparison in this case."*

**When composite peer group construction was applied:**
The report includes the statement: *"This peer group includes startups from sectors adjacent to the target startup's primary sector. Cross-sector percentile comparisons carry inherent limitations due to structural differences between sectors. Percentile positions for this evaluation should be interpreted with reference to the sector composition of the peer group."*

**When >30% of the peer group's evaluation data is more than 24 months old:**
The report includes the statement: *"A significant portion of peer group data is from evaluations conducted more than 24 months prior to this evaluation. Market conditions, sector norms, and stage expectations may have shifted during this period. Percentile positions may not fully reflect current peer standards."*

---

## Section 6: Expected Maturity by Dimension

### Overview

The concept of expected maturity within TAES is derived from the observation that startups at comparable stages of development tend to cluster around predictable levels of maturity across five dimensions: team formation, technology development, market engagement, operational systems, and ethical governance. The expected maturity framework maps these typical maturity levels against benchmark dimensions — primarily funding stage, company age, and sector — to create a calibrated set of reference expectations.

Expected maturity is not a mandate. It is a description of what the peer population typically looks like at this point. Startups significantly ahead of expected maturity are flagged as positive outliers. Those significantly behind are flagged for scrutiny — not punished, but examined more closely to understand the cause of the gap.

### Maturity Expectations by Funding Stage

The following table defines typical expected maturity levels across the five evaluation pillars at each funding stage. Values represent median expected scores within the TAES peer database, not theoretical ideals.

| Pillar | Pre-Seed | Seed | Series A | Series B+ |
|---|---|---|---|---|
| Team & Founders | 45–60 | 55–68 | 65–78 | 72–85 |
| Technology & IP | 35–52 | 50–66 | 62–76 | 70–84 |
| Market & Business Model | 38–55 | 52–67 | 63–77 | 72–86 |
| Execution & Traction | 25–42 | 42–60 | 60–75 | 72–88 |
| Ethical Readiness | 30–50 | 45–62 | 60–75 | 68–82 |

These ranges represent the interquartile range (25th to 75th percentile) of pillar scores observed across the benchmark population at each stage. They are updated quarterly as new evaluations are added to the database.

### Maturity Expectations by Company Age

| Pillar | 0–1 Year | 1–3 Years | 3–6 Years | 6+ Years |
|---|---|---|---|---|
| Team & Founders | 40–58 | 52–68 | 62–78 | 70–86 |
| Technology & IP | 30–50 | 48–65 | 60–76 | 68–83 |
| Market & Business Model | 35–52 | 50–65 | 62–76 | 70–84 |
| Execution & Traction | 20–40 | 40–60 | 58–74 | 70–86 |
| Ethical Readiness | 28–48 | 42–60 | 58–73 | 66–80 |

### Maturity Expectations by Sector

Sector-specific maturity expectations reflect the different development tempos inherent to each sector. The following notes capture the key sector-specific calibrations applied in TAES v1.1:

| Sector | Key Maturity Calibration Notes |
|---|---|
| AI | Technology maturity (TRL) advances faster than in hardware sectors; traction evidence expected earlier |
| SaaS | High execution maturity expected at Seed; slow execution growth is a significant flag |
| DeepTech | Lower TRL expectations at Seed and Series A; longer runway to deployment-ready technology accepted |
| Biotech | TRL advancement is slow by nature; regulatory milestone completion is the primary maturity indicator |
| MedTech | Clinical evidence requirements slow product maturity timelines; CE/FDA pathway progress is key indicator |
| AgriTech | Seasonal revenue patterns must be normalised; pilot-to-deployment timelines vary by crop cycle |
| ClimateTech | Subsidy and policy dependency affects revenue timing; technology maturity may precede market maturity |
| FinTech | Regulatory licensing milestones are key maturity indicators; revenue maturity expected earlier than in DeepTech |
| SpaceTech | Very long technology development cycles; TRL 4–5 at Series A is typical, not a flag |
| Defence | Classification and procurement constraints limit traction evidence; alternative maturity indicators applied |
| Manufacturing | Physical systems development timelines accepted; pilot manufacturing evidence weighted heavily |
| Consumer / D2C | Rapid traction expected; slow consumer adoption at Seed is a yellow flag |

### Flagging Startups Ahead of or Behind Expected Maturity

The benchmark engine compares each startup's pillar scores against the expected maturity ranges for its primary benchmark dimensions (stage and company age being the dominant drivers). Two types of flags are generated:

**Ahead-of-Maturity Flag:**
Triggered when a startup's pillar score exceeds the 90th percentile expected score for its stage and age. This flag is positive but prompts a validation check: exceptionally high scores are cross-checked against evidence quality ratings from pillar evaluators. If a high score is supported by strong evidence, the flag is recorded as a validated positive outlier. If the high score is driven by weak or unverified evidence, an evidence quality warning is added.

**Behind-Maturity Flag:**
Triggered when a startup's pillar score falls below the 25th percentile expected score for its stage and age. This flag is a warning indicator. The report narrative includes an analysis of the most likely contributing factors and whether the gap is explainable by legitimate sector-specific factors (e.g., a Biotech startup at Series A with low traction scores is expected; a SaaS startup at Series A with the same traction scores is a material concern).

### The Maturity Gap Concept

The **Maturity Gap** is the quantified difference between a startup's observed pillar score and the median expected pillar score for startups at the same funding stage and company age, within the same sector. It is expressed as a signed value: positive gaps indicate the startup is ahead of median maturity; negative gaps indicate it is behind.

The Maturity Gap is computed for each pillar independently. The composite Maturity Gap profile — a set of five signed gap values, one per pillar — provides a diagnostic signature of where the startup is relatively advanced and where it is relatively underdeveloped.

Maturity Gaps are used in three ways in TAES reports:

1. **Strength identification:** Large positive Maturity Gaps in specific pillars identify where the startup has developed genuine comparative advantages relative to the expected profile.

2. **Priority gap identification:** Large negative Maturity Gaps identify the pillars where the startup most urgently needs development relative to its stage and sector peers.

3. **Investment thesis calibration:** The pattern of positive and negative Maturity Gaps informs how investors should assess the startup. A startup with high Technology Maturity Gap but negative Execution Maturity Gap is a technology-strong, go-to-market-weak company — a well-understood archetype with specific investment and support implications.

---

## Section 7: Expected Funding

### Typical Funding Amounts by Sector, Stage, and Region

Expected funding benchmarks are constructed from the peer group's funding history, cross-referenced with external venture capital data sources. They represent the typical capital raised by comparable startups at comparable stages and provide the reference for identifying anomalies in a startup's funding position.

**Typical funding ranges by stage (USD, global median across sectors):**

| Stage | Typical Range (USD) | Median (USD) |
|---|---|---|
| Pre-seed | 25,000 – 500,000 | 150,000 |
| Seed | 500,000 – 3,000,000 | 1,200,000 |
| Series A | 3,000,000 – 15,000,000 | 7,500,000 |
| Series B | 15,000,000 – 60,000,000 | 28,000,000 |
| Series C+ | 60,000,000+ | Variable |
| Grant-only | 25,000 – 2,000,000 | 350,000 |

**Regional adjustments:** Funding amounts are significantly lower in emerging market ecosystems. TAES applies regional multipliers to adjust expectations:

| Region | Funding Multiplier vs. Global Median |
|---|---|
| North America | 1.5× |
| Western Europe | 1.2× |
| East Asia | 1.1× |
| Middle East & North Africa | 0.85× |
| Southeast Asia | 0.75× |
| South Asia | 0.65× |
| Sub-Saharan Africa | 0.55× |
| Latin America & Caribbean | 0.70× |
| Central & Eastern Europe | 0.80× |

**Sector adjustments:** Hardware, Biotech, MedTech, SpaceTech, and Defence sectors typically require 2–4× more capital to reach comparable TRL milestones than software-only sectors. TAES applies sector-specific capital intensity factors when assessing funding adequacy.

### Identifying Underfunded Startups

An **underfunded startup** is one that has raised significantly less capital than the sector-stage-region peer median, while showing technology and execution progress consistent with more highly funded peers. This is a positive signal when it reflects capital efficiency, but it is a risk signal when it reflects difficulty in fundraising.

Underfunding is flagged when a startup's total capital raised is below the 25th percentile of the peer group's funding distribution. The flag triggers a specific analysis covering:

- **Capital efficiency check:** Is the startup's execution progress consistent with its limited capital? If execution is above peer median despite below-peer funding, the flag is annotated as Capital Efficient.
- **Runway assessment:** Based on the disclosed burn rate and remaining capital, the report estimates the remaining runway in months. A runway below 9 months is a High Priority flag. A runway between 9–18 months is a Medium Priority flag.
- **Fundraising risk:** The report notes whether the startup is actively fundraising, the size of the current round sought, and whether the amount sought is consistent with the capital required to reach the next material milestone.

### Identifying Overfunded Startups

An **overfunded startup** is one that has raised significantly more capital than the sector-stage-region peer median, while showing execution and technology progress below the peer median. This pattern suggests capital deployment inefficiency and is associated with elevated risk of poor capital allocation, team misalignment, or premature scaling.

Overfunding is flagged when a startup's total capital raised is above the 75th percentile of the peer group's funding distribution, while its Execution & Traction pillar score is below the 40th percentile. Both conditions must be simultaneously true for the flag to be activated.

The flag triggers a specific analysis covering:
- Which execution metrics are most below expectation relative to capital raised
- Whether the gap is stage-appropriate (e.g., large pre-revenue capital raises in Biotech are normal) or anomalous
- Whether there are governance or team stability risk factors that might explain the execution gap

### Funding Efficiency Metric

The **Funding Efficiency Metric (FEM)** measures how much execution output a startup has achieved per unit of capital consumed. It is a relative metric: it is meaningful only when compared against the peer group's funding efficiency distribution, not in absolute terms.

FEM is computed as the ratio of the startup's Execution & Traction pillar score to its total capital raised, expressed as a normalised value relative to the peer group median of the same ratio. A FEM above 1.0 indicates above-peer capital efficiency. A FEM below 1.0 indicates below-peer capital efficiency.

FEM is presented in the report alongside its peer group percentile position and a qualitative interpretation. It is explicitly framed as an indicative metric, not a definitive measure: the execution pillar score captures multiple dimensions of execution, and the capital raised figure does not capture non-dilutive support (e.g., in-kind support from accelerators, value of mentorship programmes, or tax credit value) that may have meaningfully supplemented cash capital.

---

## Section 8: Expected Team Size

### Typical Team Sizes by Sector, Stage, and Business Model

Team size expectations are calibrated against the peer group's observed team sizes at comparable stages, within comparable sectors and business models. The following reference ranges represent the interquartile range (25th–75th percentile) of team sizes in the TAES benchmark database:

**By funding stage:**

| Stage | Typical FTE Range | Median FTE |
|---|---|---|
| Pre-seed | 1–3 | 2 |
| Seed | 2–8 | 4 |
| Series A | 8–25 | 14 |
| Series B | 20–75 | 35 |
| Grant-only | 1–5 | 3 |
| Bootstrapped | 1–6 | 3 |

**By sector (at Seed stage):**

| Sector | Typical FTE Range at Seed | Notes |
|---|---|---|
| AI / SaaS | 3–8 | Lean teams common; strong engineering bias |
| DeepTech | 3–10 | Includes research personnel; may include academic collaborators |
| Biotech / MedTech | 4–12 | Lab personnel included; clinical team begins at Seed |
| Hardware | 5–15 | Design, manufacturing engineering, and supply chain roles required early |
| AgriTech / ClimateTech | 3–10 | Varies significantly by technology type within sector |
| FinTech | 3–9 | Regulatory/compliance roles required earlier than in other SaaS sectors |
| Consumer / D2C | 2–6 | Lean core teams common; significant contract or agency support |

**By business model (at Seed stage):**

| Business Model | Typical FTE Range at Seed |
|---|---|
| B2B SaaS | 3–8 |
| B2C | 2–6 |
| B2B2C | 3–9 |
| Marketplace | 4–10 |
| Hardware | 6–15 |
| Platform | 4–10 |
| Services | 3–8 |

### Identifying Understaffed Situations

An **understaffed startup** is one whose team size falls below the 25th percentile of the peer group's team size distribution, while simultaneously showing evidence of significant operational commitments — such as active enterprise customers, multiple simultaneous product development tracks, or pilot deployments requiring ongoing support.

Understaffing flags are generated when the team size-to-commitment ratio indicates that the declared team could not plausibly execute the claimed or required workload at peer-median quality levels. This is distinct from deliberately lean team structures: a solo founder building an MVP with no customers is not understaffed; a team of two managing three enterprise pilots and an active fundraising process simultaneously is.

The understaffing flag prompts a report narrative section covering:
- Which operational commitments are at highest execution risk given the team size
- Whether the team composition (skill set distribution) exacerbates or mitigates the size limitation
- Whether the hiring plan is credible given the capital position

### Identifying Overstaffed Situations

An **overstaffed startup** is one whose team size exceeds the 75th percentile of the peer group's team size distribution at comparable stage and funding level, while showing execution and revenue outputs below the peer median. Overstaffing is a less common flag than understaffing but can indicate premature scaling, poor hiring strategy, or capital misallocation.

The overstaffed flag triggers an analysis of burn rate sustainability, team productivity indicators, and whether the team composition is appropriately calibrated to the startup's current development stage and primary challenges.

### The Team Completeness Index

The **Team Completeness Index (TCI)** is a structured assessment of whether the founding team and current team collectively cover the critical functional capabilities required for a startup at its current stage and sector. It is distinct from team size: a small team can be highly complete if it covers all required functions, and a large team can be functionally incomplete if key roles are absent.

The TCI assesses coverage across the following functional domains, weighted by their criticality at the current stage:

| Functional Domain | Pre-Seed Weight | Seed Weight | Series A Weight |
|---|---|---|---|
| Core technical / product development | 35% | 30% | 25% |
| Commercial / revenue generation | 20% | 25% | 25% |
| Domain expertise / sector knowledge | 20% | 20% | 15% |
| Operational / delivery capability | 10% | 15% | 20% |
| Regulatory / legal / compliance | 5% | 5% | 10% |
| Finance / fundraising | 10% | 5% | 5% |

Each functional domain is assessed as covered (full weight), partially covered (half weight), or absent (zero weight). The TCI is expressed as a percentage of maximum possible coverage. A TCI of 100% indicates full functional coverage. A TCI below 60% at any stage is flagged as a Team Completeness Gap and noted as a priority finding.

The TCI is connected to the team size benchmark through the Maturity Gap framework: a startup with an appropriately-sized team but a low TCI is flagged as having a coverage gap, while a startup with an undersized team but a high TCI is flagged as operationally stretched despite good composition.

---

## Section 9: Expected Valuation

### Typical Valuation Ranges by Sector, Stage, and Funding History

Valuation benchmarking is among the highest-risk dimensions of startup evaluation due to its dependence on negotiated transaction terms, market sentiment, investor competition, and disclosure inconsistencies. TAES treats valuation benchmarks as wide reference ranges rather than precise expectations, and all valuation conclusions carry mandatory uncertainty disclosures.

**Typical post-money valuation ranges by stage (USD, global median across sectors):**

| Stage | Typical Range (USD) | Median (USD) | Notes |
|---|---|---|---|
| Pre-seed | 500,000 – 5,000,000 | 2,000,000 | High variance; largely negotiated without empirical basis |
| Seed | 2,000,000 – 20,000,000 | 8,000,000 | Increasingly data-supported; revenue multiples emerging |
| Series A | 15,000,000 – 80,000,000 | 35,000,000 | Revenue multiples standard; growth rate and NRR drive variability |
| Series B | 60,000,000 – 300,000,000 | 120,000,000 | Full financial metrics expected; market leadership position valued |

**Regional valuation adjustments:** Valuations in emerging markets are structurally lower than in mature venture markets due to liquidity differences, exit environment constraints, and investor risk premium expectations.

| Region | Typical Valuation Discount vs. North America Comparable |
|---|---|
| Western Europe | 20–35% discount |
| East Asia | 10–25% discount |
| Southeast Asia | 30–45% discount |
| South Asia | 35–50% discount |
| Sub-Saharan Africa | 40–60% discount |
| Latin America | 30–50% discount |
| MENA | 25–40% discount |

**Sector valuation multipliers:** Technology sectors with high growth potential and large addressable markets typically command higher revenue multiples than those with limited scalability or longer development timelines.

| Sector | Typical Revenue Multiple at Seed–Series A |
|---|---|
| AI / SaaS | 8–25× ARR |
| FinTech | 5–15× ARR |
| MedTech / Biotech | Milestone-based; revenue multiples less applicable pre-commercialisation |
| DeepTech | IP-value and potential market size; limited revenue multiple applicability |
| Consumer / D2C | 2–6× ARR (lower multiples, higher volume expectations) |
| Marketplace | 3–10× GMV run rate (take-rate dependent) |
| Manufacturing | 2–5× ARR (lower due to margin compression) |

### Estimating Valuation When Not Disclosed

Many startups do not disclose their valuation, particularly at early stages. When valuation is not disclosed, TAES constructs an estimated valuation range using the following methodology:

**Step 1 — Capital and dilution inference:** If the startup has disclosed the amount raised and the equity percentage given in the last round, post-money valuation is computed directly (Post-money = Amount raised ÷ Equity percentage given).

**Step 2 — Revenue multiple estimation:** If ARR is disclosed, a revenue multiple is applied based on sector, stage, and growth rate benchmarks to produce a revenue-implied valuation range.

**Step 3 — Stage median application:** If neither capital structure nor ARR is sufficient for estimation, the stage and sector median valuation from the benchmark database is applied as the reference, with wide confidence intervals (±50% of the median).

**Step 4 — Comparison check:** Where multiple estimation methods are applicable, all estimates are computed and compared. Significant divergence between methods is noted as a valuation uncertainty flag.

All estimated valuations are clearly labelled as estimates, with the estimation method disclosed. Estimated valuations are not presented as established facts. They are reference points for contextualising fundraising conversations and credibility assessments.

### The Valuation Credibility Check

The **Valuation Credibility Check** is a structured comparison between the startup's claimed or estimated valuation and the valuation range expected for comparable peers. It is designed to identify two types of valuation anomalies:

**1. Implausible over-valuation:** The startup claims a valuation significantly above the peer 90th percentile without the product maturity, revenue, team quality, or market position that typically justifies such a premium. Over-valuation flags carry a mandatory narrative explaining the specific gaps between the claimed valuation basis and the evidence presented.

**2. Unusual under-valuation:** The startup has accepted a valuation significantly below the peer 25th percentile relative to its apparent quality and progress. This is less commonly a concern in itself, but may indicate: unfavourable term structures, distressed fundraising conditions, founder inexperience in negotiation, or emerging market structural discounts not captured in the regional adjustment factors.

The credibility check does not produce a binary pass/fail. It produces a **Valuation Credibility Assessment** characterised as:
- **Consistent:** Claimed valuation is within the expected peer range; no anomaly flagged
- **Stretched:** Claimed valuation is above the 75th percentile; higher than typical but not implausible given disclosed evidence
- **Implausible:** Claimed valuation is above the 90th percentile without supporting evidence; flag with detailed narrative required
- **Below-market:** Claimed valuation is below the 25th percentile; noted with contextual explanation

### Limitations of Valuation Benchmarking

Valuation benchmarks within TAES carry inherently wider confidence intervals than other benchmark dimensions due to the following structural limitations:

**1. Disclosure gaps.** A large proportion of startup valuations are confidential. Benchmark populations for valuation are therefore drawn from the subset of startups that have disclosed valuation data, which is a non-random sample biased toward startups that have closed formal rounds and are willing to disclose terms.

**2. Market cycle sensitivity.** Startup valuations are acutely sensitive to macro-market conditions. Benchmarks calibrated during a bull market will produce inflated reference ranges when applied in a contraction period, and vice versa. TAES applies an annual recalibration to valuation benchmarks, but intra-year shifts may not be captured.

**3. Negotiation variability.** At early stages (Pre-seed, Seed), valuation is determined largely by negotiation and investor demand, not by quantitative fundamentals. Two startups with identical profiles may receive valuations differing by 3–5× depending solely on investor competition at the time of the round.

**4. Regional discount uncertainty.** Regional valuation discounts are estimated from observed transaction data, but transaction data in many emerging markets is sparse. Regional discount estimates for Sub-Saharan Africa, Central Asia, and parts of Southeast Asia carry particularly wide uncertainty bands.

Given these limitations, all TAES valuation conclusions include the following mandatory disclaimer: *"Valuation benchmarks are indicative reference ranges derived from comparable transaction data and peer evaluation records. They should not be interpreted as valuations or appraisals. Valuation is inherently context-dependent and subject to significant market, negotiation, and disclosure variability. All valuation conclusions in this report carry wide confidence intervals and should be treated as supporting context, not as determinative assessments."*

---

## Section 10: Benchmark Confidence

### How Benchmark Confidence Is Scored

Benchmark confidence is a meta-level assessment of how much trust should be placed in the comparative conclusions derived from a benchmark. It is distinct from the confidence in any individual pillar score (which is addressed in the pillar evaluation methodology documents) and from the peer group confidence described in Section 2 (which measures how well-matched the peers are). Benchmark confidence measures the reliability of the benchmark itself — whether it is based on a sufficiently large, recent, and well-distributed population to produce stable and meaningful statistical outputs.

Benchmark confidence is expressed on a four-tier scale:

| Tier | Label | Conditions | Report Treatment |
|---|---|---|---|
| Tier 1 | High | n_effective ≥ 25; ≥70% of records within 18 months; no composite construction; all primary criteria matched; no dimension relaxations applied | Comparative conclusions presented without qualification |
| Tier 2 | Moderate | 15 ≤ n_effective < 25; or ≥50% of records within 18 months; or one secondary dimension relaxation; or one adjacent sector in composite construction | Comparative conclusions presented with one-sentence qualification note |
| Tier 3 | Low | 10 ≤ n_effective < 15; or two dimension relaxations; or >50% of records older than 18 months; or two adjacent sectors in composite | Comparative conclusions presented with explicit uncertainty flag and reduced decision weight |
| Tier 4 | Very Low / Suspended | n_effective < 10; or primary criterion relaxed; or three or more dimension relaxations; or no valid peer group constructible | Percentiles and comparative flags suppressed; absolute scores only; benchmark suspension notice included |

### Factors That Reduce Benchmark Confidence

The following conditions, individually or in combination, reduce benchmark confidence:

**1. Small peer group size.** The single largest driver of low benchmark confidence. Statistical distributions become unstable with small populations; a single outlier entity can shift the median significantly.

**2. Stale data.** Records from more than 18 months prior contribute less to the benchmark's representativeness of current conditions. Sectors with rapid evolution — AI, FinTech, Consumer — are particularly affected by data staleness, as the operational reality for startups in these sectors changes faster than in less dynamic sectors.

**3. Sparse dimension coverage.** When a high proportion of peer records lack scores for one or more pillars, the distribution for those pillars is based on an unrepresentative subset of the peer group. This reduces confidence specifically for the affected pillar's percentile calculations.

**4. High compositional heterogeneity.** When the peer group contains high variance in secondary dimensions (e.g., a peer group spanning multiple sectors, multiple stages, or multiple regions due to composite construction), the distribution is noisier and less precisely predictive of the target startup's likely position.

**5. Temporal clustering.** When a disproportionate share of peer records originate from a narrow time window (e.g., during a venture funding boom or a specific macroeconomic event), the benchmark may be systematically biased toward the conditions of that period.

**6. Disclosed vs. estimated data mix.** When a significant proportion of peer data points are estimated rather than directly disclosed (particularly for revenue and valuation dimensions), the benchmark carries additional uncertainty from the estimation errors in the underlying data.

**7. Single-source concentration.** When a disproportionate share of peer records originate from a single external data source or a single accelerator cohort, the benchmark may reflect the selection biases of that source rather than the broader population.

### How Low-Confidence Benchmarks Are Communicated

The report communication strategy for each benchmark confidence tier is as follows:

**Tier 1 (High):** Comparative conclusions are stated directly without qualification. The peer group metadata (n_effective, dataset version, confidence tier) is included in the report appendix for transparency, but does not interrupt the main narrative.

**Tier 2 (Moderate):** Each comparative conclusion that draws on the benchmark is followed by a parenthetical note: *(Benchmark confidence: Moderate; n_effective = [value])*. A summary paragraph at the end of the Benchmarking section of the report explains the conditions contributing to the moderate confidence rating.

**Tier 3 (Low):** A prominent flag box appears at the opening of the Benchmarking section of the report: *"⚠ Benchmark Confidence: Low. Comparative conclusions in this section are based on a limited or partially constructed peer group (n_effective = [value]). These comparisons should be treated as directional indicators only. Absolute pillar scores are the recommended basis for primary evaluation conclusions."* Each individual comparative statement is individually annotated with the low-confidence designation.

**Tier 4 (Very Low / Suspended):** The Benchmarking section of the report is replaced by the following notice: *"Benchmark data is not available or is insufficient to support comparative evaluation for this startup's profile. Evaluation conclusions in this report are based solely on absolute pillar scores assessed against TAES evaluation criteria. No peer group percentiles, maturity gap assessments, or comparative flags are presented. This does not affect the validity of the absolute evaluation; it reflects the absence of a sufficient comparable peer population in the current TAES database for this specific profile."*

### The Benchmark Data Quality Audit Process

All benchmarks active in TAES v1.1 are subject to a structured quarterly data quality audit. The audit process covers the following checks:

**1. Population size verification.** Confirms that each active benchmark population meets or exceeds the minimum record count. Populations that have fallen below minimum due to data aging are flagged for either composite construction or suspension.

**2. Recency verification.** Confirms the proportion of records within the benchmark that fall within the 18-month recency window. Populations with declining recency are prioritised for data enrichment from external sources.

**3. Outlier review.** Identifies any entity whose data disproportionately influences benchmark distributions (>10% of population). Outlier influence is managed by applying a contribution cap — no single entity may contribute more than one-tenth of the effective statistical weight of the benchmark population.

**4. Cross-benchmark consistency check.** Verifies that benchmark distributions are internally consistent across related populations. For example, the Seed-stage AI benchmark should produce distributions that are statistically consistent with the adjacent Pre-seed-AI and Seed-SaaS benchmarks, accounting for expected directional differences. Unexplained discontinuities between adjacent benchmarks are flagged for manual review.

**5. Source attribution review.** Verifies that each record in the benchmark population has a traceable and valid data source reference. Records without traceable sources are flagged for re-verification or exclusion.

**6. Anonymisation audit.** Confirms that benchmark outputs cannot be used to identify individual startups. Any benchmark population where the peer group is small enough that reverse-identification is plausible is subject to additional anonymisation controls (see Section: Anonymisation).

Audit results are recorded in the Benchmark Registry (see Section: Benchmark Governance) and inform decisions on benchmark activation, suspension, and data enrichment priorities.

---

## Benchmark Governance

### Overview

Benchmark governance defines the processes by which benchmark definitions, populations, methodologies, and outputs are reviewed, approved, updated, versioned, and retired. It ensures that benchmarks remain accurate, fair, and methodologically sound over time, and that any changes to benchmarks are made through a controlled, auditable process rather than ad hoc adjustments.

### The Benchmark Registry

The **Benchmark Registry** is the authoritative record of all benchmarks active within the TAES framework. For each benchmark, the registry records:

- Benchmark identifier (unique alphanumeric code)
- Benchmark dimensions covered and classification values
- Active dataset version
- Population size (n_total and n_effective)
- Recency profile (proportion of records by age band)
- Confidence tier (current)
- Date of last audit
- Date of next scheduled review
- Status (Active / Reduced Confidence / Suspended / Deprecated)
- History of all status changes with dates and rationale

The Benchmark Registry is maintained by the TIDES Evaluation Standards Committee and is reviewed quarterly. Access to the full registry is restricted to authorised TIDES personnel. Summary registry statistics (active benchmark count, aggregate confidence distribution) are published in the TIDES Annual Transparency Report.

### Benchmark Review Cycle

All active benchmarks are subject to a minimum annual review. The review process covers:

**1. Data refresh assessment.** The review determines whether the benchmark's underlying data population has changed materially since the last review — due to new evaluations, updated external data sources, or data aging. If the population has changed by more than 20% (by record count or by effective weight due to aging), a formal population refresh is initiated.

**2. Methodology assessment.** The review assesses whether the benchmark dimensions, weighting factors, and confidence tier criteria remain appropriate given changes in the ecosystem, sector norms, or TAES framework updates. Methodology changes require a framework version increment.

**3. Performance validation.** Where outcome data is available (e.g., follow-on funding events, acquisitions, or failures among previously evaluated startups), the review assesses whether benchmark percentile positions were predictively correlated with subsequent outcomes. Systematic mispredictions — where startups in the top quartile consistently underperformed or those in the bottom quartile consistently outperformed — are treated as signals of benchmark calibration error.

### Benchmark Versioning

Benchmarks are versioned at two levels:

**Framework version (TAES v1.x):** The framework version governs the methodology — the dimensions used, the weighting of dimensions in similarity scoring, the confidence tier criteria, and the rules for composite peer group construction. Framework version increments require a formal ratification process through the TIDES Evaluation Standards Committee, minimum 30-day consultation period, and a published change log documenting all modifications.

**Dataset version (e.g., Benchmark Dataset v2026-Q2):** The dataset version governs the underlying data population. Dataset versions are updated quarterly as new evaluations are added and external data is refreshed. Dataset version updates do not require a formal ratification process but are recorded in the Benchmark Registry with the date, source of new data, and the change in population metrics.

All evaluation reports record both the framework version and the dataset version used at the time of evaluation. This enables retrospective comparison and ensures that reports can be accurately interpreted in future.

### Change Management

Changes to benchmark methodology (framework-level changes) follow a structured change management process:

1. **Proposal submission:** Any TIDES evaluator, data steward, or standards committee member may submit a benchmark methodology change proposal. Proposals must include: the specific change requested, the rationale, the expected impact on existing benchmark outputs, and a proposed implementation timeline.

2. **Impact assessment:** The standards committee conducts an impact assessment, including a quantitative simulation of how the proposed change would affect benchmark outputs across the full active evaluation dataset.

3. **Consultation:** Proposals with material impact on benchmark outputs are circulated for a minimum 30-day internal consultation period.

4. **Ratification:** Changes are ratified by the standards committee (majority vote required). Ratification records are maintained in the Benchmark Governance Log.

5. **Implementation and communication:** Ratified changes are implemented in the next scheduled framework release. Affected evaluators are notified. Evaluations conducted under the previous framework version retain their original benchmark assessments; they are not retroactively updated.

---

## Benchmark Data Sources

### Overview

The benchmark database is populated from three categories of data sources: internal evaluation records generated by the TAES evaluation process, structured external databases, and curated sector reports. Each source type carries different data quality characteristics, and benchmark records derived from different source types are weighted accordingly.

### Source Category 1: Internal Evaluation Records

Internal evaluation records are the primary and highest-quality source of benchmark data. Every startup evaluated through the full TAES evaluation process generates a structured evaluation record that is eligible for inclusion in the benchmark database, subject to:

- Successful completion of all five pillar evaluations
- Minimum evidence quality rating of Bronze across all pillars (evaluations with significant evidence gaps are excluded from benchmark population)
- Consent from the evaluated startup for anonymised inclusion in aggregate benchmarks (obtained at intake; refusals are respected and the record is excluded from all benchmark populations)
- Record locking: the evaluation record is frozen at the point of report finalisation; subsequent startup updates are recorded separately and do not retroactively alter the locked benchmark record

Internal records contribute the highest-quality benchmark data because they include directly assessed pillar scores, verified dimension classifications, and standardised data formats. They receive full weight in benchmark population calculations.

### Source Category 2: Structured External Databases

Structured external databases supplement internal records, particularly for benchmark dimensions where internal coverage is sparse. Approved external database sources in TAES v1.1 include:

| Source Type | Examples | Data Contribution | Weighting Relative to Internal |
|---|---|---|---|
| Venture capital transaction databases | Dealroom, PitchBook, Crunchbase | Funding amounts, stages, valuation data | 60% (financial dimensions only) |
| Startup accelerator programme records | YC, Techstars, regional accelerator partners | Stage, sector, team data, revenue stage | 55% |
| Government innovation programme databases | Innovate UK, DST India, SBIR/STTR data | Funding, sector, TRL data | 65% |
| National startup registries | Government-maintained startup databases | Country, sector, company age | 70% |
| Industry association surveys | Sector-specific surveys with published methodology | Sector norms, team size, funding ranges | 50% |

External records do not include directly assessed pillar scores. Where external records are used in benchmark populations, they contribute to the distribution of financial and structural dimensions (funding, team size, valuation, revenue stage) but not to pillar score distributions. Pillar score percentiles are therefore always derived exclusively from internal evaluation records.

This distinction is critical: **market percentiles are computed only from internally evaluated startups**, while structural benchmarks (funding, team size, valuation, company age distributions) may draw on the broader supplemented population.

### Source Category 3: Curated Sector Reports

Curated sector reports are used to calibrate expected maturity ranges and typical development timelines rather than to populate peer group databases. Approved sector report sources include:

- Startup ecosystem reports from reputable organisations (e.g., World Economic Forum, OECD, regional development banks)
- Venture capital firm sector-specific reports (from recognised sources with disclosed methodology)
- Academic research on startup performance by sector and geography
- Industry bodies' annual benchmark publications

Sector report data is incorporated as calibration inputs rather than raw benchmark records. The calibration process is managed annually by the TIDES data stewardship team and requires documented source assessment, covering methodology transparency, sample size, recency, and potential conflicts of interest.

### Data Quality Standards for Benchmark Records

All records entering the benchmark database — regardless of source — must meet the following minimum quality standards:

| Quality Dimension | Standard |
|---|---|
| Source traceability | Each record must have a documented, auditable source reference |
| Data completeness | A minimum of 70% of dimension fields must be populated for the record to be included |
| Temporal validity | Records are included only if the data pertains to the startup's status within the last 48 months |
| Duplication control | Each startup may contribute only one record per evaluation cycle; duplicates are merged or flagged |
| Classification quality | Dimension classifications must be either directly verifiable from documents or flagged as estimated |

Records that fail to meet these standards are excluded from benchmark populations. Excluded records are retained in the raw data archive but are not used in any comparative calculation.

---

## Anonymisation

### The Anonymisation Imperative

Startup evaluation data is commercially sensitive, operationally confidential, and in some jurisdictions subject to privacy and data protection regulation. The benchmark database contains information about companies that may include unreleased product details, unannounced funding rounds, proprietary technology descriptions, and financial performance data shared under non-disclosure terms.

The anonymisation framework governing TAES benchmarks ensures that:
- No individual startup can be identified from benchmark outputs or from the peer group used in any evaluation report
- Benchmark populations are never disclosed in forms that would allow reverse-engineering of individual records
- Data subjects can exercise rights over their contributed data without disrupting the statistical integrity of the benchmark

### Anonymisation Standards

TAES v1.1 applies the following anonymisation standards to all benchmark data:

**1. Minimum peer group suppression.** Benchmark outputs derived from populations of fewer than 10 records are suppressed in their entirety. No distribution statistics, percentile ranges, or comparative conclusions are published from populations of this size, regardless of the analytical value they might otherwise provide. This is the single most important anonymisation control.

**2. Generalisation of dimension values.** In all published benchmark outputs and reports, dimension values are expressed at their classification level (e.g., "Seed stage, South Asia, B2B SaaS") rather than at values that might identify specific startups. The combination of dimension values is checked against the population to ensure that no combination of published dimension values uniquely identifies fewer than five records.

**3. Aggregation floor.** Statistical outputs (medians, percentile ranges, distribution parameters) are computed from populations of sufficient size that no individual record has a mathematically identifiable influence on the output. The contribution cap (no single entity may constitute more than 10% of effective weight) is the operational implementation of this control.

**4. Score perturbation for small populations.** In benchmark populations that meet the minimum size requirements but are small enough to carry heightened identification risk (10–19 records), published distribution statistics are rounded to the nearest 5 points (for score distributions) and the nearest 25th percentile bound (for percentile outputs). This perturbation is not applied to internal calculations; it applies only to disclosed outputs.

**5. Temporal offset.** In published benchmark summaries, the precise timing of individual evaluation records is not disclosed. Records are attributed only to a quarter-year period (e.g., Q3 2025), not to a specific date.

**6. Consent management.** Startups that withdraw consent for anonymised benchmark inclusion are removed from all active benchmark populations at the next scheduled quarterly data refresh. Withdrawal of consent does not retroactively alter reports already issued; it prevents the startup's data from contributing to future benchmark populations. A consent withdrawal flag is recorded in the Benchmark Registry.

### Anonymisation Audit

The anonymisation controls described above are audited annually by the TIDES data stewardship team, with specific focus on:

- Identifying any dimension combination in active benchmarks that could plausibly narrow the candidate population to fewer than five records
- Reviewing all recently activated small-population benchmarks (10–19 records) to confirm perturbation controls are correctly applied
- Verifying that all consent withdrawal requests from the previous year have been processed and reflected in the active benchmark populations
- Confirming that no external data records have been inadvertently included without source documentation and anonymisation classification

The results of the anonymisation audit are included as an appendix to the TIDES Annual Transparency Report. Material anonymisation findings (i.e., any case where individual identification risk was assessed as Moderate or High) are escalated to the TIDES Governance Council for remediation action within 30 days of identification.

### Cross-Border Data Compliance

Benchmark data crosses jurisdictional boundaries: a peer group for a startup in one country may include evaluation records from startups in other countries. TAES acknowledges the following compliance obligations:

- Evaluation records from EU-based startups that contain personal data (founder names linked to performance data) are handled in compliance with GDPR. Benchmark population records are stripped of all personal identifiers before inclusion.
- Evaluation records from startups in jurisdictions with specific data localisation requirements are handled in accordance with a jurisdiction-specific data processing addendum agreed at intake.
- The benchmark database does not store raw personal data alongside performance data. Linkage between personal identifiers and performance records exists only in the secure evaluation record system, which is subject to access controls and audit logging separate from the benchmark database.

---

*End of Document*

---

> **Document Control**
>
> | Field | Value |
> |---|---|
> | Document ID | TAES-v1.1-DOC-05 |
> | Document Title | Benchmarking Framework |
> | Version | 1.1.0 |
> | Status | Ratified |
> | Classification | Internal Technical Standard |
> | Maintained By | TIDES Evaluation Standards Committee |
> | Approved By | TIDES Governance Council |
> | Effective Date | 2026-06-24 |
> | Next Review Date | 2027-01-01 |
> | Related Documents | TAES-v1.1-DOC-01 (Framework Overview), TAES-v1.1-DOC-02 (Pillar Definitions), TAES-v1.1-DOC-03 (Scoring Methodology), TAES-v1.1-DOC-04 (Evidence Standards), TAES-v1.1-DOC-06 (Report Formatting Standard) |
