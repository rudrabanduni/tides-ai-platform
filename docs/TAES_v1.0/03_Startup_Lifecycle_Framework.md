> **Document:** TAES v1.0 / Startup Lifecycle Framework
> **Classification:** Internal Technical Standard
> **Version:** 1.0.0
> **Status:** Ratified
> **Maintainer:** TIDES Evaluation Standards Committee
> **Last Revised:** 2026-06-23
> **Applies To:** All AI-assisted evaluations conducted under the TIDES AI Evaluation Standard

---

# TAES v1.0 — Startup Lifecycle Framework

## Table of Contents

1. [Introduction](#1-introduction)
2. [Lifecycle Stage Summary Table](#2-lifecycle-stage-summary-table)
3. [Sector Normalisation and Lifecycle Expectations](#3-sector-normalisation-and-lifecycle-expectations)
4. [Lifecycle Stage and Scoring Weight Interaction](#4-lifecycle-stage-and-scoring-weight-interaction)
5. [AI Agent Rule: Indeterminate Stage Handling](#5-ai-agent-rule-indeterminate-stage-handling)
6. [Stage 1 — Idea](#6-stage-1--idea)
7. [Stage 2 — Research](#7-stage-2--research)
8. [Stage 3 — Prototype](#8-stage-3--prototype)
9. [Stage 4 — MVP](#9-stage-4--mvp)
10. [Stage 5 — Pilot](#10-stage-5--pilot)
11. [Stage 6 — Early Revenue](#11-stage-6--early-revenue)
12. [Stage 7 — Product Market Fit](#12-stage-7--product-market-fit)
13. [Stage 8 — Growth](#13-stage-8--growth)
14. [Stage 9 — Scale](#14-stage-9--scale)
15. [Appendix A: TRL Mapping to Lifecycle Stages](#15-appendix-a-trl-mapping-to-lifecycle-stages)
16. [Appendix B: Stage Evidence Submission Checklist](#16-appendix-b-stage-evidence-submission-checklist)

---

## 1. Introduction

### 1.1 Purpose of This Document

This document defines the **Startup Lifecycle Framework** as implemented within the TIDES AI Evaluation Standard (TAES v1.0). The framework establishes a canonical nine-stage taxonomy for classifying the developmental maturity of startups submitted for evaluation. It is the primary reference for AI evaluation agents, human review panels, sector specialists, and investment committee members operating under the TIDES programme.

The lifecycle framework is not a generic stage model repurposed from venture capital convention. It is a structured, evidence-based classification system designed to produce consistent, reproducible, and auditable stage assignments across all sectors, geographies, and founding team compositions. Every stage in this framework is defined by observable, documentable characteristics—not by founder self-declaration or aspirational roadmaps.

### 1.2 Why the Lifecycle Framework Exists

Evaluation instruments that treat all startups as equivalent at the point of assessment introduce structural bias. A pre-revenue deeptech startup with two patents and a working bench prototype is categorically different from a pre-revenue SaaS startup with a live product and zero paying customers. Without a lifecycle framework, scoring systems collapse these differences into a single undifferentiated pool, penalising early-stage deep technology ventures and rewarding superficially mature but fundamentally weak commercial ventures.

The TAES lifecycle framework solves this by:

- **Normalising scoring weights** relative to stage — evidence expectations are calibrated to what is realistically achievable at each stage, not against an absolute gold standard.
- **Enabling sector-relative assessment** — a biotech startup at Stage 2 (Research) operates under fundamentally different regulatory, capital, and time constraints than a fintech startup at Stage 2. The framework encodes these differences.
- **Creating audit trails** — every stage assignment made by an AI agent must be supported by documented evidence references. The framework defines what those references must contain.
- **Preventing stage inflation** — founders frequently self-report at stages beyond their actual maturity. The framework provides the AI agent with criteria to override self-reported stage claims.

### 1.3 How the Framework Connects to Scoring

The TAES scoring model is stage-conditioned. This means:

1. **The stage is determined first**, independently of the score.
2. **Scoring weights are then applied** relative to the assigned stage. For example, absence of revenue is not penalised at Stage 1–4; presence of detailed go-to-market execution data is not rewarded at Stage 1–2 because it is not a credible signal at those stages.
3. **Dimension thresholds shift** — the minimum acceptable evidence threshold for each scoring dimension (Technology, Market, Team, Traction, Business Model, Risk) changes based on the assigned stage.
4. **Stage advancement signals** are captured as part of the evaluation output and surfaced to reviewers as forward-looking indicators.

A startup cannot receive a TAES composite score unless a lifecycle stage has been assigned. Stage assignment is a **hard prerequisite** for scoring.

### 1.4 How the Framework Connects to TRL

The Technology Readiness Level (TRL) scale, originally developed by NASA and adopted by the European Commission, is integrated with this lifecycle framework but does not replace it. TRL addresses only technological maturity. The TAES lifecycle framework addresses commercial, operational, market, and organisational maturity in addition to technological maturity.

The relationship is mapped in Appendix A. In general:

- Stages 1–2 correspond to TRL 1–3
- Stages 3–4 correspond to TRL 3–6
- Stages 5–7 correspond to TRL 6–9
- Stages 8–9 are post-TRL (technology is assumed to be deployment-ready; evaluation shifts to commercial and operational dimensions)

In sectors where TRL is a regulatory criterion (aerospace, medical devices, nuclear), TRL evidence is treated as **required** rather than supporting evidence for stage assignment.

### 1.5 Scope and Limitations

This framework applies to:
- Technology startups across all sectors
- Startups at any funding stage (bootstrapped, pre-seed, seed, Series A, and beyond)
- Startups from any geography operating under any regulatory environment

This framework does not apply to:
- Non-technology SMEs without proprietary IP or platform components
- Corporate innovation labs evaluated as internal ventures
- Research institutions without commercial incorporation

Stage classification under this framework is a **point-in-time assessment**. It reflects the startup's maturity at the date of submission. Retroactive reclassification is permitted only in cases of material misrepresentation in the submission.

---

## 2. Lifecycle Stage Summary Table

The following table provides a one-line definition for each of the nine TAES lifecycle stages. Detailed definitions, characteristics, evidence requirements, risks, metrics, and advancement criteria are provided in the individual stage sections below.

| Stage No. | Stage Name         | One-Line Definition                                                                                   | Typical Duration      |
|-----------|--------------------|-------------------------------------------------------------------------------------------------------|-----------------------|
| 1         | Idea               | A problem-opportunity pair has been identified and articulated but no systematic work has been done   | Days to 6 months      |
| 2         | Research           | Systematic investigation of the problem, solution space, and feasibility is actively underway         | 3 months to 2+ years  |
| 3         | Prototype          | A tangible, testable artefact demonstrating core technical feasibility has been built                 | 2 to 12 months        |
| 4         | MVP                | A minimum viable product capable of delivering value to real users is live or in controlled release   | 3 to 18 months        |
| 5         | Pilot              | The product is deployed with a defined cohort of users in conditions that approximate real-world use  | 3 to 24 months        |
| 6         | Early Revenue      | The company is generating initial, non-zero, repeatable revenue from paying customers                 | 6 to 24 months        |
| 7         | Product Market Fit | Demonstrable, measurable evidence that a defined market segment is retaining and expanding product use | 12 to 36 months      |
| 8         | Growth             | The company is scaling revenue, team, and infrastructure at a rate exceeding linear growth            | 1 to 4 years          |
| 9         | Scale              | The company is operating at significant commercial scale with repeatable, systematised growth engines | 2+ years              |

> [!NOTE]
> "Typical Duration" is illustrative, not normative. Sector context significantly affects duration. A medical device startup may spend 4–7 years in Stages 2–4 due to regulatory requirements. A consumer mobile application may progress from Stage 3 to Stage 6 in under 18 months. Duration is never used as a primary criterion for stage assignment.

---

## 3. Sector Normalisation and Lifecycle Expectations

### 3.1 Why Sector Matters

The nine lifecycle stages are universal in structure but not in content. The same stage label encompasses materially different realities depending on the sector in which the startup operates. A TAES evaluation that applies identical evidence expectations across sectors without normalisation will systematically misclassify startups and produce invalid scores.

Sector normalisation is the process by which the AI evaluation agent adjusts its evidence expectations, timeline benchmarks, regulatory burden assessments, and metric thresholds to reflect the structural constraints and norms of the startup's primary sector.

### 3.2 Sector Classification

Under TAES v1.0, all startups are classified into one of seven primary sector categories at the point of submission:

| Sector Code | Sector Name                         | Key Distinguishing Feature                                      |
|-------------|-------------------------------------|-----------------------------------------------------------------|
| BIO         | Biotech / Life Sciences             | Regulatory approval pathways (FDA, EMA, CDSCO) govern timeline |
| MED         | Medical Devices / HealthTech        | Clinical validation and CE/510(k) requirements apply            |
| DEF         | Defence / Dual-Use Technology       | Export controls, security classification, and procurement cycles|
| SAS         | SaaS / Enterprise Software          | Network effects, churn, ARR, and NRR are primary signals        |
| FIN         | Fintech / RegTech                   | Licensing, compliance, and central bank regulatory oversight    |
| CLM         | Climate Tech / CleanTech            | Capital intensity, infrastructure deployment, subsidy dependence|
| CON         | Consumer / D2C / Marketplace        | Unit economics, CAC/LTV, and viral coefficient dominate         |

Sector classification is a **required field** in the submission. Where a startup operates across multiple sectors (e.g., a healthtech platform with SaaS delivery), the **primary sector** is the one most directly affecting the startup's regulatory, capital, and go-to-market environment.

### 3.3 Stage-Specific Sector Normalisation Examples

The following examples illustrate how lifecycle stage expectations differ materially by sector. These are not exhaustive; the AI agent applies the full normalisation matrix defined in TAES Supporting Reference SR-04 (Sector Normalisation Tables).

#### Stage 2 (Research) — Sector Comparison

| Dimension              | BIO / MED                                              | SAS / CON                                           |
|------------------------|--------------------------------------------------------|-----------------------------------------------------|
| Expected Duration      | 12–36 months                                           | 1–6 months                                         |
| Required Evidence      | Literature review, lab protocols, IRB/ethics approval  | Customer discovery interviews, TAM sizing           |
| IP Expectation         | Provisional patent filings expected                    | IP rarely applicable; trade secrets more common     |
| Team Expectation       | PhD-level domain experts or clinical co-founders       | Domain expertise + technical co-founder             |
| Feasibility Standard   | In vitro or in silico results required                 | Market feasibility analysis sufficient              |

#### Stage 4 (MVP) — Sector Comparison

| Dimension              | BIO / MED                                              | SAS                                                 | CON                                                |
|------------------------|--------------------------------------------------------|-----------------------------------------------------|----------------------------------------------------|
| MVP Definition         | Bench prototype + pre-clinical proof-of-concept        | Deployed software with ≥1 active user cohort        | Live product with real purchase transactions       |
| User Validation        | Animal or in vitro model validation                    | Beta users providing structured feedback            | App store reviews, repeat purchase rate            |
| Regulatory Milestone   | IND application or equivalent                          | GDPR/data compliance in place                       | Consumer protection compliance                     |
| Revenue at Stage       | Not expected; grant-funded typical                     | Freemium or pilot agreements possible               | Early transactional revenue expected               |

#### Stage 7 (Product Market Fit) — Sector Comparison

| Dimension              | SAS                                                    | FIN                                                 | CLM                                                |
|------------------------|--------------------------------------------------------|-----------------------------------------------------|----------------------------------------------------|
| PMF Signal             | NRR > 100%, churn < 3%/month                           | Regulatory approval + growing licensed user base    | Power purchase agreements + grid connection        |
| Revenue Expectation    | ARR $1M–$10M range                                     | AUM or TPV growing > 30% MoM                        | Revenue from energy sales or carbon credits        |
| Competitive Signal     | 3+ enterprise reference customers with case studies    | Regulatory moat evidenced                           | Long-term offtake contracts signed                 |

### 3.4 AI Agent Normalisation Protocol

When assigning a lifecycle stage, the AI agent must:

1. Identify the primary sector from the submission metadata.
2. Load the corresponding sector normalisation parameters from SR-04.
3. Apply sector-adjusted evidence thresholds before making a stage determination.
4. Flag any cases where sector classification is ambiguous and request clarification from the human reviewer queue before proceeding.

The AI agent must not apply SaaS-native metrics (ARR, MRR, churn) to evaluate biotech or hardware startups without explicit sector-appropriate translation.

---

## 4. Lifecycle Stage and Scoring Weight Interaction

### 4.1 Overview

The TAES composite score is computed across six primary dimensions:

| Dimension Code | Dimension Name          |
|----------------|-------------------------|
| T              | Technology              |
| M              | Market                  |
| TM             | Team                    |
| TR             | Traction                |
| BM             | Business Model          |
| R              | Risk                    |

The relative weight of each dimension in the composite score is **not fixed**. Weights are dynamically adjusted based on the assigned lifecycle stage. This is because different dimensions carry different informational value at different stages of development.

### 4.2 Stage-Weighted Scoring Matrix

The following matrix shows the approximate weight allocation per dimension at each lifecycle stage. These weights are indicative; exact weights are defined in TAES Technical Reference TR-07 (Scoring Weight Tables).

| Stage | T (Tech) | M (Market) | TM (Team) | TR (Traction) | BM (Biz Model) | R (Risk) |
|-------|----------|------------|-----------|---------------|----------------|----------|
| 1 – Idea             | 10% | 20% | 40% | 0%  | 15% | 15% |
| 2 – Research         | 20% | 20% | 30% | 5%  | 10% | 15% |
| 3 – Prototype        | 30% | 15% | 25% | 10% | 10% | 10% |
| 4 – MVP              | 25% | 15% | 20% | 15% | 15% | 10% |
| 5 – Pilot            | 20% | 15% | 15% | 20% | 15% | 15% |
| 6 – Early Revenue    | 15% | 15% | 15% | 25% | 20% | 10% |
| 7 – PMF              | 10% | 15% | 10% | 30% | 25% | 10% |
| 8 – Growth           | 10% | 15% | 15% | 30% | 25% | 5%  |
| 9 – Scale            | 10% | 20% | 15% | 25% | 25% | 5%  |

### 4.3 Interpretation of Weight Shifts

**Team weight is highest at early stages (1–3)** because, in the absence of product or traction evidence, the team's capability, domain expertise, and track record are the primary predictors of execution quality. At Stage 1, a strong team compensates for an absence of evidence in all other dimensions.

**Traction weight increases progressively from Stage 4 onward**, reflecting the increasing availability and relevance of measurable engagement, user, and revenue data. At Stage 7 and beyond, traction is the dominant evaluation signal.

**Technology weight peaks at Stage 3 (Prototype)**, when the core innovation must be demonstrably functional. By Stage 7+, technology is assumed to be validated; differentiation shifts to commercial and operational execution.

**Business Model weight increases from Stage 5 onward**, reflecting the point at which commercial model clarity becomes a prerequisite for sustainable growth. Early stages are not penalised for business model ambiguity, provided market hypothesis clarity is present.

**Risk weight is highest at Stages 1–2 and 5**, reflecting the high structural uncertainty at the idea/research phase and the specific execution risks that emerge during pilot deployment.

### 4.4 Scoring Minimum Thresholds by Stage

Each dimension has a minimum acceptable score below which a startup cannot advance to stage-gated investment committees, regardless of composite score. These floor thresholds are:

| Stage          | Team Floor | Technology Floor | Traction Floor |
|----------------|------------|------------------|----------------|
| 1 – Idea       | 60/100     | N/A              | N/A            |
| 2 – Research   | 60/100     | 40/100           | N/A            |
| 3 – Prototype  | 55/100     | 55/100           | N/A            |
| 4 – MVP        | 50/100     | 55/100           | 30/100         |
| 5 – Pilot      | 50/100     | 55/100           | 40/100         |
| 6 – Early Rev  | 50/100     | 50/100           | 50/100         |
| 7 – PMF        | 45/100     | 45/100           | 65/100         |
| 8 – Growth     | 45/100     | 40/100           | 70/100         |
| 9 – Scale      | 45/100     | 40/100           | 75/100         |

---

## 5. AI Agent Rule: Indeterminate Stage Handling

### 5.1 Definition of Indeterminate Stage

An **indeterminate stage** occurs when the evidence provided in a startup's submission is insufficient, contradictory, or ambiguous to the degree that no stage can be assigned with confidence above the minimum classification threshold (defined as ≥70% evidence alignment with a given stage's required criteria).

Indeterminate stage conditions most commonly arise when:

- The submission contains self-reported stage claims unsupported by documentary evidence.
- The startup operates in a sector where lifecycle mapping is non-linear (e.g., a platform business that is simultaneously at Stage 3 for one product and Stage 7 for another).
- The submission evidence spans multiple non-adjacent stages (e.g., a 5-year-old company with early revenue but no systematic pilot data, and a team profile matching Stage 1).
- The submission is incomplete or redacted to a degree that prevents stage determination.

### 5.2 AI Agent Protocol for Indeterminate Stage

When the AI evaluation agent cannot determine a lifecycle stage with ≥70% confidence, it must execute the following protocol in strict sequence:

**Step 1: Attempt Downward Resolution**
The agent attempts to classify the startup at the lowest stage for which ≥70% of required evidence criteria are satisfied. This is the **conservative floor stage**.

**Step 2: Identify Evidence Gaps**
The agent generates a structured evidence gap report listing:
- Which required evidence items are missing
- Which evidence items are present but ambiguous
- Which self-reported claims contradict observable evidence

**Step 3: Flag for Human Review**
The agent tags the evaluation record with status code `STA-INDET` and routes it to the human reviewer queue with the evidence gap report attached. No composite score is generated until stage assignment is confirmed.

**Step 4: Record Provisional Stage**
If the funding entity or programme requires a provisional score (e.g., for batch ranking purposes), the agent may assign a provisional stage equal to the conservative floor stage, with a mandatory disclaimer: *"Stage assignment provisional pending human review. Score not to be used for investment decision-making without reviewer confirmation."*

**Step 5: Do Not Hallucinate Stage**
Under no circumstances may the AI agent assign a stage by inference, extrapolation, or analogy without evidence-based support. Stage assignment without documented evidence alignment is a critical protocol violation under TAES v1.0 and must be logged in the audit record.

### 5.3 Common Indeterminate Stage Triggers

| Trigger Condition                                        | Most Common Sector   | Recommended Resolution                                  |
|----------------------------------------------------------|----------------------|---------------------------------------------------------|
| Founders report "PMF" with no retention data             | SAS, CON             | Downgrade to Stage 5 or 6; request retention evidence   |
| 5+ years old with no revenue and no pilot data           | BIO, CLM             | Verify regulatory/clinical timeline; may be valid Stage 2–3 |
| Revenue present but no defined customer segment          | CON, FIN             | Flag as Stage 6 with BM score floor penalty             |
| Working prototype with no user testing                   | All                  | Assign Stage 3; do not advance to Stage 4               |
| Technology not built; only a pitch deck                  | All                  | Assign Stage 1 regardless of self-reported stage        |

---

## 6. Stage 1 — Idea

### 6.1 Definition

The **Idea stage** is characterised by the identification and articulation of a problem-opportunity pair — a specific, real-world problem whose solution represents a viable commercial or social opportunity — but in the absence of any systematic investigation, technical feasibility work, or organisational formation beyond informal conceptualisation. The startup exists primarily as a concept held by one or more individuals, possibly with an informal team, but without documented evidence of research, prototyping, or market validation activity.

At this stage, the founding insight is the primary asset. The quality of the problem definition, the specificity of the hypothesis, and the credibility of the founding team are the dominant evaluation criteria.

This stage is not synonymous with "pre-incorporation." A company can be legally incorporated and still be at the Idea stage if no substantive development work has commenced. Conversely, an individual or team may be beyond the Idea stage without formal legal existence if they have completed structured feasibility work.

### 6.2 Characteristics

The following characteristics, when observed in combination, indicate that a startup is at the Idea stage:

1. **Problem statement articulated but not validated**: The founding team can describe the problem they are solving, but this description is based on personal experience, anecdote, or general observation rather than structured interviews, surveys, or primary data collection.
2. **No working artefact exists**: There is no code, device, material, process, or model — even a rough proof-of-concept — that demonstrates any aspect of the proposed solution. Design sketches, wireframes, and slide decks do not constitute artefacts.
3. **Team is informal or nascent**: The founding group may consist of one or two individuals; roles are undefined or ad hoc; no formal employment, equity, or vesting structures have been established.
4. **No external funding has been received**: The startup has not received grants, angel investment, or programme funding. Founders may have invested personal capital.
5. **No customer or user interaction has occurred**: The team has not spoken to potential customers in a structured way or collected any user feedback on the proposed solution.
6. **IP position is undefined**: No patents have been filed, no trade secrets have been identified, and no IP ownership agreements exist among team members.
7. **Business model is speculative**: Revenue model concepts may exist (subscription, transaction fee, licensing), but they are untested hypotheses with no basis in market data.
8. **Regulatory requirements have not been assessed**: The team has not formally identified applicable regulations, standards, or compliance requirements for their sector.

### 6.3 Required Evidence

**Required Evidence (must be present to assign Stage 1):**

| Evidence Item                          | Description                                                                                   | Acceptable Format                               |
|----------------------------------------|-----------------------------------------------------------------------------------------------|-------------------------------------------------|
| Problem Statement Document             | A written articulation of the specific problem being addressed, including who experiences it, how frequently, and at what cost | Pitch deck section, founder memo, executive summary |
| Opportunity Hypothesis                 | A written statement of the proposed solution concept and why it is feasible in principle      | Pitch deck, business concept note               |
| Founding Team Profiles                 | CVs or LinkedIn profiles of all founding members, including relevant domain expertise         | PDF CVs, LinkedIn URLs, team slide              |
| Sector Classification                  | Self-declared primary sector and sub-sector                                                   | Submission form field                           |

**Supporting Evidence (strengthens Stage 1 assignment but not required):**

| Evidence Item                          | Description                                                                                   |
|----------------------------------------|-----------------------------------------------------------------------------------------------|
| Market size estimate (desk research)   | A TAM/SAM estimate sourced from public reports or secondary data                              |
| Comparable solution analysis           | A list of existing solutions and why they are inadequate                                      |
| Preliminary IP landscape note          | A brief review of existing patents in the space                                               |
| Team motivation narrative              | An explanation of why this team is uniquely positioned to solve this problem                  |

### 6.4 Typical Risks

1. **Problem-reality mismatch**: The problem the team believes exists is either not experienced by the target users, experienced at insufficient severity to motivate purchase, or already adequately solved by existing alternatives. This is the most common failure mode at Stage 1 and is often not discovered until Stage 3 or 4.
2. **Founding team cohesion failure**: Informal teams with undefined roles and no equity agreements frequently fracture when the venture requires commitment, resource allocation, or direction-setting. Teams that do not formalise relationships at Stage 1 carry this structural risk forward.
3. **Premature technology bias**: Founders, particularly technical founders, prematurely commit to a specific technology implementation (e.g., blockchain, generative AI, a particular sensor modality) without validating that the technology is necessary or optimal for the problem. This creates path dependency that is costly to unwind.
4. **Absence of domain expertise**: Founding teams without direct experience in the problem domain (as practitioners, researchers, or users) systematically underestimate problem complexity, regulatory burden, and market adoption barriers.
5. **Market size overestimation**: Idea-stage market sizing is typically based on top-down TAM calculations using general industry reports. These consistently overestimate addressable markets by 5–50x relative to empirically validated SAM/SOM figures available at later stages.
6. **Regulatory naivety**: In regulated sectors (health, finance, defence, food), founders at Stage 1 frequently do not identify applicable regulatory pathways, leading to significant downstream rework, cost overrun, and timeline failure.
7. **Competitive landscape blindness**: Without structured secondary research, teams at Stage 1 routinely underestimate or mischaracterise the competitive field, including incumbents, adjacent solutions, and well-funded startups in stealth.

### 6.5 Expected Metrics

At Stage 1, financial and commercial metrics are not expected or evaluated. The relevant metrics are qualitative and structural:

| Metric Category         | Expected Observable                                                               |
|-------------------------|-----------------------------------------------------------------------------------|
| Problem specificity     | Problem is defined for a named, specific user segment (not "everyone")            |
| Founding team coverage  | At least one founder with direct domain expertise OR prior startup experience     |
| Competitive awareness   | At least 3–5 direct or adjacent competitors identified with differentiation noted |
| Opportunity sizing      | At least a desk-research TAM figure cited with source attribution                 |
| Regulatory awareness    | Primary applicable regulation or licensing requirement named, where sector requires|
| IP awareness            | Founding team has considered whether IP is applicable and whether it is defensible|

### 6.6 How to Move to the Next Stage

Advancement from Stage 1 (Idea) to Stage 2 (Research) requires the following conditions to be met:

**Hard Gates (all must be satisfied):**

- [ ] The founding team has completed a minimum of 10 structured primary research interactions (interviews, surveys, focus groups) with individuals who represent the target user or buyer persona.
- [ ] A written problem validation document exists, summarising findings from primary research and either confirming or refining the original problem hypothesis.
- [ ] The team has conducted a structured competitive landscape analysis covering all direct competitors and at least three adjacent alternatives.
- [ ] Core team roles are defined; at minimum, a technical lead and a commercial lead have been identified (these may be the same person in solo-founder contexts, documented as such).
- [ ] An entity has been incorporated, or a formal memorandum of understanding (MOU) or founders' agreement is in place among all co-founders.

**Soft Indicators (should be present; absence is flagged but not blocking):**

- [ ] A provisional patent application, trade secret register, or IP strategy note has been created.
- [ ] The team has identified at least one potential early adopter willing to engage in further research.
- [ ] The team has received or applied for a research or pre-seed grant, incubator programme, or similar structured support mechanism.
- [ ] A preliminary TRL assessment has been documented (expected: TRL 1–2).

---

## 7. Stage 2 — Research

### 7.1 Definition

The **Research stage** is defined by the systematic, structured investigation of the problem domain, the technical solution space, and the feasibility of the proposed venture. At this stage, the team transitions from conceptual articulation to evidence-based inquiry. Work at this stage is characterised by methodological rigour — primary user research, technical feasibility studies, literature reviews, regulatory pathway mapping, and competitive intelligence — rather than by the production of a functional artefact.

The Research stage is the longest and most variable in duration across sectors. In life sciences and deep technology, this stage may span several years and require significant capital. In software and consumer sectors, it may be completed in weeks. The TAES framework does not penalise long Research stages in capital- and regulation-intensive sectors, provided that the research activity itself is documented, structured, and progressing toward a defined technical milestone.

The endpoint of the Research stage is the sufficient accumulation of evidence to justify committing resources to building a testable artefact (Prototype). This is a design decision point, not merely a time elapsed condition.

### 7.2 Characteristics

1. **Active primary research is underway**: The team is conducting systematic user interviews, ethnographic observation, surveys, or experimental studies. Research is planned, documented, and producing artefacts (interview transcripts, experimental notebooks, survey data).
2. **Technical feasibility is under investigation**: The team is actively exploring whether the proposed solution mechanism is technically achievable — through literature review, computational modelling, lab experimentation, or expert consultation.
3. **Regulatory pathway has been mapped**: In regulated sectors, the team has identified the applicable regulatory framework (e.g., FDA 510(k), CE marking, RBI licensing) and has begun assessing the requirements and timeline implications.
4. **IP landscape is under systematic review**: The team is conducting or has commissioned a freedom-to-operate (FTO) analysis and has identified key prior art, competitors' IP positions, and potential filing opportunities.
5. **Team is acquiring domain-specific expertise**: The team is expanding through recruitment of advisors, scientific consultants, domain experts, or research collaborators. The team is not yet full-time in most cases.
6. **Funding is research-appropriate**: The capital structure at this stage typically involves grants, academic funding, government R&D programmes, angel investment, or incubator stipends — not institutional venture capital.
7. **No commercial activity is occurring**: The startup has not signed customer contracts, generated revenue, or deployed a product to users. Commercial relationships may exist as letters of intent (LOIs), advisory agreements, or research partnerships, not as commercial transactions.
8. **Technical risks are being systematically reduced**: The team has identified the primary technical unknowns (failure modes, physics constraints, algorithmic limitations) and is executing experiments specifically designed to resolve them.

### 7.3 Required Evidence

**Required Evidence:**

| Evidence Item                          | Description                                                                                       | Acceptable Format                                     |
|----------------------------------------|---------------------------------------------------------------------------------------------------|-------------------------------------------------------|
| Primary Research Summary               | Documented findings from ≥10 primary research interactions (interviews, surveys, experiments)      | Research report, interview summary, lab notebook      |
| Technical Feasibility Assessment       | Written assessment of whether the proposed technical mechanism is achievable, with supporting data | Technical memo, literature review, feasibility report |
| Competitive and IP Landscape Analysis  | Structured analysis of competitive solutions and existing IP in the domain                        | FTO analysis, competitor matrix, patent landscape     |
| Regulatory Pathway Document            | Identification of applicable regulatory requirements and preliminary pathway assessment            | Regulatory memo, pathway diagram (sector-dependent)   |
| Team Structure Document                | Current team composition, advisor list, and identification of technical gaps                      | Team chart, advisor bios, recruitment plan            |

**Supporting Evidence:**

| Evidence Item                          | Description                                                                                   |
|----------------------------------------|-----------------------------------------------------------------------------------------------|
| Grant or funding award documentation   | Evidence of research funding received (grant letter, term sheet)                              |
| Scientific/technical publications      | Pre-prints, published papers, or conference submissions related to the core technology         |
| Lab access or research facility agreements | Agreements with universities, research centres, or labs providing infrastructure           |
| Expert advisor engagement records      | Meeting notes, advisory agreements, or correspondence with domain experts                     |
| Provisional patent application         | Filed provisional patent(s) covering core innovation                                          |
| Early adopter identification           | Named organisations or individuals expressing willingness to be design partners               |

### 7.4 Typical Risks

1. **Research-to-product translation failure**: Teams capable of rigorous academic research frequently struggle to translate findings into product development decisions. Research outputs (publications, datasets, models) are not automatically product inputs. The absence of a defined research-to-prototype transition plan is a leading indicator of this risk.
2. **Key person dependency**: At this stage, the venture's technical feasibility is often dependent on one or two individuals with specialised expertise. Loss of these individuals — due to departure, competing academic obligations, or founder conflict — can invalidate months or years of research.
3. **Regulatory pathway underestimation**: Preliminary regulatory assessment frequently underestimates the time, cost, and evidence burden of approval pathways, particularly in medical device, pharmaceutical, and financial services sectors. Revised regulatory timelines discovered in Stage 3 or 4 routinely trigger fundamental business model restructuring.
4. **Market dynamics shift during long research phases**: In sectors where research timelines extend beyond 18 months, the competitive landscape, customer preferences, regulatory environment, and technology state-of-the-art can shift materially. Research conducted in Year 1 may be obsolete or misdirected by Year 3.
5. **Pivoting before sufficient data exists**: Teams experiencing slow research progress or early negative findings frequently pivot the problem or solution hypothesis prematurely — before accumulating sufficient evidence to distinguish a genuine technical dead end from an expected experimental setback. Early pivots waste accumulated research investment and reset the evidence base.
6. **IP filing timing errors**: Filing too early (before the invention is sufficiently defined) results in weak or overly narrow patent claims. Filing too late risks prior art from a competitor. Research-stage IP strategy requires specialist guidance that early-stage teams frequently do not retain.
7. **Advisor dependency without accountability**: Research-stage teams frequently build large advisory boards whose members provide credibility signals for fundraising but insufficient operational input. Advisors without formal engagement terms, equity incentives, or deliverable commitments rarely provide the technical depth the team requires.

### 7.5 Expected Metrics

| Metric Category                | Expected Observable                                                                                       |
|--------------------------------|-----------------------------------------------------------------------------------------------------------|
| Research volume                | Minimum 10 primary research interactions; 20+ considered strong evidence                                  |
| Technical validation depth     | At least one testable hypothesis reduced to a binary outcome (feasible/not feasible)                      |
| IP activity                    | At least one provisional filing or documented FTO analysis completed                                      |
| Regulatory clarity             | Named regulatory pathway with estimated timeline and cost (sector-dependent)                              |
| Team completeness              | Core technical function covered; commercial function identified (advisor or co-founder)                   |
| External validation            | At least one credible external validator (grant panel, academic review, industry expert) has assessed work |
| Advisory board quality         | Advisors with direct domain, regulatory, or commercial expertise in the sector                            |

### 7.6 How to Move to the Next Stage

Advancement from Stage 2 (Research) to Stage 3 (Prototype) requires:

**Hard Gates:**

- [ ] At least one core technical hypothesis has been tested and produced results sufficient to conclude that prototyping is technically justified. Results need not be positive — what is required is methodologically sound evidence that the proposed mechanism exhibits the behaviour claimed.
- [ ] A prototype specification document exists, defining what the prototype will demonstrate, how it will be tested, what success criteria apply, and what resources are required to build it.
- [ ] The team has identified the primary technical unknowns that the prototype will resolve.
- [ ] IP ownership has been formally established among all team members and any contributing institutions (university IP agreements, assignment agreements, etc.).
- [ ] Regulatory pathway has been confirmed at sufficient resolution to determine whether the prototype requires regulatory approval before user testing.
- [ ] A defined, named group of at least 5 potential early testers or design partners has been identified and has indicated willingness to engage with a prototype.

**Soft Indicators:**

- [ ] Research has been externally validated (grant award, academic review, publication, expert endorsement).
- [ ] A provisional patent has been filed on the core innovation.
- [ ] The team has secured funding sufficient to complete the prototype phase.
- [ ] An identified technical advisor or CTO-equivalent is actively engaged in the prototype specification.

---

## 8. Stage 3 — Prototype

### 8.1 Definition

The **Prototype stage** is defined by the existence and active development of a tangible, testable artefact that demonstrates the core technical feasibility of the proposed solution. The prototype need not be a complete product — it is specifically designed to test a defined subset of technical hypotheses, typically those representing the highest-risk or most novel aspects of the technology.

A prototype under the TAES framework is defined as any physical, digital, or hybrid artefact that:
- Can be operated or observed by a person other than its creator
- Produces measurable outputs against which success criteria can be evaluated
- Demonstrates at least one novel technical capability claimed by the venture

A design mockup, wireframe, pitch deck, or business plan is not a prototype. A computational simulation may qualify as a prototype in sectors where simulation is the primary validation mechanism (e.g., materials science, structural engineering, drug discovery). A paper prototype or cardboard mockup does not qualify unless the evaluation is specifically for a physical design artefact in a consumer product context.

The Prototype stage ends when the artefact has been tested, results have been documented, and the team has made a deliberate decision to proceed to MVP development based on those results.

### 8.2 Characteristics

1. **A physical or digital artefact exists**: The team can demonstrate the prototype to a third party. It operates, produces output, or performs the core function — however imperfectly.
2. **Testing protocols are defined**: The team has written success criteria against which the prototype is being tested. Testing is structured (controlled conditions, defined inputs, measured outputs) rather than informal demonstration.
3. **The prototype is purpose-built to resolve specific unknowns**: It is not a general-purpose build. It is specifically designed to answer the technical questions left open by the Research stage.
4. **Iteration is active**: The prototype is in a cycle of build-test-revise. Multiple versions (v0.1, v0.2, etc.) may exist, with documented changes between versions based on test results.
5. **The team includes a hands-on technical builder**: At this stage, the prototype must be actively built by a member of the core team, not solely outsourced. External vendors may contribute components, but core IP development is internal.
6. **User involvement is limited and structured**: A small, defined cohort of users (design partners, beta testers, research participants) may interact with the prototype under controlled conditions. This is not open user access.
7. **The prototype does not yet solve the full problem**: It typically addresses 20–40% of the eventual product's functional scope. Its purpose is feasibility demonstration, not value delivery.
8. **Cost and time to produce are disproportionate to eventual unit economics**: The prototype is built without regard to manufacturability, scalability, or cost efficiency. It may use manual processes, custom components, or expert assembly that would not be viable at scale.

### 8.3 Required Evidence

**Required Evidence:**

| Evidence Item                          | Description                                                                                           | Acceptable Format                                    |
|----------------------------------------|-------------------------------------------------------------------------------------------------------|------------------------------------------------------|
| Prototype Demonstration                | Video, images, or in-person demonstration showing the prototype in operation                          | Video file, live demo, annotated screenshots         |
| Test Protocol Document                 | Defined success criteria, testing conditions, input parameters, and measurement methods               | Test plan document, lab protocol, test script        |
| Test Results Documentation             | Recorded outputs of prototype testing against defined success criteria                                | Lab notebook, test report, data tables               |
| Technical Architecture / Build Spec    | Description of what the prototype is composed of, how it works, and what novel components it contains | Technical spec, CAD drawings, architecture diagram   |
| Iteration Log                          | Record of changes made between prototype versions and the reasons for each change                     | Version changelog, lab notebook, Jira/GitHub history |

**Supporting Evidence:**

| Evidence Item                          | Description                                                                                   |
|----------------------------------------|-----------------------------------------------------------------------------------------------|
| Design partner feedback records        | Structured feedback from individuals who have interacted with the prototype                   |
| Third-party technical assessment       | Expert review of prototype technical validity (academic, industry expert, testing lab)        |
| Component supply chain documentation  | Evidence that key components or materials have been sourced and are accessible                |
| Regulatory pre-submission or pre-IND  | Evidence of engagement with regulatory bodies on prototype testing requirements               |
| Patent claims in relation to prototype | Confirmation that filed IP covers the novel aspects demonstrated in the prototype             |

### 8.4 Typical Risks

1. **Technical feasibility confirmed but manufacturability ignored**: A prototype that works in a controlled lab environment may have fundamental manufacturing, materials, or scaling constraints that make it commercially unviable. Teams that do not conduct a parallel manufacturability or scalability assessment during the prototype phase discover this only in Stage 4 or 5, after significant investment.
2. **Feature creep into prototype phase**: Teams begin adding features to the prototype beyond what is needed to test core technical hypotheses. This extends build time, increases cost, and delays the evidence-generation that should be the prototype's sole purpose.
3. **Success criteria set too loosely**: Prototype test protocols with vague success criteria (e.g., "works well enough") produce ambiguous results that do not provide actionable go/no-go decisions. Teams continue building on a technology basis that has not been rigorously validated.
4. **User feedback collected informally**: Design partners or test users provide feedback in unstructured forms (verbal comments, email) that cannot be systematically analysed or used to drive product decisions. Absence of structured feedback mechanisms at Stage 3 leads to poor MVP scoping.
5. **IP exposure during demonstration**: Prototype demonstrations to potential customers, investors, or partners without NDAs, confidentiality agreements, or awareness of public disclosure implications can compromise patent priority dates or expose trade secrets.
6. **Core team technical capacity insufficient**: If the team lacks the in-house technical capability to build the prototype, external contractors become critical path dependencies. Contractor unavailability, IP assignment issues, or quality failures directly delay the entire lifecycle.
7. **Parallel regulatory track neglected**: In regulated sectors, prototype testing may itself require regulatory clearance (e.g., clinical study authorisation, animal research ethics approval). Teams that begin prototype testing without confirming regulatory requirements risk invalidated results or regulatory violation.

### 8.5 Expected Metrics

| Metric Category                  | Expected Observable                                                                                 |
|----------------------------------|-----------------------------------------------------------------------------------------------------|
| Prototype completeness           | Core technical hypothesis coverage: ≥1 primary hypothesis tested and resolved                      |
| Test rigour                      | Defined success criteria with quantitative thresholds (not subjective assessments)                  |
| Test result validity             | Results produced under controlled, reproducible conditions                                          |
| Iteration cadence                | At least 2 distinct prototype versions with documented changes                                      |
| Design partner engagement        | At least 3 structured interactions with potential users or buyers documented                         |
| Technical differentiation        | At least one aspect of the prototype demonstrably novel vs. documented prior art                    |
| IP coverage                      | Core innovation covered by filed application or documented trade secret register                    |

### 8.6 How to Move to the Next Stage

Advancement from Stage 3 (Prototype) to Stage 4 (MVP) requires:

**Hard Gates:**

- [ ] At least one core technical hypothesis has been tested against defined success criteria and produced results sufficient to support a go decision (results need not be perfect; they must be sufficient to justify MVP investment).
- [ ] The prototype failure modes have been documented, and a plan to address them in the MVP build has been produced.
- [ ] MVP scope has been defined: a written specification of the minimum feature set required to deliver value to the first real user cohort.
- [ ] At least 3 potential users or buyers have been identified who have committed (in writing, via LOI, pre-registration, or pilot agreement) to using the MVP when available.
- [ ] The team has confirmed that no regulatory approval is required before deploying the MVP to users, or that such approval has been obtained or is in process with a defined timeline.
- [ ] Core team is in place for MVP development: technical builders, a product owner, and at minimum an identified commercial lead.

**Soft Indicators:**

- [ ] Third-party technical validation of prototype results has been obtained.
- [ ] MVP development budget has been secured.
- [ ] Design partners have been converted to committed early adopters under a formal agreement.
- [ ] Patent application has been filed or trade secret strategy is in place for the MVP build.

---

## 9. Stage 4 — MVP

### 9.1 Definition

The **Minimum Viable Product (MVP) stage** is defined by the existence and controlled deployment of a product — software, hardware, service, or platform — that delivers a specific, defined value to a real user in a real context, using the minimum feature set necessary to test the core value proposition. The MVP is not a prototype: it is used by real users for real purposes, not in controlled test conditions designed to evaluate technical feasibility.

Under the TAES framework, "minimum" in MVP refers to feature minimality, not quality minimality. The MVP must be reliable, safe, and sufficient for a user to derive genuine value from it. An MVP that is unusable due to instability, incompleteness, or poor design is a prototype, not an MVP.

The MVP stage ends when the team has sufficient user feedback and behavioural data to make a validated decision about whether the core value proposition is confirmed, and the product is ready for broader deployment under conditions that approximate commercial reality (pilot).

### 9.2 Characteristics

1. **A deployable product exists and is accessible to real users**: Users can access and use the product independently, without hand-holding or manual intervention from the founding team, beyond standard onboarding.
2. **The value proposition is testable**: The MVP is designed to test a specific hypothesis about whether users will adopt, use, and retain the product because of the core value it delivers — not because of relationship or obligation.
3. **User cohort is controlled and monitored**: The MVP is not publicly available. Access is controlled; users are known; their behaviour is being actively monitored and recorded.
4. **The product is functional enough to reveal real usage patterns**: Users interact with the product in ways that reflect genuine intent, not artificial test scenarios. Their behaviour produces data that is analysable.
5. **The team is actively collecting and acting on feedback**: There is a structured feedback loop — usage analytics, user interviews, NPS surveys, or equivalent — and the team is making product decisions based on what they observe.
6. **The MVP is not commercially sold (typically)**: Users may be accessing the product for free, under a pilot agreement, or at a significant discount. Commercial pricing and sales processes are not yet in place.
7. **The product is built on a technology stack that can scale**: Unlike the prototype, the MVP is built with at least preliminary consideration of scalability, maintainability, and security. It should not require a complete rebuild to reach commercial deployment.
8. **The team can describe what they are measuring and why**: There is an explicit hypothesis-driven evaluation framework in place. The team knows what success looks like for the MVP phase and how they will measure it.

### 9.3 Required Evidence

**Required Evidence:**

| Evidence Item                          | Description                                                                                           | Acceptable Format                                   |
|----------------------------------------|-------------------------------------------------------------------------------------------------------|-----------------------------------------------------|
| Product Access Demonstration           | Evidence that the MVP exists and is accessible to real users                                          | Screen recording, live demo, app store listing, URL |
| User List                              | Identities (anonymised is acceptable) of MVP users, including how they were recruited                 | User registry, cohort list, anonymised ID list      |
| Usage Data                             | Analytics or observational data showing user interactions with the MVP                                | Analytics export, usage logs, session recordings    |
| Structured Feedback Documentation      | Records of user interviews, surveys, or feedback forms completed by MVP users                         | Interview transcripts, survey results, NPS data     |
| MVP Specification vs. Actual           | Comparison of intended MVP feature set vs. what was actually built and deployed                       | Feature spec, release notes, product changelog      |

**Supporting Evidence:**

| Evidence Item                          | Description                                                                                   |
|----------------------------------------|-----------------------------------------------------------------------------------------------|
| User retention data                    | Evidence of repeat usage, session frequency, or return visits                                 |
| Net Promoter Score or equivalent       | Structured satisfaction measurement from MVP users                                            |
| Product iteration log                  | Record of product changes made in response to MVP user feedback                               |
| Early adopter agreements               | Signed letters of intent, pilot agreements, or MoUs from MVP users                           |
| Technical architecture documentation  | Documentation of the MVP's technical stack, data architecture, and security posture           |
| Compliance and data governance         | Evidence that applicable data protection, consumer, or sector-specific regulations are met    |

### 9.4 Typical Risks

1. **Building beyond the minimum**: Teams routinely over-engineer the MVP, adding features driven by internal engineering interest, investor expectations, or competitive anxiety rather than user evidence. Over-built MVPs take longer, cost more, and produce less actionable feedback because the signal is diluted across too many features.
2. **Wrong users in the cohort**: MVP user cohorts are frequently populated with early adopters who are friends, colleagues, or warm contacts of the founding team. These users are not representative of the eventual buyer and provide positively biased feedback that masks product-market misalignment.
3. **Feedback collected but not actioned**: Structured feedback is collected (surveys, interviews) but product decisions continue to be made based on founder intuition rather than user data. This makes the MVP phase informative in theory but not in practice.
4. **Technical debt accumulated during speed-to-market pressure**: MVP builds conducted under deadline pressure accumulate technical debt (poor architecture, missing security, hardcoded configurations) that becomes a compounding liability in Stages 5–7. Rebuilds required to address MVP technical debt are a leading cause of growth-stage timeline failures.
5. **Premature commercial positioning**: The team begins selling the MVP before it has sufficient evidence of product-market fit. Early sales commitments made on the basis of an MVP create delivery obligations that constrain the team's ability to pivot or iterate based on feedback.
6. **Ignoring regulatory compliance at MVP stage**: In regulated sectors, deploying an MVP to real users without confirming compliance with applicable data protection, consumer protection, medical device, or financial services regulations exposes the startup to enforcement action that can terminate the venture.
7. **Retention not measured**: Teams measure activation (did the user sign up / install / try the product?) but not retention (did the user return and continue to use it?). MVP success defined solely by activation metrics produces a false signal of product-market fit.

### 9.5 Expected Metrics

| Metric Category              | Expected Observable                                                                                    |
|------------------------------|--------------------------------------------------------------------------------------------------------|
| Active user count            | ≥10 real, non-founder users actively using the product (≥20 is stronger signal)                       |
| Session depth                | Users are reaching core value features, not bouncing after initial activation                          |
| Retention (7-day)            | ≥30% of users return within 7 days of first use (sector-dependent; adjust for use frequency)          |
| Feedback volume              | ≥5 structured feedback interactions (interviews, surveys) documented per month                         |
| Iteration cadence            | Product updates deployed based on user feedback at a frequency of ≥1 per 2 weeks                      |
| Core value delivery          | At least 50% of active users have reached the core value moment as defined by the team                 |
| Data capture completeness    | Analytics in place that capture activation, engagement, and retention at minimum                       |

### 9.6 How to Move to the Next Stage

Advancement from Stage 4 (MVP) to Stage 5 (Pilot) requires:

**Hard Gates:**

- [ ] The core value proposition has been confirmed by user behaviour data: users are using the product for the purpose it was designed for, at a frequency consistent with the use case.
- [ ] Retention data shows that users who reached the core value moment are returning. Retention rate must meet the sector-normalised minimum threshold (see SR-04).
- [ ] At least 5 named organisations or individuals have confirmed willingness to participate in a structured pilot with defined objectives and success criteria.
- [ ] The product is stable enough for broader deployment: no critical bugs outstanding; security baseline assessed; data handling compliant with applicable regulations.
- [ ] The team has documented what the pilot will test that the MVP did not, and has written pilot success criteria.
- [ ] MVP feedback has been synthesised and product changes driven by that feedback have been implemented or prioritised in the development roadmap.

**Soft Indicators:**

- [ ] At least one MVP user has expressed willingness to pay for the product.
- [ ] The team has identified the repeatable onboarding process that will be used in the pilot.
- [ ] A commercial pilot agreement template has been drafted.
- [ ] The team has a defined sales or distribution hypothesis for the pilot phase.

---

## 10. Stage 5 — Pilot

### 10.1 Definition

The **Pilot stage** is defined by the structured deployment of the product with a defined cohort of users or customers in conditions that closely approximate real-world commercial use, under a formal or semi-formal agreement, for the purpose of validating operational viability, scalability of delivery, and commercial model assumptions prior to full commercial launch.

The Pilot stage is critically distinct from the MVP stage in the following ways:
- Pilot users are deploying the product in their actual operational environment, not a test environment.
- Pilot engagements are governed by formal agreements (pilot contracts, MoUs, service agreements) with defined scope, duration, and success metrics.
- The pilot tests not only the product but the entire delivery model: onboarding, support, integration, pricing, and customer success processes.
- Pilot outcomes are explicitly measured against predefined success criteria and used to make a go/no-go decision on commercial launch.

A pilot that is indefinitely extended without defined success criteria or a launch decision milestone is not a pilot — it is a stalled product deployment. The TAES evaluation agent will flag indefinite pilots as a risk indicator and not advance the stage classification.

### 10.2 Characteristics

1. **Formal pilot agreements are in place**: The startup has executed written agreements with pilot participants that define scope, duration, responsibilities, data sharing terms, and success criteria. Verbal agreements do not qualify.
2. **Pilot participants are representative of the target market**: The pilot cohort is composed of organisations or individuals that fit the intended customer profile for commercial launch. Internal users, founder contacts, or charitable participants who do not represent the commercial buyer are flagged but do not disqualify the pilot.
3. **The product is deployed in the participant's real environment**: For B2B products, this means deployment within the customer's systems, workflows, or operations. For B2C products, this means use by real consumers in their natural context.
4. **Operational delivery processes are being tested**: The pilot is not only evaluating the product. It is testing the onboarding process, integration requirements, customer support processes, training requirements, and all operational touchpoints.
5. **Success criteria are predefined and measurable**: The team and pilot participants have agreed in writing on what constitutes a successful pilot outcome, with specific metrics and timelines.
6. **Commercial model assumptions are being tested**: Pricing, payment terms, contract structure, and customer willingness-to-pay are being explored. The pilot may be free or discounted, but commercial terms are being discussed and validated.
7. **Data is being collected systematically**: Usage data, operational data, and qualitative feedback are being collected, stored, and analysed during the pilot period.
8. **The pilot has a defined end date or conversion trigger**: There is a point at which the pilot concludes and a conversion decision is made. Open-ended pilots are not evaluated as Stage 5.

### 10.3 Required Evidence

**Required Evidence:**

| Evidence Item                          | Description                                                                                           | Acceptable Format                                          |
|----------------------------------------|-------------------------------------------------------------------------------------------------------|------------------------------------------------------------|
| Executed Pilot Agreements              | Signed agreements with ≥3 pilot participants defining scope, duration, and success criteria           | Signed contracts, MoUs, pilot term sheets (redacted OK)    |
| Pilot Participant Profiles             | Description of pilot participants and confirmation they represent the target customer segment         | Participant brief, anonymised organisational profiles      |
| Pilot Success Criteria Document        | Predefined, measurable criteria that constitute a successful pilot outcome                            | Pilot charter, success metrics document                    |
| Pilot Progress Data                    | Evidence of active usage and data collection during the pilot period                                  | Usage analytics, operational data logs, interim reports    |
| Structured Feedback Records            | Documented feedback from pilot participants at defined intervals                                      | Interview transcripts, survey results, feedback reports    |

**Supporting Evidence:**

| Evidence Item                          | Description                                                                                   |
|----------------------------------------|-----------------------------------------------------------------------------------------------|
| Pilot completion reports               | End-of-pilot reports for any completed pilots, including outcomes vs. success criteria        |
| Letters of intent to convert           | Written indications from pilot participants of intent to convert to paying customers          |
| Operational incident log               | Record of issues, bugs, support requests, and resolutions during the pilot                   |
| Integration documentation              | Technical documentation of how the product integrates with pilot participants' systems        |
| Pricing discussion records             | Evidence of commercial conversations, pricing proposals, or willingness-to-pay validation     |

### 10.4 Typical Risks

1. **Pilot participant incentive misalignment**: Pilot participants who receive the product for free have fundamentally different adoption behaviours and feedback quality than paying customers. Free pilots routinely overestimate adoption rates, underestimate integration friction, and produce unreliable commercial conversion signals.
2. **Pilot fatigue and participant disengagement**: Pilot participants who initially committed to a structured pilot progressively disengage if the product does not deliver early value. By the midpoint of an extended pilot, participation rates have typically declined by 30–60%. Teams that do not monitor and manage engagement proactively receive skewed data from the most committed minority.
3. **Support load underestimation**: The operational load of supporting even a small pilot cohort — onboarding, troubleshooting, training, escalations — frequently exceeds the capacity of early-stage teams, consuming engineering and founder time at the expense of product improvement. Teams that do not scale support infrastructure before the pilot face this bottleneck acutely.
4. **Success criteria set post-hoc**: Teams that define "success" after observing pilot results produce self-validating assessments that do not reflect genuine product-market validation. Pre-registered success criteria are required to produce valid pilot outcomes.
5. **Integration underestimated in B2B context**: The time, cost, and complexity of integrating with enterprise systems (ERP, EMR, core banking, SCADA) is systematically underestimated by early-stage teams. What appears to be a straightforward API integration in the MVP may require months of customisation in a real enterprise environment.
6. **Commercial conversion not structured**: Teams complete pilots without a structured conversion process — no defined commercial proposal, no follow-up meeting, no timeline for conversion decision. Pilot participants default to inaction, and the startup misinterprets this as a positive outcome.
7. **Regulatory compliance gaps surfaced during pilot**: Real-world deployment surfaces compliance requirements not identified during MVP or research phases — particularly in data privacy, sector-specific regulations, and enterprise procurement requirements. Compliance remediation during a live pilot risks pilot suspension or participant withdrawal.

### 10.5 Expected Metrics

| Metric Category                | Expected Observable                                                                                     |
|--------------------------------|---------------------------------------------------------------------------------------------------------|
| Pilot participant count        | ≥3 formal pilot agreements executed; ≥5 is strong signal                                               |
| Pilot completion rate          | ≥70% of pilot participants complete the full defined pilot period without withdrawal                   |
| Success criteria achievement   | ≥70% of predefined success criteria are met across the pilot cohort                                    |
| NPS or equivalent              | Pilot participant satisfaction score ≥40 NPS (or equivalent sector metric)                             |
| Commercial intent signal       | ≥50% of completed pilot participants express intent to convert to a paying relationship                 |
| Onboarding time                | Time-to-value for pilot participants measured and benchmarked against target                            |
| Support ticket volume          | Support requests per pilot participant per week tracked and trending downward                           |
| Product stability              | <5% of pilot sessions terminated due to product error or downtime                                      |

### 10.6 How to Move to the Next Stage

Advancement from Stage 5 (Pilot) to Stage 6 (Early Revenue) requires:

**Hard Gates:**

- [ ] At least one pilot participant has converted to a paying customer under a formal commercial agreement (contract, subscription, purchase order).
- [ ] The pilot success criteria defined at the outset have been met or exceeded for at least 60% of pilot participants.
- [ ] The commercial pricing model has been validated: at least one customer has agreed to pay at a price point that, if replicated, would produce a viable unit economics profile.
- [ ] The onboarding and delivery process has been documented in sufficient detail that it can be executed by a non-founding team member.
- [ ] Customer support processes have been defined and are operational.
- [ ] There are no outstanding regulatory or compliance issues that would prevent commercial deployment.

**Soft Indicators:**

- [ ] Multiple pilot participants have expressed intent to convert without being specifically solicited.
- [ ] The team has identified a scalable sales or distribution channel hypothesis.
- [ ] The product has been stabilised to a degree that requires minimal engineering intervention to maintain during sales cycles.
- [ ] At least one customer reference is willing to speak to prospective customers on behalf of the startup.

---

## 11. Stage 6 — Early Revenue

### 11.1 Definition

The **Early Revenue stage** is defined by the generation of initial, non-zero, and repeatable revenue from paying customers transacting under commercial agreements. The transition from pilot to early revenue represents the company's first empirical evidence that its value proposition is commercially viable at a price point that real buyers will accept from a vendor they are willing to trust.

"Repeatable" is the operative criterion. A single transaction — a one-time project, a consulting engagement, a grant disguised as a contract — does not constitute early revenue under the TAES framework. What is required is evidence that the company can repeatedly engage, close, and deliver to customers through a process that is, in principle, systematisable. The process need not yet be systemised — but it must not depend uniquely on a single founder relationship or a one-off circumstance that cannot be replicated.

The Early Revenue stage encompasses a wide range of revenue scales — from a company generating its first $10,000 in ARR to one generating $500,000. The upper boundary of this stage is defined not by absolute revenue size but by the presence or absence of demonstrable product-market fit signals (which define Stage 7).

### 11.2 Characteristics

1. **Paying customers exist under formal commercial agreements**: Revenue is coming from customers who have signed contracts, purchase orders, or subscription agreements — not from grants, government programmes, or revenue equivalents such as in-kind contributions.
2. **Revenue is recurring or demonstrably repeatable**: Either the commercial model produces recurring revenue (subscription, retainer) or the company has evidence of multiple distinct customers each making at least one transaction through the same sales process.
3. **The sales process is beginning to crystallise**: The team can describe how they identify, approach, qualify, demonstrate, and close customers. This process is not yet documented or scalable, but it is consistent enough to have produced multiple outcomes.
4. **Customer acquisition cost (CAC) and customer lifetime value (LTV) are beginning to be measurable**: The team is tracking what it costs to acquire each customer and what revenue each customer generates. Precise figures are not expected, but directional awareness is required.
5. **Revenue is not yet sufficient to cover operating costs**: The company is still pre-profitability. Revenue represents validation, not sustainability.
6. **Churn is being tracked even if not yet problematic**: The team knows whether customers are renewing, cancelling, or expanding. Churn at this stage may be high due to product immaturity; what matters is that it is being measured and managed.
7. **The team is beginning to make commercial hires**: The company is hiring or planning to hire its first dedicated sales, customer success, or account management roles.
8. **Investment capital is primary revenue complement**: The company's operational continuity is still dependent on investor capital; revenue alone is insufficient to sustain operations.

### 11.3 Required Evidence

**Required Evidence:**

| Evidence Item                          | Description                                                                                           | Acceptable Format                                           |
|----------------------------------------|-------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| Revenue Documentation                  | Evidence of actual revenue received from paying customers                                             | Bank statements, accounting records, invoices (redacted OK) |
| Customer Contracts                     | ≥2 distinct signed commercial agreements with paying customers                                        | Signed contracts, SaaS subscription records (redacted OK)   |
| Revenue Summary                        | Summary of total revenue, revenue by customer, and revenue by period                                  | Financial summary, MRR/ARR table, revenue dashboard         |
| Sales Process Description              | Narrative description of how the company identifies, engages, and closes customers                    | Sales process document, CRM pipeline export                 |
| Churn / Retention Record               | Evidence of whether customers are renewing or churning, and at what rate                              | Renewal records, CRM notes, subscription analytics          |

**Supporting Evidence:**

| Evidence Item                          | Description                                                                                   |
|----------------------------------------|-----------------------------------------------------------------------------------------------|
| CAC and LTV estimates                  | Early estimates of customer acquisition cost and lifetime value, with methodology              |
| Revenue pipeline documentation         | CRM data or equivalent showing qualified opportunities and projected near-term revenue        |
| Unit economics analysis                | Gross margin per customer or per transaction                                                   |
| Customer reference contacts            | Named customers willing to serve as references for the startup                                |
| Commercial team structure              | Evidence of sales or commercial function being built                                           |
| Investor update letters                | Investor updates providing independent corroboration of revenue and growth narrative           |

### 11.4 Typical Risks

1. **Revenue concentration in a single customer**: Early revenue is frequently dominated by one large customer whose loss would eliminate a significant portion of total revenue. Single-customer revenue concentration above 50% is a material risk factor. Above 70%, it is a structural weakness.
2. **Revenue from non-commercial relationships**: Grants, government contracts, academic collaborations, and consulting arrangements are frequently presented as commercial revenue. These are not equivalent signals. The TAES agent is required to distinguish between commercial product revenue and non-commercial revenue equivalents.
3. **Sales process entirely founder-dependent**: Revenue at this stage is often generated through founder relationships, prior networks, and domain trust — processes that cannot be delegated to a sales hire. A sales process that exists only in the founder's head is not scalable and represents a critical organisational risk.
4. **Premature enterprise pursuit**: Early-stage teams, attracted by the size of enterprise contracts, pursue large organisations with procurement processes that are too slow, compliance requirements that are too onerous, and negotiating power that results in contract terms that are operationally or financially harmful. Enterprise sales cycles that exceed 12 months at Stage 6 frequently cause cash flow crises.
5. **Gross margin not yet assessed**: Teams at this stage frequently celebrate revenue without assessing gross margin. A business generating $200,000 in revenue at 15% gross margin is structurally more precarious than one generating $100,000 at 70% gross margin.
6. **Customer success function absent**: Without a structured customer success function, early customers experience onboarding friction, support gaps, and unmet expectations — resulting in churn before the product has had time to prove value. Customer churn at Stage 6, while structurally expected, becomes entrenched if not actively managed.
7. **Pricing set without data**: Initial pricing is frequently set by founder intuition or competitor benchmarking rather than by willingness-to-pay data or unit economics modelling. Prices set too low at Stage 6 are extremely difficult to raise at Stage 7 without customer attrition; prices set too high at Stage 6 suppress adoption and distort the learning signal.

### 11.5 Expected Metrics

| Metric Category              | Expected Observable                                                                                    |
|------------------------------|--------------------------------------------------------------------------------------------------------|
| MRR/ARR (SaaS)               | >$0; growth trajectory from month 1 to current month is the primary signal                            |
| Revenue concentration        | Top customer should represent <50% of total revenue; <35% is preferred                                |
| Customer count               | ≥3 distinct paying customers; ≥5 is strong signal                                                     |
| Gross margin                 | Positive gross margin; ≥50% for software; ≥30% for hardware; ≥20% for services (sector-dependent)    |
| Monthly revenue growth rate  | ≥10% month-over-month revenue growth (for SaaS/digital); ≥5% for capital-intensive sectors           |
| Churn rate                   | Tracked and understood; ≤10% monthly churn is acceptable at this stage for SaaS                       |
| Sales cycle length           | Defined and benchmarked; SMB: <60 days; mid-market: <120 days; enterprise: <180 days                 |
| CAC recovery period          | CAC/Monthly Revenue per Customer < 18 months (directional at this stage)                             |

### 11.6 How to Move to the Next Stage

Advancement from Stage 6 (Early Revenue) to Stage 7 (Product Market Fit) requires:

**Hard Gates:**

- [ ] ≥5 distinct paying customers under formal commercial agreements, with at least 3 having completed at least one full billing cycle.
- [ ] Net Revenue Retention (NRR) is measurable (i.e., cohort data exists) and is ≥80% (meaning less than 20% of revenue is being lost to churn on a net basis).
- [ ] At least 2 customers have expanded their use or spend without being specifically solicited by the sales team.
- [ ] Revenue growth is consistent (not single-spike) across ≥3 consecutive months.
- [ ] The team can articulate a repeatable sales motion: a defined sequence of steps that, when executed, produces a customer acquisition outcome.
- [ ] Gross margin is positive and has been calculated with cost of goods sold (COGS) properly allocated.

**Soft Indicators:**

- [ ] Inbound leads are beginning to represent ≥20% of the pipeline (indication of word-of-mouth or organic growth beginning).
- [ ] At least one customer reference is willing to participate in case study development.
- [ ] The team has made or is actively recruiting its first non-founder commercial hire.
- [ ] A financial model projecting 12–18 months of runway and path to break-even exists and has been reviewed by the board or lead investor.

---

## 12. Stage 7 — Product Market Fit

### 12.1 Definition

**Product Market Fit (PMF)** is the stage at which a startup has achieved demonstrable, measurable evidence that a defined, reachable market segment is adopting, retaining, and expanding its use of the product at a rate and scale that indicates the product is solving a real problem compellingly better than alternatives. PMF is not a self-declared milestone — it is an empirical state evidenced by specific, measurable patterns in user and revenue behaviour.

Under the TAES framework, PMF is characterised by the convergence of three independent signals:

1. **Retention signal**: Users/customers who adopt the product continue to use it at a rate significantly above a sector-appropriate baseline. This is the primary signal.
2. **Expansion signal**: Existing customers increase their usage, spend, or adoption footprint without being specifically solicited — indicating that the product's value is being discovered and reinforced through use.
3. **Acquisition signal**: New customers are arriving through channels that are partially organic or word-of-mouth, indicating that the market is beginning to pull the product rather than the startup pushing it.

The PMF stage does not require that the startup has found a large market — it requires that the startup has found a real, retaining, growing segment, however small. A startup with 50 customers who are paying, retaining at >90%, and each expanding by 30% annually is at PMF. A startup with 500 customers churning at 5% monthly is not.

### 12.2 Characteristics

1. **Retention is demonstrably above-baseline**: The cohort retention curve has flattened at a meaningful level — for SaaS, typically ≥70% at 90 days; for consumer apps, ≥25–40% at 30 days (sector-dependent). Retention curves that continue to decline toward zero indicate the absence of PMF regardless of other signals.
2. **Net Revenue Retention (NRR) exceeds 100%**: Existing customers are expanding faster than others churn. NRR >100% means the company would grow even with zero new customer acquisition.
3. **Customers are advocating for the product**: Reference customers exist and are actively introducing the startup to their peers, colleagues, or network without formal incentive. The Sean Ellis test (>40% of users would be "very disappointed" if the product disappeared) is met.
4. **The core user segment is precisely defined**: The team can describe their best customer in specific terms — industry, size, role, use case, pain point, and adoption behaviour. The segment is not "everyone" or "companies in our sector."
5. **Inbound demand is measurable and growing**: A meaningful proportion of new customers are arriving through organic, referral, or content-driven channels rather than exclusively through outbound founder-led sales.
6. **Sales velocity is increasing**: Time-to-close and cost-to-close are decreasing as the product's reputation, references, and market awareness grow.
7. **The team is moving from learning mode to growth mode**: Product development is shifting from discovery to optimisation and scaling. The team's primary challenge is no longer "does anyone want this?" but "how do we reach more of the people who want this?"
8. **Unit economics are improving**: CAC is decreasing or stable while LTV is increasing. The CAC:LTV ratio is trending toward ≥3:1.

### 12.3 Required Evidence

**Required Evidence:**

| Evidence Item                          | Description                                                                                           | Acceptable Format                                           |
|----------------------------------------|-------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| Cohort Retention Data                  | Retention curves by monthly cohort showing retention rates at 30, 60, 90 days and beyond              | Analytics export, cohort chart, retention table             |
| NRR Calculation                        | Net Revenue Retention calculation for ≥2 consecutive quarters, with methodology                       | Financial table, revenue waterfall chart                    |
| Customer Satisfaction Data             | NPS or equivalent measure from a statistically meaningful sample of customers                         | Survey results, NPS dashboard, satisfaction analysis        |
| Reference Customer Evidence            | ≥3 customers willing to serve as public or private references, with documented case studies           | Case studies, reference call records, testimonials          |
| Acquisition Channel Data               | Breakdown of new customer acquisition by channel, showing proportion of organic/referral traffic      | CRM data, marketing analytics, channel attribution report   |
| Defined ICP Document                   | Written definition of the Ideal Customer Profile (ICP) based on observed customer data                | ICP document, customer segmentation analysis                |

**Supporting Evidence:**

| Evidence Item                          | Description                                                                                   |
|----------------------------------------|-----------------------------------------------------------------------------------------------|
| Expansion revenue records              | Evidence of upsell, cross-sell, or seat expansion among existing customers                    |
| Press, analyst, or community coverage  | Third-party coverage indicating market awareness and credibility                              |
| Competitive win/loss analysis          | Records of competitive situations and outcomes, indicating product differentiation             |
| Annual Recurring Revenue (ARR)         | Total ARR figure with growth trajectory for ≥4 consecutive quarters                          |
| Sales cycle trend data                 | Evidence that sales cycles are shortening as market awareness grows                           |

### 12.4 Typical Risks

1. **PMF declared prematurely**: The single most common error at this stage. Teams declare PMF based on strong early cohort enthusiasm, positive press, or investor interest rather than sustained retention data. Premature PMF declaration triggers premature scaling (hiring, go-to-market investment) before the retention foundation is solid, resulting in expensive failures.
2. **PMF achieved in too-small a segment**: The startup has achieved genuine PMF within a niche that is too small to build a venture-scale business. The segment is retaining and expanding, but the total addressable population is insufficient to justify the capital required to grow. This is not a fatal flaw — it may indicate a need for segment expansion — but it requires an honest assessment of ceiling.
3. **NRR above 100% masked by one large customer**: A single large customer expanding rapidly can produce an NRR >100% that masks high churn among smaller customers. The TAES agent is required to decompose NRR by customer segment to identify this pattern.
4. **Acquisition channel concentration**: PMF validated through a single acquisition channel (e.g., a specific partnership, a single content piece, a programme referral) is fragile. If that channel degrades, growth stops. Multi-channel validation is required for durable PMF.
5. **Product changes at scale undermine retention**: Teams in growth mode make product changes (feature additions, UI redesign, pricing changes) that are optimised for new customer acquisition but degrade the experience for the existing retaining cohort. This is a known retention risk at the PMF/Growth transition.
6. **Operational capacity limits growth**: The team achieves PMF but lacks the operational infrastructure (customer success, engineering capacity, billing systems, legal frameworks) to onboard customers at the rate that demand growth requires. The result is a customer experience degradation that converts early retention into churn.
7. **International expansion before domestic consolidation**: PMF achieved in one market does not transfer automatically to another market. Teams that expand internationally before fully exploiting the domestic PMF signal dilute focus and often find that PMF does not replicate in different regulatory, cultural, or competitive environments.

### 12.5 Expected Metrics

| Metric Category                | Expected Observable                                                                                    |
|--------------------------------|--------------------------------------------------------------------------------------------------------|
| 90-day cohort retention        | ≥70% for SaaS/B2B; ≥25% for consumer; ≥85% for enterprise (sector-normalised)                       |
| Net Revenue Retention (NRR)    | ≥100%; ≥110% is strong PMF signal; ≥130% is exceptional                                              |
| NPS                            | ≥40; ≥50 is strong; ≥70 is exceptional (segment-dependent)                                           |
| CAC:LTV ratio                  | ≥3:1 directionally; ≥5:1 is capital-efficient PMF                                                    |
| Inbound lead proportion        | ≥20% of new customers via organic/referral/inbound channels                                           |
| ARR growth (QoQ)               | ≥20% quarter-over-quarter ARR growth for ≥3 consecutive quarters                                     |
| Customer count                 | ≥10 distinct paying customers (B2B enterprise); ≥100 (SMB/mid-market); ≥1,000 (consumer)             |
| Monthly churn rate             | ≤2% for SaaS B2B; ≤5% for consumer subscription (sector-normalised)                                 |

### 12.6 How to Move to the Next Stage

Advancement from Stage 7 (Product Market Fit) to Stage 8 (Growth) requires:

**Hard Gates:**

- [ ] NRR is ≥100% for ≥3 consecutive quarters, verified from financial records.
- [ ] Cohort retention has stabilised (the retention curve has flattened) at a level meeting the sector-normalised minimum.
- [ ] A repeatable, scalable sales motion has been validated: the team has documented a process that non-founding team members can execute and that produces consistent conversion rates.
- [ ] The company has hired or contracted at least one dedicated sales or growth function (non-founder).
- [ ] Unit economics (CAC, LTV, gross margin) are measured, tracked, and trending positively.
- [ ] The company has a defined growth plan for the next 12 months, including channel strategy, headcount plan, and financial projections reviewed by the board or lead investor.
- [ ] Technology and infrastructure can support at least 3x current customer volume without architectural rebuild.

**Soft Indicators:**

- [ ] Inbound leads represent ≥30% of pipeline.
- [ ] The startup has received or is actively fundraising at a valuation consistent with growth-stage comparable companies.
- [ ] Third-party analysts, press, or industry observers have identified the startup as a notable player in its market.
- [ ] Multiple competitors have acknowledged the startup's existence through product responses or competitive positioning.

---

## 13. Stage 8 — Growth

### 13.1 Definition

The **Growth stage** is defined by a period of sustained, intentional scaling of revenue, customer base, team, and operational infrastructure at a rate that exceeds linear growth and is driven by repeatable, systematised growth engines rather than individual founder effort. Growth-stage startups are executing against a validated business model and confirmed product-market fit. The primary challenges of this stage are operational: building the organisation, processes, systems, and channels required to grow efficiently without degrading product quality, customer experience, or unit economics.

At the Growth stage, the startup transitions from a learning organisation (whose primary question is "what should we build and for whom?") to an execution organisation (whose primary question is "how do we deliver this efficiently to more of the right customers?"). This transition is one of the most operationally difficult in the startup lifecycle and is frequently the stage at which founding team limitations become most apparent.

The Growth stage is not defined by a specific revenue threshold. A company can be in the Growth stage at $1M ARR or at $20M ARR. What defines the stage is the presence of systematised, scalable growth engines — not the absolute size of the business.

### 13.2 Characteristics

1. **Revenue growth is consistently above-linear**: Quarter-over-quarter revenue growth is sustained at ≥15–25% (sector-dependent) over multiple consecutive quarters, driven by systematised processes rather than one-off events.
2. **Multiple growth channels are operational**: The company is not dependent on a single acquisition channel. Outbound sales, inbound marketing, partnership channels, and/or platform-driven distribution are all contributing meaningfully to pipeline.
3. **The organisation is scaling**: Headcount is growing. The company is building functional teams (Sales, Engineering, Customer Success, Finance, Legal) with defined roles, performance metrics, and reporting structures.
4. **Processes and systems are being institutionalised**: CRM, ERP, HR systems, financial reporting, and operational processes are being formalised and systematised. What was previously managed through founder knowledge or spreadsheets is being translated into institutional process.
5. **Unit economics are healthy or improving**: Gross margin is stable or expanding. CAC is stable or decreasing. LTV is increasing. The company is approaching contribution margin positive.
6. **External capital is available and being deployed**: The company has raised or is deploying significant external capital specifically for growth. Capital is being invested in sales and marketing, product scaling, and infrastructure — not in extending runway.
7. **The leadership team is professionalising**: The company is hiring experienced executives (VP Sales, VP Engineering, CFO, CMO) alongside founding team members. Organisational structure is becoming more formal.
8. **Customer success is a distinct function**: The company has a defined customer success or account management function focused on retention, expansion, and reference development. This function is not the same as customer support.

### 13.3 Required Evidence

**Required Evidence:**

| Evidence Item                          | Description                                                                                           | Acceptable Format                                           |
|----------------------------------------|-------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| Revenue Growth Trajectory              | ≥6 consecutive months of revenue data showing consistent growth rate                                  | Financial statements, accounting software export            |
| Organisational Chart                   | Current team structure showing functional divisions, headcount, and reporting lines                   | Org chart, team overview document                          |
| Go-to-Market Execution Evidence        | Evidence of multiple active sales and marketing channels with attribution data                        | CRM reports, marketing analytics, channel attribution data  |
| Unit Economics Dashboard               | Tracked CAC, LTV, gross margin, and NRR for ≥4 consecutive quarters                                  | Financial model, unit economics report                      |
| Investor Round Documentation           | Evidence of growth-stage capital raise (term sheet, close documentation)                              | Round summary, investor announcement (redacted OK)         |
| Customer Expansion Evidence            | Evidence of product or revenue expansion within existing customers                                    | Expansion revenue records, upsell tracking                 |

**Supporting Evidence:**

| Evidence Item                          | Description                                                                                   |
|----------------------------------------|-----------------------------------------------------------------------------------------------|
| Sales team structure and targets       | Evidence of sales team composition, quotas, and performance against targets                   |
| Product scaling documentation          | Technical evidence that product infrastructure has scaled to support growth                   |
| Financial model with 24-month outlook  | Detailed financial projections reviewed by board                                              |
| Partner or channel agreements          | Formal agreements with distribution partners, resellers, or platform integrators             |
| Competitive positioning document       | Updated competitive landscape and differentiation strategy                                    |
| Board composition                      | Board minutes or composition showing governance structure appropriate to growth stage         |

### 13.4 Typical Risks

1. **Growth-stage hiring failures**: The transition from a founder-led team to a professional management team is one of the most structurally risky activities in the startup lifecycle. Executives hired for growth-stage roles frequently have mismatched expectations, cultural fit issues, or experience profiles that do not match the company's actual operational complexity. Failed executive hires at this stage are expensive (total cost including severance, recruiting, and disruption is typically 2–3x annual salary) and operationally damaging.
2. **Unit economics degradation under growth pressure**: The pressure to grow revenue quickly leads teams to accept customers outside their ICP, offer unsustainable discounts, or under-invest in customer success — all of which degrade gross margin, increase churn, and reduce LTV. Revenue growth that destroys unit economics is not sustainable.
3. **Engineering capacity fails to scale with product demand**: Product infrastructure (database, API, hosting, security) that was adequate for MVP and pilot phases frequently reaches capacity limits during growth-phase customer acquisition. Infrastructure failures during high-growth periods cause customer churn, brand damage, and team morale collapse.
4. **Sales team ramp time underestimated**: New sales hires at this stage typically require 3–6 months to reach full productivity. Teams that model aggressive revenue growth without accounting for sales ramp time produce financial projections that fail to materialise, resulting in cash flow crises.
5. **Process debt accumulating**: The informal processes that worked when the company was small become bottlenecks at scale. Without investment in process documentation, training, and tooling, the company's operational efficiency degrades as it grows — manifesting as longer sales cycles, higher error rates, slower product delivery, and increasing operational cost per unit of revenue.
6. **Market expansion before domestic saturation**: Growth-stage teams frequently pursue international expansion before fully capturing the domestic market opportunity, dispersing management attention and capital across multiple geographies without achieving density in any.
7. **Fundraising distraction**: Growth-stage fundraising (Series A, B) is a significant management distraction — typically consuming 3–6 months of CEO/CFO time. Teams that do not plan fundraising timelines carefully find that the fundraising process coincides with an operational growth challenge, with management attention split between investor relations and company execution.

### 13.5 Expected Metrics

| Metric Category                   | Expected Observable                                                                                  |
|-----------------------------------|------------------------------------------------------------------------------------------------------|
| ARR                               | $1M–$20M range typical; growth rate more important than absolute size                               |
| QoQ ARR growth rate               | ≥15% (capital-intensive sectors); ≥25% (SaaS/digital); ≥20% (marketplaces)                        |
| NRR                               | ≥105%; ≥120% is strong growth-stage signal                                                         |
| Gross margin                      | ≥60% for SaaS; ≥35% for hardware; ≥25% for services (sector-normalised)                           |
| CAC payback period                | <18 months for SaaS; <24 months for enterprise; <12 months for high-velocity SMB                   |
| Headcount growth                  | Consistent headcount growth tracked against revenue per employee metric                             |
| Sales quota attainment            | ≥70% of sales reps at ≥80% of quota (indicates repeatable sales process)                           |
| Customer count growth             | ≥20% QoQ growth in paying customer count                                                           |
| Revenue per employee              | Trending upward as operational efficiency improves (indicates scaling, not just hiring)             |

### 13.6 How to Move to the Next Stage

Advancement from Stage 8 (Growth) to Stage 9 (Scale) requires:

**Hard Gates:**

- [ ] Revenue has reached a scale threshold consistent with the company's sector and model ($10M+ ARR for SaaS; equivalent milestones for other sectors per SR-04).
- [ ] The company has achieved contribution margin positive operations (excluding growth-phase investment in sales, marketing, and R&D expansion).
- [ ] A leadership team capable of operating the company independently of day-to-day founder involvement in core functions (Sales, Engineering, Operations, Finance) is in place.
- [ ] Multiple independent acquisition channels are operational and attributable — the company is not dependent on any single channel for ≥60% of new customer revenue.
- [ ] The company has expanded into ≥2 distinct market segments, geographies, or product lines successfully.
- [ ] Financial controls, board governance, and audit processes appropriate to the company's revenue scale are in place.

**Soft Indicators:**

- [ ] The company has received analyst coverage or is included in industry reports as a named competitor.
- [ ] The company is approached as an acquisition target or strategic partner by larger incumbents.
- [ ] The company's products or platforms are becoming a reference standard within a customer segment.
- [ ] A growth equity or late-stage VC round has been completed or is actively in process.

---

## 14. Stage 9 — Scale

### 14.1 Definition

The **Scale stage** is defined by the operation of the company at significant commercial scale, with multiple established growth engines, institutional-grade organisational infrastructure, and a demonstrable ability to grow revenue, market share, and geographic or vertical footprint through systematised, repeatable processes that do not require proportional increases in senior leadership attention.

At this stage, the company is no longer a startup in the experiential sense — it is a scaling company that has validated its business model, captured a meaningful market position, and is executing a multi-year growth strategy with institutional capital and professional management. The primary challenges of the Scale stage are not existential (survival, PMF, initial customer acquisition) but strategic (competitive differentiation at scale, capital allocation, talent density maintenance, regulatory complexity, and international expansion).

Scale-stage companies are the primary recipients of growth equity, late-stage venture capital, and strategic investment from corporate partners. Their evaluation under TAES is correspondingly weighted toward commercial performance, competitive moat, and organisational execution rather than technological novelty or market feasibility.

### 14.2 Characteristics

1. **Revenue is operationally significant**: The company generates revenue at a scale that is material within its sector — typically ≥$10M ARR for SaaS, with equivalent thresholds for other sectors. Revenue is diversified across ≥3 distinct customer segments or geographies.
2. **The organisation operates institutionally**: The company functions with formal HR policies, defined career paths, structured performance management, legal and compliance functions, and financial controls appropriate to its size. Founder involvement is strategic, not operational.
3. **Multiple product lines or market segments are generating revenue**: The company is no longer a single-product, single-segment company. Revenue is distributed across multiple offerings, customer types, or geographies.
4. **The brand is established in the market**: The company is recognised by target customers, analysts, and competitors. It receives inbound interest from customers, partners, and press without active outreach.
5. **The competitive moat is demonstrable**: The company has established structural competitive advantages — network effects, proprietary data, switching costs, brand loyalty, regulatory barriers, or economies of scale — that make it difficult for new entrants to replicate its position.
6. **Capital deployment is optimised**: The company allocates capital between growth investment (sales, marketing, R&D) and operational efficiency (automation, process improvement) based on formal ROI frameworks and board-approved capital allocation policies.
7. **Exit optionality is visible**: The company's scale and market position make it a credible candidate for IPO, strategic acquisition, or growth equity recapitalisation. Financial sponsors and strategic acquirers are aware of and engaging with the company.
8. **Regulatory and compliance infrastructure is mature**: The company has in-house or retained legal, compliance, and regulatory expertise commensurate with its industry obligations. It does not face material unresolved regulatory risk.

### 14.3 Required Evidence

**Required Evidence:**

| Evidence Item                          | Description                                                                                           | Acceptable Format                                           |
|----------------------------------------|-------------------------------------------------------------------------------------------------------|-------------------------------------------------------------|
| Audited or Reviewed Financial Statements | Financial statements for ≥2 fiscal years, audited or reviewed by an independent accounting firm      | Audited financials, reviewed financial statements           |
| Revenue Diversification Evidence       | Revenue breakdown by customer, segment, geography, or product line                                   | Revenue analysis, CRM segment report, geographic breakdown  |
| Organisational Structure Documentation | Full organisational chart including leadership team, functional divisions, and headcount by function  | Org chart, leadership team bios                            |
| Competitive Position Analysis          | Analysis of competitive landscape positioning the company relative to named competitors               | Competitive intelligence report, analyst citation          |
| Board and Governance Documentation     | Board composition, governance structure, and evidence of board-level oversight of strategy           | Board minutes (redacted), governance framework             |
| Multi-year Financial Model             | Board-approved 3–5 year financial model with scenario analysis                                       | Financial model, board presentation (redacted OK)          |

**Supporting Evidence:**

| Evidence Item                          | Description                                                                                   |
|----------------------------------------|-----------------------------------------------------------------------------------------------|
| Analyst coverage or industry recognition | Inclusion in analyst reports, industry rankings, or press coverage as a named market leader  |
| Patent portfolio or IP register        | Summary of registered IP protecting core differentiation                                      |
| Strategic partnership agreements       | Formal partnerships with large-scale distribution or technology partners                      |
| International expansion documentation  | Evidence of active operations in ≥2 geographies with revenue from each                       |
| ESG / governance reporting             | Evidence of environmental, social, and governance reporting appropriate to company scale      |
| Talent acquisition and retention data  | Evidence of competitive talent attraction and retention (employee NPS, turnover rate)         |

### 14.4 Typical Risks

1. **Innovation stagnation at scale**: Scale-stage companies frequently experience a progressive reduction in their innovation rate as organisational complexity, resource allocation processes, and risk aversion increase. The very processes that produce operational efficiency at scale tend to suppress the exploratory, experimental culture that produced the original product advantage. Companies at this stage face the innovator's dilemma structurally.
2. **Competitive disruption from below**: The same startup-to-scale journey the company completed is being replicated by competitors at earlier stages. Scale-stage incumbents frequently underestimate the speed and agility of well-funded Stage 5–7 competitors targeting their core use case with a more modern architecture or business model.
3. **Leadership talent density dilution**: As companies scale, the ratio of high-performance talent to total headcount tends to decline. Hiring velocity required by growth creates pressure to fill roles with candidates who are adequate but not exceptional. Over time, this dilutes organisational capability and slows execution quality.
4. **Technical debt at infrastructure scale**: Technical debt accumulated across all prior stages compounds at scale. Legacy architecture, accumulated integrations, and aging codebases become significant operational liabilities. Major re-architecture projects at scale (platform migrations, database redesigns) carry multi-year timelines and significant operational risk.
5. **Regulatory exposure at scale**: Companies that were below the threshold of regulatory scrutiny at earlier stages cross regulatory attention thresholds at scale — antitrust scrutiny, data protection enforcement, sector-specific licensing requirements, and international regulatory compliance all become active concerns. Regulatory risk that was theoretical at Stage 5 is operational reality at Stage 9.
6. **Cultural coherence degradation**: Company culture — values, norms, decision-making principles — that was maintained informally by a small team becomes increasingly difficult to sustain as headcount grows. Cultural degradation manifests as misaligned incentives, inconsistent customer experience, increased internal conflict, and talent attrition among high performers who joined for the early-stage culture.
7. **Capital structure complexity**: Scale-stage companies carry complex cap tables, multiple investor classes with different information rights and approval requirements, option pools, and potentially debt facilities. Capital structure complexity can impede decision-making, complicate fundraising, and create governance dysfunction if not actively managed.

### 14.5 Expected Metrics

| Metric Category                   | Expected Observable                                                                                  |
|-----------------------------------|------------------------------------------------------------------------------------------------------|
| ARR / Annual Revenue              | ≥$10M ARR (SaaS); equivalent threshold per sector in SR-04                                          |
| YoY revenue growth                | ≥30% (high-growth); ≥15% (mature growth stage) — context-dependent                                 |
| NRR                               | ≥110%; ≥130% indicates strong expansion revenue engine                                              |
| Gross margin                      | ≥70% for SaaS; ≥40% for hardware/manufacturing; ≥30% for services (sector-normalised)             |
| EBITDA margin trajectory          | Positive or within 12-month path to positive (excluding deliberate growth investment)               |
| Customer diversification          | Top 10 customers represent <40% of total revenue                                                    |
| Employee count                    | ≥50 FTE; organisational depth in all core functions                                                 |
| Revenue per employee              | ≥$150,000 (SaaS); ≥$80,000 (services); ≥$200,000 (marketplace/platform)                          |
| Geographic or segment diversity   | ≥2 geographies or market verticals with material revenue contribution (≥10% each)                  |
| CAC payback period                | <12 months for high-velocity models; <18 months for enterprise                                      |

### 14.6 How to Move Beyond This Stage

Stage 9 (Scale) is the terminal stage in the TAES lifecycle framework. Beyond this stage, companies enter the domain of late-stage growth equity, pre-IPO structuring, and strategic M&A — processes that are governed by separate evaluation frameworks outside the scope of TAES v1.0.

The following conditions mark the transition beyond the TAES evaluation scope:

**Hard Gates for Exit from TAES Framework:**

- [ ] The company has completed a formal IPO, listed on a recognised public exchange, or been acquired by a publicly listed company, removing it from the startup evaluation domain.
- [ ] The company has raised a growth equity or late-stage VC round at a valuation at which the primary investor due diligence is conducted by institutional financial advisors under securities law frameworks, not startup evaluation instruments.
- [ ] The company has annual revenue in excess of the TAES v1.0 scale ceiling (defined as ≥$100M ARR or equivalent; adjustable by programme governing body).

**Soft Indicators of Scale-to-Exit Trajectory:**

- [ ] The company is working with investment banks on IPO readiness or formal M&A processes.
- [ ] The company files or prepares to file annual reports under securities or companies act requirements.
- [ ] The company's market position is regularly referenced in analyst reports from established research firms (Gartner, Forrester, IDC, CB Insights).

---

## 15. Appendix A: TRL Mapping to Lifecycle Stages

The following table maps the Technology Readiness Level (TRL) scale to the TAES lifecycle stages. TRL is used as a supplementary signal in the technology scoring dimension and as a required evidence criterion in sectors with regulatory TRL requirements.

| TAES Stage          | TRL Range   | TRL Description at This Stage                                       | Sectors Where TRL is Required Evidence          |
|---------------------|-------------|---------------------------------------------------------------------|--------------------------------------------------|
| 1 – Idea            | TRL 1       | Basic principles observed and reported                              | DEF, BIO, CLM                                   |
| 2 – Research        | TRL 1–3     | Technology concept formulated; analytical and experimental proof    | DEF, BIO, MED, CLM                              |
| 3 – Prototype       | TRL 3–5     | Component validation in laboratory or controlled environment        | DEF, BIO, MED, CLM                              |
| 4 – MVP             | TRL 5–6     | System/subsystem validated in relevant environment                  | DEF, MED                                        |
| 5 – Pilot           | TRL 6–7     | System prototype demonstrated in operational environment            | DEF, MED, CLM                                   |
| 6 – Early Revenue   | TRL 7–8     | System completed and qualified through test and demonstration       | DEF, MED                                        |
| 7 – PMF             | TRL 8–9     | Actual system proven in operational environment                     | DEF, MED (required for clearance/CE marking)   |
| 8 – Growth          | TRL 9       | Operational deployment at scale                                     | Not typically applicable; TRL assumed ≥9       |
| 9 – Scale           | TRL 9       | Sustained operational deployment; technology is institutionalised   | Not applicable at this stage                    |

> [!NOTE]
> TRL alone is not sufficient for TAES stage assignment. A startup at TRL 7 may be at TAES Stage 4, 5, or 6 depending on its commercial maturity. TRL describes only the technological dimension of the TAES lifecycle framework.

---

## 16. Appendix B: Stage Evidence Submission Checklist

The following checklist summarises the required evidence items across all nine TAES lifecycle stages for use by submission preparers. Each item listed is required for stage assignment; supporting evidence items are listed separately in the individual stage sections above.

| Stage     | Required Evidence Item 1                 | Required Evidence Item 2                  | Required Evidence Item 3                    | Required Evidence Item 4                    | Required Evidence Item 5               |
|-----------|------------------------------------------|-------------------------------------------|---------------------------------------------|---------------------------------------------|----------------------------------------|
| 1 – Idea  | Problem Statement Document               | Opportunity Hypothesis                    | Founding Team Profiles                      | Sector Classification                       | —                                      |
| 2 – Research | Primary Research Summary (≥10 interactions) | Technical Feasibility Assessment       | Competitive and IP Landscape Analysis       | Regulatory Pathway Document                 | Team Structure Document                |
| 3 – Prototype | Prototype Demonstration              | Test Protocol Document                    | Test Results Documentation                  | Technical Architecture / Build Spec         | Iteration Log                          |
| 4 – MVP   | Product Access Demonstration             | User List (≥10 users)                     | Usage Data (analytics)                      | Structured Feedback Documentation           | MVP Specification vs. Actual           |
| 5 – Pilot | Executed Pilot Agreements (≥3)           | Pilot Participant Profiles                | Pilot Success Criteria Document             | Pilot Progress Data                         | Structured Feedback Records            |
| 6 – Early Revenue | Revenue Documentation            | Customer Contracts (≥2)                   | Revenue Summary (MRR/ARR)                   | Sales Process Description                   | Churn / Retention Record               |
| 7 – PMF   | Cohort Retention Data                    | NRR Calculation (≥2 quarters)             | Customer Satisfaction Data (NPS)            | Reference Customer Evidence (≥3)            | Acquisition Channel Data               |
| 8 – Growth | Revenue Growth Trajectory (≥6 months)  | Organisational Chart                      | Go-to-Market Execution Evidence             | Unit Economics Dashboard (≥4 quarters)      | Investor Round Documentation           |
| 9 – Scale | Audited Financial Statements (≥2 years) | Revenue Diversification Evidence          | Organisational Structure Documentation      | Competitive Position Analysis               | Board and Governance Documentation     |

---

*End of Document*

---

> **Document Control**
> | Field | Value |
> |---|---|
> | Document ID | TAES-v1.0-LCF-003 |
> | Author | TIDES Evaluation Standards Committee |
> | Review Cycle | Annual or upon material change to evaluation methodology |
> | Next Review Date | 2027-06-23 |
> | Supersedes | N/A (first issue) |
> | Related Documents | SR-04 (Sector Normalisation Tables), TR-07 (Scoring Weight Tables), TAES-v1.0-001 (Framework Overview), TAES-v1.0-002 (TRL Integration Standard) |
