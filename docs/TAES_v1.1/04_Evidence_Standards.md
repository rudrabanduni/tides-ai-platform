# 04 — Evidence Standards

> **Document:** TAES v1.1 / Evidence Standards
> **Classification:** Internal Technical Standard
> **Version:** 1.1.0
> **Status:** Active
> **Parent Standard:** TAES v1.0 / 02_Evaluation_Principles.md (Principle P-EOO: Evidence Over Opinion)

---

## Introduction

Every score, finding, and recommendation produced by the TIDES platform must be traceable to specific, cited evidence. This document defines the official evidence framework governing what constitutes valid evidence, how evidence is classified by quality and freshness, how conflicting evidence is resolved, and what happens when evidence is absent.

The Evidence Standards defined here are binding on all AI evaluation agents, all human reviewers, and all automated scoring systems operating within the TIDES platform. An evaluation output that cannot cite evidence conforming to this standard is not a valid TAES evaluation.

Evidence is not the same as information. Information is any data point encountered during evaluation. Evidence is information that has been validated against source, assessed for quality, and formally cited in the evaluation record. The distinction is critical: an AI agent may encounter many data points in a startup's documents; only those that pass the evidence standards defined here may be used to support a score.

This document is organised as follows:
- **Section 1:** Evidence Taxonomy — the classification system
- **Section 2:** Evidence Quality Levels — from strong to inadmissible
- **Section 3:** Evidence Freshness — time-sensitivity rules
- **Section 4:** Evidence Weighting — how different evidence types contribute to confidence
- **Section 5:** Document Hierarchy — which source types take precedence
- **Section 6:** Conflict Resolution — what to do when evidence contradicts itself
- **Section 7:** Per-Domain Evidence Requirements — specific requirements for each evaluation domain
- **Section 8:** Evidence Gaps — what must happen when evidence is absent
- **Section 9:** Evidence Lifecycle — how evidence records are maintained over time

---

## Section 1: Evidence Taxonomy

Every piece of evidence used in a TAES evaluation must be classified along three axes: **Type**, **Source**, and **Form**.

### 1.1 Evidence Type

| Code | Evidence Type | Definition |
|------|--------------|------------|
| `EV-FIN` | Financial Evidence | Data relating to revenues, costs, burn rate, fundraising, cap table, unit economics |
| `EV-MKT` | Market Evidence | Data relating to market size, growth rates, customer segments, market trends |
| `EV-TEC` | Technical Evidence | Data relating to technology architecture, TRL, IP, prototypes, deployments |
| `EV-FDR` | Founder Evidence | Data relating to founder credentials, experience, track record, education |
| `EV-PRD` | Product Evidence | Data relating to product features, user feedback, roadmaps, usage metrics |
| `EV-LEG` | Legal Evidence | Data relating to incorporation, IP filings, regulatory approvals, compliance status |
| `EV-COM` | Commercial Evidence | Data relating to customers, contracts, pilots, letters of intent, partnerships |
| `EV-ESG` | ESG Evidence | Data relating to environmental impact, social metrics, governance structure |
| `EV-OPR` | Operational Evidence | Data relating to team structure, processes, infrastructure, delivery capability |
| `EV-EXT` | External Evidence | Third-party data not originating from the startup (news, analyst reports, regulatory databases) |

### 1.2 Evidence Source

| Code | Source Type | Definition | Trust Level |
|------|------------|------------|-------------|
| `SRC-PRM` | Primary Document | Directly submitted by the startup (pitch deck, financial statements, cap table) | Verified by examiner |
| `SRC-AUD` | Audited Document | Externally audited or certified document (audited accounts, legal certificates) | High |
| `SRC-REG` | Regulatory Filing | Publicly filed document (patent application, company registration, regulatory submission) | High |
| `SRC-CUS` | Customer Statement | Direct statement from a named customer (signed LOI, contract, case study, testimonial with contact) | Medium-High |
| `SRC-3PL` | Third-Party Report | Published reports from credible third parties (analyst firms, sector bodies, government data) | Medium |
| `SRC-PUB` | Academic Publication | Peer-reviewed research papers, conference proceedings | Medium |
| `SRC-NWS` | News and Media | Press coverage, interviews, press releases | Low |
| `SRC-INT` | Internal Claim | Unsubstantiated assertion in submitted documents | Lowest |

### 1.3 Evidence Form

