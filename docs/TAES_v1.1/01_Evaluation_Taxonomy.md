> **Document:** TAES v1.1 / Evaluation Taxonomy
> **Classification:** Internal Technical Standard
> **Version:** 1.1.0
> **Status:** Ratified
> **Maintained By:** TIDES Standards Committee
> **Effective Date:** 2026-06-24
> **Review Cycle:** Annual (next review: 2027-06-01)
> **Document ID:** TAES-TAX-001

---

# TIDES AI Evaluation Standard — Evaluation Taxonomy
## TAES v1.1 | 01 — Evaluation Taxonomy Reference

---

## Table of Contents

1. [Purpose and Scope](#1-purpose-and-scope)
2. [What Is an Evaluation Taxonomy?](#2-what-is-an-evaluation-taxonomy)
3. [Taxonomy vs. Rubric: A Critical Distinction](#3-taxonomy-vs-rubric-a-critical-distinction)
4. [Why a Formal Taxonomy Precedes Scoring Design](#4-why-a-formal-taxonomy-precedes-scoring-design)
5. [Master Taxonomy Tree — All 19 Domains](#5-master-taxonomy-tree--all-19-domains)
6. [Cross-Domain Relationship Map](#6-cross-domain-relationship-map)
7. [How the Taxonomy Governs AI Agent Specialisation](#7-how-the-taxonomy-governs-ai-agent-specialisation)
8. [Taxonomy Versioning and Extension Protocol](#8-taxonomy-versioning-and-extension-protocol)
9. [Domain Specifications](#9-domain-specifications)
   - [Domain 01: Founder](#domain-01-founder)
   - [Domain 02: Product](#domain-02-product)
   - [Domain 03: Technology](#domain-03-technology)
   - [Domain 04: TRL (Technology Readiness Level)](#domain-04-trl-technology-readiness-level)
   - [Domain 05: Market](#domain-05-market)
   - [Domain 06: Business Model](#domain-06-business-model)
   - [Domain 07: Financial](#domain-07-financial)
   - [Domain 08: Intellectual Property](#domain-08-intellectual-property)
   - [Domain 09: Competition](#domain-09-competition)
   - [Domain 10: Go-To-Market](#domain-10-go-to-market)
   - [Domain 11: Operations](#domain-11-operations)
   - [Domain 12: Legal](#domain-12-legal)
   - [Domain 13: Risk](#domain-13-risk)
   - [Domain 14: ESG](#domain-14-esg)
   - [Domain 15: Scalability](#domain-15-scalability)
   - [Domain 16: Investment Readiness](#domain-16-investment-readiness)
   - [Domain 17: Incubation Readiness](#domain-17-incubation-readiness)
   - [Domain 18: Commercial Readiness](#domain-18-commercial-readiness)
   - [Domain 19: Innovation](#domain-19-innovation)

---

## 1. Purpose and Scope

This document constitutes the canonical Evaluation Taxonomy for the TIDES AI Evaluation Standard (TAES) version 1.1. It defines the complete hierarchical structure through which every startup, deep-tech venture, or innovation-stage company is evaluated within the TIDES intelligence layer.

The taxonomy is an **intelligence-layer artefact**. It is implementation-independent: it contains no scoring algorithms, no prompting strategies, no API references, and no code. Its sole function is to establish what must be evaluated, organised into a named, versioned, and traversable hierarchy that all downstream components — scoring engines, AI agents, analyst interfaces, and governance committees — must reference as authoritative.

**Scope of applicability:** This taxonomy applies to all TIDES evaluation contexts including:
- IIT incubator and accelerator programme assessments
- Government grant and innovation fund diligence
- Venture capital and angel investment screening
- Technology transfer office (TTO) commercialisation assessments
- National innovation ecosystem benchmarking

**Out of scope:** This document does not specify scoring weights, evaluation rubrics, interview question banks, data collection methodologies, or AI model selection. Those are governed by separate TAES documents in the same document series.

---

## 2. What Is an Evaluation Taxonomy?

An **evaluation taxonomy** is a formal, hierarchical classification system that organises all evaluative dimensions of a subject domain into a structured tree of named nodes. In the context of startup evaluation, a taxonomy answers the foundational question: *What are all the things we must examine, and how do they relate to one another?*

A taxonomy has three structural properties that distinguish it from other classification schemes:

**2.1 Hierarchical Containment**
Every node in the taxonomy belongs to exactly one parent node (except root nodes, which are the 19 top-level domains). A child node is always a specific, refinable sub-dimension of its parent. For example, "Execution" is a child of "Founder" because execution capability is a specific dimension of the broader founder assessment. This containment relationship is strict: no node may belong to two parents simultaneously, although cross-domain *relationships* (distinct from containment) are permitted and documented.

**2.2 Mutual Exclusivity at Peer Level**
Peer nodes (nodes sharing the same parent) must be definitionally distinct. "Leadership" and "Execution" are both children of "Founder" and are deliberately defined so that evidence of one does not automatically constitute evidence of the other. This property ensures that no single piece of evidence can be double-counted within the same parent dimension.

**2.3 Collective Exhaustiveness Within Scope**
The set of children under any parent node must collectively cover the full evaluative scope of that parent. If a dimension is not named in the taxonomy, it cannot be evaluated. This constraint forces explicit, pre-deliberated decisions about what the evaluation system considers relevant — preventing ad hoc, inconsistent evaluation in practice.

A taxonomy does **not** assign scores. It does not prescribe evidence types by itself. It does not rank dimensions by importance. All of those functions belong to downstream TAES documents that reference this taxonomy by node name.

---

## 3. Taxonomy vs. Rubric: A Critical Distinction

These two terms are frequently conflated in startup evaluation practice. The distinction is foundational to TAES design.

| Property | Taxonomy | Rubric |
|---|---|---|
| **Primary question answered** | What do we evaluate? | How well does this startup perform on dimension X? |
| **Output** | A named, hierarchical structure of dimensions | Performance levels, scoring bands, or rating scales |
| **Quantitative content** | None | Explicit (scores, weights, thresholds) |
| **Stability** | High — changes require formal versioning | Moderate — may be tuned per cohort or sector |
| **Dependency direction** | Foundational — rubrics depend on taxonomy | Derivative — rubrics reference taxonomy nodes by name |
| **Ownership** | Standards Committee | Evaluation Engineering Team |
| **Version cadence** | Annual | Per evaluation cycle or fund |
| **Scope** | Universal across all TIDES evaluation contexts | Specific to a programme, sector, or stage |

A rubric without a taxonomy produces inconsistent evaluations: different evaluators assess different things, use different definitions, and cannot be aggregated or compared. A taxonomy without a rubric is incomplete but consistent — it defines the space of evaluation without making judgements. TAES mandates that the taxonomy be ratified before any rubric is developed for any evaluation programme.

---

## 4. Why a Formal Taxonomy Precedes Scoring Design

The requirement that a formal taxonomy be established before scoring is designed is not administrative convention — it is an epistemic necessity. The following reasons are operative in TAES:

**4.1 Scoring Requires Defined Units**
A score is only meaningful if it attaches to a precisely defined evaluative unit. "Rate the founder out of 10" is not a score — it is noise. "Rate the founder's demonstrated ability to recruit senior technical talent (Domain 01 > Team Building > Senior Talent Acquisition) on a 5-point scale" is a score. The taxonomy provides the units.

**4.2 AI Agent Specialisation Requires Domain Boundaries**
TIDES deploys specialised AI agents for each evaluation domain. For an agent to be trained, prompted, validated, and monitored, it must have a fixed scope of responsibility. The taxonomy defines that scope. Without it, agent scope boundaries are undefined, leading to duplication, gaps, and undetectable coverage failures.

**4.3 Cross-Domain Analysis Requires Named Nodes**
Many of the most important insights in startup evaluation emerge from relationships between domains: a founder's technical competence (Domain 01) intersects with technology differentiation (Domain 03); market sizing (Domain 05) constrains financial projections (Domain 07). These cross-domain relationships can only be formally stated if both nodes are named. The taxonomy enables relationship mapping as a first-class operation.

**4.4 Governance and Auditability**
Any evaluation that informs investment, grant allocation, or incubation selection carries a duty of explainability. Regulatory and governance requirements demand that every score be traceable to a named, defined dimension. The taxonomy creates that audit trail.

**4.5 Longitudinal Comparability**
Startups are evaluated at multiple stages: pre-seed, seed, Series A, post-incubation. For progress to be measured, the same taxonomy must be in use across all evaluations of the same entity. A versioned taxonomy enables structured comparison across time without definitional drift.

---

## 5. Master Taxonomy Tree — All 19 Domains

The following ASCII tree presents all 19 evaluation domains and their top-level sub-dimensions. This is the primary reference for domain scope. Nested children (third-level nodes) are shown in domain specification sections.

```
TAES v1.1 EVALUATION TAXONOMY
│
├─ D01 FOUNDER
│   ├─ Leadership
│   ├─ Execution
│   ├─ Vision
│   ├─ Technical Competence
│   ├─ Domain Expertise
│   ├─ Communication
│   ├─ Adaptability
│   ├─ Team Building
│   ├─ Learning Ability
│   └─ Commitment
│
├─ D02 PRODUCT
│   ├─ Problem Definition
│   ├─ Solution Architecture
│   ├─ Product-Market Fit
│   ├─ User Experience
│   ├─ Feature Completeness
│   ├─ Product Differentiation
│   ├─ Development Velocity
│   ├─ Feedback Integration
│   ├─ Product Roadmap
│   └─ Dependency Risk
│
├─ D03 TECHNOLOGY
│   ├─ Technical Architecture
│   ├─ Core Innovation
│   ├─ Technology Differentiation
│   ├─ Engineering Quality
│   ├─ Technology Stack
│   ├─ Data Strategy
│   ├─ Security & Privacy
│   ├─ Technical Debt
│   ├─ Infrastructure Resilience
│   └─ Technical Team Capability
│
├─ D04 TRL (Technology Readiness Level)
│   ├─ TRL Classification
│   ├─ Validation Evidence
│   ├─ Prototype Maturity
│   ├─ Operational Environment Testing
│   ├─ System Integration
│   ├─ Deployment Readiness
│   ├─ TRL Advancement Trajectory
│   └─ External TRL Verification
│
├─ D05 MARKET
│   ├─ Total Addressable Market
│   ├─ Serviceable Addressable Market
│   ├─ Serviceable Obtainable Market
│   ├─ Market Growth Rate
│   ├─ Market Segmentation
│   ├─ Customer Profile Definition
│   ├─ Market Timing
│   ├─ Market Entry Barriers
│   ├─ Demand Validation
│   └─ Regulatory Environment
│
├─ D06 BUSINESS MODEL
│   ├─ Revenue Model
│   ├─ Value Proposition
│   ├─ Customer Acquisition Strategy
│   ├─ Cost Structure
│   ├─ Pricing Strategy
│   ├─ Revenue Diversification
│   ├─ Unit Economics
│   ├─ Partnership Architecture
│   ├─ Monetisation Timing
│   └─ Business Model Resilience
│
├─ D07 FINANCIAL
│   ├─ Financial Projections
│   ├─ Current Financial Position
│   ├─ Burn Rate & Runway
│   ├─ Revenue Traction
│   ├─ Funding History
│   ├─ Capital Efficiency
│   ├─ Financial Controls
│   ├─ Valuation Basis
│   ├─ Break-Even Analysis
│   └─ Financial Risk Exposure
│
├─ D08 INTELLECTUAL PROPERTY
│   ├─ Patent Portfolio
│   ├─ Trade Secrets
│   ├─ Copyright Holdings
│   ├─ Trademark Registration
│   ├─ IP Ownership Clarity
│   ├─ Freedom to Operate
│   ├─ IP Defensibility
│   ├─ Licensing Strategy
│   └─ Open Source Exposure
│
├─ D09 COMPETITION
│   ├─ Competitive Landscape Mapping
│   ├─ Differentiation Analysis
│   ├─ Competitive Moat
│   ├─ Incumbent Threat Assessment
│   ├─ Substitute Product Risk
│   ├─ Competitive Intelligence Process
│   ├─ Positioning Strategy
│   ├─ Market Share Trajectory
│   └─ Alliance and Partnership Landscape
│
├─ D10 GO-TO-MARKET
│   ├─ GTM Strategy Definition
│   ├─ Sales Channel Architecture
│   ├─ Marketing Strategy
│   ├─ Early Customer Pipeline
│   ├─ Partnership-Driven Distribution
│   ├─ Brand Development
│   ├─ Pricing Communication
│   ├─ Customer Onboarding Process
│   ├─ GTM Metrics & KPIs
│   └─ Expansion Sequencing
│
├─ D11 OPERATIONS
│   ├─ Operational Process Design
│   ├─ Supply Chain & Vendor Management
│   ├─ Quality Assurance
│   ├─ Human Resources Management
│   ├─ Resource Allocation
│   ├─ Operational Technology
│   ├─ Delivery & Fulfilment
│   ├─ Knowledge Management
│   └─ Operational Risk Controls
│
├─ D12 LEGAL
│   ├─ Corporate Structure
│   ├─ Regulatory Compliance
│   ├─ Contracts & Agreements
│   ├─ Employment Law Compliance
│   ├─ Data Protection & Privacy
│   ├─ Founder Agreement Integrity
│   ├─ Litigation Exposure
│   └─ Licensing & Permits
│
├─ D13 RISK
│   ├─ Market Risk
│   ├─ Technology Risk
│   ├─ Execution Risk
│   ├─ Financial Risk
│   ├─ Regulatory Risk
│   ├─ Key Person Risk
│   ├─ Geopolitical Risk
│   ├─ Reputational Risk
│   └─ Scenario Planning Capability
│
├─ D14 ESG
│   ├─ Environmental Impact
│   ├─ Carbon & Resource Footprint
│   ├─ Social Impact
│   ├─ Labour Practices
│   ├─ Governance Structure
│   ├─ Ethical AI & Technology Use
│   ├─ Diversity & Inclusion
│   └─ ESG Reporting Maturity
│
├─ D15 SCALABILITY
│   ├─ Revenue Scalability
│   ├─ Technology Scalability
│   ├─ Operational Scalability
│   ├─ Team Scalability
│   ├─ Geographic Scalability
│   ├─ Unit Economics at Scale
│   ├─ Platform Leverage
│   └─ Scalability Risk Factors
│
├─ D16 INVESTMENT READINESS
│   ├─ Pitch Quality
│   ├─ Investor Documentation
│   ├─ Due Diligence Preparedness
│   ├─ Cap Table Structure
│   ├─ Term Sheet Literacy
│   ├─ Investor Relations Strategy
│   ├─ Use of Funds Clarity
│   └─ Prior Investor Credibility
│
├─ D17 INCUBATION READINESS
│   ├─ Programme Alignment
│   ├─ Mentorship Receptivity
│   ├─ Resource Utilisation Capability
│   ├─ Milestone Commitment
│   ├─ Peer Collaboration Disposition
│   ├─ Coachability
│   ├─ Structured Reporting Capability
│   └─ Post-Incubation Sustainability
│
├─ D18 COMMERCIAL READINESS
│   ├─ Sales Capability
│   ├─ Revenue Realisation
│   ├─ Enterprise Readiness
│   ├─ Customer Success Infrastructure
│   ├─ Contract & Procurement Readiness
│   ├─ Pricing Operationalisation
│   ├─ Distribution Infrastructure
│   └─ Commercial Team Maturity
│
└─ D19 INNOVATION
    ├─ Novelty
    ├─ Inventive Step
    ├─ Problem-Solution Originality
    ├─ Technology Frontier Positioning
    ├─ Cross-Domain Innovation
    ├─ Innovation Process Maturity
    ├─ Disruptive Potential
    ├─ Research & Development Depth
    └─ Innovation Ecosystem Engagement
```

---

## 6. Cross-Domain Relationship Map

Domains do not exist in isolation. The following matrix and narrative identify the most tightly coupled domain pairs and explain the nature of their interdependency. These relationships inform how cross-domain synthesis agents combine domain-level outputs into unified evaluation signals.

### 6.1 Coupling Matrix (Primary Relationships)

| Domain | Most Tightly Coupled To | Nature of Coupling |
|---|---|---|
| D01 Founder | D03 Technology, D11 Operations, D15 Scalability | Founder capability is the proximate cause of technology and operational quality; scalability is bounded by founder capacity to build teams |
| D02 Product | D05 Market, D06 Business Model, D10 GTM | Product definition determines which market is addressed; business model and GTM are derivative of product architecture |
| D03 Technology | D04 TRL, D08 IP, D15 Scalability | Technology maturity is measured by TRL; IP is built on technology; scalability depends on technical architecture |
| D04 TRL | D03 Technology, D18 Commercial Readiness | TRL level directly gates commercial deployment readiness |
| D05 Market | D06 Business Model, D09 Competition, D10 GTM | Market size and structure determine revenue model viability and competitive dynamics |
| D06 Business Model | D07 Financial, D15 Scalability, D18 Commercial | Business model determines unit economics and financial projections |
| D07 Financial | D06 Business Model, D16 Investment Readiness | Financial health and projections are central to investment decisions |
| D08 IP | D03 Technology, D09 Competition | IP portfolio defines defensibility against competitors and underpins technology moat |
| D09 Competition | D05 Market, D08 IP, D10 GTM | Competitive landscape shapes GTM channel choices and IP strategy |
| D10 GTM | D06 Business Model, D05 Market, D18 Commercial | GTM execution converts business model assumptions into commercial revenue |
| D11 Operations | D01 Founder, D15 Scalability | Operational maturity is a function of founder execution; operations must scale with revenue |
| D12 Legal | D08 IP, D06 Business Model | Legal structure governs IP ownership and enforceability of business model contracts |
| D13 Risk | All Domains | Risk is a meta-domain: risks are sourced from weaknesses in all other domains |
| D14 ESG | D12 Legal, D11 Operations | ESG compliance intersects with legal obligations and operational practices |
| D15 Scalability | D03 Technology, D06 Business Model, D11 Operations | Scalability depends on architecture, model economics, and operational systems |
| D16 Investment Readiness | D07 Financial, D01 Founder, D02 Product | Investor confidence is a function of financial clarity, founder quality, and product evidence |
| D17 Incubation Readiness | D01 Founder, D11 Operations | Incubation benefit depends on founder coachability and operational baseline |
| D18 Commercial Readiness | D04 TRL, D10 GTM, D06 Business Model | Commercial deployment requires sufficient TRL, an active GTM strategy, and a viable model |
| D19 Innovation | D03 Technology, D08 IP, D04 TRL | Innovation quality is evidenced through technical differentiation, IP, and TRL advancement |

### 6.2 Primary Causal Chains

Three structural causal chains run through the taxonomy. These represent the highest-leverage relationships in startup evaluation:

**Chain 1: Founder → Technology → TRL → Commercial Readiness**
The founder's technical competence drives the quality and depth of the core technology. Technology quality determines TRL advancement pace. TRL level gates commercial readiness. Weaknesses anywhere in this chain propagate forward into commercial failure.

**Chain 2: Market → Business Model → Financial → Investment Readiness**
Market size and structure define what business models are viable. The business model determines financial architecture. Financial performance and projections determine investment readiness. Overestimated markets cascade into unrealistic financial models and unjustifiable valuations.

**Chain 3: IP → Competition → Go-To-Market → Commercial Readiness**
IP portfolio defines competitive moat. The strength of the moat influences GTM channel selection (direct vs. partner vs. platform). GTM execution determines whether commercial readiness is achieved at scale. Weak IP leaves GTM vulnerable to competitive displacement.

---

## 7. How the Taxonomy Governs AI Agent Specialisation

TIDES deploys a network of specialised AI evaluation agents. Each agent is responsible for one or more taxonomy domains. The taxonomy is the governance document that defines agent scope, input requirements, output contracts, and escalation protocols.

### 7.1 Agent-to-Domain Assignment Principles

Each domain requires a specialised agent because the evidence types, reasoning patterns, and knowledge bases required differ substantially across domains. A Founder evaluation agent must reason about human capital signals, interview transcripts, and track record artefacts. A TRL evaluation agent must reason about technical specifications, prototype test reports, and validation evidence. No single general-purpose agent can maintain the evaluation precision required by TAES across all 19 domains simultaneously.

Assignment follows these principles:
- **One primary domain per agent minimum.** No domain is left without an assigned agent.
- **Grouped assignments for related domains.** Where two domains share heavy evidence overlap (e.g., D03 Technology and D04 TRL), a single specialised agent may cover both, provided domain outputs are produced independently.
- **No agent cross-contaminates domain outputs.** An agent assigned to Domain 03 must not allow Domain 05 reasoning to alter its Domain 03 output. Cross-domain synthesis is performed by a dedicated Synthesis Agent layer.

### 7.2 Standard Agent Input/Output Contract

Every domain agent operates under a contract defined by this taxonomy:

| Contract Element | Definition |
|---|---|
| **Input scope** | Only artefacts relevant to the assigned domain's leaf-node evidence sources |
| **Output format** | One structured evaluation record per taxonomy node evaluated, containing: node path, score or flag, evidence citations, confidence level, and gap flags |
| **Escalation trigger** | When evidence is absent, contradictory, or below confidence threshold for any leaf node |
| **Handoff protocol** | Domain agent output is passed to the Synthesis Agent by domain code (e.g., "D01", "D07") — never by agent name |
| **Versioning lock** | Each agent run records the taxonomy version (e.g., TAES-TAX-001 v1.1.0) used to define its scope |

### 7.3 Taxonomy Changes and Agent Re-Scoping

When a new sub-dimension is added to the taxonomy (per the versioning protocol in Section 8), the affected domain agent must be re-scoped before any evaluation using the new taxonomy version is conducted. The agent scope document (a separate operational artefact) references taxonomy node paths as its authoritative scope definition. This ensures that agent scope automatically inherits taxonomy changes through the versioned reference.

---

## 8. Taxonomy Versioning and Extension Protocol

The taxonomy is a living standard. Innovation ecosystems evolve, and new evaluation dimensions become relevant over time. The versioning protocol ensures that the taxonomy can grow without breaking existing evaluations.

### 8.1 Version Numbering

The taxonomy uses three-part semantic versioning: **MAJOR.MINOR.PATCH**

| Version Part | Change Type | Example Trigger |
|---|---|---|
| **MAJOR** | Structural redesign — domains added, removed, or renamed | A 20th domain "Quantum Readiness" is added |
| **MINOR** | Sub-dimension additions or redefinitions at any level | A new leaf node "AI Governance Maturity" is added under D14 ESG |
| **PATCH** | Clarifications, definition refinements, cross-reference corrections | A "Why It Matters" statement is updated for factual accuracy |

MAJOR version changes require full Standards Committee ratification. MINOR version changes require a sub-committee review and a 30-day consultation period. PATCH changes require approval from the document owner only.

### 8.2 Extension Rules

New sub-dimensions may be added under any existing parent node subject to the following rules:

1. **Definitional uniqueness:** The proposed new node must not overlap in definition with any existing peer node under the same parent.
2. **Exhaustiveness preservation:** Adding a node must not leave a gap — if the existing set of children was exhaustive before, the new node must address a dimension not previously covered, not subdivide an existing node without deprecating it.
3. **Leaf node specification completeness:** Any new leaf node must carry the full eight-element specification (Definition, Purpose, Why It Matters, Dependencies, Relationships, Evidence Sources, Red Flags, Expected Outputs) before the version increment is ratified.
4. **Backward compatibility:** Existing node paths (e.g., `D01 > Team Building`) must not be renamed in a MINOR version increment. Renaming requires a MAJOR version.
5. **Deprecation, not deletion:** A node that is no longer relevant is marked `[DEPRECATED: vX.X.X]` and retained in the taxonomy for one full MAJOR version cycle before removal. Deprecated nodes may not be scored but must remain in the taxonomy for auditability of historical evaluations.

### 8.3 Node Path Notation

Each node is uniquely identified by its path. Path notation uses the domain code, followed by the sub-dimension chain, separated by the `>` operator:

```
D01 > Team Building > Senior Talent Acquisition
D07 > Burn Rate & Runway > Cash Runway Months
D14 > ESG Reporting Maturity > GRI Framework Alignment
```

This path notation is used in: agent scope documents, scoring rubrics, evaluation reports, cross-domain relationship references, and all audit trail records.

---

## 9. Domain Specifications

---

### DOMAIN 01: FOUNDER

**Domain Definition:** The Founder domain evaluates the human capital at the leadership apex of the startup. It assesses whether the individuals responsible for the venture's direction, decisions, and execution possess the capabilities required to navigate the full lifecycle from ideation through scale. Founder quality is treated as the single highest-leverage variable in early-stage startup evaluation because all other domains are, in the short run, expressions of founder capability.

**Domain Scope:** Individual founders and co-founding teams. Where a professional CEO has replaced a founding CEO post-Series A, both profiles are evaluated under this domain.

**Domain Tree:**
```
D01 FOUNDER
├─ Leadership
├─ Execution
├─ Vision
├─ Technical Competence
├─ Domain Expertise
├─ Communication
├─ Adaptability
├─ Team Building
├─ Learning Ability
└─ Commitment
```

---

#### D01 > Leadership

**Definition:** Leadership measures the founder's demonstrated capacity to set direction, inspire alignment, make decisions under uncertainty, and sustain team cohesion through adversity. It encompasses both strategic leadership (setting the right direction) and operational leadership (ensuring the team moves in that direction).

**Purpose:** Investors and evaluators use leadership signals to predict whether the founding team can hold an organisation together through the inevitable crises of early-stage growth — talent departures, pivot decisions, funding gaps, and competitive shocks.

**Why It Matters:** A startup with weak founder leadership will fragment under stress. Team members lose confidence, make localised decisions that conflict with company direction, and attrition accelerates. No product quality, market size, or technology advantage can compensate for a leadership vacuum at the founding level.

**Dependencies:** Depends on `D01 > Vision` (leaders must have a clear direction to lead toward); depends on `D01 > Communication` (leadership is expressed through communication); depends on `D01 > Commitment` (sustained leadership requires committed founders).

**Relationships:** Directly influences `D11 > Operational Process Design` (leadership sets the operational culture); influences `D01 > Team Building` (leaders attract and retain talent); feeds into `D16 > Investment Readiness > Pitch Quality` (investor confidence correlates with perceived leadership strength).

**Evidence Sources:**
- Video or transcript of founder interviews demonstrating decision-making under hypothetical or real adversity
- References from former team members, investors, or colleagues attesting to leadership under pressure
- Documented instances of team conflict resolution or organisational pivots led by the founder
- Pitch deck narrative coherence as a proxy for directional clarity
- Team retention statistics over the startup's operating history

**Red Flags:**
- Founder cannot articulate a consistent strategic narrative across different conversations or documents
- Evidence of co-founder or senior hire departures attributed to leadership dysfunction
- Decision-making described as unilateral and not communicated to the team
- Founder deflects responsibility for past failures exclusively to external factors
- Board or advisory board reports of founder not acting on counsel received

**Expected Outputs:** A structured leadership profile scoring decision quality, team alignment maintenance, and crisis navigation capability on a 5-point scale per sub-criterion, accompanied by a qualitative narrative citing specific evidential instances and a confidence rating (High / Medium / Low) based on evidence depth.

---

#### D01 > Execution

**Definition:** Execution measures the founder's track record of translating plans into completed outcomes within defined timeframes and resource constraints. It is assessed through the quality and consistency of milestone achievement relative to commitments made.

**Purpose:** Execution is the mechanism by which vision converts into value. An evaluator uses execution history to distinguish between founders who are idea-generators and those who can operationalise ideas into products, customers, and revenue.

**Why It Matters:** Vision without execution produces no value. The primary failure mode of promising startups is not ideation failure but execution failure — the inability to build, ship, sell, and iterate within the constraints of capital and time.

**Dependencies:** Depends on `D01 > Commitment` (sustained effort is prerequisite to consistent execution); depends on `D11 > Operational Process Design` (execution quality reflects operational systems); depends on `D01 > Technical Competence` for technology-execution quality.

**Relationships:** Directly informs `D07 > Revenue Traction` (revenue is the output of execution); influences `D04 > TRL Advancement Trajectory` (TRL progress is an execution metric); informs `D16 > Due Diligence Preparedness` (well-executed startups produce better diligence artefacts).

**Evidence Sources:**
- Roadmap vs. actuals comparison: planned milestones versus achieved milestones with dates
- Product release history: frequency and completeness of delivered product updates
- Customer acquisition history vs. stated targets
- Prior venture or corporate role outcomes (exits, product launches, revenue milestones achieved)
- Investor update letters showing milestone reporting discipline

**Red Flags:**
- Repeated milestone slippage with no post-mortem or process correction
- Grandiose near-term commitments (e.g., "10 enterprise contracts in 60 days") with no operational plan
- No documented roadmap or milestone tracking system in place
- Prior ventures with unexplained early shutdowns and no retrospective learning evident
- Excessive time spent on pitching and fundraising relative to product and customer activity

**Expected Outputs:** An execution track record score (1–5) anchored to objective milestone delivery data, supplemented by a flag indicating whether the execution evidence is self-reported only (lower confidence) or third-party verified (higher confidence).

---

#### D01 > Vision

**Definition:** Vision measures the clarity, ambition, and internal consistency of the founder's understanding of the future state they are building toward, including the strategic rationale for why that future is both achievable and valuable.

**Purpose:** Vision serves as the strategic anchor for all product, market, and technology decisions. Evaluators assess vision to determine whether the founder has a coherent theory of change — a structured argument for why this startup will create a specific outcome in the world.

**Why It Matters:** A weak or incoherent vision leads to strategic drift: product decisions made without a unifying purpose, market entries that contradict each other, and team members who cannot explain the company's direction. Vision is also the primary instrument through which founders recruit talent and attract investors.

**Dependencies:** Depends on `D01 > Domain Expertise` (credible vision requires deep domain knowledge); depends on `D05 > Market Timing` (vision must be appropriately calibrated to market readiness).

**Relationships:** Feeds into `D02 > Product Roadmap` (product direction is derived from vision); influences `D09 > Positioning Strategy` (competitive positioning is an expression of vision); informs `D19 > Disruptive Potential` (transformative vision correlates with disruption potential).

**Evidence Sources:**
- Written vision statements in pitch decks, investor memos, or strategic documents
- Founder interviews probing the 5–10 year future state of the company and market
- Consistency of vision articulation across multiple documents and presentations over time
- Mission and values documentation showing how operational decisions trace to the stated vision
- Evidence of vision-product alignment: does the product roadmap logically serve the stated vision?

**Red Flags:**
- Vision statement is generic and applicable to hundreds of companies (e.g., "We want to democratise X")
- Vision changes fundamentally between pitch decks produced less than six months apart without explained pivots
- Founder cannot explain how today's MVP connects to the 10-year vision
- Vision is entirely technology-driven with no articulation of the human or market outcome being created
- Vision is implausibly large relative to the team, capital, and technology maturity

**Expected Outputs:** A vision coherence and ambition assessment, scored across three dimensions: specificity (is the vision precisely defined?), feasibility (is it achievable given known constraints?), and inspirational pull (does it attract talent and capital?). Output includes a narrative identifying the core strategic claim embedded in the vision.

---

#### D01 > Technical Competence

**Definition:** Technical competence measures the extent to which the founder — individually or through co-founders — possesses the engineering, scientific, or domain-specific technical knowledge required to make sound product and technology decisions without complete dependence on external contractors.

**Purpose:** In deep-tech and software startups, foundational technical decisions made in the first 12 months have multi-year consequences. Evaluators assess technical competence to determine whether the founding team can independently navigate those decisions.

**Why It Matters:** A non-technical founding team building a technical product is perpetually at the mercy of contractors or early engineers whose judgement they cannot independently assess. This creates a structural vulnerability: the company cannot evaluate the quality of its own core asset.

**Dependencies:** Depends on `D03 > Engineering Quality` (technical competence is validated through delivered engineering); depends on `D01 > Learning Ability` (technical competence must evolve with the technology landscape).

**Relationships:** Directly informs `D03 > Core Innovation` (technical competence enables genuine innovation); informs `D04 > TRL Classification` (technically competent founders make more accurate TRL self-assessments); feeds into `D08 > Patent Portfolio` (patent quality depends on founder technical depth).

**Evidence Sources:**
- Academic and professional credentials in relevant technical disciplines
- GitHub, publications, patents, or technical blog history demonstrating applied technical output
- Technical architecture documents authored by the founder
- Peer assessment from technical advisors or co-founders
- Quality and depth of technical questions posed and answered during technical due diligence interviews

**Red Flags:**
- No technical co-founder or CTO in a deep-tech venture, with all engineering outsourced
- Technical explanations during interviews are superficial, rely on buzzwords, or cannot be probed beyond surface level
- Founder cannot explain the trade-offs behind their core architecture choices
- Technical decisions are attributed entirely to a single contractor with no IP assignment
- Claimed technical credentials are unverifiable or misrepresented

**Expected Outputs:** A technical competence profile classifying the founding team as: Technically Led (founder is primary technical decision-maker), Technically Supported (technical co-founder or CTO in place), or Technically Dependent (all technical capability is external). Each classification carries different risk weights in downstream scoring.

---

#### D01 > Domain Expertise

**Definition:** Domain expertise measures the depth and currency of the founder's knowledge of the specific industry, problem space, or customer segment the startup operates in, as distinct from general technical or business competence.

**Purpose:** Domain expertise is the founder's primary source of asymmetric insight — the unfair knowledge advantage that allows them to see problems and solutions that outsiders miss. Evaluators assess it to determine whether the founder's opportunity identification is grounded in genuine insider knowledge.

**Why It Matters:** Founders lacking domain expertise consistently underestimate regulatory complexity, customer buying behaviour, sales cycle length, and incumbent inertia. These blind spots produce overly optimistic projections and strategies that fail at first contact with industry reality.

**Dependencies:** Depends on `D05 > Customer Profile Definition` (domain expertise is often expressed as deep customer understanding); depends on `D01 > Learning Ability` (domain knowledge must be continuously updated).

**Relationships:** Informs `D09 > Competitive Intelligence Process` (domain experts know where to find competitive signals); influences `D12 > Regulatory Compliance` (domain experts anticipate regulatory requirements); feeds `D05 > Market Timing` (domain experts sense timing signals that generalists miss).

**Evidence Sources:**
- Years of direct industry experience in a relevant role prior to founding
- Published articles, conference presentations, or advisory roles in the target domain
- Depth and accuracy of regulatory, customer, and competitive knowledge demonstrated in interviews
- Network quality within the target industry (advisors, customers, and channel partners drawn from the domain)
- Prior ventures or corporate initiatives in the same domain

**Red Flags:**
- Founder's only domain experience is as an end-user, not an industry insider or practitioner
- Domain claims are based on secondary research (reports, articles) rather than direct experience
- Stated customer pain points are generic and do not reflect the nuance of the actual buyer
- Competitive analysis misses major incumbents known to any industry practitioner
- Founder is entering the domain specifically because it is "hot" rather than because of deep prior engagement

**Expected Outputs:** A domain expertise classification (Deep: 5+ years direct experience; Moderate: 2–5 years or adjacent experience; Shallow: <2 years or only end-user perspective) with an evidence quality rating and a list of specific knowledge gaps identified during evaluation.

---

#### D01 > Communication

**Definition:** Communication measures the founder's ability to clearly and persuasively transmit complex ideas to diverse audiences — investors, customers, engineers, regulators, and media — adapting both content and style to the context and audience without sacrificing accuracy.

**Purpose:** Founders must continuously recruit: they recruit capital, talent, customers, and partners. Every one of these recruitment acts depends on communication quality. Evaluators assess communication to determine whether the founder can build the coalition required to reach scale.

**Why It Matters:** Poor communication creates ambiguity that cascades into misaligned teams, failed sales, and lost investment. Even technically superior products and well-reasoned strategies fail when founders cannot articulate them compellingly and precisely.

**Dependencies:** Depends on `D01 > Vision` (clear vision is prerequisite to clear communication); depends on `D01 > Domain Expertise` (credible communication requires command of the subject matter).

**Relationships:** Directly feeds `D16 > Pitch Quality`; influences `D10 > Brand Development` (founder narrative is the early brand); informs `D17 > Mentorship Receptivity` (communication skill enables productive mentorship engagement).

**Evidence Sources:**
- Pitch recording or live pitch observation with structured evaluation
- Written communications: investor updates, blog posts, whitepapers assessed for clarity and persuasion
- Customer-facing materials: sales decks, product demos, website copy
- Media interviews or public speaking appearances
- Team communication artefacts: internal memos, all-hands meeting recordings

**Red Flags:**
- Pitch deck is dense with jargon but cannot be explained simply when requested
- Written communications contain logical gaps or make claims without evidence
- Founder communicates differently (inconsistently) to different audiences in ways that suggest deception rather than adaptation
- Unable to summarise the company's value proposition in under 60 seconds
- Evidence of poor internal communication: team members describe unclear direction or conflicting instructions from leadership

**Expected Outputs:** A communication effectiveness rating across four contexts: investor communication, customer communication, team communication, and public communication. Each context is scored 1–5 with supporting evidence citations. A flag is raised where communication quality varies dramatically across contexts.

---

#### D01 > Adaptability

**Definition:** Adaptability measures the founder's demonstrated willingness and capability to revise strategy, product direction, team structure, or business model in response to new evidence, changing market conditions, or failed assumptions — while maintaining strategic coherence.

**Purpose:** The startup journey is fundamentally a process of iterative learning under uncertainty. Adaptability predicts survival through the inevitable wrong turns. Evaluators assess it to distinguish founders who pivot intelligently from those who are either rigidly committed to a failing plan or chaotically changing direction without learning.

**Why It Matters:** A founder who cannot adapt will pursue a failing strategy to exhaustion of capital. A founder who adapts too readily, without evidence-based triggers, produces organisational whiplash that destroys team trust and wastes resources. Calibrated adaptability is a survival trait.

**Dependencies:** Depends on `D01 > Learning Ability` (adaptation requires absorption and application of new information); depends on `D01 > Leadership` (adaptation decisions must be led, not imposed without context).

**Relationships:** Informs `D02 > Feedback Integration` (adaptability is expressed in how product feedback is acted upon); influences `D13 > Execution Risk` (adaptive founders mitigate execution risk through course correction); feeds `D06 > Business Model Resilience`.

**Evidence Sources:**
- Documented pivot history: what changed, why, what evidence triggered it, and what the outcome was
- Founder interviews probing hypothetical market or technical disruption scenarios
- Evidence of strategy revision in investor update letters
- Advisor or board references describing founder response to critical feedback
- Speed of response to COVID-19 or other external shock, if applicable to the startup's operating history

**Red Flags:**
- Founder has not changed any significant assumption since founding despite 18+ months of market data
- Pivots are frequent and without documented rationale — reactive rather than adaptive
- Founder dismisses negative customer feedback as customer ignorance rather than signal
- Board or advisor feedback systematically not acted upon
- Original pitch deck is identical to current pitch deck despite significant time elapsed

**Expected Outputs:** An adaptability profile scoring evidence-based pivot history, feedback responsiveness, and strategic flexibility. Includes a flag indicating whether past adaptations improved or worsened key metrics, providing a quality signal on adaptation judgment (not just willingness).

---

#### D01 > Team Building

**Definition:** Team building measures the founder's demonstrated ability to identify, recruit, onboard, retain, and develop the talent required to build and scale the startup, including the ability to attract people significantly more experienced than the founder in specific functions.

**Purpose:** No founder can build a significant company alone. Team-building capability predicts the founder's ability to assemble the human capital required to execute across all domains simultaneously as the company grows.

**Why It Matters:** The team assembled in the first two years becomes the company's organisational DNA. Founders who attract high-quality talent create compounding capability; those who cannot attract talent create a ceiling on every domain — product velocity, sales, technology, and operational quality are all bounded by team quality.

**Dependencies:** Depends on `D01 > Leadership` (talent follows leaders, not titles); depends on `D01 > Vision` (compelling vision attracts talent); depends on `D01 > Communication` (recruitment is a communication act).

**Relationships:** Directly impacts `D11 > Human Resources Management`; influences `D15 > Team Scalability`; feeds `D16 > Investment Readiness` (investors assess team quality as a primary signal).

**Evidence Sources:**
- Current team roster with backgrounds, tenure, and roles
- Evidence of attracting senior hires from established companies or competitors
- Team retention rate over the startup's operating history
- Org chart evolution showing team growth pattern
- References from current team members on the quality of the recruitment and onboarding experience

**Red Flags:**
- Team consists exclusively of founders' personal network with no diverse or independent talent
- Senior hires have departed within 6 months of joining without disclosed reasons
- Founding team is entirely homogeneous in background, function, and perspective
- No documented hiring process or criteria — hiring described as entirely informal
- Key functional areas (e.g., sales, operations) remain unfilled despite 12+ months of operation

**Expected Outputs:** A team building assessment covering: team composition completeness (are critical functions staffed?), talent calibre relative to stage, retention quality, and founder-as-recruiter effectiveness. Output includes a team gap analysis identifying unfilled roles critical to near-term execution.

---

#### D01 > Learning Ability

**Definition:** Learning ability measures the founder's demonstrated capacity to rapidly acquire new knowledge, synthesise it with existing mental models, and apply it to improve decisions and strategies — across both technical and business domains.

**Purpose:** The knowledge required to build a startup evolves continuously. A founder who learned enough to start the company must continuously learn enough to grow it. Evaluators assess learning ability to predict whether the founder can keep pace with the complexity of a scaling organisation.

**Why It Matters:** A founder whose learning rate is slower than the company's growth rate becomes an organisational bottleneck. The company outgrows its leadership, resulting in poor decisions made by a founder who no longer understands the domain deeply enough to lead it.

**Dependencies:** Depends on `D01 > Adaptability` (learning must translate into behavioural change to have value); depends on `D01 > Domain Expertise` (prior knowledge provides the scaffolding onto which new learning is anchored).

**Relationships:** Informs `D17 > Coachability` (learning ability is a prerequisite for coachability); influences `D03 > Engineering Quality` (technically learning founders make better engineering decisions over time); feeds `D19 > Innovation Process Maturity`.

**Evidence Sources:**
- History of acquiring new skills or knowledge domains during the startup's operation (e.g., self-taught regulatory knowledge, financial modelling capability)
- Quality of questions asked during investor or advisor meetings as a proxy for intellectual engagement
- Reading, course completion, or conference attendance history in domains adjacent to the startup's core
- Evidence of incorporating expert feedback into subsequent versions of key documents or decisions
- Articulation of lessons learned from prior failures or experiments

**Red Flags:**
- Founder cannot describe a specific instance of changing their mind based on new evidence
- Investor or advisor feedback is consistently received but not incorporated across multiple meetings
- Knowledge of market or technology has not visibly evolved despite 18+ months of operation
- Founder is dismissive of academic research, industry reports, or expert perspectives
- Decision-making framework described as entirely intuitive with no evidence of structured learning processes

**Expected Outputs:** A learning velocity assessment, qualitatively rated as High / Medium / Low, supported by specific evidence of knowledge acquisition and application. Includes a note on the primary learning modalities the founder demonstrates (peer networks, structured study, customer interviews, advisor relationships).

---

#### D01 > Commitment

**Definition:** Commitment measures the depth and durability of the founder's personal investment in the venture — encompassing full-time dedication, financial exposure, psychological resolve, and the demonstrated willingness to endure prolonged hardship in service of the company's success.

**Purpose:** Commitment predicts persistence through adversity. All startups encounter extended periods of difficulty. Evaluators assess commitment to determine whether the founding team has the resolve to continue operating and iterating through these periods rather than abandoning the venture.

**Why It Matters:** Investors and incubators commit multi-year resources to startups. A founder who exits the venture under moderate stress destroys those resources. Commitment signals the durability of the founding team's engagement and is therefore one of the most consequential personal variables in early-stage evaluation.

**Dependencies:** Depends on `D01 > Vision` (commitment without a compelling vision is unsustainable); depends on `D01 > Execution` (commitment is evidenced by sustained effort over time).

**Relationships:** Informs `D16 > Cap Table Structure` (committed founders retain equity rather than selling prematurely); influences `D13 > Key Person Risk` (committed founders reduce key person departure risk); feeds `D17 > Milestone Commitment`.

**Evidence Sources:**
- Full-time or part-time status: is the founder working full-time on the venture?
- Personal financial investment: has the founder invested personal capital?
- Vesting schedule and cliff: does the founder accept standard vesting terms?
- Duration of engagement: how long has the founder been working on this venture without external income?
- Evidence of personal sacrifices made (foregone salary, relocated, turned down competing opportunities)

**Red Flags:**
- Founder is operating the startup as a side project while holding a full-time corporate role
- No personal financial investment despite sufficient personal means
- Founder has not accepted a vesting schedule or has negotiated unusual acceleration provisions
- Described exit conditions are shallow ("if we don't raise in 6 months, I'll stop")
- Evidence of parallel startup activities or significant advisory commitments consuming founder time

**Expected Outputs:** A commitment classification: Full Commitment (full-time, financial exposure, vesting accepted), Conditional Commitment (full-time but with stated exit conditions or parallel commitments), or Partial Commitment (part-time or with no financial skin in the game). Output is used to apply a commitment multiplier to all other founder scores in the synthesis layer.

---

### DOMAIN 02: PRODUCT

**Domain Definition:** The Product domain evaluates the startup's primary deliverable — the solution being built for the target customer. It assesses the quality of problem identification, the fit between solution and market need, user experience, development progress, and the strategic direction of the product over time. Product evaluation is distinct from technology evaluation: Product concerns what is built and for whom, while Technology concerns how it is built and with what architectural choices.

**Domain Tree:**
```
D02 PRODUCT
├─ Problem Definition
├─ Solution Architecture
├─ Product-Market Fit
├─ User Experience
├─ Feature Completeness
├─ Product Differentiation
├─ Development Velocity
├─ Feedback Integration
├─ Product Roadmap
└─ Dependency Risk
```

---

#### D02 > Problem Definition

**Definition:** Problem definition measures the precision and depth with which the founding team has articulated the specific problem they are solving, including its scope, frequency, cost to the customer, and the inadequacy of existing solutions. A well-defined problem statement is specific, evidenced, and quantified.

**Purpose:** The quality of problem definition determines everything downstream: the product scope, the target customer, the value proposition, the pricing, and the market size. Evaluators assess problem definition to validate that the startup is solving a real and significant problem — not a problem the founder imagined or a problem that is already adequately solved.

**Why It Matters:** Poorly defined problems lead to solutions built for a non-existent or non-paying market. The most common failure mode in early-stage startups is not poor execution of a good idea but flawless execution of a solution to a problem customers do not actually have, or do not pay to solve.

**Dependencies:** Depends on `D01 > Domain Expertise` (problem identification requires insider knowledge); depends on `D05 > Customer Profile Definition` (the problem must be defined relative to a specific customer).

**Relationships:** Directly informs `D02 > Solution Architecture` (the solution is defined by the problem); feeds `D05 > Demand Validation` (demand validation is the market-side confirmation of the problem definition); influences `D19 > Problem-Solution Originality`.

**Evidence Sources:**
- Customer discovery interview summaries (10+ interviews with target customers)
- Quantified problem statements: cost of the problem, frequency of occurrence, current workaround cost
- Market research or third-party reports confirming the problem at scale
- NPS or dissatisfaction data from competitors' customers
- Jobs-to-be-done analysis documentation

**Red Flags:**
- Problem statement is abstract and not tied to a specific customer type or use case
- No customer discovery interviews conducted prior to product development
- Problem is described in terms of what the technology can do, not what the customer suffers
- Existing solutions are not acknowledged or are dismissed without specific reasons
- Problem frequency or severity is asserted without any supporting evidence

**Expected Outputs:** A problem definition quality score (1–5) assessing specificity, customer-grounding, quantification, and evidence base. Includes a flag if the problem is described in solution-first terms, indicating potential customer discovery debt.

---

#### D02 > Solution Architecture

**Definition:** Solution architecture measures the logical design of how the product addresses the defined problem — encompassing the core functional approach, the interaction model, the delivery mechanism, and the set of capabilities that must be built to produce the promised outcome for the customer.

**Purpose:** Solution architecture is the bridge between problem and technology. Evaluators assess it to determine whether the proposed product design is the right approach to the defined problem, whether it is over-engineered or under-designed, and whether it can be built within the constraints of the current team and capital.

**Why It Matters:** A misaligned solution architecture — one that technically works but does not solve the customer's actual workflow — produces a product that customers do not adopt despite its technical quality. Architecture decisions made early are expensive to reverse.

**Dependencies:** Depends on `D02 > Problem Definition` (architecture must address the stated problem); depends on `D03 > Technical Architecture` (product architecture must be technically implementable).

**Relationships:** Informs `D03 > Technology Stack` (product architecture constrains technology choices); influences `D02 > Feature Completeness`; feeds `D04 > Prototype Maturity`.

**Evidence Sources:**
- Product specification documents or functional requirement specifications
- Architecture diagrams showing how the product components interact
- Prototype or MVP demonstrating the core solution interaction
- User flow diagrams validated with target customers
- Technical feasibility assessment by independent technical reviewers

**Red Flags:**
- Solution architecture is described but no documentation exists — it lives only in the founder's head
- Architecture requires solving multiple unsolved hard technical problems simultaneously
- Solution design was developed without input from target customers
- Core architectural assumptions have not been validated through any prototype or experiment
- Solution is significantly more complex than required by the stated problem

**Expected Outputs:** A solution architecture assessment rating conceptual soundness, customer alignment, implementation feasibility, and documentation quality. Flags any architectural assumption that remains unvalidated.

---

#### D02 > Product-Market Fit

**Definition:** Product-market fit (PMF) measures the degree to which the product, as currently built, satisfies the needs of a definable and reachable market segment so completely that the market segment adopts and retains it at a rate that signals genuine pull rather than manufactured demand.

**Purpose:** PMF is the single most critical inflection point in a startup's trajectory. Before PMF, growth is artificial and capital-intensive. After PMF, growth becomes increasingly natural and defensible. Evaluators assess PMF signals to determine whether the startup has crossed, is approaching, or is far from this threshold.

**Why It Matters:** Capital deployed before PMF is consumed searching for fit. Capital deployed after PMF accelerates a proven model. Misidentifying PMF status — either by the startup or by the evaluator — leads to premature scaling of an unvalidated product, which is a leading cause of startup failure at the seed-to-Series A stage.

**Dependencies:** Depends on `D02 > Problem Definition` and `D05 > Customer Profile Definition` (PMF requires both a well-defined product and a well-defined market segment).

**Relationships:** Directly feeds `D10 > GTM Strategy Definition`; influences `D15 > Revenue Scalability`; informs `D07 > Revenue Traction`.

**Evidence Sources:**
- Retention cohort data: do users return after the first session?
- Net Promoter Score (NPS) from active users
- Sean Ellis / Rahul Vohra "must-have" survey results (% of users who would be "very disappointed" if product disappeared)
- Organic referral rate: what % of new users come from existing user recommendations?
- Customer willingness-to-pay data from closed transactions

**Red Flags:**
- PMF is claimed based on pilot programmes that were subsidised or incentivised
- Retention data is not tracked or unavailable
- NPS is positive but driven by a small, unrepresentative user base (e.g., friends and family)
- Growth has been achieved through heavy paid acquisition with no organic component
- Product is being used in ways significantly different from intended design — indicating the market wants something other than what is built

**Expected Outputs:** A PMF signal classification: Confirmed PMF (quantitative retention and organic growth evidence), PMF Indicators Present (positive signals but insufficient data volume), Pre-PMF (product in market but no consistent pull signals), or No Market Engagement (product not yet in customer hands).

---

#### D02 > User Experience

**Definition:** User experience (UX) measures the quality of the interaction between the product and its end users, encompassing ease of use, discoverability of features, clarity of feedback, error recovery, and the overall emotional quality of the interaction as perceived by the target user.

**Purpose:** UX quality directly determines whether users adopt and retain the product. Technical capability that is inaccessible through poor UX produces no user value and generates no revenue. Evaluators assess UX to determine whether the product's functional capability is actually available to and usable by its target users.

**Why It Matters:** B2C products with poor UX fail to retain users regardless of feature completeness. B2B products with poor UX face adoption resistance from end users even when procurement has been secured. In both cases, UX debt accumulates faster than it can be repaid once a product scales.

**Dependencies:** Depends on `D02 > Solution Architecture` (UX is constrained by the product's functional design); depends on `D05 > Customer Profile Definition` (UX quality is always relative to the target user's expectations and capabilities).

**Relationships:** Influences `D02 > Product-Market Fit` (poor UX prevents PMF); feeds `D10 > Customer Onboarding Process`; informs `D18 > Customer Success Infrastructure`.

**Evidence Sources:**
- Usability test recordings with target users (think-aloud protocol)
- User onboarding completion rates and drop-off analysis
- Support ticket volume and categorisation by UX-related issues
- Time-to-value measurement: how long before a new user achieves their first meaningful outcome?
- Expert UX audit conducted by independent UX practitioners

**Red Flags:**
- No usability testing has been conducted with actual target users
- Onboarding completion rate below 60% without explanation or improvement plan
- Product requires significant training or a long manual to use effectively
- Support tickets dominated by "I can't figure out how to..." category
- UX was designed by engineers without UX specialisation and has never been independently reviewed

**Expected Outputs:** A UX quality assessment rated across four dimensions: learnability, efficiency, error tolerance, and satisfaction. Accompanied by a list of top UX friction points identified through evidence, and a flag if no user testing evidence exists.

---

#### D02 > Feature Completeness

**Definition:** Feature completeness measures the degree to which the product contains the minimum set of capabilities required for the target customer to achieve their primary use case without resorting to workarounds, manual processes, or competitor tools to fill gaps.

**Purpose:** Feature completeness is not about having every possible feature — it is about having the right features for the target use case. Evaluators assess it to distinguish between MVPs that are intentionally minimal and products that are genuinely incomplete in ways that block customer value delivery.

**Why It Matters:** A product with critical feature gaps forces customers to supplement it with workarounds, which reduces perceived value, increases churn risk, and opens the door for a more complete competitor solution. Conversely, feature-complete products that exceed minimum requirements for the target use case signal readiness for commercial deployment.

**Dependencies:** Depends on `D02 > Problem Definition` (what is "complete" is defined by the problem scope); depends on `D02 > Product Roadmap` (feature gaps should be time-bound on the roadmap).

**Relationships:** Informs `D18 > Enterprise Readiness` (enterprise customers require specific feature thresholds before procurement); influences `D04 > Deployment Readiness`; feeds `D10 > Early Customer Pipeline`.

**Evidence Sources:**
- Feature checklist benchmarked against target customer use case requirements
- Customer feedback explicitly citing missing features as a barrier to adoption or expansion
- Competitor feature comparison matrix
- Product demonstration covering end-to-end customer workflow
- Pilot programme feedback documentation

**Red Flags:**
- Core workflow cannot be completed end-to-end within the product without manual steps
- Customer feedback consistently cites the same two or three missing features across multiple customers
- Product demo requires the demonstrator to work around missing features in real time
- Feature roadmap shows critical features more than 12 months out with no interim solution
- Customers are using competitor tools to supplement functionality gaps

**Expected Outputs:** A feature completeness rating for the primary use case (Complete / Substantially Complete / Partially Complete / Incomplete) accompanied by a structured gap analysis listing unimplemented features, their criticality, and their roadmap position.

---

#### D02 > Product Differentiation

**Definition:** Product differentiation measures the degree to which the product offers capabilities, experiences, or outcomes that are materially superior to, or distinct from, those offered by existing solutions — as perceived by the target customer rather than as claimed by the startup.

**Purpose:** Differentiation is the commercial foundation of defensibility. A product that is not meaningfully different from alternatives will be competed away through pricing pressure. Evaluators assess differentiation to determine whether the product can command a price premium, build customer loyalty, and resist substitution.

**Why It Matters:** Undifferentiated products commoditise over time, compressing margins and eroding the customer relationships needed to sustain growth. In competitive markets, undifferentiated products are perpetually one better-funded competitor away from obsolescence.

**Dependencies:** Depends on `D09 > Differentiation Analysis` (product differentiation must be assessed relative to competitors); depends on `D03 > Core Innovation` (technical differentiation underpins product differentiation).

**Relationships:** Feeds `D09 > Competitive Moat`; influences `D06 > Pricing Strategy` (differentiation supports price premium); informs `D08 > IP Defensibility`.

**Evidence Sources:**
- Side-by-side feature and capability comparison with top three competitors, validated by customers
- Customer testimonials specifically citing what makes this product different from alternatives they have tried
- Win/loss analysis from sales process: why do customers choose this product vs. alternatives?
- Analyst or third-party review citing differentiation
- NPS disaggregated by the specific features customers cite as reasons for recommendation

**Red Flags:**
- The only differentiation claimed is "better UX" or "easier to use" without specific evidence
- Differentiation is primarily price-based (cheaper), which is not sustainable without cost structure advantages
- Customers cannot name a specific feature or capability that makes this product their preferred choice
- Competitor analysis is superficial and does not include recently launched competing products
- Differentiation is based on future features rather than currently delivered capability

**Expected Outputs:** A differentiation profile identifying the product's top three customer-validated differentiating dimensions, assessed for durability (how easily can competitors replicate?) and evidence quality (claimed vs. customer-validated vs. analyst-verified).

---

#### D02 > Development Velocity

**Definition:** Development velocity measures the speed and consistency with which the product team ships meaningful product improvements — features, fixes, performance improvements, and UX enhancements — relative to the complexity of what is being built and the size of the team.

**Purpose:** Development velocity is an operational metric that predicts whether the startup can outpace competitors, respond to customer feedback, and reach commercial readiness within its funding runway. Evaluators assess it to determine whether the product development process is functioning at the rate required.

**Why It Matters:** A startup with low development velocity will exhaust its capital before reaching the product state required for commercial success. In competitive markets, a startup that ships more slowly than its competitors loses the feature race and cedes customer mindshare regardless of its initial head start.

**Dependencies:** Depends on `D03 > Engineering Quality` (high-quality engineering sustains velocity; technical debt destroys it); depends on `D01 > Technical Competence` (competent founders make decisions that preserve rather than impede velocity).

**Relationships:** Informs `D04 > TRL Advancement Trajectory`; influences `D15 > Technology Scalability`; feeds `D07 > Capital Efficiency`.

**Evidence Sources:**
- Sprint velocity data from project management tools (Jira, Linear, GitHub)
- Release history: number and substance of releases per month over the past 12 months
- Cycle time metrics: average time from feature concept to production deployment
- GitHub commit frequency and code review throughput
- Comparison of planned vs. actual development timelines for the last three milestones

**Red Flags:**
- No release has occurred in 60+ days without a documented technical reason
- Development velocity has been declining over consecutive quarters
- Sprint completion rate is below 60% consistently
- Team describes development process as "always in planning" or "blocked on decisions"
- No version control or project tracking system in use — progress is entirely verbal

**Expected Outputs:** A development velocity assessment quantified as releases per month, feature delivery rate relative to team size, and a trend indicator (Accelerating / Stable / Declining). Includes a note on primary velocity blockers identified from evidence.

---

#### D02 > Feedback Integration

**Definition:** Feedback integration measures the quality and consistency of the process by which the product team collects user and customer feedback, translates it into product decisions, and validates that implemented changes produce the expected improvement in user experience or business outcomes.

**Purpose:** Products that do not systematically integrate feedback fail to converge on what customers actually need. Evaluators assess feedback integration to determine whether the product development process is market-oriented (driven by customer signals) or supply-oriented (driven by what the team prefers to build).

**Why It Matters:** Feedback integration is the mechanism by which PMF is found and refined. Without a functioning feedback loop, product iterations are random walks rather than directed searches. Capital spent on development without feedback integration has a significantly lower expected return.

**Dependencies:** Depends on `D01 > Adaptability` (feedback integration requires willingness to change based on evidence); depends on `D02 > Development Velocity` (feedback must be integrated at a pace that keeps the product responsive).

**Relationships:** Informs `D02 > Product-Market Fit` (PMF is found through iterated feedback integration); influences `D18 > Customer Success Infrastructure`; feeds `D10 > Customer Onboarding Process`.

**Evidence Sources:**
- Customer feedback collection tools in use (in-app surveys, NPS, support tickets, interview programs)
- Product changelog annotations linking features to specific customer feedback sources
- Documented examples of product decisions driven by customer feedback with before/after metrics
- Frequency of customer advisory board or user research sessions
- Quantitative tracking of support ticket resolution rates and recurring issue trends

**Red Flags:**
- No formal feedback collection mechanism exists — feedback is gathered ad hoc
- Founder can recall no specific product decision made primarily in response to customer feedback
- Customer requests are acknowledged but not tracked systematically
- Product changelog shows no correlation between user-reported issues and subsequent updates
- Customer advisory board or user research has not occurred in the past six months

**Expected Outputs:** A feedback integration maturity score (Systematic / Reactive / Ad Hoc / Absent) with evidence of the feedback-to-product cycle time and the ratio of customer-driven to internally-driven product changes in the last development cycle.

---

#### D02 > Product Roadmap

**Definition:** Product roadmap measures the quality, specificity, and strategic coherence of the documented plan for future product development — encompassing near-term feature delivery (0–6 months), medium-term capability building (6–18 months), and long-term product vision alignment (18+ months).

**Purpose:** A credible product roadmap signals that the founding team has made deliberate prioritisation decisions, understands the sequence of capabilities required to reach commercial scale, and can communicate future development commitments to customers, investors, and the team.

**Why It Matters:** An absent or incoherent roadmap prevents customers from making adoption decisions, prevents investors from assessing whether the product will reach commercial readiness within the funding period, and leaves the engineering team without a shared prioritisation framework — resulting in local optimisation and misaligned effort.

**Dependencies:** Depends on `D01 > Vision` (roadmap must be traceable to strategic vision); depends on `D02 > Feedback Integration` (roadmap should reflect accumulated customer feedback).

**Relationships:** Feeds `D07 > Financial Projections` (revenue projections depend on product milestones); influences `D15 > Revenue Scalability` (roadmap shows whether the product can serve larger markets); informs `D16 > Investor Documentation`.

**Evidence Sources:**
- Written product roadmap document with time horizons, milestone definitions, and ownership
- Evidence that roadmap is shared with customers, investors, and the engineering team
- Historical roadmap vs. actuals: how accurate were previous roadmap commitments?
- Prioritisation criteria: how are features ranked? Is there a documented framework?
- Customer validation of roadmap priorities: do customers confirm that planned features address their needs?

**Red Flags:**
- No written product roadmap exists — direction is communicated verbally by the founder
- Roadmap extends 36+ months with no near-term milestones — it is aspirational, not operational
- Roadmap has not been updated in six or more months
- All roadmap items are internal features with no items driven by customer requests
- Roadmap commits to capabilities that require technology not yet proven at TRL 4 or above

**Expected Outputs:** A roadmap quality assessment covering: time horizon coverage, specificity of near-term items, historical accuracy, customer validation status, and strategic coherence. Accompanied by a flag if any roadmap commitment appears unrealistic given current development velocity and team size.

---

#### D02 > Dependency Risk

**Definition:** Dependency risk measures the degree to which the product's development, delivery, or commercial performance depends on factors outside the startup's direct control — including third-party APIs, platform providers, hardware suppliers, regulatory approvals, or single-source components.

**Purpose:** Dependency risk is a product-level vulnerability that can render a technically excellent product commercially undeliverable or economically non-viable through no fault of the startup. Evaluators assess it to identify concentration risks that could destroy product viability without any internal failure.

**Why It Matters:** Platform API changes (e.g., social media API restrictions), hardware supply chain disruptions, and regulatory delays have each destroyed otherwise viable startups. A product with unacknowledged dependency risks has a hidden fragility that standard product assessments miss.

**Dependencies:** Depends on `D03 > Technology Stack` (tech stack choices determine platform dependencies); depends on `D12 > Regulatory Compliance` (regulatory dependencies are a form of product dependency risk).

**Relationships:** Feeds `D13 > Technology Risk`; influences `D15 > Technology Scalability`; informs `D11 > Supply Chain & Vendor Management`.

**Evidence Sources:**
- Documented list of all third-party dependencies (APIs, platforms, SDKs, hardware components)
- Assessment of each dependency's replaceability: how long would migration take?
- API terms of service analysis for high-criticality dependencies
- Supplier concentration analysis: single-source vs. multi-source components
- Regulatory approval status for any required certifications or licences

**Red Flags:**
- Single third-party API or platform is in the critical path with no mitigation plan
- The startup has built core value on top of a platform that restricts commercialisation (e.g., marketplace restrictions)
- Regulatory approvals required for product launch have not been initiated and timeline is unknown
- No contractual protection against third-party dependency changes (e.g., API deprecation notice period)
- Hardware component sourced from a single geographic region with known supply constraints

**Expected Outputs:** A dependency risk register listing all identified dependencies, rated by criticality (Critical / High / Medium / Low), along with the current mitigation status and residual risk level for each. Critical dependencies with no mitigation plan generate an automatic evaluation flag.

---

### DOMAIN 03: TECHNOLOGY

**Domain Definition:** The Technology domain evaluates the technical foundation upon which the startup's product and competitive position are built. It examines the quality, originality, defensibility, and operational soundness of the technical architecture, engineering processes, and data systems. Technology evaluation is distinct from Product evaluation: Technology concerns the how — the underlying engineering decisions, the code quality, the system design, and the technical team's capabilities.

**Domain Tree:**
```
D03 TECHNOLOGY
├─ Technical Architecture
├─ Core Innovation
├─ Technology Differentiation
├─ Engineering Quality
├─ Technology Stack
├─ Data Strategy
├─ Security & Privacy
├─ Technical Debt
├─ Infrastructure Resilience
└─ Technical Team Capability
```

---

#### D03 > Technical Architecture

**Definition:** Technical architecture measures the quality of the overarching system design — the structural decisions about how the software or hardware components are organised, how they communicate, how they are deployed, and how the architecture supports the current and future requirements of the product at scale.

**Purpose:** Architecture decisions made in the first year of a startup's life define the technical ceiling of the company. Poor architecture is not a problem that future engineering effort can cleanly solve — it compounds into technical debt, performance limitations, and security vulnerabilities. Evaluators assess architecture to identify structural risks early.

**Why It Matters:** A well-architected system supports rapid feature development, horizontal scaling, reliable operations, and security. A poorly architected system becomes increasingly expensive to operate and extend, consuming engineering capacity in maintenance rather than innovation, and ultimately limiting the product's commercial potential.

**Dependencies:** Depends on `D01 > Technical Competence` (good architecture requires technically capable founders or leads); depends on `D03 > Technology Stack` (architecture is implemented through specific technology choices).

**Relationships:** Directly informs `D15 > Technology Scalability`; influences `D03 > Technical Debt`; feeds `D04 > System Integration`.

**Evidence Sources:**
- Architecture documentation: system diagrams, component interaction maps, data flow diagrams
- Independent technical review or architecture audit report
- Cloud infrastructure configuration reviewed by a technical evaluator
- Scalability stress test results demonstrating behaviour under load
- API design documentation showing interface consistency and forward compatibility design

**Red Flags:**
- No architecture documentation exists — the system design lives only in engineers' heads
- Monolithic architecture with no modularisation strategy in a product that must scale to multi-tenant enterprise use
- Architecture was designed for a single-client deployment and has not been re-evaluated for multi-tenancy
- No separation between data access, business logic, and presentation layers
- Architecture has never been reviewed by a technical person outside the founding team

**Expected Outputs:** An architecture quality assessment covering scalability potential, modularity, documentation quality, and independent review status. Rated 1–5 per dimension. Flags any single-point-of-failure architectural patterns.

---

#### D03 > Core Innovation

**Definition:** Core innovation measures the degree to which the technology contains a novel technical contribution — a new algorithm, a new application of an existing method, a new material, a new hardware design, or a new system combination — that is not already established practice in the relevant technical field.

**Purpose:** Core innovation is the technical basis of competitive moat. Without genuine technical novelty, the product's defensibility rests entirely on execution speed and brand — both of which are weaker moats than proprietary technology. Evaluators assess core innovation to determine whether the technology gives the startup a durable technical edge.

**Why It Matters:** Startups without core technical innovation are competing on execution against incumbents who have larger teams, established customers, and greater capital. A startup with genuine core innovation competes on capability, where size advantages are less determinative.

**Dependencies:** Depends on `D01 > Technical Competence` (innovation requires technical depth to produce and recognise); depends on `D04 > TRL Classification` (innovation must be at some minimum TRL to be evaluated).

**Relationships:** Directly feeds `D08 > Patent Portfolio` (core innovation is the subject of patents); informs `D19 > Novelty` and `D19 > Inventive Step`; influences `D09 > Competitive Moat`.

**Evidence Sources:**
- Technical whitepaper or research publication describing the innovation
- Patent application or granted patent with claims analysis
- Independent expert review confirming novelty relative to prior art
- Benchmarking data comparing the innovation's performance against existing solutions
- Academic citations or conference presentations of the underlying technology

**Red Flags:**
- The "innovation" is a combination of existing open-source components with no novel contribution
- No technical documentation beyond a pitch deck describes the underlying technology
- Claims of novelty have not been reviewed by any technical expert outside the founding team
- The technical approach has been described in academic literature without prior commercialisation — the startup's contribution is awareness, not invention
- Core algorithm or method is borrowed from a prior employer without IP assignment clarity

**Expected Outputs:** A core innovation assessment classifying the innovation as: Foundational (new method or theory), Applied (novel application of known method), Incremental (improvement over existing solution), or Derivative (integration or workflow improvement without technical novelty). Each classification carries different IP strategy and defensibility implications.

---

#### D03 > Technology Differentiation

**Definition:** Technology differentiation measures the degree to which the startup's technical implementation produces outcomes — performance, accuracy, cost, speed, reliability — that are measurably and materially superior to those of competing technical implementations available to the target customer.

**Purpose:** Technology differentiation is the technical dimension of competitive advantage. Evaluators assess it to determine whether the startup's technical superiority is real and quantifiable, or a matter of marketing positioning without a measurable performance gap.

**Why It Matters:** Customers and procurement decision-makers increasingly demand quantitative evidence of technical superiority before switching from established solutions. Claimed superiority without benchmarked evidence is not commercially actionable. Technology differentiation evidence directly supports sales processes and investor due diligence.

**Dependencies:** Depends on `D03 > Core Innovation` (differentiation is grounded in innovation); depends on `D09 > Competitive Landscape Mapping` (differentiation must be assessed relative to specific competitors).

**Relationships:** Directly informs `D02 > Product Differentiation`; influences `D06 > Pricing Strategy` (superior technology supports premium pricing); feeds `D08 > IP Defensibility`.

**Evidence Sources:**
- Published benchmark results comparing the startup's technology against named alternatives
- Third-party evaluation reports from recognised testing organisations
- Customer case study data showing measurable performance improvement post-adoption
- Academic paper benchmarking results if the technology emerged from research
- Independent replication of performance claims by a credible technical reviewer

**Red Flags:**
- Performance claims are made without reference to a specific comparison baseline
- Benchmarks are self-conducted without independent verification
- Differentiation is described qualitatively ("much faster", "significantly more accurate") without numbers
- The comparison set used in benchmarks excludes the most capable current competitors
- Performance advantages are visible only under specific conditions that do not reflect real-world usage

**Expected Outputs:** A technology differentiation evidence profile listing each claimed advantage, the comparison basis, the evidence source, and an evidence quality rating (Independently Verified / Self-Reported / Claimed Only). Flags any advantage claimed without any supporting evidence.

---

#### D03 > Engineering Quality

**Definition:** Engineering quality measures the internal standard of the codebase, hardware design, or other primary technical artefact — encompassing code readability, test coverage, documentation, adherence to security and performance best practices, and the maintainability of the system by engineers joining the team without prior context.

**Purpose:** Engineering quality is the foundation of long-term technical sustainability. A high-quality codebase allows the team to maintain high development velocity as the team grows, supports safe and rapid feature addition, and reduces the risk of critical production failures.

**Why It Matters:** Poor engineering quality is not a problem that can be deferred indefinitely. As the codebase grows, quality debt compounds: each new feature requires more effort, each bug fix risks introducing new bugs, and onboarding new engineers takes longer. Eventually, poor quality produces a system that must be rewritten — a costly and risky proposition for a capital-constrained startup.

**Dependencies:** Depends on `D01 > Technical Competence` (quality engineering requires technically skilled leadership); depends on `D03 > Technical Debt` (current quality level reflects the accumulation of past quality decisions).

**Relationships:** Directly informs `D02 > Development Velocity`; influences `D03 > Infrastructure Resilience`; feeds `D15 > Technology Scalability`.

**Evidence Sources:**
- Code review by an independent technical evaluator with access to the repository
- Test coverage report (unit, integration, and end-to-end test coverage percentage)
- Static code analysis results from tools such as SonarQube or CodeClimate
- Documentation quality assessment: is there a README, API documentation, and inline code commentary?
- Deployment pipeline review: CI/CD configuration, automated testing gates, release process documentation

**Red Flags:**
- Test coverage below 40% in a production product with active customers
- No automated testing of any kind — all testing is manual
- Repository access is refused during technical due diligence without a technical reason
- Code review identifies systemic patterns of unsafe practices (e.g., hardcoded credentials, unvalidated inputs)
- No documentation exists beyond code comments, and those are sparse

**Expected Outputs:** An engineering quality score (1–5) across five dimensions: test coverage, documentation, security practices, code organisation, and deployment process maturity. Supplemented by a list of the top three technical risk areas identified through code review.

---

#### D03 > Technology Stack

**Definition:** Technology stack measures the appropriateness and maturity of the specific programming languages, frameworks, databases, cloud providers, and tooling chosen by the engineering team, relative to the requirements of the product, the capability of the team, and the standards expected by enterprise customers.

**Purpose:** Stack choices made early are difficult to reverse and have lasting consequences for talent acquisition, performance, security, enterprise compliance, and vendor lock-in. Evaluators assess the stack to identify choices that create unnecessary risk or constraint.

**Why It Matters:** An inappropriate stack choice can prevent the startup from reaching enterprise-grade compliance requirements, make the product unable to perform at the required scale, or force a rewrite when the team attempts to hire engineers familiar with mainstream technologies. Stack hygiene is a component of long-term technical sustainability.

**Dependencies:** Depends on `D03 > Technical Architecture` (stack choices must serve the architectural design); depends on `D03 > Technical Team Capability` (the stack must be within the competence range of the engineering team).

**Relationships:** Informs `D02 > Dependency Risk` (stack choices create vendor and platform dependencies); influences `D18 > Enterprise Readiness` (enterprise procurement often has approved technology lists); feeds `D11 > Operational Technology`.

**Evidence Sources:**
- Technology stack documentation listing all components with version numbers
- Rationale documentation for non-standard stack choices
- Enterprise customer compatibility assessment: does the stack meet procurement security and compliance requirements?
- Community activity and maintenance status of all chosen open-source dependencies
- Engineering team proficiency assessment for each stack component

**Red Flags:**
- Core product built on a technology that has reached end-of-life or is no longer actively maintained
- Unusual or highly niche stack choices with no documented rationale and a very small global talent pool
- Multiple proprietary vendor SDKs in the critical path with no open alternative and high switching costs
- Stack includes components with known, unpatched security vulnerabilities
- Enterprise customers have stated that the stack is incompatible with their security or compliance requirements

**Expected Outputs:** A stack assessment covering: appropriateness for use case, team proficiency alignment, enterprise compatibility, dependency health, and vendor lock-in exposure. Flags any stack component rated as High Risk on any dimension.

---

#### D03 > Data Strategy

**Definition:** Data strategy measures the completeness and sophistication of the startup's plan for collecting, storing, governing, and exploiting data as a core business asset — including proprietary dataset development, data quality management, analytics infrastructure, and the use of data to create product or competitive advantages.

**Purpose:** In data-intensive startups (AI, ML, analytics, IoT, fintech), the data strategy is as important as the technology strategy. Even in non-data-native startups, a clear data strategy is required for informed product decisions, operational excellence, and regulatory compliance. Evaluators assess data strategy to determine whether the startup treats data as a strategic asset.

**Why It Matters:** Startups that fail to build a data strategy early are unable to train competitive AI models, lack the analytics to make informed product decisions, and expose themselves to regulatory penalties for unmanaged data practices. Proprietary datasets are increasingly a primary source of competitive moat.

**Dependencies:** Depends on `D03 > Technical Architecture` (data architecture is a component of overall technical architecture); depends on `D12 > Data Protection & Privacy` (data strategy must operate within legal and regulatory constraints).

**Relationships:** Feeds `D19 > Research & Development Depth` (data is the fuel of R&D in data-driven domains); informs `D14 > Ethical AI & Technology Use`; influences `D08 > Trade Secrets` (proprietary datasets may qualify as trade secrets).

**Evidence Sources:**
- Data governance documentation: data classification, retention, access control, and disposal policies
- Dataset documentation: description of proprietary datasets, their size, provenance, and quality assessment
- Analytics infrastructure description: what tools are used for data analysis and product telemetry?
- Evidence of data-driven product decisions: examples of product changes made on the basis of data analysis
- Data privacy impact assessment or legal review of data collection practices

**Red Flags:**
- No data governance policy exists for a product that collects personally identifiable information
- Data described as a key asset but no documentation of the dataset's size, quality, or provenance
- Analytics infrastructure limited to basic Google Analytics — no product telemetry or behavioural data collection
- AI or ML product built on a dataset whose licensing for commercial use is unclear
- Data stored in a single unbackuped location with no disaster recovery provision

**Expected Outputs:** A data strategy maturity assessment rated as Strategic (data is a documented, governed, and actively exploited asset), Tactical (data is collected and used informally), or Absent (no structured approach to data as an asset). Includes a data risk register identifying any compliance or quality risks.

---

#### D03 > Security & Privacy

**Definition:** Security and privacy measures the degree to which the startup has implemented technical and procedural safeguards to protect its systems, customer data, and intellectual property from unauthorised access, data breaches, cyberattacks, and privacy violations.

**Purpose:** Security and privacy are not optional enhancements — they are foundational operational requirements, particularly for products handling customer data, financial transactions, health information, or operating in regulated industries. Evaluators assess them to identify exposure that could result in regulatory penalties, customer loss, or reputational destruction.

**Why It Matters:** A single significant data breach or privacy violation can destroy a startup's customer trust, trigger regulatory investigations, create substantial legal liability, and end its fundraising prospects. Security and privacy are existential risks when left unmanaged.

**Dependencies:** Depends on `D12 > Data Protection & Privacy` (legal requirements define the compliance threshold); depends on `D03 > Engineering Quality` (security is a property of engineering decisions).

**Relationships:** Directly informs `D13 > Technology Risk`; influences `D18 > Enterprise Readiness` (enterprise procurement requires security certifications); feeds `D12 > Regulatory Compliance`.

**Evidence Sources:**
- Security audit or penetration test report conducted by an independent firm
- SOC 2, ISO 27001, or equivalent certification status
- Privacy policy and data processing agreement documentation
- Encryption practices documentation: data at rest and in transit
- Incident response plan: documented procedure for security incident detection, containment, and notification

**Red Flags:**
- No security audit has ever been conducted
- Customer data is transmitted without encryption
- Access controls are not implemented — all team members have full system access
- No incident response plan exists
- Security certifications required by enterprise customers are not in progress and have no planned timeline

**Expected Outputs:** A security and privacy posture assessment rated against a five-domain framework: access control, data encryption, vulnerability management, incident response, and compliance certification. Each domain rated as Implemented, In Progress, or Absent. Enterprise readiness flag raised if any certification required by the target customer segment is absent with no remediation plan.

---

#### D03 > Technical Debt

**Definition:** Technical debt measures the accumulation of suboptimal engineering decisions — shortcuts, deferred refactoring, missing tests, deprecated dependencies, and architectural compromises — that must eventually be addressed at a cost to development velocity and system stability.

**Purpose:** Technical debt is an invisible liability that consumes engineering capacity without producing new value. Evaluators assess it to determine whether the startup's current development pace is sustainable or whether it is being maintained by consuming future engineering capacity through debt accumulation.

**Why It Matters:** Technical debt that is acknowledged and managed is a normal and often rational part of early-stage development. Technical debt that is unacknowledged, growing, and unmanaged is a strategic risk: it will eventually slow development to a rate below that needed to compete, and require a debt-paydown effort that consumes capital without producing customer value.

**Dependencies:** Depends on `D03 > Engineering Quality` (debt is the inverse of quality); depends on `D02 > Development Velocity` (high debt reduces velocity over time).

**Relationships:** Informs `D15 > Technology Scalability` (unmanaged debt prevents scaling); influences `D07 > Capital Efficiency` (debt repayment consumes engineering capital without revenue impact); feeds `D13 > Technology Risk`.

**Evidence Sources:**
- Technical debt register: a documented list of known debt items with estimated remediation cost
- Static analysis tool output (e.g., SonarQube debt ratio metric)
- Engineering team's self-assessment of the top three areas of debt and their impact
- Development velocity trend over time: declining velocity often signals debt accumulation
- Proportion of sprint capacity allocated to maintenance vs. new feature development

**Red Flags:**
- Engineering team cannot name specific areas of technical debt — either they do not know or the culture does not acknowledge it
- More than 40% of sprint capacity is consistently spent on maintenance, bug fixes, and refactoring
- Critical features are being deferred because the codebase is "too fragile to change in that area"
- No debt remediation effort has been planned or budgeted
- The system requires a full rewrite before it can be deployed to enterprise customers at scale

**Expected Outputs:** A technical debt exposure assessment classifying overall debt level as Managed (tracked, known, and being addressed), Accumulating (growing faster than it is being addressed), or Critical (debt is actively blocking development or commercial deployment). Includes a summary of the highest-impact debt items and their estimated remediation cost in engineering weeks.

---

#### D03 > Infrastructure Resilience

**Definition:** Infrastructure resilience measures the reliability, availability, and disaster recovery capability of the startup's technical infrastructure — encompassing uptime performance, redundancy architecture, backup practices, incident detection, and recovery time objectives.

**Purpose:** For any startup deploying a product to real customers, infrastructure resilience directly affects customer experience, service level agreement compliance, and revenue continuity. Evaluators assess it to determine whether the infrastructure is capable of meeting the reliability expectations of the target customer segment.

**Why It Matters:** Infrastructure outages produce direct revenue loss, customer churn, and reputational damage. Enterprise customers require documented uptime guarantees and disaster recovery capabilities before procurement. A startup without resilient infrastructure cannot serve enterprise customers, limiting its addressable market.

**Dependencies:** Depends on `D03 > Technical Architecture` (resilience is a property of architectural design choices — redundancy, load balancing, failover); depends on `D03 > Security & Privacy` (security incidents are a leading cause of infrastructure failures).

**Relationships:** Informs `D18 > Enterprise Readiness`; influences `D13 > Technology Risk`; feeds `D11 > Operational Risk Controls`.

**Evidence Sources:**
- Historical uptime records: trailing 12-month availability percentage
- Infrastructure architecture diagram showing redundancy and failover design
- Disaster recovery plan with Recovery Time Objective (RTO) and Recovery Point Objective (RPO) specifications
- Backup and restore test records: evidence that backups are tested, not just created
- Incident post-mortem reports from any production outage in the past 12 months

**Red Flags:**
- No backup of production database or backup has never been restoration-tested
- Single-region deployment with no failover for a product serving enterprise customers
- No monitoring or alerting system: outages are discovered by customers before the team is aware
- SLA commitments to customers exceed what the infrastructure is architecturally capable of delivering
- No disaster recovery plan exists

**Expected Outputs:** An infrastructure resilience score (1–5) across four dimensions: redundancy architecture, backup and recovery, monitoring and alerting, and incident response process. Includes the documented historical uptime percentage and a flag if the architecture cannot support the reliability levels committed to customers.

---

#### D03 > Technical Team Capability

**Definition:** Technical team capability measures the collective technical competence of the engineering and technical staff — their depth in relevant technologies, their experience with production systems at the required scale, their ability to make and implement sound architectural decisions, and their capacity to grow the codebase without accumulating crippling quality debt.

**Purpose:** The technical team is the primary asset through which all technology dimensions are realised. Evaluators assess technical team capability to determine whether the startup has the human technical capital to build and maintain the technology at the level required for its commercial goals.

**Why It Matters:** Technical capability gaps compound: a team without depth in a critical area makes poor decisions in that area consistently, producing technical debt, security vulnerabilities, or architectural limitations that are expensive to remediate. Hiring to fill technical capability gaps takes time and capital that is not always available.

**Dependencies:** Depends on `D01 > Technical Competence` (founder technical capability sets the ceiling for what the team is empowered to do); depends on `D01 > Team Building` (technical team quality is a function of the founder's ability to recruit).

**Relationships:** Directly informs `D03 > Engineering Quality`; influences `D04 > TRL Advancement Trajectory`; feeds `D15 > Team Scalability`.

**Evidence Sources:**
- Technical team roster with individual credentials, prior company history, and specialisation
- Technical assessment results from structured engineering interviews
- Past technical work products: open-source contributions, patents, publications
- Code review output as a proxy for team engineering standard
- Advisor or reference checks from prior engineering colleagues or managers

**Red Flags:**
- Technical team has no member with production experience at a scale greater than the current product's scale targets
- Key technical roles are vacant with no credible hiring plan
- Technical team is entirely composed of junior engineers with no senior or principal-level engineers
- All critical technical knowledge is concentrated in one person with no knowledge transfer to the team
- Technical team has not shipped a production-grade system in a previous role

**Expected Outputs:** A technical team capability profile covering: seniority distribution, specialisation coverage relative to product requirements, experience at required scale, and knowledge concentration risk. Flags any critical capability gap not addressed by current team or hiring plan.
