> **Document:** TAES v1.0 / Evaluation Principles
> **Classification:** Internal Technical Standard
> **Version:** 1.0.0
> **Status:** Ratified
> **Effective Date:** 2026-06-23
> **Maintained By:** TIDES Platform Architecture Council
> **Review Cycle:** Annual or upon major platform revision
> **Supersedes:** None (inaugural version)

---

# TAES v1.0 — Evaluation Principles

## Document Reference: `TAES-v1.0-02`

---

## Preamble: Purpose and Binding Scope

This document defines the **eleven foundational evaluation principles** of the TIDES AI Evaluation Standard (TAES v1.0). These principles constitute the normative core of the TIDES platform: every automated evaluation pipeline, every human review workflow, every scoring algorithm, every audit log, and every output report produced by or on behalf of the TIDES platform **must conform to all principles defined herein**.

These principles are not aspirational guidelines. They are binding technical and operational requirements. Deviation from any principle — whether by a platform operator, a configured AI agent, a third-party integration, or a human reviewer acting within the TIDES system — constitutes a standards non-conformance and must be logged, escalated, and remediated in accordance with TAES governance procedures.

### Who These Principles Bind

| Actor | Binding Scope |
|---|---|
| TIDES Platform Operators | All platform configurations, deployments, and customisations |
| AI Evaluation Agents | All agent prompts, scoring logic, evidence retrieval, and output formatting |
| Human Reviewers | All override decisions, annotation activities, and escalation actions |
| Third-Party Integrations | All data connectors, API consumers, and embedded evaluators |
| IIT Incubators and Partner Institutions | All use of TIDES outputs in funding, admission, or support decisions |
| Government and Regulatory Bodies | All use of TIDES data for policy evaluation or compliance verification |

These principles are designed to be **sector-agnostic** in their formulation but **sector-sensitive** in their application. They apply equally to deep-tech, agri-tech, fintech, health-tech, and social-enterprise startups, among others.

---

## Principle Index

| # | Principle Name | Short Code |
|---|---|---|
| 1 | Evidence Over Opinion | `P-EOO` |
| 2 | Explainable AI | `P-XAI` |
| 3 | Human-in-the-Loop | `P-HIL` |
| 4 | Confidence Scoring | `P-CON` |
| 5 | Fairness | `P-FAI` |
| 6 | Transparency | `P-TRN` |
| 7 | No Hallucinations | `P-NOH` |
| 8 | AI Recommends, Humans Decide | `P-ARH` |
| 9 | Consistency | `P-CST` |
| 10 | Repeatability | `P-RPT` |
| 11 | Sector Awareness | `P-SEC` |

---

## Principle 1 — Evidence Over Opinion `[P-EOO]`

### Statement

Every score, rating, flag, recommendation, or qualitative assessment produced by the TIDES platform must be grounded in **traceable, verifiable, and cited evidence**. The platform does not permit subjective impressions, speculative assertions, or unevidenced commentary to substitute for factual basis.

### What Counts as Evidence

Evidence, in the TIDES context, is any artifact, dataset, documented interaction, or verifiable record that directly supports a specific evaluative claim. Acceptable evidence categories include:

- **Primary documents**: pitch decks, financial statements, cap tables, patent filings, regulatory submissions, incorporation certificates, product datasheets, and pilot agreements.
- **Secondary sources**: cited market research from named firms (e.g., NASSCOM, IDC, Gartner), government datasets, academic publications with DOI, and audited third-party assessments.
- **Operational data**: product usage metrics provided by the startup with a clear provenance declaration, verified traction data from App Store or SaaS analytics dashboards with screenshots or API exports.
- **Interview records**: structured mentor or evaluator interview transcripts tagged with date, participant, and topic code.
- **Public signals**: media coverage from named outlets, regulatory filings in government portals, published court judgments, or patent grant notices.

Each evidence item must be referenced using the TAES Evidence Citation Format: `[E-<type>-<sequence>]`, e.g., `[E-DOC-007]` for a financial document, `[E-PUB-003]` for a publication.

