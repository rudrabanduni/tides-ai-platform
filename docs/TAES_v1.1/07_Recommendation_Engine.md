# TAES v1.1 — Document 07: Recommendation Engine Specification

> **Document:** TAES v1.1 / Recommendation Engine
> **Classification:** Internal Technical Standard
> **Version:** 1.1.0
> **Status:** Active
> **Effective Date:** 2026-06-24
> **Document Owner:** TIDES Platform Standards Committee
> **Review Cycle:** Biannual

---

## Table of Contents

- [Introduction](#introduction)
- [Section 1: Recommendation Categories](#section-1-recommendation-categories)
- [Section 2: Recommendation Attributes](#section-2-recommendation-attributes)
- [Section 3: Prioritisation Logic](#section-3-prioritisation-logic)
- [Section 4: Recommendation Generation by Pillar](#section-4-recommendation-generation-by-pillar)
- [Section 5: Recommendation Roadmap Output Format](#section-5-recommendation-roadmap-output-format)
- [Section 6: Recommendation Tracking and Lifecycle](#section-6-recommendation-tracking-and-lifecycle)
- [Section 7: Recommendation Quality Standards](#section-7-recommendation-quality-standards)
- [Worked Example: Recommendation Roadmap](#worked-example-recommendation-roadmap)
- [Agent Interaction Model](#agent-interaction-model)

---

## Introduction

### The Philosophical Shift: From Generic Feedback to Structured Recommendations

The dominant failure mode of evaluation systems — whether applied to startups, research projects, or technology ventures — is not the absence of feedback. It is the presence of feedback that is too abstract to act upon. Statements such as "improve your product-market fit," "strengthen your team," or "develop a clearer go-to-market strategy" have been the currency of evaluation panels for decades. They describe the destination without describing the route. They identify the gap without specifying the bridge. They satisfy the form of advice while failing entirely at the function of advice.

The TIDES AI Evaluation Standard (TAES) Recommendation Engine is built on a foundational rejection of this model. Its governing premise is that every startup evaluated by the TIDES platform deserves not a verdict but a workplan — a structured, sequenced, effort-estimated, impact-projected set of actions that converts the evaluation's findings into a navigable path forward. The Recommendation Engine is the intelligence layer that performs this conversion. It is the mechanism through which measurement becomes guidance.

This document specifies the complete architecture, logic, data model, and output format of the TIDES Recommendation Engine. It defines how recommendations are generated, structured, prioritised, delivered, tracked, and updated across evaluation cycles. It is a design standard, not an operational manual. It governs what the engine must produce, not how it is implemented.

### Why Recommendations Must Be Tied to Evidence, Not Opinions

Recommendations that are not grounded in evidence are indistinguishable from editorial opinion. An evaluator who tells a founder to "build a stronger advisory board" may be correct — but without citing the specific evidence that led to that conclusion, the recommendation carries no epistemic weight and generates no compulsive reason to act.

The TIDES Recommendation Engine mandates that every recommendation cite its evidence basis explicitly. Evidence is drawn from the evaluation record: from scored sub-criteria, from document analysis outputs, from quantitative indicators supplied by the startup, from comparable market data, and from pillar-level score distributions. A recommendation exists because data supports it. Its priority is calibrated to the magnitude of the gap the data reveals. Its timeline is proportional to the complexity of the change required. None of these parameters are subjective assignments — they are computed outputs of the evaluation logic applied to the evidence record.

This evidence-binding serves three purposes. First, it makes recommendations auditable: any stakeholder can trace a recommendation backward to the data that generated it. Second, it makes recommendations defensible: when founders push back, evaluators can point to the evidence rather than defending a judgment. Third, it makes recommendations updatable: when the evidence changes (i.e., when the startup progresses), the recommendation changes with it — or is retired because it has been satisfied.

### How Recommendations Differ from Evaluation Findings

The TAES evaluation process produces two distinct classes of output: findings and recommendations. These are related but fundamentally different in purpose, structure, and epistemic status.

**Findings** describe the current state. They are descriptive, evidence-backed, and retrospective in orientation. A finding states: "The founding team lacks a dedicated Chief Technology Officer, and the current technical lead has no prior experience scaling a software platform beyond five hundred concurrent users." A finding is complete when it accurately characterises what is true at the time of evaluation.

**Recommendations** prescribe the path forward. They are normative, action-oriented, and prospective in orientation. A recommendation states: "Recruit a CTO-level technical leader with demonstrated experience in distributed systems architecture within the next ninety days, prioritising candidates with prior Series A-stage scale-up experience in the target verticals." A recommendation is complete when it specifies what must be done, by when, to what standard, and with what expected outcome.

The relationship between a finding and its corresponding recommendation is one of logical necessity: the finding establishes the gap; the recommendation specifies how to close it. Not all findings generate recommendations — findings that confirm strength or adequacy are recorded but do not produce action items. Only findings that identify deficiencies, gaps, risks, or opportunities generate recommendations.

### The Recommendation Output Model

The TIDES Recommendation Engine does not produce a "Recommendations Section" appended to an evaluation report. It produces a structured Recommendation Roadmap — a standalone, machine-readable, human-navigable action plan that is generated from the evaluation data, stands independently of the narrative report, and persists across evaluation cycles as a living document.

The Recommendation Roadmap contains:

1. **A Priority Stack**: all recommendations sorted by computed priority score, with the top five displayed prominently as the startup's immediate action agenda.
2. **A Timeline View**: recommendations distributed across a 0–18 month horizon, showing when each action should begin and when it should be completed.
3. **A Pillar View**: recommendations grouped by the evaluation pillar they address, allowing pillar owners to identify and own their domain's improvement agenda.
4. **An Implementation Tracker**: a record of which recommendations from prior evaluation cycles have been implemented, partially implemented, or remain pending.
5. **An Impact Projection**: for each implemented recommendation, the projected improvement in pillar score, enabling startups to model their trajectory toward target scores.

The Roadmap is not a report section. It is an operational artefact that governs the startup's improvement agenda between evaluation cycles.

### How Recommendations Are Prioritised

The Recommendation Engine applies a multi-dimensional prioritisation model. No single factor determines priority. Instead, four dimensions are evaluated for each recommendation and combined into a Priority Score:

1. **Impact**: How much improvement in evaluation score — and by extension, in the underlying capability the score measures — is expected if this recommendation is implemented? Impact is expressed as an expected pillar score improvement range (e.g., +0.8 to +1.2 points on a 10-point scale).

2. **Effort**: How much resource — time, capital, personnel, and organisational capacity — does implementation require? Effort is categorised as Minimal, Moderate, Significant, or Intensive.

3. **Urgency**: Is there a time-sensitive condition (such as an upcoming fundraise, a regulatory deadline, a partnership negotiation, or a competitive window) that makes this recommendation more pressing than its intrinsic score impact alone would indicate?

4. **Dependency Order**: Does this recommendation unblock other recommendations? If Recommendation A must be completed before Recommendations B, C, and D can begin, then A carries compounded priority beyond its individual impact.

The combination of these four dimensions produces a Priority Score that determines the recommendation's rank within the Roadmap. The full prioritisation logic is specified in Section 3.

### How Recommendations Are Updated Across Evaluation Cycles

Recommendations are not static. They are living records within the TIDES platform's evaluation memory. Across evaluation cycles, the following update processes occur:

- **Implementation verification**: In each subsequent evaluation cycle, the evaluator team assesses whether previously issued recommendations have been implemented. Evidence of implementation is sought in the submitted documentation and in observed score changes.
- **Status transitions**: Recommendations transition through defined status states (Pending, In Progress, Implemented, Superseded, Withdrawn) based on what the new evaluation finds.
- **Carry-forward**: Unimplemented recommendations from prior cycles are carried forward with updated priority scores that reflect elapsed time, changed conditions, and any partial progress observed.
- **Supersession**: When a new evaluation cycle produces a superior or more specific recommendation that replaces a prior one, the prior recommendation is marked Superseded rather than deleted, preserving the evaluation history.
- **Retirement**: When a recommendation has been implemented — verified through evidence — it is marked Implemented and its expected score impact is reconciled against the actual score change observed.

The full lifecycle model is specified in Section 6.

---

## Section 1: Recommendation Categories

The TIDES Recommendation Engine organises all generated recommendations into ten named categories. Categories serve as organisational containers that help startups, evaluators, and platform users navigate the recommendation set by timeline, domain, and purpose. Every recommendation belongs to exactly one primary category, selected based on the nature of the action required, the timeline for completion, and the domain the action addresses.

---

### Category 1: Quick Wins

**Definition and Scope**

Quick Wins are recommendations that can be implemented by the startup within thirty calendar days of the evaluation report delivery, require no significant capital outlay, no new hiring, and no regulatory or third-party approval processes. They are characterised by high or significant expected impact relative to the effort required. Quick Wins typically involve correcting documentation deficiencies, completing partially done work, clarifying public-facing materials, or activating capabilities the startup already possesses but has not yet deployed.

The category label "Quick Win" does not imply trivial impact. Many Quick Wins have outsized score effects precisely because they close obvious, evaluable gaps that evaluators can immediately observe and reward. A startup that lacks a data room, for example, may receive a Quick Win recommendation to construct one — a task achievable in two to three weeks that improves scores across the Financial, Business Model, and IP pillars simultaneously.

**Types of Actions**

- Completing and publishing documentation that is partially written or exists internally but has not been submitted (e.g., a product roadmap, a cap table summary, a terms of service document)
- Registering for publicly visible credentialing, certification, or listing programmes (e.g., DPIIT startup registration, MSME certification, government scheme registration)
- Correcting factual inconsistencies between documents submitted to the evaluation platform
- Making existing IP filings visible and documented in the submission record
- Publishing a privacy policy, terms of service, or regulatory disclosure that is legally required but absent from the startup's public presence
- Updating a pitch deck to include elements identified as missing in the evaluation (e.g., a competitive landscape slide, a team background slide)
- Establishing basic financial reporting practices where none exist (e.g., creating a chart of accounts, reconciling bank statements)
- Activating already-contracted customer relationships that are not yet documented as reference customers

**Generation Logic**

Quick Win recommendations are generated when the evaluation identifies a scored sub-criterion with a score below 5 out of 10 where the primary cause of the low score is an absence of documentation or visibility — not an absence of the underlying capability. The distinction is critical: if the startup has the capability but has not documented or demonstrated it, the fix is documentation. If the startup lacks the capability, the recommendation falls into a medium or long-term category.

**Prioritisation Within Category**

Within the Quick Wins category, recommendations are ordered by expected score improvement per hour of effort invested. Recommendations that improve scores across multiple pillars simultaneously are ranked above single-pillar improvements of equal effort.

**Typical Timeline**

0 to 30 days from report delivery.

---

### Category 2: Medium-Term Improvements

**Definition and Scope**

Medium-Term Improvements are structural enhancements to the startup's capabilities, processes, or market position that require between one and six months to implement. They typically involve developing something that does not yet exist (rather than documenting something that does), building internal processes, completing product development milestones, or establishing recurring operational functions. Medium-Term Improvements generally require moderate to significant effort and may involve both internal resources and external expertise.

**Types of Actions**

- Completing a specific product feature or module identified as missing in the product evaluation
- Building and documenting a formal customer discovery or user research process
- Developing a financial model with defined assumptions, scenario analysis, and eighteen-month cash flow projections
- Establishing a formal IP management policy and conducting a freedom-to-operate analysis
- Completing an industry-specific certification process (e.g., ISO 27001 information security certification, BIS certification for hardware products)
- Building a structured sales pipeline with CRM tooling and defined stage criteria
- Developing and launching a content-led or partnership-led market development programme
- Completing a pilot or proof-of-concept deployment with a named anchor customer
- Establishing a board of directors or advisory board with documented governance procedures

**Generation Logic**

Medium-Term Improvement recommendations are generated when the evaluation identifies scored sub-criteria with scores between 3 and 6 where the gap represents a genuine capability deficiency that requires months to address. They are also generated when a Quick Win has been identified as a precondition for a larger medium-term change.

**Prioritisation Within Category**

Within the Medium-Term category, recommendations are sorted by their dependency relationships first (foundational actions ranked above dependent actions), then by expected score improvement, then by estimated cost.

**Typical Timeline**

1 to 6 months from report delivery.

---

### Category 3: Long-Term Improvements

**Definition and Scope**

Long-Term Improvements are transformational changes to the startup's position, capabilities, or market standing that require sustained effort over six to eighteen months. They involve strategic pivots, significant product development cycles, international market entry, platform-level scaling, or deep regulatory clearance processes. Long-Term Improvements typically generate the highest absolute score improvements but require the most resource commitment.

**Types of Actions**

- Completing a full product development cycle to reach a defined TRL milestone (e.g., advancing from TRL 4 to TRL 6)
- Establishing international market presence with in-country operations, partnerships, or licensing arrangements
- Achieving sector-specific regulatory approval (e.g., CDSCO approval for medical devices, SEBI registration for fintech products, MeitY certification for government-facing software)
- Building a complete enterprise sales function with defined territory coverage, channel partnerships, and documented reference accounts
- Completing a strategic technology integration or migration (e.g., migrating from a monolithic architecture to a microservices model to enable enterprise-grade scalability)
- Developing a second product line or adjacent service offering that diversifies revenue concentration
- Achieving and maintaining profitability in a defined market segment
- Completing an R&D programme that validates a core technical hypothesis underpinning the product's differentiation

**Generation Logic**

Long-Term Improvement recommendations are generated when the evaluation identifies pillar scores below 4 out of 10 that reflect deep structural or capability gaps, or when a pattern of multiple low sub-criterion scores within a single pillar indicates systemic weakness requiring sustained strategic intervention.

**Prioritisation Within Category**

Within the Long-Term category, recommendations are sorted by strategic importance — defined as the degree to which the recommendation's completion enables the startup to access its next significant value-creation milestone (next funding round, commercial contract threshold, regulatory clearance, or international expansion).

**Typical Timeline**

6 to 18 months from report delivery.

---

### Category 4: Investment Readiness Tasks

**Definition and Scope**

Investment Readiness Tasks are a specialised subset of recommendations focused specifically on improving the startup's appeal and credibility to institutional investors. They are distinct from general improvement recommendations because they are calibrated to investor expectations — the specific documents, metrics, structures, and narratives that professional investors use to make allocation decisions. These recommendations are generated regardless of the pillar that surfaces the underlying gap; their unifying characteristic is that their primary beneficiary is investor due diligence.

**Types of Actions**

- Constructing or completing a virtual data room with the standard investor due diligence package (cap table, audited financials or management accounts, shareholder agreements, IP ownership certificates, customer contracts, key employee agreements, product roadmap, technical architecture document)
- Developing a formal investor pitch deck compliant with institutional investor expectations (problem, solution, market size, traction, team, financials, ask, use of funds)
- Establishing a cap table management tool with fully documented equity history, including all convertible instruments, ESOPs, and prior investment tranches
- Completing a company valuation exercise using a recognised methodology (DCF, comparables, or market-based approach) with documented assumptions
- Establishing a board structure with at least one independent director and documented board governance procedures
- Preparing a formal Term Sheet negotiation position document for the anticipated funding round
- Resolving any identified deficiencies in corporate governance documents (shareholder agreements, articles of association, consent thresholds)
- Completing and registering any IP that represents a core value driver for the business

**Generation Logic**

Investment Readiness Task recommendations are generated when the platform's Investment Readiness Score (a composite derived from Financial, IP, Business Model, and Founder pillar scores) falls below 6.5 out of 10, or when specific high-salience investor due diligence elements are identified as absent from the submitted documentation.

**Prioritisation Within Category**

Investment Readiness Tasks are sorted by their estimated impact on the Investment Readiness Score, with legal and governance deficiencies (which can constitute deal-breakers) ranked above documentation completeness tasks.

**Typical Timeline**

Predominantly 0 to 60 days, with some structural governance tasks extending to 3 months.

---

### Category 5: TRL Advancement Tasks

**Definition and Scope**

TRL Advancement Tasks are recommendations that directly advance the startup's Technology Readiness Level, as assessed against the TAES Technology Pillar rubric. These recommendations are development-programme tasks: they specify what engineering, validation, testing, integration, or demonstration milestones the startup must reach to move from its current TRL to the next. TRL Advancement is tracked separately because it is the primary measure of technology de-risking used by government grant programmes, defence and public sector procurement, and technology-focused investors.

**Types of Actions**

- Completing a laboratory demonstration of the core technology function under controlled conditions (TRL 3 → TRL 4 transition)
- Completing a component- or subsystem-level validation in a simulated operational environment (TRL 4 → TRL 5 transition)
- Completing a system prototype demonstration in a relevant environment (TRL 5 → TRL 6 transition)
- Completing an operational prototype demonstration in an operational environment with a pilot customer (TRL 6 → TRL 7 transition)
- Completing a pre-commercial production unit demonstration and customer acceptance testing (TRL 7 → TRL 8 transition)
- Achieving full commercial deployment with operational evidence and documented performance metrics (TRL 8 → TRL 9 transition)
- Producing and submitting technical documentation that supports TRL verification (test reports, validation certificates, performance benchmarks, customer acceptance letters)
- Engaging an independent technical evaluator to conduct a third-party TRL assessment

**Generation Logic**

TRL Advancement Task recommendations are generated when the Technology Pillar score for the TRL sub-criterion falls below 7 out of 10, or when the startup's declared TRL is inconsistent with the technical evidence submitted (a common finding where founders self-assess higher TRL than the evidence supports).

**Prioritisation Within Category**

TRL Advancement Tasks are sorted by the gap between the current verified TRL and the TRL threshold required for the startup's next target milestone (e.g., government programme eligibility, enterprise pilot, or strategic investor interest).

**Typical Timeline**

3 to 18 months, depending on the TRL gap and the complexity of the technology domain.

---

### Category 6: Fundraising Tasks

**Definition and Scope**

Fundraising Tasks are action-oriented recommendations that prepare the startup to execute a specific funding round — not to improve investor appeal in the abstract, but to complete the mechanics, legal structure, documentation, and outreach preparation required to close a round. These recommendations are generated when the evaluation indicates the startup is within 3 to 9 months of a fundraising event or has explicitly declared one.

**Types of Actions**

- Defining the specific funding round parameters: target raise amount, instrument type (equity, SAFE, CCD, convertible note), pre-money valuation anchor, minimum ticket size, and target investor profile
- Completing the ESOP scheme setup and option pool allocation prior to round (standard pre-round requirement for institutional investors)
- Preparing a financial model with a defined use-of-funds breakdown showing deployment of round proceeds against milestones
- Developing a list of targeted investors with documented rationale for strategic fit
- Preparing and rehearsing the investor presentation narrative with a defined Q&A preparation document
- Completing all necessary regulatory filings for foreign investment acceptance (FEMA compliance for FDI, RBI prior approval if applicable)
- Engaging a transactional legal advisor to review term sheets and shareholder agreement templates
- Completing a pre-round cap table clean-up to resolve any ambiguous or disputed equity positions

**Generation Logic**

Fundraising Task recommendations are generated when the startup is in an active or declared pre-fundraise state, when the Financial Pillar sub-criterion for funding strategy scores below 6, or when the Investment Readiness Score falls in the 5.0–7.0 range — indicating a startup that is close to fundable but requires specific mechanical preparation to close.

**Prioritisation Within Category**

Fundraising Tasks are sorted by their position in the fundraise sequencing logic: regulatory and governance tasks that must be completed before investor engagement rank first; investor documentation and outreach preparation tasks rank second; negotiation support tasks rank third.

**Typical Timeline**

0 to 90 days, with a strong front-loading of tasks in the first 30 days for startups within 3 months of a planned round close.

---

### Category 7: IP Tasks

**Definition and Scope**

IP Tasks encompass all recommendations related to intellectual property identification, protection, management, and strategy. This includes patent prosecution, trade secret formalisation, trademark registration, copyright documentation, freedom-to-operate analysis, and the development of a formal IP strategy document. IP Tasks are generated from the IP Pillar evaluation but may also be triggered by findings in the Technology or Business Model pillars where IP is a core component of the startup's defensibility or revenue model.

**Types of Actions**

- Filing a provisional patent application for a core invention not yet under patent protection
- Conducting a freedom-to-operate (FTO) search and analysis for the primary product or technology
- Completing a trademark registration for the brand name, logo, and key product names in the primary market jurisdictions
- Developing and implementing a trade secret policy, including employee and contractor NDAs, access controls, and documentation of confidential know-how
- Completing a copyright registration for proprietary software, content, or creative works that constitute a commercial asset
- Conducting an IP audit to identify all protectable IP assets and produce a formal IP register
- Developing a formal IP licensing strategy for IP assets that have monetisation potential independent of the core business
- Resolving any identified IP ownership ambiguity (e.g., work-for-hire agreements with former contractors, ownership of pre-company IP contributed by founders)
- Engaging a patent attorney for a claims review of any granted or pending patents

**Generation Logic**

IP Task recommendations are generated when the IP Pillar score falls below 7 out of 10, or when specific high-risk IP conditions are identified: no filed IP protection for a technology-dependent business, no trademark protection in a consumer-facing brand business, or IP ownership documentation that is absent or ambiguous.

**Prioritisation Within Category**

IP Tasks with legal risk implications (ownership ambiguity, FTO gaps in core markets) are ranked Critical or High. Filing and prosecution tasks for unprotected core IP are ranked High. Monitoring and strategy tasks are ranked Medium.

**Typical Timeline**

IP filing tasks: 0 to 60 days. FTO analysis: 30 to 60 days. Patent prosecution (to grant): 18 to 36 months (ongoing, not a short-term completion task, but the filing must occur within the recommended window).

---

### Category 8: Hiring Tasks

**Definition and Scope**

Hiring Tasks are recommendations that address specific, identified gaps in the startup's team composition, capability coverage, or organisational structure. Unlike general talent acquisition, Hiring Tasks in the TIDES context are generated from specific findings: a missing function (no CTO, no CFO, no Head of Sales), an identified capability gap (founding team lacks regulatory expertise in a regulated industry), or a concentration risk (all technical knowledge concentrated in one individual who is not a co-founder).

**Types of Actions**

- Recruiting a specific named role identified as missing from the founding team (e.g., CTO, VP Sales, Head of Regulatory Affairs)
- Engaging an industry-specific advisor or board member to fill an expertise gap the team cannot address through hiring
- Hiring a part-time or fractional resource to fill a function that requires expertise but does not yet justify a full-time hire (e.g., fractional CFO, part-time legal counsel)
- Establishing a formal advisory board with documented engagement terms and equity or cash compensation
- Developing and deploying a talent acquisition pipeline for technical roles required for the next product development phase
- Establishing a formal employee onboarding and knowledge management process to reduce key-person concentration risk
- Restructuring reporting lines and role definitions to resolve identified organisational governance gaps

**Generation Logic**

Hiring Task recommendations are generated when the Founder Pillar sub-criterion for team completeness scores below 6, or when specific domain expertise gaps are identified in the Market, Technology, or Financial pillar evaluations that are attributable to missing team roles rather than to structural market uncertainty.

**Prioritisation Within Category**

Hiring Tasks for roles that are blocking other evaluation improvements (e.g., no CTO in a deep tech company) are ranked Critical. Hiring Tasks for roles that improve investor confidence (C-suite completion, independent board member) are ranked High. Advisory board construction tasks are ranked Medium.

**Typical Timeline**

Fractional or advisory engagement: 30 to 60 days. Full-time executive hire: 60 to 120 days. Technical team build-out: 3 to 6 months.

---

### Category 9: Go-To-Market Tasks

**Definition and Scope**

Go-To-Market (GTM) Tasks are recommendations that improve the startup's commercial traction, channel effectiveness, sales pipeline quality, pricing clarity, and customer acquisition repeatability. These recommendations are generated from the Market and Business Model pillar evaluations. They address the gap between having a product and systematically selling it — the operational and strategic mechanisms through which the startup converts market opportunity into revenue.

**Types of Actions**

- Defining and documenting an Ideal Customer Profile (ICP) with firmographic, technographic, and behavioural criteria
- Developing a channel strategy that specifies primary and secondary sales channels, channel partner criteria, and channel economics
- Building and instrumenting a sales pipeline with defined stages, conversion benchmarks, and a target sales velocity metric
- Completing a formal pricing strategy review using competitive benchmarking and willingness-to-pay research
- Developing a reference customer programme with documented case studies, testimonials, and ROI evidence
- Establishing a customer success function with defined onboarding, adoption, and renewal processes
- Completing a partnership agreement with a named distribution or channel partner in the target market
- Developing a content-led demand generation programme targeting the defined ICP
- Establishing a product-led growth mechanism where the product itself drives user acquisition and expansion

**Generation Logic**

GTM Task recommendations are generated when the Market Pillar score for commercial traction falls below 6, when revenue growth metrics indicate the startup has a product-market fit hypothesis but lacks commercial execution capability, or when customer concentration is high (more than 60% of revenue from a single customer) and diversification is identified as a risk mitigation priority.

**Prioritisation Within Category**

GTM Tasks that directly generate or accelerate revenue (pipeline building, reference customer programmes, channel partnerships) are ranked above awareness and positioning tasks. ICP definition is ranked first because it is a prerequisite for all other GTM activities.

**Typical Timeline**

ICP definition and pipeline instrumentation: 0 to 30 days. Channel strategy and partner agreements: 1 to 3 months. Reference customer programme: 2 to 4 months. Product-led growth mechanism: 3 to 6 months.

---

### Category 10: Regulatory and Compliance Tasks

**Definition and Scope**

Regulatory and Compliance Tasks are recommendations required for the startup to operate legally, access government programmes, complete public sector or enterprise procurement, or remove a regulatory risk identified in the evaluation. These tasks are distinct from other categories because non-compliance with regulatory requirements can constitute a blocking condition — an issue that prevents the startup from advancing in its market regardless of product quality, team strength, or funding.

**Types of Actions**

- Registering for mandatory sectoral regulatory programmes (e.g., DPIIT recognition, MeitY empanelment, SEBI registration, IRDAI authorisation, RBI licensing for payment businesses)
- Completing a data localisation and data governance review for products subject to personal data regulations (Digital Personal Data Protection Act, GDPR where applicable)
- Obtaining industry-specific certifications required for product sale (e.g., BIS certification for hardware, CDSCO approval for health technology, AERB clearance for radiation equipment)
- Developing and implementing a cybersecurity policy and conducting a security audit to meet enterprise procurement requirements
- Completing export control compliance review for products with dual-use technology components
- Establishing a compliance management system for startups in regulated industries operating at scale
- Resolving any identified employment law compliance gaps (ESOP registration, PF/ESIC compliance, labour law registrations)
- Completing environmental compliance requirements for manufacturing or hardware-centric businesses

**Generation Logic**

Regulatory and Compliance Task recommendations are generated from the Risk Pillar evaluation, from specific sub-criteria within the Financial and Market pillars that assess regulatory exposure, and from any identified regulatory gap in the submitted documentation that constitutes a material risk to business continuity or investor confidence.

**Prioritisation Within Category**

Regulatory tasks that constitute blocking conditions (absence of a mandatory licence) are ranked Critical. Tasks that reduce risk exposure (data governance, cybersecurity) are ranked High. Certification and programme participation tasks that improve market access are ranked Medium.

**Typical Timeline**

Varies significantly by regulatory body and jurisdiction. Simple registrations: 0 to 30 days. Certification processes: 1 to 6 months. Licensing processes (e.g., NBFC, payment aggregator): 6 to 18 months.

---

## Section 2: Recommendation Attributes

Every individual recommendation generated by the TIDES Recommendation Engine must carry a complete, populated set of attributes. No recommendation may be issued with incomplete attributes. The following attribute definitions govern the data model for every recommendation record.

---

### 2.1 Recommendation ID

**Structure:** `TAES-REC-[StartupID]-[EvalCycle]-[PillarCode]-[SequenceNumber]`

**Format Specification:**
- `TAES-REC` — fixed prefix identifying this as a TAES Recommendation Engine output
- `[StartupID]` — the six-character alphanumeric unique identifier assigned to the startup at platform registration
- `[EvalCycle]` — the evaluation cycle number, zero-padded to two digits (e.g., `01`, `02`, `03`)
- `[PillarCode]` — a two-character code identifying the primary evaluation pillar: `FD` (Founder), `PR` (Product), `TK` (Technology), `MK` (Market), `BM` (Business Model), `FN` (Financial), `IP` (IP), `RK` (Risk)
- `[SequenceNumber]` — a three-digit sequential number within the pillar for this evaluation cycle

**Example:** `TAES-REC-AX7B3K-01-FD-003` — the third Founder pillar recommendation from the first evaluation cycle for startup AX7B3K.

**Purpose:** The Recommendation ID enables unambiguous tracking of recommendations across evaluation cycles, cross-referencing between findings and recommendations, and systematic measurement of implementation status.

---

### 2.2 Title

**Requirement:** The title must be a specific, imperative sentence (verb-first) that names the exact action to be taken. It must not be a category label, a general direction, or an abstract goal.

**Acceptable format:** "Recruit a full-time Chief Technology Officer with distributed systems architecture experience within 90 days."

**Unacceptable format:** "Strengthen the technical team" or "Address technology leadership gap."

**Length:** Maximum 20 words. The title must be intelligible as a standalone directive without requiring the surrounding recommendation text to interpret it.

---

### 2.3 Category

The single primary category from Section 1 that this recommendation belongs to. If a recommendation has characteristics of two categories (e.g., an IP filing that also has investment readiness implications), it is assigned to its primary driver category and the secondary category is noted in the Dependencies field.

---

### 2.4 Priority Level

Four priority levels are defined. Every recommendation must be assigned to exactly one priority level, determined by the prioritisation logic in Section 3.

**Critical:** The recommendation addresses a condition that is currently blocking the startup from advancing to its next stage, constitutes a legal or regulatory compliance failure, or represents a risk that could materially impair the business's continuity or fundability. Critical recommendations must be acted upon within 30 days of report delivery. They appear in a separate, prominently labelled section at the top of the Roadmap.

**High:** The recommendation addresses a significant capability gap or scoring deficiency that is materially affecting the startup's evaluation score, investor readiness, or commercial performance. High recommendations should be initiated within 60 days of report delivery and targeted for completion within the applicable category timeline.

**Medium:** The recommendation addresses an identifiable improvement opportunity that, while not urgent or blocking, represents a meaningful enhancement to the startup's capability or score position. Medium recommendations should be initiated within 90 days and completed within the applicable category timeline.

**Low:** The recommendation addresses a marginal gap or an opportunistic improvement that would incrementally improve the evaluation score or operational quality. Low recommendations are included for completeness and may be deferred if resource constraints require prioritisation of higher-priority items.

---

### 2.5 Linked Evaluation Pillar

The primary TAES evaluation pillar that this recommendation addresses. Every recommendation must be linked to exactly one of the eight TAES pillars: Founder, Product, Technology, Market, Business Model, Financial, IP, or Risk.

Where a recommendation has meaningful secondary impacts on a second pillar, that pillar is noted in the Expected Business Impact field.

---

### 2.6 Linked Sub-Criterion

The specific sub-criterion within the linked pillar that this recommendation targets. Sub-criteria are defined in the TAES Scoring Rubric (Document 04). The sub-criterion reference must include its pillar code and sub-criterion identifier (e.g., `FD-SC-04: Team Completeness and Functional Coverage`).

Linking to the sub-criterion is mandatory because it establishes the direct connection between the finding, the score, and the recommendation — the traceability chain that makes the recommendation auditable.

---

### 2.7 Evidence Basis

A specific statement of the evidence, drawn from the evaluation record, that generated this recommendation. The Evidence Basis must cite:

- The sub-criterion score that indicated the gap (e.g., "Sub-criterion FD-SC-04 scored 3.5/10")
- The specific document or absence of document that led to the score (e.g., "No CTO or equivalent technical leadership role identified in the submitted team profile; the founding team of three includes two commercial founders and one generalist software developer with no enterprise-scale architecture experience")
- Any supporting quantitative data (e.g., "Comparable startups at Series A stage in the SaaS-for-enterprise segment carry an average technical team headcount of 8–12 engineers with at least one senior architect")

---

### 2.8 Current State Description

A precise, factual description of the startup's current position with respect to the sub-criterion this recommendation addresses. This is drawn directly from the evaluation finding. It must be descriptive (what is true now) and not evaluative (not a judgment about whether the current state is good or bad — the score provides the evaluation; the description provides the context).

**Example:** "The startup currently operates with a two-person founding team comprising a CEO with a commercial background and a CPO with a UX design background. No technical co-founder or senior engineer is employed. Product development is contracted to an external agency. No technical leadership sits on the founding team or the board."

---

### 2.9 Desired State Description

A precise description of the state the startup must reach for this recommendation to be considered implemented. The Desired State is not an aspirational vision — it is a specific, verifiable endpoint that can be assessed in the next evaluation cycle.

**Example:** "The startup employs or has engaged (as a co-founder, full-time employee, or formalised technical advisor) an individual with demonstrable experience in enterprise-grade software architecture, who holds a defined technical leadership role, participates in product roadmap decisions, and is named in the company's formal governance documents."

---

### 2.10 Expected Score Improvement

The projected improvement in the linked pillar's score if this recommendation is fully implemented, expressed as a minimum-to-maximum range on the 10-point TAES scoring scale.

**Format:** `+[min] to +[max] points on the [Pillar] Pillar score`

**Example:** `+0.8 to +1.4 points on the Founder Pillar score`

Expected Score Improvement ranges are calibrated using the score weight assigned to the linked sub-criterion within its pillar, the magnitude of the gap between current and desired state, and historical data from prior evaluation cycles showing the score improvement achieved by startups that implemented comparable recommendations.

---

### 2.11 Estimated Effort

**Minimal:** Less than 20 hours of internal effort; no capital expenditure required; achievable by a founder in parallel with normal operations. Typically involves documentation, registration, or communication tasks.

**Moderate:** 20 to 80 hours of internal effort; may require modest external cost (legal fees, consultant engagement, software tooling); requires dedicated founder time but does not require halting other activities. Typically involves process development, document creation, or advisory engagement.

**Significant:** 80 to 300 hours of internal effort; requires material capital allocation (typically ₹2–10 lakh) or a dedicated team member's full attention for four to twelve weeks; may require external expertise engagement. Typically involves product development, certification processes, or hiring.

**Intensive:** More than 300 hours of internal effort; requires significant capital allocation (typically ₹10 lakh or more) or a sustained programme of work over multiple months involving multiple team members. Typically involves full TRL advancement programmes, regulatory approval processes, or transformational team restructuring.

---

### 2.12 Estimated Timeline

The specific time range within which the recommendation should be initiated and completed, expressed in weeks or months. The Estimated Timeline is a realistic operational estimate based on the type of action, the effort classification, and domain-specific knowledge of process durations (e.g., patent filings, certification timelines, executive recruiting cycles).

**Format:** "Initiate within [X] days of report delivery. Target completion within [Y] weeks/months."

**Example:** "Initiate within 14 days of report delivery. Target completion within 10 to 14 weeks."

---

### 2.13 Dependencies

A complete list of conditions, prior actions, or external resources that must be in place before this recommendation can be initiated or completed. Dependencies fall into three types:

- **Internal Dependencies:** Other recommendations that must be completed first (referenced by Recommendation ID)
- **Resource Dependencies:** Capital, tools, or personnel that must be available (e.g., "Requires engagement of a patent attorney")
- **External Dependencies:** Third-party processes or decisions that must occur (e.g., "Depends on receipt of company incorporation certificate" or "Requires completion of the MCA21 filing")

If a recommendation has no dependencies, this field is populated with "None — this recommendation can be initiated immediately upon report delivery."

---

### 2.14 Expected Business Impact

A specific description of the commercial, operational, or strategic outcome that this recommendation drives — beyond its effect on the evaluation score. This field answers the question: "Why does this matter for the business, not just for the evaluation?"

**Example:** "Recruiting a CTO will enable the startup to internalise its product development function, reducing per-feature development cost, improving roadmap velocity, and enabling the technical due diligence capability expected by Series A investors in the enterprise software category."

---

### 2.15 Success Criteria

A set of specific, verifiable conditions that indicate this recommendation has been fully implemented. Success Criteria are used by the evaluator team in the next evaluation cycle to assess implementation and determine whether the expected score improvement should be awarded.

Success Criteria must be observable (not inferred), specific (not general), and binary or graduated (clearly indicating whether the condition is met or not met).

**Example — three success criteria for the CTO hiring recommendation:**
1. A named individual holds the title of Chief Technology Officer or equivalent (Co-Founder and CTO / Head of Engineering) and is listed in the company's MCA filing or equivalent governance document.
2. The individual has a documented employment or co-founder agreement with the company, executed within the evaluation period.
3. The individual's prior work experience includes at least one documented instance of leading product development at an enterprise software company with more than 50 employees or more than ₹5 crore in annual revenue.

---

### 2.16 Next Evaluation Trigger

A specification of when this recommendation should be formally re-evaluated. This is either:

- **Cycle-based:** "This recommendation will be assessed in the next scheduled evaluation cycle."
- **Milestone-based:** "This recommendation should be re-assessed when the startup initiates a fundraise, completes a pilot deployment, or submits an application to a government grant programme."
- **Condition-based:** "This recommendation should be re-assessed if the regulatory landscape changes materially (e.g., DPDPA implementation regulations are published) within the recommendation's open window."

---

## Section 3: Prioritisation Logic

### 3.1 The Four Prioritisation Dimensions

Every recommendation is scored across four independent dimensions before its Priority Score is computed. These dimensions are evaluated separately and combined using a weighted formula.

**Dimension 1 — Impact (I)**
Impact measures the expected improvement in the startup's evaluation score if the recommendation is implemented. Impact is expressed numerically as the midpoint of the expected score improvement range (from Section 2.10), normalised to a 0–10 scale relative to the maximum possible score improvement for any single recommendation within the evaluation cycle.

For example, if the highest expected improvement in this evaluation cycle is +2.0 points on a pillar and this recommendation projects +1.2 points, its normalised Impact score is 6.0.

**Dimension 2 — Effort Inverse (E)**
Effort is converted to a numeric scale representing the inverse of resource burden: high effort maps to a low score, and low effort maps to a high score. This ensures that recommendations with the same impact are ranked higher if they require less effort.

| Effort Level | Numeric Value (E) |
|---|---|
| Minimal | 10 |
| Moderate | 7 |
| Significant | 4 |
| Intensive | 1 |

**Dimension 3 — Urgency (U)**
Urgency is a situational modifier that elevates the Priority Score when time-sensitive conditions apply. Urgency is assessed by the evaluator team based on stated startup context (e.g., an active fundraise, a pending regulatory deadline, a competitive threat window, or an expiring grant application window).

| Urgency Condition | Urgency Score |
|---|---|
| Active blocking condition (legal risk, regulatory non-compliance) | 10 |
| Fundraise or major commercial milestone within 90 days | 8 |
| Significant milestone within 6 months | 5 |
| No time-sensitive condition identified | 2 |

**Dimension 4 — Dependency Multiplier (D)**
The Dependency Multiplier assesses whether implementing this recommendation unblocks other recommendations. If completing this recommendation enables N other recommendations to begin, its Dependency Multiplier is `1 + (0.2 × N)`.

For example, if completing Recommendation A enables three other recommendations to begin, its Dependency Multiplier is `1 + (0.2 × 3) = 1.6`. If a recommendation has no downstream dependencies, its Dependency Multiplier is 1.0.

---

### 3.2 Priority Score Calculation

The Priority Score is calculated conceptually as:

```
Priority Score = [(I × 0.40) + (E × 0.25) + (U × 0.35)] × D
```

**Weighting rationale:**
- Impact carries the highest weight (0.40) because the primary objective of the Recommendation Engine is to improve evaluation scores and underlying capabilities.
- Urgency carries the second-highest weight (0.35) because time-sensitive conditions — particularly legal risks and fundraise windows — require system-level emphasis that raw score impact alone does not capture.
- Effort carries the lowest base weight (0.25) because effort is a constraint, not an objective. The Dependency Multiplier then amplifies the Priority Score for foundational recommendations, ensuring that structural prerequisites are surfaced before dependent actions.

**Priority Level Assignment from Score:**

| Priority Score Range | Assigned Priority Level |
|---|---|
| 8.0 – 10.0 | Critical |
| 6.0 – 7.9 | High |
| 4.0 – 5.9 | Medium |
| 0.0 – 3.9 | Low |

---

### 3.3 The Priority Matrix

The Priority Matrix provides an intuitive two-dimensional view of recommendations using Impact (vertical axis, Low to High) and Effort (horizontal axis, Low to High). Recommendations are placed in one of four quadrants, each with defined handling rules:

```
                    IMPACT
                    High │
                         │
    Q2: STRATEGIC        │    Q1: QUICK WINS
    (High Impact /       │    (High Impact /
     High Effort)        │    Low Effort)
                         │
    ─────────────────────┼─────────────────────
                         │
    Q4: DEPRIORITISE     │    Q3: FILL-INS
    (Low Impact /        │    (Low Impact /
     High Effort)        │    Low Effort)
                         │    Low  EFFORT   High
```

**Quadrant 1 — Quick Wins (High Impact, Low Effort):** These recommendations are surfaced first in the Roadmap priority stack. They are the immediate action agenda for the startup. Every Q1 recommendation is assigned at minimum a High priority level.

**Quadrant 2 — Strategic Investments (High Impact, High Effort):** These recommendations are critical to long-term improvement but cannot be completed quickly. They are assigned medium-to-long timelines and must be sequenced after any Q1 recommendations that are prerequisites. Strategic Investment recommendations with a high Urgency score may be elevated to Critical priority.

**Quadrant 3 — Fill-Ins (Low Impact, Low Effort):** These recommendations are low-risk improvements that can be executed opportunistically when resource bandwidth exists. They are assigned Low or Medium priority and are placed at the end of the Roadmap.

**Quadrant 4 — Deprioritise (Low Impact, High Effort):** Recommendations that fall in this quadrant are included in the Roadmap for completeness but are clearly labelled as low-priority items that should not consume significant resource during the current evaluation cycle. They are placed last in the priority stack and tagged accordingly.

---

### 3.4 Dependency Chain Resolution

When a set of recommendations form a dependency chain — where Recommendation B cannot begin until Recommendation A is complete, and Recommendation C cannot begin until Recommendation B is complete — the Recommendation Engine applies the following presentation and sequencing rules:

**Rule 1 — Cascade Ranking:** All recommendations in a dependency chain are ranked above other recommendations of comparable Priority Score, because their collective impact exceeds their individual impact measures.

**Rule 2 — Sequential Display:** In the Roadmap timeline view, recommendations in a dependency chain are displayed as a connected sequence with clear predecessor-successor indicators. The blocking recommendation (A) is marked with a "Gateway" flag; dependent recommendations (B, C) are indented beneath it and show their blocking dependency explicitly.

**Rule 3 — Critical Path Elevation:** If a dependency chain contains five or more recommendations, the first recommendation in the chain (the gateway) is elevated to Critical priority regardless of its individual Priority Score, because blocking the gateway blocks all downstream recommendations.

**Rule 4 — Partial Completion Handling:** If a gateway recommendation is partially implemented at the time of the next evaluation cycle, the evaluator team assesses whether the partial implementation is sufficient to permit initiation of the next recommendation in the chain. If yes, the next recommendation is unlocked and moves to In Progress status. If no, the gateway recommendation is maintained in In Progress status with a note on what remains to be completed.

---

### 3.5 Maximum Recommendations Per Report

**Limit:** The TIDES Recommendation Engine produces a maximum of 30 active recommendations per evaluation cycle report, across all categories.

**Rationale:** Research on decision fatigue and organisational change management consistently demonstrates that when individuals or teams are presented with more than 25–30 distinct action items, their ability to prioritise and act on any of them is impaired. The value of the Recommendation Engine lies not in the comprehensiveness of its output but in the quality of its prioritisation. A Roadmap with 12 well-prioritised, highly specific recommendations generates more startup improvement than a Roadmap with 45 recommendations of varying quality and clarity.

**Implementation of the limit:** When the engine generates more than 30 candidate recommendations, the lowest-Priority-Score recommendations are excluded from the active Roadmap and placed in a Deferred Recommendations register. Deferred recommendations are not deleted — they are retained in the platform and may be promoted to the active Roadmap in the next evaluation cycle if higher-priority items have been addressed or if the startup's context changes.

**Minimum recommendations per evaluation:** Every evaluation cycle must produce at least five active recommendations. If fewer than five recommendations are generated, the evaluator team must review the evaluation to ensure scoring thresholds have been applied correctly.

---

### 3.6 The Critical Threshold

A recommendation is assigned Critical priority when any one of the following conditions is met:

1. **Legal or regulatory non-compliance:** The startup is operating in a manner that violates a mandatory legal or regulatory requirement, and this was identified in the evaluation.
2. **Score floor breach:** The linked pillar score is below 3.0 out of 10.0, indicating a fundamental capability failure in a core evaluation dimension.
3. **Fundraise blocking condition:** The recommendation addresses a specific deficiency (ownership ambiguity, missing governance document, unregistered IP, regulatory gap) that would constitute a deal-breaker in a standard investor due diligence process, and the startup has a declared fundraise within 6 months.
4. **Dependency gateway at scale:** This recommendation is the gateway to a chain of five or more dependent recommendations.
5. **Safety or integrity risk:** The evaluation identified a risk factor that could materially harm customers, employees, or the startup's market licence if not addressed.

Critical recommendations are presented in a dedicated "Critical Actions" block at the top of every Roadmap format. They are explicitly flagged with red-status indicators and carry a 30-day action mandate.

---

## Section 4: Recommendation Generation by Pillar

For each of the eight TAES evaluation pillars, this section defines the score threshold that triggers recommendations, the most common recommendation types, the cross-pillar cascade logic, and one complete worked example recommendation with all attributes.

---

### 4.1 Founder Pillar

**Score Threshold:** Founder Pillar score below 6.5 triggers recommendation generation. Individual sub-criterion scores below 5.0 trigger specific sub-criterion recommendations regardless of the overall pillar score.

**Most Common Recommendation Types**

1. **Team Completeness:** Recruit a named missing function (CTO, CFO, Head of Sales, Head of Regulatory Affairs) through full-time hire, co-founder appointment, or fractional engagement.
2. **Domain Expertise Gap:** Engage a named-domain advisor or board member to provide sector-specific credibility and strategic guidance.
3. **Equity Structure:** Formalise founder equity agreements, implement vesting schedules, and resolve any undocumented equity commitments.
4. **Prior Track Record Documentation:** Compile and submit documented evidence of founding team members' prior ventures, exits, or relevant professional achievements.
5. **Board Governance:** Establish a formal board of directors with at least one independent member and documented governance procedures.
6. **Founder-Market Fit Narrative:** Develop and document a structured, evidence-backed narrative of the founding team's specific insight into the problem they are solving.
7. **Key-Person Risk Mitigation:** Document institutional knowledge, establish succession protocols, and cross-train team members to reduce single-founder concentration risk.
8. **Commitment Formalisation:** Execute and submit formal employment agreements or founder service agreements for all founding team members.

**Cross-Pillar Cascade Logic**

A weak Founder Pillar score — particularly in the Team Completeness sub-criterion — generates recommendations in three additional categories:

- **Hiring Tasks (Category 8):** Specific role hiring recommendations for the missing functions.
- **Investment Readiness Tasks (Category 4):** Investor-facing board governance recommendations, since team completeness is a primary investor due diligence criterion.
- **Technology Pillar (Section 4.3):** If the missing role is technical (CTO, Lead Architect), a Hiring Task recommendation in the Technology domain is also generated, reflecting the cross-pillar impact of technical leadership absence.

**Complete Worked Example Recommendation**

| Attribute | Value |
|---|---|
| **Recommendation ID** | `TAES-REC-AX7B3K-01-FD-001` |
| **Title** | Recruit a Chief Technology Officer with enterprise software architecture experience within 90 days |
| **Category** | Hiring Tasks |
| **Priority Level** | Critical |
| **Linked Evaluation Pillar** | Founder |
| **Linked Sub-Criterion** | `FD-SC-04: Team Completeness and Functional Coverage` |
| **Evidence Basis** | Sub-criterion FD-SC-04 scored 3.0/10. The founding team comprises a CEO (commercial background) and a CPO (UX background). Product development is entirely contracted to an external agency. No technical leadership is employed, engaged as an advisor, or named in governance documents. The startup's product is a B2B SaaS platform with a complex data integration layer; enterprise sales cycles require technical credibility in customer meetings and technical due diligence capability for prospective investors. |
| **Current State Description** | The startup has no technical co-founder, no CTO, and no senior engineer. All development is managed through a third-party agency. The founders have no ability to conduct technical due diligence, evaluate product architecture decisions independently, or present credibly in enterprise customer technical review sessions. |
| **Desired State Description** | The startup employs or has formally engaged a CTO or equivalent technical leadership individual who is named in company governance documents, participates in board and product strategy, holds a documented agreement with the company, and has demonstrable prior experience leading enterprise software development at scale. |
| **Expected Score Improvement** | +1.2 to +1.8 points on the Founder Pillar score |
| **Estimated Effort** | Significant (executive recruiting process; 8–16 weeks) |
| **Estimated Timeline** | Initiate within 7 days of report delivery. Target appointment within 90 days. |
| **Dependencies** | Internal: None — this recommendation can be initiated immediately. Resource: Budget allocation for CTO compensation (salary or equity package); engagement of an executive recruiting firm or activation of the founders' professional networks. |
| **Expected Business Impact** | Technical leadership internalisation reduces per-feature development cost by an estimated 30–40%, accelerates roadmap velocity, enables independent technical due diligence in investor processes, and increases enterprise customer close rate for deals involving technical buyer participation. |
| **Success Criteria** | 1. A named individual holds the CTO title and is listed in the company's MCA filing or equivalent governance document. 2. The individual has a signed employment agreement or co-founder agreement with the company. 3. The individual's documented work history includes at least one senior technical leadership role at a software company with more than ₹5 crore in annual revenue or more than 50 engineers. |
| **Next Evaluation Trigger** | Cycle-based — assessed at next scheduled evaluation cycle. Condition-based — to be assessed immediately if the startup initiates a fundraise process before the next scheduled evaluation. |

---

### 4.2 Product Pillar

**Score Threshold:** Product Pillar score below 6.0 triggers recommendation generation. Sub-criterion scores below 4.5 trigger specific sub-criterion recommendations.

**Most Common Recommendation Types**

1. **Product-Market Fit Evidence:** Conduct structured customer discovery interviews (minimum 30 conversations) and document findings in a formal PMF validation report.
2. **Product Roadmap:** Develop and publish (internally and to evaluators) a 12-month product roadmap with defined milestones, dependencies, and success metrics per feature.
3. **User Research:** Establish a continuous user research programme with documented interview protocols, synthesis outputs, and evidence of roadmap influence.
4. **Competitive Differentiation:** Conduct a structured competitive analysis and document the startup's product differentiation claims against specific, named competitors.
5. **Design and Usability:** Commission a usability audit of the product by a qualified UX practitioner and implement priority findings.
6. **Feature Completeness:** Complete a specific missing core feature identified in the evaluation as a prerequisite for the primary target customer segment's adoption.
7. **Product Analytics:** Instrument the product with a defined analytics and event-tracking system and establish a monthly product metrics review cadence.
8. **Customer Feedback Loop:** Implement a structured mechanism for collecting, categorising, and acting on customer feedback (e.g., in-product NPS, regular customer advisory sessions).

**Cross-Pillar Cascade Logic**

Weak Product scores cascade into:
- **Market Pillar (Section 4.4):** Low PMF evidence scores generate GTM Task recommendations, since product-market fit and commercial traction are interdependent.
- **Business Model Pillar (Section 4.5):** Low differentiation scores generate recommendations to revise pricing strategy and value proposition documentation.

**Complete Worked Example Recommendation**

| Attribute | Value |
|---|---|
| **Recommendation ID** | `TAES-REC-AX7B3K-01-PR-002` |
| **Title** | Complete 30 structured customer discovery interviews and document findings in a formal PMF validation report within 60 days |
| **Category** | Medium-Term Improvements |
| **Priority Level** | High |
| **Linked Evaluation Pillar** | Product |
| **Linked Sub-Criterion** | `PR-SC-02: Product-Market Fit Evidence` |
| **Evidence Basis** | Sub-criterion PR-SC-02 scored 3.5/10. The startup submitted a product pitch deck with testimonials from two pilot users but no structured customer discovery documentation, no defined ICP, and no evidence of a systematic PMF validation process. The two pilot user testimonials are qualitative and do not address adoption behaviour, willingness to pay, or competitive switching behaviour. |
| **Current State Description** | Two informal pilot user testimonials exist. No structured discovery process has been conducted. The founding team has spoken to fewer than 10 potential customers based on the submitted documentation. No documented ICP exists. |
| **Desired State Description** | A formal customer discovery programme has been completed with a minimum of 30 interviews across the target ICP. Findings are documented in a structured PMF validation report covering: problem severity ranking, willingness-to-pay data, competitive alternatives currently in use, and adoption drivers and barriers. |
| **Expected Score Improvement** | +0.8 to +1.2 points on the Product Pillar score |
| **Estimated Effort** | Moderate (estimated 40–60 hours of founder time across 6–8 weeks) |
| **Estimated Timeline** | Initiate within 7 days. Complete 30 interviews within 45 days. Produce written validation report within 60 days. |
| **Dependencies** | Internal: ICP definition (if not already complete, should be completed first — Category 9, GTM Task). Resource: Interview guide, note-taking or synthesis tool, access to target customer segment. |
| **Expected Business Impact** | Structured discovery findings directly inform product prioritisation, reducing feature development waste. Documented PMF evidence increases investor confidence and is a standard early-stage diligence requirement. Discovery conversations frequently identify early anchor customers. |
| **Success Criteria** | 1. A minimum of 30 discovery interview transcripts or structured notes submitted to the platform. 2. A written PMF validation report covering all four required domains (problem severity, WTP, competitive alternatives, adoption drivers) submitted to the platform. 3. Evidence that at least one product roadmap decision has been made based on the discovery findings. |
| **Next Evaluation Trigger** | Cycle-based — assessed at next scheduled evaluation. |

---

### 4.3 Technology Pillar

**Score Threshold:** Technology Pillar score below 6.5 triggers recommendation generation. TRL sub-criterion scores below 6.0 trigger TRL Advancement Task recommendations regardless of overall pillar score.

**Most Common Recommendation Types**

1. **TRL Advancement:** Complete the specific engineering, validation, or demonstration milestone required to advance from the current verified TRL to the next (see Category 5 for TRL milestone definitions).
2. **Technical Documentation:** Produce a comprehensive Technical Architecture Document (TAD) describing system design, technology stack, scalability model, and security architecture.
3. **Scalability Validation:** Conduct and document a load and performance testing programme to demonstrate system performance at production scale.
4. **Security Architecture:** Commission and complete a security architecture review or penetration test by a qualified third-party security firm.
5. **IP-Technology Alignment:** Identify all novel technical elements of the product and initiate patent filing for any patentable inventions not yet under protection.
6. **Open Source Compliance:** Conduct an open source licence audit to ensure all third-party libraries used in the product are licence-compatible with the startup's commercial model.
7. **Technical Debt Assessment:** Commission an independent code quality and technical debt assessment and develop a remediation plan for identified high-severity issues.
8. **Third-Party Technology Independence:** Identify critical third-party technology dependencies and develop a contingency plan or alternative sourcing strategy for any single-vendor dependencies.

**Cross-Pillar Cascade Logic**

Weak Technology scores cascade into:
- **Risk Pillar (Section 4.8):** Low security architecture scores generate Risk Pillar compliance recommendations.
- **IP Pillar (Section 4.7):** Identified novel technical elements without IP protection generate IP Task recommendations.
- **Founder Pillar (Section 4.1):** If the low Technology score is attributable to absence of technical leadership, a Hiring Task recommendation is generated in the Founder domain.

**Complete Worked Example Recommendation**

| Attribute | Value |
|---|---|
| **Recommendation ID** | `TAES-REC-AX7B3K-01-TK-001` |
| **Title** | Complete an operational prototype demonstration in a live customer environment and produce a signed customer acceptance letter within 120 days |
| **Category** | TRL Advancement Tasks |
| **Priority Level** | High |
| **Linked Evaluation Pillar** | Technology |
| **Linked Sub-Criterion** | `TK-SC-01: Technology Readiness Level` |
| **Evidence Basis** | Sub-criterion TK-SC-01 scored 5.0/10. The startup self-declared TRL 7 but submitted documentation supporting only TRL 5: a laboratory prototype validation report in a simulated environment, with no evidence of deployment in an operational customer environment. A TRL 7 demonstration requires operational environment deployment with documented performance metrics and a customer acceptance document. |
| **Current State Description** | Technology is validated at TRL 5 — prototype demonstrated in a simulated environment. No operational deployment with a real customer exists. No customer acceptance letter or live environment performance data has been submitted. |
| **Desired State Description** | Technology is validated at TRL 7 — an operational prototype has been deployed in a real customer environment, has operated for a defined period, has met defined performance criteria, and the customer has issued a signed acceptance letter documenting performance outcomes. |
| **Expected Score Improvement** | +1.0 to +1.5 points on the Technology Pillar score |
| **Estimated Effort** | Significant (estimated 120–200 hours of engineering time plus customer engagement and documentation) |
| **Estimated Timeline** | Initiate within 14 days. Complete live deployment within 60 days. Obtain customer acceptance letter within 120 days. |
| **Dependencies** | Internal: Identification and agreement with at least one pilot customer for live deployment. Resource: Engineering resources for deployment and support; customer relationship management time; legal review of pilot agreement. |
| **Expected Business Impact** | TRL 7 validation unlocks eligibility for multiple government technology development grants that require TRL 6+ entry. It also constitutes a reference deployment that can be used in enterprise sales cycles and investor presentations. |
| **Success Criteria** | 1. Documented evidence of live deployment in a real customer environment (deployment logs, customer access confirmation). 2. Performance metrics report showing system performance against defined benchmarks over a minimum 30-day operational period. 3. Signed customer acceptance letter on customer letterhead naming the technology, the deployment period, and the performance outcomes observed. |
| **Next Evaluation Trigger** | Condition-based — to be assessed when the startup applies for government grant programmes with TRL eligibility thresholds. Cycle-based otherwise. |

---

### 4.4 Market Pillar

**Score Threshold:** Market Pillar score below 6.0 triggers recommendation generation. Commercial traction sub-criterion scores below 4.5 trigger GTM Task recommendations regardless of overall score.

**Most Common Recommendation Types**

1. **ICP Definition:** Define and document an Ideal Customer Profile with firmographic, technographic, and behavioural criteria drawn from actual customer and prospect data.
2. **Market Sizing:** Conduct a bottom-up TAM/SAM/SOM analysis with documented methodology, data sources, and assumptions.
3. **Commercial Traction:** Secure and document a minimum of three paying customers or one anchor enterprise customer with a signed contract.
4. **Revenue Metrics:** Establish monthly tracking of ARR, MRR, churn rate, CAC, and LTV — and submit a 6-month historical view.
5. **Competitive Intelligence:** Develop a formal competitive landscape document updated quarterly, covering direct and indirect competitors, their positioning, pricing, and differentiation.
6. **Customer Concentration:** Develop a plan to reduce revenue concentration (if more than 50% from one customer) through pipeline diversification.
7. **Channel Strategy:** Define primary and secondary sales channels with economic models showing channel unit economics.
8. **Market Entry Validation:** Document the basis on which the startup selected its target geography and segment, including regulatory, competitive, and demand evidence.

**Cross-Pillar Cascade Logic**

Weak Market scores cascade into:
- **Business Model Pillar (Section 4.5):** Low commercial traction generates pricing strategy and unit economics recommendations.
- **Financial Pillar (Section 4.6):** Low revenue metrics generate financial modelling recommendations.

**Complete Worked Example Recommendation**

| Attribute | Value |
|---|---|
| **Recommendation ID** | `TAES-REC-AX7B3K-01-MK-001` |
| **Title** | Secure and document three paying B2B customers with signed contracts within 90 days and produce a commercial traction summary report |
| **Category** | Go-To-Market Tasks |
| **Priority Level** | High |
| **Linked Evaluation Pillar** | Market |
| **Linked Sub-Criterion** | `MK-SC-03: Commercial Traction and Revenue Evidence` |
| **Evidence Basis** | Sub-criterion MK-SC-03 scored 3.0/10. The startup submitted one LOI from a prospective customer but no signed contracts, no invoiced revenue, and no data on pipeline stage distribution. The founding team reports verbal interest from "several prospects" but has not submitted documented evidence of any closed sales. |
| **Current State Description** | One LOI exists. No paying customers. No signed contracts. No invoiced revenue. The startup is pre-revenue with unverified pipeline. |
| **Desired State Description** | Three or more paying B2B customers have signed commercial contracts, have made at least one payment, and are documented in the evaluation submission with copies of signed agreements and payment evidence. |
| **Expected Score Improvement** | +1.0 to +1.6 points on the Market Pillar score |
| **Estimated Effort** | Significant (sales execution effort; highly variable based on sales cycle length) |
| **Estimated Timeline** | Initiate immediately. Target first closed customer within 30 days; three customers within 90 days. |
| **Dependencies** | Internal: ICP definition must be complete to ensure sales effort is directed at the correct segment. Resource: Sales execution capacity (founder-led sales or a hired sales resource). |
| **Expected Business Impact** | Three paying customers validate the revenue model, reduce investor risk perception, establish reference relationships for enterprise sales expansion, and provide cash flow that may extend runway. |
| **Success Criteria** | 1. Three or more signed commercial contracts with distinct, named B2B customers submitted to the platform. 2. Payment evidence (invoice and bank statement confirmation) for at least two of the three customers. 3. A commercial traction summary report documenting deal size, contract terms, and customer profile for each. |
| **Next Evaluation Trigger** | Cycle-based. |

---

### 4.5 Business Model Pillar

**Score Threshold:** Business Model Pillar score below 6.0 triggers recommendation generation. Unit economics sub-criterion scores below 5.0 trigger specific recommendations.

**Most Common Recommendation Types**

1. **Revenue Model Clarity:** Document the revenue model in full: pricing structure, billing frequency, contract length, upsell pathways, and revenue recognition policy.
2. **Unit Economics:** Calculate and document CAC, LTV, payback period, and gross margin per customer segment, with methodology and data sources.
3. **Pricing Strategy:** Conduct a competitive pricing benchmarking exercise and document the basis for the current pricing relative to alternatives.
4. **Revenue Diversification:** Develop a plan to introduce a second revenue stream or monetisation mechanism to reduce single-revenue-model concentration risk.
5. **Scalability Model:** Document how the business model scales — specifically, how costs scale as customers increase, and at what customer volume the business reaches breakeven.
6. **Partner/Channel Economics:** If a channel or partner model is used, document the channel economics: margin structure, minimum order commitments, and incentive alignment mechanisms.
7. **Recurring Revenue Conversion:** If the business currently operates on transactional revenue, develop a plan to convert to a subscription or retainer model to improve revenue predictability.
8. **Value Proposition Specificity:** Rewrite the value proposition as a specific, quantified statement of the customer outcome achieved through use of the product.

**Cross-Pillar Cascade Logic**

Weak Business Model scores cascade into:
- **Financial Pillar (Section 4.6):** Low unit economics scores generate financial modelling recommendations.
- **Market Pillar (Section 4.4):** Low pricing strategy scores generate GTM Task recommendations on pricing validation through customer research.

**Complete Worked Example Recommendation**

| Attribute | Value |
|---|---|
| **Recommendation ID** | `TAES-REC-AX7B3K-01-BM-001` |
| **Title** | Calculate and document CAC, LTV, gross margin, and payback period for each customer segment within 45 days |
| **Category** | Medium-Term Improvements |
| **Priority Level** | High |
| **Linked Evaluation Pillar** | Business Model |
| **Linked Sub-Criterion** | `BM-SC-03: Unit Economics` |
| **Evidence Basis** | Sub-criterion BM-SC-03 scored 3.5/10. No unit economics documentation was submitted. The founding team's pitch deck states "LTV:CAC of 5:1" but provides no calculation methodology, no segmentation, and no data sourcing. The claim cannot be validated from the submitted evidence. |
| **Current State Description** | Unit economics are asserted but not calculated or documented. No CAC, LTV, gross margin per customer, or payback period calculation has been submitted. |
| **Desired State Description** | A unit economics document is produced for each defined customer segment, showing CAC with methodology (sum of sales and marketing cost over period / new customers acquired), LTV (average revenue per customer × average contract duration × gross margin), gross margin, and payback period (CAC / monthly gross profit per customer). |
| **Expected Score Improvement** | +0.9 to +1.4 points on the Business Model Pillar score |
| **Estimated Effort** | Minimal to Moderate (20–35 hours of financial analysis work) |
| **Estimated Timeline** | Initiate within 7 days. Complete within 45 days. |
| **Dependencies** | Internal: Requires access to sales expenditure records, marketing spend records, customer revenue data, and cost of goods sold breakdown. Resource: A finance professional (internal or fractional CFO) may be required if the founders lack financial modelling competency. |
| **Expected Business Impact** | Documented unit economics are a mandatory investor due diligence element at Series A. They enable informed pricing decisions, sales commission structure design, and marketing budget allocation. They also identify which customer segments are profitable and which are destroying value. |
| **Success Criteria** | 1. A unit economics spreadsheet or document submitted to the platform showing CAC, LTV, gross margin, and payback period per customer segment, with all input data and formulas visible. 2. Assumptions and data sources documented for each input. 3. A written narrative explaining what the unit economics imply for the business model's scalability. |
| **Next Evaluation Trigger** | Cycle-based. |

---

### 4.6 Financial Pillar

**Score Threshold:** Financial Pillar score below 6.0 triggers recommendation generation. Runway and financial management sub-criterion scores below 4.5 trigger specific recommendations.

**Most Common Recommendation Types**

1. **Financial Model:** Develop a fully integrated three-statement financial model (P&L, balance sheet, cash flow) with 18-month projections and defined assumptions.
2. **Cash Flow Management:** Implement monthly cash flow tracking and produce a rolling 90-day cash flow forecast updated weekly.
3. **Runway Extension:** Identify and execute on specific actions to extend cash runway by a minimum of 6 months (revenue acceleration, cost reduction, grant funding, bridge financing).
4. **Bookkeeping and Accounts:** Establish a formal bookkeeping system with monthly reconciliation and produce the last 12 months of management accounts.
5. **Financial Reporting:** Implement monthly board-level financial reporting covering P&L vs. budget, cash position, AR/AP aging, and key financial ratios.
6. **Revenue Recognition:** Develop and document a revenue recognition policy compliant with applicable accounting standards (Ind AS or IFRS).
7. **Grant and Subsidy Mapping:** Identify all applicable government grant programmes (DST, BIRAC, STPI, SIDBI, GeM, production-linked incentive schemes) and prepare applications for the top three by value.
8. **Audit and Statutory Compliance:** Ensure all statutory financial filings (GST returns, income tax, MCA annual filing) are current and submit compliance certificates to the evaluation platform.

**Cross-Pillar Cascade Logic**

Weak Financial scores cascade into:
- **Risk Pillar (Section 4.8):** Low runway scores generate Risk recommendations around financial concentration and contingency planning.
- **Fundraising Tasks (Category 6):** Low financial readiness scores generate fundraising preparation recommendations where the startup's stated intent includes a near-term funding round.

**Complete Worked Example Recommendation**

| Attribute | Value |
|---|---|
| **Recommendation ID** | `TAES-REC-AX7B3K-01-FN-001` |
| **Title** | Develop a fully integrated 18-month financial model with P&L, cash flow, and balance sheet projections and submit to the platform within 60 days |
| **Category** | Investment Readiness Tasks |
| **Priority Level** | Critical |
| **Linked Evaluation Pillar** | Financial |
| **Linked Sub-Criterion** | `FN-SC-02: Financial Model Quality and Completeness` |
| **Evidence Basis** | Sub-criterion FN-SC-02 scored 2.5/10. No financial model was submitted. The startup's pitch deck includes a single-slide revenue projection chart with no assumptions, no cost structure, and no cash flow implications. The founders could not respond to standard financial due diligence questions during the evaluation interview. The startup is targeting a Series A raise within 6 months. |
| **Current State Description** | No financial model exists. A revenue projection slide was submitted but contains no supporting assumptions, no cost model, and no cash flow projection. The startup has no documented understanding of its burn rate, runway, or break-even timeline. |
| **Desired State Description** | A fully integrated financial model is built and maintained, covering 18 months of P&L, cash flow statement, and balance sheet, with all major assumptions documented and subject to scenario sensitivity analysis. The model is submitted to the evaluation platform and is capable of surviving investor scrutiny. |
| **Expected Score Improvement** | +1.4 to +2.0 points on the Financial Pillar score |
| **Estimated Effort** | Moderate to Significant (estimated 40–80 hours of financial modelling work; may require engagement of a fractional CFO) |
| **Estimated Timeline** | Initiate within 7 days. First draft within 30 days. Final model submitted to platform within 60 days. |
| **Dependencies** | Internal: Requires current actual P&L, balance sheet, and bank statements as input data. Resource: Financial modelling expertise — founders should assess whether this requires a fractional CFO engagement. |
| **Expected Business Impact** | A credible financial model is a prerequisite for Series A investor engagement. It also enables internal resource allocation decisions, identifies the funding requirement precisely, and demonstrates to investors that the founders understand the financial dynamics of their business. |
| **Success Criteria** | 1. A three-statement financial model submitted to the platform in a standard spreadsheet format with visible formulas. 2. A minimum of 15 major assumptions documented with sources. 3. Three scenario versions (base, upside, downside) with sensitivity analysis on revenue growth rate and CAC. 4. Runway calculation under each scenario. |
| **Next Evaluation Trigger** | Condition-based — to be reviewed at the initiation of the fundraise process. Cycle-based otherwise. |

---

### 4.7 IP Pillar

**Score Threshold:** IP Pillar score below 6.5 triggers recommendation generation. IP protection sub-criterion scores below 5.0 trigger specific IP Task recommendations.

**Most Common Recommendation Types**

1. **Patent Filing:** File a provisional patent application for the core technology invention within the next 60 days.
2. **FTO Analysis:** Commission a freedom-to-operate analysis for the primary product in the key commercial jurisdictions.
3. **Trademark Registration:** File trademark registrations for brand name, logo, and key product names in India and in any international target markets.
4. **Trade Secret Policy:** Develop and implement a trade secret protection policy covering access controls, employee NDAs, and know-how documentation.
5. **IP Ownership Audit:** Conduct an IP ownership audit to verify that all IP created by founders, employees, and contractors is validly assigned to the company.
6. **IP Register:** Create and maintain a formal IP register documenting all IP assets, their status, ownership, and associated filings.
7. **Licensing Strategy:** Develop an IP licensing strategy for any IP assets with standalone monetisation potential.
8. **Copyright Registration:** File copyright registrations for proprietary software code, content assets, and creative works.

**Cross-Pillar Cascade Logic**

Weak IP scores cascade into:
- **Technology Pillar (Section 4.3):** If the IP gap is related to an unprotected core technology, a TRL Advancement Task may be linked to the IP filing recommendation (since evidence of innovation is required for certain patent filings).
- **Risk Pillar (Section 4.8):** IP ownership gaps or FTO exposure generate Risk recommendations.
- **Investment Readiness Tasks (Category 4):** Any IP deficiency generates an Investment Readiness recommendation because IP ownership and protection status is a primary investor due diligence item.

**Complete Worked Example Recommendation**

| Attribute | Value |
|---|---|
| **Recommendation ID** | `TAES-REC-AX7B3K-01-IP-001` |
| **Title** | File a provisional patent application for the core data integration algorithm with a qualified patent attorney within 45 days |
| **Category** | IP Tasks |
| **Priority Level** | Critical |
| **Linked Evaluation Pillar** | IP |
| **Linked Sub-Criterion** | `IP-SC-01: IP Protection Status` |
| **Evidence Basis** | Sub-criterion IP-SC-01 scored 2.0/10. The startup's core product includes a proprietary data normalisation algorithm described in the technical documentation as the primary differentiator. No patent application has been filed. No trade secret policy is in place. The algorithm is documented in a technical whitepaper available to all registered users of the platform. Public disclosure without a patent filing may have started the 12-month Paris Convention grace period clock in some jurisdictions. |
| **Current State Description** | The core differentiating technology (data normalisation algorithm) is unprotected by patent, trade secret, or any other IP instrument. It has been publicly disclosed. No IP of any kind has been filed or registered by the company. |
| **Desired State Description** | A provisional patent application has been filed by a qualified patent attorney with the Indian Patent Office, covering the core data normalisation algorithm and its key inventive claims. The filing receipt is submitted to the evaluation platform. A trade secret policy is in place to protect elements of the technology not covered by the patent. |
| **Expected Score Improvement** | +1.5 to +2.2 points on the IP Pillar score |
| **Estimated Effort** | Moderate (patent attorney engagement: ₹50,000–₹1,50,000 for provisional application; 20–30 hours of internal technical documentation time to prepare invention disclosure) |
| **Estimated Timeline** | Engage patent attorney within 7 days. Complete invention disclosure document within 14 days. File provisional application within 45 days. |
| **Dependencies** | Internal: None — this is the gateway recommendation for all other IP recommendations. Resource: Patent attorney engagement; internal technical resource to prepare the invention disclosure document. |
| **Expected Business Impact** | Patent filing establishes priority date, provides 12-month window to file complete specification, enables "patent pending" claims in marketing, is required for certain government grant programmes (BIRAC, DST NIDHI), and is a primary investor due diligence item for technology-based startups. |
| **Success Criteria** | 1. Provisional patent application filing receipt from the Indian Patent Office submitted to the evaluation platform, showing filing date, application number, and title. 2. Name of the patent attorney or firm engaged is documented. 3. Draft trade secret policy covering the startup's technical know-how is submitted to the platform. |
| **Next Evaluation Trigger** | Condition-based — to be assessed when the startup files a complete specification (12-month deadline from provisional filing date). Cycle-based otherwise. |

---

### 4.8 Risk Pillar

**Score Threshold:** Risk Pillar score below 6.0 triggers recommendation generation. Any individual risk sub-criterion score below 4.0 triggers specific recommendations regardless of overall pillar score.

**Most Common Recommendation Types**

1. **Regulatory Risk:** Conduct a comprehensive regulatory mapping exercise and implement a compliance roadmap for all identified applicable regulatory requirements.
2. **Financial Concentration Risk:** Implement a plan to reduce dependence on a single customer, investor, or revenue source.
3. **Key-Person Risk:** Document institutional knowledge for all key individuals and implement cross-training or succession planning.
4. **Technology Risk:** Identify single-point-of-failure technology dependencies and develop contingency or redundancy plans.
5. **Market Risk:** Document the basis for the startup's chosen market entry strategy and develop a contingency plan for the scenario in which the primary market assumption is invalidated.
6. **Cybersecurity Risk:** Commission a cybersecurity risk assessment and implement identified priority remediation actions.
7. **Contractual Risk:** Conduct a review of all major contracts (customer, supplier, partner) for unfavourable terms, concentration of liability, or absence of standard protection clauses.
8. **Insurance:** Assess and obtain appropriate business insurance coverage (directors and officers liability, product liability, professional indemnity where applicable).

**Cross-Pillar Cascade Logic**

Weak Risk scores cascade into:
- **Financial Pillar (Section 4.6):** Financial concentration risk generates runway extension and diversification recommendations.
- **Regulatory and Compliance Tasks (Category 10):** Identified regulatory gaps generate specific compliance task recommendations.
- **IP Pillar (Section 4.7):** Technology IP risk generates IP protection recommendations.

**Complete Worked Example Recommendation**

| Attribute | Value |
|---|---|
| **Recommendation ID** | `TAES-REC-AX7B3K-01-RK-001` |
| **Title** | Conduct a regulatory mapping exercise for all applicable data protection and fintech regulations and produce a written compliance roadmap within 60 days |
| **Category** | Regulatory and Compliance Tasks |
| **Priority Level** | Critical |
| **Linked Evaluation Pillar** | Risk |
| **Linked Sub-Criterion** | `RK-SC-02: Regulatory and Compliance Risk` |
| **Evidence Basis** | Sub-criterion RK-SC-02 scored 2.5/10. The startup operates a B2B fintech data platform processing personal financial data of end users on behalf of its enterprise customers. The evaluation found no privacy policy, no data processing agreement template, no data localisation assessment, and no documentation of compliance with the Digital Personal Data Protection Act 2023. The startup's enterprise customer base includes one bank and two NBFCs — entities subject to RBI data governance guidelines. |
| **Current State Description** | The startup processes personal financial data without a documented privacy policy, a DPDP Act compliance assessment, or data processing agreements with its enterprise customers. No data localisation review has been conducted. The startup is potentially in breach of multiple applicable data protection requirements. |
| **Desired State Description** | A regulatory mapping document is produced identifying all applicable data protection, financial sector, and consumer protection regulations. A compliance roadmap with specific actions, timelines, and responsible owners is developed. Priority compliance gaps (privacy policy, DPAs, data localisation) are remediated within 90 days. |
| **Expected Score Improvement** | +1.2 to +1.8 points on the Risk Pillar score |
| **Estimated Effort** | Significant (requires legal counsel engagement; estimated ₹1–3 lakh for regulatory review and documentation) |
| **Estimated Timeline** | Engage legal counsel within 7 days. Regulatory mapping complete within 30 days. Compliance roadmap produced within 45 days. Priority gaps remediated within 90 days. |
| **Dependencies** | Internal: None — this is the gateway for all compliance-related recommendations. Resource: Engagement of a qualified technology law firm with data protection and fintech regulatory expertise. |
| **Expected Business Impact** | Regulatory compliance is a contractual prerequisite for enterprise customers in the financial sector. Non-compliance is a deal-blocker for bank and NBFC customer contracts and a material risk flag for investors. Remediation enables the startup to sign DPAs, bid for regulated sector contracts, and qualify for fintech-specific government programmes. |
| **Success Criteria** | 1. A written regulatory mapping document covering DPDP Act, RBI data governance guidelines, and applicable NBFC/banking sector regulations submitted to the platform. 2. A written compliance roadmap with specific action items and completion dates submitted. 3. A published privacy policy on the startup's website compliant with DPDP Act disclosure requirements. 4. A template Data Processing Agreement reviewed by legal counsel and submitted to the platform. |
| **Next Evaluation Trigger** | Condition-based — to be reassessed when the startup executes its first contract with a regulated financial institution. Cycle-based otherwise. |

---

## Section 5: Recommendation Roadmap Output Format

The Recommendation Roadmap is the primary output artefact of the TIDES Recommendation Engine. It is generated as part of the evaluation report but constitutes an independent document that is maintained, updated, and tracked across evaluation cycles. The Roadmap is presented in three distinct views, each designed for a different audience and use case.

---

### 5.1 Roadmap Summary View

The Summary View presents the top five recommendations from the full Roadmap, selected by Priority Score. It is designed to provide founders, evaluators, and platform reviewers with an immediate, actionable snapshot of the startup's most critical next steps.

**Structure of the Summary View:**

**Header block:** Startup name, evaluation cycle number, report date, overall TAES score, and a single sentence characterising the startup's primary improvement priority (e.g., "This startup's most significant immediate improvement opportunity lies in Financial Pillar completeness, with a concurrent Critical action required in IP protection.").

**Critical Actions Panel (if applicable):** A distinctly marked panel listing all Critical-priority recommendations. This panel appears before the ranked top-5 list if any Critical recommendations exist in the full Roadmap. It is displayed with a visual separator and a clear urgency indicator.

**Top 5 Priority Recommendations Table:**

| Rank | Rec ID | Title (shortened to 15 words max) | Pillar | Category | Priority | Est. Impact | Est. Timeline |
|---|---|---|---|---|---|---|---|
| 1 | TAES-REC-... | File provisional patent for core algorithm with patent attorney | IP | IP Tasks | Critical | +1.5–2.2 pts | 45 days |
| 2 | TAES-REC-... | Develop 18-month integrated financial model | Financial | Investment Readiness | Critical | +1.4–2.0 pts | 60 days |
| 3 | TAES-REC-... | Recruit CTO with enterprise software architecture experience | Founder | Hiring Tasks | Critical | +1.2–1.8 pts | 90 days |
| 4 | TAES-REC-... | Complete 30 customer discovery interviews and document findings | Product | Medium-Term | High | +0.8–1.2 pts | 60 days |
| 5 | TAES-REC-... | Secure three paying B2B customers with signed contracts | Market | GTM Tasks | High | +1.0–1.6 pts | 90 days |

**Cumulative Impact Indicator:** Below the table, a statement indicating the total expected score improvement if all five recommendations are implemented: "Full implementation of these five recommendations is projected to improve the overall TAES score by approximately +[X] points, from [current score] to approximately [projected score]."

**Roadmap Access Link:** A reference to the full Roadmap document, the Timeline View, and the Pillar View.

---

### 5.2 Roadmap Timeline View

The Timeline View arranges all recommendations across a 0–18 month horizon, grouped by implementation window. It is designed for operational planning — enabling founders to see what must happen in which order and to sequence their resource allocation accordingly.

**Timeline Bands:**

- **Month 0–1 (Immediate):** All Critical recommendations and Quick Win recommendations. Typically 3–8 items.
- **Month 1–3 (Near-Term):** High-priority Medium-Term and domain-specific task recommendations that should be initiated in the first quarter.
- **Month 3–6 (Mid-Term):** Medium-priority recommendations requiring sustained effort.
- **Month 6–12 (Longer-Term):** Long-Term Improvement recommendations and complex domain-specific tasks.
- **Month 12–18 (Strategic):** Transformational recommendations requiring sustained investment and development time.

**Dependency Chains in the Timeline View:**

Recommendations in a dependency chain are shown as connected bars on the timeline. The gateway recommendation occupies the first position on the bar. Dependent recommendations are shown as bars that begin at the estimated completion point of their predecessor. A visual indicator (connector line or indented display) makes the dependency explicit.

**Parallel vs. Sequential Streams:**

Recommendations in different pillars that have no dependencies on each other are displayed in parallel rows, making it clear which activities can proceed simultaneously and which must be sequential. This is particularly useful for founders managing multiple workstreams.

**Status Overlay:**

In subsequent evaluation cycles, the Timeline View shows the implementation status of each recommendation using colour coding or status indicators: Implemented (green), In Progress (amber), Pending (grey), Superseded (strikethrough), Withdrawn (red).

---

### 5.3 Roadmap Pillar View

The Pillar View organises all recommendations by evaluation pillar. It is designed for domain-specific review — enabling founders to assess the full improvement agenda for a specific pillar, and enabling evaluators to verify that all scored sub-criteria with gaps have generated corresponding recommendations.

**Structure:**

Each pillar is presented as a collapsible section containing:
- Current pillar score and target score (the score the pillar would reach if all recommendations in this section were implemented)
- All recommendations linked to this pillar, displayed as a compact summary table
- A sub-criterion coverage map: a row for each sub-criterion in the pillar, indicating whether it has a linked recommendation (if the score was below the threshold) or is documented as adequate (if the score was above the threshold)

**Cross-Pillar Recommendations in the Pillar View:**

Recommendations that were generated by a weakness in one pillar but whose implementation primarily addresses a different domain (e.g., a Hiring Task generated by a Founder Pillar gap) appear in both pillar sections — in the generating pillar section as the source recommendation, and in the implementing domain section (e.g., Team/HR) with a cross-reference note.

---

### 5.4 Implementation Status Tracking Across Cycles

When a subsequent evaluation cycle is completed, the Roadmap from the prior cycle is displayed alongside the new Roadmap in an integrated comparison view. For each recommendation in the prior Roadmap, the new evaluation provides one of the following status outcomes:

- **Implemented (Verified):** The success criteria for this recommendation have been met. The recommendation is marked green. The actual score improvement achieved is displayed alongside the projected score improvement.
- **Implemented (Partial):** Some but not all success criteria have been met. The recommendation remains open with a reduced impact expectation and a note on what remains.
- **In Progress:** The startup has demonstrably begun implementation (evidence of initiation is visible) but completion criteria are not yet met.
- **Not Implemented:** No evidence of implementation was found in the new evaluation submission. The recommendation is carried forward to the new Roadmap with its status reset to Pending and its priority score adjusted (see Section 6).
- **Superseded:** A new recommendation in the current cycle replaces this recommendation with a more specific or updated version.
- **Withdrawn:** The evaluator team has determined that the recommendation is no longer applicable due to a change in the startup's context, market, or regulatory environment.

---

## Section 6: Recommendation Tracking and Lifecycle

### 6.1 Persistence Across Evaluation Cycles

Recommendations do not expire between evaluation cycles. Every recommendation generated by the TIDES Recommendation Engine is stored in the platform's persistent evaluation record for the startup and remains associated with the startup's account indefinitely. Recommendations are never deleted — they are transitioned through status states that maintain a complete historical record of the startup's improvement journey.

The persistent record serves multiple purposes:
- It prevents the same recommendation from being issued redundantly across cycles without acknowledgement of prior issuance.
- It enables trend analysis: a recommendation that remains unimplemented across three consecutive cycles indicates either a resource constraint, a founder capability gap, or a recommendation design problem (the recommendation may be unrealistic and should be reconsidered).
- It enables improvement delta calculation: the record of what was recommended and what was implemented provides the input data for measuring how much the startup improved as a result of platform engagement.

---

### 6.2 Recommendation Status States

Every recommendation in the platform exists in exactly one of the following status states at any given time:

**Pending:** The recommendation has been issued, the startup is aware of it, and no implementation evidence has been observed. The recommendation is in the active Roadmap.

**In Progress:** The startup has submitted evidence of initiation (e.g., a draft document, a signed engagement letter, a project plan, or a verbal confirmation documented by the evaluator) but has not yet met the success criteria. The recommendation remains active in the Roadmap with a progress notation.

**Implemented:** The success criteria have been fully met and verified by the evaluator team in a formal evaluation cycle or a documented interim review. The recommendation is moved out of the active Roadmap and into the Implemented record.

**Superseded:** A later evaluation has generated a more specific, more appropriate, or higher-scope recommendation that replaces this one. The original recommendation is closed and the superseding recommendation carries a cross-reference to the superseded ID.

**Withdrawn:** The evaluator team has determined that the recommendation is no longer applicable. This occurs when the startup's context has changed materially (e.g., a pivoted business model makes a prior product recommendation irrelevant), when a regulatory change has resolved the condition that generated the recommendation, or when the recommendation is identified retrospectively as having been based on incorrect evidence.

---

### 6.3 Implementation Verification in Subsequent Cycles

Implementation verification is conducted by the evaluator team as a structured component of each evaluation cycle. The verification process for each open recommendation proceeds as follows:

**Step 1 — Evidence Review:** The evaluator team reviews the startup's submission for the new evaluation cycle, specifically searching for evidence that meets the success criteria documented in the recommendation. Evidence is reviewed against each success criterion individually — partial evidence results in Partial Implementation status, not Implemented status.

**Step 2 — Score Observation:** The evaluator team computes the new pillar score for the linked sub-criterion. An improvement in the sub-criterion score is consistent with but not sufficient to verify implementation — the score improvement must be accompanied by documentary evidence that meets the success criteria.

**Step 3 — Status Assignment:** Based on the evidence review and score observation, the evaluator team assigns one of the five status states to each open recommendation.

**Step 4 — Impact Reconciliation:** For recommendations assigned Implemented status, the actual score improvement is compared to the projected range (from the Expected Score Improvement attribute). If the actual improvement falls within the projected range, no adjustment is required. If it falls outside the range — in either direction — the evaluator team documents the variance and updates the impact model for similar recommendations in future cycles.

---

### 6.4 Carry-Forward Rules

Recommendations that are not implemented by the time of the next evaluation cycle are carried forward into the new Roadmap under the following rules:

**Rule 1 — Priority Escalation:** A recommendation that has been Pending for two consecutive evaluation cycles without evidence of initiation is escalated by one priority level (Low → Medium, Medium → High, High → Critical) and assigned a Carry-Forward flag. The escalation reflects the compounding cost of delay — the longer a gap is left unaddressed, the more it compounds in its negative effects on the startup's score position and strategic options.

**Rule 2 — Rationale Requirement:** For any recommendation carried forward from a prior cycle, the evaluator team must document the reason for non-implementation as assessed from the evaluation record. Possible reasons include: resource constraint (capital), resource constraint (time), external dependency unresolved, recommendation not pursued (no evidence of any action), or evidence of attempt without completion.

**Rule 3 — Specificity Review:** When a recommendation is carried forward, its attributes are reviewed and updated to reflect any changed context. If the startup's current state has changed since the recommendation was issued (even if the recommendation itself has not been implemented), the Current State Description and Evidence Basis fields are updated.

**Rule 4 — Supersession at Carry-Forward:** If the carried-forward recommendation has been made obsolete by intervening circumstances (not resolved but obsolete), it is Withdrawn at the carry-forward review and a replacement recommendation is issued if still applicable.

---

### 6.5 Improvement Delta Calculation

The Improvement Delta measures the change in the startup's overall TAES score between evaluation cycles attributable to recommendation implementation. It is calculated as follows:

**Step 1 — Baseline Score Record:** The overall TAES score and each pillar score from Evaluation Cycle N are recorded as the baseline.

**Step 2 — New Score Record:** The overall TAES score and each pillar score from Evaluation Cycle N+1 are recorded as the new score.

**Step 3 — Raw Delta:** The raw delta is `(New Overall Score) − (Baseline Overall Score)`.

**Step 4 — Attributed Delta:** The portion of the raw delta attributable to implemented recommendations is calculated by summing the actual score improvements for each recommendation marked Implemented in Cycle N+1. This is the Attributed Delta.

**Step 5 — Unattributed Delta:** Any raw delta not explained by implemented recommendations is the Unattributed Delta. This may reflect external events (new customers acquired, new IP filed without a specific recommendation triggering it, market improvement), evaluator methodology variance, or score drift.

**Step 6 — Implementation Efficiency Ratio:** `Attributed Delta / Number of Implemented Recommendations` provides the average score improvement per implemented recommendation — a platform-level metric used to calibrate the accuracy of the impact projection model.

The Improvement Delta is reported to the startup in the next evaluation cycle report and is also aggregated across the full TIDES platform portfolio to track the effectiveness of the Recommendation Engine at the programme level.

---

## Section 7: Recommendation Quality Standards

Every recommendation generated by the TIDES Recommendation Engine must meet the following quality standards before it is included in a Roadmap. These standards apply at the point of recommendation generation and are enforced through the evaluator review process prior to report delivery.

---

### 7.1 Specificity Requirement

A recommendation must name a specific action, not a general direction. This standard is enforced by applying the following test to every recommendation title and desired state description:

**Specificity Test:** Can the startup's founder read this recommendation and begin executing it immediately, without needing to interpret what it means, determine what "success" looks like, or seek clarification from the evaluator? If the answer is no, the recommendation is insufficiently specific and must be rewritten.

**Specificity Failure Indicators:**
- The title contains abstract nouns without specified objects (e.g., "Improve financial management" — improve what specific aspect, by what specific mechanism?)
- The desired state is expressed as a quality attribute rather than a defined deliverable (e.g., "The startup should have better IP protection" — better than what? by what mechanism? as evidenced by what?)
- The success criteria are not independently verifiable by a third-party evaluator who has no prior knowledge of the startup

**Remediation:** Every failing recommendation must be rewritten to name a specific action, a specific deliverable, and a specific verifiable outcome before it is issued.

---

### 7.2 Evidence Linkage Requirement

Every recommendation must cite the specific evidence from the evaluation record that generated it. The Evidence Basis field is mandatory and must be populated with:

1. The sub-criterion code and score
2. The specific document, data point, or absence thereof that produced the low score
3. Where applicable, a benchmark or reference point (comparable startup performance, industry standard, regulatory requirement) that contextualises the gap

**Evidence Linkage Test:** Can the evaluator demonstrate, for any specific recommendation, the exact data point(s) from the evaluation record that generated it? If no, the recommendation lacks a verifiable evidence basis and must not be issued.

**Prohibition on Assumption-Based Recommendations:** Recommendations must not be generated from assumptions about what the startup "probably" needs or from generalised knowledge about startups at a given stage, without a specific finding in the evaluation record to support them.

---

### 7.3 Achievability Requirement

Every recommendation must be achievable by the startup with resources that are reasonably available given the startup's stage, geography, and industry context. This requirement has two components:

**Financial Achievability:** The estimated cost of implementing the recommendation must be proportional to the startup's known resource position. A recommendation to "complete a full clinical trial" for a pre-seed medical device startup is not achievable and must not be issued. Instead, the achievable recommendation at that stage would be to complete the specific milestone within the clinical development pathway that is appropriate for the funding available.

**Operational Achievability:** The time and personnel demands of the recommendation must be realistic given the startup's team size and current workload. No recommendation should require more than approximately 20% of the founding team's collective working hours over its implementation period, unless it is specifically designated as a strategic, full-attention project.

**Achievability Review:** The evaluator team must confirm achievability for every Intensive effort recommendation before issuing it.

---

### 7.4 Non-Duplication Requirement

No two recommendations in the same Roadmap may address the same specific action. If the evaluation generates two candidate recommendations that prescribe the same action through different routes (e.g., "file a trademark" generated from both the IP Pillar and the Investment Readiness analysis), they must be merged into a single recommendation with both evidence bases cited.

**Overlap Test:** Before finalising the Roadmap, the evaluator team reviews the full recommendation set for any two recommendations whose Desired State Descriptions overlap materially. Overlapping recommendations are merged, with the higher-priority attributes retained and all evidence bases combined.

**Proximity Test:** Two recommendations that address adjacent but distinct actions are not duplicates even if they share a domain. "File a provisional patent" and "conduct a freedom-to-operate analysis" are distinct actions in the IP domain and both may appear in the same Roadmap.

---

### 7.5 Measurability Requirement

Every recommendation must have defined success criteria that are measurable — specifically, criteria that produce a binary or graduated assessment of completion that does not require subjective interpretation.

**Measurability Test:** Could two independent evaluators, reviewing the same startup submission, reach the same conclusion about whether this recommendation has been implemented? If significant disagreement is probable, the success criteria are insufficiently measurable and must be revised.

**Measurability Standards for Common Recommendation Types:**
- Document-based recommendations: the specific document must be named, its required contents specified, and its submission to the platform required as evidence.
- Hiring-based recommendations: the named role must be documented in governance records and the individual's relevant experience must be verifiable from a submitted CV or professional profile.
- Registration-based recommendations: the registration certificate or filing receipt must be submitted as evidence.
- Revenue-based recommendations: contract documentation and payment evidence must be submitted.
- Process-based recommendations: documented evidence of the process (e.g., a written procedure, a meeting log, a tool configuration) must be submitted.

---

## Worked Example: Recommendation Roadmap

### Context

**Startup:** NeuralLend Technologies Pvt. Ltd.
**Industry:** B2B Fintech — AI-powered credit risk assessment for MSME lending
**Stage:** Pre-Series A
**Evaluation Cycle:** 01
**Evaluation Date:** 2026-06-24
**Overall TAES Score:** 4.8 / 10.0

**Score Summary:**

| Pillar | Score | Status |
|---|---|---|
| Founder | 3.5 / 10 | Critical Gap |
| Product | 5.5 / 10 | Below Threshold |
| Technology | 6.2 / 10 | Adequate |
| Market | 5.0 / 10 | Below Threshold |
| Business Model | 4.5 / 10 | Below Threshold |
| Financial | 2.8 / 10 | Critical Gap |
| IP | 4.0 / 10 | Below Threshold |
| Risk | 5.0 / 10 | Below Threshold |

**Key Findings:**
- Two-person founding team (CEO and CPO); no CTO, no CFO, no Head of Risk
- Core ML credit scoring model is operational but not validated by a third-party model risk management review
- Product has two paying customers (one urban cooperative bank, one NBFC); ARR of ₹24 lakh
- No financial model exists; burn rate is undocumented; estimated runway of 4 months based on current account balance
- No patent filed for the ML model architecture; no trade secret policy; no FTO analysis
- No DPDP Act compliance documentation; no RBI regulatory mapping completed
- Series A fundraise planned for Q4 2026 (approximately 4 months from evaluation date)

---

### Full Recommendation Roadmap — NeuralLend Technologies Pvt. Ltd. (Cycle 01)

**Total Active Recommendations: 18 | Critical: 4 | High: 8 | Medium: 5 | Low: 1**

---

#### CRITICAL ACTIONS (Immediate — 0 to 30 days)

---

**Recommendation 1 of 18**

| Attribute | Value |
|---|---|
| **Rec ID** | `TAES-REC-NL0042-01-FN-001` |
| **Title** | Engage a fractional CFO and produce a documented 18-month integrated financial model within 45 days |
| **Category** | Investment Readiness Tasks |
| **Priority** | Critical |
| **Pillar** | Financial |
| **Sub-Criterion** | `FN-SC-02: Financial Model Quality` |
| **Evidence Basis** | FN-SC-02 scored 1.5/10. No financial model was submitted. Founders confirmed during interview that burn rate is estimated informally from account balance. Runway is approximately 4 months. Series A planned in 4 months. |
| **Current State** | No financial model. Burn rate unknown precisely. Runway approximately 4 months by informal estimation. No revenue recognition policy. No management accounts. |
| **Desired State** | Integrated 18-month P&L, cash flow, and balance sheet model with documented assumptions, three scenarios, and monthly actuals-to-forecast comparison capability. |
| **Expected Score Improvement** | +1.6 to +2.2 points on Financial Pillar |
| **Estimated Effort** | Significant |
| **Timeline** | Initiate within 3 days. Fractional CFO engaged within 7 days. First model draft within 21 days. Final model within 45 days. |
| **Dependencies** | Resource: Engagement of fractional CFO (estimated ₹60,000–₹1,20,000 per month; 2-month engagement minimum). Internal: access to all bank statements, invoices, and expense records. |
| **Business Impact** | Without a financial model, the Series A process cannot be initiated. Investors will request financial projections in the first meeting. A credible model also identifies the precise cash need and prevents runway exhaustion before the raise closes. |
| **Success Criteria** | 1. Fractional CFO engagement agreement signed and submitted. 2. Integrated 18-month financial model submitted to the platform with visible formulas and assumption documentation. 3. Three scenarios (base, upside, downside) with runway calculation under each. 4. Last 6 months of management accounts produced and submitted. |
| **Next Evaluation Trigger** | Condition-based: immediately upon initiating the Series A process. |

---

**Recommendation 2 of 18**

| Attribute | Value |
|---|---|
| **Rec ID** | `TAES-REC-NL0042-01-RK-001` |
| **Title** | Conduct a regulatory mapping exercise for DPDP Act, RBI MSME lending guidelines, and RBI digital lending regulations and produce a written compliance roadmap within 30 days |
| **Category** | Regulatory and Compliance Tasks |
| **Priority** | Critical |
| **Pillar** | Risk |
| **Sub-Criterion** | `RK-SC-02: Regulatory and Compliance Risk` |
| **Evidence Basis** | RK-SC-02 scored 2.0/10. NeuralLend processes personal financial and credit data of MSME borrowers. No DPDP Act compliance documentation was submitted. No RBI digital lending guidelines compliance review was submitted. The startup's enterprise customers (bank and NBFC) are subject to RBI's outsourcing and model risk guidelines, which impose obligations on their technology vendors. |
| **Current State** | No regulatory mapping. No privacy policy. No data processing agreements with enterprise customers. No documentation of compliance with RBI's digital lending or outsourcing guidelines. |
| **Desired State** | A written regulatory compliance roadmap covering DPDP Act, RBI digital lending guidelines, RBI outsourcing guidelines (for lender customers), and state-level money lending regulations. Priority compliance gaps remediated within 90 days. |
| **Expected Score Improvement** | +1.2 to +1.7 points on Risk Pillar |
| **Estimated Effort** | Significant |
| **Timeline** | Engage fintech regulatory counsel within 7 days. Mapping complete within 30 days. Roadmap produced within 45 days. |
| **Dependencies** | Resource: Fintech law firm with RBI regulatory expertise (estimated ₹1.5–3 lakh for initial engagement). |
| **Business Impact** | RBI-regulated bank and NBFC customers cannot expand their vendor relationship with NeuralLend without a vendor risk assessment that includes regulatory compliance. Non-compliance is a contract-blocker and investor risk flag. |
| **Success Criteria** | 1. Written regulatory mapping document submitted covering all four regulatory domains. 2. Written compliance roadmap with specific actions and timelines submitted. 3. Privacy policy published on website. 4. Draft Data Processing Agreement reviewed by legal counsel and submitted. |
| **Next Evaluation Trigger** | Condition-based: upon signing of next enterprise customer contract. |

---

**Recommendation 3 of 18**

| Attribute | Value |
|---|---|
| **Rec ID** | `TAES-REC-NL0042-01-IP-001` |
| **Title** | File a provisional patent application for the ML-based credit scoring model architecture with a qualified patent attorney within 45 days |
| **Category** | IP Tasks |
| **Priority** | Critical |
| **Pillar** | IP |
| **Sub-Criterion** | `IP-SC-01: IP Protection Status` |
| **Evidence Basis** | IP-SC-01 scored 2.5/10. No patent filed. The ML credit scoring model architecture is described in the technical documentation as the core competitive differentiator. The architecture is partially described in a published conference paper co-authored by one of the founders. Public disclosure has occurred. No trade secret policy exists. |
| **Current State** | Core ML model architecture is unprotected and has been partially disclosed publicly via academic publication. No patent application filed. No trade secret policy. |
| **Desired State** | Provisional patent application filed covering the inventive elements of the ML model architecture. Trade secret policy implemented for elements not covered by the patent. Filing receipt submitted to the platform. |
| **Expected Score Improvement** | +1.4 to +2.0 points on IP Pillar |
| **Estimated Effort** | Moderate |
| **Timeline** | Engage patent attorney within 7 days. Invention disclosure document produced within 14 days. Provisional application filed within 45 days. |
| **Dependencies** | Resource: Patent attorney with AI/ML domain experience (estimated ₹75,000–₹1,50,000 for provisional application). Internal: Technical founder must produce invention disclosure document. |
| **Business Impact** | Patent filing establishes priority date, enables "patent pending" claims, is required for BIRAC and DST NIDHI funding eligibility, and is a standard investor due diligence item for technology-driven fintech startups. |
| **Success Criteria** | 1. Indian Patent Office filing receipt submitted with application number and date. 2. Invention disclosure document submitted. 3. Draft trade secret policy submitted. |
| **Next Evaluation Trigger** | Condition-based: upon filing of complete specification (12 months from provisional filing). |

---

**Recommendation 4 of 18**

| Attribute | Value |
|---|---|
| **Rec ID** | `TAES-REC-NL0042-01-FD-001` |
| **Title** | Recruit a full-time Chief Risk Officer or Head of Model Risk Management with RBI-regulated lending experience within 90 days |
| **Category** | Hiring Tasks |
| **Priority** | Critical |
| **Pillar** | Founder |
| **Sub-Criterion** | `FD-SC-04: Team Completeness and Functional Coverage` |
| **Evidence Basis** | FD-SC-04 scored 2.0/10. The founding team of two (CEO: sales background; CPO: data science background) has no risk management, regulatory, or financial services operations expertise. NeuralLend's customers are regulated financial institutions whose vendor risk assessments will specifically assess the vendor's own risk management capability. No regulatory or risk professional is employed or on the advisory board. |
| **Current State** | Two-person founding team with no risk, regulatory, or lending operations expertise. No advisory board member with RBI-regulated lending experience. |
| **Desired State** | A named individual with demonstrable experience in model risk management or credit risk in a regulated financial institution holds a senior role (CRO, Head of Risk, or equivalent) at NeuralLend, participates in product and compliance decisions, and is named in company governance documents. |
| **Expected Score Improvement** | +1.0 to +1.6 points on Founder Pillar |
| **Estimated Effort** | Significant |
| **Timeline** | Begin recruiting immediately. Target appointment within 90 days. If full-time hire is unfeasible within 30 days, engage a qualified fractional advisor within 30 days as an interim measure. |
| **Dependencies** | Resource: Compensation budget for CRO hire (salary or equity package). If fractional: ₹30,000–₹60,000 per month advisory retainer. |
| **Business Impact** | A qualified CRO enables NeuralLend to credibly represent risk management capability to regulated financial institution customers, pass vendor risk assessments, and present a complete risk governance narrative to Series A investors. |
| **Success Criteria** | 1. Named individual in CRO or equivalent role documented in company records. 2. Individual's prior experience includes minimum 3 years in model risk management or credit risk at an RBI-regulated financial institution. 3. Employment agreement or advisory agreement signed and submitted. |
| **Next Evaluation Trigger** | Condition-based: immediately if the Series A process begins before this role is filled. |

---

#### HIGH PRIORITY ACTIONS (Near-Term — 1 to 3 months)

---

**Recommendation 5 of 18**

| Attribute | Value |
|---|---|
| **Rec ID** | `TAES-REC-NL0042-01-FD-002` |
| **Title** | Commission a third-party model risk management validation review of the ML credit scoring model and submit the validation report within 90 days |
| **Category** | TRL Advancement Tasks |
| **Priority** | High |
| **Pillar** | Technology |
| **Sub-Criterion** | `TK-SC-03: Technical Validation and Third-Party Evidence` |
| **Evidence Basis** | TK-SC-03 scored 4.0/10. The ML credit scoring model has been internally validated by the CPO but has not been subject to independent model validation — a standard requirement for AI/ML models deployed in regulated lending decisions under RBI guidelines. |
| **Current State** | Internal validation only. No third-party model risk management review has been completed. RBI-regulated lender customers cannot formally adopt the model in credit decisioning without an independent validation. |
| **Desired State** | An independent model validation report produced by a qualified third party (risk advisory firm or model risk specialist) confirming model performance, stability, fairness, and compliance with applicable AI governance standards. |
| **Expected Score Improvement** | +0.8 to +1.2 points on Technology Pillar |
| **Estimated Effort** | Significant |
| **Timeline** | Engage model risk advisory firm within 14 days. Validation complete within 90 days. |
| **Dependencies** | Dependency: Recommendation 4 (CRO/Head of Risk) should be initiated in parallel; the CRO will manage the validation engagement. Resource: ₹3–8 lakh for model validation engagement. |
| **Business Impact** | Third-party model validation is a contractual prerequisite for regulated lender customers to use NeuralLend's model in credit decisions. It is also a competitive differentiator — few MSME credit AI startups have independent validation at this stage. |
| **Success Criteria** | 1. Model validation report from a named third-party firm submitted to the platform. 2. Report covers: model performance metrics, stability testing, fairness/bias analysis, and compliance assessment. 3. Any identified model deficiencies have a documented remediation plan. |
| **Next Evaluation Trigger** | Condition-based: upon signing of next enterprise customer contract. |

---

**Recommendation 6 of 18**

| Attribute | Value |
|---|---|
| **Rec ID** | `TAES-REC-NL0042-01-MK-001` |
| **Title** | Secure two additional paying enterprise customers (bank or NBFC) with signed commercial contracts within 90 days |
| **Category** | Go-To-Market Tasks |
| **Priority** | High |
| **Pillar** | Market |
| **Sub-Criterion** | `MK-SC-03: Commercial Traction and Revenue Evidence` |
| **Evidence Basis** | MK-SC-03 scored 4.0/10. Two paying customers exist but revenue concentration is extreme: the NBFC customer accounts for 83% of current ARR. The cooperative bank customer has a trial contract that has not yet converted to a full commercial agreement. |
| **Current State** | Two customers, one of which is on a trial contract. 83% revenue concentration in one customer. Pipeline of "several prospects" is unverified and undocumented. |
| **Desired State** | Four or more paying enterprise customers, each on a signed commercial contract, with no single customer representing more than 50% of ARR. A documented sales pipeline with defined stage distribution and conversion metrics. |
| **Expected Score Improvement** | +0.9 to +1.3 points on Market Pillar |
| **Estimated Effort** | Significant |
| **Timeline** | ICP and pipeline documentation: 14 days. First new customer targeted close: 60 days. Second new customer close: 90 days. |
| **Dependencies** | Internal: ICP must be formally defined (Recommendation 7). Resource: Sales execution capacity — consider founder-led sales supported by a part-time business development resource. |
| **Business Impact** | Customer diversification reduces financial concentration risk, demonstrates commercial scalability to investors, and provides additional reference relationships for enterprise sales development. |
| **Success Criteria** | 1. Four or more signed commercial contracts with distinct named enterprise customers submitted to the platform. 2. No single customer exceeds 50% of ARR. 3. A CRM-based pipeline report showing all active opportunities, their stage, and estimated close dates submitted. |
| **Next Evaluation Trigger** | Cycle-based. |

---

**Recommendation 7 of 18**

| Attribute | Value |
|---|---|
| **Rec ID** | `TAES-REC-NL0042-01-BM-001` |
| **Title** | Document the complete revenue model including pricing structure, unit economics (CAC, LTV, payback period), and gross margin per customer segment within 45 days |
| **Category** | Medium-Term Improvements |
| **Priority** | High |
| **Pillar** | Business Model |
| **Sub-Criterion** | `BM-SC-03: Unit Economics` |
| **Evidence Basis** | BM-SC-03 scored 3.0/10. No unit economics documentation submitted. Pricing is described informally as "negotiated per customer" with no published price list, no pricing rationale, and no calculation of LTV or CAC. |
| **Current State** | Revenue model is informal. Pricing is negotiated ad hoc. No CAC, LTV, or gross margin calculation exists. Unit economics are unknown. |
| **Desired State** | A documented revenue model covering: pricing tiers, CAC calculation methodology, LTV calculation, gross margin per customer segment, and payback period. Unit economics demonstrate a path to a sustainable LTV:CAC ratio above 3:1 within 18 months. |
| **Expected Score Improvement** | +0.8 to +1.2 points on Business Model Pillar |
| **Estimated Effort** | Moderate |
| **Timeline** | Initiate within 7 days (in parallel with financial model development). Complete within 45 days. |
| **Dependencies** | Dependency: Fractional CFO engagement (Recommendation 1) — the CFO should produce unit economics as part of the financial model engagement. |
| **Business Impact** | Investors will request unit economics in the first meeting. Defined pricing enables scalable sales (no ad hoc negotiation). Unit economics inform hiring and marketing spend decisions. |
| **Success Criteria** | 1. Unit economics document submitted covering CAC, LTV, payback period, and gross margin for each customer segment. 2. Pricing tiers documented and internally published. 3. LTV:CAC ratio calculated and documented with methodology. |
| **Next Evaluation Trigger** | Cycle-based. |

---

**Recommendation 8 of 18**

| Attribute | Value |
|---|---|
| **Rec ID** | `TAES-REC-NL0042-01-FD-003` |
| **Title** | Establish a formal advisory board with minimum two members covering regulatory/RBI expertise and enterprise fintech sales within 60 days |
| **Category** | Investment Readiness Tasks |
| **Priority** | High |
| **Pillar** | Founder |
| **Sub-Criterion** | `FD-SC-06: Board Governance and External Expertise` |
| **Evidence Basis** | FD-SC-06 scored 3.5/10. No advisory board exists. No external expertise supplements the two-person founding team. No independent oversight of regulatory or strategic decisions exists. |
| **Current State** | No advisory board. No external advisors engaged. No independent governance. |
| **Desired State** | A formal advisory board of minimum two members with documented engagement terms. One member must have regulatory/RBI expertise. One member must have enterprise fintech sales or business development expertise in the Indian regulated lending sector. |
| **Expected Score Improvement** | +0.6 to +1.0 points on Founder Pillar |
| **Estimated Effort** | Moderate |
| **Timeline** | Identify candidates within 21 days. Agreements signed within 60 days. |
| **Dependencies** | Resource: Advisory equity allocation (typically 0.1–0.5% per advisor with 2-year vesting); legal documentation for advisory agreements. |
| **Business Impact** | Advisory board members provide credibility in enterprise customer sales meetings, support fundraising introductions, and provide the regulatory expertise gap-fill required before the CRO hire is complete. |
| **Success Criteria** | 1. Signed advisory agreements for minimum two advisors submitted to the platform. 2. Each advisor's relevant domain expertise documented. 3. Advisory board terms of engagement (frequency of meetings, expected commitments) documented. |
| **Next Evaluation Trigger** | Cycle-based. |

---

**Recommendation 9 of 18**

| Attribute | Value |
|---|---|
| **Rec ID** | `TAES-REC-NL0042-01-FN-002` |
| **Title** | Implement a monthly financial reporting cadence with board-level reporting package by end of current month |
| **Category** | Quick Wins |
| **Priority** | High |
| **Pillar** | Financial |
| **Sub-Criterion** | `FN-SC-04: Financial Management Practices` |
| **Evidence Basis** | FN-SC-04 scored 2.0/10. The startup has no formal financial reporting. No board-level reporting package exists. Founders review account balance informally and do not track burn rate, AR aging, or revenue metrics in any structured system. |
| **Current State** | No financial reporting system. No management reporting. Financial management is entirely informal. |
| **Desired State** | A monthly financial reporting package is produced covering: P&L vs. budget, cash position and burn rate, accounts receivable aging, revenue metrics (ARR, MRR, new vs. churn), and key financial ratios. Package is reviewed in a monthly financial review meeting. |
| **Expected Score Improvement** | +0.6 to +0.9 points on Financial Pillar |
| **Estimated Effort** | Minimal |
| **Timeline** | Implement within 14 days. First monthly report produced within 30 days. |
| **Dependencies** | Dependency: Fractional CFO (Recommendation 1) will implement reporting as part of engagement. |
| **Business Impact** | Financial reporting is a prerequisite for board governance, investor updates, and fundraise preparation. It also prevents the runway exhaustion risk identified in the current evaluation. |
| **Success Criteria** | 1. A financial reporting template submitted to the platform. 2. First completed monthly financial report submitted. 3. Evidence of a financial review meeting (minutes or agenda) submitted. |
| **Next Evaluation Trigger** | Cycle-based. |

---

**Recommendation 10 of 18**

| Attribute | Value |
|---|---|
| **Rec ID** | `TAES-REC-NL0042-01-IP-002` |
| **Title** | Conduct an IP ownership audit to verify all ML model IP is validly assigned to the company and resolve any ambiguous ownership within 45 days |
| **Category** | IP Tasks |
| **Priority** | High |
| **Pillar** | IP |
| **Sub-Criterion** | `IP-SC-03: IP Ownership and Assignment` |
| **Evidence Basis** | IP-SC-03 scored 3.0/10. The ML credit scoring model was developed partially during the CPO's prior academic affiliation. The academic institution's IP policy may claim rights over inventions developed by faculty or students using institutional resources. No IP assignment agreement from the academic institution exists in the submitted documentation. |
| **Current State** | IP ownership of the core ML model is ambiguous. No IP assignment agreement from the CPO's prior institution. No IP assignment clauses in employee or contractor agreements. |
| **Desired State** | Written confirmation from the relevant academic institution that it does not claim rights over the ML model. IP assignment clauses in all employee and contractor agreements. An IP register documenting all company IP and its ownership status. |
| **Expected Score Improvement** | +0.7 to +1.0 points on IP Pillar |
| **Estimated Effort** | Moderate |
| **Timeline** | Engage IP attorney within 7 days. Audit complete within 45 days. Institution clearance obtained within 60 days (timeline depends on institution). |
| **Dependencies** | Internal: Recommendation 3 (Patent filing) should not proceed until IP ownership is confirmed. Resource: IP attorney (same engagement as Recommendation 3). |
| **Business Impact** | IP ownership ambiguity is a Series A deal-breaker. Investors' legal due diligence will identify this risk and may refuse to proceed until it is resolved. Early resolution prevents a late-stage diligence delay. |
| **Success Criteria** | 1. Written IP clearance letter from the CPO's prior academic institution submitted to the platform. 2. IP assignment clauses added to all employment and contractor agreements. 3. IP register documenting all company IP assets submitted. |
| **Next Evaluation Trigger** | Condition-based: prior to initiating Series A process. |

---

**Recommendation 11 of 18**

| Attribute | Value |
|---|---|
| **Rec ID** | `TAES-REC-NL0042-01-PR-001` |
| **Title** | Develop a 12-month product roadmap with defined milestones, customer-backed feature prioritisation, and a product metrics dashboard within 45 days |
| **Category** | Medium-Term Improvements |
| **Priority** | High |
| **Pillar** | Product |
| **Sub-Criterion** | `PR-SC-04: Product Roadmap and Development Process` |
| **Evidence Basis** | PR-SC-04 scored 4.5/10. No formal product roadmap was submitted. The founding team described product direction verbally during the evaluation interview but could not provide a documented roadmap. Feature prioritisation is described as "driven by customer requests" without a formal prioritisation framework. |
| **Current State** | No documented product roadmap. Feature development driven by informal customer requests. No product metrics dashboard. No evidence of a formal product development process. |
| **Desired State** | A 12-month product roadmap is documented and submitted, showing quarterly milestones, feature prioritisation rationale, customer validation for prioritised features, and success metrics per milestone. A product metrics dashboard tracks weekly active users, feature adoption, and customer satisfaction. |
| **Expected Score Improvement** | +0.7 to +1.0 points on Product Pillar |
| **Estimated Effort** | Moderate |
| **Timeline** | Draft roadmap within 21 days. Customer validation of top 5 features within 30 days. Final roadmap and dashboard within 45 days. |
| **Dependencies** | None. |
| **Business Impact** | A documented roadmap enables enterprise customer planning conversations, investor confidence in product execution, and internal team alignment. It also provides a basis for the customer success function (knowing when promised features will be delivered). |
| **Success Criteria** | 1. 12-month roadmap document submitted with quarterly milestones and feature-level detail. 2. Evidence of customer input into the roadmap (call notes, survey results, or advisory meeting minutes). 3. Product metrics dashboard screenshot or report submitted showing at least 4 tracked metrics. |
| **Next Evaluation Trigger** | Cycle-based. |

---

**Recommendation 12 of 18**

| Attribute | Value |
|---|---|
| **Rec ID** | `TAES-REC-NL0042-01-BM-002` |
| **Title** | Develop a DPIIT startup registration and submit a grant application to SIDBI Fund of Funds or DST NIDHI within 30 days |
| **Category** | Quick Wins |
| **Priority** | High |
| **Pillar** | Financial |
| **Sub-Criterion** | `FN-SC-05: Alternative Funding and Grant Strategy` |
| **Evidence Basis** | FN-SC-05 scored 2.5/10. No DPIIT registration exists. No grant applications have been made. The startup's current runway of approximately 4 months makes grant funding an important potential bridge. DPIIT registration is also a prerequisite for several government fintech programmes and procurement categories. |
| **Current State** | No DPIIT recognition. No government grant applications made. No engagement with any government startup funding programme. |
| **Desired State** | DPIIT recognition certificate obtained. Applications submitted to at least two government grant or fund-of-funds programmes relevant to the startup's stage and sector. |
| **Expected Score Improvement** | +0.4 to +0.7 points on Financial Pillar |
| **Estimated Effort** | Minimal |
| **Timeline** | DPIIT application within 7 days (online process; typically 7–14 days to recognition). Grant applications within 30 days. |
| **Dependencies** | None. |
| **Business Impact** | DPIIT recognition provides tax benefits, access to government procurement portals, and programme eligibility. Grant funding extends runway, reducing the urgency of the Series A and improving the startup's negotiating position. |
| **Success Criteria** | 1. DPIIT recognition certificate submitted to the platform. 2. Evidence of at least two government grant or fund programme applications submitted (application reference numbers). |
| **Next Evaluation Trigger** | Cycle-based. |

---

#### MEDIUM PRIORITY ACTIONS (Mid-Term — 3 to 6 months)

---

**Recommendation 13 of 18**

| Attribute | Value |
|---|---|
| **Rec ID** | `TAES-REC-NL0042-01-IP-003` |
| **Title** | Conduct a freedom-to-operate analysis for the ML credit scoring model in India, UAE, and Singapore markets within 90 days |
| **Category** | IP Tasks |
| **Priority** | Medium |
| **Pillar** | IP |
| **Sub-Criterion** | `IP-SC-02: IP Risk and FTO Status` |
| **Evidence Basis** | IP-SC-02 scored 4.0/10. No FTO analysis has been conducted. The startup is planning international expansion to UAE and Singapore within 18 months. ML credit scoring is a high-patent-density domain. |
| **Current State** | No FTO analysis. Potential patent conflict exposure in international target markets unknown. |
| **Desired State** | FTO analysis completed for India, UAE, and Singapore jurisdictions, identifying any patent risk and documenting clearance or design-around strategy where necessary. |
| **Expected Score Improvement** | +0.5 to +0.8 points on IP Pillar |
| **Estimated Effort** | Significant |
| **Timeline** | Engage IP attorney for FTO scope definition within 30 days. Analysis complete within 90 days. |
| **Dependencies** | Dependency: Recommendation 3 (patent filing) and Recommendation 10 (IP ownership audit) should be complete before FTO analysis is commissioned to ensure the analysis covers the correct inventive scope. |
| **Business Impact** | FTO analysis is required before entering new markets. It also provides the confidence to invest in international expansion without legal risk. |
| **Success Criteria** | 1. FTO analysis report for all three jurisdictions submitted. 2. Any identified risk areas documented with proposed design-around or licensing strategy. |
| **Next Evaluation Trigger** | Condition-based: upon initiation of UAE or Singapore market entry. |

---

**Recommendation 14 of 18**

| Attribute | Value |
|---|---|
| **Rec ID** | `TAES-REC-NL0042-01-MK-002` |
| **Title** | Define a formal Ideal Customer Profile with firmographic, technographic, and credit portfolio criteria and document it within 21 days |
| **Category** | Quick Wins |
| **Priority** | Medium |
| **Pillar** | Market |
| **Sub-Criterion** | `MK-SC-01: Market Segmentation and ICP Definition` |
| **Evidence Basis** | MK-SC-01 scored 4.5/10. The ICP is described informally as "urban cooperative banks and small NBFCs." No firmographic criteria (asset size, loan book size, geography, digital infrastructure), technographic criteria (existing core banking system, API capability), or credit portfolio criteria (MSME portfolio share, NPA ratio) have been documented. |
| **Current State** | ICP is informally defined. No firmographic, technographic, or credit portfolio criteria exist. Sales effort may be directed at prospects that are poor fits, extending sales cycles and reducing conversion. |
| **Desired State** | A formal ICP document defines: asset size range, loan book composition, geography, core banking system (for API compatibility), MSME portfolio share, digital readiness criteria, and decision-maker personas (CRO, CTO, CEO at target institutions). |
| **Expected Score Improvement** | +0.4 to +0.7 points on Market Pillar |
| **Estimated Effort** | Minimal |
| **Timeline** | Complete within 21 days. |
| **Dependencies** | None — foundational recommendation that enables Recommendation 6 (customer acquisition). |
| **Business Impact** | ICP definition enables targeted sales prospecting, reduces sales cycle length, improves conversion rates, and provides investors with evidence of disciplined commercial strategy. |
| **Success Criteria** | 1. Written ICP document submitted covering all six defined criteria. 2. ICP criteria used to segment the existing prospect pipeline (evidence: updated CRM or pipeline document). |
| **Next Evaluation Trigger** | Cycle-based. |

---

**Recommendation 15 of 18**

| Attribute | Value |
|---|---|
| **Rec ID** | `TAES-REC-NL0042-01-BM-003` |
| **Title** | Develop and launch a formal customer success function with defined onboarding, adoption tracking, and renewal process within 90 days |
| **Category** | Medium-Term Improvements |
| **Priority** | Medium |
| **Pillar** | Business Model |
| **Sub-Criterion** | `BM-SC-05: Revenue Retention and Expansion Mechanics` |
| **Evidence Basis** | BM-SC-05 scored 3.5/10. No formal customer success function exists. Onboarding is managed informally by the CPO. No adoption metrics are tracked. The cooperative bank pilot has been operational for 6 months without a formal renewal conversation or expansion discussion. |
| **Current State** | Customer success is informal, CPO-managed, and unstructured. No onboarding process, no adoption tracking, no renewal management. |
| **Desired State** | A customer success function exists with: a defined onboarding process (with documented milestones and handoffs), monthly adoption reporting per customer (API call volume, decision coverage, model performance metrics), a quarterly business review cadence, and a formal renewal and expansion conversation process. |
| **Expected Score Improvement** | +0.5 to +0.8 points on Business Model Pillar |
| **Estimated Effort** | Moderate |
| **Timeline** | Onboarding process documented within 30 days. Adoption reporting implemented within 60 days. QBR cadence launched within 90 days. |
| **Dependencies** | Dependency: Product metrics dashboard (Recommendation 11) provides the adoption data inputs for the customer success reporting. |
| **Business Impact** | Customer success reduces churn risk (the NBFC customer concentration is a serious revenue risk if that customer churns), enables expansion revenue, and provides the documented performance evidence that supports both new customer sales and investor due diligence. |
| **Success Criteria** | 1. Written onboarding process document submitted. 2. Monthly adoption report template submitted with sample data from at least one active customer. 3. Evidence of at least one completed QBR (meeting notes or customer communication submitted). |
| **Next Evaluation Trigger** | Cycle-based. |

---

**Recommendation 16 of 18**

| Attribute | Value |
|---|---|
| **Rec ID** | `TAES-REC-NL0042-01-RK-002` |
| **Title** | Conduct a cybersecurity risk assessment by a qualified third-party firm and implement priority findings within 120 days |
| **Category** | Regulatory and Compliance Tasks |
| **Priority** | Medium |
| **Pillar** | Risk |
| **Sub-Criterion** | `RK-SC-03: Cybersecurity and Data Security Risk` |
| **Evidence Basis** | RK-SC-03 scored 4.0/10. NeuralLend processes sensitive financial data. No cybersecurity assessment has been conducted. No documented security policy exists. RBI-regulated lender customers are required by RBI guidelines to assess the cybersecurity posture of their third-party technology vendors. |
| **Current State** | No cybersecurity assessment. No documented security policy. Security practices are informal and undocumented. |
| **Desired State** | A third-party cybersecurity risk assessment is completed, covering application security, data security, access controls, incident response, and vendor risk. Priority findings are remediated and a security policy is documented and implemented. |
| **Expected Score Improvement** | +0.6 to +0.9 points on Risk Pillar |
| **Estimated Effort** | Significant |
| **Timeline** | Engage cybersecurity firm within 30 days. Assessment complete within 90 days. Priority findings remediated within 120 days. |
| **Dependencies** | Dependency: Regulatory mapping (Recommendation 2) identifies the specific cybersecurity standards applicable to fintech data processors; this recommendation should follow that mapping. |
| **Business Impact** | Cybersecurity assessment is a contractual requirement in enterprise vendor agreements for RBI-regulated institutions. Without it, NeuralLend cannot pass vendor risk assessments for its target customer segment. |
| **Success Criteria** | 1. Third-party cybersecurity assessment report submitted. 2. A remediation plan for all high and critical findings submitted. 3. Evidence of completion of at least 70% of high-priority findings within 120 days. 4. A documented security policy submitted. |
| **Next Evaluation Trigger** | Condition-based: upon execution of next enterprise customer agreement. |

---

**Recommendation 17 of 18**

| Attribute | Value |
|---|---|
| **Rec ID** | `TAES-REC-NL0042-01-PR-002` |
| **Title** | Trademark the "NeuralLend" brand name and primary product logo in India and UAE within 60 days |
| **Category** | IP Tasks |
| **Priority** | Medium |
| **Pillar** | IP |
| **Sub-Criterion** | `IP-SC-04: Trademark Protection` |
| **Evidence Basis** | IP-SC-04 scored 3.5/10. No trademark filings exist for the brand name or product logo. The startup is planning UAE expansion. Trademark registration in target markets is a standard pre-expansion step. |
| **Current State** | No trademark protection in India or internationally. Brand name and logo are unprotected. |
| **Desired State** | Trademark applications filed for "NeuralLend" word mark and primary logo in India (CGPDTM) and UAE (MOCCAE/ESMA) in relevant Nice Classification classes. |
| **Expected Score Improvement** | +0.4 to +0.6 points on IP Pillar |
| **Estimated Effort** | Minimal to Moderate |
| **Timeline** | Engage trademark attorney within 14 days. Applications filed within 60 days. |
| **Dependencies** | Dependency: IP ownership audit (Recommendation 10) should confirm that the brand name and logo are unambiguously owned by the company before filing. Resource: Trademark attorney (estimated ₹25,000–₹50,000 per jurisdiction for filing). |
| **Business Impact** | Trademark protection prevents brand squatting in expansion markets and is a standard investor due diligence item for consumer-facing and B2B brand-dependent businesses. |
| **Success Criteria** | 1. Trademark application acknowledgements from CGPDTM (India) and MOCCAE (UAE) submitted to the platform. 2. Application numbers and filing dates documented. |
| **Next Evaluation Trigger** | Cycle-based. |

---

#### LOW PRIORITY ACTIONS

---

**Recommendation 18 of 18**

| Attribute | Value |
|---|---|
| **Rec ID** | `TAES-REC-NL0042-01-MK-003` |
| **Title** | Develop and publish two customer case studies from existing customers within 90 days |
| **Category** | Go-To-Market Tasks |
| **Priority** | Low |
| **Pillar** | Market |
| **Sub-Criterion** | `MK-SC-04: Reference Customer Programme` |
| **Evidence Basis** | MK-SC-04 scored 5.0/10. No published case studies exist. The two existing customers have not been developed into reference relationships. The evaluation notes that verbal reference potential exists but is not yet formalised or documented. |
| **Current State** | No case studies. No published reference customer evidence. |
| **Desired State** | Two written case studies published (on website and available as sales collateral), covering the problem addressed, NeuralLend's solution, the implementation process, and quantified outcomes (e.g., reduction in NPAs, improvement in credit decision speed, reduction in credit assessment cost). |
| **Expected Score Improvement** | +0.3 to +0.5 points on Market Pillar |
| **Estimated Effort** | Minimal |
| **Timeline** | Initiate customer engagement within 45 days. Case studies produced and published within 90 days. |
| **Dependencies** | None. Note: customer approval of case study content will require appropriate relationship management time. |
| **Business Impact** | Case studies are sales collateral that reduce the buying decision effort for prospective enterprise customers in the same sector. They also provide evidence of commercial traction for investor presentations. |
| **Success Criteria** | 1. Two published case studies (URL or document) submitted to the platform. 2. Each case study includes: customer name (or anonymised with customer consent), problem statement, solution deployed, implementation timeline, and at least two quantified outcomes. 3. Customer sign-off on case study content documented. |
| **Next Evaluation Trigger** | Cycle-based. |

---

### Roadmap Summary — NeuralLend Technologies Pvt. Ltd.

**Evaluation Cycle 01 | Overall TAES Score: 4.8 / 10.0**
**Projected Score After Full Implementation: 7.6 – 8.2 / 10.0**
**Total Projected Improvement: +2.8 to +3.4 points**

| Phase | Window | Actions | Key Deliverables |
|---|---|---|---|
| Critical | Month 0–1 | 4 | Financial model, regulatory mapping, patent filing, CRO hire |
| High | Month 1–3 | 8 | Model validation, 2 new customers, unit economics, advisory board, reporting, IP audit, product roadmap, DPIIT registration |
| Medium | Month 3–6 | 5 | FTO analysis, ICP, customer success, cybersecurity, trademarks |
| Low | Month 3+ | 1 | Case studies |

---

## Agent Interaction Model

The TIDES Recommendation Engine is not a standalone component — it receives structured inputs from a set of specialist AI agents whose domain-specific analysis provides the evidence base from which recommendations are generated. The following table defines which agents contribute inputs to which recommendation categories and which evaluation pillars.

| Recommendation Category | Primary Contributing Agents | Pillar Coverage | Nature of Agent Contribution |
|---|---|---|---|
| Quick Wins | Document Analysis Agent, Compliance Check Agent | All pillars (documentation gaps) | Identifies missing, incomplete, or inconsistent documents that can be remediated without structural change |
| Medium-Term Improvements | Product Evaluation Agent, Market Intelligence Agent, Financial Analysis Agent | Product, Market, Business Model, Financial | Identifies capability gaps requiring structured development: product features, market research, financial modelling |
| Long-Term Improvements | Technology Evaluation Agent, Market Intelligence Agent, Strategic Assessment Agent | Technology, Market, Business Model | Identifies systemic capability gaps requiring sustained strategic investment |
| Investment Readiness Tasks | Financial Analysis Agent, Governance Review Agent, IP Assessment Agent | Financial, IP, Founder, Business Model | Identifies investor due diligence gaps against a standard Series A/B due diligence framework |
| TRL Advancement Tasks | Technology Evaluation Agent, R&D Assessment Agent | Technology | Maps current TRL evidence against next TRL milestone requirements and generates specific milestone tasks |
| Fundraising Tasks | Financial Analysis Agent, Governance Review Agent, Legal Compliance Agent | Financial, Founder, Business Model | Identifies mechanical, legal, and documentation prerequisites for a clean fundraise process |
| IP Tasks | IP Assessment Agent, Legal Compliance Agent, Technology Evaluation Agent | IP, Technology | Identifies IP protection gaps, ownership risks, and FTO exposure; generates filing, policy, and strategy recommendations |
| Hiring Tasks | Founder Evaluation Agent, Organisational Assessment Agent | Founder, Technology, Market | Identifies team composition gaps against a stage-appropriate capability model; generates role-specific hiring recommendations |
| Go-To-Market Tasks | Market Intelligence Agent, Revenue Analysis Agent, Customer Traction Agent | Market, Business Model | Identifies commercial execution gaps — pipeline, channel, pricing, customer success — and generates specific GTM actions |
| Regulatory and Compliance Tasks | Legal Compliance Agent, Risk Assessment Agent, Sector Regulation Agent | Risk, Financial, Market | Identifies regulatory exposure by sector and jurisdiction; generates specific compliance action items against applicable regulatory frameworks |

**Agent Contribution Protocol:**

Each contributing agent outputs a structured assessment record for its domain. The Recommendation Engine's synthesis layer ingests these records, identifies sub-criteria with scores below threshold, and generates candidate recommendations for each gap. The synthesis layer then applies the prioritisation logic from Section 3, de-duplicates candidate recommendations using the non-duplication test from Section 7.4, enforces the quality standards from Section 7, and produces the final ranked Roadmap.

The synthesis layer does not generate recommendations autonomously. It applies the recommendation templates defined in this standard to the agent-provided evidence and scores, populating each attribute from the structured data provided by the contributing agents. The evaluator team reviews the draft Roadmap before finalisation, exercising professional judgment on achievability, specificity, and contextual appropriateness — particularly for recommendations where context-specific knowledge (startup relationships, market dynamics, recent regulatory developments) may affect the recommendation's validity.

The final Roadmap is the output of this human-AI collaborative process. The agents provide the evidence and scale the analysis across all scoring dimensions. The evaluator team applies the domain judgment that ensures recommendations meet the quality standards this document requires.

---

*End of Document*

---

> **Document Control**
> | Version | Date | Author | Change Summary |
> |---|---|---|---|
> | 1.0.0 | 2026-03-01 | TIDES Platform Standards Committee | Initial release |
> | 1.1.0 | 2026-06-24 | TIDES Platform Standards Committee | Added agent interaction model; expanded Section 4 worked examples; updated prioritisation formula; added carry-forward rules |

> **Related Documents**
> - TAES v1.1 / Document 01: Evaluation Framework Overview
> - TAES v1.1 / Document 04: Scoring Rubric and Sub-Criterion Definitions
> - TAES v1.1 / Document 06: Report Structure and Output Standards
> - TAES v1.1 / Document 08: Evaluation Cycle Management
