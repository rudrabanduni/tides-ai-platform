> **Document:** TAES v1.0 / Scoring Standard
> **Classification:** Internal Technical Standard
> **Version:** 1.0.0
> **Maintained By:** TIDES Platform — Evaluation Standards Committee
> **Effective Date:** 2026-06-23
> **Review Cycle:** Annual or upon material change to evaluation methodology
> **Related Documents:** 01_Platform_Overview, 02_Data_Ingestion_Standard, 03_Agent_Architecture, 04_Prompt_Engineering_Standard, 06_Sector_Normalization_Standard, 07_Override_And_Audit_Standard

---

# TAES v1.0 — Scoring Standard

## Table of Contents

1. [Introduction and Scoring Philosophy](#1-introduction-and-scoring-philosophy)
2. [Score Architecture Overview](#2-score-architecture-overview)
3. [Configurable Weight Design Principle](#3-configurable-weight-design-principle)
4. [Sector Normalisation and Its Effect on Scoring](#4-sector-normalisation-and-its-effect-on-scoring)
5. [Pillar 1: Founder](#5-pillar-1-founder)
6. [Pillar 2: Product](#6-pillar-2-product)
7. [Pillar 3: Technology](#7-pillar-3-technology)
8. [Pillar 4: Market](#8-pillar-4-market)
9. [Pillar 5: Business Model](#9-pillar-5-business-model)
10. [Pillar 6: Financial](#10-pillar-6-financial)
11. [Pillar 7: IP (Intellectual Property)](#11-pillar-7-ip-intellectual-property)
12. [Pillar 8: Risk](#12-pillar-8-risk)
13. [Overall Score Aggregation](#13-overall-score-aggregation)
14. [Score Override Protocol](#14-score-override-protocol)
15. [Historical Scoring and Longitudinal Tracking](#15-historical-scoring-and-longitudinal-tracking)
16. [Summary Reference Table](#16-summary-reference-table)

---

## 1. Introduction and Scoring Philosophy

### 1.1 Purpose of This Document

This document defines the complete scoring methodology for the TIDES AI Evaluation Standard, version 1.0 (TAES v1.0). It governs how the TIDES platform evaluates startups across eight structured evaluation pillars, how pillar scores are computed, how they are combined into a single overall score, and how that score must be interpreted by downstream consumers — whether human reviewers, institutional investors, accelerator programmes, government grant committees, or API clients.

The TAES v1.0 Scoring Standard is not a ratings guide. It is a computational and analytical specification. Every score produced by the TIDES platform must be traceable to evidence, weighted by confidence, and explainable in natural language. Any score that cannot be explained and attributed to observed evidence should be treated as invalid.

### 1.2 Scoring Philosophy

The TIDES scoring system is built on five foundational principles:

**Principle 1 — Explainability Over Precision.**
A score of 7.4 with a clear, evidence-linked rationale is more valuable than a score of 7.421 produced by an opaque model. Every pillar score must be accompanied by a natural-language justification that references specific evidence inputs. The platform is designed to produce scores a qualified human could reconstruct independently given the same evidence.

**Principle 2 — Confidence as a First-Class Signal.**
Every pillar score has two components: the score itself and a confidence level. A pillar score of 8/10 with 40% confidence must be interpreted very differently from an 8/10 with 90% confidence. Confidence is a function of evidence completeness and source quality. It is always reported alongside the score, never suppressed.

**Principle 3 — No Hardcoded Universalism.**
No startup exists in a contextual vacuum. A fintech startup and a deep-tech hardware company cannot be evaluated against identical benchmarks. Sector normalisation adjustments, configurable weights, and cohort-relative thresholds are first-class features of the scoring model, not afterthoughts.

**Principle 4 — Evidence Primacy.**
The platform does not infer what it cannot observe. If evidence for a subcriteria is absent, that absence is recorded and reflected in the confidence score. The scoring agent does not extrapolate favourable outcomes from partial data; it flags gaps explicitly.

**Principle 5 — Auditability.**
Every score produced under TAES v1.0 must be reproducible. All input evidence, agent reasoning steps, subcriteria assessments, pillar scores, confidence calculations, and weighting configurations must be persisted in the evaluation record. Human overrides must be documented with full justification.

### 1.3 What a Final Score Means

The TIDES overall score is a number on the continuous scale of 0.00 to 10.00, representing the platform's holistic assessment of a startup's investment readiness, execution capability, and strategic viability at the time of evaluation.

The score is not a prediction of success. It is an evaluation of current state against structured criteria, with context applied through sector normalisation and cohort calibration. A score of 8.5 does not mean the startup will succeed; it means that across the eight evaluation pillars, the available evidence supports a strong assessment of the startup's fundamentals, with high confidence.

Score interpretation must always account for:
- The confidence level of the overall score
- The sector normalisation context applied
- The recency of the underlying evidence
- Whether any pillar scores have been subject to human override

### 1.4 The Role of Confidence

Confidence is reported as a percentage (0%–100%) at both the pillar level and the overall level. It represents the degree to which the platform can assert the accuracy of the assigned score, given the evidence available.

| Confidence Band | Label | Interpretation |
|---|---|---|
| 85%–100% | High Confidence | Score is well-supported by primary evidence; suitable for high-stakes decisions |
| 60%–84% | Moderate Confidence | Score is substantiated but has evidence gaps; suitable with supplementary review |
| 35%–59% | Low Confidence | Score is partially supported; significant gaps exist; treat as indicative only |
| 0%–34% | Very Low Confidence | Score is largely inferential; not suitable for any formal decision without additional data collection |

When a pillar's confidence is below 35%, the platform must flag that pillar as **data-deficient** and the overall score must include a corresponding warning. Downstream consumers (investor portals, grant systems) must be configured to display this warning prominently.

---

## 2. Score Architecture Overview

### 2.1 Score Structure

The TIDES evaluation model produces scores at three levels:

```
Level 3 — Subcriteria Scores     (one per sub-criterion within each pillar, 0–10)
     |
     v
Level 2 — Pillar Scores          (one per pillar, 0–10, derived from subcriteria)
     |
     v
Level 1 — Overall Score          (single composite, 0–10, derived from pillar scores)
```

Each level carries its own confidence score. Confidence propagates upward: a low-confidence subcriteria assessment reduces the pillar confidence, which in turn reduces the overall confidence.

### 2.2 The Eight Pillars

| Pillar | Code | Suggested Default Weight |
|---|---|---|
| Founder | FND | 18% |
| Product | PRD | 16% |
| Technology | TEC | 14% |
| Market | MKT | 14% |
| Business Model | BIZ | 12% |
| Financial | FIN | 10% |
| IP (Intellectual Property) | IPC | 8% |
| Risk | RSK | 8% |

> **Important:** These weights are suggestions, not fixed values. They reflect the default configuration of TAES v1.0 for a general-purpose early-stage startup evaluation context. All weights are configurable at the organisation, sector, and cohort level. See Section 3 for the full design specification for configurable weights.

### 2.3 Scoring Notation

Throughout this document, scores are referenced using the following notation:

- **S(pillar)**: The score for a given pillar on the 0–10 scale
- **C(pillar)**: The confidence score for a given pillar, expressed as a percentage
- **W(pillar)**: The weight assigned to a given pillar, expressed as a decimal fraction summing to 1.0 across all eight pillars
- **S(overall)**: The weighted aggregate score across all pillars
- **C(overall)**: The propagated confidence score for the overall assessment

---

## 3. Configurable Weight Design Principle

### 3.1 Why Weights Must Be Configurable

The relative importance of each evaluation pillar is not constant across contexts. A government innovation grant committee may weight IP and Technology significantly higher than Financials, because early-stage technology startups funded by grants are not expected to show revenue. A late-stage venture capital firm may weight Financial and Business Model very heavily, because it is investing at the point where commercial viability must be demonstrated. An accelerator focused on social impact may apply a non-standard weighting that elevates Risk (specifically social and governance risk) alongside Founder and Market.

Hardcoding weights would make the TIDES platform suitable only for one evaluation context. TAES v1.0 is designed to support multiple concurrent evaluation contexts without requiring changes to the underlying scoring logic.

### 3.2 Weight Configuration Levels

Weight configurations are applied at three hierarchical levels. A more specific level always overrides a less specific one:

**Organisation Level** — The default weights for all evaluations performed by an organisation using the TIDES platform. Set during onboarding and reviewed annually.

**Sector Level** — Weight adjustments applied automatically based on the sector classification of the startup being evaluated. For example, a Deep Tech sector profile may increase the Technology and IP weights and reduce the Business Model weight relative to the organisation baseline. Sector-level overrides are governed by the `06_Sector_Normalization_Standard`.

**Cohort Level** — One-time weight configurations applied to a specific evaluation cohort, such as a grant round, accelerator batch, or investment screening exercise. Cohort-level weights expire with the cohort and do not persist.

### 3.3 Weight Constraints

Regardless of the configuration level, all weight configurations must comply with the following constraints:

1. All eight pillar weights must sum to exactly 1.000 (100%).
2. No single pillar weight may be set below 3% (0.03). This prevents any pillar from being effectively eliminated from the evaluation.
3. No single pillar weight may exceed 35% (0.35). This prevents any single dimension from dominating the overall score to the point of invalidating the holistic model.
4. Weight configurations must be named, versioned, and stored in the evaluation metadata. Every evaluation record must reference the weight configuration used.
5. Changes to organisation-level weights require documented justification and are subject to the change management process defined in `07_Override_And_Audit_Standard`.

### 3.4 Weight Configuration Record Format

Every evaluation must store a weight configuration record in the following structure:

```json
{
  "weight_config_id": "WC-2026-003",
  "config_level": "cohort",
  "cohort_id": "BATCH-2026-Q2",
  "effective_from": "2026-04-01",
  "effective_to": "2026-06-30",
  "weights": {
    "FND": 0.20,
    "PRD": 0.18,
    "TEC": 0.16,
    "MKT": 0.12,
    "BIZ": 0.10,
    "FIN": 0.08,
    "IPC": 0.10,
    "RSK": 0.06
  },
  "rationale": "Deep Tech cohort — elevated Technology and IP weights per sector standard TEC-DT-01",
  "approved_by": "Standards Committee",
  "approved_date": "2026-03-15"
}
```

### 3.5 Displaying Scores with Non-Default Weights

When a score is produced using a non-default weight configuration, this must be disclosed in the evaluation report. The report must state clearly which weight configuration was applied, who approved it, and when it was effective. Consumers of the score must be able to request a recalculation using the default TAES v1.0 weights for comparison purposes.

---

## 4. Sector Normalisation and Its Effect on Scoring

### 4.1 Overview

Sector normalisation is the process by which absolute subcriteria assessments are adjusted to reflect the expected performance range for a startup in a given sector at a given stage. Full specification of the normalisation methodology is contained in `06_Sector_Normalization_Standard`. This section describes only the interaction between normalisation and the scoring system.

### 4.2 Why Normalisation Matters for Scoring

Consider two startups both assessed as having modest revenue at seed stage:

- **Startup A** is a consumer mobile app. Industry benchmarks show that seed-stage consumer apps typically have 3,000–15,000 monthly active users and modest revenue. Startup A has 8,000 MAUs and $4,000 MRR. This is in line with sector expectation.
- **Startup B** is an enterprise B2B deep-tech hardware company. At seed stage in this sector, it is normal to have zero revenue, as sales cycles are 12–24 months and the product is still in pilot phase. Startup B has $0 MRR but two signed pilots with enterprise clients.

Without normalisation, both startups may receive a similar raw Financial score. With normalisation, Startup A's score is contextualised against consumer app benchmarks, while Startup B's score is contextualised against deep-tech hardware benchmarks. Startup B's zero revenue does not penalise it to the degree it would in a sector where early revenue is expected.

### 4.3 Mechanics of Normalisation in Scoring

Normalisation operates at the subcriteria level. Before subcriteria scores are aggregated into a pillar score, the following transformation is applied:

1. Each raw subcriteria score is passed through a sector-specific calibration function that maps the raw score to a normalised score, based on the expected distribution of that subcriteria value within the sector.
2. The normalisation function is parameterised by sector code, startup stage, and geography (where geographic data affects benchmarks).
3. The normalised score replaces the raw score in the pillar aggregation.

The sector code and stage classification used for normalisation are stored in the evaluation metadata and are visible in the evaluation report. If the sector code cannot be determined with confidence, the platform applies a generalised early-stage normalisation baseline and flags this in the report.

### 4.4 Scoring Transparency Under Normalisation

Evaluation reports must display both the raw subcriteria score and the normalised subcriteria score, along with the normalisation context applied. Reviewers must be able to see the effect of normalisation on each subcriteria. This is especially important for the Financial pillar, the Market pillar, and the Technology pillar, where sector variation is most pronounced.

---

## 5. Pillar 1: Founder

### 5.1 Purpose

The Founder pillar evaluates the human capital at the centre of the startup. Empirically, the quality, experience, and cohesion of the founding team is among the strongest predictors of startup survival and growth across all sectors and stages. Investors frequently reference the principle that they "invest in people, not ideas," and the TIDES evaluation model reflects this by assigning the Founder pillar the highest suggested default weight.

This pillar measures founder domain expertise, execution history, team completeness, leadership capacity, commitment, and the quality of relationships within and around the team. It is not a measure of academic credentials or network status; it is a measure of whether this team, as constituted, is capable of executing on the stated opportunity.

### 5.2 Evaluation Questions

The AI evaluation agent will assess the following questions when scoring the Founder pillar:

1. What is the founding team's direct domain experience relevant to the problem they are solving, and how many years of hands-on experience does each founder have in this area?
2. Have any of the founders previously founded, co-founded, or held a senior executive role in a startup that reached Series A or beyond? If so, what was the outcome?
3. Does the team collectively cover the critical functional domains required to execute — specifically: technical product development, commercial/sales leadership, and operational management?
4. What is the evidence of a prior working relationship between co-founders? Have they collaborated professionally before, and for how long?
5. Are all founders working full-time on the startup? If not, what is the plan and timeline for transitioning to full-time commitment?
6. Has the team demonstrated the ability to recruit or attract talent, advisors, or early customers based on the strength of its credibility alone?
7. Are there any disclosed conflicts of interest, competing obligations, or unresolved equity/IP disputes among founding team members?
8. What external advisors, mentors, or board members are formally engaged, and what is the nature of their commitment and contribution?
9. How does the team respond to direct challenges to their business model or competitive positioning? Is there evidence of intellectual honesty and adaptive thinking?
10. What is the leadership dynamic within the team — is there a clearly designated decision-making authority, and how are disagreements resolved?
11. Is the founding team's network demonstrably relevant to their go-to-market strategy? Do they have existing relationships with potential customers, channel partners, or industry regulators?

### 5.3 Subcriteria

#### 5.3.1 Domain Expertise (FND-01)
**Measures:** The degree to which the founding team has direct, practitioner-level experience in the industry or problem domain they are addressing. Distinguished from adjacent experience — a software engineer who has worked in healthcare IT is not equivalent to a physician-turned-founder for a clinical diagnostics startup.
**Mapping to Pillar Score:** FND-01 contributes approximately 25% to the Founder pillar score. It is the highest-weighted subcriteria because domain expertise is consistently correlated with the ability to identify real problems, navigate industry-specific challenges, and earn the trust of sector-specific customers and investors.

#### 5.3.2 Execution Track Record (FND-02)
**Measures:** Evidence of prior achievements that demonstrate the team's ability to build, ship, sell, or scale. This includes prior startup experience (including failed startups, which are valued as learning experiences), senior operational roles in high-growth companies, or significant measurable achievements in their professional history.
**Mapping to Pillar Score:** FND-02 contributes approximately 22% to the Founder pillar score. Startups led by founders with proven execution records statistically outperform those led by first-time founders with equivalent domain expertise, because execution requires a distinct set of learned capabilities.

#### 5.3.3 Team Completeness and Complementarity (FND-03)
**Measures:** Whether the founding team collectively possesses the capabilities required to execute the company's stated strategy. A complete team is one that does not have critical functional gaps that would immediately require an expensive external hire or that create a single point of failure. Complementarity refers to whether the founders' skills reinforce each other rather than overlap.
**Mapping to Pillar Score:** FND-03 contributes approximately 20% to the Founder pillar score. Teams with significant functional gaps (e.g., no commercial/sales capability in a B2B startup, or no technical co-founder in a deep-tech startup) receive materially lower scores on this subcriteria.

#### 5.3.4 Commitment and Cohesion (FND-04)
**Measures:** Whether all founders are fully committed to the venture (full-time status, equity vesting in place, no undisclosed competing obligations) and whether the founding team demonstrates a stable, functional working relationship with clear governance.
**Mapping to Pillar Score:** FND-04 contributes approximately 18% to the Founder pillar score. Part-time founders, undocumented equity agreements, and teams with no prior working relationship are all penalised here, as these are statistically elevated risk factors for team dissolution.

#### 5.3.5 Network and Ecosystem Access (FND-05)
**Measures:** The quality and relevance of the founders' professional network relative to the startup's specific go-to-market and fundraising needs. This is not about the size of a LinkedIn network; it is about whether the founders can credibly access the specific decision-makers, customers, partners, or regulators they need to execute.
**Mapping to Pillar Score:** FND-05 contributes approximately 15% to the Founder pillar score. Founders with demonstrably relevant networks gain access advantages that can compress sales cycles, reduce fundraising time, and accelerate regulatory navigation.

### 5.4 Evidence Required

**Primary Evidence (Required):**
- Founder CVs/LinkedIn profiles with verifiable employment history
- Founding team equity and vesting schedule documentation
- Disclosed advisor agreements or advisory board compositions
- Incorporation documents confirming founding team membership and roles

**Secondary Evidence (Supporting):**
- Reference letters or verifiable endorsements from industry figures
- Media coverage, speaking engagements, or published thought leadership
- Prior company records (incorporation, exit documents, press coverage) for prior ventures
- University affiliations, patents, or research publications where relevant to domain expertise
- Recorded pitch sessions or Q&A transcripts showing depth of founder knowledge

### 5.5 Red Flags

1. **Undisclosed equity disputes or vesting gaps:** If the cap table shows uneven equity distribution with no vesting schedule, or if any founder holds a disproportionate share without commensurate contribution, this signals future governance fragility.
2. **Solo founder with no team-building evidence:** A solo founder with no documented effort to recruit co-founders, advisors, or early employees — and no explanation for the solo structure — is a high-attrition risk factor.
3. **All founders from the same functional background:** A founding team composed entirely of engineers, or entirely of business/sales professionals, with no acknowledged plan to address the gap, suggests an incomplete understanding of what is required to build a company.
4. **Prior startup failure with undisclosed or denied learning:** A founder who has previously failed a startup but cannot articulate what they learned or what they would do differently scores materially lower than a founder who demonstrates reflective learning from the same failure.
5. **Conflicting time commitments:** Any founder holding a full-time employment position, directorship in a competing entity, or academic role that creates IP ownership ambiguity without a clear, documented resolution timeline.
6. **No prior working relationship between co-founders:** Founding teams that met within the past six months and have never worked together professionally are at statistically elevated risk of team breakdown under the pressure of building a company.
7. **Advisor relationships that are nominal only:** Advisory boards that list prominent names but have no formal agreement, no documented compensation, and no evidence of active engagement represent misrepresentation risk and provide no actual strategic value.

### 5.6 Scoring Methodology

The Founder pillar score is constructed by assessing each of the five subcriteria individually on a 0–10 basis, applying the subcriteria weights described in Section 5.3, and producing a weighted average. However, the scoring agent does not execute a mechanical calculation alone; it applies the following reasoning process:

First, the agent establishes a baseline for each subcriteria by examining the available primary evidence. It identifies what can be confirmed, what is claimed but unverified, and what is absent. The score for each subcriteria reflects what can be confirmed, with partial credit for credibly claimed but unverified information.

Second, the agent checks whether any red flags are present. A single severe red flag (e.g., an active equity dispute) can cause the entire pillar score to be capped below 6, regardless of subcriteria scores, because red flags in the Founder pillar represent systemic risk rather than localised weakness.

Third, the agent considers the team holistically. A team with four average subcriteria scores and one exceptional subcriteria may score differently than the mechanical average suggests if the exceptional subcriteria is the one most critical for the specific type of startup being evaluated. For example, a highly technical deep-tech startup with exceptional Domain Expertise but only moderate Team Completeness should score differently from a consumer app startup with the same profile.

The resulting pillar score is then subject to confidence weighting before being reported.

### 5.7 Confidence Calculation

Confidence for the Founder pillar is calculated based on the following evidence completeness criteria:

| Evidence Item | Confidence Contribution |
|---|---|
| Verified CVs/LinkedIn for all founders | +20% |
| Documented equity and vesting schedule | +20% |
| Evidence of prior working relationship | +15% |
| Verified prior company history (where claimed) | +15% |
| Advisory board with formal agreements | +10% |
| Reference or endorsement verification | +10% |
| Pitch or interview recording demonstrating domain depth | +10% |

Maximum achievable confidence: 100%. Minimum expected confidence with only primary evidence: 55%.

If confidence falls below 50%, the Founder pillar score must be flagged as **indicative** and the evaluation report must note the specific evidence gaps that drove the low confidence rating. No investment-grade decision should be based on a Founder pillar confidence below 60%.

### 5.8 Suggested Weight

**Suggested Default Weight: 18%**

The Founder pillar carries the highest default weight in the TAES v1.0 model for two reasons grounded in empirical startup research. First, founding team quality is the single factor most consistently cited by experienced investors as their primary evaluation criterion at the pre-seed and seed stages, when the product is often incomplete and the market is still being validated. Second, founding team quality is the factor most difficult to change mid-journey — a weak product can be rebuilt, a market can be repositioned, but a dysfunctional or under-qualified founding team cannot be easily repaired without fundamental disruption to the company.

This weight is configurable. Organisations evaluating later-stage startups where team quality has already been demonstrated through traction may choose to reduce the Founder weight and increase the Financial and Business Model weights. Grant evaluation bodies focused on technical innovation may reduce Founder weight and increase Technology and IP weights.

### 5.9 Scoring Examples

**Score: 3/10 (Low)**
The startup is led by a solo founder who has worked in the relevant industry for two years in a junior capacity. He claims to be working full-time but is currently completing a postgraduate degree and holds a part-time consulting contract in the same industry, creating potential IP conflict. There is no co-founder, no documented advisory board, and no evidence of any attempts to build a team. The founder's equity in the company is undocumented — the company has not completed formal incorporation. Domain knowledge is surface-level: the pitch deck contains accurate industry statistics but the founder struggles with detailed technical or commercial questions. Confidence: 38% (limited primary evidence verified).

**Score: 6/10 (Moderate)**
The startup has three co-founders who met while working at the same mid-sized technology company two years ago and have worked together formally for 18 months. The CEO has seven years of B2B SaaS sales experience and was a regional sales manager; the CTO has eight years of software engineering experience with two prior product launches; the COO is transitioning from full-time employment in three months, which is documented. Equity and vesting is properly structured. The team covers the three critical functional domains. Domain expertise is solid in the commercial and technical dimensions but thinner on the specific sector they are entering (healthtech) — none of the founders has worked inside a hospital or with a healthcare system. They have engaged one advisor from the healthtech space who has a signed advisory agreement for 0.25% equity over two years. Confidence: 72%.

**Score: 9/10 (Exceptional)**
The startup is co-founded by two individuals who previously built and sold a company in an adjacent sector (Series B, acqui-hired). Both founders are full-time with documented vesting. The CEO spent twelve years as a product and commercial leader in the specific sector this startup addresses and has established relationships with three of the five target enterprise customers already in the pipeline. The CTO holds two relevant patents and has led engineering teams of up to forty people. Equity is cleanly structured, a formal advisory board of four sector-specific experts with verified agreements is in place, and one board seat is held by a known institutional investor from the prior venture. The team has a clearly documented decision-making framework and the founders can articulate learned lessons from specific challenges in their prior company with precision. Confidence: 91%.

---

## 6. Pillar 2: Product

### 6.1 Purpose

The Product pillar evaluates the quality, maturity, and differentiation of the startup's core product or service offering. It assesses whether the product demonstrably solves the problem it claims to solve, whether it is built with sufficient quality to be used by real users, and whether it is meaningfully differentiated from alternatives in the market. The pillar does not assess the technology underlying the product (that is covered in Pillar 3); it assesses the product as experienced by the user — its design, usability, problem-solution fit, adoption evidence, and development trajectory.

This pillar is particularly sensitive to stage of development. A pre-revenue startup with a working prototype at seed stage is evaluated against different benchmarks than a Series A startup that should have demonstrated sustained user retention.

### 6.2 Evaluation Questions

1. What specific user problem does the product solve, and can the founding team articulate the problem from the user's perspective rather than the technology's perspective?
2. What stage of product development has the startup reached — concept, mockup, prototype, beta, live product, or commercially deployed — and is this consistent with the funding stage being evaluated?
3. Is there demonstrable evidence of user engagement with the product, and what do usage metrics (retention rate, DAU/MAU, session length, or equivalent sector-appropriate metrics) reveal?
4. How does the product compare to the alternatives a target user currently employs — including non-digital alternatives — on the dimensions that matter most to that user?
5. What is the core differentiating feature or experience that makes this product meaningfully better than alternatives, and is that differentiation sustainable over 12–24 months?
6. What user research, usability testing, or customer discovery has been conducted, and how has it directly shaped the product roadmap?
7. What is the product's net promoter score, customer satisfaction score, or equivalent qualitative user sentiment signal?
8. What is the current product roadmap, and how does it reflect a prioritisation of user value over internal technical preferences?
9. Is there evidence of iteration — has the product changed meaningfully in response to user feedback, and does the team demonstrate a disciplined approach to deciding what to build?
10. Are there any known product deficiencies, limitations, or user complaints that the team has not yet addressed, and what is the plan to address them?
11. What is the onboarding experience for a new user, and what is the known drop-off point in the user journey?
12. For B2B products: What does the implementation or integration burden look like for a customer, and how does that affect adoption velocity?

### 6.3 Subcriteria

#### 6.3.1 Problem-Solution Fit (PRD-01)
**Measures:** The degree to which the product genuinely and demonstrably addresses the stated user problem. This is assessed by examining evidence that users actually use the product to solve the problem, not merely that the product could theoretically solve it. Survey data, user interviews, and usage analytics all contribute.
**Mapping to Pillar Score:** PRD-01 contributes approximately 28% to the Product pillar score. It is the highest-weighted subcriteria because a product with strong problem-solution fit can recover from quality deficiencies; a product without genuine fit cannot be rescued by any level of technical quality.

#### 6.3.2 Product Maturity and Stage Appropriateness (PRD-02)
**Measures:** The current development stage of the product relative to the funding stage, time since founding, and market stage. A product that is still at the concept stage in a company that has been operating for two years is assessed differently than a product at the same concept stage in a company that was founded six months ago.
**Mapping to Pillar Score:** PRD-02 contributes approximately 22% to the Product pillar score. Stage-appropriateness is a critical lens: the benchmark is not an absolute standard of quality but rather whether the product has progressed appropriately given available resources and time.

#### 6.3.3 User Adoption and Retention Evidence (PRD-03)
**Measures:** Quantitative evidence of how many real users have engaged with the product, how many continue to use it, and at what frequency. For B2B products, this includes customer count, pilot status, expansion within accounts, and Net Revenue Retention. For B2C products, this includes DAU/MAU ratio, session frequency, and churn rate.
**Mapping to Pillar Score:** PRD-03 contributes approximately 22% to the Product pillar score. Adoption and retention data is the most objective signal available for product quality — it captures user voting behaviour rather than stated preferences.

#### 6.3.4 Differentiation and Competitive Position (PRD-04)
**Measures:** How meaningfully the product stands apart from alternatives — including incumbent solutions, other startups, and the status quo (doing nothing or using a workaround). Differentiation must be genuine: a faster UI or slightly lower price is not meaningful differentiation. The subcriteria assesses whether the differentiation is substantial, observable, and defensible.
**Mapping to Pillar Score:** PRD-04 contributes approximately 18% to the Product pillar score. Products that cannot clearly articulate and demonstrate their differentiation are at high risk of commoditisation or being copied by well-resourced incumbents.

#### 6.3.5 Product Development Process Quality (PRD-05)
**Measures:** The quality of how the product is built — not the technical stack, but the process: whether the team has a structured approach to prioritisation, user research integration, release management, and feedback loops. This subcriteria distinguishes teams that build with discipline from teams that build reactively.
**Mapping to Pillar Score:** PRD-05 contributes approximately 10% to the Product pillar score. This subcriteria is weighted lower than others because process quality, while important, is more correctable than the other subcriteria and is not directly visible to users.

### 6.4 Evidence Required

**Primary Evidence (Required):**
- Product demo (live or recorded) showing current functionality
- User metrics: retention data, active user counts, session data, or B2B equivalent
- Customer list or user roster (anonymised where confidential)
- Product roadmap (current version)

**Secondary Evidence (Supporting):**
- User interview transcripts or research summaries
- NPS scores or CSAT survey results
- App store reviews or public user feedback
- Pilot agreement letters or letters of intent from customers
- Competitive analysis prepared by the team
- Changelogs or release notes demonstrating iteration cadence
- Support ticket volumes and resolution times

### 6.5 Red Flags

1. **No user engagement evidence for a live product:** A startup claiming a live product but unable to provide any user engagement metrics — not even anecdotal — suggests either that the product is not genuinely live or that the team is not monitoring usage at all.
2. **Product built without prior user research:** A product that was designed entirely on the founders' assumptions, with no customer discovery, user interviews, or market validation prior to building, is at high risk of solving a problem that does not exist in the form assumed.
3. **Prototype or mockup presented as working product:** A common misrepresentation is presenting a clickable prototype or a heavily staged demo as a functional product. The platform checks for this through questions about technical implementation depth, edge case handling, and integration completeness.
4. **Retention metrics far below sector benchmarks:** A consumer mobile app with a 30-day retention rate below 5% (where the sector benchmark is 10–15%) represents a fundamental product-market fit failure, not a temporary metrics gap.
5. **Product roadmap driven entirely by internal technical preference:** A roadmap that prioritises architectural improvements, technology migrations, or engineering elegance over user-facing value — with no evidence of user input in the prioritisation — suggests a product culture that does not centre on the user.
6. **All positive user feedback and no critical signals:** A startup that presents only positive user testimonials with no evidence of having encountered or acted on critical feedback is either cherry-picking evidence or has not yet gathered it systematically, both of which are concerning.
7. **Dependency on a single enterprise customer for all usage data:** A B2B startup whose entire user evidence base comes from a single pilot customer is not demonstrating product-market fit; it is demonstrating the ability to conduct one pilot, which is a much lower bar.

### 6.6 Scoring Methodology

The Product pillar scoring process begins with the agent establishing the startup's product stage with precision. The stage determines which benchmarks are applicable. A seed-stage company with only a prototype is not expected to have retention data; a Series A company is. Applying inappropriate benchmarks is one of the most common sources of scoring error in this pillar, and the normalisation framework (see Section 4) is especially relevant here.

Once the stage benchmark is established, the agent scores each subcriteria against that benchmark. PRD-01 (Problem-Solution Fit) is evaluated first because it is the most foundational — a product without genuine fit receives a hard ceiling on the overall pillar score, regardless of other subcriteria performance. Specifically, a PRD-01 score below 4 results in a pillar score that cannot exceed 5.5, because the absence of product-market fit is a structural limitation on the entire product assessment.

Red flags are then evaluated. Each confirmed red flag reduces the pillar score by a defined quantum (ranging from 0.3 to 0.8 points per flag), with the severity of the reduction determined by the nature and severity of the red flag. A misrepresentation red flag (prototype presented as live product) carries a more severe reduction than a process maturity red flag (no structured roadmap).

The final pillar score reflects the weighted subcriteria assessment, adjusted for red flag deductions, and bounded by the structural rules described above.

### 6.7 Confidence Calculation

| Evidence Item | Confidence Contribution |
|---|---|
| Live product demo with walkthrough | +25% |
| Verified user metrics (authenticated source) | +20% |
| User research or interview documentation | +15% |
| Customer/user list (verified, even if anonymised) | +15% |
| Product roadmap with prioritisation rationale | +10% |
| NPS or CSAT data with methodology | +10% |
| Release notes or changelogs | +5% |

A product assessment with only a recorded demo and a brief metrics summary should yield approximately 45–55% confidence. Full confidence (85%+) requires verified user metrics, customer documentation, and evidence of user research integration.

### 6.8 Suggested Weight

**Suggested Default Weight: 16%**

The Product pillar receives the second-highest default weight. The product is the vehicle through which all value is delivered; without a viable product, no other pillar can rescue the startup. However, it is weighted slightly below Founder because at the earliest stages, the product is still being built and evaluated, whereas founder quality is a more stable and immediate signal.

Organisations evaluating product-led growth companies or consumer-facing startups may increase the Product weight. Organisations evaluating deep-tech infrastructure startups where the technology platform itself is the primary asset may reduce the Product weight and correspondingly increase Technology and IP weights.

### 6.9 Scoring Examples

**Score: 3/10 (Low)**
The startup shows a polished clickable mockup built in Figma, which the founders refer to as their "app." No actual code has been written, and there are no real users. The pitch deck includes a competitor analysis but no customer discovery interviews are documented. The roadmap is a list of features without prioritisation logic. The stated differentiation — "AI-powered, faster, and more affordable than competitors" — is generic and not substantiated. The stage description (Seed Round) does not match the product maturity (no MVP). Confidence: 30%.

**Score: 6/10 (Moderate)**
The startup has a live Beta product with 340 registered users across three pilot companies. Monthly active user rate is 61% (205/340), which is slightly below the sector benchmark but acceptable given the early stage. Three structured customer interviews are documented and one led directly to a significant product pivot six months ago (abandoning a self-service model in favour of a managed onboarding process). The product roadmap is clearly prioritised with user feedback references. The core differentiation (a proprietary data integration layer that eliminates a manual step competitors require) is real and observable. No NPS data is available yet. Confidence: 68%.

**Score: 9/10 (Exceptional)**
The startup has a commercially deployed SaaS product with 42 paying customers. The 90-day retention rate is 87%, significantly above the sector benchmark of 70%. Net Revenue Retention is 112%, indicating expansion within existing accounts. Three independent user interviews provided to the evaluator contain unsolicited, detailed praise for a specific feature (automated compliance mapping) that no competitor offers. The product roadmap is governed by a formal prioritisation framework documented in Notion, with each item linked to a customer request or usage data insight. The product has shipped 14 notable releases in the past 12 months with documented changelogs. Competitive differentiation is specific, functional, and validated by customer testimony. Confidence: 88%.

---

## 7. Pillar 3: Technology

### 7.1 Purpose

The Technology pillar evaluates the technical foundation of the startup's product and operations. It is distinct from the Product pillar in that it looks beneath the user experience to assess the engineering choices, technical architecture, scalability, and code quality that determine whether the product can grow, adapt, and remain reliable at scale. The Technology pillar is most significant for software, hardware, biotech, deep-tech, and platform companies. It is less significant (but not irrelevant) for service-led businesses where technology is an enabler rather than the core asset.

This pillar answers the question: Is the technical foundation sound enough to support the ambitions of this startup over a 3–5 year horizon without requiring a complete rebuild?

### 7.2 Evaluation Questions

1. What technology stack has the team chosen, and what is the rationale for those choices relative to the specific requirements of the product?
2. Is the architecture designed for scalability — can the system handle 10x or 100x the current load without a fundamental redesign?
3. What is the current state of the codebase: is it well-documented, tested, and structured for team collaboration, or is it a rapid prototype built for speed at the expense of maintainability?
4. Does the startup have a CTO or technical lead with sufficient authority and experience to make and enforce architectural decisions?
5. What is the team's approach to security? Are there documented security policies, access controls, data encryption practices, and vulnerability management processes?
6. What external dependencies does the product have — on third-party APIs, open-source libraries, cloud provider services — and what is the risk if any of those dependencies change materially?
7. Has the product experienced significant technical outages, data loss events, or security incidents, and how were they handled?
8. How is the codebase versioned, reviewed, and deployed? Is there a CI/CD pipeline, and what is the release process?
9. What is the current technical debt profile? Does the team acknowledge it explicitly, and is there a plan to manage it?
10. For AI/ML companies: What is the training data strategy, model evaluation framework, and approach to managing model drift and bias?
11. For hardware companies: What is the current stage of hardware development (prototype, pre-production, or production-ready), and what manufacturing relationships exist?

### 7.3 Subcriteria

#### 7.3.1 Architecture Quality and Scalability (TEC-01)
**Measures:** Whether the system architecture is designed to handle the scale required by the startup's growth projections, and whether the architectural decisions made reflect sound engineering judgment. This includes the appropriateness of the technology stack, the use of scalable cloud infrastructure, the separation of concerns in the system design, and the presence of load management, caching, and data architecture planning.
**Mapping to Pillar Score:** TEC-01 contributes approximately 28% to the Technology pillar score. Architecture quality is the most consequential technical dimension because it determines the cost and feasibility of scaling.

#### 7.3.2 Technical Team Competence (TEC-02)
**Measures:** The depth and breadth of the technical team's skills relative to what the product requires. This includes the seniority and experience of the technical lead, the coverage of key technical disciplines (frontend, backend, data/ML, infrastructure, security), and whether the team has the capacity to handle the planned technical roadmap.
**Mapping to Pillar Score:** TEC-02 contributes approximately 25% to the Technology pillar score. A technically brilliant architecture designed by a team that lacks the skills to execute it is not a strong position.

#### 7.3.3 Code Quality and Engineering Practices (TEC-03)
**Measures:** The quality of engineering practices in place: code review processes, automated testing coverage, documentation, version control discipline, and deployment practices. These practices determine whether the codebase can be safely extended by new team members and whether new features can be shipped without disproportionate risk of regressions.
**Mapping to Pillar Score:** TEC-03 contributes approximately 20% to the Technology pillar score. Poor code quality is a significant long-term liability, particularly for startups planning to scale their engineering team.

#### 7.3.4 Security and Data Governance (TEC-04)
**Measures:** Whether the startup has implemented appropriate security controls for its product and data assets. This includes data encryption at rest and in transit, access control policies, compliance with relevant data protection regulations (GDPR, HIPAA, etc.), documented incident response procedures, and regular security assessment.
**Mapping to Pillar Score:** TEC-04 contributes approximately 15% to the Technology pillar score. Security gaps are increasingly a commercial and regulatory liability, and for enterprise B2B startups, security posture is often a formal procurement requirement.

#### 7.3.5 Technical Debt and Dependency Risk (TEC-05)
**Measures:** The extent to which the current technical implementation carries debt (shortcuts, undocumented systems, deprecated dependencies, brittle integrations) and the degree to which the startup is exposed to risks from external technical dependencies that it does not control.
**Mapping to Pillar Score:** TEC-05 contributes approximately 12% to the Technology pillar score. Some technical debt is normal and expected in early-stage startups; the question is whether it is acknowledged, managed, and has a clear resolution path.

### 7.4 Evidence Required

**Primary Evidence (Required):**
- Technical architecture overview or system design document
- Technology stack description (languages, frameworks, cloud services)
- Technical team CVs/GitHub profiles or portfolio evidence

**Secondary Evidence (Supporting):**
- Code repository access or structured code review output
- CI/CD pipeline configuration or deployment frequency data
- Security audit report or penetration test results
- Uptime and incident history data
- API documentation (for platform products)
- Third-party dependency manifest

### 7.5 Red Flags

1. **No dedicated technical leadership:** A startup beyond the prototype stage with no CTO or equivalent technical decision-maker — particularly one where the product is the core asset — is at high risk of accumulating unchecked technical debt or making catastrophic architectural decisions.
2. **Entire codebase written by one person with no version control discipline:** A sole technical contributor with no documentation, no code review, and no version control history represents an extreme key-person and bus-factor risk.
3. **Critical security gaps in a regulated data environment:** A startup handling sensitive data (financial, health, personal) without demonstrable encryption, access controls, and documented data handling procedures has an existential compliance and liability exposure.
4. **Over-reliance on a single third-party service with no fallback:** Products built on a single cloud provider, a single payment processor, or a single AI API with no abstraction layer or fallback plan are operationally fragile and commercially vulnerable to pricing or policy changes.
5. **Prototype-quality code in a commercially deployed product:** If a code review or technical discussion reveals that the production codebase is essentially a proof-of-concept that was never refactored for reliability, this represents a significant scalability and reliability risk.
6. **AI/ML product with no model evaluation framework:** An AI-powered product that cannot describe how it measures the performance of its models, how it detects model drift, or how it handles edge cases and bias represents an AI quality governance failure.
7. **Hardware startup with no manufacturing relationship or supply chain plan:** A hardware company still at the prototype stage without any engagement with contract manufacturers, component suppliers, or regulatory certification bodies is significantly behind the expected development trajectory.

### 7.6 Scoring Methodology

The Technology pillar scoring is conducted by an agent with access to technical documentation provided by the startup and, where available, structured input from a human technical reviewer. The agent cannot independently verify claims about code quality without code access; where code access is not provided, TEC-03 and TEC-05 confidence is automatically capped.

The scoring process first establishes the technology type context: software SaaS, mobile app, hardware, deep-tech/research, platform API, AI/ML, or hybrid. This context determines which subcriteria receive elevated importance and which benchmarks apply.

TEC-01 (Architecture) is evaluated against the startup's own stated scale requirements — not against absolute standards. An architecture that cannot handle one million concurrent users is not penalised if the startup's three-year target does not require that scale. The question is whether the architecture can handle the scale the startup itself is planning for.

TEC-04 (Security) is evaluated against the regulatory environment of the sector. A consumer gaming startup is held to a different security standard than a fintech or healthtech startup. The sector normalisation framework applies here.

### 7.7 Confidence Calculation

| Evidence Item | Confidence Contribution |
|---|---|
| Architecture document or system design review | +25% |
| Technical team CV with verifiable background | +20% |
| Code repository access or structured code review | +20% |
| Security documentation or audit report | +15% |
| Deployment pipeline and release process description | +10% |
| Dependency manifest or third-party service list | +10% |

Without code repository access, the maximum achievable confidence for this pillar is approximately 65%. Organisations requiring high-confidence Technology assessments must configure their intake process to require repository access or a structured technical review.

### 7.8 Suggested Weight

**Suggested Default Weight: 14%**

Technology receives a substantial default weight, reflecting the reality that for the majority of startups evaluated by the TIDES platform, technology is either the core product or a critical enabler. However, it is weighted below Founder and Product because technical quality, while important, is the dimension most amenable to improvement with capital — an investor can fund the hiring of a CTO or a system refactor. Team quality and product-market fit are less directly purchasable.

Deep-tech, hardware, and AI/ML companies should consider increasing the Technology weight to 18–22% in their organisation or sector weight configurations.

### 7.9 Scoring Examples

**Score: 3/10 (Low)**
The startup's technology consists of a WordPress website with a custom plugin handling transactions. The technical "co-founder" has 18 months of frontend development experience and no backend or infrastructure background. The system has no test coverage, no version control history (the team uses email to share code files), and customer data is stored in an unencrypted local database. No deployment process exists — changes are made directly to the production server via FTP. Security posture is non-existent. Confidence: 42% (no architecture document, no formal technical review).

**Score: 6/10 (Moderate)**
The startup has a microservices architecture hosted on AWS, using Python/FastAPI for the backend and React for the frontend. The CTO has six years of backend engineering experience. There is a basic CI/CD pipeline using GitHub Actions, and all features go through code review before merging. Test coverage is approximately 40% (below the desired 70% but adequate for the current stage). Security practices include HTTPS encryption and basic IAM controls, but no formal security audit has been conducted. The team acknowledges a significant technical debt item (a legacy data import module) and has scheduled a refactoring sprint. Confidence: 67%.

**Score: 9/10 (Exceptional)**
The startup's platform is built on a Kubernetes-based microservices architecture with automated horizontal scaling. The engineering team of eight includes three senior engineers with prior experience at scale. Test coverage is 78%, all production deployments go through a staging environment and automated regression suite, and the system achieved 99.97% uptime over the past 12 months. A SOC 2 Type II audit was completed nine months ago and the resulting certification is held. The CTO has 14 years of engineering experience and has previously scaled a platform to 10M+ users. The team maintains a public API with comprehensive documentation and a formal SLA for enterprise customers. Technical debt is explicitly tracked in a dedicated board with quarterly review. Confidence: 89%.

---

## 8. Pillar 4: Market

### 8.1 Purpose

The Market pillar evaluates the startup's understanding of the market it is entering, the size and accessibility of that market, and the dynamics that will shape its growth potential. A startup with a brilliant product and exceptional team can fail if it is addressing a market that is too small, too difficult to penetrate, too fragmented, or already dominated by entrenched incumbents with structural advantages.

This pillar also evaluates the quality of the startup's market analysis — not just the numbers they present, but the methodology behind those numbers and the sophistication with which the team understands the competitive dynamics they face. A team that can cite market size figures from analyst reports but cannot explain the mechanics of how they will capture share has not demonstrated real market understanding.

### 8.2 Evaluation Questions

1. What is the startup's definition of its target market, and is it specific and realistic (a defined addressable segment) rather than a generic reference to a large global industry?
2. How is the market size calculated — what methodology was used, and what assumptions underlie the TAM/SAM/SOM figures? Have these figures been independently substantiated or are they derived solely from third-party analyst estimates?
3. What is the current growth rate of the target market, and what are the structural drivers of that growth? Is the market growing due to fundamental demand drivers or due to short-term hype?
4. Who are the current market leaders, and what are their specific advantages and vulnerabilities? How does the startup plan to compete against or work around incumbent advantages?
5. What barriers to entry protect this market from new entrants, and how does the startup plan to navigate or leverage those barriers?
6. Is there evidence of near-term market timing advantage — a regulatory change, technology shift, or macroeconomic trend that creates a window for entry that did not exist previously?
7. What is the startup's plan for acquiring its first 100 customers, and what is the estimated cost of acquiring those customers relative to the expected revenue?
8. What customer segments has the startup validated through direct engagement, and how does customer feedback confirm or challenge the market size assumptions?
9. What is the competitive intensity of the market — how many direct competitors exist, what is their funding level, and what are the known switching costs in the market?
10. Are there regulatory, geographic, or structural barriers that would prevent the startup from expanding beyond its initial target segment?

### 8.3 Subcriteria

#### 8.3.1 Market Size and Accessibility (MKT-01)
**Measures:** Whether the target market is large enough to support the startup's stated ambitions, and whether that market is realistically accessible given the startup's resources and approach. This subcriteria evaluates the quality of the TAM/SAM/SOM analysis and the realism of the addressable market definition.
**Mapping to Pillar Score:** MKT-01 contributes approximately 26% to the Market pillar score. Market size is a fundamental constraint on the investment case — a startup cannot grow into a venture-scale company if the total addressable market cannot support venture-scale revenue.

#### 8.3.2 Market Growth and Timing (MKT-02)
**Measures:** The rate at which the target market is growing and whether the startup is positioned to benefit from structural growth drivers. This subcriteria also evaluates timing — whether the startup is entering the market at the right moment, ahead of the growth curve, or behind it.
**Mapping to Pillar Score:** MKT-02 contributes approximately 22% to the Market pillar score. A startup entering a shrinking or stagnant market faces structural headwinds regardless of product quality. Conversely, a startup riding a structural growth wave has tailwinds that can compensate for operational imperfections.

#### 8.3.3 Competitive Landscape Understanding (MKT-03)
**Measures:** The depth and accuracy of the team's understanding of the competitive environment. This is not just about listing competitors; it is about demonstrating an accurate understanding of competitor strengths, weaknesses, strategies, and the specific dynamics of how competition plays out in this market.
**Mapping to Pillar Score:** MKT-03 contributes approximately 22% to the Market pillar score. Teams that underestimate their competition or mischaracterise competitive dynamics are at high risk of strategic errors when they actually enter the market.

#### 8.3.4 Customer Segment Validation (MKT-04)
**Measures:** Whether the startup has directly engaged with its target customer segments and gathered evidence that validates (or challenges) its market assumptions. This is distinct from product validation — it measures whether the market analysis is grounded in real customer intelligence rather than desk research alone.
**Mapping to Pillar Score:** MKT-04 contributes approximately 18% to the Market pillar score. Market analysis built on direct customer intelligence is materially more reliable than analysis built on secondary sources alone.

#### 8.3.5 Go-to-Market Realism (MKT-05)
**Measures:** Whether the startup's go-to-market plan is grounded in a realistic understanding of how customers in this market actually make buying decisions, what channels are effective, and what the cost and timeline of customer acquisition realistically looks like.
**Mapping to Pillar Score:** MKT-05 contributes approximately 12% to the Market pillar score. Even a correct market size analysis is commercially useless if the path to market is unrealistic.

### 8.4 Evidence Required

**Primary Evidence (Required):**
- TAM/SAM/SOM analysis with methodology documentation
- Competitive landscape overview identifying at least five direct or indirect competitors
- Evidence of direct customer engagement (interviews, surveys, pilot agreements)

**Secondary Evidence (Supporting):**
- Industry analyst reports (Gartner, IDC, IBISWorld, or sector-specific equivalents)
- Market growth data from government or trade association sources
- Customer personas developed from primary research
- Channel partner agreements or expressions of interest
- Win/loss analysis from competitive sales situations

### 8.5 Red Flags

1. **TAM calculated as a percentage of a global industry with no segment definition:** "The global healthcare market is $10 trillion; we need only 0.1% of it" is not a market analysis. It reveals that the team has not defined who their actual customer is.
2. **No direct competitor acknowledged:** A startup that claims to have no direct competitors either has not done its research or is defining its category so narrowly that it is misleading. Every market has alternatives; the relevant question is the nature of those alternatives.
3. **Market timing argument entirely dependent on trend continuation:** A market thesis that relies entirely on a technology trend (e.g., AI adoption, blockchain, etc.) without a structural demand-side driver is fragile and subject to rapid reversal.
4. **Customer discovery based entirely on the founders' network:** Customer interviews with friends, former colleagues, and family members are not market validation. If the entire customer discovery base consists of people who are predisposed to be supportive, the market analysis is unreliable.
5. **Ignoring a dominant incumbent with network effects or regulatory moats:** A competitive analysis that dismisses a well-funded incumbent with established network effects or regulatory barriers without a specific, credible strategy for working around or displacing them represents a material analytical failure.
6. **Serviceable market that requires immediate national or international scale to be viable:** A startup whose unit economics only work at very large scale (requiring millions of users or customers), but which has no credible path to that scale within a reasonable timeframe, has a market access problem that makes the stated SAM unrealistic.
7. **Go-to-market plan that relies on viral growth with no basis for the assumption:** Assuming viral growth or word-of-mouth as the primary acquisition channel without any evidence of organic referral behaviour in early users is a common and dangerous planning error.

### 8.6 Scoring Methodology

The Market pillar scoring begins with a systematic evaluation of the market analysis methodology. The agent does not simply accept the numbers in the pitch deck; it evaluates the methodology used to arrive at those numbers. A bottom-up market sizing (estimating the number of target customers multiplied by expected revenue per customer) is significantly more credible than a top-down sizing (taking a percentage of a large market figure), and this is reflected in the confidence weighting applied.

Competitive landscape understanding (MKT-03) is evaluated by examining whether the startup has identified the correct competitors. Agents are configured with sector-specific knowledge bases that allow them to identify significant competitors that the startup may have omitted, and omissions are noted in the assessment.

The scoring agent applies a timing assessment that considers the trajectory of the market, not just its current state. A market that was growing rapidly but is showing signs of saturation or competitive maturity is assessed differently than one that is at an early growth stage.

### 8.7 Confidence Calculation

| Evidence Item | Confidence Contribution |
|---|---|
| Bottom-up TAM/SAM/SOM with documented methodology | +25% |
| Directly cited analyst or government market data | +20% |
| Direct customer engagement evidence (interviews/pilots) | +20% |
| Named competitive landscape with factual descriptions | +15% |
| Go-to-market plan with channel and CAC data | +10% |
| Win/loss or comparative analysis | +10% |

Market pillar confidence is particularly sensitive to the quality of market sizing methodology. A purely top-down analysis with no primary research should yield confidence no higher than 50%.

### 8.8 Suggested Weight

**Suggested Default Weight: 14%**

Market is weighted equally with Technology in the default configuration. The market defines the theoretical ceiling on the startup's potential, and a startup pursuing a poorly understood or structurally unfavourable market faces challenges that no amount of product quality or team capability can overcome.

Organisations evaluating startups at the growth stage may increase Market weight, as market dynamics are more immediately relevant to growth-stage decisions. Accelerators focused on technically innovative early-stage companies may temporarily reduce Market weight in early cohort evaluations, recognising that market analysis matures significantly during the accelerator programme.

### 8.9 Scoring Examples

**Score: 3/10 (Low)**
The startup presents a TAM of $500 billion for "the global logistics market" and claims a 0.1% target share worth $500 million, with no definition of which segment, customer type, geography, or use case they are addressing. The competitive landscape slide lists three large companies (all public corporations) and states they are not real competitors because "they don't focus on our niche" — but the niche is not defined. No customer interviews are documented; the founders say they "know the market" from prior employment. The go-to-market plan says "we will use LinkedIn and industry events." Confidence: 25%.

**Score: 6/10 (Moderate)**
The startup presents a bottom-up TAM calculation based on the number of mid-market manufacturing companies in their target geography (3,400 companies), an estimated 30% addressable rate, and a $28,000 annual contract value, yielding a SAM of $28.6 million. The methodology is sound. They have identified six direct competitors, including two well-funded ones, with a reasonably accurate description of competitive positioning. Customer discovery includes 22 interviews with actual procurement managers at manufacturing companies. The go-to-market plan relies on a channel partnership with an ERP reseller network, which is realistic but unvalidated by any signed agreement. Confidence: 65%.

**Score: 9/10 (Exceptional)**
The startup operates in the legal tech space and provides a granular market analysis showing 18,200 law firms in their target geography with between 10 and 200 employees, of which they estimate 7,400 as their addressable segment based on defined criteria. Their SAM of $133 million is conservative and uses a bottoms-up model cross-validated against two independent analyst reports. They have conducted 64 documented customer interviews, identified twelve direct competitors with a detailed feature and pricing comparison, and have signed referral agreements with two bar association networks. Their competitive moat — a proprietary database of legal precedent built over two years — is a genuine barrier to replication. The go-to-market plan includes actual CAC data from their 90-day pilot acquisition campaign ($1,200 per customer), which validates the channel economics. Confidence: 91%.

---

## 9. Pillar 5: Business Model

### 9.1 Purpose

The Business Model pillar evaluates how the startup creates, delivers, and captures value economically. A startup may have an exceptional product and a large market but still fail to build a sustainable business if its model for generating revenue does not create defensible unit economics, does not scale with reasonable efficiency, and does not align incentives between the company and its customers over time.

This pillar assesses the clarity and coherence of the business model, the health of the unit economics, the revenue structure, the scalability of the model, and the alignment between the stated business model and the actual commercial evidence available.

### 9.2 Evaluation Questions

1. What is the core revenue mechanism — how does the startup make money for each unit of value it delivers?
2. What are the current unit economics? What is the Customer Acquisition Cost (CAC), the Lifetime Value (LTV), the LTV:CAC ratio, and the payback period?
3. What is the pricing strategy, and how was the price point determined? Is it based on competitive benchmarking, value-based pricing, or cost-plus pricing?
4. How does the business model scale — does margin improve as the business grows, or does it require proportional cost increases to sustain revenue growth?
5. What is the revenue mix — is the startup dependent on a single revenue stream, or does it have diversified revenue sources with different risk profiles?
6. What are the key assumptions underlying the business model, and how sensitive is the model to changes in those assumptions (e.g., a 20% reduction in conversion rate or a 15% increase in customer churn)?
7. Does the startup have recurring revenue, and if so, what is the gross churn rate?
8. Are the current pricing and model consistent with what similar companies charge in the sector, and if there is a significant deviation, what justifies it?
9. What are the key cost drivers in the business, and how are they structured (fixed vs. variable)?
10. How does the business model handle customers at different segments — does it have tiered pricing or segment-specific models?
11. What is the path to profitability — at what revenue level does the startup expect to reach breakeven, and what assumptions drive that calculation?

### 9.3 Subcriteria

#### 9.3.1 Revenue Model Clarity and Coherence (BIZ-01)
**Measures:** Whether the startup has a clearly defined, coherent revenue model that is logically consistent with the product, customer, and market. A coherent revenue model is one where the mechanism of value capture aligns with the mechanism of value delivery, and where the pricing structure makes sense to the buyer.
**Mapping to Pillar Score:** BIZ-01 contributes approximately 22% to the Business Model pillar score.

#### 9.3.2 Unit Economics Health (BIZ-02)
**Measures:** The financial health of the fundamental unit transaction of the business. For most startups this involves LTV:CAC ratio (a ratio above 3:1 is generally considered healthy), payback period (ideally under 18 months for SaaS), gross margin at the unit level, and contribution margin. Where the startup is pre-revenue, this subcriteria is assessed against the modelled unit economics and their credibility.
**Mapping to Pillar Score:** BIZ-02 contributes approximately 28% to the Business Model pillar score. Unit economics are the most diagnostic financial signal for business model health.

#### 9.3.3 Scalability of the Model (BIZ-03)
**Measures:** Whether the business model improves economically as it scales. A scalable model is one where marginal revenue grows faster than marginal cost. Models requiring linear headcount growth to deliver linear revenue (e.g., a professional services model without a product component) are less scalable than platform models where software serves additional customers with near-zero marginal cost.
**Mapping to Pillar Score:** BIZ-03 contributes approximately 22% to the Business Model pillar score.

#### 9.3.4 Revenue Defensibility and Retention (BIZ-04)
**Measures:** How sticky the startup's revenue is — specifically, whether customers continue to use and pay for the product over time, and whether the product creates meaningful switching costs or lock-in. Recurring revenue models with high retention are significantly more defensible than one-time or transactional models with high churn.
**Mapping to Pillar Score:** BIZ-04 contributes approximately 16% to the Business Model pillar score.

#### 9.3.5 Business Model Assumptions Realism (BIZ-05)
**Measures:** Whether the assumptions underpinning the financial model and business projections are realistic and internally consistent. This includes growth rate assumptions, conversion rate assumptions, churn assumptions, and cost assumptions — evaluated against sector benchmarks and the startup's own early evidence.
**Mapping to Pillar Score:** BIZ-05 contributes approximately 12% to the Business Model pillar score.

### 9.4 Evidence Required

**Primary Evidence (Required):**
- Revenue model description (how the startup makes money)
- Financial model or projection with stated assumptions
- Unit economics data (CAC, LTV, gross margin — actual or modelled)

**Secondary Evidence (Supporting):**
- Pricing documentation or pricing page
- Customer contract or subscription data showing retention
- Revenue breakdown by customer or segment
- Comparable company benchmarks the startup has used in modelling
- Investor materials containing financial projections

### 9.5 Red Flags

1. **No defined pricing at the time of customer acquisition:** A startup actively selling to customers with no defined price list, relying entirely on custom negotiation for every deal, has not yet found its commercial model and faces severe scalability challenges.
2. **LTV:CAC ratio below 1:1 with no credible path to improvement:** A unit economics model where the customer acquisition cost exceeds the lifetime value from that customer represents a fundamentally broken business model, not a growth problem.
3. **Revenue entirely dependent on one or two anchor customers:** If more than 40% of total revenue comes from a single customer, the revenue quality is poor and the business faces existential risk if that customer churns.
4. **Business model projections that assume hypergrowth with no basis:** A financial model showing 500% year-over-year revenue growth in years 2–3 with no mechanism for achieving that growth (no sales hiring plan, no channel strategy, no product expansion) is a fantasy model.
5. **Gross margin below sector sustainability threshold without a credible improvement path:** For SaaS businesses, gross margins below 50% (sector norm is 70–80%) represent a structural cost problem. For marketplace businesses, take rates that leave insufficient margin for growth investment indicate a model that cannot self-fund.
6. **Business model that has changed fundamentally more than twice in the past 18 months:** While pivoting is normal, a startup that has changed its core revenue model more than twice in less than two years suggests the team has not found clarity on how to monetise its product, which is a significant risk.
7. **Pricing set arbitrarily without reference to customer willingness to pay:** Founders who set prices based on cost-plus reasoning or competitive copying, without any evidence of having tested willingness to pay with actual customers, have an unvalidated pricing assumption that is likely to create commercial friction.

### 9.6 Scoring Methodology

The Business Model pillar scoring prioritises evidence over assertion. When actual financial data is available (real CAC, real LTV, real churn), the agent uses it directly. When the startup is pre-revenue and only modelled data is available, the agent evaluates the quality of the modelling rather than the numbers themselves: are the assumptions stated explicitly, are they benchmarked against comparable companies, and do they form an internally consistent model?

BIZ-02 (Unit Economics) is the most weighted subcriteria and acts as a gate on the pillar score. A startup with fundamentally broken unit economics (LTV:CAC below 1:1 based on actual data, not projections) receives a pillar score that cannot exceed 4.5, because regardless of how clearly the model is articulated or how defensible the revenue is, the model cannot sustain growth.

The scoring agent also evaluates the consistency between the stated business model and the financial model — a common source of error is a pitch deck that describes a SaaS subscription model while the financial model shows one-time implementation fees as the majority of revenue.

### 9.7 Confidence Calculation

| Evidence Item | Confidence Contribution |
|---|---|
| Actual revenue data (real transactions) | +30% |
| Documented unit economics with source data | +25% |
| Financial model with stated assumptions | +20% |
| Pricing documentation | +10% |
| Customer retention or churn data | +10% |
| Comparable company benchmarking | +5% |

Pre-revenue startups with no actual financial data are capped at 45% confidence for this pillar regardless of the quality of their financial modelling. This is appropriate, because modelled unit economics are inherently uncertain.

### 9.8 Suggested Weight

**Suggested Default Weight: 12%**

The Business Model pillar receives a moderate default weight. Business model clarity is critically important but is also the pillar most likely to evolve during the company's early life. For very early-stage evaluations, a lower weight is appropriate because the model is still being validated. For later-stage evaluations, this weight should increase significantly.

Organisations using TIDES to evaluate revenue-stage or growth-stage companies should increase Business Model weight to 16–20% and correspondingly reduce Founder or Technology weight to reflect the stage shift.

### 9.9 Scoring Examples

**Score: 3/10 (Low)**
The startup has been operating for 14 months and has still not defined a pricing model — it has been running its service for free "to acquire users" with no stated point at which monetisation will begin. The founders vaguely reference a "freemium model" but cannot describe the trigger or limit that would move a user to a paid tier. The financial model shows revenue appearing in Year 2 with no explanation of how it is generated. Gross margin is estimated at 30% "because we'll have some costs." No comparable companies have been studied. Confidence: 30%.

**Score: 6/10 (Moderate)**
The startup has a clear subscription pricing model ($299/month/seat for SMEs, custom enterprise pricing). CAC from its marketing experiments is $1,800. LTV assuming 24-month average contract life and 15% annual churn is $6,480, giving a 3.6:1 LTV:CAC ratio and a 10-month payback period — both within acceptable ranges for the sector. Gross margin is 62%, which is slightly below SaaS norms but improving as infrastructure costs amortise. Revenue is recurring and no single customer represents more than 8% of ARR. The main weakness is that the growth projections for year 3 assume a sales team of 12 but the current hiring plan only supports 6. Confidence: 70%.

**Score: 9/10 (Exceptional)**
The startup operates a B2B SaaS platform with a clearly tiered pricing structure ($599/$1,199/$2,499/month). Real CAC from the past 12 months of paid marketing and sales activity is $2,200. Real LTV based on actual cohort analysis across 24 months is $18,700 (8.5:1 ratio). Gross margin on software is 78% with a 7-month payback period. Net Revenue Retention is 118%, meaning the revenue base expands organically without new customer acquisition. The financial model is detailed, with stated assumptions cross-referenced to industry benchmarks and a sensitivity table showing the impact of +/- 10% variation in key assumptions. Revenue is distributed across 61 paying customers with the top customer representing 4% of ARR. Confidence: 87%.

---

## 10. Pillar 6: Financial

### 10.1 Purpose

The Financial pillar evaluates the startup's current financial position, the quality of its financial management, its fundraising history and use of capital, and the credibility of its financial projections. It is distinct from the Business Model pillar: where Business Model evaluates the structural health of how the company makes money, the Financial pillar evaluates the current state of the balance sheet, the historical and projected cash flows, and the discipline with which capital has been deployed.

For very early-stage startups, this pillar primarily assesses financial hygiene and fundraising credibility. For growth-stage startups, it assesses whether the company is building toward sustainable financial performance and whether capital efficiency is improving over time.

### 10.2 Evaluation Questions

1. What is the startup's current cash position and monthly burn rate, and what is the runway in months at the current burn rate?
2. What is the startup's current revenue run rate (ARR or MRR), and what is the month-over-month or quarter-over-quarter revenue growth rate?
3. What is the history of capital raised — how much has been raised in each round, from whom, at what valuation, and when?
4. How has capital been deployed? What proportion has gone to product development, team building, sales and marketing, and operations?
5. Are the startup's accounts formally maintained and up-to-date? Has the company completed statutory filings, and are financial records available for review?
6. What is the startup's gross burn versus net burn, and how does this reflect the company's revenue progress?
7. What are the key financial milestones the company needs to achieve before it will reach profitability or its next funding event, and are these milestones credible given current trajectory?
8. Are there any outstanding liabilities, debt instruments, convertible notes, or SAFEs that would materially affect the cap table or the next round valuation?
9. What is the current valuation expectation for the funding round being evaluated, and how is it justified relative to comparable company valuations and current traction?
10. Has the company ever missed payroll, had a payment default, or experienced a significant financial control failure?

### 10.3 Subcriteria

#### 10.3.1 Financial Health and Runway (FIN-01)
**Measures:** The current state of the startup's balance sheet — specifically cash on hand, monthly burn rate, and the resulting operational runway. A startup with less than six months of runway faces acute operational risk. A startup with 18+ months of runway has the freedom to execute without imminent capital pressure.
**Mapping to Pillar Score:** FIN-01 contributes approximately 25% to the Financial pillar score.

#### 10.3.2 Revenue Quality and Growth Trajectory (FIN-02)
**Measures:** The quality of current revenue (recurring vs. one-time, diversified vs. concentrated, contracted vs. at-risk) and the trajectory of revenue growth relative to sector benchmarks. Rapid, consistent month-over-month growth from a diversified customer base is higher quality than lumpy, concentrated one-time revenue.
**Mapping to Pillar Score:** FIN-02 contributes approximately 28% to the Financial pillar score. Revenue quality is the most forward-looking signal in the Financial pillar.

#### 10.3.3 Capital Efficiency (FIN-03)
**Measures:** How effectively the startup has deployed the capital it has raised. This includes comparing revenue generated against total capital raised (capital efficiency ratio), assessing whether the burn rate is appropriate for the stage and growth trajectory, and evaluating whether there is evidence of financial discipline in how money has been spent.
**Mapping to Pillar Score:** FIN-03 contributes approximately 22% to the Financial pillar score.

#### 10.3.4 Financial Management Quality (FIN-04)
**Measures:** The quality of the financial management infrastructure: whether the company maintains accurate, up-to-date accounts; whether it has completed statutory filings; whether it has a CFO or finance lead; and whether financial reporting is structured and reliable.
**Mapping to Pillar Score:** FIN-04 contributes approximately 13% to the Financial pillar score. Poor financial management is an investability barrier, particularly for institutional investors.

#### 10.3.5 Fundraising Credibility and Cap Table Health (FIN-05)
**Measures:** Whether the current fundraising round is appropriately priced, whether the cap table is clean and investor-friendly, and whether any instruments (convertible notes, SAFEs, outstanding options) have been fully disclosed and would not create problematic dilution scenarios at the next round.
**Mapping to Pillar Score:** FIN-05 contributes approximately 12% to the Financial pillar score.

### 10.4 Evidence Required

**Primary Evidence (Required):**
- Current financial statements or management accounts (P&L, balance sheet, cash flow)
- Bank statement or cash position confirmation
- Cap table with all current and pending instruments

**Secondary Evidence (Supporting):**
- Prior round term sheets or investment agreements (summary)
- Revenue recognition policy
- Monthly MRR/ARR tracking spreadsheet
- Statutory filings or incorporation accounts
- Any existing debt or credit facility documentation
- Investor-ready financial model with 36-month projection

### 10.5 Red Flags

1. **Runway below six months with no clear path to additional capital:** A startup with less than six months of runway and no advanced fundraising conversations or revenue events that would extend runway is in distress mode, regardless of how the pitch framing presents it.
2. **Financial statements that do not reconcile with stated metrics:** If the P&L submitted shows materially different revenue numbers than the pitch deck claims, this is either an accounting error or misrepresentation — both are serious.
3. **Significant capital raised with minimal product progress:** A startup that has raised $1.5M and has only a prototype to show for it, with most capital consumed by founder salaries and marketing, has poor capital efficiency that raises questions about resource allocation discipline.
4. **Cap table issues: excessive founder dilution at early stage:** Founders who are already below 50% equity after a seed round face motivation and governance challenges that can complicate future fundraising and company management.
5. **Unresolved convertible notes with aggressive caps or uncapped structures:** Uncapped convertible notes or SAFE agreements with highly aggressive terms outstanding at the time of a new round can create unexpected and significant dilution that materially changes the economics of the new round.
6. **No engagement of a qualified accountant or bookkeeper:** A startup that has been operating for more than 12 months with no professional financial management — relying entirely on founder self-accounting — has significant compliance and data reliability risk.
7. **Revenue projections that are disconnected from operational capacity:** A financial model showing $5M ARR in 18 months at a startup currently generating $50K ARR with a five-person team and no planned hiring describes an impossible growth path.

### 10.6 Scoring Methodology

Financial pillar scoring applies sector normalisation most aggressively, because financial benchmarks vary enormously by sector, stage, and geography. A SaaS company at Seed with $0 revenue is at a very different position than a logistics company at Seed with $0 revenue, because the expectation and norm for revenue at seed stage differs significantly between sectors.

The agent evaluates financial evidence with a higher threshold for verification than other pillars. Financial claims in pitch materials are treated as assertions until supported by primary financial documentation. When primary documentation is provided, the agent cross-validates key figures: revenue figures in the P&L should match the MRR tracker; cash figures in the P&L should match the balance sheet and bank statement; fundraising history in the cap table should match stated round history.

FIN-02 (Revenue Quality) is the primary forward-looking signal and receives the highest subcriteria weight. A startup with modest revenue but a consistent 20% month-over-month growth trajectory and strong revenue quality receives a higher score than a startup with higher revenue but declining growth and high customer concentration.

### 10.7 Confidence Calculation

| Evidence Item | Confidence Contribution |
|---|---|
| Formal financial statements (audited or management accounts) | +30% |
| Bank statement or cash position verification | +20% |
| MRR/ARR tracker with monthly data | +20% |
| Cap table with all instruments | +15% |
| Prior round documentation | +10% |
| Financial model with stated assumptions | +5% |

Financial confidence without formal financial statements is capped at 50%. Without a verified bank statement or cash position, confidence is further capped at 40%. The Financial pillar has the most aggressive confidence penalties for missing primary evidence because the financial claims in this pillar are objectively verifiable and the absence of verification is itself informative.

### 10.8 Suggested Weight

**Suggested Default Weight: 10%**

The Financial pillar carries a moderate-to-lower default weight in the general TIDES configuration because the platform is primarily designed for early-stage evaluation where financial data is limited. A seed-stage startup with six months of operations cannot produce the financial evidence that a Series B company can, and penalising it heavily on this pillar would produce a systematically unfair evaluation for early-stage companies.

Organisations using TIDES to evaluate later-stage companies (Series A and beyond) should increase the Financial pillar weight to 15–18% and apply more demanding financial evidence requirements via their intake configuration.

### 10.9 Scoring Examples

**Score: 3/10 (Low)**
The startup has raised $400K in a friends-and-family round 20 months ago. Current bank balance is $28,000 — representing less than three weeks of runway at the current $40,000/month burn rate. Revenue is zero. The founders have been drawing $6,500/month each in salary from the raised capital. No formal accounts exist; the financial "model" is a spreadsheet with revenue appearing in month 4 with no explanatory formula. The cap table has a $1.2M uncapped convertible note from an angel investor that was not disclosed in the initial intake. Confidence: 33%.

**Score: 6/10 (Moderate)**
The startup has raised $1.2M in a Seed round 11 months ago. Current MRR is $22,000 (ARR $264,000), growing at approximately 15% month-over-month over the past four months. Runway at current burn ($95,000/month, net burn $73,000) is approximately 14 months. Management accounts are maintained by a part-time bookkeeper and are current to the prior month. Cap table is clean with no outstanding convertible instruments. Revenue is distributed across 19 paying customers with no single customer above 15% of ARR. Financial model projections for the next 18 months appear achievable based on current growth trajectory, though the model does not include a sensitivity analysis. Confidence: 68%.

**Score: 9/10 (Exceptional)**
The startup raised a $3M Series A 16 months ago. Current ARR is $1.8M, having grown from $400K ARR at the time of the Series A (4.5x growth). Monthly net burn is $130,000, giving runway of 22 months. The company has been audited by a Big 4 affiliate firm as required by the lead investor. Net Revenue Retention is 121%. The cap table is clean, with fully vested founder equity and a standard ESOP pool. The CFO (appointed 8 months ago, previously VP Finance at a unicorn) has implemented a monthly Board reporting package including P&L, cash flow, unit economics dashboard, and updated 18-month projection. The projected path to breakeven at $3.2M ARR (approximately 14 months away) is supported by current growth trajectory and a credible sales hiring plan. Confidence: 93%.

---

## 11. Pillar 7: IP (Intellectual Property)

### 11.1 Purpose

The IP pillar evaluates the startup's intellectual property position — the legal, technical, and strategic assets that create barriers to competitive replication and form the basis of long-term defensibility. IP assets include patents, trade secrets, proprietary data, copyrights, trademarks, and know-how that is meaningfully difficult for a competitor to replicate.

This pillar is most significant for deep-tech, pharmaceutical, biotech, hardware, and platform startups where IP forms a structural competitive moat. It is less significant (but not irrelevant) for service-led or early-stage startups where IP has not yet been formalised. The pillar rewards both formal IP (patents, registrations) and strategic IP (proprietary datasets, trade secrets, first-mover algorithmic advantages) when they are genuinely defensible.

### 11.2 Evaluation Questions

1. What specific intellectual property assets does the startup own, control, or have exclusive access to?
2. For filed or granted patents: what is the scope of the claims, in which jurisdictions have they been filed, and what aspects of the business do they protect?
3. Does the company hold clear title to all its IP — have all founders, employees, and contractors signed IP assignment agreements, and are there no undisclosed prior claims from employers or academic institutions?
4. Is there any proprietary data — training datasets, customer databases, behavioural datasets — that competitors cannot readily acquire or replicate?
5. What trade secrets does the company rely on, and what measures are in place to maintain their secrecy (NDAs, access controls, documented trade secret protection policies)?
6. Are there any ongoing or threatened IP disputes, third-party claims, or freedom-to-operate concerns that could materially affect the startup's ability to use or commercialise its technology?
7. How long would it take a well-resourced competitor to replicate the startup's core IP position, and what would it cost them to do so?
8. For software companies: what is the open-source policy, and are there any open-source components in the product that carry licensing obligations that constrain the startup's commercialisation options?
9. How does the startup plan to expand and protect its IP portfolio as the company grows?
10. Are trademarks registered for the company name and product names in primary operating jurisdictions?

### 11.3 Subcriteria

#### 11.3.1 IP Asset Quality and Scope (IPC-01)
**Measures:** The quality, breadth, and commercial relevance of the startup's formal IP assets. A granted patent with broad independent claims in key commercial jurisdictions is a stronger IP asset than a provisional patent application with narrow claims in a single geography.
**Mapping to Pillar Score:** IPC-01 contributes approximately 30% to the IP pillar score.

#### 11.3.2 IP Ownership Clarity (IPC-02)
**Measures:** Whether the startup holds unambiguous, undisputed legal title to all its IP assets. This includes verification that IP assignment agreements are in place with all founders, employees, and contractors; that there are no residual claims from prior employers or academic institutions; and that there are no co-inventor disputes.
**Mapping to Pillar Score:** IPC-02 contributes approximately 25% to the IP pillar score. IP ownership disputes are one of the most serious investability blockers encountered by startups in due diligence.

#### 11.3.3 Proprietary Data and Knowledge Assets (IPC-03)
**Measures:** Whether the startup has built meaningful proprietary data assets — datasets, knowledge graphs, trained models, customer behaviour databases — that form a moat independent of formal IP protection. Data assets are increasingly the primary competitive moat for software and AI companies.
**Mapping to Pillar Score:** IPC-03 contributes approximately 22% to the IP pillar score.

#### 11.3.4 Freedom to Operate (IPC-04)
**Measures:** Whether the startup has assessed and confirmed that its products and processes do not infringe on third-party IP rights. A startup that has not conducted a freedom-to-operate analysis, or that has identified potential conflicts and not resolved them, faces material legal risk.
**Mapping to Pillar Score:** IPC-04 contributes approximately 13% to the IP pillar score. Freedom-to-operate issues are not always the startup's fault, but ignoring them is.

#### 11.3.5 IP Protection Strategy (IPC-05)
**Measures:** Whether the startup has a coherent, forward-looking strategy for building and protecting its IP portfolio as the company grows. This includes patent filing strategy, trade secret management, open-source policy, and jurisdiction planning for international expansion.
**Mapping to Pillar Score:** IPC-05 contributes approximately 10% to the IP pillar score.

### 11.4 Evidence Required

**Primary Evidence (Required):**
- IP assignment agreements for all founders, employees, and contractors
- Patent filing details (application numbers, jurisdictions, status) or explanation if no patents are held
- Disclosure of any known third-party IP claims or disputes

**Secondary Evidence (Supporting):**
- Freedom-to-operate legal opinion
- Trade secret register or protection policy
- Open-source license audit (for software products)
- Trademark registration certificates
- Data collection and proprietary dataset documentation
- Prior academic or employer IP release documentation (where relevant)

### 11.5 Red Flags

1. **No IP assignment agreements for one or more founders:** If any founding team member — particularly a technical co-founder who wrote the initial codebase — has not signed an IP assignment agreement, the startup's ownership of its core asset is legally uncertain.
2. **Patent claims derived from academic research with unresolved university ownership:** If a technical founder built the core technology during postgraduate research, and the university has not formally released its ownership rights, there is an active IP ownership risk.
3. **Core technology built on GPL or AGPL licensed open-source with no audit:** Incorporating strong copyleft open-source code (GPL v3, AGPL) into a commercial product without a legal audit can create an obligation to open-source the entire product, which is an existential commercial risk.
4. **Prior employer IP conflict undisclosed:** A founder who worked on directly related technology at a prior employer has an increased risk of that employer asserting IP rights. If this scenario has not been disclosed and assessed by legal counsel, it is a material undisclosed risk.
5. **No formal IP protection for a product claiming deep-tech innovation:** A startup that describes itself as a deep-tech innovator with a novel technology but has no patents, no documented trade secret protection, and no proprietary data assets has either overestimated the novelty of its technology or is leaving its core asset unprotected.
6. **Freedom-to-operate analysis identifies conflicts that have not been addressed:** If a freedom-to-operate analysis (commissioned by the startup or identified during the evaluation) identifies potential infringement of a third party's IP and the startup has not obtained a legal opinion or taken steps to address it, this is a material unresolved risk.
7. **Trademarks unregistered in primary commercial markets:** Operating commercially under an unregistered trademark exposes the startup to third-party squatting, infringement claims, and forced rebranding — all of which carry significant commercial and reputational cost.

### 11.6 Scoring Methodology

The IP pillar scoring is sector-sensitive. For software-as-a-service companies, the absence of patents is not automatically penalised, because software patents are difficult and expensive to obtain and enforce, and the primary IP moat for most SaaS companies is proprietary data and accumulated know-how rather than patents. For pharmaceutical, biotech, and hardware companies, the absence of a robust patent portfolio at the appropriate stage is a significant negative signal.

IPC-02 (IP Ownership Clarity) acts as a binary gate on this pillar. If there is any unresolved IP ownership dispute, the pillar score is automatically capped at 4, regardless of the strength of the remaining subcriteria. An investor considering a startup with unresolved IP ownership issues cannot safely proceed regardless of the quality of the IP itself.

The agent assesses IPC-03 (Proprietary Data) with increasing weight for AI and ML startups. For these companies, the proprietary training dataset is often the most valuable and defensible asset the company has, and its evaluation receives proportionally more attention.

### 11.7 Confidence Calculation

| Evidence Item | Confidence Contribution |
|---|---|
| IP assignment agreements for all team members | +25% |
| Patent application or grant documentation | +20% |
| Freedom-to-operate legal opinion | +20% |
| Trade secret policy or proprietary data documentation | +15% |
| Trademark registration certificates | +10% |
| Open-source license audit | +10% |

IP pillar confidence is unique in that legal documentation provides very high confidence increments. Without the IP assignment agreements, confidence cannot exceed 40% regardless of other evidence. A startup with all primary evidence verified should achieve 85%+ confidence.

### 11.8 Suggested Weight

**Suggested Default Weight: 8%**

IP receives a lower default weight than many other pillars in the general TIDES configuration, reflecting the reality that most early-stage startups have limited formal IP protection, and that the lack of IP in some sectors (consumer apps, marketplaces, service platforms) is not necessarily a strategic weakness.

However, organisations evaluating deep-tech, biotech, pharmaceutical, or hardware startups should increase the IP weight significantly — up to 18–22% — because in these sectors, the IP position is often the primary source of long-term competitive advantage and is a central driver of valuation.

### 11.9 Scoring Examples

**Score: 3/10 (Low)**
The startup claims to have novel AI technology but has no patent filings, no documented trade secret policy, and no documented proprietary dataset. Two of the three founders have not signed IP assignment agreements, including the technical founder who wrote the entire codebase. The CTO previously worked at a competing company in the same space for four years and left nine months ago. No freedom-to-operate analysis has been conducted. The company name is unregistered as a trademark. Confidence: 28%.

**Score: 6/10 (Moderate)**
The startup has a provisional patent application filed in the US covering its core algorithm (filed 8 months ago). All team members have signed IP assignment agreements. The technical co-founder completed his PhD at a university that has signed an IP release for the relevant research under a technology transfer agreement. No freedom-to-operate analysis has been formally conducted, but the founders have reviewed the space and are not aware of conflicts. The company name and product name are registered trademarks in the UK. The open-source components used are MIT and Apache 2.0 licensed with no copyleft concerns. Confidence: 63%.

**Score: 9/10 (Exceptional)**
The startup holds two granted US patents and one European patent covering complementary aspects of its core technology, with three additional applications pending in Japan, Canada, and Australia. All IP assignment agreements are in place, reviewed by a qualified IP attorney. A formal freedom-to-operate analysis was commissioned 12 months ago; it identified one potential conflict that was resolved through a targeted claim amendment during prosecution. The startup has a documented trade secret register and access control policy for sensitive algorithmic processes. Its proprietary training dataset (500M annotated data points accumulated over 3 years through exclusive data partnerships) is documented as a separate IP asset with a clear ownership and licensing structure. All trademarks are registered in the five primary commercial markets. Confidence: 92%.

---

## 12. Pillar 8: Risk

### 12.1 Purpose

The Risk pillar evaluates the nature, severity, and management of material risks facing the startup. Every startup carries risk; the pillar does not score a startup higher for having fewer risks, but for having identified its material risks accurately, understood their potential impact, and implemented credible mitigation strategies.

The Risk pillar is intentionally broad, covering operational risk, regulatory and compliance risk, market risk, execution risk, people risk, and external environmental risk. A low score does not simply mean the startup faces many risks — it means the startup has unidentified, unacknowledged, or unmanaged risks that pose a material threat to its ability to execute.

This pillar also functions as a synthesis layer: it captures systemic risks that emerge from the interaction of weaknesses across multiple other pillars. A startup with moderate weaknesses in Technology, Financial, and Founder pillars may have an elevated aggregate risk profile that would not be visible looking at any single pillar.

### 12.2 Evaluation Questions

1. What does the founding team identify as the three most material risks to their business, and are those the actual three most material risks as assessed by the evaluator?
2. What is the regulatory environment in which the startup operates, and does the team demonstrate a clear understanding of current requirements, pending regulatory changes, and compliance obligations?
3. What single-point-of-failure risks exist — in the technology stack, in the founding team, in the customer base, or in supplier relationships?
4. Is the startup dependent on a single channel, customer, or partner for survival, and what is the plan if that relationship ends or deteriorates?
5. What is the startup's exposure to macroeconomic or geopolitical risks — currency fluctuation, supply chain disruption, regulatory changes affecting its sector, or competitive dynamics in its primary geography?
6. What is the key-person risk — is the startup's success disproportionately dependent on one individual, and what would happen to the company if that person left?
7. Does the startup operate in a sector that is currently or likely to be subject to regulatory changes that could fundamentally alter the business model or market opportunity?
8. What is the startup's approach to data privacy and cybersecurity risk, and is it appropriate for the sensitivity of the data it handles and the regulatory environment it operates in?
9. Are there any known legal proceedings, regulatory inquiries, or contractual disputes that the startup is currently involved in or that are threatened?
10. What is the startup's financial risk profile — is it at risk of a funding gap, a cash crisis, or an inability to meet its financial obligations in the near term?
11. How does the team demonstrate resilience — can they describe specific instances of adversity they have faced, how they managed it, and what they learned?

### 12.3 Subcriteria

#### 12.3.1 Risk Identification Accuracy (RSK-01)
**Measures:** Whether the founding team has accurately identified the most material risks to their business. A team that describes only minor operational risks when major regulatory or competitive risks are clearly present has a risk awareness deficit that is itself a material risk. This subcriteria is evaluated by comparing the team's stated risk list against the evaluator's independent risk assessment.
**Mapping to Pillar Score:** RSK-01 contributes approximately 25% to the Risk pillar score. The ability to identify risk accurately is a prerequisite for managing it.

#### 12.3.2 Regulatory and Compliance Risk (RSK-02)
**Measures:** The nature and severity of regulatory risk in the startup's operating environment, and the quality of the startup's compliance posture. Sectors with significant regulatory risk include fintech, healthtech, edtech (student data), defence, food and beverage, and automotive. This subcriteria assesses both current compliance status and readiness for anticipated regulatory changes.
**Mapping to Pillar Score:** RSK-02 contributes approximately 22% to the Risk pillar score. Regulatory risk is one of the most common causes of startup failure in regulated sectors, and it is frequently underestimated by founding teams without regulatory experience.

#### 12.3.3 Concentration and Dependency Risk (RSK-03)
**Measures:** The degree to which the startup's survival is dependent on a single entity — a single customer, a single supplier, a single technology platform, or a single team member. High concentration creates fragility; a single negative event can be existential rather than manageable.
**Mapping to Pillar Score:** RSK-03 contributes approximately 22% to the Risk pillar score.

#### 12.3.4 Execution Risk (RSK-04)
**Measures:** The risk that the startup cannot execute its stated plan given its current resources, team, and operational capability. This is a synthesis subcriteria that draws on evidence from the Founder, Product, and Technology pillars to assess whether the gap between stated ambition and current capability poses an execution risk.
**Mapping to Pillar Score:** RSK-04 contributes approximately 18% to the Risk pillar score.

#### 12.3.5 Risk Mitigation Quality (RSK-05)
**Measures:** Whether the startup has credible, actionable mitigation strategies in place for its identified material risks. Acknowledging a risk without having a mitigation plan is only marginally better than not acknowledging it.
**Mapping to Pillar Score:** RSK-05 contributes approximately 13% to the Risk pillar score.

### 12.4 Evidence Required

**Primary Evidence (Required):**
- Risk register or formal risk documentation (even if informal)
- Disclosure of any current legal proceedings, regulatory inquiries, or disputes
- Regulatory compliance documentation (licenses, certifications, compliance assessments)

**Secondary Evidence (Supporting):**
- Insurance coverage summary (D&O, cyber, professional indemnity)
- Business continuity plan or disaster recovery documentation
- Regulatory horizon scanning documentation
- Key-person insurance or retention documentation
- Customer concentration analysis (% of revenue from top customers)
- Supplier dependency mapping

### 12.5 Red Flags

1. **Founding team cannot identify the three most material risks to their business:** If the team's stated top risks are operational minutiae (e.g., "our website might go down") while macro-level risks (e.g., a pending regulatory change that could prohibit their business model) are unacknowledged, the team has a critical blind spot in risk awareness.
2. **Operating in a regulated sector with no compliance infrastructure:** A healthtech startup handling patient data with no HIPAA compliance documentation, or a fintech processing payments with no FCA or equivalent regulatory engagement, is operating with significant legal and operational exposure.
3. **Customer concentration above 40% in a single entity:** A startup generating more than 40% of its revenue from a single customer is operationally fragile and faces existential risk if that relationship ends for any reason.
4. **Key-person risk concentrated in a single non-founder individual:** A startup that is functionally dependent on a single technical team member who is not a founder, not equity-compensated, and could leave at any time without financial consequence, has an unmanaged key-person risk.
5. **No known legal proceedings disclosed, but later discovered:** The absence of disclosure does not guarantee the absence of legal proceedings. If due diligence reveals undisclosed disputes, regulatory inquiries, or IP conflicts that were not disclosed during evaluation, this is a serious integrity issue beyond the scope of the risk score.
6. **Business model entirely dependent on a regulatory environment that is under active review:** If the startup's entire business model depends on a specific regulatory position (e.g., a data processing permission, a marketplace exemption, or a specific product classification) that is actively under review by regulators, the business faces existential risk from regulatory change.
7. **No cyber incident response capability for a data-intensive product:** A startup collecting, storing, or processing significant quantities of sensitive user data with no documented incident response plan, no cyber insurance, and no security team has an unmanaged operational risk that increases in severity as the customer base grows.

### 12.6 Scoring Methodology

The Risk pillar is unique in that a higher score does not mean fewer risks — it means the risks are identified, understood, and managed. The scoring process is explicitly comparative: the agent independently identifies the material risks it observes from the evaluation evidence across all pillars, and then compares this list to the risks the founding team has acknowledged and addressed.

RSK-01 (Risk Identification Accuracy) is scored by measuring the overlap between the agent's independent risk assessment and the team's disclosed risks. A team that has identified all of the top five material risks identified by the agent receives a high RSK-01 score. A team that has identified only one of five scores much lower, because the missed risks represent unmanaged exposures.

RSK-02 (Regulatory Risk) applies sector-specific knowledge. The TIDES platform maintains sector-specific regulatory risk databases for each sector code, covering current regulatory requirements, pending legislative changes, and historical regulatory enforcement actions in the sector.

The Risk pillar score is NOT simply an inverse of risk quantity. A startup operating in a genuinely high-risk environment that has identified all its risks, maintains a current risk register, has mitigation plans in place, and is actively engaged with regulators can score highly. A startup in a low-risk environment that has not engaged with risk management at all and cannot articulate a coherent risk picture may score poorly.

### 12.7 Confidence Calculation

| Evidence Item | Confidence Contribution |
|---|---|
| Formal risk register or documented risk discussion | +25% |
| Regulatory compliance documentation | +25% |
| Disclosure of legal proceedings (including nil disclosure) | +20% |
| Insurance coverage documentation | +10% |
| Customer and supplier concentration analysis | +10% |
| Business continuity documentation | +10% |

Risk pillar confidence is particularly sensitive to the completeness of disclosure. A startup that provides comprehensive disclosure (including nil returns on legal proceedings and regulatory inquiries) receives a higher confidence score than one that provides partial disclosure or omits sections entirely. Incomplete disclosure reduces confidence because it prevents the evaluator from distinguishing between "no risk" and "undisclosed risk."

### 12.8 Suggested Weight

**Suggested Default Weight: 8%**

Risk receives an equal default weight with IP at 8%. While risk is an important dimension, it is intentionally kept at a lower default weight because it is largely captured by the other pillars when they are evaluated with sufficient depth — a weak Founder score already incorporates team risk, a weak Financial score captures financial risk, and so on. The Risk pillar provides a synthesis view and captures residual and cross-cutting risks not fully visible in individual pillars.

Organisations using TIDES to evaluate startups in highly regulated sectors (healthcare, financial services, energy, defence) should materially increase the Risk weight — to 12–15% — because regulatory risk management capability is a primary investment criterion in these sectors.

### 12.9 Scoring Examples

**Score: 3/10 (Low)**
When asked about their biggest risks, the founding team lists "competition" and "hiring the right people" — both generic and non-specific. The evaluator independently identifies four material risks: (1) the startup's core business model requires data processing permissions that are currently under active review by the relevant data protection authority; (2) 65% of revenue is from a single customer who has not signed a renewal agreement; (3) the CTO holds all technical knowledge and is not equity-compensated; (4) the startup is operating in a jurisdiction where their product is currently in a regulatory grey area. None of these four risks appear in the team's risk discussion. No formal risk documentation exists. No legal, regulatory, or insurance disclosures are provided. Confidence: 30%.

**Score: 6/10 (Moderate)**
The team provides a risk register containing twelve items. The top three match three of the five material risks independently identified by the evaluator — a meaningful overlap. Two material risks are absent: the concentration risk from the top customer (28% of ARR) and a potential IP freedom-to-operate concern. The startup has completed a basic GDPR compliance assessment and holds data processor agreements with all customers. No cyber insurance is in place, but the team acknowledges this and has it on their Q3 priorities list. No legal proceedings are disclosed. D&O insurance is held. Confidence: 62%.

**Score: 9/10 (Exceptional)**
The team presents a formal risk register with 22 items, categorised by likelihood and impact, with named owners and scheduled review dates. The top five risks identified by the team match five of the six material risks independently identified by the evaluator; the one missed risk (a forthcoming sector-specific AI regulation) is one the evaluator agrees has only recently emerged. The startup is registered with the FCA as an appointed representative and is actively engaging with the regulator's innovation sandbox. SOC 2 Type II compliance is in place. A cyber incident response plan has been tested via a tabletop exercise. D&O and cyber insurance are both held. Customer concentration analysis shows the top customer representing 11% of ARR. A dedicated risk review is included in monthly Board reporting. Confidence: 88%.

---

## 13. Overall Score Aggregation

### 13.1 How Pillar Scores Combine into the Overall Score

The overall TIDES score (S_overall) is a weighted average of the eight pillar scores, where the weight of each pillar is determined by the active weight configuration for the evaluation:

```
S_overall = Sum of (W(pillar_i) x S(pillar_i))   for i = 1 to 8
```

Where the sum of all W(pillar_i) = 1.0.

This calculation is straightforward, but the overall score must be interpreted in conjunction with the overall confidence score (C_overall) and the sector normalisation context. A score presented without these contextual factors is incomplete.

### 13.2 Confidence Propagation to the Overall Score

The overall confidence score is not simply the average of pillar confidences. Confidence propagates to the overall score through the following logic:

1. Each pillar confidence score is weighted by the pillar's weight in the evaluation (more heavily weighted pillars have a proportionally larger effect on overall confidence).
2. The weighted average pillar confidence forms the baseline overall confidence.
3. If any pillar is flagged as data-deficient (confidence below 35%), the overall confidence is reduced by an additional 5 percentage points per data-deficient pillar, regardless of the weighted average.
4. If a human override has been applied to any pillar score, the overall confidence is annotated with an override flag but the confidence value is not automatically reduced; however, the override record must be visible to all score consumers.

### 13.3 Score Bands and Their Meaning

| Band | Score Range | Label | Interpretation |
|---|---|---|---|
| 1 | 0.00 – 2.99 | Not Ready | The startup has fundamental, unresolved gaps across multiple critical pillars. The evaluation does not support investment or advancement at this stage. Specific remediation guidance should accompany this score. |
| 2 | 3.00 – 4.99 | Conditional | The startup shows meaningful potential but has material weaknesses that must be addressed before it is appropriate for investment or programme advancement. A conditional score warrants a follow-up evaluation after specified improvements. |
| 3 | 5.00 – 6.99 | Developing | The startup demonstrates a solid foundation across most pillars with specific gaps. Suitable for early-stage programmes, mentorship-focused accelerators, and exploratory investment conversations. |
| 4 | 7.00 – 8.49 | Strong | The startup demonstrates strong fundamentals across the evaluated pillars. Suitable for investment consideration at the appropriate stage. Due diligence is warranted. |
| 5 | 8.50 – 9.49 | Exceptional | The startup demonstrates exceptional fundamentals with minimal material weaknesses. Highly suitable for investment. Represents the top tier of startups evaluated by the platform. |
| 6 | 9.50 – 10.00 | Outstanding | Reserved for startups that achieve near-perfect scores across all pillars with high confidence on all assessments. Extremely rare at any stage. |

> **Important:** Score bands are thresholds for interpretation, not automatic decision triggers. A score of 7.2 does not automatically approve a startup for investment. A score of 4.8 does not automatically reject it. Scores are inputs to human decision-making processes, not substitutes for them.

### 13.4 Score Breakdown Reporting

Every evaluation report must include the following components of the overall score summary:

- The overall score to two decimal places
- The overall confidence percentage
- The score band and label
- A table showing all eight pillar scores, their confidence, and their weights used in this evaluation
- A flagging of any pillars with confidence below 60%
- A flagging of any pillar scores that have been subject to human override
- The weight configuration reference used
- The sector normalisation profile applied

---

## 14. Score Override Protocol

### 14.1 Purpose and Scope of Overrides

The TIDES platform generates scores from evidence through a structured AI evaluation process. However, the platform explicitly acknowledges that human expertise has a legitimate role in the scoring process, particularly when:

- The evaluator has direct, material knowledge about the startup that is not captured in the evidence submission (e.g., they attended a live pitch session, conducted reference calls, or have sector expertise that provides contextual insight the AI cannot replicate)
- The AI evaluation has produced a score that conflicts significantly with the evaluator's professional judgment and the evaluator can articulate specific, evidence-based reasons for the divergence
- New material information becomes available after the AI evaluation is completed that would meaningfully change one or more pillar scores

Score overrides are a structured, auditable feature of the platform, not an escape valve from the evaluation process.

### 14.2 What Can Be Overridden

A human reviewer can override any individual pillar score. The overall score is then automatically recalculated using the revised pillar score. The reviewer cannot directly override the overall score without overriding at least one pillar score — this preserves the traceability of every score component.

A reviewer cannot override the confidence score of a pillar. Confidence is a function of evidence completeness, which is objectively determined by the platform. If the reviewer believes that confidence is too low because evidence exists that was not submitted, the correct action is to resubmit with the additional evidence and trigger a re-evaluation, not to override confidence.

### 14.3 Override Record Requirements

Every override must produce an Override Record that is permanently attached to the evaluation. The Override Record must contain:

| Field | Content |
|---|---|
| Override ID | Unique identifier for this override event |
| Evaluation ID | Reference to the parent evaluation |
| Pillar | The pillar whose score was overridden |
| AI Score | The original AI-generated pillar score |
| Override Score | The new pillar score assigned by the reviewer |
| Reviewer ID | The authenticated identity of the reviewer |
| Reviewer Role | The reviewer's position (e.g., Investment Partner, Programme Manager, Technical Advisor) |
| Override Timestamp | Date and time of the override (UTC) |
| Justification | A minimum 100-word written justification explaining the specific reason for the override, referencing the evidence or knowledge that informed it |
| Evidence Reference | Any additional evidence documents or references that support the override |
| Disclosure Flag | Whether the override is disclosed to the startup being evaluated (Boolean) |

### 14.4 Override Disclosure Policy

Overrides may be disclosed or non-disclosed to the startup, depending on the evaluation context. Confidential scoring contexts (e.g., competitive grant evaluation where all applicants are evaluated against each other) may appropriately use non-disclosed overrides. Advisory or accelerator contexts where the startup receives its score as feedback should disclose that an override was applied and the general basis for it.

### 14.5 Override Audit and Review

All override records are subject to the audit process defined in `07_Override_And_Audit_Standard`. Organisations must review override patterns on a quarterly basis to identify:
- Systematic bias toward specific sectors, founder demographics, or geographies
- Individual reviewers who override AI scores consistently in one direction without documented justification
- Patterns that suggest reviewers are using overrides to bypass the scoring process rather than supplement it

---

## 15. Historical Scoring and Longitudinal Tracking

### 15.1 Why Longitudinal Tracking Matters

A single point-in-time evaluation provides a snapshot. For organisations that work with startups over multiple months or years — accelerators, incubators, corporate venture arms, and government innovation agencies — the trajectory of a startup's score over time is at least as informative as any single score.

A startup that scored 4.5 on its first evaluation and 6.8 on its second evaluation six months later is demonstrably executing and improving. A startup that scored 7.2 on its first evaluation and 5.8 on its second is showing deterioration that warrants investigation. Neither insight is available from a single evaluation.

### 15.2 Evaluation Record Retention

Every evaluation record produced by the TIDES platform must be permanently retained and linked to the startup entity record. Startup entity records are keyed on a persistent Startup Entity ID (SEID) that is assigned at first evaluation and persists across all subsequent evaluations, regardless of company name changes or legal restructuring.

The following data points are retained for every evaluation cycle:

- Evaluation ID
- Evaluation timestamp
- Startup Entity ID (SEID)
- Weight configuration used
- Sector normalisation profile applied
- All eight pillar scores and confidence scores (pre-override and post-override)
- Overall score and confidence
- All override records (if any)
- Evidence submission inventory (list of evidence items submitted)
- Evaluating agent configuration reference

### 15.3 Longitudinal Score Display

The TIDES dashboard provides a longitudinal score view for each startup entity, displaying:

1. A timeline chart showing overall score trajectory across all evaluation cycles
2. A pillar-level trajectory showing which pillars have improved, deteriorated, or remained stable across cycles
3. A confidence trajectory showing whether evidence quality is improving over time
4. Annotations for significant events: funding rounds, major product releases, team changes, override events

### 15.4 Re-evaluation Triggers

The platform supports three types of re-evaluation:

**Scheduled Re-evaluation:** At a cadence defined by the organisation (quarterly, semi-annually, or annually). The platform notifies startup entities and evaluation coordinators when a scheduled re-evaluation window opens.

**Event-Triggered Re-evaluation:** Triggered by a material event disclosure — a funding round closed, a major customer won or lost, a significant product release, or a key team change. The startup or the organisation can request an event-triggered re-evaluation by providing evidence of the triggering event.

**Comparative Re-evaluation:** Triggered when new sector benchmark data is available. The platform can re-evaluate a cohort against updated sector benchmarks without requiring new evidence from the startups, allowing the organisation to see how its portfolio stands against evolving sector norms.

### 15.5 Score Delta Analysis

For any startup with two or more evaluation cycles, the platform generates a Score Delta Report that includes:

- Overall score delta (the change in overall score between evaluations)
- Per-pillar score delta, with direction indicators
- Explanation of the primary drivers of positive and negative change
- Identification of pillars that have improved in confidence (more evidence submitted) versus those where confidence has not changed or has declined

Score delta reports are available to the startup (to show impact of improvements made), to the investing organisation (to track portfolio development), and to programme managers (to evaluate accelerator programme effectiveness).

---

## 16. Summary Reference Table

The following table provides a complete summary of all eight evaluation pillars under TAES v1.0. All weights listed are suggested defaults; they are configurable per organisation, sector, and cohort as described in Section 3.

| Pillar | Code | Default Weight | Key Primary Evidence | Key Secondary Evidence | Primary Red Flags |
|---|---|---|---|---|---|
| **Founder** | FND | 18% | Founder CVs; equity/vesting docs; advisory agreements | Reference endorsements; prior company records; pitch recordings | No IP assignment; solo founder with no team-building; all founders same functional background; undisclosed competing obligations |
| **Product** | PRD | 16% | Live product demo; user metrics; customer list; roadmap | User interviews; NPS/CSAT; app store reviews; pilot letters | No user evidence for live product; built without user research; prototype misrepresented as working product; single customer user base |
| **Technology** | TEC | 14% | Architecture document; tech stack description; technical team CVs | Code repository; CI/CD config; security audit; dependency manifest | No technical leadership; sole contributor with no version control; critical security gaps in regulated environment; no ML evaluation framework |
| **Market** | MKT | 14% | TAM/SAM/SOM with methodology; competitive landscape; customer engagement evidence | Analyst reports; market growth data; customer personas; channel agreements | TAM as percentage of global market with no segment; no competitors acknowledged; customer discovery from founders' network only; dominant incumbent ignored |
| **Business Model** | BIZ | 12% | Revenue model description; financial model with assumptions; unit economics data | Pricing documentation; retention data; comparable benchmarks | No defined pricing; LTV:CAC below 1:1; revenue from one or two customers; projections with no mechanism; frequent model changes |
| **Financial** | FIN | 10% | Financial statements; bank statement; cap table | MRR/ARR tracker; prior round docs; financial projections | Runway below 6 months; financials do not reconcile; significant capital with minimal progress; cap table issues; undisclosed instruments |
| **IP** | IPC | 8% | IP assignment agreements; patent documentation; legal dispute disclosures | Freedom-to-operate opinion; trade secret policy; trademark registrations; open-source audit | No IP assignments; academic IP unresolved; GPL in commercial product; prior employer conflict; FTO conflicts unaddressed |
| **Risk** | RSK | 8% | Risk register; regulatory compliance docs; legal disclosure | Insurance docs; BCP; customer concentration analysis; supplier dependency mapping | Team cannot identify material risks; operating in regulated sector without compliance; 40%+ revenue from single customer; undisclosed legal proceedings |

**Total Suggested Default Weight: 100%**

> **Note:** The weights in the table above represent the TAES v1.0 default configuration for general early-stage startup evaluation. They are starting points, not mandates. All eight weights are configurable at the organisation, sector, and cohort level within the constraints defined in Section 3. Any published evaluation score must reference the weight configuration that was applied.

---

*End of TAES v1.0 / Scoring Standard (05_Scoring_Standard.md)*
*Document version 1.0.0 — Effective 2026-06-23*
*Next scheduled review: 2027-06-01*
*Questions and amendment requests: Submit via the TIDES Standards Committee issue tracker*