### What Does Not Count as Evidence

The following must never be treated as evidence in TIDES evaluations:

- Verbal claims made by the startup that are unsupported by any document or third-party corroboration.
- Agent-generated paraphrasing of claims made elsewhere in the evaluation that has not been independently verified.
- Analogies to other startups (e.g., "similar to how Company X scaled in 2019") without a documented source.
- Inferred assumptions about market conditions, team capabilities, or technology readiness not tied to a specific cited artifact.

### Handling Evidence Absence

When evidence is absent for a required criterion, the TIDES agent must:

1. Flag the criterion as **Evidence Gap** (`EG`) in the evaluation record.
2. Assign a **null score** or the sector-appropriate default floor score for that criterion, as defined in the scoring rubric.
3. Populate the `evidence_gap_note` field with a plain-language description of what evidence was missing and what would be needed to resolve the gap.
4. Reduce the overall confidence score for that dimension in accordance with Principle 4 (Confidence Scoring).

An evidence gap must never be silently absorbed into a score or treated as neutral. It must always be visible in the output report.

---

## Principle 2 — Explainable AI `[P-XAI]`

### Statement

Every score produced by the TIDES platform must be fully decomposable. No score — whether at the criterion level, dimension level, or overall level — may be opaque. Any reviewer, startup representative, or auditor must be able to trace any score to its contributing sub-scores, and each sub-score to the specific evidence items and rubric rules that generated it.

### Decomposability Requirements

Scores in TIDES follow a strict hierarchical composition model:

```
Overall Score
└── Dimension Score (e.g., Team, Market, Product)
    └── Criterion Score (e.g., Founder Domain Expertise)
        └── Sub-Criterion Score (e.g., Years of relevant experience)
            └── Evidence Citation (e.g., [E-DOC-002]: LinkedIn profile)
```

Each level of this hierarchy must be explicitly populated in the evaluation record. No level may be computed without the level beneath it being populated first. Aggregation formulas — including any weighted averages, normalisation transforms, or penalty adjustments — must be stored in the evaluation record alongside the scores they produce.

### Traceability Requirements

Traceability requires that, for each score node in the hierarchy, the following fields are populated:

- `score_value`: the numeric or ordinal score assigned.
- `score_basis`: the rubric rule or rubric band that maps the evidence to this score.
- `evidence_refs`: a list of evidence citation codes that were considered.
- `evidence_used`: the subset of cited evidence that was actually weighted in the score.
- `agent_reasoning`: a natural-language summary (50–150 words) of how the agent interpreted the evidence in light of the rubric.
- `confidence_value`: the confidence level for this score (see Principle 4).

### Explainability at the Sub-Criterion Level

Sub-criterion explainability is the most granular level at which TIDES enforces explanation. Each sub-criterion must have a dedicated narrative block that:

1. Names the specific rubric band the score falls into (e.g., "Band 3: Demonstrated but not differentiated").
2. Quotes or references the specific evidence that determined band placement.
3. Identifies any conflicting evidence and explains how it was weighted.
4. States what additional evidence would have moved the score to the next higher band.

This level of granularity is not optional. It is what enables the Human-in-the-Loop reviewer to exercise informed override authority (Principle 3) and what enables post-evaluation audits (Principle 6).

---

## Principle 3 — Human-in-the-Loop `[P-HIL]`

### Statement

The TIDES platform is an AI-assisted evaluation system, not an autonomous decision-making system. Every consequential evaluation output — defined as any output that directly informs a funding recommendation, cohort admission decision, grant eligibility determination, or regulatory assessment — must pass through a designated Human Reviewer before it becomes a platform decision.

### The Role of Human Reviewers

Human Reviewers in the TIDES system perform the following functions:

- **Validation**: confirming that the AI agent has correctly interpreted the available evidence and applied the correct rubric rules.
- **Contextual enrichment**: adding domain knowledge, market understanding, or sector nuance that the AI agent may not have adequately weighted.
- **Conflict resolution**: resolving cases where evidence is ambiguous, contradictory, or where the startup's context falls outside standard rubric parameters.
- **Override execution**: formally changing one or more scores when the reviewer determines the AI assessment is materially incorrect, and documenting the reason for each override.
- **Final sign-off**: confirming the evaluation output as fit for use by the consuming institution.

### Override Authority

Human Reviewers hold full override authority over any AI-generated score. An override is valid when:

1. The reviewer provides a written override justification of at least 80 words.
2. The override justification references at least one of: a specific evidence item, a rubric rule, or a documented contextual factor not reflected in the AI assessment.
3. The override is logged in the evaluation audit trail with the reviewer's ID, timestamp, and the pre- and post-override score values.

Override authority does not extend to the evaluation methodology itself. Reviewers may not change the weighting scheme, rubric band definitions, or scoring formula of a published standard version. Such changes must go through the TAES governance process.

### Formal Separation of AI Recommendation and Human Decision

The platform enforces this separation architecturally. The AI evaluation pipeline produces an **Evaluation Recommendation Package (ERP)**, which is a structured, read-only artifact. The Human Reviewer then produces a **Reviewed Evaluation Record (RER)**, which is a separate artifact that references the ERP and records all acceptances, modifications, and overrides. The RER — not the ERP — is the authoritative output that flows downstream to consuming institutions.

---

## Principle 4 — Confidence Scoring `[P-CON]`

### Statement

Every score produced by the TIDES platform must be accompanied by a **Confidence Score** that quantifies how much trust should be placed in that score given the quality, quantity, and consistency of the evidence on which it is based. Confidence is not a measure of how good or bad the startup is; it is a measure of how well-evidenced the evaluation is.

### How Confidence Is Calculated

Confidence for each score node is computed as a weighted composite of four factors:

| Factor | Description | Max Weight |
|---|---|---|
| Evidence Quantity | Number of independent evidence items available | 30% |
| Evidence Quality | Primacy, recency, and source credibility of evidence | 30% |
| Evidence Consistency | Degree to which evidence items agree with each other | 25% |
| Rubric Coverage | Proportion of sub-criteria for which evidence was found | 15% |

Each factor is scored on a 0–1 normalised scale. The composite confidence score is expressed as a percentage rounded to the nearest integer.

### Factors That Reduce Confidence

The following conditions apply automatic confidence penalties:

- **Missing evidence** (`EG` flag): -15 points per flagged sub-criterion.
- **Conflicting signals**: when two or more evidence items directly contradict each other without a documented resolution, -10 points per unresolved conflict.
- **Low data quality**: evidence items older than 36 months, from unverifiable sources, or submitted without provenance declaration incur -5 points each.
- **Single-source dependency**: when a criterion relies on a single evidence item with no corroboration, -8 points.

These penalties are additive up to a floor of 5%, which is the minimum reportable confidence for a non-null score.

### Confidence Levels and Their Meanings

| Confidence Range | Level Label | Operational Meaning |
|---|---|---|
| 80–100% | HIGH | Score is well-evidenced; Human Reviewer may accept without detailed re-examination |
| 55–79% | MODERATE | Score is reasonably evidenced; Human Reviewer should confirm key sub-criteria |
| 30–54% | LOW | Score has significant evidence gaps; Human Reviewer must conduct targeted due diligence |
| 5–29% | VERY LOW | Score is speculative; this dimension should be deferred pending additional evidence |

### Confidence Propagation

Confidence propagates upward through the score hierarchy using a **minimum-bounded weighted average**. The confidence of a Dimension Score equals the confidence-weighted average of its Criterion Scores, subject to the rule that the Dimension Confidence cannot exceed the lowest Criterion Confidence by more than 10 points. This ensures that one very low-confidence criterion cannot be masked by high-confidence siblings.

The Overall Confidence is the confidence-weighted average of Dimension Confidences, subject to the same bounding rule. It is reported prominently in the Evaluation Recommendation Package header.