| Form | Description |
|------|------------|
| **Quantitative** | Numerical data: revenue figures, team size, TRL score, market size estimates |
| **Qualitative** | Descriptive data: problem articulation, strategy description, technology explanation |
| **Documentary** | A specific document: a contract, patent, certificate, financial statement |
| **Testimonial** | A statement from a person: customer quote, reference letter, advisor endorsement |
| **Observational** | Something that can be directly verified: a working product, a live system, a deployed pilot |

---

## Section 2: Evidence Quality Levels

Every piece of evidence used in a TAES evaluation must be assigned one of five quality levels. The quality level directly affects the confidence score for the evaluation criterion it supports.

### 2.1 Quality Level Definitions

| Level | Name | Definition | Confidence Multiplier |
|-------|------|------------|----------------------|
| **Q5** | Authoritative | Externally verified, independently validated, or legally certified evidence. Examples: audited financial statements, granted patents, regulatory approval letters, signed multi-year contracts with named enterprises, published peer-reviewed research validating the technology. | 1.00 |
| **Q4** | Strong | Evidence from credible external sources or documents that can be independently verified. Examples: company registration certificates, signed LOIs with named customers, academic publications, referenced analyst reports with named firm and publication date, pilot agreements with verifiable counterparties. | 0.85 |
| **Q3** | Acceptable | Evidence that is plausible, internally consistent, and partially verifiable, but not independently confirmed. Examples: management accounts with clear methodology, customer testimonials without signed documents, team CVs with verifiable employment history, self-reported TRL with supporting technical description. | 0.65 |
| **Q2** | Weak | Evidence that is provided but difficult to verify, internally inconsistent, or lacking specific detail. Examples: vague market size claims without cited sources, revenue projections without stated assumptions, generic testimonials without identifying the customer, unsubstantiated technology claims. | 0.35 |
| **Q1** | Inadmissible | Evidence that cannot be evaluated, is anonymous, is self-contradictory, or appears fabricated. Evidence at Q1 must be flagged and must not be used to support a positive score. It may be cited as a red flag. Examples: financial figures that change between sections of the same document, patents claimed as granted that are not found in public databases, customer references that cannot be reached or verified. | 0.00 |

### 2.2 Quality Level Assignment Rules

1. Every evaluator (AI or human) must assign a quality level to every evidence item they cite.
2. If the quality level cannot be determined, the evidence is treated as Q2 (Weak) until further verification is obtained.
3. A score derived entirely from Q2 evidence carries a maximum confidence of 0.40, regardless of the volume of evidence.
4. A score that relies on any Q1 evidence must be flagged with a `EVIDENCE_QUALITY_FLAG` and brought to human reviewer attention.
5. When multiple evidence items at different quality levels support the same claim, the dominant quality level is the weighted average of all contributing items, not the highest or lowest.

### 2.3 Evidence Quality vs. Evidence Quantity

Volume of evidence does not substitute for quality. Ten Q2 evidence items for a revenue claim do not produce the same confidence as one Q5 item (an audited account). The confidence calculation must weight quality over quantity. The relationship is:

- Confidence ceiling from quality alone: determined by the highest quality level of primary evidence
- Confidence floor from quantity alone: no floor exists; additional weak evidence does not guarantee minimum confidence
- Practical rule: Q5 single item ≥ Q3 items × 10 in confidence contribution for the same claim

---

## Section 3: Evidence Freshness

Evidence has a shelf life. Data that was accurate when collected may be materially outdated by the time it is evaluated. TAES defines freshness rules for every major evidence category.

### 3.1 Freshness Tiers

| Tier | Freshness Window | Evidence Types | Staleness Effect |
|------|-----------------|----------------|-----------------|
| **F1 — Real-Time** | ≤ 30 days | Current MRR, active customer count, current team headcount, ongoing pilot status | Evidence older than 30 days is downgraded to F2 |
| **F2 — Current** | ≤ 6 months | Financial statements, customer contracts, fundraising records, TRL assessments, regulatory filings | Evidence older than 6 months is downgraded to F3 |
| **F3 — Recent** | ≤ 18 months | Market size reports, competitor analyses, academic publications, audit reports | Evidence older than 18 months is treated as background context only |
| **F4 — Historical** | > 18 months | Founder work history, prior exits, early research papers, original technology invention records | Not subject to freshness downgrade; evaluated for relevance only |

### 3.2 Freshness Downgrade Rules

