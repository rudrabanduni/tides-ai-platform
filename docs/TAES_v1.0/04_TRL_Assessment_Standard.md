> **Document:** TAES v1.0 / TRL Assessment Standard
> **Classification:** Internal Technical Standard
> **Version:** 1.0.0
> **Issued By:** TIDES Platform Evaluation Authority
> **Effective Date:** 2026-06-23
> **Review Cycle:** Annual or upon significant platform update
> **Supersedes:** None (inaugural version)
> **Audience:** AI Evaluation Agents, Human Analysts, Incubator Staff, VC Technical Due-Diligence Teams, Government Evaluation Bodies

---

# TIDES AI Evaluation Standard (TAES v1.0)
# Module 04: Technology Readiness Level (TRL) Assessment Standard

---

## Table of Contents

1. [Introduction and Purpose](#1-introduction-and-purpose)
2. [Origins of TRL: NASA, ESA, and the Standardization Journey](#2-origins-of-trl-nasa-esa-and-the-standardization-journey)
3. [How TIDES Adapts TRL for Startup Evaluation](#3-how-tides-adapts-trl-for-startup-evaluation)
4. [TRL Summary Table](#4-trl-summary-table)
5. [TRL Scoring Integration into the Technology Pillar](#5-trl-scoring-integration-into-the-technology-pillar)
6. [TRL vs. Business Readiness Level (BRL)](#6-trl-vs-business-readiness-level-brl)
7. [AI Agent Indeterminate TRL Rule](#7-ai-agent-indeterminate-trl-rule)
8. [TRL Gaming: Detection and Mitigation](#8-trl-gaming-detection-and-mitigation)
9. [TRL Level Definitions](#9-trl-level-definitions)
   - [TRL 1 — Basic Principles Observed](#trl-1--basic-principles-observed)
   - [TRL 2 — Technology Concept Formulated](#trl-2--technology-concept-formulated)
   - [TRL 3 — Experimental Proof of Concept](#trl-3--experimental-proof-of-concept)
   - [TRL 4 — Technology Validated in Laboratory](#trl-4--technology-validated-in-laboratory)
   - [TRL 5 — Technology Validated in Relevant Environment](#trl-5--technology-validated-in-relevant-environment)
   - [TRL 6 — Technology Demonstrated in Relevant Environment](#trl-6--technology-demonstrated-in-relevant-environment)
   - [TRL 7 — System Prototype Demonstrated in Operational Environment](#trl-7--system-prototype-demonstrated-in-operational-environment)
   - [TRL 8 — System Complete and Qualified](#trl-8--system-complete-and-qualified)
   - [TRL 9 — Actual System Proven in Operational Environment](#trl-9--actual-system-proven-in-operational-environment)
10. [Appendix A: TRL Evidence Checklist Master Reference](#appendix-a-trl-evidence-checklist-master-reference)
11. [Appendix B: Sector-Specific TRL Mapping Reference](#appendix-b-sector-specific-trl-mapping-reference)
12. [Appendix C: Document Change Log](#appendix-c-document-change-log)

---

## 1. Introduction and Purpose

Technology Readiness Level (TRL) is one of the most rigorously validated frameworks for measuring the maturity of an emerging technology. Originally devised for large-scale aerospace and defence programmes, the framework provides a structured, nine-point scale that allows evaluators to position a technology along its development trajectory — from the observation of a basic scientific phenomenon to the full operational deployment of a proven system.

Within the TIDES (Technology and Innovation Development Evaluation System) platform, TRL serves as the primary technical spine of startup evaluation. The TIDES platform is an AI-assisted due-diligence and evaluation engine designed for use by incubators, accelerators, venture capital firms, government grant-allocation agencies, and technology-transfer offices. It ingests structured and unstructured documentation submitted by startups — including technical white papers, prototype demonstration records, regulatory filings, pilot study reports, customer letters of intent, and financial projections — and produces a multi-dimensional evaluation score.

The TRL Assessment Standard, codified in this document as Module 04 of the TAES v1.0 specification, governs how the AI evaluation agent assigns a TRL level to a startup's core technology. It defines:

- The precise meaning of each TRL level as applied to startups (not government programmes)
- The specific evidence required at each level for the AI agent to make a confident assignment
- The rules for handling ambiguous, incomplete, or conflicting evidence
- The rules for detecting TRL misrepresentation (gaming)
- How the TRL score integrates with the broader Technology Pillar score in the TIDES evaluation model
- How TRL relates to, but is distinct from, Business Readiness Level (BRL)

This document is both a technical reference for the AI agent's inference rules and an operational manual for human analysts who review, override, or audit the agent's assessments. All AI agent behaviour described herein is normative; departures from this standard require documented justification and escalation to the Platform Evaluation Authority.

---

## 2. Origins of TRL: NASA, ESA, and the Standardization Journey

### 2.1 NASA Origins (1974–1989)

The concept of Technology Readiness Level was first articulated by Stanislaw Ulam and later systematised within NASA during the 1970s. The framework as a structured nine-level scale was formally documented by Stan Sadin at NASA in 1974 and refined into a published standard in 1989. NASA's original intent was to create a common vocabulary that programme managers, contractors, and engineers could use to communicate the maturity of space technology components — preventing the recurrent failure mode of integrating immature technologies into mission-critical spacecraft systems.

The original NASA TRL scale was explicitly calibrated for hardware systems: propulsion components, guidance electronics, materials, and communications subsystems. A technology at TRL 1 had only its underlying physical principles observed and reported in scientific literature. A technology at TRL 9 had been flight-proven in an actual mission. Every level in between represented a specific type of validation activity and a specific environment in which that validation occurred.

### 2.2 ESA and European Adoption (1999–2008)

The European Space Agency formally adopted and refined the TRL framework in the late 1990s, publishing its own TRL definitions in the ESA Technology Readiness Level Handbook (2008). ESA's contribution was to clarify the distinction between the *validation environment* (laboratory vs. relevant vs. operational) and the *type of activity* performed (analysis, demonstration, qualification, mission). This distinction became foundational for subsequent non-aerospace applications of TRL.

### 2.3 Broader Standardisation (2008–Present)

Following ESA's handbook, the TRL framework was adopted by:

- **European Commission** (Horizon 2020 and Horizon Europe programmes): TRL became a mandatory reporting metric for funded research projects, with definitions aligned to ISO 16290:2013
- **ISO 16290:2013**: The first international standard formalising TRL definitions for space systems
- **US Department of Defence (DoD)**: Adopted TRL with additional manufacturing readiness level (MRL) considerations
- **UK Research and Innovation (UKRI)**: Uses a TRL-derived scale for Innovate UK grant evaluation
- **DARPA**: Uses TRL as a gating criterion for programme phase transitions

By 2020, TRL had been adapted by dozens of national innovation agencies, technology transfer offices, and private investment firms — though with varying and sometimes incompatible definitions at the individual level boundaries.

### 2.4 Limitations of the Original Framework for Startup Evaluation

The original TRL framework was designed for government-funded, multi-year, programme-managed technology development. Applied naively to startup evaluation, it produces systematic errors:

1. **Hardware bias**: Original TRL definitions assume physical hardware artefacts. Software, AI/ML models, and platform technologies do not produce the same artefact types.
2. **Programme context assumption**: Original TRL assumes a funded programme with defined requirements documents (SRD, ICD, etc.). Startups rarely have these.
3. **No commercialisation signal**: Original TRL ends at mission deployment, which says nothing about commercial viability, pricing, distribution, or market fit.
4. **Single-technology scope**: Startups typically combine multiple technology components at different readiness levels; a single TRL number can misrepresent the system.
5. **Validation authority ambiguity**: Original TRL validation is performed by government labs or certified contractors. Startup validation is often internal or by early customers — of different evidentiary weight.

The TIDES adaptation addresses all five of these limitations explicitly, as described in the following section.

---

## 3. How TIDES Adapts TRL for Startup Evaluation

### 3.1 Core Adaptation Principles

The TIDES TRL framework preserves the nine-level structure and the fundamental logic of the original scale (increasing validation rigour, escalating environment fidelity, and decreasing development risk) while replacing hardware-centric language and government-programme assumptions with startup-appropriate equivalents.

The four core adaptation principles are:

**Principle 1 — Technology-Type Neutrality**: Each TRL level must be definable across hardware, software, AI/ML, biological, chemical, and hybrid technologies. Where the evidence type differs by technology category, the standard explicitly specifies sector-specific evidence equivalents rather than using a single evidence type as the default.

**Principle 2 — Commercialisation-Awareness**: TRL in the TIDES framework is evaluated alongside Business Readiness Level (BRL). A startup can be at TRL 7 with BRL 2 — technically advanced but commercially immature. The TRL score is not inflated by commercial signals, and commercial signals do not substitute for technical evidence.

**Principle 3 — Evidence-Weight Calibration**: Evidence produced by the founding team (internal) is weighted lower than evidence produced by independent third parties (external labs, regulators, customers). The AI agent's confidence score adjusts based on the independence and verifiability of submitted evidence.

**Principle 4 — Composite Technology Handling**: When a startup's solution combines multiple technology components, the AI agent assigns a TRL to each component and computes a system TRL as the lowest TRL among critical-path components (the "weakest link" rule). Non-critical components may be noted but do not determine the system TRL.

### 3.2 TIDES TRL vs. ISO 16290 and EC Horizon TRL

The following table summarises key definitional differences between the TIDES TRL standard and the two most widely-cited existing standards:

| Dimension | ISO 16290 (Space) | EC Horizon Europe | TIDES v1.0 |
|---|---|---|---|
| Primary domain | Space hardware | Research/R&D projects | Startup technologies (all sectors) |
| Software TRL | Appendix only | Partially addressed | First-class, fully specified |
| AI/ML TRL | Not addressed | Not addressed | Fully specified |
| Validation authority | ESA-approved test labs | Project partners / reviewers | Weighted by independence tier |
| Commercialisation | Not included | Partially (TRL 8–9) | Separated into BRL |
| Composite systems | Not addressed | Not addressed | Weakest-link system TRL rule |
| Gaming detection | Not addressed | Not addressed | Fully specified (Module 04 §8) |
| Confidence scoring | Not addressed | Not addressed | Required for every assignment |

### 3.3 The TIDES TRL Assignment Process

When the AI evaluation agent processes a startup's documentation package, it executes the following TRL assessment process:

1. **Technology decomposition**: Identify all distinct technology components in the startup's solution
2. **Component TRL assessment**: For each component, gather evidence, apply level definitions, assign preliminary TRL with confidence score
3. **Critical path identification**: Determine which components lie on the critical path to the startup's core value proposition
4. **System TRL computation**: Apply the weakest-link rule to critical-path components
5. **Gaming detection pass**: Apply TRL gaming detection rules (§8) to all assigned levels
6. **Confidence finalisation**: Compute final confidence score per component and for the system TRL
7. **Indeterminate rule check**: If confidence falls below threshold, apply the Indeterminate TRL Rule (§7)
8. **Technology Pillar score computation**: Map system TRL and confidence scores to the Technology Pillar score (§5)

---

## 4. TRL Summary Table

The following table provides a rapid-reference overview of all nine TRL levels as defined in the TIDES framework. Each level's one-line definition and typical correspondence to startup lifecycle stage are included.

| TRL | Level Name | One-Line Definition | Typical Startup Stage |
|---|---|---|---|
| **1** | Basic Principles Observed | Underlying scientific or engineering principle has been observed and reported | Pre-ideation / Research Phase |
| **2** | Technology Concept Formulated | Practical application of the principle has been conceptualised; no experimental work yet | Ideation / Concept Stage |
| **3** | Experimental Proof of Concept | Laboratory experiments confirm the concept is technically feasible | Pre-seed / Founder Lab Stage |
| **4** | Technology Validated in Laboratory | Key functional elements integrated and tested in a controlled lab setting | Pre-seed to Seed Stage |
| **5** | Technology Validated in Relevant Environment | Technology performs as specified in an environment that simulates real-world conditions | Seed Stage |
| **6** | Technology Demonstrated in Relevant Environment | Functional prototype demonstrated in a realistic environment to an external audience | Seed to Series A Stage |
| **7** | System Prototype Demonstrated in Operational Environment | Near-final prototype tested in the actual deployment environment with real constraints | Series A Stage |
| **8** | System Complete and Qualified | Final system passes all qualification tests; ready for first commercial deployment | Series A to Series B Stage |
| **9** | Actual System Proven in Operational Environment | System has been deployed and operated successfully in real commercial or operational conditions | Series B and beyond / Growth Stage |

> **Note on TRL Distribution in the TIDES Submission Pool**: Based on calibration data from evaluation exercises, the modal TRL for startups submitting to incubator and pre-seed grant programmes is TRL 3–4. Startups submitting to Series A investment evaluations typically range TRL 5–7. Claims of TRL 8–9 from pre-revenue startups are a primary trigger for TRL gaming investigation.

---

## 5. TRL Scoring Integration into the Technology Pillar

### 5.1 Technology Pillar Architecture

The TIDES evaluation model scores startups across five pillars: Technology, Market, Team, Financials, and ESG/Impact. The Technology Pillar contributes 30% of the total TIDES Score in the default weighting configuration (configurable by the evaluating organisation).

The Technology Pillar score is computed from four sub-dimensions:

| Sub-Dimension | Weight within Technology Pillar | Description |
|---|---|---|
| TRL Score | 40% | Maturity of the core technology |
| Technical Differentiation Score | 25% | Novelty and defensibility of the technical approach |
| IP Strength Score | 20% | Quality and coverage of intellectual property |
| Technical Team Capability Score | 15% | Depth of technical expertise on the founding team |

### 5.2 TRL-to-Score Mapping

The AI agent converts the assigned TRL level (1–9) and its associated confidence score into a TRL Score on a 0–100 scale using the following mapping:

| TRL Level | Base TRL Score | Confidence Multiplier Range | Effective Score Range |
|---|---|---|---|
| TRL 1 | 10 | 0.70 – 1.00 | 7 – 10 |
| TRL 2 | 20 | 0.70 – 1.00 | 14 – 20 |
| TRL 3 | 30 | 0.70 – 1.00 | 21 – 30 |
| TRL 4 | 42 | 0.70 – 1.00 | 29 – 42 |
| TRL 5 | 54 | 0.70 – 1.00 | 38 – 54 |
| TRL 6 | 65 | 0.70 – 1.00 | 46 – 65 |
| TRL 7 | 76 | 0.70 – 1.00 | 53 – 76 |
| TRL 8 | 88 | 0.70 – 1.00 | 62 – 88 |
| TRL 9 | 100 | 0.70 – 1.00 | 70 – 100 |

**Confidence Multiplier**: The confidence score is expressed as a value between 0.70 and 1.00. A confidence score below 0.70 triggers the Indeterminate TRL Rule (§7) and the TRL assignment is suspended pending additional evidence or human analyst review. The confidence multiplier is computed as:

```
Confidence = 0.70 + (0.30 × Evidence_Quality_Index)
```

Where `Evidence_Quality_Index` is computed from:
- **Completeness**: Fraction of required evidence items present (Must Have items weighted 2×, Should Have items weighted 1×)
- **Independence**: Average independence tier of evidence sources (Internal=0.5, Customer/Partner=0.8, Independent Lab=0.9, Regulator=1.0)
- **Recency**: Decay factor for evidence older than 24 months (5% per month of age beyond 24 months)
- **Specificity**: Whether evidence directly references the startup's technology (generic citations scored lower)

### 5.3 TRL Score Interpretation Thresholds

Evaluating organisations may configure threshold rules that gate specific decisions (e.g., investment, grant approval, programme admission) based on TRL Score. TIDES provides the following default thresholds as a reference configuration:

| Decision Gate | Minimum TRL Score | Minimum TRL Level | Notes |
|---|---|---|---|
| Pre-seed grant eligibility | 14 | TRL 2 | Concept must be defined |
| Incubator admission | 21 | TRL 3 | Experimental PoC required |
| Seed investment consideration | 38 | TRL 5 | Relevant environment validation required |
| Series A investment consideration | 53 | TRL 7 | Operational prototype required |
| Government procurement shortlist | 62 | TRL 8 | System qualification required |
| Full commercial deployment recommendation | 70 | TRL 9 | Proven operational system required |

### 5.4 TRL Trajectory Scoring

In addition to the point-in-time TRL Score, the TIDES platform computes a **TRL Trajectory Score** when a startup has submitted to the platform on more than one occasion (or has provided dated historical evidence across multiple TRL levels). The trajectory score rewards consistent, evidence-backed progression:

- Startups advancing one full TRL level per six-month period: Trajectory bonus of +5 points to Technology Pillar
- Startups advancing two or more TRL levels in under six months without corresponding evidence increase: Trajectory flag (potential gaming indicator)
- Startups with stagnant TRL across two or more evaluation cycles: Trajectory penalty of −3 points to Technology Pillar per cycle

---

## 6. TRL vs. Business Readiness Level (BRL)

### 6.1 Why TRL Alone Is Insufficient

A startup at TRL 9 has a fully operational, deployment-proven technology. This tells an evaluator precisely nothing about:

- Whether a market exists and is large enough to justify commercialisation
- Whether the startup has a viable business model, pricing strategy, or distribution channel
- Whether customers are willing to pay, or have paid, at sustainable unit economics
- Whether the founding team has the commercial capabilities to capture market share
- Whether the regulatory environment permits commercial sale in target markets
- Whether the competitive landscape leaves room for a new entrant at any price point

Conversely, a startup at TRL 3 with extraordinary commercial traction (signed LOIs, pilot customers, strong founder networks) is commercially promising but technically risky. Neither the TRL alone nor commercial indicators alone give a complete picture.

The TIDES platform therefore uses a parallel **Business Readiness Level (BRL)** scale (defined in TAES v1.0 Module 05) that measures commercial and organisational maturity on a nine-point scale analogous to TRL. The two scales are always reported together in the TIDES Evaluation Report.

### 6.2 TRL–BRL Matrix

The TRL–BRL matrix provides a diagnostic framework for categorising startups by their combined technical and commercial maturity:

| | **BRL 1–3 (Early Commercial)** | **BRL 4–6 (Mid Commercial)** | **BRL 7–9 (Mature Commercial)** |
|---|---|---|---|
| **TRL 1–3 (Early Technical)** | **Research Stage**: High-risk; appropriate for basic research grants, university spinout support | **Commercially Ahead**: Unusual; risk that commercial commitments outpace technical delivery | **Red Flag**: Commercial claims unsupported by technical maturity; investigate for TRL gaming |
| **TRL 4–6 (Mid Technical)** | **Technology Push**: Technically progressing but needs commercial validation urgently | **Balanced Development**: Healthy profile for seed-to-Series A; typical accelerator cohort | **Market Pull with Tech Risk**: Commercial engine running; technology must catch up |
| **TRL 7–9 (Mature Technical)** | **Technology Seeking Market**: Deep tech seeking product-market fit; significant pivot risk | **Scaling Mismatch**: Technical system ready but commercial operations not yet scaled | **Market Leader Profile**: Full readiness; appropriate for growth investment or acquisition |

### 6.3 Investment Decision Rules Based on TRL–BRL

The following rules govern how the TIDES platform flags evaluation outcomes when TRL and BRL are in significant imbalance:

1. **BRL exceeds TRL by 4 or more points**: Mandatory TRL gaming investigation flag. Extremely unlikely to have strong commercial traction without commensurate technical maturity. Evidence for both TRL and BRL must be independently verified.

2. **TRL exceeds BRL by 5 or more points**: Deep technology commercialisation risk flag. Technical validation is advanced but the startup has not developed the commercial apparatus to extract value. Flag for commercial strategy review.

3. **Both TRL and BRL below 3**: Research-stage classification. TIDES recommends routing evaluation to grant/basic research funding instruments rather than equity investment.

4. **TRL ≥ 7 and BRL ≤ 2**: Phantom product flag. A complete, operationally proven technology with no commercial evidence is highly unusual and warrants investigation for misrepresentation of technical status.

### 6.4 Interaction Rules in Scoring

When computing the final TIDES Score:
- TRL contributes to the Technology Pillar (see §5); BRL contributes to the Market Pillar
- TRL and BRL do not directly adjust each other's scores
- However, specific cross-pillar penalty rules apply when TRL–BRL imbalance exceeds defined thresholds (defined in TAES v1.0 Module 07: Cross-Pillar Interaction Rules)

---

## 7. AI Agent Indeterminate TRL Rule

### 7.1 Trigger Conditions

The AI evaluation agent must invoke the Indeterminate TRL Rule whenever any of the following conditions are met:

1. **Insufficient evidence**: The startup has not provided documentation sufficient to satisfy any "Must Have" evidence requirement at any single TRL level with confidence ≥ 0.70
2. **Conflicting evidence**: Two or more pieces of submitted evidence imply different TRL levels for the same technology component, and the conflict cannot be resolved by evidence quality weighting
3. **Unverifiable claims**: All evidence for a claimed TRL level comes from sources that cannot be independently verified (e.g., undated internal test reports with no external reference, verbal customer references with no written documentation)
4. **Technology not described**: The submitted documentation does not contain a sufficiently detailed technical description for the AI agent to identify the underlying technology principle
5. **Composite system with unresolvable component TRL**: In a composite system, one or more critical-path components cannot be assigned a TRL level with confidence ≥ 0.70, making system TRL computation impossible

### 7.2 Required Agent Behaviour Under the Indeterminate Rule

When the Indeterminate TRL Rule is triggered, the AI agent MUST:

**Step 1 — Document the trigger**: Record the specific trigger condition(s) that caused the Indeterminate Rule to activate. This must be included in the evaluation report with explicit reference to the evidence gap or conflict.

**Step 2 — Assign a tentative TRL floor**: Based on available evidence (even incomplete), assign the lowest TRL level for which at least 50% of Must Have requirements are satisfied. Label this as "TRL Floor (Tentative)" — not as the assigned TRL.

**Step 3 — Generate a specific Evidence Request List**: Produce a structured list of the specific evidence items, document types, and validation activities that would be required to resolve the indeterminate status. This list must be:
- Specific (naming exact document types, not generic categories)
- Prioritised (Must Have items before Should Have)
- Actionable (each item should be something the startup can realistically produce)

**Step 4 — Escalate to human analyst**: Flag the evaluation for mandatory human analyst review. The AI agent may not finalise a TRL assignment when the Indeterminate Rule has been triggered. A human analyst must review the tentative TRL floor, the evidence request list, and any available contextual information before an assigned TRL is recorded.

**Step 5 — Suspend scoring**: Do not compute a Technology Pillar TRL Score using the tentative TRL floor. Report the TRL Score as "Pending — Indeterminate TRL" in the evaluation report. Downstream scoring that depends on the Technology Pillar TRL Score must be similarly suspended.

### 7.3 Resolution Pathway

An Indeterminate TRL designation is resolved when:
- The startup provides the requested evidence and the AI agent re-evaluates with confidence ≥ 0.70
- A human analyst reviews available evidence and makes a documented TRL assignment with a written justification
- The evaluation is formally closed without a TRL assignment (in which case the startup's Technology Pillar score is computed without a TRL component, with an appropriate penalty applied per the configuration of the evaluating organisation)

### 7.4 Indeterminate TRL in Reports

Evaluation reports that contain an Indeterminate TRL designation must include the following language in the Technology Pillar section:

> "The AI evaluation agent was unable to assign a Technology Readiness Level to [Technology Component Name] with the required confidence threshold of 0.70. The primary reason for the indeterminate status is [specific trigger condition]. The tentative TRL floor is TRL [X], based on partial satisfaction of evidence requirements at that level. The following specific evidence items would resolve this designation: [Evidence Request List]. This evaluation has been escalated to a human analyst for review. No Technology Pillar TRL Score has been computed pending resolution."

---

## 8. TRL Gaming: Detection and Mitigation

### 8.1 Definition and Motivation

TRL gaming refers to the practice by which a startup — knowingly or unknowingly — claims a TRL level higher than is warranted by available evidence. Motivations include:

- **Grant eligibility**: Many grant programmes have minimum TRL requirements (e.g., EC Horizon Europe instrument boundaries)
- **Investment narrative**: Higher TRL levels are associated with lower technical risk, making fundraising easier
- **Competitive positioning**: In competitive evaluation processes, a higher TRL claim can improve relative ranking
- **Founder self-deception**: In some cases, founders genuinely misunderstand TRL definitions and self-assess too generously

The TIDES platform is designed to detect all forms of TRL gaming, including unintentional misrepresentation. The standard does not distinguish between deliberate and unintentional gaming in its detection rules — only in its reporting language (deliberate gaming triggers a fraud flag; unintentional gaming triggers a calibration correction).

### 8.2 Gaming Patterns and Detection Rules

The following table documents the most common TRL gaming patterns, their observable indicators, and the detection rules applied by the AI agent:

| Gaming Pattern | Description | Observable Indicator | Detection Rule |
|---|---|---|---|
| **Environment Inflation** | Claiming validation in a "relevant environment" when only laboratory conditions were used | Test reports mention controlled lab settings but claim field validation | Agent checks environmental descriptors against TRL 4 vs. TRL 5 boundary definitions |
| **Customer Letter Substitution** | Using a Letter of Intent or customer expression of interest as evidence of operational deployment | LOI or MOU submitted as evidence of TRL 8–9 | Letters of intent are not evidence of TRL above 6; agent flags any LOI cited for TRL 7+ |
| **Publication Citation as Validation** | Citing a journal paper as validation evidence without having conducted the validation themselves | Third-party research paper cited as sole technical evidence | Agent checks whether cited validation was performed by the startup's team or by others |
| **Demo as Prototype** | Describing a marketing demonstration or investor demo as an operational prototype | "Live demo" video or slides submitted as TRL 7 evidence | Agent requires evidence of operational environment conditions; demos in conference settings do not qualify |
| **Prototype as System** | Claiming TRL 8 (system complete and qualified) based on a non-qualified prototype | No qualification test reports; only prototype photos or videos | Agent requires formal qualification documentation (test standards, pass/fail criteria, results) for TRL 8 |
| **Regulatory Filing as Clearance** | Claiming regulatory approval when only a regulatory filing or pre-submission has been made | "FDA filed" or "CE applied for" language submitted as TRL 8 evidence | Agent distinguishes between filing, review, and clearance/approval; filing does not confer TRL uplift |
| **Single-Customer Pilot as Operational Proof** | Claiming TRL 9 based on a single pilot project with one customer | One pilot customer cited; no multi-site, multi-condition evidence | TRL 9 requires evidence of operation across multiple operational conditions; single-pilot is TRL 7 at most |
| **Historical TRL Projection** | Claiming current TRL based on a roadmap that has not yet been executed | "We will achieve TRL 7 by Q3 2026" submitted as current TRL claim | Agent only assigns TRL based on completed activities; future projections are scored separately in the roadmap assessment |
| **Academic Spinout Overreach** | Citing university lab validation as commercial-environment validation | University lab test results claimed as field or operational validation | Agent applies university lab = controlled laboratory environment (TRL 4 ceiling without independent replication) |

### 8.3 Graduated Response to Gaming Detection

The TIDES platform applies a graduated response to detected TRL gaming:

**Level 1 — Calibration Correction (Unintentional Gaming)**: The agent corrects the TRL assignment to the appropriate level based on available evidence. A note is included in the evaluation report explaining the correction and the evidence basis. No fraud flag is raised.

**Level 2 — Inconsistency Flag (Moderate Concern)**: When multiple gaming patterns are detected simultaneously, or when the claimed TRL exceeds the evidence-supported TRL by two or more levels, an Inconsistency Flag is raised. The flag triggers mandatory human analyst review of the TRL assignment and a more thorough examination of all submitted evidence.

**Level 3 — Material Misrepresentation Flag (High Concern)**: When the agent detects evidence that the startup has submitted documents that directly contradict other submitted documents (e.g., a technical paper co-authored by the founders shows results inconsistent with claims in the pitch deck), a Material Misrepresentation Flag is raised. This flag triggers escalation to senior analyst review, potential notification to the evaluating organisation, and suspension of the evaluation pending further investigation.

### 8.4 Gaming Resistance in Evidence Requirements

The evidence requirements specified for each TRL level in §9 are designed with gaming resistance as a core criterion. Each Must Have evidence item was selected because:

1. It is difficult to fabricate without corresponding technical work having been done
2. It is either independently verifiable or requires a third-party co-author/witness
3. It corresponds to a specific stage of development that cannot realistically be completed without the preceding stages

Evaluators reviewing or overriding AI agent TRL assignments should apply the same gaming-resistance lens: if a piece of evidence is easy to produce without having done the underlying technical work, it should be weighted as a Should Have (corroborative) rather than a Must Have (determinative) item.

---

## 9. TRL Level Definitions

---

### TRL 1 — Basic Principles Observed

---

#### 9.1.1 Definition

TRL 1 represents the lowest level of technology readiness. At this stage, the basic scientific, engineering, or mathematical principles that could underpin a new technology have been observed and described. No application has been proposed, no practical concept has been formulated, and no experimental work has been initiated. The technology exists only as an identified phenomenon or a theoretical possibility.

In the startup context, TRL 1 typically corresponds to a founding team that has identified a scientific or technical principle — often through academic research — that they believe can be the basis for a new technology. The team may have published or read literature on the principle, may have observed it in laboratory or computational settings, and may have formed a preliminary hypothesis about its potential utility. However, no work has been done to translate the principle into a practical application.

TRL 1 is not a measure of the quality or novelty of the underlying science. A startup founding team working from a Nobel Prize-winning scientific discovery is still at TRL 1 if they have not begun conceptualising how that discovery translates into a product or service. Similarly, a team working from an obscure but directly applicable laboratory finding is also at TRL 1 if no conceptualisation has occurred.

**Key boundary with TRL 2**: TRL 1 ends and TRL 2 begins when the founding team has articulated a specific, practical application of the observed principle. The mere belief that "this science could be used for X" is TRL 1. A written, specific proposal for how the principle would be applied — even without experimental work — is TRL 2.

---

#### 9.1.2 Required Evidence

**Must Have:**

- At least one piece of scientific literature (peer-reviewed paper, conference proceeding, technical report, patent, or equivalent) that describes the underlying principle. This literature need not have been authored by the founding team, but the team must demonstrate awareness of it and its relevance.
- A founding team technical statement (written, dated) that describes: (a) the specific principle observed, (b) why it is relevant to the startup's intended technology area, and (c) the source(s) from which the principle was identified.

**Should Have:**

- Founding team credentials (academic CVs, publication records) demonstrating competence to evaluate and interpret the underlying science
- Preliminary literature review or annotated bibliography showing breadth of scientific grounding
- A dated notebook entry, research log, or similar document showing when the principle was first identified by the team
- Any computational models, simulations, or thought experiments that illuminate the behaviour of the principle (not required; highly corroborative)
- Evidence of connection to a university research group or laboratory where the principle was first observed (for academic spinouts)

---

#### 9.1.3 Technical Expectations

At TRL 1, technical expectations are minimal but specific. The evaluator should expect to find:

- A coherent, accurate description of the underlying scientific or engineering principle in the startup's documentation. The description should demonstrate genuine technical understanding — not a layperson's paraphrase of a press release.
- Correct attribution of the principle's origin (who discovered it, in what context, with what implications).
- An absence of specific product descriptions, performance specifications, or market claims. Startups that mix TRL 1 scientific discussion with detailed product roadmaps are typically attempting to paper over technical immaturity with commercial vision.
- Acknowledgement of what is unknown: TRL 1 documentation should contain statements of scientific uncertainty and open questions, not confident technical claims.

The evaluator should NOT expect:
- Hardware, software, or biological artefacts of any kind
- Experimental data from the founding team's own work
- Performance metrics, benchmarks, or test results
- Customer or market validation of any kind

---

#### 9.1.4 Validation Requirements

At TRL 1, formal validation has not yet occurred. The validation activity appropriate to this level is peer acknowledgement of the underlying science:

- **Who must have performed validation**: Not applicable in the traditional sense. The "validation" at TRL 1 is the scientific community's acceptance of the underlying principle as real and reproducible. This is represented by peer-reviewed publication, citation records, or replication by independent laboratories.
- **Founding team validation**: The founding team is not expected to have validated anything at TRL 1. Their role is to identify, understand, and document the relevant scientific principle.
- **Minimum requirement**: At least one peer-reviewed source (or equivalent high-credibility technical source) must exist that describes the underlying principle. If the principle is entirely novel and unconfirmed by external sources, the startup is at TRL 0 by TIDES definitions (not evaluated; routed to basic research funding).

---

#### 9.1.5 Common Mistakes

**Mistake 1 — Assigning TRL 2 to a team that has only read papers**: A founding team that has extensively reviewed literature and has great enthusiasm for a scientific area is still at TRL 1 if they have not articulated a specific application concept. Enthusiasm and domain knowledge do not constitute a technology concept.
*How to avoid*: Apply the TRL 1/2 boundary test rigorously: Is there a written, specific proposal for how the principle is applied? If not, it is TRL 1.

**Mistake 2 — Conflating scientific novelty with TRL elevation**: A highly novel, unpublished scientific principle discovered by the founding team is not at TRL 2 just because it is novel. Novelty is a quality of the science; TRL measures development maturity. The principle still needs to be formulated into an application concept to advance to TRL 2.
*How to avoid*: Evaluate TRL on the development activity axis, not the novelty axis. A separate "Technical Differentiation Score" captures novelty.

**Mistake 3 — Accepting a pitch deck as TRL 1 evidence**: A pitch deck that contains a "how it works" slide describing a scientific principle does not constitute documentation of the TRL 1 evidence standard. Pitch decks are marketing documents optimised for persuasion, not technical precision.
*How to avoid*: Require a separate technical documentation artefact for TRL evidence. Pitch deck content may be used as corroborating context but not as primary evidence.

**Mistake 4 — Undervaluing TRL 1**: Some evaluators treat TRL 1 as "nothing" and decline to evaluate startups at this stage. This is an error; TRL 1 is a valid, assessable level with specific evidence requirements. Many breakthrough technologies that became major commercial successes started at TRL 1. The correct response is to assign TRL 1 with a low TRL score and route to appropriate early-stage instruments.
*How to avoid*: Treat TRL 1 as a complete, evaluable level. Document the assigned TRL, the evidence basis, and the path to TRL 2.

**Mistake 5 — Failing to distinguish between "principle" and "idea"**: A startup that says "we want to build a better battery" is not at TRL 1 — they have an idea but have not identified a specific scientific principle. TRL 1 requires that a specific principle (e.g., solid-state lithium-ion transport through a particular ceramic membrane) has been identified.
*How to avoid*: Require the startup to name the specific scientific principle and cite the source literature. Vague application domains are not TRL 1 principles.

**Mistake 6 — Conflating TRL 1 with concept-stage startups in AI/ML**: A startup building an AI/ML model that has identified a machine learning technique (e.g., transformer-based attention mechanisms for protein folding) as its underlying principle is at TRL 1, not TRL 3, if they have not yet produced any experimental results. The breadth and sophistication of the technique's existing literature does not elevate the startup's own TRL.
*How to avoid*: Apply the same principle-to-concept-to-experiment sequence regardless of how mature the underlying field is.

---

#### 9.1.6 How to Reach the Next TRL

To advance from TRL 1 to TRL 2, the founding team must complete the following:

**Activities that require only internal effort and time:**
- [ ] Translate the identified principle into a specific, written application concept: describe what product or service this principle would enable, what problem it would solve, and who would use it
- [ ] Prepare a technology concept document (minimum 2–5 pages) describing the proposed application, the mechanism by which the principle would be exploited, and the anticipated technical challenges
- [ ] Define the first-order performance specifications that the technology would need to achieve to be commercially useful (e.g., target accuracy, throughput, energy consumption, cost per unit)
- [ ] Document the technology concept with a date stamp and team signatures (for IP chain of custody)
- [ ] Conduct a prior art search to confirm the proposed application concept is not already patented or published

**Activities that require specific external events:**
- [ ] (Optional but recommended) Disclosure to a technology transfer office or patent attorney to assess IP landscape — this requires an external party appointment
- [ ] (For academic spinouts) Notification to university technology transfer office of intended commercialisation — required by most university IP policies before concept documentation can become the startup's IP

---

#### 9.1.7 Confidence Indicators

**High Confidence (0.90–1.00)**: The founding team has provided dated scientific literature, a clear technical statement identifying the specific principle, and team credentials demonstrating scientific competence in the relevant domain. The principle is well-established in scientific literature with multiple independent replications.

**Moderate Confidence (0.75–0.89)**: The founding team has cited relevant literature but the technical statement is generic rather than specific to the identified principle. Team credentials exist but are not directly aligned to the specific scientific domain. The principle has some literature support but is not universally accepted in the field.

**Low Confidence (0.70–0.74)**: The founding team's documentation references a principle but does not demonstrate genuine understanding of the underlying science. Literature citations are tangential. This is the minimum confidence level for a TRL 1 assignment; below 0.70, the Indeterminate TRL Rule applies.

**Evidence Gaps That Are Acceptable**: Missing founding team credentials (though concerning, does not invalidate the scientific principle); no lab access yet; no computational modelling.

**Evidence Gaps That Are Disqualifying**: No scientific literature whatsoever; principle described only in marketing language with no scientific citation; founding team cannot explain the principle in technical terms when queried.

---

#### 9.1.8 Sector-Specific Notes

| Sector | TRL 1 Characteristics | Key Evidence Sources |
|---|---|---|
| **Software/SaaS** | Rare for pure software startups to be at TRL 1; typically corresponds to a novel algorithmic idea with no implementation yet | Algorithm description, academic paper on novel computational approach |
| **AI/ML** | Corresponds to identification of a novel ML approach or dataset type; no experiments run yet | Literature on the identified technique; hypothesis paper or preprint |
| **Biotech/MedTech** | Corresponds to identification of a novel biological mechanism, target, or material property | Peer-reviewed paper on the identified mechanism; preclinical research literature |
| **DeepTech/Hardware** | Corresponds to observation of a physical, chemical, or materials science phenomenon | Physics or materials science publication; lab notebook from discovery context |
| **AgriTech** | Corresponds to identification of a biological, genetic, or ecological principle applicable to agriculture | Agricultural science literature; genomics or ecology publication |
| **ClimaTech** | Corresponds to identification of a physical, chemical, or computational principle applicable to climate mitigation or adaptation | Environmental science or climate modelling literature |
| **DefenceTech** | Corresponds to identification of a novel sensing, propulsion, communications, or materials principle | May include classified or restricted literature; ITAR/EAR compliance must be confirmed |

---

### TRL 2 — Technology Concept Formulated

---

#### 9.2.1 Definition

TRL 2 represents the stage at which the underlying scientific principle identified at TRL 1 has been translated into a practical technology concept. The founding team has articulated a specific, written proposal for how the principle could be exploited to create a product or service. No experimental work has been undertaken, and no prototype or working model exists. The technology exists as a detailed conceptual description: what it would do, how it would work mechanistically, what it would be made of or built from, and what level of performance would be required for it to be useful.

TRL 2 is characterised by paper studies, analytical models, and conceptual design. The team is reasoning from first principles about whether the proposed application is theoretically feasible. Feasibility at this stage means theoretical consistency — the laws of physics, biology, mathematics, or chemistry do not forbid the proposed application. It does not mean the team has demonstrated that the application is practically achievable.

**Key boundary with TRL 3**: TRL 2 ends and TRL 3 begins when the founding team has conducted actual experiments (wet lab work, coded and run computational experiments, built and measured physical samples) that test the proposed concept. The first time a team generates original experimental data from their own work on the proposed concept, they have crossed into TRL 3.

---

#### 9.2.2 Required Evidence

**Must Have:**

- A written technology concept document (dated) that describes: (a) the specific application of the identified principle, (b) the proposed mechanism of operation, (c) the anticipated inputs, outputs, and operating conditions, (d) the minimum performance requirements for commercial or operational utility, and (e) the key technical assumptions the concept rests upon.
- An analytical or theoretical feasibility argument — even a simple first-principles calculation demonstrating that the proposed concept does not violate fundamental laws. This may be embedded in the concept document.
- Identification of the primary technical unknowns and risks that would need to be resolved through experimental work (i.e., a preliminary risk register or unknowns list).

**Should Have:**

- Preliminary design sketches, block diagrams, system architecture diagrams, or conceptual schematics illustrating the proposed technology
- A preliminary bill of materials, technology stack, or biological component list identifying the elements the technology would incorporate
- First-order cost or performance estimates derived from the theoretical concept
- A patent landscape search or freedom-to-operate preliminary analysis
- Identification of analogous technologies in adjacent domains that provide partial existence proof for components of the proposed concept
- An initial estimation of the experimental approach that would be required to progress to TRL 3

---

#### 9.2.3 Technical Expectations

At TRL 2, evaluators should expect:

- A technology description that is specific enough to distinguish this concept from all other technologies in the same domain. Generic descriptions ("AI-powered diagnostics platform") do not satisfy TRL 2; specific descriptions ("a convolutional neural network trained on 16S rRNA sequencing data to classify gut microbiome dysbiosis patterns associated with Type 2 Diabetes onset within a 30-day predictive window") may satisfy TRL 2.
- Theoretical performance estimates: The team should be able to state, from theory alone, what level of performance they expect if the concept works as intended. These estimates do not need to be correct, but they demonstrate that the team has thought rigorously about the concept.
- Awareness of technical risk: TRL 2 documentation that contains no technical risks or uncertainties is itself a red flag — it suggests the team has not thought deeply about the concept.
- Absence of experimental data from the founding team's own work (any such data would indicate TRL 3 or higher).

---

#### 9.2.4 Validation Requirements

At TRL 2, validation is internal and analytical:

- **Who must have performed validation**: The founding team, potentially with input from scientific advisors or academic collaborators. No external validation body is required.
- **Nature of validation**: Analytical verification that the concept is theoretically sound. This may involve first-principles calculation, literature-based analogy, simulation using established modelling tools, or peer critique from a technical advisor.
- **Minimum requirement**: The technology concept document must have been reviewed by at least one technically qualified person — this may be a co-founder, technical advisor, or academic collaborator. Evidence of this review (email exchange, signed review form, advisory board minutes) is a Should Have item.

---

#### 9.2.5 Common Mistakes

**Mistake 1 — Accepting a pitch deck "technology" slide as TRL 2 evidence**: A PowerPoint slide showing a diagram of a proposed system is not a technology concept document. It lacks the specificity, the theoretical analysis, and the technical risk identification required.
*How to avoid*: Require a dedicated technical concept document, not marketing materials.

**Mistake 2 — Elevating TRL 2 because the concept is clever**: A clever, innovative concept that is still purely on paper is TRL 2 regardless of its potential significance. The TRL scale measures experimental and validation progress, not intellectual quality.
*How to avoid*: Separate the assessment of novelty (Technical Differentiation Score) from the TRL assessment.

**Mistake 3 — Confusing preliminary simulation results with experimental proof of concept**: If a team runs a computer simulation of their concept using a general-purpose tool (MATLAB, Python, COMSOL) based on assumed parameters, this is TRL 2 — it is a theoretical analysis, not an experimental result. If they run a simulation using a validated model with real experimental inputs, this may approach TRL 3.
*How to avoid*: Apply the test: Did the team generate original experimental data from a physical, biological, or computationally-validated system? If no, it is not above TRL 2.

**Mistake 4 — Ignoring the minimum performance requirements test**: A concept document that does not specify what level of performance the technology would need to achieve to be useful cannot be properly evaluated. Without performance targets, it is impossible to assess whether the concept could ever work.
*How to avoid*: Require performance targets as a Must Have for TRL 2 confirmation.

**Mistake 5 — Treating TRL 2 as trivially achieved**: Some evaluators assume that any startup with a written business plan or pitch deck is at TRL 2. This is incorrect — TRL 2 requires a specific technical concept with analytical grounding. A business plan that describes a problem and a proposed solution category is not TRL 2 technical documentation.
*How to avoid*: Apply the specificity test: Could a technically qualified engineer, scientist, or developer begin designing an experiment to test this concept based on what is written? If not, it is likely TRL 1.

**Mistake 6 — Failing to check for theoretical infeasibility**: Occasionally, startups propose concepts that contradict known science (e.g., a "perpetual motion" energy device, a drug that targets a receptor whose biology is well-established not to function as claimed). TRL 2 requires theoretical feasibility; a concept that is demonstrably infeasible from first principles should be flagged, not assigned a TRL level.
*How to avoid*: Include a theoretical feasibility check as part of TRL 2 evaluation. Flag concepts that appear to contradict established science for senior analyst review.

---

#### 9.2.6 How to Reach the Next TRL

To advance from TRL 2 to TRL 3:

**Activities that require only internal effort and time:**
- [ ] Design a specific experiment or set of experiments that will test the core assumptions of the technology concept
- [ ] Acquire or access the laboratory facilities, computing resources, biological samples, or hardware components needed to conduct the experiments
- [ ] Build or configure the simplest possible experimental setup that can test the central hypothesis
- [ ] Run the experiments and record the results (whether positive, negative, or inconclusive)
- [ ] Analyse the results against the theoretical predictions made at TRL 2
- [ ] Write up the experimental results in a formal technical report (even if internal)
- [ ] Update the risk register based on experimental findings

**Activities that require specific external events:**
- [ ] Access to a specialist laboratory (requires application to a university lab, national facility, or commercial lab)
- [ ] Ethics approval for human or animal experiments (biotech/medtech)
- [ ] Biosafety committee approval for work with biological materials
- [ ] Access to proprietary datasets for AI/ML experiments (requires data access agreements)
- [ ] GPU cluster access for large-scale computational experiments (requires cloud credits or HPC allocation)

---

#### 9.2.7 Confidence Indicators

**High Confidence (0.90–1.00)**: Detailed, dated concept document with specific mechanism description, first-principles feasibility analysis, named technical unknowns, and evidence of technical advisor review. Concept is clearly distinguishable from competing approaches.

**Moderate Confidence (0.75–0.89)**: Written concept description exists and is specific but lacks analytical depth. Performance targets are mentioned but not derived from theory. No evidence of external technical review.

**Low Confidence (0.70–0.74)**: Concept is described but only at a high level. Feasibility analysis is absent or perfunctory. This is the minimum for TRL 2 assignment.

**Acceptable Gaps**: No experimental data (by definition); no hardware or software artefacts; no customer feedback; no IP protection yet.

**Disqualifying Gaps**: No written concept document at all (oral description only); concept demonstrably contradicts established science; no technically qualified team member who could have formulated the concept.

---

#### 9.2.8 Sector-Specific Notes

| Sector | TRL 2 Characteristics | Key Evidence Sources |
|---|---|---|
| **Software/SaaS** | System architecture design; API specification draft; database schema concept; algorithmic design | Architecture diagrams, pseudocode, data model descriptions |
| **AI/ML** | Model architecture concept; dataset requirement specification; training pipeline design | Model architecture paper/description, dataset feasibility analysis, training compute estimate |
| **Biotech/MedTech** | Mechanism of action hypothesis; target identification; proposed assay design | MOA documentation, target validation literature, assay protocol draft |
| **DeepTech/Hardware** | Device concept drawing; materials selection rationale; operating principle description | CAD concept sketches, materials science analysis, physics-based performance estimate |
| **AgriTech** | Crop intervention concept; biological mechanism application plan; sensor/data system concept | Agronomy design brief, genomic target identification, field measurement concept |
| **ClimaTech** | System design concept; carbon capture/energy storage mechanism description; modelling approach | Engineering concept document, thermodynamic analysis, climate model reference |
| **DefenceTech** | Capability concept document; sensor or materials concept; performance requirement derivation | Classified or unclassified concept document; CONOPS draft; performance envelope analysis |

---

### TRL 3 — Experimental Proof of Concept

---

#### 9.3.1 Definition

TRL 3 is the first level at which the founding team has generated original experimental data from their own work. At this stage, laboratory experiments or computational studies have been conducted specifically to test whether the technology concept formulated at TRL 2 is experimentally feasible — not merely theoretically possible. The experiments at TRL 3 are typically simple, small-scale, and not optimised for performance; their purpose is to demonstrate that the core technical principle can be made to work under any conditions, even idealised laboratory conditions.

The critical distinction from TRL 2 is the presence of founding-team-generated experimental evidence. The critical distinction from TRL 4 is that TRL 3 experiments test individual, isolated technical elements or sub-functions — they do not yet represent an integrated technology system. A TRL 3 experiment might demonstrate that a specific chemical reaction proceeds as theorised, that a specific machine learning architecture learns a target pattern from a training dataset, or that a specific material exhibits the electrical properties predicted by the TRL 2 concept. It does not demonstrate that an integrated system combining these elements works end-to-end.

TRL 3 is sometimes called "proof of concept" in startup parlance, though this term is used loosely in investment contexts. For TIDES evaluation purposes, "proof of concept" means experimental confirmation of the core technical mechanism at the sub-system level.

**Key boundary with TRL 4**: TRL 3 ends and TRL 4 begins when the key functional components have been integrated into a working prototype (even a very crude one) and the integrated system has been tested as a whole. A collection of component-level results is TRL 3; an integrated system demonstration — however primitive — is TRL 4.

---

#### 9.3.2 Required Evidence

**Must Have:**

- At least one experimental report or technical data record (dated) documenting experiments conducted by the founding team that test a core component or sub-function of the technology concept. The report must include: (a) the objective of the experiment, (b) the experimental setup and conditions, (c) the measured results, (d) comparison of results against theoretical predictions, and (e) conclusions about the feasibility of the tested component.
- Evidence that the experiments were conducted by or under the direct supervision of a member of the founding team (e.g., lab notebook, researcher signatures, institutional affiliation).
- A description of the experimental conditions sufficient for another technically qualified person to assess whether the conditions are appropriate for the intended application (i.e., what temperature, pressure, dataset, environment, or computational configuration was used).

**Should Have:**

- Multiple experimental runs demonstrating repeatability of the core result
- Statistical analysis of experimental results (where applicable)
- Photographs, video recordings, or instrument output logs from experiments
- Lab notebook entries (physical or electronic) corresponding to the experimental work
- A summary of what the experimental results confirm and what they leave unanswered
- Updated technical risk register reflecting experimental findings
- Any negative or inconclusive results (their presence actually increases evaluation confidence, as it suggests genuine experimentation rather than cherry-picked reporting)

---

#### 9.3.3 Technical Expectations

At TRL 3, evaluators should expect:

- Raw or processed experimental data, not just conclusions. A claim of "experiments confirmed our approach works" without supporting data is not TRL 3 evidence.
- Honest acknowledgement of limitations: TRL 3 experiments are necessarily idealised. The team should acknowledge that their laboratory conditions do not yet reflect real-world operating conditions.
- Component-level scope: Results should relate to specific sub-functions of the technology, not the complete system. End-to-end system results at this stage suggest either TRL 4 (if integrated) or potential gaming (if the "system" is far simpler than claimed).
- Quantitative results: Wherever possible, results should be expressed numerically. Qualitative descriptions of experimental outcomes ("it seemed to work") are insufficient for TRL 3.

---

#### 9.3.4 Validation Requirements

- **Who must have performed validation**: The founding team (internal validation). External validation is not required at TRL 3 but is strongly corroborative if present.
- **Nature of validation**: Experimental confirmation of specific component-level hypotheses. For AI/ML, this includes training and evaluation runs on defined datasets. For biotech, this includes initial in vitro or in silico results. For hardware, this includes bench measurement of physical phenomena.
- **Minimum independence**: At least the experiment should have been witnessed by or conducted in collaboration with a person outside the immediate founding team — a research supervisor, graduate student collaborator, or lab technician. Solo experiments with no witness are the lowest-confidence TRL 3 evidence.
- **Peer-reviewed publication**: A peer-reviewed publication of the TRL 3 experimental results is the highest-quality evidence at this level. Not required, but substantially increases confidence score.

---

#### 9.3.5 Common Mistakes

**Mistake 1 — Confusing a technology demo with experimental proof of concept**: A live product demonstration — even a technically impressive one — is not TRL 3 experimental evidence unless it is accompanied by underlying data. A demo shows that something appears to work; experimental data shows why and under what conditions it works.
*How to avoid*: Require underlying experimental data for every TRL 3 assignment. Demos may be corroborative but never primary evidence.

**Mistake 2 — Treating published academic results as the founding team's proof of concept**: If a research group (not the founding team) published experimental results demonstrating the concept, this is relevant background science but not the founding team's TRL 3 evidence. The team must have conducted their own experiments.
*How to avoid*: Check whether cited experimental results were produced by the startup team. If all citations are to others' work, the startup is at TRL 2 regardless of how strong the published results are.

**Mistake 3 — Accepting simulation results as TRL 3 experimental evidence for hardware/physical technologies**: For software and AI/ML technologies, computational experiments (model training runs, simulation studies) are legitimate TRL 3 evidence. For hardware, materials, biotech, and other physical technologies, computational simulation is TRL 2 analysis, not TRL 3 experimental proof. Physical fabrication and measurement is required.
*How to avoid*: Apply sector-appropriate definitions of "experiment." For physical technologies, insist on physical measurement data.

**Mistake 4 — Ignoring negative results**: A startup that has run experiments and observed mostly negative or inconclusive results is still at TRL 3 if they have generated genuine experimental data. Some evaluators penalise negative results or treat them as evidence of non-viability. This is incorrect — negative results are scientifically valuable and demonstrate genuine experimental engagement.
*How to avoid*: Evaluate the quality and rigor of the experimental process, not just the sign of the results.

**Mistake 5 — Accepting "results on request" without documentation**: Some startups claim they have experimental results but have not included them in their submission, offering to provide them on request. This is insufficient for TRL 3 assignment. The evidence must be in the submitted documentation package.
*How to avoid*: Apply the rule strictly: if the evidence is not in the submission, it is not evaluated. Flag the gap and either request the submission of the data or apply the Indeterminate TRL Rule.

**Mistake 6 — Failing to check experimental conditions for relevance**: An experiment conducted under conditions so idealised as to bear no relationship to real-world operation may not be meaningful evidence. For example, a drug compound tested in a perfectly pH-balanced, temperature-controlled, protein-free buffer that bears no resemblance to biological tissue is lower-quality evidence than a drug tested in a cell culture model.
*How to avoid*: Assess the relevance of experimental conditions as part of TRL 3 evaluation. Idealised conditions are expected and acceptable at TRL 3, but conditions that are entirely disconnected from any practical implementation should reduce confidence.

---

#### 9.3.6 How to Reach the Next TRL

To advance from TRL 3 to TRL 4:

**Activities that require only internal effort and time:**
- [ ] Identify all functional components that must work together to constitute a basic system
- [ ] Design an integration architecture showing how components connect (software API layer, hardware interface, biological assay workflow, etc.)
- [ ] Build or configure the integrated system at the minimum viable level — even crude integration is sufficient for TRL 4
- [ ] Define a test protocol for the integrated system specifying the inputs, expected outputs, and pass/fail criteria
- [ ] Execute the integration test and record results for all system functions, not just the previously tested components
- [ ] Document observed failure modes at the integration boundary (these are expected and valuable)
- [ ] Produce an integration test report with raw data, analysis, and conclusions

**Activities that require specific external events:**
- [ ] Access to integration facilities (e.g., if components are built in separate labs, integration requires co-location or travel)
- [ ] Component supply (for hardware: ordering parts, waiting for fabrication; for biotech: cell line acquisition, reagent delivery)
- [ ] Software licensing or API access for third-party tools incorporated into the integrated system
- [ ] Institutional approval for experiments involving integrated systems (especially in regulated domains)

---

#### 9.3.7 Confidence Indicators

**High Confidence (0.90–1.00)**: Multiple experimental runs with quantitative results, lab notebook documentation, evidence of peer review or publication, confirmation by technically qualified external collaborator.

**Moderate Confidence (0.75–0.89)**: One or more experimental runs with quantitative results but limited documentation of conditions and methodology. Results are plausible given the stated concept.

**Low Confidence (0.70–0.74)**: Experimental results are described qualitatively; conditions are not fully specified; no witness or collaborator documentation. Meets the minimum threshold for TRL 3 assignment.

**Acceptable Gaps**: No external validation; no peer review; no patent filing; no customer engagement.

**Disqualifying Gaps**: No founding-team-generated experimental data at all; all experimental results are from third parties; experimental conditions described are physically or biologically implausible.

---

#### 9.3.8 Sector-Specific Notes

| Sector | TRL 3 Characteristics | Key Evidence Sources |
|---|---|---|
| **Software/SaaS** | Core algorithm implemented and tested; key function demonstrated in isolation; basic API or data pipeline function confirmed | Code repository with test results, algorithm benchmark output, unit test logs |
| **AI/ML** | Initial model trained on a representative dataset subset; baseline performance metrics established; key learning behaviour confirmed | Training logs, validation curves, confusion matrices, benchmark comparisons |
| **Biotech/MedTech** | In vitro or in silico confirmation of mechanism; initial cell or molecular assay results; basic efficacy signal observed | Lab reports, assay data, biochemical analysis results, in silico simulation outputs |
| **DeepTech/Hardware** | Key physical component fabricated and measured; primary operating principle confirmed at bench level; material property verified | Measurement data logs, material characterisation reports, oscilloscope/spectrometer outputs |
| **AgriTech** | Controlled environment plant or soil experiment; genomic or biological mechanism confirmed in a laboratory setting | Greenhouse trial data, soil analysis results, genomic sequencing outputs |
| **ClimaTech** | Laboratory-scale process or reaction confirmed; energy balance or capture efficiency measured at bench scale | Reaction kinetics data, energy measurement logs, materials performance data |
| **DefenceTech** | Sub-system function demonstrated at bench level; sensor signal or material response measured under controlled conditions | May be classified; unclassified summary with classification markings must confirm experimental basis |

---

### TRL 4 — Technology Validated in Laboratory

---

#### 9.4.1 Definition

TRL 4 represents the first integration milestone in the TIDES TRL framework. At this level, the key functional components of the technology have been combined into an integrated system — however crude — and that integrated system has been tested and validated in a laboratory (controlled) setting. The integrated system demonstrates that the individual components identified at TRL 3 can be made to work together to perform the intended function.

The environment at TRL 4 is explicitly a laboratory environment: controlled, idealised conditions that do not yet replicate the variability, interference, or operational stress of real-world deployment. The distinction from TRL 5 is entirely about environment fidelity: TRL 4 validation occurs in an environment the team controls completely; TRL 5 validation occurs in an environment that simulates or introduces real-world conditions.

"Laboratory" in the TIDES context is defined broadly to accommodate diverse technology types:
- For hardware: a physical laboratory with controlled temperature, power, vibration, and interference
- For software: a development environment with idealised data, synthetic test cases, and no production-level traffic or user variability
- For AI/ML: a training and evaluation environment using clean, curated, representative datasets without distribution shift, noise, or adversarial inputs
- For biotech: in vitro cell culture, controlled-condition animal models, or validated computational models with known parameters
- For AgriTech: greenhouse or growth chamber conditions; controlled soil or hydroponic environments

A common test of TRL 4 status is whether the integrated system can demonstrate its key function on demand, repeatedly, in front of a technically qualified observer, under the team's controlled conditions. If yes, TRL 4 is achievable. If the system is not yet integrated to the point of repeatable demonstration, it is TRL 3.

**Key boundary with TRL 5**: TRL 4 ends and TRL 5 begins when the technology has been validated in an environment that introduces real-world conditions — not a perfect laboratory setting. The first time a system is tested with real data, real environmental variability, or in a setting the team does not fully control, this crosses into TRL 5 territory.

---

#### 9.4.2 Required Evidence

**Must Have:**

- An integration test report documenting the testing of the assembled, integrated technology system in a laboratory setting. The report must include: (a) a description of the integrated system configuration (what components, how connected), (b) the test conditions (environmental parameters, input data or stimuli, equipment used), (c) the performance metrics measured and their values, (d) comparison against the specifications defined at TRL 2, and (e) conclusions on validation status.
- Evidence that all primary functions of the proposed technology have been tested (not just the easiest or most impressive functions). At minimum, the core value-generating function must be demonstrated.
- Quantitative performance data from the integrated system tests — not qualitative descriptions.

**Should Have:**

- Photographs or video recordings of the integrated laboratory setup
- Complete test protocol documentation (what was tested, how, in what sequence, by whom)
- Equipment calibration records or software version records
- Repeatability data: results from multiple test runs under the same conditions
- Identification and documentation of failure modes observed during integration testing
- Updated component-level risk register based on integration findings
- Peer or advisor review of the test results
- Any independent replication of the laboratory validation by a non-founding-team member

---

#### 9.4.3 Technical Expectations

At TRL 4, evaluators should expect:

- Evidence of a genuine integration exercise, not just a collection of component-level tests. Integration means the components talk to each other, exchange data or energy, and produce a combined system output.
- System-level performance metrics, not just component-level metrics. If a startup reports only component specifications but no system-level test results, they have not crossed into TRL 4.
- Honest documentation of integration challenges. TRL 4 integration rarely proceeds without problems; documentation that shows only successful results without any integration challenges is a gaming signal.
- A gap assessment comparing laboratory performance against the performance needed for the relevant application environment (this gap is expected to be significant at TRL 4 and is not penalised).

---

#### 9.4.4 Validation Requirements

- **Who must have performed validation**: The founding team, in a laboratory they have access to. External validation is not required but increases confidence.
- **Nature of validation**: Integration testing of the assembled system against defined performance specifications under controlled laboratory conditions.
- **Minimum standard**: The validation must be repeatable — the system must demonstrate the same core function across multiple test runs, not just once. One-time demonstrations that cannot be repeated are TRL 3.
- **External witness**: Preferred but not required. An independent technical observer (academic supervisor, technical advisor, external engineer) who can attest to witnessing the laboratory demonstration substantially increases the confidence score.

---

#### 9.4.5 Common Mistakes

**Mistake 1 — Awarding TRL 4 for a non-integrated system**: A startup that has tested all components individually but not yet assembled them into an integrated system is at TRL 3. The integration step is the defining characteristic of TRL 4.
*How to avoid*: Require evidence of system-level integration (e.g., an architecture diagram showing how components are connected, plus test results from the integrated system as a whole).

**Mistake 2 — Confusing laboratory validation with field testing**: A field test conducted under carefully controlled conditions by the startup team in a real-world location is still a controlled environment test and counts as TRL 4, not TRL 5. What matters is not the physical location but the degree to which real-world variability is present.
*How to avoid*: Apply the "uncontrolled variability" test: Did the test environment include conditions the team could not control? If no, it is TRL 4.

**Mistake 3 — Accepting a product demo video as TRL 4 evidence**: A polished demonstration video showing the technology working is not TRL 4 validation. Videos can be edited, cherry-picked, or recorded under highly idealised conditions. They may be corroborating context but never primary evidence.
*How to avoid*: Require the integration test report with raw data. Videos may support the narrative but cannot substitute for documentation.

**Mistake 4 — Ignoring failure modes**: A TRL 4 validation that never encountered a failure is statistically implausible. Evaluators who accept zero-failure laboratory validation reports without scrutiny are failing to apply appropriate skepticism.
*How to avoid*: Ask what failed during integration testing. If the startup reports no failures at all, probe the testing rigor and scope.

**Mistake 5 — Treating a minimum viable product (MVP) as TRL 4**: A software MVP that has been released to a small group of users is not TRL 4 — it may be TRL 5 or 6, depending on what "relevant environment" means for the software category. An MVP used internally by the team with synthetic test data is TRL 4. Apply the environment fidelity test carefully.
*How to avoid*: Distinguish between the technical validation activity (TRL) and the product development stage (which may use different terminology). Evaluate based on the environment and validation rigor, not the product development vocabulary.

**Mistake 6 — Failing to check that all primary functions are tested**: A startup may demonstrate one impressive function of a multi-function system in the laboratory while leaving other functions untested. TRL 4 requires that all primary functions — not just the most developed one — have been integrated and tested.
*How to avoid*: Review the integration test report for coverage: does it address every function claimed in the technology concept document?

---

#### 9.4.6 How to Reach the Next TRL

To advance from TRL 4 to TRL 5:

**Activities that require only internal effort and time:**
- [ ] Define what "relevant environment" means for the target application: identify the specific real-world conditions that differ from the laboratory setting (e.g., temperature range, data distribution shift, user variability, electromagnetic interference, biological matrix complexity)
- [ ] Redesign or harden the integrated system to withstand the relevant environment conditions
- [ ] Develop test protocols for relevant environment validation, including pass/fail criteria for each real-world condition
- [ ] Document the performance gap between laboratory results and relevant environment requirements
- [ ] Identify what must change in the system design to close this gap

**Activities that require specific external events:**
- [ ] Access to a relevant environment test site or facility (e.g., a pilot plant, a clinical environment, a real agricultural field, a representative customer site)
- [ ] Partnership agreement with an organisation that can provide access to a relevant test environment
- [ ] Ethical approvals for testing in clinical or human-subject-involved environments
- [ ] Regulatory pre-submission for studies in regulated domains (medical devices, food/agriculture)
- [ ] Data access agreements for testing with real, un-curated datasets

---

#### 9.4.7 Confidence Indicators

**High Confidence (0.90–1.00)**: Complete integration test report with quantitative data, repeatability evidence, all primary functions tested, witnessed by external technical observer, performance data compared against defined specifications.

**Moderate Confidence (0.75–0.89)**: Integration test report present but incomplete (some functions not tested, limited repeatability data, no external witness). Performance data present but not compared systematically to specifications.

**Low Confidence (0.70–0.74)**: Integration test described but supporting data is sparse. System described as integrated but evidence of actual end-to-end testing is thin. Minimum threshold for TRL 4.

**Acceptable Gaps**: No field testing; no external users; no regulatory engagement; limited repeatability data.

**Disqualifying Gaps**: No integration test report at all; only component-level test data submitted; system described as integrated but architecture diagram shows components are not yet connected.

---

#### 9.4.8 Sector-Specific Notes

| Sector | TRL 4 Characteristics | Key Evidence Sources |
|---|---|---|
| **Software/SaaS** | End-to-end system running on development infrastructure; all primary features functional with synthetic/test data; integration tests passing | Integration test logs, CI pipeline reports, functional test results, API test documentation |
| **AI/ML** | Full training pipeline operational; model trained and evaluated on held-out test set; end-to-end inference pipeline tested; performance benchmarks established | Model evaluation reports, benchmark comparisons, confusion matrices, precision/recall curves |
| **Biotech/MedTech** | In vitro integrated assay demonstrating mechanism; animal model study (preclinical) confirming primary endpoint; validated biomarker or formulation | Preclinical study report, in vitro assay data, formulation stability data |
| **DeepTech/Hardware** | Bench prototype assembled and tested; key electrical, mechanical, or photonic functions confirmed; subsystem interfaces validated | PCB test reports, optical characterisation data, mechanical test results, power consumption measurements |
| **AgriTech** | Controlled environment (greenhouse/growth chamber) trial completed; primary crop or soil effect demonstrated; sensor or data system integrated with physical trial | Trial data report, sensor calibration records, plant growth or yield measurements |
| **ClimaTech** | Bench-scale process demonstration complete; energy balance or capture efficiency validated at small scale; system integration demonstrated | Process performance data, energy measurement records, materials stability tests |
| **DefenceTech** | Subsystem integrated and tested in controlled laboratory conditions against defined performance metrics | Test and evaluation (T&E) report (may be classified); unclassified summary must confirm integrated validation basis |

---

### TRL 5 — Technology Validated in Relevant Environment

---

#### 9.5.1 Definition

TRL 5 marks a critical transition in the TIDES TRL framework: it is the first level at which the technology has been tested outside the team's fully controlled laboratory environment, in conditions that introduce meaningful elements of real-world operational complexity. The "relevant environment" is not the actual deployment environment, but it systematically introduces a defined subset of the conditions, constraints, or variabilities that the deployed system will encounter.

The relevant environment at TRL 5 is defined relative to the target application. For a medical diagnostic device, the relevant environment might be a clinical simulation laboratory where clinician workflows, sample variability, and instrument interference are introduced. For an agricultural sensor system, the relevant environment might be a research farm field with real soil and weather variability but without the commercial pressures of a full farming operation. For an AI fraud detection system, the relevant environment might be a production-representative dataset including real adversarial examples and distribution shift, even if the system is not yet processing live transactions.

The key characteristics that distinguish TRL 5 from TRL 4:
1. **Environmental fidelity**: Real-world variability is present, even if the full operational complexity is not
2. **Reduced team control**: The team does not fully control all parameters of the test environment
3. **Representative inputs**: The system is tested with inputs that are representative of real operational inputs, not just idealised test cases

TRL 5 validation confirms that the technology functions correctly in conditions that approximate real use, not just in the team's idealised test setup. This is the level at which many technologies encounter their first serious engineering challenges: heat dissipation in real environments, data distribution shift in real datasets, biological variability in real patient samples, mechanical stress from real operational loads.

**Key boundary with TRL 6**: TRL 5 ends and TRL 6 begins when the technology is not merely validated (confirmed to function to specifications) but actively demonstrated to an external audience — a prospective customer, an investor, a regulator, or an independent assessor — in a realistic environment. The difference is between internal validation and external demonstration.

---

#### 9.5.2 Required Evidence

**Must Have:**

- A validation report documenting tests conducted in a relevant environment (as defined above). The report must include: (a) a description of the relevant environment and how it differs from both the laboratory and the full operational deployment environment, (b) the specific real-world conditions introduced and how they were generated or accessed, (c) quantitative performance metrics measured under these conditions, (d) comparison against laboratory performance and against target specifications, and (e) conclusions on validation status and identified gaps.
- Evidence that the test environment introduced at least some real-world variability or conditions not fully controlled by the team (e.g., real data samples, real environmental conditions, real user inputs — even from a simulated user study).
- Documentation of any performance degradation observed relative to laboratory results, with technical explanation.

**Should Have:**

- Access records or agreements showing how the relevant environment was accessed (partner facility, field site agreement, dataset access agreement)
- Environmental condition logs (temperature, pressure, interference levels, or equivalent domain-specific parameters) recorded during testing
- Multiple test runs across varying relevant environment conditions (not just a single test point)
- Video or photographic documentation of the test environment (not the product, but the environment)
- Involvement of at least one external party in the test (partner organisation representative, independent observer, facility operator)
- A gap analysis document identifying what remains to be solved before full operational deployment

---

#### 9.5.3 Technical Expectations

At TRL 5, evaluators should expect:

- Evidence of performance under real-world conditions — not just confirmation that the system works in the best possible circumstances. TRL 5 validation will typically reveal performance gaps relative to TRL 4 results.
- An honest technical account of what broke, degraded, or behaved unexpectedly in the relevant environment. Startups that report identical performance in the relevant environment as in the laboratory — without explanation — should be questioned.
- A description of how the relevant environment was defined and why it is representative of the target deployment environment. If the startup has not thought carefully about what "relevant" means for their application, the quality of TRL 5 evidence will be low regardless of what they tested.
- Beginning of user or operator interaction (where applicable): some TRL 5 validations for user-facing technologies involve human participants using the system in realistic but controlled conditions (e.g., healthcare workers using a diagnostic tool with sample patients in a clinical simulation lab).

---

#### 9.5.4 Validation Requirements

- **Who must have performed validation**: The founding team with involvement of at least one external party (partner organisation, test facility, independent observer). Purely internal validation in a self-described "relevant environment" is insufficient for TRL 5.
- **Nature of validation**: Systematic testing of the integrated system under representative real-world conditions, against defined performance specifications.
- **Environment fidelity standard**: The relevant environment must be documentably different from the laboratory setting and documentably similar to the operational environment in at least one key dimension.
- **External involvement minimum**: At least one person or organisation outside the founding team must have been involved in providing or accessing the relevant environment.

---

#### 9.5.5 Common Mistakes

**Mistake 1 — Relabelling laboratory testing as relevant environment testing**: Teams sometimes conduct additional laboratory tests with slightly more realistic parameters (e.g., adding some noise to synthetic data, testing at a slightly different temperature) and call this "relevant environment validation." This is still TRL 4.
*How to avoid*: Apply the external environment access test: did the team have to leave their own facilities, obtain access to external data, or work with a partner to conduct the validation? If no, critically examine whether TRL 5 is warranted.

**Mistake 2 — Accepting a single-condition relevant environment test as full TRL 5 validation**: Testing in a relevant environment once, under one set of conditions, is a starting point, not a full validation. TRL 5 requires systematic testing across the range of relevant environment conditions that the deployed system will encounter.
*How to avoid*: Check for coverage: does the validation report address the full range of relevant operational conditions, or only the most favourable subset?

**Mistake 3 — Confusing user testing with relevant environment validation for software**: User testing (beta testing, usability testing) introduces real-world users but may not introduce the technical environmental conditions that constitute relevant environment validation. An AI model tested by real users on clean, curated data is not at TRL 5; the same model tested with real, uncurated, distribution-shifted data may be.
*How to avoid*: Distinguish between user experience testing (which informs BRL) and technical environment validation (which determines TRL). Both may occur at TRL 5, but only the latter determines TRL assignment.

**Mistake 4 — Granting TRL 5 based on a paid pilot that has not yet started**: A signed pilot agreement or customer letter of intent is not TRL 5 evidence. The pilot must have been executed and results documented for TRL 5 to be warranted.
*How to avoid*: Apply the "completed activity" rule: TRL is assigned only for activities that have been completed and documented, not for activities planned or contracted.

**Mistake 5 — Overlooking the need for a gap analysis**: TRL 5 validation almost always reveals gaps between current performance and operational requirements. A startup that reports TRL 5 validation with no identified gaps is almost certainly underreporting technical challenges.
*How to avoid*: Require a gap analysis as part of TRL 5 evidence. The absence of a gap analysis is itself a red flag.

**Mistake 6 — Accepting peer-reviewed publication of another group's relevant environment results**: As at TRL 3, if the relevant environment testing was conducted by a third-party research group and the startup has not conducted their own equivalent testing, the startup is at a lower TRL.
*How to avoid*: Confirm that the cited relevant environment validation was conducted by or in direct collaboration with the founding team.

---

#### 9.5.6 How to Reach the Next TRL

To advance from TRL 5 to TRL 6:

**Activities that require only internal effort and time:**
- [ ] Prepare a demonstration-ready version of the system: more stable, better documented, and capable of being operated by someone other than the primary developer
- [ ] Develop demonstration protocols and materials (demonstration scripts, backup plans for technical failures, contingency data)
- [ ] Address the performance gaps identified in TRL 5 validation to the extent possible before demonstration
- [ ] Prepare technical documentation (one-pager, technical data sheet, system specification) suitable for a technically qualified external audience
- [ ] Conduct internal rehearsals of the demonstration

**Activities that require specific external events:**
- [ ] Identify and secure a demonstration audience: a prospective customer site visit, an industry conference demonstration slot, an investor technical due-diligence session, or a regulator pre-submission demonstration meeting
- [ ] Arrange for an independent technical assessor or evaluator to attend and document the demonstration
- [ ] Obtain access to the demonstration venue or partner site
- [ ] For regulated technologies: schedule a pre-submission interaction with the relevant regulatory body

---

#### 9.5.7 Confidence Indicators

**High Confidence (0.90–1.00)**: Validation report documenting multiple test conditions in a clearly defined and externally accessed relevant environment, with quantitative performance data, gap analysis, and external party involvement confirmed by documentation.

**Moderate Confidence (0.75–0.89)**: Validation report present with quantitative data but limited to a narrow range of conditions. External party involvement documented but limited. Gap analysis incomplete.

**Low Confidence (0.70–0.74)**: Relevant environment described and tested, but documentation of conditions is sparse and external involvement is not clearly documented. Minimum for TRL 5 assignment.

**Acceptable Gaps**: No external demonstration yet; no customer payment; no regulatory filing; no press coverage.

**Disqualifying Gaps**: No relevant environment access documented; all test data indistinguishable from laboratory test data; no external party involvement of any kind; all evidence is internal self-report.

---

#### 9.5.8 Sector-Specific Notes

| Sector | TRL 5 Characteristics | Key Evidence Sources |
|---|---|---|
| **Software/SaaS** | System tested with real user data or in a staging environment with production-representative data; performance under realistic load conditions measured | Load test reports, real data evaluation results, staging environment performance logs |
| **AI/ML** | Model evaluated on real-world (non-curated) data; distribution shift robustness tested; adversarial or edge-case performance assessed; model fairness/bias evaluation conducted | Real-world dataset evaluation reports, bias audit results, distribution shift analysis, fairness metrics |
| **Biotech/MedTech** | In vivo animal model study confirming primary endpoint; clinical simulation laboratory study; ex vivo tissue model results | GLP-compliant animal study report, clinical simulation results, ex vivo data |
| **DeepTech/Hardware** | Prototype tested in a representative physical environment (temperature cycling, vibration, electromagnetic compatibility); field measurement campaign (non-commercial) | Environmental test chamber reports, field measurement logs, EMC test results |
| **AgriTech** | Field trial on a research farm or partner farm with real soil, weather, and crop conditions; agronomist-supervised observation | Field trial reports, weather log data, crop yield or health measurements, agronomist sign-off |
| **ClimaTech** | Pilot-scale process tested in representative conditions; real feedstock or atmospheric input used; independent measurement of performance | Pilot plant performance data, real feedstock analysis, independent measurement records |
| **DefenceTech** | System tested in a representative operational environment (may be a test range, simulation centre, or equivalent); operational scenario fidelity documented | T&E report (may be classified); CONOPS-aligned test scenario documentation |

---

### TRL 6 — Technology Demonstrated in Relevant Environment

---

#### 9.6.1 Definition

TRL 6 marks the transition from internal validation to external demonstration. At this level, the technology has been demonstrated — not merely validated internally — in a relevant environment, to an external audience. The demonstration is a structured, witnessed event in which the technology performs its intended function under realistic conditions in front of technically qualified observers who are not members of the founding team.

The distinction between TRL 5 and TRL 6 is one of audience and intent. At TRL 5, the team validates the technology for their own satisfaction — to confirm it works. At TRL 6, the team demonstrates the technology to external parties — to show others that it works. The external demonstration introduces a new constraint: the technology must perform reliably enough to demonstrate on demand, without prior knowledge of exactly what conditions will be present.

A TRL 6 demonstration typically represents the first time the technology is shown to prospective customers, investors, regulators, or independent technical assessors in a realistic setting. This is the stage at which prototypes are refined enough to show to the world, and where the gap between the technology's current capabilities and its ultimate commercial requirements becomes externally visible.

TRL 6 does not require commercial deployment or payment by users. It requires a documented, witnessed demonstration in a realistic environment that shows the full system performing its primary intended function. A successful TRL 6 demonstration is one in which technically qualified external observers can confirm, from what they witnessed, that the technology is capable of performing its core function in conditions representative of real operation.

**Key boundary with TRL 7**: TRL 6 ends and TRL 7 begins when the technology is no longer merely demonstrated in a realistic environment but is actually tested in the operational environment itself — the environment in which the system will ultimately be deployed. The distinction is between "realistic" (simulated or representative) and "operational" (actual deployment context).

---

#### 9.6.2 Required Evidence

**Must Have:**

- A demonstration record (contemporaneous documentation) specifying: (a) date, location, and duration of the demonstration, (b) the identities and organisations of external observers present, (c) what was demonstrated (specific functions, scenarios, use cases), (d) the conditions under which the demonstration occurred (environment, inputs, test cases used), and (e) the outcome of the demonstration — what the observers saw and whether the system met its demonstrated performance targets.
- Sign-off or attestation from at least one external observer confirming that they witnessed the demonstration and that the system performed as described. This may take the form of a signed witness statement, a letter from the observer's organisation, or meeting minutes that include the observer's confirmation.
- Quantitative performance data from the demonstration event itself (not historical data presented at the event).

**Should Have:**

- Video recording of the demonstration (with consent where applicable)
- Feedback from external observers (structured or unstructured): what impressed them, what they questioned, what they would need to see before making a commercial or investment decision
- A post-demonstration technical debrief report documenting what went well, what failed or underperformed, and what was learned
- Any post-demonstration follow-up communications from observers expressing continued interest
- Technical questions raised by observers and the team's responses (demonstrating that the team can answer advanced technical questions about the system)

---

#### 9.6.3 Technical Expectations

At TRL 6, evaluators should expect:

- Evidence that the demonstration was meaningful — not a scripted show with a pre-loaded, cherry-picked result. The demonstration should have included conditions or inputs that were not entirely known in advance to the demonstrating team.
- A system capable of being operated by someone other than the primary developer. A demonstration where only one specific person can operate the system raises concerns about robustness.
- External observer engagement: the observers should have asked technical questions, raised concerns, or identified gaps. A demonstration with no observer feedback is either not real or not meaningful.
- Clear documentation of what the demonstration did and did not cover. TRL 6 demonstrations should acknowledge what aspects of the technology remain undemonstrated.

---

#### 9.6.4 Validation Requirements

- **Who must have performed validation**: A technically qualified external audience must have witnessed the demonstration. "External" means outside the founding team and outside any organisation directly affiliated with the founding team (investors already committed are borderline; treat as lower-weight external witness).
- **Nature of validation**: Live, unscripted (or minimally scripted) demonstration of the full system performing its primary function in a realistic environment.
- **Documentation standard**: The demonstration must be documented contemporaneously — a retrospective account written weeks later by the founding team is lower-quality evidence. Contemporaneous notes from an external observer are the gold standard.
- **Minimum audience**: At least one technically qualified external observer who can assess the demonstration against the technology's claimed specifications.

---

#### 9.6.5 Common Mistakes

**Mistake 1 — Treating a conference poster or panel presentation as a TRL 6 demonstration**: Presenting slides or a poster about the technology at a conference is marketing, not demonstration. TRL 6 requires that the actual technology is demonstrated performing its function — not described in a slide deck.
*How to avoid*: Require evidence that the physical or digital system was operated in front of observers, not merely described.

**Mistake 2 — Accepting a static product demo at a startup pitch event as TRL 6 evidence**: Startup pitch events typically involve short, polished demonstrations designed for a generalist audience in an investor-friendly environment. These are typically TRL 4–5 demonstrations at most — the environment is rarely representative of real deployment conditions.
*How to avoid*: Apply the "relevant environment" test: was the demonstration environment meaningfully representative of the actual deployment context? A demo at an accelerator demo day almost never qualifies as TRL 6.

**Mistake 3 — Requiring TRL 6 to be a paying customer pilot**: TRL 6 does not require payment or a commercial agreement. External demonstration to an investor or industry expert in a realistic environment qualifies. Conflating TRL 6 with the commercial pilot stage leads to systematic undervaluation of technically mature startups that have not yet monetised.
*How to avoid*: Decouple TRL from BRL in the assessment. A paid pilot is a strong BRL signal; it may or may not correspond to TRL 6 depending on the technical content of the pilot.

**Mistake 4 — Conflating a trade show demo with a technical demonstration**: A trade show product demonstration is designed for commercial persuasion, not technical validation. It may be conducted under highly controlled conditions (pre-loaded data, controlled connectivity, curated scenarios) that do not represent real operational conditions.
*How to avoid*: Investigate the technical conditions of any demonstration submitted as TRL 6 evidence. If the team cannot describe the exact conditions, inputs, and potential failure modes of the demonstration, treat it as lower than TRL 6.

**Mistake 5 — Accepting a single positive demonstration as definitive TRL 6 evidence**: A single successful demonstration does not fully establish TRL 6 if that demonstration was not representative of the range of operational conditions. Robust TRL 6 evidence includes multiple demonstrations under varying realistic conditions.
*How to avoid*: Ask whether the technology has been demonstrated multiple times with consistent results. A technology that works beautifully once but inconsistently thereafter has a repeatability problem that must be addressed before TRL 6 is solidly established.

**Mistake 6 — Ignoring the external observer qualification**: An external observer who is not technically qualified to assess the demonstration adds little evidentiary value. The CFO of a partner company watching a technical demonstration does not provide the same validation weight as a domain expert engineer from the same organisation.
*How to avoid*: Check the technical qualifications of named external observers. Require that at least one observer has the technical expertise to assess the demonstration against specifications.

---

#### 9.6.6 How to Reach the Next TRL

To advance from TRL 6 to TRL 7:

**Activities that require only internal effort and time:**
- [ ] Harden the prototype for deployment in an operational environment: ruggedise hardware, implement security measures for software, address regulatory requirements for the target operational context
- [ ] Develop operational documentation: user manuals, installation guides, maintenance procedures, troubleshooting guides
- [ ] Design and execute a system-level qualification test plan against the operational environment requirements
- [ ] Identify and mitigate failure modes that could occur in the operational environment but not in the relevant demonstration environment
- [ ] Train the system to handle operational environment edge cases not covered in TRL 5–6 testing

**Activities that require specific external events:**
- [ ] Negotiate access to an operational environment for system deployment (requires agreement with an operational partner, customer, or government body)
- [ ] Complete any required regulatory notifications or approvals for testing in the operational environment
- [ ] Procure operational-grade components or certifications required for the target deployment environment (e.g., industrial certifications, medical device classifications, aviation standards)
- [ ] Enter into an operational trial or pilot agreement with a partner willing to host the prototype in their operational environment

---

#### 9.6.7 Confidence Indicators

**High Confidence (0.90–1.00)**: Multiple witnessed demonstrations in realistic environments with contemporaneous documentation, sign-off from technically qualified external observers, video evidence, and structured observer feedback.

**Moderate Confidence (0.75–0.89)**: At least one witnessed demonstration with external observer attestation, reasonable environment fidelity, quantitative performance data present.

**Low Confidence (0.70–0.74)**: Demonstration described and minimally documented; one external observer named but attestation is informal (e.g., email); environment described but fidelity to operational conditions is partial.

**Acceptable Gaps**: No commercial agreement; no regulatory clearance; no formal user documentation; no scaling plan.

**Disqualifying Gaps**: No external observer evidence of any kind; demonstration described but only internally documented; environment demonstrably not representative of real-world conditions.

---

#### 9.6.8 Sector-Specific Notes

| Sector | TRL 6 Characteristics | Key Evidence Sources |
|---|---|---|
| **Software/SaaS** | Live system demonstrated to prospective customers in a real-data environment; customer acceptance testing (non-commercial) conducted | Customer visit records, UAT report, live demonstration recordings |
| **AI/ML** | Model demonstrated processing real-world inputs in front of domain experts; model performance on live or real data confirmed; independent evaluation by domain expert conducted | Expert evaluation report, live inference demonstration records, independent test results |
| **Biotech/MedTech** | GLP-compliant preclinical results presented to regulatory body or scientific advisory board; IND-enabling studies underway or complete (pharma); CE mark technical file draft complete (medtech) | Scientific advisory board meeting minutes, regulatory meeting minutes, technical file documentation |
| **DeepTech/Hardware** | Engineering prototype demonstrated at industry event, customer site, or independent test facility; prototype operated by non-team personnel | Test facility records, customer site visit documentation, independent operator log |
| **AgriTech** | Field trial results presented to agricultural industry body, extension service, or major agricultural customer; agronomist or expert farmer feedback documented | Expert review report, industry body presentation records, farmer feedback documentation |
| **ClimaTech** | Technology demonstrated at pilot scale to infrastructure operators, government agency, or major industrial customer; performance data shared with independent reviewer | Government agency meeting records, industrial partner site visit documentation, independent review report |
| **DefenceTech** | System demonstrated to programme office or defence end user in a representative test environment; DARPA/MoD evaluator present and documented | Programme office evaluation report (may be classified); evaluator attestation |

---

### TRL 7 — System Prototype Demonstrated in Operational Environment

---

#### 9.7.1 Definition

TRL 7 represents a major maturity milestone: the technology is no longer being demonstrated in a simulated or representative environment, but is actually being operated and tested in the real operational environment — the actual context in which the finished product will be deployed and used. The system at TRL 7 is a near-final prototype: it contains all or nearly all the functions of the intended end system, built with production-representative components, processes, and interfaces, and operated by or alongside real end-users, operators, or deploying organisations.

The operational environment at TRL 7 introduces all of the variability, constraints, regulatory context, user behaviour, and environmental conditions that the system will face in commercial deployment. A medical diagnostic device is tested in a real clinical setting with real clinical workflows and real patient samples. An agricultural IoT platform is deployed in a commercial farming operation. An AI fraud detection system is integrated into a bank's actual transaction processing infrastructure. A deeptech sensor is installed in an industrial facility and operated through a full production cycle.

What distinguishes TRL 7 from TRL 8 is the prototype status of the system: at TRL 7, the system is a prototype (not yet the production-qualified system), and the operational testing is explicitly an evaluation activity — not normal commercial operation. The system is being operated in the real environment specifically to identify remaining gaps, validate performance against operational requirements, and generate the evidence needed to justify full system qualification.

TRL 7 is the level at which regulatory interactions typically intensify, as the operational environment for many technology domains is a regulated context. This is also the level at which the gap between a technically functional system and a commercially deployable product becomes most visible — and where many deep-tech startups discover that the distance from "working prototype" to "qualified system" is far larger than anticipated.

**Key boundary with TRL 8**: TRL 7 ends and TRL 8 begins when the system has been formally qualified — that is, when a structured qualification programme has been completed, the system has been tested against all relevant standards and specifications, and the system has been declared by an appropriate authority (the founding team's own quality management system for non-regulated domains, or a regulatory body for regulated domains) to be ready for commercial deployment.

---

#### 9.7.2 Required Evidence

**Must Have:**

- An operational trial report documenting: (a) the operational environment in which the prototype was deployed, including the name of the hosting organisation (or a written description of the operational environment if the organisation prefers anonymity), (b) the duration of the operational trial, (c) the specific functions and scenarios exercised during the trial, (d) quantitative performance metrics measured during operation, (e) comparison of operational performance against laboratory and relevant environment results, (f) identified gaps and failure modes encountered, and (g) conclusions on operational performance and readiness for system qualification.
- Evidence that the prototype was operated in the actual operational environment, not a replica or simulation thereof. This may include photographs, system logs from operational equipment, facility access records, or a letter from the hosting organisation confirming the trial.
- A named hosting organisation or operational partner (or written justification for why the partner must remain confidential, with a commitment to provide this information to the evaluating organisation under NDA).

**Should Have:**

- End-user or operator feedback from the operational trial, including any usability, reliability, or performance concerns raised by real users
- System log data from the operational deployment (not just test data — real operational logs)
- An incident or issue log documenting problems encountered during the operational trial
- Third-party or independent assessment of the operational trial results
- Evidence that the operational trial was conducted under a formal trial agreement (pilot agreement, trial services agreement, etc.)
- Updated system specification reflecting lessons learned from operational trial
- A qualification gap analysis identifying what must be resolved before TRL 8 qualification

---

#### 9.7.3 Technical Expectations

At TRL 7, evaluators should expect:

- A system that is functionally complete: all primary features are implemented and testable. A prototype with core features only and significant planned functionality missing is at TRL 5–6, not TRL 7.
- Real operational challenges: TRL 7 operational trials almost always reveal unexpected system behaviours, integration problems with existing operational infrastructure, user experience issues, and performance shortfalls under real load. Documentation that shows no problems is almost certainly understating the situation.
- Evidence of operational context complexity: the documentation should convey the genuine complexity of the operational environment and demonstrate that the system has been tested against that complexity.
- A credible path to qualification: the team should be able to articulate, based on TRL 7 findings, what specific steps are required to achieve TRL 8 qualification. Vague answers to "what's left to do?" suggest the team does not yet understand the gap.

---

#### 9.7.4 Validation Requirements

- **Who must have performed validation**: The founding team in collaboration with an operational partner organisation. The partner organisation must be a genuine operational entity — not a partner organisation set up specifically to create the impression of operational validation.
- **Nature of validation**: Operational deployment and testing of the near-final prototype in the real deployment environment, against operational requirements.
- **Partner organisation minimum credibility**: The operational partner should be a legitimate organisation in the target market that would have a genuine reason to host such a trial. Red flags include: partner organisations with no verifiable existence, partners with no track record in the target domain, or partners who are financially related to the founding team.
- **Duration minimum**: An operational trial lasting less than one week (unless the operational cycle is inherently short) is insufficient for TRL 7. The trial should be long enough to capture the full range of operational conditions, including edge cases, peak loads, and routine maintenance cycles.

---

#### 9.7.5 Common Mistakes

**Mistake 1 — Conflating a "beta test" with operational trial**: A software beta test with volunteer users is not equivalent to operational prototype testing. Beta tests often use self-selected users in non-operational contexts. TRL 7 requires the system to be operated in the actual workflow of a genuine operational organisation.
*How to avoid*: Investigate the beta test methodology. Was it conducted in the actual operational environment of real organisations? Were users using the system as part of their real work, or as an optional activity? Apply the operational workflow test.

**Mistake 2 — Accepting a single-site operational trial as full TRL 7 evidence when multiple site types are required**: For technologies that must operate across different types of operational environments (e.g., a medical device that must work in both urban hospitals and rural clinics), a trial at a single representative site may not constitute full TRL 7 validation.
*How to avoid*: Check whether the operational environment of the trial is representative of the full intended deployment scope. If not, flag the limitation.

**Mistake 3 — Confusing an operational pilot with commercial deployment**: A paid operational pilot is still a pilot — it is TRL 7 evidence, not TRL 9. Commercial payment does not automatically elevate TRL; what matters is whether the system has been fully qualified and proven across multiple operational contexts.
*How to avoid*: Apply the qualification test: has the system been through a formal qualification programme and declared ready for unrestricted commercial deployment? If not, it is at most TRL 7–8.

**Mistake 4 — Overlooking integration with operational infrastructure**: A prototype that works as a standalone system but has not been integrated with the existing operational infrastructure of the host organisation is not fully at TRL 7. Operational environments always include existing IT systems, workflows, regulatory processes, and human actors that the new technology must interface with.
*How to avoid*: Check whether the operational trial included integration with existing infrastructure. A system tested in isolation within an operational environment is at best TRL 6.

**Mistake 5 — Not distinguishing between "operational environment" and "realistic environment"**: TRL 6 uses a relevant/realistic environment; TRL 7 uses the operational environment. Evaluators sometimes award TRL 7 for what is clearly a TRL 6 demonstration in a very realistic but not actual operational setting.
*How to avoid*: Apply the strict test: was the hosting organisation actually using the system as part of their normal operations, even during the trial period? If the system was present but not operationally active (only running on the side), it is TRL 6.

**Mistake 6 — Ignoring duration and continuity of operational trial**: A two-hour demonstration at a customer site during which the customer's staff operate the system does not constitute an operational trial. TRL 7 requires extended operational exposure.
*How to avoid*: Check trial duration and continuity. An operational trial should span multiple operational cycles and reveal the system's behaviour under all typical operational conditions.

---

#### 9.7.6 How to Reach the Next TRL

To advance from TRL 7 to TRL 8:

**Activities that require only internal effort and time:**
- [ ] Develop and execute a formal system qualification plan against all relevant standards and specifications
- [ ] Complete all design modifications identified during the operational trial
- [ ] Conduct reliability and durability testing (MTBF analysis, accelerated life testing, security penetration testing, etc.) as appropriate to the domain
- [ ] Produce a complete system documentation package (design documentation, test results, compliance records, user documentation)
- [ ] Conduct a formal design review (internal) confirming the system is ready for external qualification

**Activities that require specific external events:**
- [ ] Regulatory submission and review process (for medical devices, pharmaceuticals, agrichemicals, aerospace equipment, financial services software, etc.)
- [ ] Third-party certification or testing (e.g., CE marking, UL certification, ISO certification, SOC 2 audit, penetration testing by accredited firm)
- [ ] Independent verification and validation (IV&V) by an accredited external body
- [ ] Customer or deploying organisation formal acceptance testing
- [ ] Insurance or liability clearance for operational deployment in certain domains

---

#### 9.7.7 Confidence Indicators

**High Confidence (0.90–1.00)**: Full operational trial report with named partner, duration documented, quantitative operational performance data, end-user feedback recorded, independent assessment present, and trial formally documented in a signed trial agreement.

**Moderate Confidence (0.75–0.89)**: Operational trial documented with reasonable detail but partner organisation is described without name (with justification); end-user feedback is informal; duration is short relative to operational cycle.

**Low Confidence (0.70–0.74)**: Operational trial described but with sparse documentation; partner organisation not documented at all; operational performance data is limited. Minimum threshold for TRL 7.

**Acceptable Gaps**: No regulatory clearance yet; no full qualification; no commercial contract; no multi-site deployment.

**Disqualifying Gaps**: No operational partner; trial conducted entirely in team-controlled environment described as "operational"; no operational performance data distinguishable from laboratory data; partner organisation shows signs of being related to founding team.

---

#### 9.7.8 Sector-Specific Notes

| Sector | TRL 7 Characteristics | Key Evidence Sources |
|---|---|---|
| **Software/SaaS** | Integrated with customer's production infrastructure; real users using the system as part of their daily workflow; production performance data available | Customer integration logs, active user counts and engagement data, production performance dashboards |
| **AI/ML** | Model deployed in production-representative pipeline; real-world inference at scale; model monitoring and drift detection operational; human-in-the-loop workflows tested | Model monitoring logs, inference latency/accuracy metrics from production pipeline, drift detection reports |
| **Biotech/MedTech** | Phase I/II clinical trial underway or complete (pharma); clinical evaluation in hospital setting for MedTech; regulatory pre-submission package submitted | Clinical trial registration record (clinicaltrials.gov or equivalent), IRB approval, clinical performance study report |
| **DeepTech/Hardware** | Prototype deployed in an industrial, commercial, or field operational environment; operated through full production cycles; facility safety and compliance verified | Facility deployment records, operational logs, safety clearance documentation, operator feedback reports |
| **AgriTech** | Commercial farm deployment with full crop cycle observation; agronomist and farmer sign-off; yield or quality data from commercial farming conditions | Commercial farm trial agreement, full season yield data, farmer and agronomist attestation |
| **ClimaTech** | Pilot plant or full-scale subsystem operating in real industrial or infrastructure context; emissions, energy, or capture performance measured under operational conditions | Industrial facility operation records, emissions monitoring data, independent performance verification |
| **DefenceTech** | System demonstrated in operational military or dual-use environment; user unit assessment completed; programme milestone review passed | Milestone review decision document (may be classified); user unit assessment report |

---

### TRL 8 — System Complete and Qualified

---

#### 9.8.1 Definition

TRL 8 represents the completion of system development. At this level, the technology has progressed from prototype to final system: all components are production-grade, all interfaces are specified and implemented, the system has been tested and has passed all qualification requirements, and the system has been declared ready for its first commercial or operational deployment. TRL 8 is the last level before actual mission/commercial operation begins.

The defining characteristic of TRL 8 is qualification: a formal, documented process in which the system is tested against all required standards, specifications, and regulatory requirements, and is declared by an appropriate authority to meet those requirements. Qualification is not the same as operational deployment; it is the gate that must be passed before deployment is authorised.

What constitutes "qualification" depends on the domain:
- For a medical device: regulatory clearance (510(k), CE mark, Medsafe certification, etc.) from the relevant regulatory body
- For a pharmaceutical: regulatory approval (IND, NDA, EMA authorisation, etc.) for clinical use
- For safety-critical hardware: third-party certification to relevant standards (ISO, IEC, DO-178C for aviation software, etc.)
- For enterprise software: successful completion of security audit, penetration testing, compliance certification (ISO 27001, SOC 2 Type II, GDPR Data Protection Impact Assessment)
- For a consumer product: compliance with consumer safety standards (CE, FCC, UL, etc.)
- For an AI/ML system in a regulated context: Model documentation package meeting regulatory AI guidelines (EU AI Act conformity assessment, FDA AI/ML SaMD guidance, etc.)
- For an agricultural product: regulatory approval from the relevant national agricultural authority

For technologies in non-regulated domains, qualification is a self-declared readiness milestone based on the completion of a documented quality management process — though this carries lower evidentiary weight than third-party qualification.

**Key boundary with TRL 9**: TRL 8 ends and TRL 9 begins when the qualified system has been deployed and operated in real commercial or operational conditions across multiple deployments, with sustained evidence of operational performance meeting requirements.

---

#### 9.8.2 Required Evidence

**Must Have:**

- For regulated technologies: a regulatory clearance certificate, approval letter, or equivalent official document from the relevant regulatory authority (FDA, CE Notified Body, MHRA, TGA, CDSCO, SEBI, CAA, etc.) confirming the system is approved or cleared for the intended use.
- For non-regulated technologies: a formal qualification test report documenting all qualification tests conducted, the standards against which the system was tested, the test results, and a formal declaration of qualification readiness. This report must be produced against a documented qualification plan established before testing commenced.
- Evidence that the final production-representative system (not an earlier prototype) was the subject of qualification testing. Qualification of an earlier prototype that differs significantly from the production system does not constitute TRL 8.
- A completed system documentation package including, at minimum: product specification, user documentation, maintenance/support documentation, and configuration/version management records.

**Should Have:**

- Third-party certification or test laboratory reports (for non-regulatory domains)
- Quality management system documentation confirming the system was developed and tested under a documented quality framework (ISO 9001 or equivalent)
- Manufacturing readiness assessment or supply chain qualification (for hardware systems)
- Legal review confirmation that all third-party IP and licensing requirements have been addressed
- Signed customer purchase order, deployment agreement, or Letter of Award based on the qualified system (highest-confidence BRL signal coinciding with TRL 8)
- Insurance or liability documentation appropriate for the deployment domain

---

#### 9.8.3 Technical Expectations

At TRL 8, evaluators should expect:

- Definitive, externally verifiable proof of qualification. For regulated domains, this means an official document with a certificate or reference number from the regulatory body. For non-regulated domains, this means a comprehensive qualification test report that could withstand external technical audit.
- A production-ready system, not a research prototype. The system at TRL 8 is built from production-grade components, manufactured (even in small quantities) through production-representative processes, and packaged, documented, and supported to a standard appropriate for commercial deployment.
- Completion of the supply chain: for hardware, this means the components, manufacturing processes, and supply sources for the production system have been identified and verified. For software, this means the production infrastructure, deployment pipeline, and support processes are established.
- A zero-to-first-customer plan: a startup at TRL 8 should be able to articulate exactly how they will go from the current qualified system to their first commercial deployment. If the plan is vague, the qualification may not be as complete as claimed.

---

#### 9.8.4 Validation Requirements

- **Who must have performed validation**: For regulated domains — the relevant regulatory authority. For non-regulated domains — the founding team plus an independent third-party validator (certification body, test laboratory, security auditor, etc.).
- **Nature of validation**: Formal qualification testing against defined standards and specifications; regulatory review and approval process (where applicable); independent third-party verification.
- **Documentation standard**: Qualification documentation must be complete, controlled (version-managed), and reproducible. An external reviewer should be able to read the qualification package and confirm that the system meets its stated specifications.
- **Non-negotiable for regulated technologies**: Regulatory clearance is a hard requirement, not a Should Have. A system in a regulated domain that has not received regulatory clearance is at TRL 7, not TRL 8, regardless of how complete the system otherwise is.

---

#### 9.8.5 Common Mistakes

**Mistake 1 — Equating regulatory filing with regulatory clearance**: A startup that has submitted a regulatory application (filed a 510(k), submitted a CE technical file, applied for ISO certification) has not achieved TRL 8. Filing is a TRL 7 activity; clearance or certification is TRL 8.
*How to avoid*: Apply a hard rule: for regulated technologies, TRL 8 requires a clearance document, not a filing reference number.

**Mistake 2 — Accepting a "complete" prototype as a qualified system**: A prototype that has been fully developed and internally tested but not subjected to a formal qualification process — with defined pass/fail criteria, complete documentation, and independent validation — is TRL 7, not TRL 8.
*How to avoid*: Ask for the qualification plan and the qualification test results. If no formal qualification plan existed before testing commenced, the testing cannot constitute qualification.

**Mistake 3 — Treating a customer order for an unqualified system as TRL 8 evidence**: A customer may order a system that is not yet fully qualified, particularly in non-regulated domains. The commercial agreement is BRL evidence; it is not a substitute for technical qualification evidence.
*How to avoid*: Evaluate TRL based on technical qualification evidence, not on commercial agreements. Note the commercial agreement separately in the BRL assessment.

**Mistake 4 — Ignoring manufacturing readiness for hardware systems**: A hardware system that has been qualified as a prototype but has not established a production-ready manufacturing process is not truly at TRL 8. The production system must be manufacturable at the required quality level before TRL 8 is warranted.
*How to avoid*: Ask about manufacturing: how many units have been produced? Through what process? At what quality yield? A hardware startup that has built only one handcrafted prototype is not at TRL 8 regardless of that prototype's technical quality.

**Mistake 5 — Accepting software "launch" as TRL 8 qualification**: Launching a software product (making it publicly available) is not equivalent to qualification. Software qualification at TRL 8 requires completed security audits, performance load tests, compliance certifications, and disaster recovery testing — not just a production deployment.
*How to avoid*: For software, define qualification as the completion of all security, performance, compliance, and disaster recovery validation activities. Check each of these for evidence of completion.

**Mistake 6 — Applying non-regulated qualification standards to regulated domains**: In regulated domains, self-declared qualification is not sufficient regardless of how rigorous the internal process is. An evaluator who accepts a high-quality internal qualification report as TRL 8 evidence for a medical device (without regulatory clearance) is committing a systematic error.
*How to avoid*: Identify whether the technology domain is regulated at the outset. For all regulated domains, apply the hard regulatory clearance requirement for TRL 8.

---

#### 9.8.6 How to Reach the Next TRL

To advance from TRL 8 to TRL 9:

**Activities that require only internal effort and time:**
- [ ] Develop deployment playbooks and customer onboarding documentation
- [ ] Establish post-deployment monitoring, support, and incident response processes
- [ ] Train customer-facing and operational support staff
- [ ] Deploy the system at the first commercial site and begin structured post-deployment monitoring
- [ ] Collect systematic performance and reliability data across the first deployment period
- [ ] Develop case study and reference documentation from the first deployment

**Activities that require specific external events:**
- [ ] Securing a first commercial customer deployment agreement (requires commercial negotiation)
- [ ] Completing the first customer's internal procurement and approval process
- [ ] Negotiating data access or system integration with the customer's existing infrastructure
- [ ] For regulated technologies: post-market surveillance reporting requirements begin (regulatory obligation begins at first deployment)
- [ ] Additional regulatory approvals for different geographies or use extensions

---

#### 9.8.7 Confidence Indicators

**High Confidence (0.90–1.00)**: Official regulatory clearance certificate or third-party certification from a recognised body; complete qualification test package; production-representative system documented; supply chain established.

**Moderate Confidence (0.75–0.89)**: Internal qualification documentation is comprehensive and credible; third-party security or compliance audit completed; regulatory clearance pending final decision with positive review feedback received.

**Low Confidence (0.70–0.74)**: System described as qualified but documentation is incomplete; for non-regulated domain, qualification plan exists but some qualification tests are pending; no third-party involvement. Minimum threshold for TRL 8.

**Acceptable Gaps**: No commercial revenue yet; no multi-site deployment; no long-term operational data.

**Disqualifying Gaps**: For regulated domains — no regulatory clearance and no evidence that the regulatory process has been completed; for all domains — no qualification test results; system known to be a prototype rather than a production-grade system.

---

#### 9.8.8 Sector-Specific Notes

| Sector | TRL 8 Characteristics | Key Evidence Sources |
|---|---|---|
| **Software/SaaS** | SOC 2 Type II audit completed; GDPR/CCPA compliance documented; penetration test by accredited firm passed; production SLA defined; DR/BCP tested | SOC 2 audit report, pen test report, compliance certification, DR test results |
| **AI/ML** | Conformity assessment under applicable AI regulations completed; model cards and transparency documentation finalised; bias and explainability audit completed; monitoring and retraining pipeline in production | AI conformity assessment documentation, model card, bias audit report, EU AI Act compliance record (if applicable) |
| **Biotech/MedTech** | Regulatory approval received (NDA, 510(k), CE Mark, PMDA approval, etc.); GMP manufacturing established; post-market surveillance plan approved | Approval letter, GMP certificate, manufacturing site audit report, PMS plan |
| **DeepTech/Hardware** | CE, UL, FCC, or equivalent certification complete; qualification test reports to relevant standards (ISO, IEC, MIL-STD if applicable); production line qualified | Certification documents, qualification test reports, production line validation records |
| **AgriTech** | National pesticide/seed/product registration complete; field trial data package submitted and approved; product labelling approved | Registration certificate, regulatory approval letter, approved product label |
| **ClimaTech** | Environmental impact assessment approved; technology certified by relevant standards body (e.g., Gold Standard, ISO 14064); performance guarantee documentation established | EIA approval, carbon standard certification, performance guarantee contract |
| **DefenceTech** | System qualification review (SQR) passed; programme milestone C approval (or equivalent); export control classification confirmed; ITAR/EAR licence obtained if required | SQR decision document, milestone C approval (may be classified); ITAR/EAR licence |

---

### TRL 9 — Actual System Proven in Operational Environment

---

#### 9.9.1 Definition

TRL 9 is the highest level of technology readiness in the TIDES framework. At this level, the actual system — the production-qualified system, not a prototype — has been deployed and operated successfully in real operational conditions across multiple deployment instances, over a sufficient time period, and across a sufficient range of operational conditions to constitute a proven track record of reliable operational performance.

The critical distinction from TRL 8 is the transition from "declared ready for deployment" to "proven in deployment." TRL 8 is a gate decision; TRL 9 is the evidence of what happened after the gate was passed. A system at TRL 9 has been through at least one full operational cycle in its primary application domain, has been used by real end-users or operators who were not members of the founding team, has encountered real operational conditions (including unexpected conditions and failure scenarios), and has produced documented evidence of its performance across these conditions.

TRL 9 in the TIDES context does not require that the system has been deployed at massive commercial scale. It requires that the system has been proven in real operation — even if only at a limited commercial scale — with evidence of sustained, reliable performance that justifies confidence in its operational readiness for broader deployment. A startup at TRL 9 may be a pre-Series A company with three paying customers, as long as those deployments have generated systematic evidence of operational performance across a meaningful range of conditions.

What TRL 9 does signify is that the primary technical risk has been retired. The question of "does this technology work in the real world?" has been answered affirmatively, with evidence. Remaining risks for a TRL 9 startup are primarily commercial, operational, and scaling risks — not technical feasibility risks.

**Note on "mission-proven" terminology**: In aerospace and defence contexts, TRL 9 is sometimes described as "mission-proven" (NASA) or "flight-proven" (ESA). In the TIDES startup context, the equivalent is "commercially proven" or "operationally proven" — meaning the system has demonstrated reliable performance in real commercial or operational use.

---

#### 9.9.2 Required Evidence

**Must Have:**

- Documented evidence of operational deployment in at least two distinct deployment instances (different customers, sites, or use cases — not two instances of the same customer). Single-customer deployments, even large ones, constitute TRL 7–8 evidence for purposes of operational proof.
- Quantitative operational performance data covering a meaningful period of real operation (minimum six months of operational data, or evidence that shorter periods are representative of full operational cycles for the specific domain).
- Evidence that operational performance meets or exceeds the specifications established at TRL 2 and refined through subsequent development stages.
- Evidence that the system has encountered and successfully handled real operational challenges (not just nominal operation). This may include incident reports showing how the system responded to unexpected conditions, failure reports showing how the system's failsafe or recovery mechanisms worked, or performance data showing consistent performance across variable operational conditions.

**Should Have:**

- Customer references or testimonials from operational users (with permission) documenting their operational experience
- Post-deployment performance monitoring data over the full operational period
- Incident and bug report logs showing the nature, frequency, and resolution of operational issues
- Comparison of operational performance against the performance achieved in TRL 7 operational trials (to confirm that qualification-to-deployment performance was maintained)
- Evidence of operational deployment in diverse operational contexts (geographic, organisational, or environmental diversity)
- Revenue data from commercial deployments (this is BRL evidence but provides strong corroboration of TRL 9 status)
- Third-party or independent post-deployment evaluation report

---

#### 9.9.3 Technical Expectations

At TRL 9, evaluators should expect:

- Real operational data, not just first-deployment results. TRL 9 requires sustained, multi-deployment operational evidence. A single deployment — even an extensive and well-documented one — is at the boundary of TRL 8/9; multiple deployments with consistent results clearly establish TRL 9.
- Evidence of operational maturity: the team should have established post-deployment monitoring, support operations, update/patch management, and user support processes. A technology is not truly proven in operation if the team is still managing it as a research project.
- Honesty about operational limitations: TRL 9 does not mean the technology is perfect. Operational data should reveal the conditions under which performance is strongest and weakest, the failure modes encountered and how they were resolved, and the operational edge cases that remain challenging.
- Commercial sustainability signals: while TRL 9 is a technical designation, at this maturity level it would be extraordinary for the technology to have no associated commercial activity. Revenue, repeat customer deployments, and commercial contract renewals are not TRL evidence per se, but their complete absence at TRL 9 warrants scrutiny.

---

#### 9.9.4 Validation Requirements

- **Who must have performed validation**: Real customers, operators, or deploying organisations operating the system in their normal operational activities — not the founding team, not the founding team's partner organisations established for the purpose, and not evaluation observers.
- **Nature of validation**: Sustained operational use producing real operational data, with performance assessed against defined specifications.
- **Minimum deployment instances**: Two or more distinct operational deployments (different organisations, sites, or clearly distinct use cases) with documented performance data.
- **Minimum duration**: Six months of operational data per deployment, or a complete operational cycle if the operational cycle is inherently shorter (e.g., a single agricultural growing season, a single clinical trial cycle, a single fiscal year processing cycle for a financial software product).
- **Third-party assessment**: A post-deployment review by an independent technical assessor, industry analyst, or auditor substantially increases confidence at TRL 9.

---

#### 9.9.5 Common Mistakes

**Mistake 1 — Claiming TRL 9 based on a single-customer deployment**: A single operational deployment, regardless of its size or duration, does not constitute "proven" operational readiness. TRL 9 requires evidence across multiple deployments demonstrating consistent performance in varying operational conditions.
*How to avoid*: Apply the multi-deployment requirement strictly. One large customer is TRL 7–8 operationally; multiple customers with consistent results are TRL 9.

**Mistake 2 — Conflating commercial success with TRL 9**: A startup with significant revenue and a large customer base but whose technology is still under active development (frequent major updates, significant customer-reported defects, ongoing fundamental capability changes) is not at TRL 9. Commercial success is BRL evidence; technical maturity is TRL evidence.
*How to avoid*: Separate commercial indicators from technical maturity indicators. Ask specifically about system stability, defect rates, deployment consistency, and performance reproducibility across customers.

**Mistake 3 — Accepting self-reported operational performance without third-party corroboration**: A startup may report impressive operational performance metrics without customer or third-party corroboration. At TRL 9, the evidence standard should require external corroboration of operational performance claims.
*How to avoid*: For TRL 9, require at least one independently verifiable source of operational performance data (customer testimonial with consent, third-party audit, published case study).

**Mistake 4 — Treating a continuously evolving AI/ML model as TRL 9**: An AI/ML system that is under constant, significant retraining and architectural change is not proven in the way that TRL 9 requires. A TRL 9 AI/ML system has a stable production model (even if minor updates are applied) whose performance in the operational environment is well-characterised and reproducible.
*How to avoid*: For AI/ML, assess whether the production model has been stable long enough to accumulate meaningful operational performance data. If the model is being substantially retrained every few weeks due to performance degradation, it is operationally unstable and TRL 8 is more appropriate.

**Mistake 5 — Requiring TRL 9 to mean widespread commercial deployment**: TRL 9 is about proven operational performance, not commercial scale. A startup with two well-documented, multi-month deployments producing consistent operational data may be solidly at TRL 9 even if it has not yet achieved large-scale commercial deployment. TRL 9 retires the technical risk; commercial scale-up is a business execution challenge.
*How to avoid*: Apply the operational proof test, not the commercial scale test. TRL 9 is about evidence of technical operation; BRL 8–9 is about evidence of commercial scale.

**Mistake 6 — Assigning TRL 9 to a startup that has recently deployed but has not yet collected sustained operational data**: A system that was deployed two weeks ago, regardless of how technically mature it is, has not yet produced the sustained operational evidence required for TRL 9. The time dimension is essential.
*How to avoid*: Apply the duration requirement. Require a minimum of six months of operational data (or a full operational cycle) before TRL 9 can be assigned. Flag recent deployments as "TRL 8 with TRL 9 pathway active."

---

#### 9.9.6 How to Reach the Next TRL

There is no TRL 10 in the TIDES framework (or any standard TRL framework). TRL 9 is the terminal level. Beyond TRL 9, the relevant metrics shift from technical readiness to commercial and operational performance:

**Post-TRL-9 growth activities:**
- [ ] Multi-site and multi-geography deployment scale-up
- [ ] Product line extension into adjacent use cases
- [ ] Platform development for third-party integrations
- [ ] Operational efficiency and unit economics improvement
- [ ] Development of next-generation technology capabilities (which may begin the TRL cycle again at a higher baseline)
- [ ] Technology transfer, licensing, or acquisition preparation

At TRL 9, the TIDES evaluation focus transitions from the Technology Pillar (TRL complete) to the Market Pillar (BRL progression), Team Pillar (scaling capability), and Financials Pillar (unit economics and growth trajectory).

---

#### 9.9.7 Confidence Indicators

**High Confidence (0.90–1.00)**: Multiple operational deployments documented with quantitative performance data, independent corroboration (customer testimonials, third-party audit), sustained performance over six or more months, and evidence of failure mode handling and recovery.

**Moderate Confidence (0.75–0.89)**: Two or more operational deployments documented but one is more thoroughly documented than others; performance data present but limited third-party corroboration; operational period is adequate but on the shorter end.

**Low Confidence (0.70–0.74)**: Two operational deployments described but documentation is sparse; operational performance data is aggregate rather than detailed; no independent corroboration. Minimum threshold for TRL 9 assignment.

**Acceptable Gaps**: No massive commercial scale yet; ongoing product improvement (at the feature/optimisation level, not the fundamental capability level); not yet profitable.

**Disqualifying Gaps**: Only one operational deployment; no independently verifiable operational performance data; technology still under fundamental capability development; significant active customer-reported defect backlog; operational performance data covers less than one operational cycle.

---

#### 9.9.8 Sector-Specific Notes

| Sector | TRL 9 Characteristics | Key Evidence Sources |
|---|---|---|
| **Software/SaaS** | Multiple paying customers using the system in production; stable product with defined release cadence; SLA compliance data available; customer renewal rate documented | Production uptime/SLA reports, customer case studies, NPS/CSAT data, ARR/MRR growth data, customer renewal documentation |
| **AI/ML** | Stable production model deployed across multiple customers/environments; model performance monitoring active; retraining cadence established and documented; bias and performance SLAs in place | Production model performance dashboards, fairness monitoring reports, customer performance SLA compliance data, post-deployment audit report |
| **Biotech/MedTech** | Approved product on market with post-market surveillance data; pharmacovigilance reports filed; real-world evidence (RWE) study initiated or complete; PMCF/PMSS ongoing | Post-market surveillance reports, pharmacovigilance submissions, RWE study data, PMCF report |
| **DeepTech/Hardware** | Units deployed in multiple operational sites; field reliability data (MTBF, failure rate) collected; maintenance and support operations established; second-generation design informed by field data | Field deployment records, MTBF/reliability reports, maintenance log data, customer operational testimonials |
| **AgriTech** | Multi-season, multi-region commercial deployment; agronomist and farmer satisfaction documented; yield or input efficiency improvement data from multiple commercial farms | Multi-season commercial trial data, farmer adoption and retention data, agronomist advisory board feedback |
| **ClimaTech** | System operating at commercial scale in multiple facilities; independently verified emissions reduction, energy production, or resource efficiency data; regulatory compliance records across operational sites | Independent verification reports, energy/emissions performance data, regulatory compliance certificates |
| **DefenceTech** | System in operational service; IOC (Initial Operational Capability) declared; operational unit feedback documented; logistics and maintenance support established | IOC declaration (may be classified); operational unit assessment; in-service support contract |

---

## Appendix A: TRL Evidence Checklist Master Reference

The following consolidated checklist provides a rapid-reference summary of evidence requirements across all TRL levels. This checklist is used by the AI evaluation agent as the primary input to the Evidence Quality Index computation.

| Evidence Item | TRL Levels Where Required | Must Have / Should Have | Independence Tier |
|---|---|---|---|
| Scientific literature citation identifying underlying principle | 1+ | Must Have at TRL 1 | External (published) |
| Founding team technical statement on observed principle | 1 | Must Have | Internal |
| Technology concept document (specific application description) | 2+ | Must Have at TRL 2 | Internal |
| Theoretical feasibility analysis (first-principles calculation) | 2+ | Must Have at TRL 2 | Internal |
| Technical unknowns / preliminary risk register | 2+ | Must Have at TRL 2 | Internal |
| Experimental report with founding-team-generated data | 3+ | Must Have at TRL 3 | Internal / Collaborative |
| Integration test report (assembled system, lab environment) | 4+ | Must Have at TRL 4 | Internal |
| Quantitative system-level performance data | 4+ | Must Have at TRL 4+ | Internal |
| Relevant environment access documentation | 5+ | Must Have at TRL 5 | External |
| Relevant environment validation report | 5+ | Must Have at TRL 5 | Internal / External |
| Gap analysis (lab vs. relevant environment) | 5+ | Must Have at TRL 5 | Internal |
| Demonstration event record with external observer attestation | 6+ | Must Have at TRL 6 | External |
| Operational trial report with named hosting organisation | 7+ | Must Have at TRL 7 | External |
| Operational performance data (from real operational environment) | 7+ | Must Have at TRL 7+ | External |
| End-user / operator feedback from operational deployment | 7+ | Should Have at TRL 7; Must Have at TRL 9 | External |
| Qualification test report against defined standards | 8+ | Must Have at TRL 8 | Internal / External |
| Regulatory clearance / third-party certification document | 8+ (regulated domains) | Must Have at TRL 8 (regulated) | Regulatory / Certification Body |
| Multi-deployment operational evidence (2+ distinct deployments) | 9 | Must Have at TRL 9 | External |
| Sustained operational performance data (≥6 months) | 9 | Must Have at TRL 9 | External |
| Independent post-deployment evaluation | 9 | Should Have at TRL 9 | Independent |

---

## Appendix B: Sector-Specific TRL Mapping Reference

This appendix provides consolidated cross-sector TRL mappings for rapid reference. Full sector-specific notes are provided within each TRL level definition in §9.

### B.1 Software/SaaS TRL Progression

| TRL | Software/SaaS Milestone | Key Technical Artefact |
|---|---|---|
| 1 | Novel algorithmic principle or computational approach identified | Literature review, algorithm description |
| 2 | System architecture concept formulated; data model defined | Architecture diagram, API specification draft |
| 3 | Core algorithm implemented and unit tested; basic function confirmed | Code, unit test results, benchmark data |
| 4 | End-to-end system integrated and tested with synthetic data | Integration test report, CI pipeline results |
| 5 | System validated with real/production-representative data at scale | Load test reports, real-data evaluation results |
| 6 | Live system demonstrated to external audience in realistic environment | Customer demo records, UAT results |
| 7 | System integrated into customer's production infrastructure; real users active | Production logs, active user data, customer integration records |
| 8 | SOC 2 / security audit / compliance certification complete; SLA defined | SOC 2 report, pen test report, compliance certificates |
| 9 | Multiple paying customers using system in production; SLA compliance documented | Customer case studies, uptime data, renewal records |

### B.2 AI/ML TRL Progression

| TRL | AI/ML Milestone | Key Technical Artefact |
|---|---|---|
| 1 | Novel ML technique or dataset type identified as principle | Literature review, hypothesis statement |
| 2 | Model architecture concept defined; dataset requirements specified; training pipeline designed | Model architecture description, dataset specification |
| 3 | Initial model trained on representative data subset; baseline metrics established | Training logs, validation curves, benchmark comparison |
| 4 | Full training pipeline operational; end-to-end inference tested on held-out test set | Model evaluation report, precision/recall curves |
| 5 | Model evaluated on real-world data; distribution shift and adversarial robustness tested | Real-data evaluation report, robustness analysis, bias audit |
| 6 | Model demonstrated processing live inputs to domain experts; independent evaluation conducted | Expert evaluation report, live demonstration records |
| 7 | Model deployed in production-representative pipeline; real-world inference monitored | Production pipeline logs, model monitoring dashboards |
| 8 | AI conformity assessment complete; model card finalised; monitoring pipeline in production | Conformity assessment docs, model card, bias audit report |
| 9 | Stable production model across multiple customers; performance SLAs met; drift monitoring active | Production dashboards, SLA compliance data, post-deployment audit |

### B.3 Biotech/MedTech TRL Progression

| TRL | Biotech/MedTech Milestone | Key Technical Artefact |
|---|---|---|
| 1 | Biological mechanism, drug target, or material property identified | Scientific literature, lab notebook |
| 2 | Mechanism of action hypothesis; target selection rationale; assay design concept | MOA document, target profile, assay protocol draft |
| 3 | In vitro/in silico confirmation of mechanism; initial efficacy signal observed | Lab reports, assay data, in silico results |
| 4 | Integrated assay or preclinical model confirming primary endpoint | Preclinical study report, formulation stability data |
| 5 | GLP-compliant animal study; clinical simulation laboratory study | GLP study report, clinical simulation results |
| 6 | Preclinical data presented to scientific advisory board or regulator | SAB meeting minutes, regulatory meeting records |
| 7 | Phase I/II clinical trial underway; regulatory pre-submission submitted | Clinical trial registration, IRB approval, clinical performance data |
| 8 | Regulatory approval received; GMP manufacturing established | Approval letter, GMP certificate, PMS plan |
| 9 | Product on market; post-market surveillance data collected; RWE study active | PMS reports, pharmacovigilance submissions, RWE data |

---

## Appendix C: Document Change Log

| Version | Date | Author | Change Description |
|---|---|---|---|
| 1.0.0 | 2026-06-23 | TIDES Platform Evaluation Authority | Inaugural release of TAES v1.0 Module 04 — TRL Assessment Standard. Covers TRL 1–9 with full sector-specific notes, evidence requirements, AI agent rules, gaming detection, and BRL integration. |

---

*End of Document: TAES v1.0 / Module 04 — Technology Readiness Level Assessment Standard*
*Classification: Internal Technical Standard*
*© TIDES Platform Evaluation Authority, 2026. All rights reserved. This document may not be reproduced or distributed without written authorisation from the TIDES Platform Evaluation Authority.*