---

## Principle 5 — Fairness `[P-FAI]`

### Statement

The TIDES evaluation platform must produce scores that are fair across sectors, stages, geographies, and startup demographic profiles. Fairness means that differences in scores between startups reflect genuine differences in evaluated characteristics — not artefacts of sector conventions, stage expectations, data availability biases, or demographic assumptions embedded in the rubric.

### Cross-Sector Fairness

Different sectors have structurally different characteristics that are not indicators of quality. For example:

- A deep-tech startup may have near-zero revenue at Series A but possess multiple granted patents and published peer-reviewed research.
- An agri-tech startup operating in rural markets may have low digital traction but high ground-level pilot adoption documented through partner NGO records.
- A fintech startup may be unable to share detailed user data due to RBI compliance requirements.

The TIDES platform implements **sector-relative scoring bands** for criteria where sector context materially changes the interpretation of evidence. Sector-relative bands are defined in the TAES Sector Profiles (document `TAES-v1.0-08`) and must be applied by the evaluation agent before scoring. An evaluator that applies a generic scoring band to a sector with documented alternate norms is in violation of this principle.

### Cross-Stage Fairness

Startups at different stages — idea, prototype, pilot, early revenue, growth — must not be compared using absolute metrics. The evaluation framework applies **stage-normalised scoring**, where the rubric band for each criterion is anchored to what is expected at that stage, not what is expected in the abstract.

### Penalisation Avoidance

The platform explicitly prohibits the following penalisation patterns:

- Penalising a startup for lacking audited financials at the idea or prototype stage.
- Penalising a startup in a regulated sector (health, fintech, defence) for slow go-to-market due to compliance requirements.
- Penalising a first-time founder for lacking a prior exit, unless the criterion explicitly measures prior exits.

### Diversity Considerations

The TIDES platform does not collect or score on the basis of founder demographics (gender, caste, religion, disability status) as scoring inputs. However, the platform logs demographic metadata (where voluntarily provided) for post-hoc bias auditing purposes, to detect whether the scoring model produces systematically different outputs for demographic subgroups with otherwise equivalent profiles.

---

## Principle 6 — Transparency `[P-TRN]`

### Statement

Every TIDES evaluation must be conducted in a manner that is fully auditable after the fact. The platform must produce a durable, structured audit record for every evaluation, and that record must be accessible — in whole or in relevant part — to authorised stakeholders including the evaluated startup, the reviewing institution, and regulatory bodies with oversight authority.

### What Must Be Logged

The following must be logged for every evaluation without exception:

| Log Category | Required Fields |
|---|---|
| Evaluation Metadata | Startup ID, evaluation ID, standard version, evaluation date, operator ID |
| Agent Configuration | Agent version, prompt version, model identifier, temperature settings |
| Evidence Ingestion | For each evidence item: source, ingestion timestamp, format, hash/checksum |
| Scoring Trace | For each score node: score value, rubric rule applied, evidence refs, reasoning summary |
| Confidence Computation | For each score node: all four confidence factors and composite value |
| Human Review Actions | Reviewer ID, review timestamp, accepted/overridden scores, override justifications |
| Output Generation | Output format, delivery timestamp, recipient record |

All logs must be stored in a tamper-evident format. Deletion or modification of evaluation logs after the evaluation is complete is a platform integrity violation.

### What Stakeholders Can Inspect

**Startups** may request access to:
- Their own evaluation's dimension-level and criterion-level scores.
- The evidence items cited in their evaluation.
- The confidence scores for each dimension.
- Any override decisions made by Human Reviewers.
- The rubric band definitions used to score them.

**Reviewing Institutions** may access:
- All of the above, plus the full agent reasoning trace.

**Regulatory Bodies** with appropriate authority may access:
- The complete audit record, including agent configuration and log hashes.

Transparency does not require disclosure of proprietary rubric weights or internal platform architecture details unless mandated by specific regulatory instruments.

---