- Evidence that falls outside its Freshness Tier window is not discarded; it is downgraded by one quality level for scoring purposes.
- Evidence in Tier F3 position that relates to a dynamic market (e.g., AI competitive landscape, crypto regulation) is downgraded by two quality levels, not one.
- Evidence in Tier F4 (historical) is exempt from quality downgrade but is explicitly labelled as historical in the evaluation record.
- The evaluation system must record the collection date of every evidence item. If the collection date is unknown, the evidence is classified as F3 regardless of stated claims.

### 3.3 Evaluation Timestamp

Every evaluation must record:
- The date of the evaluation
- The stated date of every evidence item used
- The freshness tier assigned to each evidence item at the time of evaluation

This allows re-evaluation of historical assessments to account for data that has since become stale.

---

## Section 4: Evidence Weighting

Not all evidence contributes equally to a score. The weight assigned to an evidence item is determined by the combination of its quality level and its freshness tier.

### 4.1 Weight Calculation Principle

Evidence Weight = Quality Multiplier × Freshness Factor × Relevance Factor

| Factor | Definition | Range |
|--------|-----------|-------|
| **Quality Multiplier** | Derived from the Quality Level (Q5=1.00, Q4=0.85, Q3=0.65, Q2=0.35, Q1=0.00) | 0.00–1.00 |
| **Freshness Factor** | F1=1.00, F2=0.90, F3=0.70, F4=0.50 | 0.50–1.00 |
| **Relevance Factor** | How directly this evidence relates to the specific evaluation criterion: Direct=1.00, Supporting=0.70, Tangential=0.40 | 0.40–1.00 |

### 4.2 Weight Application

- The weighted evidence pool for a criterion is the sum of weighted contributions from all evidence items for that criterion.
- The confidence score for the criterion is derived from the ratio of the actual weighted pool to the ideal weighted pool (what the pool would be if all required evidence were present at Q5/F1/Direct).
- This means that a rich body of weak evidence will always produce lower confidence than sparse but strong evidence.

### 4.3 Minimum Evidence Threshold

For every evaluation criterion, a minimum evidence threshold must be defined:
- **Full Assessment:** At least one Q4 or Q5 item is present; confidence ≥ 0.70
- **Provisional Assessment:** Only Q3 items are present; confidence between 0.40–0.69; must be labelled as provisional
- **Insufficient Evidence:** Only Q1/Q2 items, or no evidence; confidence < 0.40; the criterion score must not be presented as reliable; an evidence gap must be declared

---

## Section 5: Document Hierarchy

When a startup submits multiple documents, some documents take precedence over others for specific claim types. The document hierarchy defines which source type governs when sources conflict.

### 5.1 Document Precedence Table

| Rank | Document Type | Governs | Overrides |
|------|--------------|---------|-----------|
| 1 | Audited Financial Statements | All financial claims | All other financial documents |
| 1 | Granted Patent Certificate | Patent status claims | All other IP documents |
| 1 | Regulatory Approval Letter | Regulatory status claims | All other compliance claims |
| 2 | Signed Customer Contract | Customer commitment claims | LOIs, testimonials, verbal references |
| 2 | Certificate of Incorporation | Legal status claims | Self-stated legal descriptions |
| 3 | Management Accounts | Financial trajectory claims | Projections, pitch deck financials |
| 3 | Signed Letter of Intent | Commercial interest claims | Unsigned LOIs, verbal commitments |
| 4 | Pitch Deck | Narrative overview only | No factual precedence; narrative only |
| 4 | Founder CV/LinkedIn | Founder background claims | Self-stated claims without verification |
| 5 | Application Form | Self-stated overview | All other document types |

### 5.2 Pitch Deck Handling

The pitch deck is one of the most commonly submitted documents. It must be treated with specific care:

- **The pitch deck is not an evidence document.** It is a narrative presentation whose purpose is persuasion, not proof.
- Every claim in the pitch deck must be corroborated by a higher-rank document before it is used as evidence.
- Market size figures, revenue claims, customer counts, and TRL claims appearing only in a pitch deck and nowhere else are classified as Q2 (Weak) evidence at best.
- A pitch deck that is internally consistent with higher-rank documents improves confidence marginally. A pitch deck that contradicts higher-rank documents is a red flag.

### 5.3 Application Form Handling

- The application form captures self-stated information at the time of application.
- Application form data is the starting point for evaluation, not the ending point.
- Every material claim in the application form should be corroborated by submitted documents before being weighted above Q2.

---

