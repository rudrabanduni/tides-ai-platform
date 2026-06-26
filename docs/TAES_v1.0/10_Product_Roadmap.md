# TIDES AI Evaluation Standard — Product Roadmap

> **Document:** TAES v1.0 / Product Roadmap
> **Classification:** Internal Technical Standard
> **Version:** 1.0.0
> **Status:** Active
> **Authored:** 2026-06-23
> **Owner:** TIDES Platform Engineering

---

## Table of Contents

1. [Document Purpose and Scope](#1-document-purpose-and-scope)
2. [Roadmap Philosophy and Design Principles](#2-roadmap-philosophy-and-design-principles)
3. [Cross-Phase Dependency Overview](#3-cross-phase-dependency-overview)
4. [Phase 1 — Internal Incubator Platform](#4-phase-1--internal-incubator-platform)
5. [Phase 2 — Enterprise Evaluation Engine](#5-phase-2--enterprise-evaluation-engine)
6. [Phase 3 — Multi-Incubator SaaS](#6-phase-3--multi-incubator-saas)
7. [Phase 4 — Investor Intelligence Platform](#7-phase-4--investor-intelligence-platform)
8. [Phase 5 — Government Startup Evaluation Platform](#8-phase-5--government-startup-evaluation-platform)
9. [Phase 6 — Founder Self-Evaluation Platform](#9-phase-6--founder-self-evaluation-platform)
10. [Future AI Capabilities (Post–Phase 6)](#10-future-ai-capabilities-postphase-6)
11. [Future Analytics Capabilities](#11-future-analytics-capabilities)
12. [Future Benchmarking Infrastructure](#12-future-benchmarking-infrastructure)
13. [Future Simulation Engine](#13-future-simulation-engine)
14. [The Principle of Incremental Evolution](#14-the-principle-of-incremental-evolution)
15. [Appendix A — Phase Completion Checklist Summary](#15-appendix-a--phase-completion-checklist-summary)

---

## 1. Document Purpose and Scope

This document defines the official product roadmap for the TIDES AI Evaluation Standard (TAES) platform, version 1.0. It is not a feature wishlist and must not be treated as one. It is a structured, milestone-driven engineering roadmap that defines:

- The phased expansion of platform scope from single-incubator deployment to global SaaS infrastructure
- The specific technical milestones that gate phase completion
- The dependency relationships between phases that govern sequencing
- The new AI capabilities, analytics modules, and integrations introduced at each phase
- The technical debt risks that must be mitigated at each decision point to preserve architectural integrity across future phases

This document is intended for the TIDES platform engineering team, product leadership, external engineering partners, technical due diligence reviewers, and programme delivery leads. It assumes familiarity with the TIDES AI Evaluation Framework, the TAES dimension taxonomy, and the agent orchestration architecture described in companion documents.

The roadmap covers six formally defined phases plus four forward-looking sections on capabilities beyond Phase 6. Each phase is defined with enough specificity for an engineering team to produce sprint-level work breakdown structures without requiring additional clarification.

---

## 2. Roadmap Philosophy and Design Principles

### 2.1 Progressive Scope Expansion

The TIDES platform is designed to serve fundamentally different user classes across its lifetime: incubator programme managers, enterprise accelerator directors, institutional investors, government programme administrators, and individual founders. Each user class has distinct data access requirements, privacy expectations, compliance obligations, and evaluation objectives.

The roadmap addresses this diversity not by building a monolithic system that attempts to serve all users from Day 1, but by progressively expanding scope in a controlled sequence. Each phase is designed to prove one specific value hypothesis before the next phase is funded and built.

### 2.2 No Destructive Transitions

A core architectural constraint of this roadmap is that no phase transition should require breaking changes to the data model, API contracts, or evaluation schema that were established in a previous phase. Every design decision in each phase must be made with awareness of the next two phases. Where a Phase 1 decision is known to require revision in Phase 3, that revision must be planned in Phase 1 and implemented as a non-destructive migration.

### 2.3 Evaluation Standard Stability

The TAES evaluation standard — the dimension taxonomy, scoring weights, evidence classification rules, and agent behaviour specifications — is versioned independently of the platform. Platform phases may introduce new evaluation dimensions or reconfigure existing ones, but all changes must follow the TAES versioning protocol. The platform must support running evaluations under TAES v1.0 and any later version simultaneously, to preserve comparability of historical evaluations.

### 2.4 Data Sovereignty and Isolation

Every architectural decision involving multi-tenancy, data storage, or external integrations must treat data isolation as a non-negotiable constraint. No evaluation data from one tenant (incubator, investor firm, government programme) may be readable, inferable, or statistically derivable by another tenant. This principle applies even when aggregate analytics are shared across tenant boundaries.

---

## 3. Cross-Phase Dependency Overview

The following table defines the formal dependency relationships between phases. A phase listed in the "Depends On" column must reach its completion criteria before the dependent phase may begin development.

| Phase | Name | Depends On | Can Overlap With |
|-------|------|------------|-----------------|
| 1 | Internal Incubator Platform | None | None |
| 2 | Enterprise Evaluation Engine | Phase 1 (complete) | None |
| 3 | Multi-Incubator SaaS | Phase 2 (complete) | Phase 4 (planning only) |
| 4 | Investor Intelligence Platform | Phase 3 (complete) | Phase 5 (planning only) |
| 5 | Government Startup Evaluation Platform | Phase 3 (complete), Phase 4 (API layer stable) | Phase 6 (planning only) |
| 6 | Founder Self-Evaluation Platform | Phase 4 (complete), Phase 5 (complete) | None |

### 3.1 Dependency Rationale

**Phase 2 depends on Phase 1 completion** because the multi-cohort configuration system in Phase 2 requires a stable, battle-tested single-cohort evaluation pipeline. Building multi-cohort logic on an unvalidated pipeline introduces compound defect risk.

**Phase 3 depends on Phase 2 completion** because multi-tenancy requires that the scoring engine, analytics layer, and API surface are fully stabilised. Introducing tenant isolation on a mutable codebase generates prohibitive technical debt.

**Phase 4 depends on Phase 3 completion** because investor-facing portfolio analytics require access to normalised cross-company evaluation data, which only becomes available once the platform is operating with multiple incubator tenants producing comparable evaluation outputs.

**Phase 5 depends on Phase 3 completion and Phase 4 API stability** because government programmes require the audit trail and evidence archiving infrastructure built in Phase 3, and the cross-programme benchmarking capabilities require the normalised scoring infrastructure built in Phase 4.

**Phase 6 depends on both Phase 4 and Phase 5 completion** because the founder self-evaluation module requires access to anonymised benchmark data from investor screenings (Phase 4) and government programme evaluations (Phase 5) to provide founders with meaningful comparative positioning.

### 3.2 Phase Dependency Diagram

```
Phase 1 ──────────────────────────────────────────────► Phase 2
                                                              │
                                                              ▼
                                                         Phase 3
                                                        /        \
                                                       ▼          ▼
                                                  Phase 4      Phase 5
                                                       \          /
                                                        ▼        ▼
                                                         Phase 6
```

---

## 4. Phase 1 — Internal Incubator Platform

### 4.1 Phase Objective

Phase 1 establishes the TIDES platform as a functioning, production-grade evaluation system operating within a single incubator environment. The objective of this phase is not completeness — it is proof. Specifically, it must be demonstrated that the TAES evaluation standard can be operationalised at scale, that AI-generated evaluation outputs are trusted and acted upon by human programme managers, and that the platform produces consistent, explainable, and reproducible scores across a real cohort of startups under real programme conditions. This phase is the foundation upon which all subsequent phases are built. Every architectural decision made here carries forward.

### 4.2 Prerequisite State

Phase 1 has no platform prerequisites. However, the following pre-conditions must be satisfied before Phase 1 development begins:

- The TAES dimension taxonomy (v1.0) must be formally published, including all dimension definitions, evidence type classifications, scoring weight tables, and agent behaviour specifications.
- A pilot incubator partner must be formally committed, with a minimum of one active cohort of at least 8 startups available for evaluation within the Phase 1 window.
- A baseline LLM provider must be selected, contracted, and its API latency and throughput characteristics documented under expected load.
- The core engineering team (minimum: 2 backend engineers, 1 ML engineer, 1 frontend engineer) must be in place.
- A data processing agreement (DPA) must be executed between the platform operator and the pilot incubator, governing how startup submission data is processed and stored.

### 4.3 Key Milestones

**Milestone 1.1 — Core Data Ingestion Pipeline Operational**
The platform can accept structured startup submissions via a defined ingestion schema (JSON). Documents including pitch decks, business plans, financial projections, and team profiles are parsed, chunked, and stored in a retrieval-indexed format. All ingested data is associated with a startup_id and cohort_id. Processing time from submission to indexed state must be under 3 minutes for a standard 30-page submission package.

**Milestone 1.2 — Single-Dimension Evaluation Agent Live**
One TAES evaluation dimension (recommended: Market Opportunity, as it is the most structurally complex) is implemented as a functioning AI agent. The agent accepts a startup's indexed document set, executes structured retrieval queries, applies the dimension-specific rubric, and produces a dimension score with a minimum of three cited evidence fragments and a narrative justification paragraph. Output passes a human review by two domain experts before the milestone is accepted.

**Milestone 1.3 — Full 10-Dimension Evaluation Pipeline Complete**
All ten TAES evaluation dimensions are implemented as agents and have been validated against synthetic test cases covering edge conditions (missing evidence, contradictory evidence, over-claimed evidence). The orchestrator agent correctly sequences and parallelises dimension evaluations according to the dependency graph defined in the TAES specification. End-to-end evaluation of a single startup from submission to final report generation completes within 8 minutes.

**Milestone 1.4 — Human Review Interface Deployed**
A web-based interface is deployed for programme managers to review, annotate, override, and accept AI-generated evaluation outputs. The interface presents dimension scores, evidence citations, and narrative justifications. Override actions are logged with a mandatory reason field. The interface supports exporting a final evaluation report as a structured PDF.

**Milestone 1.5 — First Cohort Evaluation Complete**
A full cohort of at least 8 startups from the pilot incubator partner has been evaluated end-to-end using the platform. All evaluation reports have been reviewed and accepted (or overridden with documented reasons) by programme managers. Inter-rater reliability between AI scores and independent human scores on the same submissions must be documented.

**Milestone 1.6 — Audit Log and Data Retention Infrastructure**
Every evaluation event — submission ingestion, agent invocation, score generation, human override, report export — is logged to an append-only audit trail with timestamps, operator identity, and event payload. Log storage uses a format that supports export for external review. Retention policy (minimum 7 years) is enforced by automated expiry controls.

**Milestone 1.7 — Internal Admin Dashboard**
A minimal internal dashboard displays cohort-level statistics: number of startups evaluated, average scores by dimension, score distribution, pending reviews, and override rate. This is not a public analytics product — it is a programme operations tool.

### 4.4 New Modules Introduced

| Module | Description |
|--------|-------------|
| **Document Ingestion Service** | Accepts, validates, parses, and indexes startup submission packages. Handles PDF, DOCX, PPTX, and structured JSON formats. |
| **Dimension Evaluation Agents (×10)** | One agent per TAES dimension, each implementing the dimension rubric as a structured prompt chain with retrieval augmentation. |
| **Orchestrator Agent** | Sequences and parallelises dimension agent invocations, aggregates outputs, and computes composite TIDES Score. |
| **Evidence Citation Engine** | Extracts and indexes specific document passages that support or contradict each dimension claim. Associates citations with scores. |
| **Human Review Interface (HRI)** | Web UI for programme managers to review, annotate, override, and accept evaluation outputs. |
| **Evaluation Report Generator** | Produces structured PDF and JSON evaluation reports from completed dimension outputs. |
| **Audit Log Service** | Append-only event log for all platform actions with tamper-evident storage. |
| **Internal Admin Dashboard** | Cohort-level operations visibility for programme staff. |

### 4.5 New AI Capabilities

- **Retrieval-Augmented Generation (RAG) pipeline** for startup documents, using chunking strategies optimised for business documents (pitch deck section boundaries, financial table extraction, team bio segmentation).
- **Per-dimension structured prompt chains** implementing rubric logic as multi-step reasoning sequences with explicit evidence gathering steps prior to scoring.
- **Contradiction detection** within single-startup document sets: the agent identifies cases where a claim in the pitch deck is contradicted by data in the financial model or market research appendix.
- **Confidence scoring** per dimension: each agent produces a confidence value (0.0–1.0) reflecting the quantity and quality of retrieved evidence. Low-confidence scores are automatically flagged for mandatory human review.
- **Missing evidence detection**: agents explicitly identify which rubric criteria could not be scored due to absent evidence and record these as structured gaps rather than defaulting to zero scores.

### 4.6 New Analytics

- **Cohort Score Summary**: aggregate dimension scores across a cohort with mean, median, and standard deviation per dimension.
- **Score Distribution Chart**: histogram of composite TIDES Scores across a cohort, segmented by sector and founding stage.
- **Override Rate Tracking**: percentage of AI-generated scores overridden by human reviewers, segmented by dimension, to identify dimensions where model performance is weakest.
- **Evidence Gap Heatmap**: matrix showing, per dimension per startup, the proportion of rubric criteria that could not be scored due to missing evidence.
- **Evaluation Throughput Metrics**: pipeline latency, queue depth, and per-agent processing time for operational monitoring.

### 4.7 New Integrations

| Integration | Purpose | Protocol |
|-------------|---------|---------|
| **LLM Provider API** | Powers all evaluation agents | REST/HTTPS with API key authentication |
| **Document Storage (S3-compatible)** | Stores raw submission documents | S3 API, server-side encryption |
| **Vector Store** | Hosts document embeddings for RAG | Self-hosted or managed (Qdrant/Weaviate/Pinecone) |
| **PDF Generation Service** | Renders structured evaluation reports | Internal service or headless Chrome |
| **Email Notification Service** | Notifies programme managers of completed evaluations | SMTP/SendGrid |

### 4.8 Completion Criteria

Phase 1 is complete when ALL of the following conditions are satisfied:

1. A minimum of 8 startups from a real cohort have been evaluated end-to-end with no unhandled pipeline failures.
2. The inter-rater reliability coefficient (Cohen's Kappa or ICC) between AI-generated dimension scores and independent human expert scores is ≥ 0.65 across all ten dimensions, measured on at least 5 startups.
3. Human reviewers (programme managers) report that AI-generated narrative justifications are "useful" or "very useful" in structured feedback collected after the pilot cohort evaluation, with ≥ 75% positive rating.
4. End-to-end evaluation latency (submission to report) is ≤ 8 minutes at p95 under concurrent load of 5 simultaneous evaluations.
5. Audit log coverage is 100%: every platform action traceable to an operator identity and timestamp with no gaps.
6. The human review interface supports all core review workflows with no workarounds required by users.
7. A documented post-mortem of the pilot cohort evaluation has been completed, identifying at minimum: top 3 model failure modes, top 3 UX pain points, and top 3 data quality issues encountered.

### 4.9 Technical Debt Considerations

**Document schema flexibility**: The document ingestion schema must be designed to support schema versioning from the start. A rigid schema that cannot evolve without re-ingesting all documents will block Phase 2's multi-cohort ingestion needs.

**Prompt chain versioning**: Every agent prompt chain must be stored as a versioned artefact, not as inline code strings. Evaluations must record which prompt version was used. Failure to do this makes it impossible to reproduce historical evaluations after prompt updates.

**Vector store selection**: The vector store chosen in Phase 1 must support multi-tenancy (namespace isolation) before Phase 3 requires it. Choosing a store that does not support this will require a full data migration in Phase 3.

**Score data model**: The score entity must include fields for `evaluation_version`, `model_id`, `prompt_version`, `confidence`, `override_flag`, and `override_reason` from the start. Retrofitting these fields in Phase 2 is expensive.

**API surface**: Even for internal use, all backend services should expose versioned REST APIs (e.g., `/v1/evaluations`). Internal direct calls bypass the contract layer and make Phase 3 API productisation significantly harder.

### 4.10 Estimated Complexity

**Baseline reference: Phase 1 = 1.0×**

Phase 1 is the complexity baseline. All subsequent phases are rated relative to it. The primary complexity drivers in Phase 1 are: prompt engineering for ten diverse evaluation dimensions, RAG pipeline tuning for low-quality business documents, and the human review interface UX design. Absolute engineering estimate: 12–18 person-months for an experienced team.

---

## 5. Phase 2 — Enterprise Evaluation Engine

### 5.1 Phase Objective

Phase 2 transforms the TIDES platform from a single-cohort evaluation tool into an enterprise-grade evaluation engine capable of serving a large incubator or accelerator that runs multiple cohorts simultaneously, applies different scoring configurations to different programme types, and requires comprehensive analytics to manage programme performance. The core value addition of this phase is configurability and scale: a programme manager must be able to configure a new cohort with a custom evaluation profile (adjusted dimension weights, sector-specific rubric overlays, custom evidence requirements) without engineering intervention, and the platform must handle concurrent evaluation of 50+ startups across multiple active cohorts without degradation.

### 5.2 Prerequisite State

- Phase 1 must be complete (all completion criteria satisfied).
- At least one post-pilot cohort evaluation (beyond the Phase 1 pilot) must have been completed, demonstrating that the platform operates reliably outside of supervised pilot conditions.
- The Phase 1 post-mortem findings must have been reviewed and the top model failure modes and UX pain points addressed or formally accepted as known limitations.
- Prompt chain versioning infrastructure from Phase 1 must be in place.
- The score data model must include all fields specified in Phase 1's technical debt considerations.

### 5.3 Key Milestones

**Milestone 2.1 — Cohort Configuration System**
Programme managers can create and configure cohorts through the platform UI without engineering involvement. Configuration includes: cohort name and dates, participant sector tags, dimension weight overrides (within permitted bounds defined by TAES v1.0), evidence requirement overrides (e.g., requiring audited financials for later-stage cohorts), and evaluation report template selection. Configuration changes are versioned and the effective configuration at the time of each evaluation is stored with the evaluation record.

**Milestone 2.2 — Sector-Specific Rubric Overlays**
The evaluation engine supports sector-specific rubric overlays that modify how generic TAES rubric criteria are interpreted for specific sectors (e.g., for a deep-tech cohort, the Technology Readiness dimension applies TRL-based scoring criteria; for a consumer startup cohort, the Market Opportunity dimension applies retail market sizing methodology). Overlays are defined in a structured YAML format and loaded at evaluation time based on cohort configuration. A minimum of 5 sector overlays (Deep Tech, Consumer, FinTech, AgriTech, HealthTech) must be built and validated.

**Milestone 2.3 — Concurrent Evaluation Architecture**
The evaluation pipeline is refactored to support concurrent processing of multiple startups across multiple cohorts. A task queue (e.g., Celery with Redis, or AWS SQS) manages evaluation jobs. Agent invocations are parallelised within a single startup's evaluation and across startups. The system must maintain stable throughput when processing 10 simultaneous startup evaluations without timeout or queue overflow failures. Resource isolation between cohorts prevents a large cohort from starving a smaller one.

**Milestone 2.4 — Scoring Analytics Dashboard (v1)**
A full-featured analytics dashboard for programme managers is deployed. It displays cohort performance metrics, inter-cohort comparison (for programmes running multiple cohorts), dimension-level score trends over time, and outlier identification. The dashboard supports filtering by sector, stage, and date range. All charts are exportable as PNG and the underlying data is exportable as CSV.

**Milestone 2.5 — Comparative Startup Ranking Engine**
Within a cohort, startups are ranked on composite TIDES Score and per-dimension scores. The ranking engine supports configurable weighting for ranking purposes that may differ from evaluation scoring weights (e.g., an accelerator may prioritise the Team dimension for selection but evaluate all ten dimensions). Rankings are re-computed when human overrides change underlying scores.

**Milestone 2.6 — Bulk Submission Ingestion**
The platform supports bulk ingestion of startup submissions via a ZIP archive or CSV manifest with document links. A batch ingestion job processes up to 50 submissions in a single batch, with per-submission status tracking, failure reporting, and partial batch completion (failed submissions do not block successful ones).

**Milestone 2.7 — Evaluation Report Versioning**
When a human override changes an underlying score, the system creates a new version of the evaluation report rather than overwriting the previous version. Programme managers can view the full version history of an evaluation report. The final accepted version is marked as canonical.

**Milestone 2.8 — Programmatic API (v1) for Evaluation Results**
A documented REST API (v1) allows external systems (e.g., incubator CRM, portfolio management tools) to query evaluation results, cohort statistics, and startup rankings. The API uses token-based authentication and returns JSON. Rate limiting and usage logging are implemented. This API is the precursor to the productised API in Phase 3.

### 5.4 New Modules Introduced

| Module | Description |
|--------|-------------|
| **Cohort Configuration Manager** | UI and backend for creating, configuring, versioning, and managing cohorts. |
| **Rubric Overlay Engine** | Loads and applies sector-specific rubric overlays at evaluation time. |
| **Task Queue and Job Orchestrator** | Manages concurrent evaluation jobs across cohorts with priority queuing and failure recovery. |
| **Scoring Analytics Dashboard (v1)** | Programme manager-facing analytics with cohort comparison, dimension trends, and outlier detection. |
| **Ranking Engine** | Configurable startup ranking within and across cohorts based on composite and dimension scores. |
| **Bulk Ingestion Processor** | Batch document ingestion with per-submission status tracking and failure isolation. |
| **Evaluation Report Version Manager** | Tracks and stores multiple versions of evaluation reports for a single startup. |
| **Public API Gateway (v1)** | Authenticated REST API exposing evaluation results and cohort statistics to external systems. |

### 5.5 New AI Capabilities

- **Sector-adaptive prompt chains**: Prompt chains for each dimension are parameterised to accept sector overlay instructions, modifying the evidence retrieval queries and scoring criteria applied without requiring separate agents per sector.
- **Cross-startup comparative analysis agent**: A new agent that, after individual startup evaluations are complete for a cohort, performs a structured pairwise comparison across startups in the same cohort to identify outliers, rank discriminators, and pattern clusters. This agent does not change individual scores but produces cohort-level analytical commentary.
- **Evidence quality scoring**: The evidence citation engine is upgraded to assess not just the presence of evidence but its quality: specificity, recency, source authority, and internal consistency with other cited evidence. Quality scores are surfaced in the human review interface and factored into confidence scores.
- **Dimension drift detection**: When a startup submits updated documents (e.g., revised financials for a re-evaluation), the agent explicitly identifies which evidence fragments have changed and whether those changes affect the dimension score, producing a structured change delta rather than a full re-evaluation.

### 5.6 New Analytics

- **Cohort Comparison Matrix**: side-by-side dimension score comparison across multiple cohorts run in the same programme period.
- **Dimension Reliability Index**: per-dimension tracking of override rate, confidence score distribution, and evidence gap rate across all evaluations to date, indicating which dimensions have the highest and lowest AI reliability.
- **Stage-Adjusted Benchmarks**: dimension score norms computed separately for pre-revenue, early-revenue, and growth-stage startups to enable stage-appropriate comparison.
- **Evaluation Velocity Tracking**: time from submission to report completion, time to human review, and time to final acceptance — broken down by cohort and reviewer to identify process bottlenecks.
- **Top-N Startup Report**: ranked shortlist report for decision makers, showing top-N startups by configurable criteria with one-paragraph AI-generated summaries per startup.

### 5.7 New Integrations

| Integration | Purpose | Protocol |
|-------------|---------|---------|
| **CRM Webhook Integration** | Pushes evaluation completion events to incubator CRM (HubSpot, Salesforce) | Webhook (HTTPS POST) |
| **Google Drive / SharePoint** | Pulls submission documents directly from linked folder | OAuth 2.0 + Drive/SharePoint API |
| **LinkedIn (Founder Verification)** | Retrieves public founder profile data to supplement team evaluation | LinkedIn API (read-only) |
| **Companies House / MCA API** | Retrieves company registration and director data for UK/India registered companies | REST API |
| **Power BI / Tableau Embed** | Embeds cohort analytics into external BI dashboards via embed token | REST + iframe embed |

### 5.8 Completion Criteria

Phase 2 is complete when ALL of the following conditions are satisfied:

1. The platform has successfully processed a minimum of 3 simultaneously active cohorts with at least 15 startups each, without pipeline failures or resource contention incidents.
2. Programme managers can create and fully configure a new cohort through the UI with zero engineering involvement, as verified by an unsupervised user acceptance test.
3. At least 5 sector rubric overlays are live, validated against at least 3 real evaluations each.
4. The comparative ranking engine produces rankings that programme managers rate as "aligned" or "mostly aligned" with their independent manual rankings in ≥ 80% of cases.
5. The v1 API is documented (OpenAPI spec), deployed, and has been integrated by at least one external system (CRM or BI tool).
6. Evaluation throughput supports 10 concurrent startup evaluations with p95 latency ≤ 12 minutes and zero queue overflow failures in a 48-hour stress test.
7. A formal capacity planning document has been produced, projecting infrastructure costs and performance characteristics at 10×, 50×, and 100× Phase 2 evaluation volume.

### 5.9 Technical Debt Considerations

**Rubric overlay schema**: The overlay schema must be designed for extension from Phase 2. If sector overlays are hard-coded rather than schema-driven, Phase 3's multi-tenant overlay management (where each tenant may define custom overlays) becomes a full rewrite.

**Task queue architecture**: The task queue must support named priority queues from the start. A single flat queue will cause SLA violations in Phase 4 when investor-tier evaluations require guaranteed processing windows.

**API versioning discipline**: The v1 API must be treated as immutable once published. Phase 3 may introduce a v2 API with additional tenant-scoping capabilities, but v1 must remain functional for all Phase 2 integrations.

**Multi-tenant data structures in analytics**: Even though Phase 2 serves a single incubator, all analytics queries should be written with a `tenant_id` scoping clause from the start. Retrofitting tenant scoping into analytics queries at Phase 3 is a high-risk data isolation exercise.

### 5.10 Estimated Complexity

**Relative to Phase 1: 1.8×**

The primary complexity drivers are: concurrent task queue architecture, rubric overlay engine design (which must be both flexible and constrained), and the analytics dashboard (data modelling for multi-dimensional time-series analysis of evaluation results). The v1 API is straightforward but requires formal API design and documentation discipline. Absolute engineering estimate: 20–28 person-months.

---

## 6. Phase 3 — Multi-Incubator SaaS

### 6.1 Phase Objective

Phase 3 transforms the TIDES platform into a commercially deployable Software-as-a-Service product capable of serving multiple independent incubator organisations simultaneously, each with full data isolation, custom branding, and independent configuration. The primary objective of this phase is not to add new evaluation capabilities — those are largely mature from Phase 2 — but to solve the engineering problems of multi-tenancy: data segregation, billing, onboarding, white-labelling, and service-level management at scale. A secondary objective is to establish the platform's commercial operating model (subscription tiers, usage quotas, service-level agreements) and to build the operational infrastructure (support, monitoring, incident response) required to serve paying enterprise customers.

### 6.2 Prerequisite State

- Phase 2 must be complete (all completion criteria satisfied).
- All analytics queries and data models must have `tenant_id` scoping in place (required from Phase 2 technical debt decisions).
- The vector store must support namespace or collection-level isolation (required from Phase 1 technical debt decisions).
- A commercial legal framework (subscription agreement template, DPA template, SLA definition) must be prepared for tenant onboarding.
- A minimum of 2 prospective incubator tenants (beyond the Phase 1/2 pilot partner) must be identified and commercially committed before Phase 3 development begins.

### 6.3 Key Milestones

**Milestone 3.1 — Multi-Tenant Data Architecture**
The platform's data architecture is formally restructured to enforce strict per-tenant isolation at every layer: relational database (schema-per-tenant or row-level security with mandatory `tenant_id` predicate), vector store (namespace isolation), object storage (per-tenant bucket or prefix with IAM boundary policies), and audit logs (physically segregated log streams). A penetration test specifically targeting cross-tenant data leakage must be passed before this milestone is accepted.

**Milestone 3.2 — Tenant Onboarding and Provisioning System**
A self-service onboarding flow allows a new incubator to sign up, verify their organisation, select a subscription tier, and reach a fully operational platform environment within 24 hours. Provisioning creates the tenant's data environment, assigns an administrative user, configures default settings, and sends onboarding documentation. The provisioning process is fully automated with no manual engineering steps.

**Milestone 3.3 — White-Label Branding System**
Each tenant can configure their platform environment with their own logo, primary colour palette, domain name (via CNAME), and email sender identity. Evaluation reports generated for their startups carry the tenant's branding, not the TIDES platform branding. White-label configuration is managed through a self-service UI available to tenant administrators.

**Milestone 3.4 — Subscription and Billing Infrastructure**
A billing system tracks each tenant's usage (number of evaluations, number of active users, API call volume) against their subscription tier. Billing is automated monthly via a payment gateway (Stripe). Usage dashboards are available to tenant administrators. Overage notifications are sent at 80% and 95% of quota limits. Tenants can upgrade or downgrade their tier through the platform UI.

**Milestone 3.5 — Tenant Administration Console**
A full-featured tenant administration console allows incubator administrators (not TIDES platform staff) to: manage user accounts and roles within their organisation, configure their cohorts and sector overlays, view their usage metrics, manage their billing details, access their audit logs, and submit support requests. This console is entirely scoped to the administrator's own tenant — no cross-tenant visibility is possible.

**Milestone 3.6 — Service Level Agreement Monitoring**
The platform monitors and reports on SLA metrics per tenant: evaluation pipeline latency (p50, p95, p99), API availability, and report generation success rate. SLA breaches are automatically detected and trigger an internal incident response workflow. A tenant-facing SLA dashboard shows their real-time service status and historical uptime.

**Milestone 3.7 — Cross-Tenant Anonymised Benchmarks (v1)**
The first version of the cross-tenant benchmark dataset is produced: anonymised, aggregated dimension score distributions drawn from all tenant evaluation data, with no data point traceable to a specific tenant or startup. These benchmarks are surfaced in each tenant's analytics dashboard, allowing them to compare their cohort's dimension performance against the anonymised platform-wide distribution. The anonymisation methodology must be formally reviewed before publication.

**Milestone 3.8 — Platform Operations Runbook**
A comprehensive operational runbook is produced covering: incident classification and response procedures, tenant data export procedures, backup and recovery procedures, scaling procedures (horizontal and vertical), and deprecation procedures for major platform components. This runbook is required before the platform is considered commercially operable.

### 6.4 New Modules Introduced

| Module | Description |
|--------|-------------|
| **Multi-Tenant Data Isolation Layer** | Enforces per-tenant data segregation at DB, vector store, object storage, and audit log levels. |
| **Tenant Provisioning Engine** | Automates creation of a complete, isolated tenant environment on signup. |
| **White-Label Configuration Manager** | Manages tenant-specific branding assets, domain configuration, and report templates. |
| **Billing and Quota Management** | Tracks usage, enforces quotas, manages subscriptions, and integrates with Stripe. |
| **Tenant Administration Console** | Self-service admin UI scoped to a single tenant's environment. |
| **SLA Monitoring Service** | Tracks per-tenant SLA metrics and triggers incident workflows on breach. |
| **Anonymised Benchmark Engine (v1)** | Produces cross-tenant anonymised benchmark datasets with differential privacy controls. |
| **Support Ticket Integration** | Routes tenant support requests to the internal support platform (Zendesk/Freshdesk). |

### 6.5 New AI Capabilities

- **Automated onboarding rubric calibration**: When a new tenant onboards, an onboarding agent analyses the tenant's stated programme focus (sector, stage, geography) and recommends a pre-configured rubric overlay and dimension weight profile as a starting point, which the tenant administrator can then customise.
- **Cross-cohort pattern recognition** (anonymised): An analytical AI layer processes anonymised, aggregated evaluation data across all tenants to identify common patterns — e.g., which dimension gaps are most common across specific sectors, which evidence types are most predictive of high composite scores. These patterns are surfaced as platform-wide insights in a curated quarterly report, not as real-time tenant-facing features.
- **Language localisation for evaluation agents**: Evaluation agents are extended to process submission documents in languages beyond English, with structured translation pre-processing before rubric application. Initial support for Hindi, French, Arabic, and Portuguese.

### 6.6 New Analytics

- **Cross-Tenant Benchmark Dashboard**: shows each tenant how their cohort dimensions compare against anonymised platform-wide distributions, with percentile rankings.
- **Subscription Utilisation Report**: tenant-facing breakdown of their evaluation quota usage, API usage, storage consumption, and projected quota exhaustion date.
- **Tenant Health Scorecard** (internal, TIDES staff only): per-tenant engagement metrics — active cohorts, evaluation volume, API call frequency, support ticket rate — to identify at-risk tenants and expansion opportunities.
- **Platform-Wide Reliability Report**: weekly automated report on pipeline success rates, latency distributions, and SLA compliance across all tenants.

### 6.7 New Integrations

| Integration | Purpose | Protocol |
|-------------|---------|---------|
| **Stripe** | Subscription billing, invoicing, and payment processing | Stripe API + Webhooks |
| **Zendesk / Freshdesk** | Tenant support ticket routing | REST API |
| **Auth0 / Okta** | Enterprise SSO (SAML, OIDC) for large tenant organisations | SAML 2.0, OIDC |
| **Cloudflare / AWS CloudFront** | Custom domain routing for white-label deployments | DNS CNAME + CDN |
| **Datadog / New Relic** | Infrastructure monitoring, per-tenant latency tracking, SLA alerting | Agent + API |
| **AWS S3 + KMS** | Per-tenant encrypted object storage with key isolation | S3 + KMS API |

### 6.8 Completion Criteria

Phase 3 is complete when ALL of the following conditions are satisfied:

1. A minimum of 3 independent incubator tenants (excluding the Phase 1/2 pilot partner) have been onboarded, have completed at least one cohort evaluation, and are on active paid subscriptions.
2. A third-party penetration test targeting cross-tenant data isolation has been passed with no critical or high-severity findings.
3. The self-service onboarding flow has been completed by at least one tenant without any engineering team assistance, from signup to first evaluation, within the 24-hour provisioning SLA.
4. The billing system has executed at least one complete monthly billing cycle for all active tenants without manual intervention.
5. The anonymised benchmark dataset has been reviewed and approved by a data privacy officer before being surfaced to tenants.
6. The platform operations runbook is complete and has been tested via at least one simulated incident exercise.
7. Platform uptime across all tenants is ≥ 99.5% over a trailing 90-day period.

### 6.9 Technical Debt Considerations

**Anonymisation methodology**: The cross-tenant benchmark anonymisation approach must be formally reviewed against differential privacy standards. A weak anonymisation approach that is later found to leak tenant identity will require full dataset withdrawal and will be a commercial liability.

**Key management architecture**: Per-tenant encryption key management (KMS) is complex. Using a shared key for all tenants in Phase 3 because it is simpler will create a catastrophic migration challenge in Phase 5 when government tenants require per-tenant HSM-backed key isolation.

**API versioning for tenant scoping**: The v2 API introduced in Phase 3 must include `tenant_id` as a first-class parameter in all endpoints. Any endpoint that implicitly derives tenant context from the authentication token must document this behaviour clearly — failing to do so creates ambiguity in Phase 4's cross-tenant investor APIs.

**Subscription tier design**: Subscription tier limits (evaluation quota, user count, API rate limits) must be defined with Phase 4 and Phase 5 tier structures in mind. Retroactively restructuring tier limits for existing paying tenants is commercially and contractually complex.

### 6.10 Estimated Complexity

**Relative to Phase 1: 2.5×**

The primary complexity drivers are: multi-tenant data architecture (the most technically risky element of the entire roadmap), white-label domain routing, and the billing/quota system. The anonymised benchmark engine is moderately complex due to the privacy requirements. SaaS operations infrastructure (monitoring, runbooks, SLA management) adds significant non-engineering effort. Absolute engineering estimate: 28–40 person-months.

---

## 7. Phase 4 — Investor Intelligence Platform

### 7.1 Phase Objective

Phase 4 extends the TIDES platform to serve a fundamentally different user class: institutional investors — venture capital firms, angel networks, family offices, and corporate venture arms. While incubator programme managers use the platform to evaluate cohorts of startups for programme selection, investors use it to screen deal flow at scale, monitor portfolio company health over time, and compare investment opportunities using standardised, AI-generated evaluation metrics. This phase positions TIDES as a deal-flow intelligence layer that sits between startup applications and investment decisions, enabling investors to replace or augment inconsistent, relationship-driven screening processes with structured, reproducible, AI-powered due diligence signals.

### 7.2 Prerequisite State

- Phase 3 must be complete (all completion criteria satisfied), providing a stable multi-tenant platform.
- The anonymised cross-tenant benchmark dataset (Phase 3, Milestone 3.7) must be live, as it provides the comparative context investors require.
- A minimum of 2 VC firms or angel networks must be identified as design partners for Phase 4 and must have participated in requirement definition sessions.
- The v2 API must be stable and documented, as investor-facing integrations will be built on it.
- A legal review of the data sharing and derivative analytics implications of investor access to evaluation data from incubator-originated evaluations must be completed.

### 7.3 Key Milestones

**Milestone 4.1 — Investor Account Type and Permission Model**
A new account type ("Investor") is introduced with a distinct permission model. Investor accounts can: view evaluation reports for startups that have explicitly consented to investor visibility, receive evaluation data via API, create and manage deal pipelines, and access their own portfolio analytics. Investor accounts cannot access any evaluation data without explicit startup consent. The consent model is implemented as a cryptographically signed consent record stored in the audit log.

**Milestone 4.2 — Deal Flow Screening Pipeline**
Investors can create named deal pipelines and invite startups (or receive referrals from incubator tenants) to submit their documents directly for evaluation under the investor's configured rubric. The evaluation pipeline for investor-initiated submissions supports faster SLA tiers (p95 ≤ 5 minutes for initial screening score) and a two-stage evaluation flow: a lightweight initial screening evaluation (5 dimensions) and a full 10-dimension deep evaluation triggered by investor decision after screening.

**Milestone 4.3 — Portfolio Monitoring Dashboard**
Investors can designate evaluated startups as portfolio companies. Once designated, the system tracks all subsequent evaluation events (re-evaluations, updated submissions) for portfolio companies and surfaces changes in dimension scores over time. The portfolio dashboard shows each portfolio company's score trajectory, dimension changes, and AI-generated commentary on material changes.

**Milestone 4.4 — Cross-Portfolio Comparison Engine**
Investors can compare multiple startups — whether portfolio companies or deal flow candidates — on standardised TIDES dimensions using a structured comparison view. The comparison engine normalises scores against the platform benchmark dataset to show each company's percentile position, not just its raw score. Comparison sets can be saved and shared within an investor team.

**Milestone 4.5 — Investor-Configurable Scoring Profiles**
Investors can define custom scoring profiles — weighting adjustments that reflect their investment thesis — without modifying the underlying evaluation standard. A seed-stage deep-tech fund might weight Technology Readiness and Founder Profile at 2× relative to Market Opportunity; a growth-stage consumer fund might do the reverse. The platform computes both a standard TIDES Score and a thesis-weighted score for each evaluated startup, always clearly labelling which is which.

**Milestone 4.6 — Deal Room Data Room Integration**
The platform generates a structured digital data room package for each evaluated startup (with startup consent), containing the evaluation report, cited evidence fragments, dimension scores, and confidence assessments, formatted for sharing via a standard virtual data room tool (Dropbox, Intralinks, Datasite).

**Milestone 4.7 — Investor Network Deal Sharing**
Investors within a defined investor network (e.g., a syndicate or an LP-GP network) can share deal evaluations with each other, with startup consent, under a network data sharing agreement. Sharing is implemented as a time-limited, read-only access grant. All access events are logged.

**Milestone 4.8 — Investor Analytics API (v1)**
A dedicated investor-tier API endpoint provides programmatic access to deal pipeline data, portfolio monitoring events, and cross-portfolio comparison datasets. This API supports higher rate limits than the standard API and includes a WebSocket channel for real-time deal pipeline notifications.

### 7.4 New Modules Introduced

| Module | Description |
|--------|-------------|
| **Investor Account Manager** | Account type, permission model, and consent management for investor users. |
| **Deal Flow Pipeline Manager** | Investor deal pipeline creation, startup invitation, and submission management. |
| **Two-Stage Evaluation Orchestrator** | Lightweight screening evaluation followed by optional full evaluation. |
| **Portfolio Monitoring Service** | Tracks score changes over time for designated portfolio companies. |
| **Cross-Portfolio Comparison Engine** | Normalised comparison of multiple companies across TIDES dimensions. |
| **Investor Scoring Profile Manager** | Manages investor-defined thesis-weighted scoring configurations. |
| **Data Room Generator** | Produces structured evaluation data room packages for due diligence sharing. |
| **Investor Network Share Manager** | Manages time-limited, consent-gated evaluation sharing within investor networks. |
| **Investor Analytics API (v1)** | High-throughput, investor-tier API with WebSocket support. |

### 7.5 New AI Capabilities

- **Screening evaluation agent**: A condensed evaluation agent that assesses 5 key TIDES dimensions (Founder Profile, Market Opportunity, Product Differentiation, Business Model, Traction) in ≤ 90 seconds, using a simplified evidence retrieval strategy. Designed for high-volume top-of-funnel screening.
- **Dimension change detection agent**: Monitors re-evaluations of portfolio companies and produces a structured change report highlighting which dimension scores have moved, what new or removed evidence drove the change, and whether the change is statistically significant given the confidence intervals.
- **Investment thesis alignment scorer**: Given an investor's configured thesis (expressed as weighted scoring profile + sector + stage preferences), this agent scores each incoming deal on thesis alignment (separate from absolute quality) and produces a ranked shortlist sorted by alignment.
- **Red flag detection agent**: A specialised agent that explicitly searches submission documents for signals associated with high-risk characteristics: revenue recognition irregularities, team composition instability, regulatory exposure, customer concentration, and IP encumbrance. Red flags are reported separately from dimension scores and do not modify the TIDES Score.

### 7.6 New Analytics

- **Deal Flow Funnel Analytics**: for each investor pipeline, tracks the conversion funnel from submission to screening evaluation, full evaluation, shortlist, and deal decision.
- **Portfolio Score Trajectory**: longitudinal chart of each portfolio company's TIDES Score and per-dimension scores across all evaluation events.
- **Investment Thesis Alignment Distribution**: for a given investor's thesis profile, the distribution of incoming deal flow by thesis alignment score — showing whether the investor's deal flow is well-matched to their stated strategy.
- **Sector and Stage Benchmark Positioning**: for each evaluated company, its percentile position within its sector and stage peer group on each dimension, derived from the anonymised cross-tenant benchmark dataset.
- **Network Deal Flow Summary**: for investor networks, an aggregated view of shared deals, evaluation scores, and network member access activity.

### 7.7 New Integrations

| Integration | Purpose | Protocol |
|-------------|---------|---------|
| **Crunchbase / PitchBook** | Enriches startup profiles with external funding history and market data | REST API |
| **Dropbox / Intralinks / Datasite** | Pushes data room packages to virtual data rooms | REST API |
| **DocuSign** | Manages consent record signing for data sharing | DocuSign API |
| **Slack / Microsoft Teams** | Sends deal pipeline notifications to investor team channels | Webhook |
| **Bloomberg / Refinitiv** | Pulls sector-level market data to contextualise market opportunity assessments | REST API (licensed) |

### 7.8 Completion Criteria

Phase 4 is complete when ALL of the following conditions are satisfied:

1. A minimum of 2 VC firms or angel networks are operating as live investor tenants, with active deal pipelines and at least 10 evaluated startups each.
2. The two-stage screening evaluation meets the p95 ≤ 5-minute SLA for the screening stage, measured over a 30-day production period.
3. The startup consent model has been reviewed by a data privacy counsel and confirmed to be legally sufficient in at least two jurisdictions (India and UK as minimum).
4. The red flag detection agent's output has been reviewed by at least 2 domain expert investors and its false-positive rate is documented as below 20%.
5. Portfolio monitoring has successfully tracked at least one re-evaluation cycle for a portfolio company, producing a documented change report.
6. The investor analytics API is documented (OpenAPI spec) and has been integrated into at least one external portfolio management tool.
7. Data room packages generated by the platform have been successfully imported into at least one supported virtual data room tool.

### 7.9 Technical Debt Considerations

**Consent record architecture**: The startup consent model for investor data access is a legally significant data structure. It must be implemented as an immutable, append-only record with cryptographic signing — not as a simple boolean flag on a startup record. A lightweight implementation in Phase 4 will be legally inadequate for Phase 5's government programme consent requirements.

**Benchmark data freshness**: The cross-portfolio comparison engine depends on the benchmark dataset being regularly updated. If benchmark update frequency is not defined and enforced in Phase 4, investor comparisons will degrade in quality as the market evolves.

**API rate limit tiers**: Investor-tier API rate limits must be distinct from incubator-tier limits. A shared rate limit pool will cause incubator traffic spikes to affect investor SLAs and vice versa.

**Red flag documentation**: Red flag detection outputs must carry explicit disclaimer language and must never be used as a sole basis for rejection without human review. This requirement must be enforced at the API level, not just through UI warnings.

### 7.10 Estimated Complexity

**Relative to Phase 1: 2.2×**

The primary complexity drivers are: the consent model legal precision, the two-stage evaluation orchestration, and the cross-portfolio comparison engine's dependency on the benchmark dataset normalisation. The investor network deal sharing feature requires careful authorisation logic. The Red Flag agent is a novel AI capability requiring significant evaluation and calibration effort. Absolute engineering estimate: 24–34 person-months.

---

## 8. Phase 5 — Government Startup Evaluation Platform

### 8.1 Phase Objective

Phase 5 extends the TIDES platform to serve government agencies and national bodies administering startup development programmes — schemes such as Startup India, Innovate UK, Horizon Europe, SBIR, or equivalent national grant and accelerator programmes. Government clients differ fundamentally from commercial clients in their requirements: they operate at significantly greater scale (potentially thousands of applicants per programme cycle), they require comprehensive and legally defensible audit trails, they are subject to public procurement and freedom-of-information obligations, they must demonstrate fairness and non-discrimination in evaluation, and they may need to operate the platform within specific national data sovereignty boundaries. This phase is the most compliance-intensive of the roadmap.

### 8.2 Prerequisite State

- Phase 3 must be complete (multi-tenant infrastructure with full data isolation).
- Phase 4 API layer must be stable (the government programme API builds on the investor API architecture with additional audit extensions).
- A government programme partner must be formally contracted, with a defined programme scope (applicant volume, sector focus, evaluation timeline, reporting requirements).
- A legal opinion on the applicability of public sector procurement and AI decision-support regulations to the platform's use case must be available.
- Data residency options (cloud region selection, on-premise deployment pathway) must be formally evaluated and documented.

### 8.3 Key Milestones

**Milestone 5.1 — National Programme Configuration**
A specialised programme configuration module supports the definition of government programme structures: application rounds (open date, close date, eligibility criteria), applicant volume (supporting programmes with 500–10,000 applicants per round), evaluation SLA requirements (all applicants evaluated within N days of round close), and mandatory reporting outputs (statistical breakdown by sector, stage, region, and founding team demographics). Programme configuration is versioned and signed by an authorised government programme officer.

**Milestone 5.2 — Legally Defensible Audit Trail (Enhanced)**
The audit trail system is enhanced to meet government-grade evidential standards. Every evaluation action — document ingestion, each agent invocation with full prompt and response, human review, score override, final report generation — is stored as an immutable, cryptographically hashed record. Audit trail export must produce a package that can be submitted as evidence in an administrative appeal or judicial review. The audit trail system must be formally reviewed by a public law solicitor.

**Milestone 5.3 — Fairness and Bias Assessment Framework**
A formal fairness assessment module is implemented. After each evaluation round, the system runs a structured statistical analysis to detect potential bias in evaluation outcomes: score distribution by founder demographic (where demographic data is voluntarily provided), by applicant geography, by company founding date (proxy for applicant recency bias), and by document language. Fairness reports are produced for government programme officers and must show no statistically significant bias patterns before round results are published.

**Milestone 5.4 — Volume Scaling Architecture**
The evaluation pipeline is re-architected to support processing 1,000 applicants within a 72-hour window following programme round close. This requires: horizontal auto-scaling of evaluation agents, priority queue management (ensuring no applicant waits more than 6 hours for their evaluation to begin once in the queue), and graceful degradation under LLM API rate limits (queueing and retrying rather than failing). Load testing at 1,200 applicants must be documented.

**Milestone 5.5 — On-Premise / Sovereign Cloud Deployment**
The platform is packaged for deployment in a government-controlled cloud environment (GovCloud, Azure Government, NIC Cloud) or on-premise data centre. This requires containerisation (Kubernetes), environment variable-driven configuration (no hardcoded cloud endpoints), and documented deployment procedures for each supported environment. At least one government partner deployment in a sovereign cloud environment must be completed.

**Milestone 5.6 — Grant Eligibility Screening Module**
A specialised pre-evaluation screening module checks applicants against programme eligibility criteria before their full TIDES evaluation is run. Eligibility criteria may include: company registration age, sector classification, headcount, annual revenue ceiling, previous grant receipt, and geographic location. Applications failing eligibility screening are rejected automatically, with a structured rejection notice. Eligibility screening decisions are included in the audit trail.

**Milestone 5.7 — Public Reporting and Transparency Reports**
The platform generates structured public transparency reports for completed government programme rounds: aggregate statistics on applicant volume, evaluation outcomes, sector distribution, and demographic representation (where data is available), with no individually identifying information. Reports are formatted for publication on government programme websites.

**Milestone 5.8 — Policy Compliance Engine**
A policy compliance module allows government programme administrators to define compliance rules (drawn from programme policy documents) as structured checks that the evaluation agent must validate against each application. Examples: applicant must not have received more than X in prior public grant funding; applicant must operate in a priority sector as defined by national policy; applicant's IP must be primarily UK-owned. Compliance check results are returned as a structured compliance scorecard alongside the TIDES evaluation.

### 8.4 New Modules Introduced

| Module | Description |
|--------|-------------|
| **National Programme Configuration Manager** | Government-specific programme definition with round management and officer sign-off. |
| **Enhanced Audit Trail (Government Grade)** | Cryptographically hashed, immutable, appeal-ready audit records. |
| **Fairness and Bias Assessment Engine** | Post-round statistical bias analysis across demographic and geographic dimensions. |
| **Volume Scaling Auto-Scaler** | Horizontal scaling orchestration for high-volume programme rounds. |
| **Sovereign Deployment Package** | Kubernetes-packaged deployment for GovCloud and on-premise environments. |
| **Grant Eligibility Screener** | Pre-evaluation eligibility check against programme-specific criteria. |
| **Public Transparency Report Generator** | Produces aggregate, privacy-safe public reports for government programme transparency obligations. |
| **Policy Compliance Engine** | Validates applications against programme-specific policy rules expressed as structured checks. |

### 8.5 New AI Capabilities

- **Eligibility classification agent**: Rapidly classifies applicant eligibility from structured application data and company registration records, flagging borderline cases for human review with an explanation of which criteria are ambiguous.
- **Bias detection language model**: Analyses evaluation narrative outputs across a completed round to detect linguistic patterns that may indicate differential treatment of applicants by demographic group. Flags dimension narratives that contain language associated with known bias patterns for human reviewer attention.
- **Policy compliance extraction agent**: Reads programme policy documents (uploaded as PDFs) and automatically extracts compliance rules into structured check definitions, which a programme officer then validates before the programme round opens.
- **Volume-optimised evaluation agent**: A lighter-weight evaluation pipeline variant designed for initial screening of high-volume government programmes, producing a 5-dimension screening score in ≤ 3 minutes per applicant, with full 10-dimension evaluation reserved for shortlisted applicants.

### 8.6 New Analytics

- **Round Outcome Statistical Report**: full statistical breakdown of a programme round's evaluation outcomes: pass/fail rates, score distributions, geographic spread, sector spread, and demographic breakdown (where available).
- **Fairness Metrics Dashboard** (programme officer access): real-time fairness monitoring during evaluation, showing emerging demographic or geographic score patterns before the round is finalised.
- **Budget Impact Modelling**: given a round's evaluation outcomes and a defined grant budget, models the allocation of grants across scoring tiers and shows the expected portfolio composition under different allocation strategies.
- **Year-on-Year Programme Comparison**: for programmes running in multiple annual cycles, compares applicant quality metrics, sector distribution, and evaluation outcomes across years.

### 8.7 New Integrations

| Integration | Purpose | Protocol |
|-------------|---------|---------|
| **MCA / Companies House / National Business Registry** | Company registration verification for eligibility screening | REST API |
| **Aadhaar / UK Government Verify** | Founder identity verification for government programme eligibility | REST API + OAuth 2.0 |
| **DPIIT / HMRC / DSIT APIs** | Previous grant receipt verification, tax compliance status | REST API (government gateway) |
| **NIC Cloud / Azure Government / AWS GovCloud** | Sovereign cloud deployment target | Cloud provider APIs |
| **PDF Sign / DSC Integration** | Digital signature for officer-approved programme configurations and round reports | PKCS#7 / DSC API |
| **Government OpenData Portal** | Publication of transparency reports to national data portals | CKAN / REST API |

### 8.8 Completion Criteria

Phase 5 is complete when ALL of the following conditions are satisfied:

1. At least one government programme has been delivered end-to-end on the platform, with a minimum of 200 applicants evaluated in a single round.
2. The enhanced audit trail has been reviewed by a public law solicitor and confirmed to meet evidential standards for administrative appeal proceedings.
3. The fairness assessment report for the first completed government round shows no statistically significant bias patterns at p < 0.05 level across any monitored demographic dimension.
4. Volume scaling has been demonstrated in load testing to process 1,200 applicants within a 72-hour window without pipeline failure.
5. At least one sovereign cloud deployment has been successfully completed and is operating in production.
6. The public transparency report for the first completed round has been published (or approved for publication) by the government programme partner.
7. The policy compliance engine has been tested against at least two real programme policy documents, with programme officers confirming that the extracted compliance rules accurately reflect programme policy.

### 8.9 Technical Debt Considerations

**Audit trail immutability**: The cryptographic hashing scheme for audit records must be designed for longevity (SHA-256 minimum, with a migration path to SHA-3). If a simpler hashing scheme is used to meet the timeline, it must be documented as a known limitation requiring upgrade before the platform is used in a judicial review context.

**Fairness metric definition**: The fairness metrics computed in Phase 5 must be formally defined in a published methodology document before they are used in programme reporting. Retroactively changing fairness metric definitions after programme results have been published is politically and legally risky.

**Sovereign deployment maintenance**: On-premise and GovCloud deployments require a formal update delivery mechanism. If the update mechanism is not standardised in Phase 5, each government tenant will accumulate version drift, creating support complexity that scales with the number of government tenants in Phase 6's operational period.

**LLM provider dependency for government use**: Government tenants may require use of a specific approved LLM provider or may prohibit sending data to commercial LLM APIs. The evaluation agent architecture must support pluggable LLM backends (open-source models running in the sovereign environment) from Phase 5. This is a significant architectural constraint if Phase 1's agent design is tightly coupled to a specific provider's API format.

### 8.10 Estimated Complexity

**Relative to Phase 1: 3.0×**

This is the most compliance-intensive phase of the roadmap. The primary complexity drivers are: the legally defensible audit trail design and legal review process, the volume scaling architecture, the fairness assessment engine, and the sovereign deployment packaging. The policy compliance engine requires significant domain modelling to express arbitrary policy rules as structured checks. Absolute engineering estimate: 34–48 person-months.

---

## 9. Phase 6 — Founder Self-Evaluation Platform

### 9.1 Phase Objective

Phase 6 opens the TIDES platform directly to founders, allowing individual startup founders to evaluate their own companies against the TAES standard before applying to incubators, submitting to investors, or entering government programmes. This phase inverts the platform's primary usage pattern: rather than an institution evaluating a startup, the startup evaluates itself. The platform in this mode serves as a structured preparation tool, diagnostic instrument, and improvement tracker. Founders receive a detailed gap analysis against the TIDES dimensions, positioned against anonymised benchmark data from thousands of real evaluations. The goal of this phase is to create a self-service, high-volume consumer-like product that also functions as a pipeline entry point for incubator, investor, and government users of the platform — founders who prepare using TIDES and then apply to programmes already have evaluation records that can be shared with programme administrators.

### 9.2 Prerequisite State

- Phase 4 must be complete (investor intelligence platform operational), providing the anonymised benchmark data that founders need for positioning context.
- Phase 5 must be complete (government platform operational), providing the additional benchmark data from government programme evaluations.
- The cross-tenant anonymised benchmark dataset must contain data from at least 500 evaluated startups before founder-facing benchmarks are meaningful.
- A B2C commercial model (pricing, payment, freemium/premium tiers) must be designed and legally reviewed before Phase 6 development begins.
- A UX research programme specifically with founders (not programme managers) must have produced validated design insights, as the founder user experience is fundamentally different from the institutional user experience.

### 9.3 Key Milestones

**Milestone 6.1 — Founder-Facing Submission Interface**
A simplified, founder-optimised document submission interface is deployed. Unlike the institutional submission interface, this interface guides founders through a structured document checklist, explains what each document type contributes to the evaluation, and provides real-time completeness feedback before submission. The interface supports mobile-responsive operation. Submission is priced and paid for at the point of submission (Stripe integration).

**Milestone 6.2 — Founder-Facing Evaluation Report**
The evaluation report format is redesigned for a founder audience. Rather than a programme manager's structured scoring report, the founder report presents: a dimension-by-dimension gap analysis (what is strong, what is weak, and specifically what evidence is missing or weak), a positioning chart showing the founder's dimension scores relative to the anonymised benchmark distribution, and an ordered improvement priority list — the three dimensions where improvement would most significantly increase the composite TIDES Score.

**Milestone 6.3 — Improvement Tracking and Re-evaluation**
Founders can submit updated documents and receive a re-evaluation at a discounted rate. The platform tracks the score trajectory across all re-evaluations, showing dimension score changes over time and attributing changes to specific evidence additions or updates. A re-evaluation delta report shows exactly what changed and why.

**Milestone 6.4 — Freemium Tier (Screening Score)**
A free, anonymised version of the evaluation is offered: founders can submit their pitch deck only and receive a 3-dimension screening score (Founder Profile, Market Opportunity, Product Differentiation) with no benchmark positioning and no narrative justification. The full 10-dimension evaluation with benchmark positioning and narrative justifications is a paid tier. The freemium tier serves as a top-of-funnel conversion mechanism.

**Milestone 6.5 — Incubator and Investor Application Forwarding**
Founders can, with one click, forward their completed TIDES evaluation report (and the underlying evaluation record) to any participating incubator or investor who has opted into receiving founder-initiated submissions. Forwarding requires explicit founder consent per recipient. Participating incubators and investors are listed in a directory within the founder platform.

**Milestone 6.6 — Improvement Resource Recommendations**
After each evaluation, the platform generates a structured set of resource recommendations for each weak dimension: relevant articles, courses, frameworks, mentors, and service providers that address the identified gaps. Recommendations are curated and ranked by the TIDES team; they are not AI-generated freeform suggestions. A resource directory is maintained as a managed content asset.

**Milestone 6.7 — Cohort Preparation Packages**
For founders who are preparing to apply to a specific named incubator or government programme whose evaluation profile is on the platform, a cohort preparation package is available: the evaluation uses the specific rubric configuration of that programme, and the report shows how the founder would score under that programme's specific criteria — not just the generic TIDES standard.

**Milestone 6.8 — Founder Community Analytics (Anonymised)**
An optional, opt-in feature allows founders to contribute their anonymised evaluation data to a community benchmark. Founders who opt in receive access to a richer benchmark dashboard — including sector-specific, stage-specific, and geography-specific peer comparisons — than those who do not.

### 9.4 New Modules Introduced

| Module | Description |
|--------|-------------|
| **Founder Submission Portal** | Mobile-responsive, guided document submission interface for individual founders. |
| **Founder Evaluation Report Engine** | Produces gap-analysis-focused, benchmark-positioned evaluation reports for founder audiences. |
| **Improvement Tracker** | Tracks score trajectory across multiple re-evaluations for a single founder/startup. |
| **Freemium Evaluation Tier** | 3-dimension screening evaluation at no cost, as top-of-funnel conversion. |
| **Application Forwarding Manager** | Consent-gated evaluation forwarding to participating incubators and investors. |
| **Resource Recommendation Engine** | Curated resource directory with dimension-matched improvement recommendations. |
| **Cohort Preparation Package Generator** | Programme-specific evaluation using the named programme's rubric configuration. |
| **Community Benchmark Opt-In System** | Opt-in anonymous data contribution for enhanced peer benchmarking. |

### 9.5 New AI Capabilities

- **Improvement priority ranking agent**: Given a completed evaluation, this agent models the marginal TIDES Score increase achievable by improving each dimension from its current score to the sector benchmark median, taking into account dimension weights and score ceiling constraints, and produces an ordered improvement priority list.
- **Gap narrative generation**: A specialised report generation mode that produces founder-facing improvement narratives in plain language, explicitly avoiding evaluation jargon, explaining why a dimension scored as it did and what specific documentary additions would change the assessment.
- **Programme fit matching agent**: Given a founder's TIDES evaluation profile, this agent computes a fit score against each participating incubator and programme's rubric configuration, ranking programmes by the founder's likely performance under their specific criteria.
- **Submission completeness advisor**: During document upload, an agent analyses incoming documents in real time and provides section-level completeness feedback — identifying which standard sections (e.g., financial projections, competitive analysis, team biographies) are absent or insufficiently detailed before the full evaluation is triggered.

### 9.6 New Analytics

- **Founder Funnel Analytics**: tracks the conversion from freemium screening score to paid full evaluation, from full evaluation to re-evaluation, and from evaluation to application forwarding.
- **Improvement Velocity Metrics**: across founders who have completed multiple re-evaluations, measures average score improvement per re-evaluation cycle by dimension — indicating which dimensions founders are most and least able to improve through document iteration.
- **Programme Application Success Correlation**: for founders who have forwarded their evaluation to a programme and then received an outcome (accepted or rejected), tracks the correlation between TIDES Score and programme outcome to validate the predictive value of the evaluation. (This data is only available when programmes share outcome data back to the platform.)
- **Community Benchmark Dashboard**: for opt-in founders, sector and stage peer comparison across all ten dimensions with percentile positioning.

### 9.7 New Integrations

| Integration | Purpose | Protocol |
|-------------|---------|---------|
| **Stripe (B2C)** | Individual founder payments, subscription management, refund handling | Stripe API |
| **WhatsApp Business API** | Submission notifications and evaluation completion alerts for founders | WhatsApp Cloud API |
| **Google Sign-In / Apple Sign-In** | Simplified authentication for consumer-tier founder accounts | OAuth 2.0 |
| **Notion / Google Docs** | Founder-facing report export to collaborative document formats | API |
| **Calendly / Cal.com** | Links improvement resource recommendations to bookable mentor sessions | REST API |
| **LinkedIn Founder Profile Sync** | Supplements founder submission with publicly available LinkedIn profile data | LinkedIn API |

### 9.8 Completion Criteria

Phase 6 is complete when ALL of the following conditions are satisfied:

1. A minimum of 100 individual founders have completed paid full evaluations through the self-service portal within the first 90 days of launch.
2. The freemium to paid conversion rate is ≥ 15%, measured over the first 60 days of operation.
3. At least 10 participating incubators or investors have opted into receiving founder-initiated application forwards, and at least 20 forwarding events have occurred.
4. The improvement tracking feature has been used by at least 30 founders completing a second evaluation, and the average composite score improvement across re-evaluations is positive and statistically significant.
5. The programme fit matching agent's rankings have been validated by at least 3 participating incubator programme managers confirming that founders matched as "high fit" to their programme performed as expected in their application review.
6. The founder-facing report format has been validated in user testing with at least 15 founders, achieving a ≥ 80% "clear and useful" rating.
7. The community benchmark dataset contains at least 200 opt-in founder evaluation records before the community benchmark dashboard is published.

### 9.9 Technical Debt Considerations

**Consumer data at scale**: Phase 6 introduces a consumer-grade usage pattern with potentially orders-of-magnitude more users than previous phases. The platform's user management, authentication, and session management systems must be load-tested at consumer scale (10,000 concurrent sessions) before Phase 6 launches.

**Freemium abuse prevention**: The freemium 3-dimension evaluation must be rate-limited to prevent systematic abuse (e.g., submitting the same startup multiple times to probe the evaluation logic). Rate limiting must be identity-based, not just IP-based, as consumer users frequently share IP addresses.

**Application forwarding consent audit**: The forwarding consent records are legally significant. They must meet the same evidential standard as Phase 4's investor consent records. A simplified consent implementation for consumer UX that does not meet this standard will create legal exposure.

**Community benchmark anonymisation**: The community benchmark data contributed by opt-in founders adds a new anonymisation surface to manage alongside the institutional anonymised benchmark from Phase 3. The two datasets must be kept segregated and anonymised through separate pipelines to prevent cross-correlation attacks.

### 9.10 Estimated Complexity

**Relative to Phase 1: 1.7×**

Phase 6 is lower in engineering complexity than Phases 3–5 because it primarily adapts existing evaluation infrastructure for a new user interface and pricing model, rather than introducing new architectural components. The primary complexity drivers are: consumer-scale infrastructure (authentication, session management, payment), the freemium tier's real-time completeness advisor, and the programme fit matching agent. The UX design effort for the founder audience is significantly higher than for previous institutional interfaces and should not be underestimated. Absolute engineering estimate: 18–26 person-months.

---

## 10. Future AI Capabilities (Post–Phase 6)

The following capabilities are not assigned to any numbered phase. They represent the next generation of AI functionality to be explored once the platform has accumulated sufficient evaluation data from six phases of deployment. These are not speculative features — each has a defined data dependency that must be satisfied before development is feasible.

### 10.1 Predictive Scoring Models

**Description**: Supervised machine learning models trained on the platform's accumulated evaluation data, paired with programme outcome data (programme acceptance decisions, subsequent funding rounds, revenue milestones, and company failures), to produce a predictive TIDES Score — an estimate of a company's likely evaluation trajectory and programme outcome probability at the time of submission.

**Data Dependency**: A minimum of 2,000 evaluated startups with documented post-evaluation outcomes (at minimum: accepted/rejected by programme, and 12-month funding outcome) is required before predictive model training is meaningful.

**Technical Approach**: Gradient-boosted regression ensemble trained on TIDES dimension scores, evidence quality vectors, and cohort configuration metadata. Output: a probability distribution over outcome states (programme acceptance, seed funding within 12 months, Series A within 24 months) with confidence intervals. The predictive score is displayed separately from the TIDES Score and labelled explicitly as a probabilistic estimate.

**Ethical Consideration**: Predictive models trained on historical evaluation and outcome data inherit any biases present in historical programme selection decisions. A formal bias audit of the training data must be conducted before any predictive model is deployed to users.

### 10.2 Exit Probability Models

**Description**: A specialised predictive model estimating the probability that a startup will achieve a defined exit event (acquisition, IPO, significant revenue milestone) within a defined time horizon, conditioned on its TIDES Score profile at a given stage.

**Data Dependency**: Requires evaluation data from startups with ≥ 5-year longitudinal histories. Given Phase 1's launch date, this data will not be available until approximately Year 6 of platform operation.

**Technical Approach**: Survival analysis model (e.g., Cox Proportional Hazards or discrete-time hazard model) with TIDES dimension scores and evidence quality features as covariates. Output: time-to-exit probability curves at 1, 3, and 5 year horizons. Designed specifically for investor portfolio monitoring use cases.

### 10.3 Agent Specialisation by Sector

**Description**: Rather than sector-adaptive prompt chain modifications (Phase 2), true sector-specialised evaluation agents — fine-tuned on sector-specific evaluation corpora and incorporating sector-domain knowledge — for each major startup sector: Deep Tech, FinTech, HealthTech, AgriTech, EdTech, CleanTech, and Consumer.

**Data Dependency**: Requires at least 500 evaluated startups per sector with human-validated evaluation outcomes before fine-tuning data is sufficient.

**Technical Approach**: Domain-adaptive fine-tuning of the base LLM on sector-specific evaluation reasoning examples. Each sector agent maintains a separate model checkpoint with a defined version history. Sector agent performance is benchmarked against generic agent performance on sector-specific test sets before deployment.

### 10.4 Multimodal Evaluation Agents

**Description**: Evaluation agents capable of processing not just text documents but also structured data (financial model spreadsheets), presentation slides as visual layouts, product demonstration videos, and prototype screenshots. This expands the evidence surface available to evaluation agents beyond text.

**Data Dependency**: Requires multimodal foundation model with sufficient financial document and presentation understanding capability — currently (2026) at the boundary of commercial LLM capability.

**Technical Approach**: Multimodal model pipeline where visual inputs (slide images, screenshots, video keyframes) are processed by a vision encoder and the resulting embeddings are concatenated with text embeddings for retrieval. Financial spreadsheet inputs are parsed into structured JSON representations before agent processing.

### 10.5 Counterfactual Evidence Analysis

**Description**: An agent capability that, given an evaluation, generates counterfactual analyses: "If the startup had provided evidence of X, their dimension score would have increased from Y to Z." These counterfactuals are presented as specific, actionable evidence gaps in the evaluation report.

**Data Dependency**: Requires a sufficiently large dataset of evaluations with varying evidence quality to train or calibrate the counterfactual scoring model.

**Technical Approach**: Conditional inference using the dimension rubric: the agent explicitly traces which rubric criteria are unsatisfied, models the score under the assumption that specific evidence were present, and computes the score delta. This is a prompt-engineering-first approach rather than a trained model approach, making it feasible before the full predictive model data dependencies are met.

---

## 11. Future Analytics Capabilities

### 11.1 Sector Benchmarks

The platform will develop and publish sector-specific benchmark score profiles once sufficient evaluation data is accumulated (minimum 200 evaluations per sector). Sector benchmarks will provide:

- **Dimension score norms**: Mean and standard deviation for each TAES dimension within a sector, segmented by funding stage (pre-revenue, early-revenue, growth).
- **Sector archetype profiles**: Cluster analysis of evaluation profiles within a sector, identifying characteristic "startup archetypes" (e.g., in Deep Tech: IP-strong but market-weak; in FinTech: market-strong but regulatory-weak) with their frequency distribution.
- **Benchmark update cadence**: Sector benchmarks are updated quarterly using rolling 18-month evaluation windows to reflect market evolution.
- **Publication format**: Benchmarks are published as structured JSON datasets available via API and as PDF sector reports available for download by institutional platform users.

### 11.2 Cohort Analytics

For institutional users (incubators and government programmes) running multiple cohorts over time:

- **Cohort Quality Index**: a composite metric tracking the average TIDES Score of each cohort over time, controlling for sector and stage composition changes, to measure whether programme selection quality is improving.
- **Dimensional Improvement Tracking**: for incubators that evaluate the same startup at programme entry and programme exit (post-incubation), the platform will track which dimensions improved most and least across the programme, providing evidence of programme value-add.
- **Cohort Peer Comparison**: allows an incubator to compare a current cohort's profile against any of their previous cohorts on all ten dimensions, with statistical significance testing.

### 11.3 Longitudinal Tracking

The platform's most significant long-term analytical capability is longitudinal tracking: following individual startups from their first evaluation through multiple re-evaluations, programme participation, funding events, and eventual outcome. Longitudinal analytics require:

- A persistent `startup_id` that survives across programme contexts (e.g., a startup evaluated by Incubator A and later independently by an investor must be recognised as the same entity, with their consent).
- An outcome event registry: a structured schema for recording startup outcome events (funding rounds, revenue milestones, acquisitions, closures) that are linked to a startup's evaluation history.
- A longitudinal analytics API that returns a startup's full evaluation and outcome history, subject to consent and access controls.
- An aggregate longitudinal report that, across the platform's population of evaluated startups, shows the statistical relationship between initial TIDES dimension profiles and longitudinal outcome events.

---

## 12. Future Benchmarking Infrastructure

### 12.1 Purpose and Methodology

The TIDES platform's long-term value is not just the evaluation of individual startups, but the creation and maintenance of an authoritative, evidence-based benchmark dataset for startup quality across dimensions, sectors, and geographies. This benchmark dataset will become a reference standard — cited in academic research, used in policy development, and referenced by investors making market assessments.

### 12.2 Benchmark Construction

Benchmarks are constructed using the following methodology:

1. **Data collection**: Every completed evaluation on the platform contributes to the benchmark dataset, subject to data sharing consent (institutional tenants must explicitly opt their evaluation data into the benchmark pool as part of their DPA).
2. **Anonymisation**: Before inclusion in the benchmark, each evaluation record is anonymised using a defined differential privacy protocol: dimension scores are perturbed with calibrated Laplacian noise, exact document evidence is removed, and any potentially identifying metadata (cohort name, programme date) is replaced with categorical buckets.
3. **Quality filtering**: Evaluations with confidence scores below 0.6 across more than 3 dimensions, or with override rates above 40%, are excluded from the benchmark dataset as low-quality signals.
4. **Stratification**: The benchmark dataset is stratified by sector (using a defined sector taxonomy), stage (pre-revenue, ≤£500K ARR, ≤£2M ARR, growth), and geography (regional groupings).
5. **Update cadence**: Full benchmark recomputation is performed quarterly. A continuous update mode (rolling 30-day window) is maintained for live percentile positioning calculations.

### 12.3 Benchmark Governance

The benchmark dataset is governed by a Benchmark Advisory Committee comprising: TIDES platform technical leads, at least 2 independent academic researchers, at least 1 investor representative, and at least 1 government programme representative. The Committee reviews and approves:

- Changes to the benchmark construction methodology.
- Changes to the sector or stage taxonomy.
- Publication of new benchmark reports.
- Requests to use benchmark data for external research purposes.

### 12.4 Benchmark Publication

Benchmarks are published in three forms:

| Publication Format | Access Level | Update Frequency |
|-------------------|-------------|-----------------|
| **Sector Benchmark JSON (API)** | Institutional tenants (Phase 3+) | Quarterly |
| **Annual Startup Quality Report (PDF)** | Public | Annual |
| **Academic Research Dataset (de-identified)** | Academic partners (by application) | Annual |
| **Real-Time Percentile API** | Investor and Government tenants (Phase 4/5) | Continuous (30-day rolling) |

---

## 13. Future Simulation Engine

### 13.1 Scenario Modelling for Startups

The TIDES Simulation Engine is a future capability that allows authorised users to model "what if" scenarios for individual startups: hypothetical changes to a startup's profile are simulated, and the resulting change in TIDES dimension scores, composite score, and benchmark positioning is projected. This capability transforms the platform from a retrospective evaluation tool into a forward-looking strategic planning instrument.

### 13.2 Scenario Types

| Scenario Type | Description | Primary User |
|--------------|-------------|-------------|
| **Funding Round Simulation** | Models the effect of raising a specific funding round (amount, lead investor type) on Team, Traction, and Financial Health dimensions | Founder, Investor |
| **Team Composition Change** | Models the effect of adding a specific role (e.g., CTO, CFO, domain expert) to the founding team on the Founder Profile dimension | Founder |
| **Market Pivot Simulation** | Models the effect of pivoting from the current primary market to an adjacent market on Market Opportunity and Business Model dimensions | Founder, Incubator |
| **Revenue Milestone Achievement** | Projects how reaching a specific revenue milestone (e.g., £500K ARR, 1,000 customers) would change Traction and Financial Health scores | Founder, Investor |
| **Regulatory Clearance** | For HealthTech and FinTech, models the score impact of achieving specific regulatory approvals (CE mark, FCA authorisation, CDSCO approval) | Founder |
| **IP Filing** | Models the score impact of filing or receiving a patent, trademark, or copyright registration | Founder |

### 13.3 Simulation Methodology

Simulations are not the output of a generative AI model freely extrapolating. They are constrained, rubric-based projections:

1. The scenario is expressed as a structured set of parameter changes (e.g., `{ "team_additions": [{ "role": "CFO", "prior_CFO_experience_years": 8 }] }`).
2. The relevant dimension agent's rubric criteria that would be affected by these parameter changes are identified.
3. The agent re-scores only the affected rubric criteria under the simulated state, holding all other criteria constant.
4. The score delta is computed and presented with confidence bounds.
5. Simulation outputs are clearly labelled as projections and are never stored as evaluation records.

### 13.4 Simulation Governance

Simulation outputs must not be used as a substitute for actual evaluations. The platform's UI and API must enforce:

- Simulation outputs cannot be shared as an evaluation report.
- Simulation outputs cannot be forwarded to incubators, investors, or government programmes.
- Simulation outputs are watermarked with "SIMULATED — NOT AN EVALUATION" in all export formats.
- Simulation scenarios are logged in the audit trail (for institutional users) but are not part of the primary evaluation record.

---

## 14. The Principle of Incremental Evolution

### 14.1 Definition

The Principle of Incremental Evolution governs how the TIDES platform grows across phases. It states: **each phase must extend the platform without requiring destructive changes to any component that was production-stable in a previous phase.** This principle is not aspirational — it is a hard engineering constraint enforced by the following rules.

### 14.2 Implementation Rules

**Rule 1 — Additive Data Model Changes Only**
Every new phase may add columns, tables, or documents to the data model. No new phase may remove or rename an existing field that is referenced by a production API, UI component, or analytics query without completing a formal deprecation cycle (a minimum of one full phase duration with the old field maintained in parallel).

**Rule 2 — API Backward Compatibility**
Every API version that has been consumed by a production tenant must remain functional for a minimum of 24 months after a new API version is introduced. API versioning (e.g., `/v1/`, `/v2/`) is the mechanism for introducing breaking changes. There must be no silent breaking changes within a version.

**Rule 3 — Prompt Chain Versioning**
Every change to an agent's prompt chain creates a new prompt version. The evaluation record for every startup must record the prompt version used. Historical evaluations must be reproducible using the prompt version stored in their record, even after multiple subsequent prompt version updates.

**Rule 4 — Evaluation Standard Versioning**
The TAES evaluation standard version (e.g., TAES v1.0, TAES v1.1) is a first-class entity in the platform's data model. The platform must support running evaluations under any supported TAES version simultaneously. Results from different TAES versions must never be directly compared in analytics without explicit version-control adjustments.

**Rule 5 — Zero-Downtime Phase Transitions**
Phase transitions must not require maintenance windows that affect production tenants. New capabilities are deployed using feature flags, progressive rollout, and blue-green deployment patterns. The phase transition is complete when the new capabilities are validated and the flags are fully enabled — not before.

### 14.3 Technical Governance Mechanism

At the start of each phase, the engineering team produces a **Phase Transition Impact Assessment** document that:

1. Lists every component that will be modified in the new phase.
2. For each modified component, assesses the impact on all previous-phase consumers of that component.
3. Identifies all required backward compatibility measures.
4. Defines the rollback procedure if the phase transition encounters critical failures.

The Phase Transition Impact Assessment must be reviewed and approved by the platform technical lead before phase development begins.

### 14.4 Knowledge Continuity

As the platform evolves across phases, the engineering team and product documentation must evolve in parallel:

- Architecture Decision Records (ADRs) must be maintained for every significant architectural decision, recording the rationale, the alternatives considered, and the future-phase implications.
- The TAES specification documents are updated to reflect new dimensions, overlays, and evaluation rules introduced at each phase, with each version formally published and archived.
- Onboarding documentation for new engineering team members must cover the architectural history of the platform — not just the current state — so that phase transition constraints are understood by all team members.

---

## 15. Appendix A — Phase Completion Checklist Summary

The following table provides a condensed summary of each phase's completion criteria for programme management use. Full criteria are defined in each phase's dedicated section.

| Phase | Critical Gates |
|-------|---------------|
| **Phase 1** | 8+ startups evaluated; ICC ≥ 0.65 inter-rater; ≥ 75% reviewer satisfaction; ≤ 8min p95 latency; 100% audit coverage; pilot post-mortem complete |
| **Phase 2** | 3 simultaneous cohorts (15+ startups each); zero-engineer cohort configuration UAT; 5+ sector overlays validated; v1 API integrated externally; throughput SLA met in 48hr stress test |
| **Phase 3** | 3+ paid tenants live; penetration test passed; zero-engineer onboarding UAT; automated billing cycle completed; anonymised benchmark privacy-reviewed; 99.5% uptime over 90 days |
| **Phase 4** | 2+ VC/angel tenants with 10+ evaluated startups each; screening p95 ≤ 5min; consent model legally reviewed; red flag FP rate < 20%; portfolio monitoring re-evaluation cycle completed |
| **Phase 5** | 200+ applicants in single government round; audit trail legally reviewed; fairness analysis p < 0.05 clean; 1,200-applicant load test passed; sovereign deployment completed; transparency report published |
| **Phase 6** | 100+ paid founder evaluations in 90 days; freemium conversion ≥ 15%; 10+ participating programmes in forwarding directory; improvement tracking validated over 30+ re-evaluations; community benchmark at 200+ records |

---

*End of Document — TAES v1.0 / 10_Product_Roadmap.md*

*This document is classified as Internal Technical Standard. Distribution is restricted to authorised personnel. Any reproduction, redistribution, or modification of this document requires approval from the TIDES Platform Engineering lead.*