## Principle 7 — No Hallucinations `[P-NOH]`

### Statement

TIDES AI agents must never fabricate, invent, or confabulate evidence, assessments, citations, or facts. This is an absolute prohibition with no exceptions. Any agent output that cannot be traced to a specific ingested evidence item or an explicitly documented inference chain is a hallucination and constitutes a platform integrity failure.

### Defining Hallucination in the TIDES Context

In the TIDES context, hallucination is defined as any agent output that:

- Asserts the existence of a document, dataset, fact, or market figure that was not present in the ingested evidence package.
- Cites a publication, report, or source that was not provided to or retrieved by the agent.
- Paraphrases a startup's claims in a way that materially changes their meaning and presents the paraphrase as independently verified.
- Generates a score based on assumed characteristics not present in the evidence (e.g., assuming a startup has a founding team of three when only one founder is documented).

### Handling Evidence Gaps Without Hallucination

When an agent encounters an evidence gap, the correct behaviour is to:

1. State the gap explicitly using the `evidence_gap_note` mechanism (see Principle 1).
2. Assign the appropriate floor score or null score for that criterion.
3. Apply the relevant confidence penalty.
4. In the reasoning summary, note that "no evidence was available to assess this criterion" — not offer a speculative assessment.

### The Difference Between Inference and Hallucination

Inference from weak evidence is permitted, provided it is explicitly labelled as inference and the evidence basis is cited. For example: "Based on the single mention of a pilot with Apollo Hospitals in the pitch deck [E-DOC-004], the agent infers limited but present clinical validation. This is a weak inference due to single-source dependency (confidence penalty applied)." This is not hallucination — it is transparent, labelled inference from a real evidence item.

Hallucination would be: asserting Apollo Hospitals as a confirmed partner without a citation, or generating a market size figure not present in any ingested document. Agents must be configured and tested to detect and refuse such outputs. Hallucination detection hooks must be integrated at the agent output validation layer before any score is written to the evaluation record.

---

## Principle 8 — AI Recommends, Humans Decide `[P-ARH]`

### Statement

The formal boundary between AI output and human output in the TIDES platform is absolute and non-negotiable. The AI evaluation pipeline produces **recommendations**. Human Reviewers produce **decisions**. These are distinct artifacts with distinct authorities, distinct audit trails, and distinct legal and institutional implications.

### The Formal Boundary

| Artifact | Produced By | Authoritative For |
|---|---|---|
| Evaluation Recommendation Package (ERP) | AI Agent Pipeline | Informing the Human Reviewer |
| Reviewed Evaluation Record (RER) | Human Reviewer | Informing the consuming institution |
| Institutional Decision Record (IDR) | Consuming Institution | Grant, admission, or investment decision |

No downstream system, institution, or process may treat an ERP as equivalent to an RER. The ERP is explicitly marked as a draft recommendation in its header metadata. Systems that consume TIDES output must be configured to reject ERPs that have not been reviewed and countersigned as RERs.

### Accountability Separation

Accountability in the TIDES system is allocated as follows:

- The **platform operator** is accountable for the correctness of the agent configuration, rubric implementation, and evidence ingestion pipeline.
- The **Human Reviewer** is accountable for the accuracy and fairness of the final RER.
- The **consuming institution** is accountable for how it uses the RER in its own decision-making process.

No party may transfer accountability to another. In particular, a consuming institution may not cite the AI evaluation as the sole basis for a consequential decision affecting a startup. The existence of a Human Reviewer step is a platform requirement precisely to ensure that a human professional has exercised independent judgment.

### Legal and Institutional Implications

In jurisdictions where algorithmic decision-making in consequential contexts (funding, credit, admission) is regulated — including under the EU AI Act, India's proposed AI governance frameworks, and sector-specific RBI or SEBI guidelines — the TAES `P-ARH` principle provides the structural compliance mechanism. The RER is the instrument of record for legal purposes. The ERP has the status of a working document.

---

## Principle 9 — Consistency `[P-CST]`