## Section 6: Conflict Resolution

Conflicting evidence occurs when two or more evidence items support opposite or incompatible claims about the same fact. Conflict resolution is a formal process in TAES.

### 6.1 Conflict Classification

| Conflict Type | Definition | Example |
|--------------|-----------|---------|
| **Numerical Conflict** | Two sources provide different numerical values for the same metric | Application form states 50 customers; pitch deck states 120 customers |
| **Status Conflict** | Two sources report different status for a binary state | Patent claimed as granted in deck; not found in public database |
| **Temporal Conflict** | Two sources describe the same fact at different points in time as if it is the current state | 2022 audited accounts show profit; 2024 management accounts show loss; deck claims profitability |
| **Narrative Conflict** | Two sources describe the same event or situation in materially different terms | Founder CV describes a previous exit; reference check contradicts this |
| **Scope Conflict** | Two sources agree on a fact but disagree on its scope or significance | Market size described as $1B in deck; independently sourced report shows $200M |

### 6.2 Conflict Resolution Protocol

**Step 1 — Identify and Document**
Every conflict must be identified, classified, and recorded in the evaluation record with both conflicting sources cited.

**Step 2 — Apply Document Hierarchy**
Apply the document precedence table from Section 5. The higher-ranked document's version of the fact governs.

**Step 3 — Apply Freshness Rules**
If both documents are at the same rank, the more recent document governs, provided the newer document is within its Freshness Tier.

**Step 4 — Apply Quality Rules**
If documents are of the same rank and similar recency, the higher quality level document governs.

**Step 5 — Flag for Human Review**
If the conflict cannot be resolved by Steps 2–4, or if the conflict is material (affects the pillar score by more than 1.0 point), the conflict must be escalated to a human reviewer. The AI evaluation must not silently choose one version of the fact; it must declare the conflict and the uncertainty it creates.

**Step 6 — Record the Resolution**
The resolution decision — including which source was selected as governing and the reason — must be recorded in the evaluation evidence record.

### 6.3 Material Conflict Threshold

A conflict is considered material if:
- It would change any pillar score by ≥ 1.0 point
- It concerns a legally significant claim (patent status, regulatory approval, funding received)
- It concerns a fundamental business characteristic (is the startup generating revenue or not?)
- The conflicting claims cannot both be true simultaneously

Material conflicts must always result in a human review flag, regardless of whether document hierarchy suggests a resolution.

### 6.4 Startup's Right of Response

When a material conflict is identified, the platform should, where operationally possible, provide the startup the opportunity to submit a clarifying document before the final evaluation is concluded. The clarifying document is added to the evidence record with the date of submission and classified at Q3 until it can be assessed.

---

## Section 7: Per-Domain Evidence Requirements

For each major evaluation domain, the following defines what constitutes acceptable, weak, strong, and missing evidence.

---

### 7.1 Founder Domain

**Strong Evidence (Q4–Q5)**
- Professional references from previous employers or investors, with named and contactable referees
- Documented exits: acquisition records, public announcements of previous company sales
- Published work: patents in the founder's name, academic publications, press coverage of specific achievements
- Named board or advisory roles at verifiable organisations
- Evidence of domain expertise: regulatory licences, professional certifications, named projects

**Acceptable Evidence (Q3)**
- LinkedIn profile consistent with submitted CV (verifiable employment history)
- Named participation in previous funded projects with verifiable grant references
- Video demonstrations or presentations demonstrating subject matter expertise
- References that can be followed up but have not yet been verified

**Weak Evidence (Q2)**
- Unverified CV with no corroborating documents
- Generic testimonials ("great founder, highly recommended") without specific achievements cited
- Self-stated expertise without any corroborating external reference

**Missing Evidence**
- No CV, no LinkedIn, no verifiable history for any founder
- Founders listed by name only with no biographical information
- All claimed achievements are unverifiable

**Red Flags (triggers Q1 handling)**
- CV claims contradict each other (dates overlap impossibly, claimed positions not found)
- Previous company claims cannot be verified in any public database
- Academic credentials claimed cannot be verified with named institution

---

### 7.2 Financial Domain

**Strong Evidence (Q4–Q5)**
- Audited financial statements for the most recent 1–2 financial years
- Bank statements for the most recent 3–6 months
- Signed investment agreements or term sheets with verifiable investor names
- Signed revenue contracts with named customers and stated values
- Cap table signed by company secretary or legal counsel

