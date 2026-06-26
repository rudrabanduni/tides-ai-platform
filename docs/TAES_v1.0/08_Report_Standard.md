# TAES v1.0 — Report Standard

> **Document:** TAES v1.0 / Report Standard
> **Classification:** Internal Technical Standard
> **Version:** 1.0.0
> **Status:** Ratified
> **Effective Date:** 2026-06-23
> **Maintained By:** TIDES Platform Engineering & Standards Committee
> **Review Cycle:** Annual or upon major platform revision
> **Parent Standard:** TIDES AI Evaluation Standard (TAES) v1.0
> **Related Documents:** TAES v1.0 / Scoring Rubric, TAES v1.0 / Agent Pipeline Specification, TAES v1.0 / Data Schema

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Report Section Specifications](#2-report-section-specifications)
   - 2.1 [Page 1 — Executive Dashboard](#21-page-1--executive-dashboard)
   - 2.2 [Page 1–2 — Startup Snapshot](#22-page-12--startup-snapshot)
   - 2.3 [Page 2 — Spider Chart / Radar Chart](#23-page-2--spider-chart--radar-chart)
   - 2.4 [Page 2–3 — Pillar Breakdown Table](#24-page-23--pillar-breakdown-table)
   - 2.5 [Page 3 — Founder Analysis](#25-page-3--founder-analysis)
   - 2.6 [Page 3–4 — Product & Technology Analysis](#26-page-34--product--technology-analysis)
   - 2.7 [Page 4 — Market & Competition Analysis](#27-page-4--market--competition-analysis)
   - 2.8 [Page 4–5 — Financial Analysis](#28-page-45--financial-analysis)
   - 2.9 [Page 5 — Risk Matrix](#29-page-5--risk-matrix)
   - 2.10 [Page 5–6 — Improvement Roadmap](#210-page-56--improvement-roadmap)
   - 2.11 [Page 6 — Final Recommendation](#211-page-6--final-recommendation)
   - 2.12 [Appendix — Evidence Log & Metadata](#212-appendix--evidence-log--metadata)
3. [Visual Design Principles](#3-visual-design-principles)
4. [Report Versioning](#4-report-versioning)
5. [Report Security and Access Control](#5-report-security-and-access-control)
6. [Report Formats and Delivery](#6-report-formats-and-delivery)

---

## 1. Introduction

### 1.1 Purpose of This Document

This document defines the official structure, content specification, layout rules, quality constraints, and delivery format for startup evaluation reports produced by the TIDES AI Evaluation Standard (TAES) platform. It is the authoritative reference for all agents, rendering pipelines, human reviewers, and external integrations involved in the production, review, and distribution of TAES evaluation reports.

A TAES evaluation report is the primary artifact delivered to decision-makers at the conclusion of an AI-assisted startup evaluation. It encapsulates the outputs of a multi-agent evaluation pipeline — covering founder quality, product maturity, technology readiness, market opportunity, business model soundness, financial health, intellectual property, and risk exposure — into a single structured document. The report does not merely summarise raw data; it presents evaluated, scored, and interpreted intelligence in a format optimised for high-stakes decision-making under time constraints.

This document governs what appears in the report, in what order, in what format, and to what quality standard. It also defines what the AI must not do: pad sections with generic language, present unverified data as fact, omit confidence qualifiers, or exceed the structural limits defined herein.

### 1.2 Target Reader of the Evaluation Report

The TAES Evaluation Report is designed to be read by the following audience profiles, each with distinct information needs:

| Reader Type | Primary Information Need | Reading Behaviour |
|---|---|---|
| **Committee Member** | Score justification, risks, recommendation rationale | Reads full report; compares across multiple reports |
| **Mentor / Technical Advisor** | TRL, technology stack, product gaps, founder capability | Skips to pillar breakdown and founder/product sections |
| **Investor (Angel / VC)** | Market size, business model, traction, financial risk | Reads executive dashboard first; dives into market and financial sections |
| **Program Officer (Government / Incubator)** | Recommendation, conditions, improvement roadmap | Reads recommendation, roadmap, and risk matrix |
| **Startup Founder (Post-Decision)** | Improvement roadmap, pillar scores, concerns | Reads feedback-oriented sections |

The report structure is sequenced to serve this multi-reader reality: the most critical decision-relevant information appears on Page 1, with increasing depth on subsequent pages. A committee member who reads only Page 1 has sufficient information to vote on the recommendation. A technical advisor who skips to Page 3 finds a self-contained founder and product analysis.

### 1.3 The Five-Minute Readability Requirement

The TAES Report Standard enforces a strict readability constraint: **every evaluation report must be fully comprehensible by its primary reader within five minutes of opening the document.** This is not a suggestion; it is a structural requirement enforced through section length limits, layout rules, and content quality constraints.

The five-minute requirement is justified by operational reality. Evaluation committees at IIT incubators, government startup programs, and venture networks routinely assess dozens of startups within a selection cycle. Decision fatigue and time pressure are real constraints. A report that requires fifteen minutes to parse, or that buries the recommendation on page five, fails its primary purpose regardless of analytical depth.

**How the structure enforces five-minute readability:**

1. **Page 1 is self-sufficient.** The Executive Dashboard contains the recommendation, overall score, top strengths, and top concerns. A reader who reads only Page 1 can make an informed preliminary decision.
2. **No section exceeds its allocated space.** Each section has a defined space allocation. AI agents are prohibited from generating content that exceeds the section's page fraction.
3. **No narrative filler.** Sections that call for bullet points must use bullet points. Sections that call for tables must use tables. Free-form narrative is permitted only in designated narrative fields, with strict sentence limits.
4. **Information hierarchy is enforced by layout.** Score, recommendation, and confidence appear in large, visually distinct elements on Page 1. Supporting data is progressively detailed on subsequent pages.
5. **All claims are qualified, not elaborated.** Where data is unavailable or uncertain, the AI uses confidence labels and flags the gap — it does not expand the narrative to compensate for missing information.

A report that exceeds 6 rendered PDF pages is non-compliant with this standard and must be regenerated.

### 1.4 Design Philosophy

The TAES Report is built on three design principles:

**Dense information, not verbose explanation.** Every square centimetre of a TAES report carries decision-relevant data. There is no section whose purpose is to demonstrate the thoroughness of the analysis. The analysis is demonstrated through the quality and precision of the data presented, not the quantity of words used to describe it.

**Visual hierarchy over textual hierarchy.** The reader's eye must be guided to the most important information within the first three seconds of viewing any page. This is achieved through consistent use of colour-coded score indicators, bold labels, structured tables, and the radar chart. No page should present a wall of undifferentiated text.

**No padding, no hedging, no generic language.** The AI pipeline is explicitly prohibited from generating sentences such as "The startup shows promise in a competitive landscape" or "Further due diligence is recommended." Every sentence in the report must convey a specific, verifiable, or evaluated claim. Qualifications must be data-driven (e.g., "Score: 6.2 / 10, Confidence: Medium — limited public traction data available"), not rhetorical hedges.

### 1.5 Report Generation: From Agent Outputs to Structured Document

TAES Evaluation Reports are never free-form documents written by a single generative model from a raw startup submission. They are assembled from the structured, schema-validated outputs of a multi-agent evaluation pipeline, each agent responsible for one or more scoring pillars.

The report generation process is as follows:

1. **Data Ingestion Agents** parse the startup submission package (pitch deck, business plan, founder CVs, financial projections, product documentation) and extract structured data fields conforming to the TAES Data Schema v1.0.
2. **Pillar Evaluation Agents** independently score each of the eight evaluation pillars using evidence extracted from the submission, supplemented by web search, patent database queries, and market intelligence APIs. Each agent outputs a structured JSON object containing: score, confidence level, evidence list, primary concern, and secondary concerns.
3. **Synthesis Agent** aggregates pillar scores into an overall weighted score, determines the recommendation category, and generates the summary fields (key strengths, key concerns, recommendation justification) using constrained generation templates that enforce sentence limits and prohibit filler language.
4. **Report Assembly Pipeline** maps all agent outputs to the report schema defined in this document, applies visual rendering rules, enforces page limits, and produces the final PDF, web view, and API JSON outputs.

Human reviewers receive the assembled report and may annotate or override specific fields. All overrides are logged with reviewer identity, timestamp, and justification. The AI-generated baseline and the human-reviewed final version are stored as separate versioned documents.

---

## 2. Report Section Specifications

This section defines every section of the TAES Evaluation Report. For each section, the specification covers: section purpose, content specification (data source and content rules), layout description, space allocation, and quality rules.

---

### 2.1 Page 1 — Executive Dashboard

#### 2.1.1 Section Purpose

The Executive Dashboard is the first thing a reader sees and must function as a complete decision summary in isolation. A committee member reading only this section must have enough information to: (a) understand what the startup does at the highest level, (b) know its overall evaluation score, (c) know the formal recommendation, (d) know the top strengths and concerns, and (e) understand the evaluator's confidence in those conclusions.

#### 2.1.2 Content Specification

The Executive Dashboard is populated entirely from the outputs of the Synthesis Agent and Scoring Aggregation Module. The following fields are required, and their data sources are specified:

| Field | Data Source | Constraints |
|---|---|---|
| **Overall Score** | Weighted average of 8 pillar scores (Synthesis Agent) | Displayed as X.X / 10.0; no rounding to integer |
| **Confidence Level** | Aggregate confidence computed from individual pillar confidence ratings | One of: High / Medium / Low / Insufficient Data |
| **Lifecycle Stage** | Extracted by Data Ingestion Agent from submission metadata | One of: Ideation / Validation / Early Traction / Growth / Scale |
| **TRL Level** | Output of Technology Pillar Agent | Integer 1–9 per standard TRL scale |
| **Sector** | Extracted from submission; validated against TIDES sector taxonomy | Primary sector and sub-sector |
| **Recommendation** | Output of Synthesis Agent based on score thresholds and override rules | One of: Incubate / Conditional Incubation / Defer / Reject |
| **Key Strengths** | Top 3 items from Synthesis Agent strength extraction | Max 15 words per bullet; must reference specific evidence |
| **Key Concerns** | Top 3 items from Synthesis Agent concern extraction | Max 15 words per bullet; must name the specific risk or gap |
| **Evaluation Date** | System timestamp at evaluation completion | Format: DD Month YYYY |
| **Evaluation Version** | Pipeline version + report schema version | Format: Pipeline vX.X / Report vX.X |

**Recommendation Thresholds (default):**

| Score Range | Default Recommendation |
|---|---|
| 8.0 – 10.0 | Incubate |
| 6.5 – 7.9 | Conditional Incubation |
| 5.0 – 6.4 | Defer |
| 0.0 – 4.9 | Reject |

Threshold overrides are permitted by the Synthesis Agent if specific pillar scores trigger mandatory flags (e.g., a Legal/IP pillar score below 2.0 triggers at minimum a Conditional recommendation regardless of overall score). All override conditions are documented in the TAES Scoring Rubric (TAES v1.0 / Scoring Rubric, Section 9).

#### 2.1.3 Layout Description

The Executive Dashboard occupies the top two-thirds of Page 1. It is structured as a two-column layout:

**Left column (60% width):**
- Startup name in large bold heading (18pt equivalent)
- Sector and sub-sector as sub-heading
- Recommendation displayed as a colour-coded badge (green = Incubate, amber = Conditional, orange = Defer, red = Reject) with the label in 14pt bold
- Overall Score displayed as a large numeric indicator (32pt bold) accompanied by a horizontal progress bar scaled 0–10
- Confidence Level displayed as a label with an icon indicator (filled circle = High, half-filled = Medium, outline = Low, X = Insufficient)
- Lifecycle Stage and TRL Level displayed as two compact labelled badges side-by-side

**Right column (40% width):**
- **Key Strengths** header followed by exactly 3 bullet points, each prefaced with a green checkmark icon
- **Key Concerns** header followed by exactly 3 bullet points, each prefaced with a red warning icon
- Evaluation Date and Evaluation Version displayed as small-type metadata at the bottom of the column

The bottom one-third of Page 1 transitions into the Startup Snapshot section (Section 2.2).

#### 2.1.4 Space Allocation

The Executive Dashboard occupies approximately **40–45% of Page 1**, which corresponds to roughly **7–8% of the total report length**. It must not overflow onto Page 2. If content generation exceeds the space allocation, the pipeline must truncate Key Strengths and Key Concerns bullets to 12 words maximum and reduce metadata to single-line format.

#### 2.1.5 Quality Rules

**The AI must:**
- Express every Key Strength as a specific, evidenced claim. Example: "Founder holds 2 patents in medical device miniaturisation directly relevant to the core product."
- Express every Key Concern as a specific gap or risk. Example: "No evidence of pilot customer or letter of intent; traction claims are projections only."
- Use the exact recommendation category wording from the approved taxonomy. No paraphrasing (e.g., "Strongly Recommend" is not a valid category).
- Include confidence qualifier if overall confidence is Low or Insufficient.

**The AI must not:**
- Use generic language such as "strong team," "exciting opportunity," or "competitive market."
- List a strength or concern that is not traceable to a specific piece of evidence or a specific agent output.
- Display a score of 0.0 or 10.0 without a mandatory human reviewer flag, as extreme scores require escalated validation.
- Omit any of the 10 required fields. Missing fields must be displayed as `[DATA NOT AVAILABLE]` with a confidence impact note, not silently omitted.

---

### 2.2 Page 1–2 — Startup Snapshot

#### 2.2.1 Section Purpose

The Startup Snapshot provides the factual foundation for all analytical sections that follow. It answers the fundamental questions: who is this startup, what do they do, for whom, and what have they accomplished so far? It is not an analytical section — it presents extracted and lightly synthesised facts, not evaluations.

Readers who are unfamiliar with the startup (e.g., committee members reviewing a new submission) rely on this section to orient themselves before engaging with scored assessments. Readers who know the startup (e.g., mentors who have met the founders) use it as a quick verification check.

#### 2.2.2 Content Specification

| Field | Data Source | Constraints |
|---|---|---|
| **Startup Name** | Submission metadata | Exact legal name as registered; trade name noted if different |
| **Sector / Sub-sector** | TIDES sector taxonomy classification (Data Ingestion Agent) | Primary sector + sub-sector |
| **Stage** | Lifecycle classification (Data Ingestion Agent) | One of: Ideation / Validation / Early Traction / Growth / Scale |
| **Founding Date** | Submission metadata | Month and year; if unavailable, "Year: YYYY (approx.)" |
| **Team Size** | Submission metadata | Full-time headcount; part-time noted separately if declared |
| **Location** | Submission metadata | City, State/Province, Country; remote-first noted if applicable |
| **Problem Statement** | Synthesised by Synthesis Agent from pitch deck / business plan problem section | 2–3 sentences maximum; must describe: who has the problem, what the problem is, and why existing solutions are inadequate |
| **Solution Summary** | Synthesised from submission solution/product section | 2–3 sentences maximum; must describe: what the product is, how it solves the problem, what is distinctly different about the approach |
| **Business Model Summary** | Synthesised from revenue/go-to-market section | 1–2 sentences; must name the revenue mechanism (subscription, transaction fee, licence, etc.) |
| **Target Market Summary** | Synthesised from market section | 1–2 sentences; must name the primary customer segment and geography |
| **Current Traction** | Extracted by Data Ingestion Agent from submission traction section | Key quantitative metrics only (see quality rules); if none available, state "No traction data provided in submission" |

**Traction Metrics Priority Order** (display the highest-evidence metrics available):
1. Paying customers and Monthly Recurring Revenue (MRR)
2. Active users and growth rate
3. Signed letters of intent (LOIs) or pilots
4. Waitlist size or pre-registrations
5. Awards, grants, or institutional recognitions with named entities

#### 2.2.3 Layout Description

The Startup Snapshot spans the bottom third of Page 1 and the top quarter of Page 2. It is structured as follows:

**Metadata block** (top of section, full width): A compact horizontal metadata strip displaying Startup Name (bold), Sector, Stage, Founded, Team Size, and Location as labelled key-value pairs in a single row or two-row grid. This block uses a light grey background to visually distinguish it from the Dashboard above.

**Three-column narrative block** (below metadata): Three equal-width columns containing:
- Column 1: Problem Statement (labelled "Problem") and Solution Summary (labelled "Solution")
- Column 2: Business Model Summary (labelled "Business Model") and Target Market Summary (labelled "Target Market")
- Column 3: Current Traction (labelled "Traction") displayed as a bulleted metric list

Narrative text in columns uses 10pt body font. Column headers use 11pt bold. Each column has a subtle left border line for visual separation.

#### 2.2.4 Space Allocation

The Startup Snapshot occupies approximately **25–30% of Page 1** (below the Dashboard) and **15–20% of Page 2** (top). Total allocation: approximately **8–10% of the report**. Narrative fields must not exceed their sentence limits. The traction column must not list more than 5 metrics.

#### 2.2.5 Quality Rules

**The AI must:**
- Synthesise the Problem Statement to be comprehensible to a non-specialist. Technical jargon must be defined or avoided.
- Ground the Solution Summary in a verifiable product claim, not a vision statement. "We are building X" is acceptable if the product exists in prototype or MVP form. "We aim to revolutionise X" is not acceptable.
- Express traction metrics with precision: "42 paying customers as of March 2026" rather than "dozens of customers." If the submission uses vague language, the agent must flag it as `[UNVERIFIED — SUBMITTED AS-IS]`.
- Identify and state if the founding date is unverified or approximate.

**The AI must not:**
- Invent or extrapolate traction figures. If a metric is not present in the submission, it is not present in the report.
- Expand the Problem Statement beyond 3 sentences to compensate for a complex problem space. Additional problem detail belongs in the Product & Technology Analysis section.
- Use promotional language in the Solution Summary. "Groundbreaking," "revolutionary," and similar adjectives are prohibited.
- Include forward-looking projections in the Traction field. Projections belong in the Financial Analysis section.

---

### 2.3 Page 2 — Spider Chart / Radar Chart

#### 2.3.1 Section Purpose

The Spider Chart (also called a Radar Chart) provides an immediate visual representation of the startup's evaluation profile across all eight scoring pillars. It serves two purposes: (1) it allows readers to identify at a glance which pillars are strong and which are weak, and (2) it enables visual comparison against a sector benchmark line (if available), giving immediate context for whether this startup's profile is typical, exceptional, or deficient relative to comparable startups.

The chart is the only mandatory data visualisation element in the report body. All other data is presented in tabular or bullet format.

#### 2.3.2 Content Specification

The chart displays the following eight pillars on eight equidistant radial axes:

| Axis | Pillar Name | Scoring Agent | Max Score |
|---|---|---|---|
| 1 | Founder & Team | Founder Evaluation Agent | 10 |
| 2 | Product & MVP | Product Evaluation Agent | 10 |
| 3 | Technology | Technology Assessment Agent | 10 |
| 4 | Market Opportunity | Market Analysis Agent | 10 |
| 5 | Business Model | Business Model Agent | 10 |
| 6 | Financial Health | Financial Analysis Agent | 10 |
| 7 | IP & Defensibility | IP Assessment Agent | 10 |
| 8 | Risk & Resilience | Risk Assessment Agent | 10 |

**Data fields for the chart:**
- **Score polygon**: The primary polygon plotted using the 8 pillar scores as radial distances. Filled with a semi-transparent colour (platform brand primary, 30% opacity).
- **Confidence overlay**: A secondary polygon representing the confidence-adjusted score range for each pillar (score ± confidence margin). Rendered as a dashed line only, no fill. Confidence margins are defined as: High = ±0.3, Medium = ±0.8, Low = ±1.5.
- **Benchmark polygon** (conditional): If sector benchmark data is available from the TIDES benchmarking database, a third polygon displays the sector average score for each pillar. Rendered as a thin solid line in a distinct neutral colour (e.g., slate grey). If no benchmark is available, the benchmark polygon is omitted and a note reads: "Sector benchmark not yet available for this sector/stage combination."
- **Pillar score labels**: Each axis displays the pillar name and numeric score at the outer edge.

#### 2.3.3 Layout Description

The Spider Chart is centred on Page 2, occupying the full width of the content area, with a height equivalent to approximately one-third of the page. It is rendered as a vector graphic (SVG in web view; embedded vector in PDF).

Below the chart, a three-item legend block identifies: (1) the startup's score polygon, (2) the confidence overlay, and (3) the benchmark line (if applicable).

To the right of or below the legend, a compact interpretation note (3–4 sentences maximum) explains how to read the chart. Example standard text: *"A larger overall polygon area indicates stronger aggregate evaluation performance. Significant indentations on individual axes indicate pillar-specific weaknesses that warrant focused attention. The dashed overlay shows the confidence range; wide dashes indicate lower data quality for that pillar. The grey benchmark line shows the median score for [Sector] startups at [Stage] stage in the TIDES database."*

#### 2.3.4 Space Allocation

The Spider Chart section occupies approximately **30–35% of Page 2**, including the chart itself, the legend, and the interpretation note. The chart graphic itself takes approximately 25% of Page 2.

#### 2.3.5 Quality Rules

**The AI must:**
- Plot all 8 axes even if a pillar score is zero or unavailable. A score of 0.0 due to insufficient data is plotted at the origin and labelled `[N/A — Insufficient Data]`.
- Display the confidence overlay whenever any pillar confidence is rated Medium or Low.
- Suppress the benchmark polygon entirely (and note its absence) if fewer than 5 startups in the same sector-stage combination exist in the TIDES benchmark database, to prevent statistically unreliable comparisons.
- Label every axis with both the pillar name and the numeric score (e.g., "Technology: 7.4").

**The AI must not:**
- Modify or smooth scores for visual appeal. The plotted values must exactly match the pillar scores in the Pillar Breakdown table.
- Use colour schemes that fail WCAG AA contrast requirements (see Section 3 — Visual Design Principles).
- Display the benchmark line without the data provenance note (sector, stage, sample size N, database version).

---

### 2.4 Page 2–3 — Pillar Breakdown Table

#### 2.4.1 Section Purpose

The Pillar Breakdown Table provides a structured, compact summary of all eight pillar evaluations in a single comparative view. It is the analytical backbone of the report — the section that translates raw scores into evaluated intelligence by presenting, for each pillar: the score, the evaluator's confidence in that score, the top evidence that drove the score, and the primary concern that limits the score.

This section serves committee members who want to understand the basis for each score without reading the full pillar-specific analysis sections. It also serves as a cross-reference index: every detailed claim in Sections 2.5–2.8 can be traced back to this table.

#### 2.4.2 Content Specification

The table contains one row per pillar (8 rows) and the following columns:

| Column | Content | Data Source | Constraints |
|---|---|---|---|
| **Pillar** | Pillar name | Static | Full name, not abbreviation |
| **Score** | Pillar score X.X / 10.0 | Respective Pillar Agent | Colour-coded: ≥7.5 = green, 5.0–7.4 = amber, <5.0 = red |
| **Confidence** | High / Medium / Low / Insufficient | Respective Pillar Agent | Displayed with icon |
| **Top Evidence** | Single most decisive piece of evidence used in scoring | Respective Pillar Agent (evidence list, item 1) | Max 20 words; must be specific (e.g., "Founder published 3 peer-reviewed papers in target domain, 2018–2022") |
| **Primary Concern** | The single most important limitation or risk in this pillar | Respective Pillar Agent (concern list, item 1) | Max 20 words; must name the specific gap or risk |
| **Agent** | Name/ID of the evaluating agent | Pipeline metadata | For traceability |

All 8 rows are mandatory. If an agent did not produce output for a pillar (e.g., due to a pipeline failure), the row is populated with `[EVALUATION INCOMPLETE — SEE APPENDIX]` and the overall report is flagged as requiring human review before distribution.

#### 2.4.3 Layout Description

The Pillar Breakdown Table is a full-width, 6-column table spanning the lower portion of Page 2 and the upper portion of Page 3. Row height is compact (single-line entries where possible; two-line maximum for Top Evidence and Primary Concern). Table uses alternating row shading (white / very light grey) for readability. The Score column is visually distinguished with colour-coded text or a small filled circle indicator.

A section header "Pillar Breakdown" appears above the table in 13pt bold, with a sub-note: "Scores out of 10.0. Confidence reflects data availability and source reliability."

#### 2.4.4 Space Allocation

The Pillar Breakdown Table occupies approximately **30–35% of Page 2** (lower half) and **20–25% of Page 3** (upper portion). Total allocation: approximately **10–12% of the report**.

#### 2.4.5 Quality Rules

**The AI must:**
- Use the exact same score values in this table as plotted in the Spider Chart. Any discrepancy between the table score and the chart score is a pipeline error and must trigger a validation failure.
- Ensure that "Top Evidence" is a specific item from the evidence log, not a category description. "Founder experience" is not acceptable. "Founder: 7 years as CTO at Series B SaaS company (LinkedIn, verified)" is acceptable.
- Ensure that "Primary Concern" is actionable or specific. "Limited market data" is not acceptable. "TAM estimate based on a single 2019 Gartner report; no primary research cited" is acceptable.
- Colour-code the Score column consistently with the colour scheme defined in Section 3.

**The AI must not:**
- Repeat the same evidence item in multiple rows. Evidence shared across pillars must be attributed to the most relevant pillar and cross-referenced in others.
- List a concern that is directly contradicted by a stated strength. Contradictions must be resolved by the Synthesis Agent before report assembly; unresolved contradictions must be flagged.

---

### 2.5 Page 3 — Founder Analysis

#### 2.5.1 Section Purpose

The Founder Analysis section provides a structured assessment of the founding team's capability, completeness, and fit for the specific opportunity being pursued. Research consistently identifies founding team quality as one of the strongest predictors of startup outcomes. This section translates the Founder Evaluation Agent's outputs into a readable, evidence-grounded profile of each founder and an assessment of the team as a whole.

This section is of particular interest to mentors, angel investors, and program officers who want to understand whether the people behind the startup have the domain expertise, execution experience, and interpersonal dynamics to navigate the challenges ahead.

#### 2.5.2 Content Specification

**Part A — Individual Founder Profiles**

For each founder, the following fields are populated from the Founder Evaluation Agent's structured output, drawing on submitted CVs, LinkedIn profiles, and any published work:

| Field | Content | Constraints |
|---|---|---|
| **Name** | Full name | As submitted |
| **Role** | Formal role in the startup | CEO / CTO / COO / CPO / Other — exact title |
| **Key Credentials** | Up to 3 most relevant credentials | Degree (institution, field, year), prior company roles (title, company, stage), notable achievements (patent, publication, exit) |
| **Domain Expertise** | Assessment of depth in the startup's primary domain | One of: Deep Domain Expert / Strong Adjacent / Generalist with Domain Learning / No Clear Domain Alignment |
| **Relevant Prior Experience** | Most relevant prior role or accomplishment | 1 sentence; specific and verifiable |
| **Red Flags** | Any founder-level concerns | Gaps in CV, unverified claims, conflicts of interest; "None identified" if applicable |

Maximum 4 founders displayed in the main section. If the team has more than 4 founders, a note directs readers to the Appendix for complete founder profiles.

**Part B — Team Assessment**

| Assessment Dimension | Content | Data Source |
|---|---|---|
| **Team Completeness** | Does the founding team cover the key functional domains required for this startup's stage and sector? | Founder Evaluation Agent — cross-referenced against TIDES Team Completeness Matrix |
| **Missing Functional Roles** | Specific roles absent from the founding team that are critical for the next 12 months | Founder Evaluation Agent output |
| **Founder-Market Fit** | How well does the team's combined background position them to solve this specific problem for this specific customer? | Synthesis Agent — rated: Strong / Moderate / Weak |
| **Team Dynamics Indicators** | Any signals from submission content suggesting alignment, conflict, or imbalance | Founder Evaluation Agent — qualitative note, 1–2 sentences |
| **Critical Team Gaps** | The 1–2 most important capability gaps that could materially limit execution | Founder Evaluation Agent output |

**TIDES Team Completeness Matrix (reference):**

| Startup Stage | Minimum Required Functional Coverage |
|---|---|
| Ideation | Domain expert + business generalist |
| Validation | Domain expert + business lead + technical lead (or plan to hire) |
| Early Traction | Domain expert + CEO + CTO + sales/BD lead |
| Growth | Full C-suite or clear hiring roadmap to full C-suite within 6 months |
| Scale | Full C-suite + functional VPs or equivalents |

#### 2.5.3 Layout Description

The Founder Analysis section occupies the middle portion of Page 3. Founder profiles are displayed in a compact card format: each founder occupies one row of a structured table with columns for Name, Role, Key Credentials, Domain Expertise, and Red Flags. If there are more than 2 founders, the table continues without additional visual treatment.

The Team Assessment fields are displayed below the founder table as a two-column key-value block: dimension names on the left (bold), assessment values on the right. The Founder-Market Fit rating is displayed with a colour indicator (green/amber/red).

#### 2.5.4 Space Allocation

The Founder Analysis section occupies approximately **35–40% of Page 3**. Individual founder profiles take approximately 60% of this allocation; team assessment takes 40%.

#### 2.5.5 Quality Rules

**The AI must:**
- Distinguish between claimed credentials and verified credentials. If a credential was verified against a public source (LinkedIn, institutional website, publication database), it is presented as stated. If it was not verifiable, it is appended with `[CLAIMED — UNVERIFIED]`.
- Apply the Team Completeness Matrix explicitly. The Team Completeness assessment must name which roles are present and which are absent, not simply state "the team appears complete."
- Express Founder-Market Fit as a compound judgment: the agent must cite at least one specific alignment (e.g., "Founder X's 8-year career at Apollo Hospitals directly maps to the target customer in the MedTech product") and, where applicable, one alignment gap.

**The AI must not:**
- Include personal information beyond professional credentials: age, nationality, marital status, photographs, and similar personal data are not included.
- Rate "Team Dynamics Indicators" negatively based solely on the absence of data. If no signals are available, the field reads "No adverse team dynamic signals identified in submission."
- Express opinions about founders' personalities, leadership styles, or interpersonal compatibility. The section is evidence-based, not psychographic.

---

### 2.6 Page 3–4 — Product & Technology Analysis

#### 2.6.1 Section Purpose

The Product & Technology Analysis section assesses the maturity, differentiation, technical soundness, and defensibility of the startup's core product and the technology underpinning it. It answers the questions investors, mentors, and technical reviewers most want answered: Does the product actually solve the problem? How mature is it? What makes it different? How solid is the technology? What IP exists? What are the key product risks?

This section draws on the outputs of two agents — the Product Evaluation Agent and the Technology Assessment Agent — and cross-references with the IP Assessment Agent for IP status.

#### 2.6.2 Content Specification

**Sub-section A — Product Assessment**

| Field | Content | Data Source | Constraints |
|---|---|---|---|
| **Product Description** | What the product is and what it does, in plain language | Product Evaluation Agent | 2–3 sentences; non-promotional; include form factor (SaaS / hardware / service / platform / other) |
| **Core Differentiation** | What is meaningfully different about this product compared to existing alternatives | Product Evaluation Agent | 1–3 specific differentiators as bullet points; each must be grounded in a product feature or characteristic, not a positioning claim |
| **MVP Status** | Current state of the product | Product Evaluation Agent | One of: Concept Only / Prototype / MVP / Beta / Commercially Available |
| **User Validation** | Evidence that real users have interacted with the product and responded | Product Evaluation Agent | Number of users/testers, feedback mechanism, outcome; "None documented" if absent |
| **Key Product Risks** | Top 2–3 risks specific to the product (not the market or the team) | Product Evaluation Agent | Bullet list; each risk is specific (e.g., "Core NLP model performance degrades significantly below 500-word input — not viable for the stated mobile use case") |

**Sub-section B — Technology Assessment**

| Field | Content | Data Source | Constraints |
|---|---|---|---|
| **TRL Level** | Technology Readiness Level (1–9) | Technology Assessment Agent | Integer with one-sentence justification citing the evidence that determined the TRL |
| **TRL Justification** | Specific evidence that determined the TRL rating | Technology Assessment Agent | 1–2 sentences; must cite observable artefact (prototype, demo, pilot deployment, etc.) |
| **Technology Stack** | Key technologies used (if disclosed) | Technology Assessment Agent | Bullet list of technology components; annotated with "disclosed" or "inferred from submission" |
| **Technical Complexity** | Assessment of the technical challenge involved | Technology Assessment Agent | One of: Low / Moderate / High / Very High; with 1-sentence rationale |
| **Technical Debt / Scalability Concerns** | Any concerns about the long-term technical architecture | Technology Assessment Agent | Bullet list; "None identified at current stage" if not applicable |

**Sub-section C — IP Status**

| Field | Content | Data Source | Constraints |
|---|---|---|---|
| **IP Status** | Summary of intellectual property position | IP Assessment Agent | One of: No IP / Trade Secret / Provisional Patent Filed / Patent Pending / Patent Granted / Multiple Patents |
| **IP Details** | Specifics of any filed or granted IP | IP Assessment Agent | Patent number or application reference if available; jurisdiction; date filed/granted |
| **IP Risk** | Risks to the IP position | IP Assessment Agent | 1–2 sentences; includes freedom-to-operate concerns if identified |

#### 2.6.3 Layout Description

The Product & Technology Analysis section spans the lower third of Page 3 and the upper third of Page 4. It uses a three-sub-section layout with bold sub-section headers ("Product Assessment," "Technology Assessment," "IP Status"). Each sub-section uses a compact two-column key-value format for structured fields, with bullet lists for differentiators, risks, and technology stack items. TRL Level is displayed with a visual indicator (numbered progression bar from 1 to 9 with the current level highlighted).

#### 2.6.4 Space Allocation

Product & Technology Analysis occupies approximately **30% of Page 3** (lower portion) and **30% of Page 4** (upper portion). Total allocation: approximately **10–12% of the report**.

#### 2.6.5 Quality Rules

**The AI must:**
- Assign TRL using the standard NASA/ESA Technology Readiness Level definitions. The justification must cite the observable evidence that maps to the TRL definition (e.g., TRL 4 requires "technology validated in laboratory environment" — the justification must cite the specific lab validation evidence from the submission).
- Distinguish between technology the startup has built versus technology they have licensed or integrated. Third-party dependencies are noted separately.
- Rate Core Differentiation claims critically. If a claimed differentiator is also claimed by two or more competitors identified by the Market Analysis Agent, it is flagged as `[WEAK DIFFERENTIATOR — ALSO CLAIMED BY COMPETITORS]`.

**The AI must not:**
- Accept self-reported TRL levels from the startup without independent assessment. The Technology Assessment Agent independently determines TRL from the evidence.
- Omit the IP Risk field if the IP Assessment Agent has identified any freedom-to-operate concern, regardless of how minor.
- Describe the product as "innovative," "cutting-edge," or similar without citing the specific technical characteristic that supports the assessment.

---

### 2.7 Page 4 — Market & Competition Analysis

#### 2.7.1 Section Purpose

The Market & Competition Analysis section establishes the size and accessibility of the opportunity, the timing of the market entry, and the competitive landscape the startup must navigate. It answers: Is the market large enough to justify investment? Is this the right time to enter? Who are the competitors and can this startup win against them?

This section is of primary interest to investors and program officers evaluating opportunity scale. It draws on the Market Analysis Agent's outputs, which combine submission-provided data with external market intelligence sources.

#### 2.7.2 Content Specification

**Sub-section A — Market Sizing**

| Field | Content | Data Source | Constraints |
|---|---|---|---|
| **TAM** (Total Addressable Market) | Total global/regional market for the problem being solved | Market Analysis Agent + external sources | USD value + basis for estimate + source name + year |
| **SAM** (Serviceable Addressable Market) | Portion of TAM reachable with current product and GTM | Market Analysis Agent | USD value + segmentation logic |
| **SOM** (Serviceable Obtainable Market) | Realistic market share achievable in 3–5 years | Market Analysis Agent | USD value + % of SAM + basis for estimate |
| **Market Growth Rate** | CAGR of the primary market | External market intelligence | % CAGR + period + source |
| **Source Quality Assessment** | Quality rating of the market sizing sources | Market Analysis Agent | One of: Primary Research / Tier-1 Industry Report / Tier-2 Industry Report / Founder Estimate / Unverified |

All market sizing figures must include the year of the source data. Outdated sources (more than 3 years old for rapidly evolving markets, more than 5 years for stable markets) must be flagged `[SOURCE MAY BE OUTDATED]`.

**Sub-section B — Market Timing**

| Field | Content | Data Source | Constraints |
|---|---|---|---|
| **Market Timing Assessment** | Is now the right time for this solution? | Market Analysis Agent | One of: Ahead of Market / Well-Timed / Late Entry / Market Saturating |
| **Timing Rationale** | Evidence for the timing assessment | Market Analysis Agent | 2–3 sentences; citing regulatory changes, technology inflection points, demand shifts, or competitive dynamics |

**Sub-section C — Competitive Landscape**

Top 3 competitors are displayed in a structured comparison table:

| Dimension | Competitor 1 | Competitor 2 | Competitor 3 | This Startup |
|---|---|---|---|---|
| **Company Name** | | | | [Startup Name] |
| **Funding Stage** | | | | |
| **Key Product** | | | | |
| **Primary Differentiator** | | | | |
| **Pricing Model** | | | | |
| **Key Weakness** | | | | |
| **Geography** | | | | |

Below the competitor table, a **Competitive Moat Assessment** presents the startup's defensibility in 2–3 sentences, assessing: network effects, switching costs, proprietary technology, regulatory moat, brand, distribution advantage, or first-mover position. The moat assessment is rated: Strong / Moderate / Weak / No Identified Moat.

#### 2.7.3 Layout Description

Market & Competition Analysis occupies the middle and lower portions of Page 4. The market sizing figures are displayed in a compact three-item visual block (TAM > SAM > SOM as nested concentric rectangles or a three-step funnel diagram) accompanied by the figures and source attributions. The competitor table is full-width. The Competitive Moat Assessment appears as a labelled paragraph below the competitor table.

#### 2.7.4 Space Allocation

Market & Competition Analysis occupies approximately **40–45% of Page 4**. Market sizing takes 20%, competitive table takes 55%, moat assessment takes 25% of this section's allocation.

#### 2.7.5 Quality Rules

**The AI must:**
- Attribute every market figure to a named source with a year. "Industry estimates suggest" is not acceptable. "Grand View Research, 2024" is acceptable.
- Flag any market size figure that was provided in the submission without independent corroboration as `[FOUNDER ESTIMATE — NOT INDEPENDENTLY VERIFIED]`.
- Identify competitors using objective criteria: companies offering products that solve the same problem for the same customer segment, not merely companies in the same broad industry.
- Note if no direct competitors could be identified, with the specific reason (e.g., "No direct competitors identified in commercial databases — market may be nascent or the search terms may be insufficient for this domain").

**The AI must not:**
- Use the startup's own TAM/SAM/SOM figures without cross-checking against at least one external source. Discrepancies of more than 30% between startup-provided and independently estimated figures must be flagged.
- Describe the market as "underserved" or "fragmented" without citing specific evidence of those characteristics.
- Include more than 3 competitors in the main table. Additional competitors may be listed in the Appendix.

---

### 2.8 Page 4–5 — Financial Analysis

#### 2.8.1 Section Purpose

The Financial Analysis section presents a structured assessment of the startup's current financial position, the clarity and viability of its revenue model, and its financial risks. For early-stage startups (Ideation/Validation), many financial fields will have limited or no data; the section must accurately represent this reality without fabricating or extrapolating figures. For later-stage startups, the section provides quantitative insight into financial health and sustainability.

This section is of primary interest to investors and program officers concerned with capital efficiency, funding needs, and financial risk.

#### 2.8.2 Content Specification

| Field | Content | Data Source | Constraints |
|---|---|---|---|
| **Current Financial Status** | Revenue status and funding situation | Financial Analysis Agent | One of: Pre-Revenue / Revenue Generating (non-recurring) / MRR Stage / ARR Established; plus current monthly/annual revenue figure if available |
| **Revenue Model Clarity** | How clearly defined and validated is the revenue model | Financial Analysis Agent | One of: Clearly Defined & Validated / Defined but Unvalidated / Partially Defined / Undefined |
| **Revenue Streams** | Named revenue streams | Financial Analysis Agent | Bullet list of streams (e.g., SaaS subscription, implementation fee, professional services); include pricing if disclosed |
| **Monthly Burn Rate** | Monthly cash outflow | Financial Analysis Agent | USD/month; if not disclosed, state "Not disclosed in submission" |
| **Runway** | Months of operation at current burn before capital exhaustion | Financial Analysis Agent | Months figure + calculation basis; or "Not calculable — burn rate not disclosed" |
| **Unit Economics** | Key per-unit financial metrics | Financial Analysis Agent | CAC (Customer Acquisition Cost), LTV (Lifetime Value), LTV:CAC ratio, Gross Margin; each with "disclosed," "calculated from submission data," or "not available" |
| **Funding History** | All prior rounds and grants | Financial Analysis Agent | Table: Round name, amount, date, lead investor/grantor; "No prior funding" if applicable |
| **Current Raise** | Current fundraising details | Submission metadata | Amount sought, instrument (equity, SAFE, convertible note), valuation (if disclosed), use of funds summary |
| **Financial Risk Assessment** | Top 2–3 financial risks | Financial Analysis Agent | Bullet list; specific risks (e.g., "Burn rate of ₹12L/month with 4 months runway and no confirmed next round creates high near-term capital risk") |

**Funding History Table Format:**

| Round | Amount | Date | Investor / Grantor | Notes |
|---|---|---|---|---|
| Pre-seed | USD X | Month YYYY | [Name] | SAFE / Equity / Grant |
| BIRAC Grant | INR X | Month YYYY | BIRAC | Government grant, non-dilutive |

If no funding history exists, a single row reads: "No prior external funding received."

#### 2.8.3 Layout Description

The Financial Analysis section spans the lower portion of Page 4 and the upper portion of Page 5. It uses a two-column layout for the structured fields (field name left, value right), with the Funding History table displayed full-width below the two-column block. The Financial Risk Assessment is displayed as a bulleted list with a light amber background band to visually signal risk content.

Unit Economics, if available, are displayed as a compact four-box grid (CAC | LTV | LTV:CAC | Gross Margin) with values prominently displayed and the calculation basis noted in small type below each value.

#### 2.8.4 Space Allocation

Financial Analysis occupies approximately **20% of Page 4** (lower portion) and **25% of Page 5** (upper portion). Total allocation: approximately **8–10% of the report**.

#### 2.8.5 Quality Rules

**The AI must:**
- Clearly distinguish between disclosed figures (from the submission) and calculated figures (derived by the agent from submission data). Calculated figures must include the calculation basis.
- Express runway in months with a specific calculation: "Runway: 6 months (cash balance INR 72L ÷ burn rate INR 12L/month, as of March 2026)."
- Flag any unit economics figure with an LTV:CAC ratio below 1.0 as a critical financial risk, regardless of other financial indicators.
- Note explicitly if financial projections are not supported by disclosed actuals, and rate the projection reliability as: Grounded in Actuals / Partially Grounded / Not Grounded.

**The AI must not:**
- Present financial projections provided by the startup as if they are current actuals. Projections and actuals must be clearly distinguished in all cases.
- Extrapolate revenue growth rates beyond what is supported by the evidence. If a startup has 3 months of revenue data, the agent may not project a 3-year growth curve as a "likely trajectory."
- Omit the burn rate and runway fields if they can be calculated from disclosed data. These fields may only read "Not calculable" when the underlying data is genuinely absent.

---

### 2.9 Page 5 — Risk Matrix

#### 2.9.1 Section Purpose

The Risk Matrix provides a systematic, categorised assessment of the risks facing the startup across all major risk domains. It enables readers to understand not just what the risks are, but how serious each risk is (likelihood × impact) and what the startup could do about the most critical ones.

This section is mandatory in all TAES evaluation reports regardless of the startup's stage, sector, or score. A startup with a high overall score may still have significant risks; the Risk Matrix ensures these are not buried in the narrative.

#### 2.9.2 Content Specification

Risks are assessed and categorised by the Risk Assessment Agent across six risk categories:

| Category | Description |
|---|---|
| **Technical** | Risks related to the technology not working, scaling, or remaining secure as expected |
| **Market** | Risks related to market size, demand, customer adoption, or competitive displacement |
| **Regulatory** | Risks related to compliance requirements, licencing, government policy, or legal exposure |
| **Financial** | Risks related to capital availability, burn, revenue model failure, or financial fraud |
| **Team** | Risks related to key-person dependency, attrition, skills gaps, or founder conflict |
| **Execution** | Risks related to the startup's ability to deliver on its plan within its resource constraints |

**Risk Rating Dimensions:**

Each identified risk is rated on two dimensions:

| Dimension | Scale |
|---|---|
| **Likelihood** | Low (event unlikely in next 18 months) / Medium (plausible) / High (probable or already occurring) |
| **Impact** | Low (manageable setback) / Medium (significant disruption to plan) / High (existential threat) |

**Risk Matrix Table Format:**

| Risk Category | Risk Description | Likelihood | Impact | Severity | Mitigation Suggestion |
|---|---|---|---|---|---|
| Technical | [Specific risk] | Medium | High | Critical | [1-sentence mitigation] |
| Market | [Specific risk] | Low | High | High | [1-sentence mitigation] |

**Severity** is computed from Likelihood × Impact using the standard 3×3 matrix:

| | Low Impact | Medium Impact | High Impact |
|---|---|---|---|
| **Low Likelihood** | Low | Low | Medium |
| **Medium Likelihood** | Low | Medium | High |
| **High Likelihood** | Medium | High | Critical |

The Risk Matrix must include all identified risks from the Risk Assessment Agent's output. There is no minimum or maximum row count; however, a report with fewer than 4 risks identified should be flagged for human review, as this likely indicates an incomplete assessment.

**Top 3 Critical Risks** are highlighted in a separate sub-section below the matrix with a dedicated mitigation paragraph for each (2–3 sentences per risk).

#### 2.9.3 Layout Description

The Risk Matrix occupies the middle portion of Page 5. The matrix table is full-width, with colour-coded Severity cells (red = Critical, orange = High, amber = Medium, green = Low). The Top 3 Critical Risks are displayed below the table as numbered items with a bolded risk statement followed by the mitigation paragraph in regular text.

#### 2.9.4 Space Allocation

The Risk Matrix occupies approximately **35–40% of Page 5**, including the table and the critical risk sub-section. If the number of identified risks exceeds 10, additional rows are moved to the Appendix and a note in the main section reads: "Full risk register (N risks) available in Appendix A."

#### 2.9.5 Quality Rules

**The AI must:**
- Describe each risk as a specific event or condition, not a category label. "Regulatory risk" is not a risk. "Failure to obtain CDSCO medical device approval within the planned 18-month timeline" is a risk.
- Apply severity ratings consistently using the 3×3 matrix defined above. Severity may not be manually overridden by the agent without a logged justification.
- Provide a mitigation suggestion for every Critical-severity risk. Mitigation suggestions must be specific and actionable (e.g., "Engage CDSCO pre-submission consultation to identify documentation gaps before formal application filing").
- Cross-reference identified risks with concerns raised in other sections (Founder Analysis, Product Analysis, Financial Analysis) to ensure consistency.

**The AI must not:**
- List generic risks that apply to all startups (e.g., "market may not develop as expected," "the team may face challenges") without startup-specific qualification.
- Assign a "Low / Low" risk that does not represent a genuine assessed risk. The Risk Matrix must contain only risks the agent has specifically identified from evidence in the submission or from sector intelligence.

---

### 2.10 Page 5–6 — Improvement Roadmap

#### 2.10.1 Section Purpose

The Improvement Roadmap is the most actionable section of the TAES Evaluation Report. It translates the analytical findings across all eight pillars into a prioritised, specific, and feasible set of improvements the startup should pursue. It is written for the startup founder as the primary reader of this section, while remaining informative for program officers who must design mentoring or intervention plans.

The Improvement Roadmap does not repeat concerns or scores. It converts identified gaps into directives: what specific action should be taken, why it matters (which pillar it addresses), how hard it is, and how urgently it should be done.

#### 2.10.2 Content Specification

The Roadmap contains 3–5 specific, actionable improvement items. Each item is structured as follows:

| Field | Content | Data Source | Constraints |
|---|---|---|---|
| **Improvement** | A specific, actionable task the startup should undertake | Synthesis Agent (drawing on pillar agent concern outputs) | Must start with an action verb; max 20 words for the title |
| **Pillar Addressed** | Which scoring pillar this improvement will impact | Cross-referenced from Pillar Breakdown | One or two pillars |
| **Why It Matters** | The consequence of not addressing this improvement | Synthesis Agent | 1–2 sentences; must state the risk or missed opportunity |
| **Priority** | Urgency classification | Synthesis Agent | One of: Critical / Important / Optional |
| **Estimated Effort** | Qualitative effort estimate | Synthesis Agent | One of: Days / Weeks / Months / Multi-quarter |
| **Suggested First Step** | The single most concrete first action to initiate this improvement | Synthesis Agent | 1 sentence; must be actionable immediately (e.g., "File a provisional patent application with a registered patent attorney in the target market jurisdiction within 30 days") |

**Priority Definitions:**

| Priority | Definition |
|---|---|
| **Critical** | Failure to address this within 60 days materially risks programme disqualification, legal exposure, or irreversible competitive disadvantage |
| **Important** | Addressing this within 90 days would materially improve the startup's evaluation score and programme outcomes |
| **Optional** | Valuable but not time-sensitive; can be deferred beyond 90 days without significant consequence |

#### 2.10.3 Layout Description

The Improvement Roadmap occupies the lower portion of Page 5 and the upper portion of Page 6. Each improvement item is displayed as a numbered card: the improvement title in bold (12pt), followed by the structured fields as a compact two-column layout within the card. Priority is displayed as a colour-coded badge (red = Critical, amber = Important, grey = Optional). Estimated Effort is displayed as a timeline icon or simple label.

A note at the top of the section reads: "The following improvements are ranked by priority. Items marked Critical should be actioned immediately. This roadmap is generated from evaluated evidence, not from general startup best practice."

#### 2.10.4 Space Allocation

The Improvement Roadmap occupies approximately **20–25% of Page 5** (lower portion) and **25–30% of Page 6** (upper portion). Total allocation: approximately **8–10% of the report**. Each improvement card must not exceed 8 lines of content.

#### 2.10.5 Quality Rules

**The AI must:**
- Limit the Roadmap to 3–5 items. Comprehensiveness is not the goal; priority is. A startup that has 12 identified weaknesses should receive a roadmap of the 3–5 that matter most, in priority order.
- Link every improvement to a specific pillar score. An improvement that does not address a scored pillar is not a TAES Roadmap item.
- Make "Suggested First Step" immediately actionable. It must describe an action a founder can begin today, not a vague direction (e.g., not "strengthen the IP strategy" but "file a provisional patent application covering the core algorithm with a registered patent attorney in [jurisdiction]").
- Apply the Priority taxonomy strictly. A Critical item cannot be assigned to a startup that scored 8.0 or above on the relevant pillar, unless a specific override condition applies (such as a compliance risk that is not captured in the pillar score).

**The AI must not:**
- Generate generic startup advice unconnected to this startup's specific findings (e.g., "hire great people," "focus on product-market fit").
- List an improvement that is already complete according to the submission data.
- Assign Critical priority to more than 2 items unless there is exceptional justification logged in the agent output. Over-assigning Critical priority devalues the signal.

---

### 2.11 Page 6 — Final Recommendation

#### 2.11.1 Section Purpose

The Final Recommendation section is the formal, accountable output of the TAES evaluation. It states the recommendation, justifies it, qualifies it (if conditional), and establishes the next evaluation milestone. It is the section that programme officers and committee members act on. It must be unambiguous, authoritative, and signed.

This section is also the point at which human reviewer accountability is explicitly established. The AI generates the recommendation and justification; a named human reviewer validates and signs it before distribution.

#### 2.11.2 Content Specification

| Field | Content | Data Source | Constraints |
|---|---|---|---|
| **Formal Recommendation** | The recommendation category | Synthesis Agent | One of: Incubate / Conditional Incubation / Defer / Reject — displayed in large bold type |
| **Justification Narrative** | Explanation of the recommendation | Synthesis Agent | 3–5 sentences; must reference the overall score, at least 2 specific pillar outcomes, and the decisive factor(s) that determined the recommendation |
| **Conditions for Approval** | Specific conditions the startup must meet (Conditional Incubation only) | Synthesis Agent | Numbered list of conditions; each condition must be specific, verifiable, and time-bound. Not applicable for Incubate / Defer / Reject |
| **Suggested Next Milestone** | The next formal evaluation event | Synthesis Agent | Specific event type (e.g., "90-day follow-up evaluation focused on IP filing completion and pilot customer LOI") |
| **AI Confidence in Recommendation** | The system's confidence in this recommendation | Synthesis Agent | One of: High / Medium / Low; accompanied by 1-sentence explanation of the confidence basis |
| **Human Reviewer Block** | Identity and endorsement of the human reviewer | Human reviewer input | Fields: Reviewer Name, Role, Organisation, Date Reviewed, Signature (digital or handwritten), Notes (optional) |

**Recommendation Justification Quality Criteria:**

A valid justification narrative for each recommendation category must contain the following elements:

| Recommendation | Required Justification Elements |
|---|---|
| **Incubate** | Overall score ≥ 8.0, minimum 2 pillars scored ≥ 8.0, no Critical risks unmitigated, positive Founder-Market Fit |
| **Conditional Incubation** | Score 6.5–7.9, or score ≥ 8.0 with a specific critical gap; conditions must address the specific gap(s) |
| **Defer** | Score 5.0–6.4, or identified structural weaknesses not addressable in a short timeframe; re-evaluation timeline must be specified |
| **Reject** | Score < 5.0, or identified disqualifying conditions (e.g., fraudulent claims, unresolvable IP conflict, team not capable of execution at any realistic level) |

**Conditions for Conditional Incubation Format:**

Each condition must follow this template:
> Condition [N]: [Specific deliverable] must be [completed / submitted / demonstrated] by [specific date or milestone], verified by [specific verifier (e.g., TIDES IP Advisor, independent technical reviewer)].

Example:
> Condition 1: A provisional patent application covering the core machine learning inference engine must be filed with a registered patent attorney in the Indian jurisdiction and confirmation provided to the TIDES programme office by 30 September 2026, verified by the TIDES IP Advisor.

#### 2.11.3 Layout Description

The Final Recommendation section occupies the lower portion of Page 6. The Formal Recommendation is displayed in large (18pt) bold type with a colour-coded background block (green for Incubate, amber for Conditional, orange for Defer, red for Reject). The Justification Narrative follows in standard body text. Conditions for Approval (if applicable) are displayed as a numbered list in a bordered box with a light amber background.

The Human Reviewer Block is displayed at the very bottom of Page 6, using a formal layout with labelled fields and a signature line. A watermark or banner across the top of Page 6 reads "EVALUATION PENDING HUMAN REVIEW" until the reviewer block is completed and the report is finalised.

The AI Confidence in Recommendation is displayed as a compact labelled badge adjacent to the Justification Narrative.

#### 2.11.4 Space Allocation

The Final Recommendation section occupies approximately **50–55% of Page 6** (below the Improvement Roadmap continuation). The Formal Recommendation display takes 15%, Justification Narrative takes 30%, Conditions (if applicable) takes 25%, and the Human Reviewer Block takes 30%.

#### 2.11.5 Quality Rules

**The AI must:**
- Use only the four approved recommendation categories. The Synthesis Agent may not generate intermediate categories, qualified descriptions, or ranked variations.
- Ensure the Justification Narrative explicitly names the scores and evidence that determined the recommendation. A narrative that could be copy-pasted onto a different startup's report is non-compliant.
- Generate conditions that are verifiable. A condition that cannot be objectively assessed by a reviewer ("improve team dynamics," "demonstrate market understanding") is non-compliant.
- Flag any recommendation of Reject with a mandatory human escalation notice, requiring confirmation from two independent human reviewers before the report is distributed.

**The AI must not:**
- Use softening language in a Reject recommendation. If the evidence supports Reject, the recommendation is stated clearly without diplomatic hedging.
- Include the phrase "we recommend further due diligence" as a substitute for a formal recommendation category.
- Leave the Conditions for Approval blank for a Conditional Incubation recommendation. A Conditional Incubation with no conditions is a pipeline error and must be flagged for human review.

---

### 2.12 Appendix — Evidence Log & Metadata

#### 2.12.1 Section Purpose

The Appendix contains the complete evidentiary and operational metadata underlying the report. It is not counted toward the 5–6 page report limit and is not intended for routine reading by committee members or investors. Its primary audiences are: (1) human reviewers who need to verify a specific claim, (2) programme officers who need audit records, (3) platform engineers who need pipeline execution data, and (4) legal/compliance teams who need provenance records.

The Appendix is generated automatically by the pipeline and is attached to every report. Its presence is mandatory for all reports distributed to programme officers and above.

#### 2.12.2 Content Specification

**Appendix A — Full Evidence Log**

A structured log of all evidence items used in the evaluation, keyed to the pillar and field they supported.

| Evidence ID | Pillar | Field | Evidence Description | Source Type | URL / Reference | Verified? | Verification Method |
|---|---|---|---|---|---|---|---|
| EV-001 | Founder | Key Credentials | "Founder X: Listed as CTO at [Company], 2018–2022" | LinkedIn Profile | [URL] | Yes | Agent web retrieval, 2026-06-22 |
| EV-002 | Market | TAM | "Global MedTech market USD 603B by 2028, CAGR 5.4%" | Tier-1 Industry Report | Grand View Research, 2024 | Yes | Direct retrieval |

Source types: Submission Document / LinkedIn / Patent Database / Company Website / Industry Report / News Article / Academic Publication / Regulatory Database / Agent Inference.

**Appendix B — Document Sources Referenced**

A complete list of all documents included in the submission package and any external documents retrieved by agents during evaluation, with file names, document types, and retrieval dates.

**Appendix C — Evaluation Timestamp and Version Record**

| Field | Value |
|---|---|
| Evaluation Initiated | YYYY-MM-DD HH:MM:SS UTC |
| Evaluation Completed | YYYY-MM-DD HH:MM:SS UTC |
| Pipeline Version | vX.X.X |
| Report Schema Version | vX.X.X |
| TAES Standard Version | v1.0 |
| Scoring Rubric Version | vX.X |
| Human Reviewer (if completed) | [Name, Role, Timestamp] |
| Report Finalised | YYYY-MM-DD HH:MM:SS UTC |

**Appendix D — Agent Pipeline Execution Log Summary**

For each agent in the pipeline, a one-row execution record:

| Agent Name | Agent Version | Status | Execution Time | Input Tokens | Output Tokens | Errors / Warnings |
|---|---|---|---|---|---|---|
| Data Ingestion Agent | v2.1 | Success | 34s | 12,450 | 3,200 | None |
| Founder Evaluation Agent | v1.8 | Success | 67s | 8,100 | 2,400 | 1 Warning: LinkedIn profile unverifiable |

**Appendix E — Additional Founder Profiles** (if team size > 4)

Full structured profiles for all founders not included in the main report body, using the same format defined in Section 2.5.

**Appendix F — Extended Competitor List** (if more than 3 competitors identified)

Profiles for all competitors beyond the top 3 featured in the main report, using the same comparison dimensions defined in Section 2.7.

**Appendix G — Full Risk Register** (if more than 10 risks identified)

Complete risk register with all identified risks, using the same format defined in Section 2.9.

---

## 3. Visual Design Principles

This section defines the visual design rules that govern all TAES Evaluation Reports. These rules apply to both the PDF and web view formats. They are enforced by the Report Rendering Engine and must not be overridden by individual agents or report templates.

### 3.1 Typography

| Element | Typeface | Size | Weight | Colour |
|---|---|---|---|---|
| Report Title | Inter or equivalent sans-serif | 22pt | Bold | Brand Primary |
| Section Header | Inter | 13pt | Bold | Dark Charcoal (#1A1A2E) |
| Sub-section Header | Inter | 11pt | SemiBold | Dark Charcoal |
| Body Text | Inter | 10pt | Regular | Near-black (#2D2D2D) |
| Table Header | Inter | 9pt | Bold | White on Brand Primary |
| Table Body | Inter | 9pt | Regular | Near-black |
| Small / Metadata | Inter | 8pt | Regular | Mid-grey (#6B6B6B) |
| Recommendation Badge | Inter | 14pt | Bold | White on status colour |
| Overall Score | Inter | 32pt | Black (900) | Brand Primary or status colour |

**Line spacing:** Body text at 1.4× line height. Tables at 1.2× line height. No additional paragraph spacing beyond the defined line height.

**Margins:** Top 18mm, Bottom 18mm, Left 20mm, Right 20mm for A4 PDF. For US Letter, scale proportionally.

**Column gutter:** 6mm between columns in multi-column layouts.

### 3.2 Colour Usage

The TAES report uses a controlled colour system with five semantic colour categories:

| Colour Role | Hex Code | Usage |
|---|---|---|
| **Brand Primary** | #1B4F72 | Section headers, score bars, primary chart polygon, badges |
| **Incubate Green** | #1E8449 | Incubate recommendation, high scores (≥7.5), positive indicators |
| **Conditional Amber** | #D4AC0D | Conditional recommendation, medium scores (5.0–7.4), warnings |
| **Defer Orange** | #CA6F1E | Defer recommendation, notable concerns |
| **Reject Red** | #A93226 | Reject recommendation, critical risks, low scores (<5.0), red flags |
| **Neutral Grey** | #95A5A6 | Benchmark line, supplementary data, unavailable data |
| **Background Light** | #F4F6F7 | Alternating table rows, metadata blocks, card backgrounds |

**Colour restraint rules:**
- A maximum of 3 semantic colours may appear on any single page, excluding Brand Primary and Background Light.
- Status colours (green, amber, orange, red) must only appear in the contexts defined above. They must not be used decoratively.
- All text-on-colour combinations must meet WCAG AA minimum contrast ratio (4.5:1 for normal text, 3:1 for large text). Red on white and dark text on light backgrounds are the primary text modes.

### 3.3 Data Visualisation Standards

**Spider / Radar Chart:**
- Rendered in SVG (web) or embedded vector (PDF) — never rasterised.
- Minimum 300 DPI equivalent resolution for print formats.
- All axis labels in 8pt, pillar names in 9pt bold.
- Score polygon fill: Brand Primary at 30% opacity.
- Confidence overlay: Brand Primary dashed line, 1pt stroke.
- Benchmark polygon: Neutral Grey solid line, 0.75pt stroke.

**Market Sizing Diagram (TAM/SAM/SOM):**
- Nested rectangle or funnel format only. No 3D effects, no gradients.
- Each level labelled with: name, USD value, source.

**Score Progress Bars:**
- Horizontal bars, Brand Primary fill, light grey background track.
- Exact pixel width proportional to score on 0–10 scale.
- Numerical score displayed to one decimal place at the end of the bar.

**Risk Matrix:**
- Severity cells use status colour fills. Critical = Reject Red, High = Defer Orange, Medium = Conditional Amber, Low = Incubate Green.
- Text in all severity cells uses white for Critical and High; dark text for Medium and Low.

### 3.4 Accessibility

All TAES Evaluation Reports must meet the following accessibility requirements:

- **WCAG 2.1 Level AA compliance** for all text-on-background colour combinations.
- **Alt text** for all visual elements (Spider Chart, TAM/SAM/SOM diagram) in the web view format. Alt text describes the chart's content, not merely its type (e.g., "Radar chart showing 8 pillar scores: Founder 7.2, Product 6.8, Technology 8.1, Market 5.9, Business 6.5, Financial 4.8, IP 7.0, Risk 6.2. Highest: Technology. Lowest: Financial.").
- **Tagged PDF** structure (PDF/UA compliant) for all PDF outputs, enabling screen reader navigation.
- **No colour-only encoding:** All information conveyed by colour is also conveyed by text labels, icons, or patterns.
- **Minimum 10pt body text** in all rendered formats to maintain readability in print and on standard screens.

### 3.5 Branding

TAES Evaluation Reports carry the TIDES platform brand mark on the header of Page 1 and the footer of every page. The following branding rules apply:

- The TIDES logo appears in the top-left of the Page 1 header, followed by the report title "TIDES AI Evaluation Report" in Brand Primary.
- The report footer on every page displays: TIDES platform mark (small), page number (e.g., "Page 2 of 6"), report ID, and "TAES v1.0 — Confidential."
- Third-party logos (e.g., incubator partner logos) may appear in the Page 1 header if the report is produced under a co-branding arrangement, subject to the TIDES Co-Branding Policy.
- The startup's name and logo (if provided in the submission) appear in the Page 1 header alongside the TIDES mark.

---

## 4. Report Versioning

### 4.1 Versioning Rationale

Startups evaluated by the TIDES platform may undergo multiple evaluations: initial evaluation, re-evaluation after implementing improvements, and follow-up milestone evaluations. Each evaluation produces a new version of the report for that startup. The versioning system must ensure that: (a) all versions are preserved for audit purposes, (b) the most current version is clearly identified, (c) changes between versions are traceable, and (d) recipients know exactly which version they are reading.

### 4.2 Report Identifier Structure

Every TAES Evaluation Report is assigned a unique Report Identifier (Report ID) at the time of pipeline initiation:

```
TAES-[STARTUP-CODE]-[YYYY]-[VVV]
```

Where:
- `STARTUP-CODE` is a 6-character alphanumeric code assigned to the startup at registration (e.g., MEDTX1)
- `YYYY` is the four-digit year of the evaluation
- `VVV` is a zero-padded three-digit version number starting at 001

**Example:** `TAES-MEDTX1-2026-001` is the first evaluation report for startup MEDTX1 in 2026. `TAES-MEDTX1-2026-002` is the second (re-evaluation).

### 4.3 Version Increment Triggers

A new report version is created under the following conditions:

| Trigger | Version Increment Type | Notes |
|---|---|---|
| Initial evaluation | Creates v001 | Baseline report |
| Re-evaluation requested by startup after improvements | Increments to next VVV | Full pipeline re-run required |
| Human reviewer override of score or recommendation | Creates a sub-version (e.g., v001r1) | Only the overridden fields are updated; AI baseline preserved |
| Data correction (error in submitted data identified post-evaluation) | Creates a corrected version (e.g., v001c1) | Correction log appended; original version preserved |
| Periodic milestone re-evaluation | Increments to next VVV | Full pipeline re-run |

### 4.4 Version Display in Report

The current report version is displayed:
1. In the Executive Dashboard metadata (Section 2.1), under "Evaluation Version."
2. In the report header on Page 1.
3. In the report footer on every page.
4. In the Appendix C timestamp record.

### 4.5 Version Comparison

When a report is re-evaluated, the platform generates a **Version Comparison Summary** that can be attached to the new report as an additional appendix section. The comparison summary displays, for each pillar, the score change (previous → current), the recommendation change (if any), and the primary reason for significant score changes (>1.0 point in any pillar). This summary is generated automatically by the Versioning Module from the stored structured outputs of both evaluations.

### 4.6 Report Archival

All report versions are retained in the TIDES platform archive indefinitely, subject to the data retention policy of the programme operator. Reports may not be deleted. They may be archived (marked inactive, not shown by default in the dashboard) but must remain retrievable for audit. A report that has been superseded by a newer version displays a banner: "Superseded — See [Report ID of latest version]."

---

## 5. Report Security and Access Control

### 5.1 Security Classification

All TAES Evaluation Reports are classified as **Confidential — Programme Internal** by default. This classification governs storage, transmission, access, and distribution. Reports may not be shared with parties outside of the access control list (ACL) defined below without explicit authorisation from the Programme Director.

A report may be downgraded to **Restricted — Startup Distribution** if the Programme Director authorises distribution to the evaluated startup (typically for feedback purposes). When so downgraded, the Appendix D (Agent Pipeline Execution Log) is automatically redacted before distribution.

### 5.2 Access Control Matrix

The following matrix defines which roles have access to which report sections and which operations:

| Role | Full Report Access | Appendix Access | Download / Print | Modify (Override) | Share Externally |
|---|---|---|---|---|---|
| **Programme Director** | ✅ All versions | ✅ | ✅ | ✅ With audit log | ✅ With authorisation |
| **Evaluation Committee Member** | ✅ Current version | ✅ | ✅ | ❌ | ❌ |
| **Mentor / Technical Advisor** | ✅ Current version (assigned startups only) | ❌ | ✅ (PDF only) | ❌ | ❌ |
| **Investor (Invited)** | ✅ Pages 1–4 only (Executive view) | ❌ | ✅ (Watermarked PDF) | ❌ | ❌ |
| **Programme Officer** | ✅ Current version | ✅ | ✅ | ❌ (Can request override) | ❌ |
| **Startup Founder** | ✅ Pages 1–6 only (no Appendix) | ❌ | ✅ (Watermarked PDF) | ❌ | ❌ |
| **Platform Engineer** | ✅ All versions (for debugging) | ✅ | ✅ | ❌ | ❌ |
| **External Auditor** | ✅ All versions (audit scope only) | ✅ | ✅ (Controlled) | ❌ | ❌ |

### 5.3 Report Distribution Rules

**Investor Distribution:** Reports shared with investors are automatically watermarked with the investor's name, the distribution date, and the legend "CONFIDENTIAL — FOR AUTHORISED RECIPIENT ONLY — NOT FOR FURTHER DISTRIBUTION." The watermark is embedded in the PDF and is not removable by standard tools.

**Founder Feedback Distribution:** When a report is distributed to the evaluated startup for feedback purposes, the following modifications are applied automatically before distribution:
- Appendix A (Evidence Log) is redacted to remove specific evidence URLs and source references that could reveal intelligence-gathering methods.
- Appendix D (Agent Pipeline Execution Log) is fully redacted.
- The Competitor Analysis section (Section 2.7) retains all content, as this information is based on publicly available data.

**Committee Distribution:** Reports distributed to evaluation committee members are distributed as read-only PDF with copying and printing permitted but screenshotting discouragement watermarks applied in the web view.

### 5.4 Data Storage and Encryption

All report data — including structured agent outputs, rendered PDFs, and version history — is stored in the TIDES secure document store with the following requirements:
- Encryption at rest: AES-256
- Encryption in transit: TLS 1.3 minimum
- Access logging: All access events (view, download, print, share) are logged with user identity, timestamp, and IP address
- Geographic restriction: Report data must remain within the jurisdiction specified by the programme operator at programme setup
- Backup: Daily encrypted backup with 7-year retention for audit compliance

### 5.5 Breach and Unauthorised Access Protocol

If a report is accessed by an unauthorised party or distributed outside the ACL, the Programme Director is notified automatically within 15 minutes via the TIDES incident management system. The incident is logged, the affected report is flagged, and the ACL is audited. If a distribution breach is confirmed, all outstanding distribution links for that report are revoked immediately and a new secured version is issued.

---

## 6. Report Formats and Delivery

### 6.1 Format Overview

TAES Evaluation Reports are produced in three official formats: PDF, Web View, and API JSON. All three formats are generated simultaneously by the Report Rendering Engine upon pipeline completion. They are all considered primary outputs; no format is a derivative of another. All three must contain identical data.

### 6.2 PDF Format

**Purpose:** The PDF is the official, legally recognised version of the report. It is the format used for committee review, archival, investor distribution, and regulatory compliance.

**Specification:**
- Format: PDF/A-3b (ISO 19005-3) for long-term archival compliance; PDF/UA (ISO 14289) for accessibility compliance
- Page size: A4 (210 × 297mm) primary; US Letter (8.5 × 11in) variant available on request
- Page count: 6 pages maximum (body) + Appendix (no page limit)
- Colour profile: sRGB for screen; CMYK conversion available for print distribution
- Fonts: Embedded subset
- Image resolution: Minimum 150 DPI for screen; 300 DPI for print
- Digital signature: Programme Director digital signature embedded in the PDF at report finalisation, using X.509 certificate
- File naming: `TAES-[STARTUP-CODE]-[YYYY]-[VVV]-Report.pdf`
- File size target: < 5MB for the body report; < 15MB including Appendix

**PDF Generation Process:**
The PDF is generated from the report's HTML/CSS web view using a headless browser rendering engine (e.g., Chromium-based) with the print stylesheet applied. The rendering engine enforces page break rules defined in the report CSS. The final PDF is digitally signed and stored in the secure document store.

### 6.3 Web View Format

**Purpose:** The Web View is an interactive, browser-based version of the report intended for online review, navigation, and annotation. It is the format used in the TIDES platform dashboard.

**Specification:**
- Rendered as a responsive single-page application (SPA) or multi-page HTML document
- Supported browsers: Chrome 115+, Firefox 115+, Safari 16+, Edge 115+
- Mobile responsive: Yes — reflows to single-column layout on screens narrower than 768px
- Interactive features:
  - Clickable section navigation (table of contents sidebar)
  - Expandable evidence citations (hover/click on any claim to see the evidence source)
  - Score tooltips (hover over any score to see the confidence band and evidence count)
  - Annotation mode: Authorised reviewers can add inline comments in the web view; comments are stored separately and do not modify the report content
  - Spider Chart: Interactive (hover to see pillar name, score, and confidence on each axis)
  - Print to PDF: "Download PDF" button generates the PDF format on demand
- Accessibility: WCAG 2.1 AA compliant, keyboard navigable, screen reader compatible
- Authentication: TIDES platform login required; session-based access control aligned with ACL in Section 5.2

### 6.4 API JSON Format

**Purpose:** The API JSON format provides machine-readable access to all structured report data for integration with external systems, dashboards, ERP systems, and partner platforms.

**Specification:**
- Format: JSON (RFC 8259 compliant)
- Schema: TAES Report JSON Schema v1.0 (separately documented in `TAES_v1.0/schemas/report_schema_v1.0.json`)
- Endpoint: `GET /api/v1/reports/{report_id}`
- Authentication: API key (Bearer token) with role-based scope
- Response structure:

```json
{
  "report_id": "TAES-MEDTX1-2026-001",
  "version": "1.0.0",
  "schema_version": "1.0",
  "generated_at": "2026-06-23T10:45:00Z",
  "finalised_at": "2026-06-23T14:30:00Z",
  "startup": {
    "name": "string",
    "sector": "string",
    "sub_sector": "string",
    "stage": "string",
    "trl": "integer",
    "location": "string"
  },
  "executive_dashboard": {
    "overall_score": "float",
    "confidence_level": "string",
    "recommendation": "string",
    "key_strengths": ["string", "string", "string"],
    "key_concerns": ["string", "string", "string"]
  },
  "pillar_scores": {
    "founder": { "score": "float", "confidence": "string" },
    "product": { "score": "float", "confidence": "string" },
    "technology": { "score": "float", "confidence": "string" },
    "market": { "score": "float", "confidence": "string" },
    "business_model": { "score": "float", "confidence": "string" },
    "financial": { "score": "float", "confidence": "string" },
    "ip": { "score": "float", "confidence": "string" },
    "risk": { "score": "float", "confidence": "string" }
  },
  "recommendation": {
    "category": "string",
    "justification": "string",
    "conditions": ["string"],
    "next_milestone": "string",
    "ai_confidence": "string",
    "human_reviewer": {
      "name": "string",
      "role": "string",
      "organisation": "string",
      "reviewed_at": "string"
    }
  },
  "risk_matrix": [ { "category": "string", "description": "string", "likelihood": "string", "impact": "string", "severity": "string" } ],
  "improvement_roadmap": [ { "title": "string", "pillar": "string", "priority": "string", "effort": "string", "first_step": "string" } ],
  "appendix": {
    "evidence_log_url": "string",
    "pipeline_log_url": "string"
  }
}
```

**API Rate Limits:**
- Standard: 100 requests per minute per API key
- Bulk export: Available via `GET /api/v1/reports?startup_id={id}&all_versions=true`
- Webhook: Reports can trigger a POST webhook notification to a registered endpoint upon finalisation

**API JSON Completeness Requirement:**
The API JSON must contain 100% of the structured data fields defined in this standard. Any field not available for a given report (e.g., benchmark data not available) must be represented as `null` with an accompanying `"field_unavailable_reason"` key. Fields may never be omitted from the JSON response.

### 6.5 Format Consistency Validation

At the time of report finalisation, the Report Consistency Validator module performs a cross-format check:
1. Every numerical score in the PDF matches the corresponding score in the API JSON.
2. The recommendation in the PDF matches the recommendation in the API JSON.
3. The number of risk items in the PDF Risk Matrix matches the number of items in the API JSON `risk_matrix` array.
4. The human reviewer identity in the PDF matches the reviewer record in the API JSON.

Any inconsistency detected by the validator triggers a pipeline alert and prevents report distribution until resolved.

---

*End of Document — TAES v1.0 / Report Standard / Version 1.0.0*

---

> **Revision History**
>
> | Version | Date | Author | Changes |
> |---|---|---|---|
> | 1.0.0 | 2026-06-23 | TIDES Standards Committee | Initial ratified version |
>
> **Next Scheduled Review:** 2027-06-23
>
> **Document Owner:** TIDES Platform Engineering & Standards Committee
>
> **Approvals:** Programme Director (signature on file) | Chief Evaluation Officer (signature on file)