### Statement

Given identical input data, an identical evidence package, and the same published standard version, two independent TIDES evaluations of the same startup must produce scores that are **materially the same**. Material consistency is defined as: no criterion score diverging by more than 0.5 points on the TIDES 0–5 scale, and no overall score diverging by more than 2 percentage points.

### Achieving Consistency

Consistency is achieved through the following mechanisms:

1. **Rubric precision**: Each scoring band is defined with explicit, objectively applicable criteria, not vague descriptors. Band boundaries are tested against a calibration corpus before each standard version is published.
2. **Prompt locking**: The agent prompt and system instructions are version-locked per standard version. Prompt changes that materially affect scoring behaviour require a minor version increment of the standard.
3. **Model pinning**: The underlying language model version used for scoring is pinned per standard version. Model updates that affect scoring require a version transition protocol.
4. **Calibration testing**: Before publishing a standard version, the TIDES Architecture Council must demonstrate that the evaluation system produces consistent scores across at least 20 calibration cases, with inter-rater agreement (Cohen's κ) of ≥ 0.75.

### Version Control of the Standard

The TAES standard uses semantic versioning: `MAJOR.MINOR.PATCH`. Evaluations conducted under different MAJOR versions are not directly comparable. Evaluations under the same MAJOR version but different MINOR versions may be compared with documented caveats. The version used for each evaluation is permanently recorded in the evaluation metadata.

### Consistency Across Operators

When multiple operators deploy the TIDES platform independently, consistency requires that:
- All operators use the same published rubric and scoring bands.
- All operators use the same standard version for a given evaluation cycle.
- Cross-operator calibration exercises are conducted at least annually.

Operators may not customise rubric weights or band definitions without creating a documented **Operator Extension** that is registered with the TIDES Architecture Council and disclosed to all evaluation consumers.

---

## Principle 10 — Repeatability `[P-RPT]`

### Statement

A TIDES evaluation is **repeatable** if, given the same frozen input set and the same standard version, any authorised party with access to the evaluation system can re-run the evaluation and obtain a materially identical output. Repeatability is the property that enables independent audit, dispute resolution, and longitudinal tracking of a startup across evaluation cycles.

### Formal Definition of a Repeatable Evaluation

An evaluation `E` is repeatable if and only if:

1. The **Evidence Package** is frozen: all ingested documents and data files are stored with cryptographic hashes in the evaluation record, and are available for retrieval at audit time.
2. The **Standard Version** is pinned: the exact rubric, weight set, and scoring algorithm version are recorded in the evaluation metadata.
3. The **Agent Configuration** is pinned: the exact prompt version, model version, and inference parameters (temperature, top-p, context window) are recorded.
4. The **Execution Environment** is documented: the runtime version, dependency versions, and infrastructure configuration used for the evaluation are logged.

If any of these four elements changes, the re-run is considered a **new evaluation**, not a repeat of the original. The original evaluation record must not be overwritten; a new evaluation record must be created with a reference to the original.

### What Must Be Frozen

| Input Category | Freezing Mechanism |
|---|---|
| Startup evidence documents | SHA-256 hash stored in evaluation record |
| Standard version | Semantic version tag locked at evaluation creation |
| Agent prompt | Git commit hash of the prompt repository |
| Model version | Model identifier including provider version string |
| Rubric weight file | SHA-256 hash stored in evaluation record |

### Audit and Replication Requirements

Regulatory bodies, accreditation authorities, or dispute-resolution panels may request a full replication of a past evaluation. The platform must support this by:

- Retaining frozen evidence packages for a minimum of 5 years after the evaluation date.
- Maintaining archived versions of all standard components (rubrics, prompts, weight files) indefinitely.
- Providing a documented replication procedure in the TAES Operations Manual (`TAES-v1.0-11`).

---

## Principle 11 — Sector Awareness `[P-SEC]`

### Statement

Sector context is a **first-class input** to every TIDES evaluation. The platform does not evaluate startups in an abstract, sector-neutral space. Instead, it explicitly configures the evaluation pipeline with a Sector Profile that changes the interpretation of metrics, the applicable rubric bands, the expected evidence types, and the cross-sector comparison rules.

### Why Sector Context Is Essential

The same raw metric can have radically different implications depending on sector:

| Metric | Deep-Tech Sector Interpretation | Consumer App Sector Interpretation |
|---|---|---|
| Zero revenue at Month 18 | Expected; IP and research milestones are primary | Concerning; product-market fit should be evidenced |
| 5 enterprise pilot agreements | Strong traction signal | Weak signal compared to thousands of users expected |
| 3-year regulatory approval timeline | Normal (FDA, CDSCO, SEBI) | Red flag for a product with no regulatory requirement |
| 80% gross margin | Below average for SaaS | Strong for a hardware-intensive product |

Without sector awareness, the platform would systematically disadvantage startups whose sector characteristics differ from the implicit baseline embedded in generic rubrics.

### How Sector Changes the Interpretation of Metrics

The TIDES Sector Profile for each recognised sector defines:

1. **Expected evidence types**: what documents and data are normally available at each stage in this sector.
2. **Band recalibrations**: which rubric bands are shifted or redefined to reflect sector norms.
3. **Stage-sector matrix**: the combined effect of stage and sector on expectations for each dimension.
4. **Sector risk factors**: known regulatory, supply-chain, or market-structure risks that should inform the evaluation but not automatically penalise the startup.

Sector Profiles are published as appendices to TAES v1.0 and are reviewed annually. Recognised sectors include: Deep-Tech / Hard-Tech, Agri-Tech, Health-Tech, Fintech / Insurtech, EdTech, CleanTech / Climate-Tech, Consumer Internet, Enterprise SaaS, and Social Enterprise.

### Cross-Sector Comparison Rules

TIDES evaluations produce **sector-relative scores** by default. When a consuming institution wishes to compare startups across sectors (e.g., for a sector-agnostic funding cohort), the following rules apply:

1. Cross-sector comparison must use the **Normalised Overall Score (NOS)**, which is the sector-relative score adjusted to a common baseline using the cross-sector normalisation table.
2. Cross-sector comparison reports must prominently label each startup's sector and stage.
3. The evaluation report must include a **Cross-Sector Comparability Warning** if the compared startups span sectors with normalisation uncertainty above 15%.
4. Human Reviewers performing cross-sector shortlisting must have completed TAES cross-sector adjudication training.

---

## Compliance Checklist: Principles by Enforcing Document

The following table maps each principle to the TAES documents and platform components responsible for its operational enforcement.

| Principle | Short Code | Primary Document | Supporting Documents | Platform Component |
|---|---|---|---|---|
| Evidence Over Opinion | `P-EOO` | `TAES-v1.0-03` (Evidence Standards) | `TAES-v1.0-05` (Scoring Rubric) | Evidence Ingestion Module, Citation Validator |
| Explainable AI | `P-XAI` | `TAES-v1.0-04` (Score Architecture) | `TAES-v1.0-06` (Output Format) | Score Decomposition Engine, Reasoning Trace Logger |
| Human-in-the-Loop | `P-HIL` | `TAES-v1.0-07` (Review Workflow) | `TAES-v1.0-09` (Governance) | Human Review Portal, Override Engine |
| Confidence Scoring | `P-CON` | `TAES-v1.0-04` (Score Architecture) | `TAES-v1.0-05` (Scoring Rubric) | Confidence Computation Module |
| Fairness | `P-FAI` | `TAES-v1.0-08` (Sector Profiles) | `TAES-v1.0-05` (Scoring Rubric) | Sector Profile Loader, Bias Audit Logger |
| Transparency | `P-TRN` | `TAES-v1.0-10` (Audit Standard) | `TAES-v1.0-11` (Operations Manual) | Audit Log Service, Stakeholder Access Portal |
| No Hallucinations | `P-NOH` | `TAES-v1.0-04` (Score Architecture) | `TAES-v1.0-03` (Evidence Standards) | Hallucination Detection Hook, Output Validator |
| AI Recommends, Humans Decide | `P-ARH` | `TAES-v1.0-07` (Review Workflow) | `TAES-v1.0-09` (Governance) | ERP/RER Separation Layer, Countersignature Module |
| Consistency | `P-CST` | `TAES-v1.0-01` (Standard Specification) | `TAES-v1.0-05` (Scoring Rubric) | Calibration Test Suite, Version Registry |
| Repeatability | `P-RPT` | `TAES-v1.0-10` (Audit Standard) | `TAES-v1.0-11` (Operations Manual) | Evidence Freeze Service, Execution Provenance Logger |
| Sector Awareness | `P-SEC` | `TAES-v1.0-08` (Sector Profiles) | `TAES-v1.0-05` (Scoring Rubric) | Sector Profile Loader, Cross-Sector Normalisation Engine |

---

## Technical Enforcement Roadmap

As the TIDES platform matures, these principles will be enforced progressively through the following technical mechanisms:

### Phase 1 — Baseline Enforcement (v1.0, Current)

- **Structural enforcement**: the evaluation record schema enforces the presence of required fields (`evidence_refs`, `agent_reasoning`, `confidence_value`, `evidence_gap_note`) at the data model level. Records that do not populate mandatory fields cannot be committed to the evaluation store.
- **Prompt-level guardrails**: AI agent system prompts contain explicit instructions for each principle, including prohibition statements for hallucination, mandatory confidence computation steps, and evidence citation format requirements.
- **Human review gate**: the ERP-to-RER workflow is enforced architecturally — no ERP can be delivered to a consuming institution without a countersigned RER in the pipeline.
- **Version locking**: evaluation records store a cryptographic reference to the standard version, prompt version, and model version used.

### Phase 2 — Automated Validation (v1.1, Planned)

- **Post-generation hallucination detection**: a secondary validation agent will cross-check all evidence citations in the ERP against the ingested evidence package, flagging any citation that does not correspond to an ingested artifact.
- **Confidence audit**: an automated audit pass will verify that confidence scores are consistent with the evidence gap flags and conflict flags present in the record.
- **Cross-operator calibration dashboard**: a platform-level dashboard will aggregate consistency metrics across operators and flag statistically significant divergences for Architecture Council review.
- **Fairness monitoring**: the platform will run automated sector-fairness checks on batches of evaluations to detect rubric drift that disproportionately affects specific sectors or stages.

### Phase 3 — Institutional Auditability (v2.0, Planned)

- **Immutable audit ledger**: evaluation audit logs will be written to a tamper-evident distributed ledger, enabling independent third-party audit without platform operator involvement.
- **Replication API**: consuming institutions with regulatory oversight authority will be able to trigger evaluation replications via an authenticated API, using frozen evidence packages and archived agent configurations.
- **Bias certification**: the platform will undergo annual third-party bias audits for cross-sector and cross-stage fairness, with results published in the TIDES Annual Standards Report.
- **Regulatory API compliance modules**: jurisdiction-specific compliance modules will map TAES audit records to the required formats of the EU AI Act, India AI governance frameworks, and other applicable instruments.

---

## Document Control

| Field | Value |
|---|---|
| Document ID | `TAES-v1.0-02` |
| Title | Evaluation Principles |
| Version | 1.0.0 |
| Status | Ratified |
| Effective Date | 2026-06-23 |
| Author | TIDES Platform Architecture Council |
| Review Date | 2027-06-23 |
| Predecessor | None |
| Related Documents | TAES-v1.0-01, TAES-v1.0-03, TAES-v1.0-04, TAES-v1.0-05, TAES-v1.0-07, TAES-v1.0-08, TAES-v1.0-09, TAES-v1.0-10, TAES-v1.0-11 |

---

*End of Document: TAES v1.0 / Evaluation Principles (`TAES-v1.0-02`)*