**Acceptable Evidence (Q3)**
- Management accounts prepared by an accountant (even if unaudited)
- Payment platform exports (e.g., Stripe dashboard exports) showing revenue history
- Investor communications (term sheet summaries, closing announcements)
- Payroll records or salary data demonstrating team operating costs

**Weak Evidence (Q2)**
- Financial projections without stated assumptions or methodology
- Revenue claims in pitch deck without supporting transaction records
- Verbal confirmation of funding without documentation
- Financial model spreadsheets without actuals section

**Missing Evidence**
- No financial documents of any kind
- Projections only; no historical data
- Claims of revenue with no documentation

**Red Flags**
- Financial figures in the application form do not match those in the pitch deck
- Revenue claimed with no corresponding customers identified
- Burn rate implied by team size and claimed salaries is inconsistent with stated runway
- Cap table allocations sum to more than 100%

---

### 7.3 Technology Domain

**Strong Evidence (Q4–Q5)**
- Working, accessible product or prototype with verifiable functionality
- Third-party technical audit or security assessment report
- Academic or laboratory validation of core technology claims
- Regulatory submission or approval demonstrating technical compliance
- Deployment records in a real operational environment (not just development)

**Acceptable Evidence (Q3)**
- Technical documentation (architecture diagrams, system design documents) with sufficient detail to assess feasibility
- GitHub or equivalent repository with meaningful activity and code (evaluator can assess technology direction without reading every line)
- Demo recording showing core functionality
- Patent application (filed, not granted) describing the technical approach

**Weak Evidence (Q2)**
- High-level technology description without architectural detail
- Demo that shows only UI without demonstrating underlying technical capability
- Technology claims that rest entirely on a third party's platform (e.g., "we use GPT-4 therefore we have AI")

**Missing Evidence**
- No technical documentation of any kind
- Technology described only in business terms with no technical specificity

**Red Flags**
- Technology claims that are physically impossible given the stated team size and timeline
- Core technology described as proprietary but no IP protection attempted or explained
- Demo environment that appears pre-scripted rather than functional

---

### 7.4 Market Domain

**Strong Evidence (Q4–Q5)**
- Market size data from named, credible research firms (Gartner, IDC, McKinsey, etc.) with publication date
- Government statistical data on market size or growth
- Independent market study commissioned for the startup (if properly conducted)
- Paying customer data demonstrating actual demand at current pricing

**Acceptable Evidence (Q3)**
- Market size estimates from credible industry associations with stated methodology
- Bottom-up market sizing using documented customer segments and willingness-to-pay data
- Survey data with stated sample size, methodology, and margin of error

**Weak Evidence (Q2)**
- Market size figures cited without source
- TAM estimates that apply a percentage to a global figure without justification
- Market growth claims based on a single news article

**Missing Evidence**
- No market size data of any kind
- Market described only in qualitative terms with no quantification attempt

**Red Flags**
- TAM, SAM, and SOM all presented as the same number
- Market size claim is orders of magnitude larger than sector benchmarks suggest
- No credible path from stated SOM to stated SAM

---

### 7.5 Intellectual Property Domain

**Strong Evidence (Q4–Q5)**
- Granted patent with verifiable patent number, jurisdiction, and expiry date
- Trade secret protection agreement (NDA, employment agreement with IP assignment clause)
- Copyright registration certificate
- Freedom to Operate legal opinion from qualified IP counsel

**Acceptable Evidence (Q3)**
- Patent application (published, with application number verifiable in national patent office database)
- Provisional patent application with filing reference
- IP strategy document prepared by qualified IP counsel
- Trademark registration (granted)

**Weak Evidence (Q2)**
- Claim of patent protection without application number
- IP described as protected by "trade secret" without any documented protection mechanism
- Trademark application pending without filing reference

**Missing Evidence**
- No IP discussion of any kind
- No evidence that the startup has considered IP protection

**Red Flags**
- Patent claimed as granted but not found in named patent office database
- Core technology appears to replicate published prior art without acknowledgement
- IP ownership is ambiguous: team members who developed the technology before founding the company

---

### 7.6 Commercial Evidence Domain

**Strong Evidence (Q4–Q5)**
- Signed contracts with named customers, stated values, and contract durations
- Bank statement entries corresponding to stated revenue transactions
- Active SaaS subscriptions verifiable through platform records
- Signed enterprise pilot agreements with defined success criteria and expansion terms

**Acceptable Evidence (Q3)**
- Signed Letters of Intent with named organisations and stated intent to purchase
- Named reference customers willing to be contacted
- Documented trial agreements or proof-of-concept installations
- Purchase orders received (without completed delivery)

**Weak Evidence (Q2)**
- Verbal customer commitments without documentation
- Unnamed customer references ("a large bank in Mumbai")
- Pipeline described in terms of deals without named organisations

**Missing Evidence**
- No commercial engagement of any kind beyond internal testing
- All claims of customer interest are described as "in discussions"

**Red Flags**
- Customers named who cannot be contacted or do not recognise the relationship
- Revenue claimed but no corresponding customers identified
- A single customer representing >80% of revenue (concentration risk)

---

## Section 8: Evidence Gaps

An evidence gap occurs when the expected evidence for an evaluation criterion is absent. Evidence gaps are not the same as weak scores — they are declarations of epistemic uncertainty.

### 8.1 Evidence Gap Protocol

When an evaluation criterion lacks the minimum required evidence threshold:

1. **Declare the gap** — The evaluation record must explicitly state that evidence is insufficient for this criterion. The declaration must name the criterion, the evidence type that is missing, and the reason the gap exists (not submitted, not available at this stage, commercially sensitive).

2. **Assign provisional scoring** — The criterion receives a provisional score based on whatever weak evidence is available, with a confidence of ≤ 0.35. The score must be labelled `PROVISIONAL - EVIDENCE GAP`.

3. **Do not assume** — The absence of evidence is not evidence of absence. A startup that has not yet filed a patent may be planning to do so. An AI agent must not infer the worst-case interpretation from a gap unless supporting evidence specifically suggests a problem.

4. **Do not assume the best** — Equally, the absence of evidence is not permission to assume the best case. If a startup claims revenue but provides no documentation, the claim is treated as unsubstantiated, not confirmed.

5. **Request resolution** — The evaluation record must include a formal evidence request: a specific list of documents or data points that would resolve the gap. This request is included in the startup's feedback report.

### 8.2 Evidence Gap Severity Classification

| Severity | Condition | Effect |
|----------|-----------|--------|
| **Critical Gap** | Required primary evidence is entirely absent for a primary evaluation pillar | The pillar score is marked `INSUFFICIENT EVIDENCE`; the overall confidence score is capped at 0.50 |
| **Major Gap** | Primary evidence is absent but secondary evidence allows a partial assessment | The criterion score is labelled `PROVISIONAL`; confidence is capped at 0.40 for the affected criterion |
| **Minor Gap** | Supporting (not primary) evidence is absent | Score is delivered with a note; confidence is reduced by 0.10 |

---

## Section 9: Evidence Lifecycle

Evidence records are not static. They must be maintained, updated, and archived according to defined rules.

### 9.1 Evidence Record Creation
Every evidence item used in a TAES evaluation must be recorded with: source identifier, document title, source type code, quality level, freshness tier, collection date, evaluation date, the specific claim it supports, and the evaluator who assigned it.

### 9.2 Evidence Record Updates
When a startup is re-evaluated, new evidence items are added to the record. Existing evidence items are not deleted; they are marked with the date they were superseded (if newer evidence replaces them) or confirmed (if newer evaluation corroborates them).

### 9.3 Evidence Immutability
Once an evaluation is finalised, the evidence record for that evaluation is immutable. No evidence item may be added, removed, or changed after finalisation without creating a new evaluation cycle. This ensures that past evaluations can always be audited and reproduced.

### 9.4 Evidence Retention
Evidence records must be retained for a minimum of seven years from the date of the evaluation. For startups that subsequently receive public funding or regulatory approvals, evidence records must be retained for the full duration of any compliance obligation.

### 9.5 Evidence Privacy
Evidence items that contain personal data (founder personal addresses, individual financial details, personal health information) must be handled in accordance with applicable data protection law. The evaluation system must not expose personal data from evidence records to any party who does not have a legitimate, documented need for access.

---

## Implementation Priority

This document should be the **second** document implemented after the Evaluation Taxonomy, because:

1. The taxonomy defines what must be evaluated.
2. The evidence standards define what can be used to evaluate it.

No scoring system, rubric, or AI agent can be validly designed until these two layers are established. Every confidence score in every pillar depends on the evidence quality and freshness rules defined here.

---

*This document is authoritative for all evidence handling decisions within the TIDES platform. Where implementation behaviour conflicts with these standards, this document governs.*
