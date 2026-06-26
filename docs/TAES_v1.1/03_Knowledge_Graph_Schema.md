> **Document:** TAES v1.1 / Knowledge Graph Schema
> **Classification:** Internal Technical Standard
> **Version:** 1.1.0
> **Maintainer:** TIDES Platform Architecture Team
> **Review Cycle:** Quarterly
> **Status:** Active

---

# TAES v1.1 — Startup Knowledge Graph Schema

## Document Purpose

This document defines the complete schema of the Startup Knowledge Graph (SKG) used within the TIDES AI Evaluation Standard (TAES) version 1.1. It establishes every entity, every attribute, every relationship, every validation rule, and every traversal pattern that governs how startup data is stored, queried, and reasoned over by the multi-agent evaluation pipeline.

This is a schema and design specification document. It is implementation-independent and contains no database-specific syntax, no query language code, no API references, and no prompt templates. It is authoritative over all downstream implementation decisions concerning graph structure.

---

## Table of Contents

1. [Introduction](#1-introduction)
   - 1.1 What Is a Knowledge Graph in the Startup Evaluation Context
   - 1.2 Why a Graph Model Is Superior to a Document Model
   - 1.3 The Knowledge Graph as Shared Memory of the Multi-Agent Pipeline
   - 1.4 Three Core Functions: Storage, Traversal, and Confidence Tracking
   - 1.5 How the Knowledge Graph Is Populated
   - 1.6 How AI Agents Query the Graph
2. [Entity Definitions](#2-entity-definitions)
   - 2.1 Startup
   - 2.2 Founder
   - 2.3 Team Member
   - 2.4 Technology
   - 2.5 TRL Record
   - 2.6 Market
   - 2.7 Customer Segment
   - 2.8 Revenue Record
   - 2.9 Investor
   - 2.10 Grant
   - 2.11 Patent
   - 2.12 Product
   - 2.13 Competitor
   - 2.14 Financial Statement
   - 2.15 Document
   - 2.16 Pitch Deck
   - 2.17 Research Paper
   - 2.18 Mentor
   - 2.19 Evaluation
   - 2.20 Recommendation
   - 2.21 Milestone
   - 2.22 Risk Record
   - 2.23 Roadmap
   - 2.24 ESG Record
   - 2.25 IP Portfolio
3. [Graph Traversal Patterns](#3-graph-traversal-patterns)
4. [Confidence Propagation](#4-confidence-propagation)
5. [Graph Integrity Rules](#5-graph-integrity-rules)
6. [Temporal Versioning](#6-temporal-versioning)
7. [How AI Agents Query the Graph](#7-how-ai-agents-query-the-graph)
8. [Graph Population Pipeline](#8-graph-population-pipeline)

---

## 1. Introduction

### 1.1 What Is a Knowledge Graph in the Startup Evaluation Context

A knowledge graph is a structured, networked representation of information in which real-world entities — such as founders, technologies, markets, and patents — are modelled as nodes, and the relationships between them are modelled as directed, labelled edges. Each node carries a set of typed attributes that describe the entity in detail. Each edge carries a label that names the relationship and, optionally, additional metadata such as timestamps, confidence scores, and source provenance.

In the TIDES evaluation context, the Startup Knowledge Graph (SKG) is the authoritative, machine-readable model of a startup at any given point in its evaluation lifecycle. Rather than storing information about a startup as a collection of documents — pitch decks, financial PDFs, founder CVs, market research reports — the SKG translates all of this information into a unified graph of entities and relationships that can be traversed, queried, and reasoned over by AI agents without any need to re-read or re-parse raw source materials.

Every startup that enters the TIDES pipeline receives its own SKG instance. This instance is initialised upon intake, incrementally populated as documents and data are submitted, updated as agents produce outputs, and versioned to preserve the historical record of how the startup's profile has evolved. The SKG is the single source of truth for all downstream evaluation activity. No agent in the pipeline makes a decision based on unstructured documents if the corresponding structured data is already present in the graph.

The SKG is not a search index, a vector store, or a document repository. It is a structured intelligence model — a formal, typed, relationship-rich representation of everything that is known about a startup and the degree of confidence with which it is known.

---

### 1.2 Why a Graph Model Is Superior to a Document Model for AI Evaluation

Startup due diligence, historically conducted by human analysts, has relied on a document-centric information model: the evaluator reads a pitch deck, cross-references a financial statement, consults a market research report, and mentally assembles a picture of the startup's strengths and weaknesses. This process is inherently serial, non-reproducible, and difficult to audit. When applied to AI agents, a document-centric model reproduces all of these deficiencies at scale, adding additional failure modes such as hallucination during re-reading, inconsistency across multiple agent calls over the same document, and loss of relational context.

The graph model addresses each of these deficiencies systematically.

**Elimination of Redundant Re-Reading.** Once a document is parsed and its content is extracted into graph entities and attributes, no subsequent agent needs to read that document again. Agents query the graph directly. This reduces latency, eliminates the risk of divergent interpretations of the same source text, and decouples the extraction process from the reasoning process.

**Relationship Inference Without Full Document Scans.** In a document model, inferring that a founder's prior company is a direct competitor of the startup being evaluated requires reading multiple documents and matching entity names. In the graph model, this inference is accomplished by a two-hop traversal: from the Startup node to the Founder node via the FOUNDED_BY edge, and from the Founder node to their prior venture via the PREVIOUSLY_FOUNDED edge, followed by a check of whether that venture appears as a Competitor node in the same graph. The traversal takes microseconds and is deterministic.

**Version Tracking Without Document Duplication.** When a startup updates its financial projections or revises its product roadmap, the document model requires the evaluator to identify which version of which document is current. The graph model handles versioning at the entity level: each node carries a version number and a timestamp, and the full historical sequence of values for any attribute is preserved as a linked list of version records. Evaluators can query the state of the graph at any point in time.

**Confidence-Aware Reasoning.** Documents carry no inherent signal about the reliability of the claims they contain. The graph model assigns a confidence score to every attribute, derived from the quality of the source, the number of corroborating sources, and the coherence of the value with related attributes. Agents can reason over high-confidence subgraphs selectively, flag low-confidence attributes for additional verification, and produce evaluation outputs that are explicitly calibrated to the quality of the underlying data.

**Multi-Dimensional Cross-Entity Analysis.** A startup is not a flat set of facts. It is an ecosystem of interrelated entities — founders with histories, technologies with maturity levels, markets with competitive dynamics, revenue streams with validation status. The graph model preserves and makes explicit all of these dimensions and their mutual dependencies, enabling AI agents to perform multi-dimensional analysis that would be impossible over a flat document set.

---

### 1.3 The Knowledge Graph as Shared Memory of the Multi-Agent Pipeline

The TIDES evaluation pipeline is executed by a system of specialised AI agents, each responsible for a specific evaluation dimension: founder assessment, technology readiness, market sizing, financial modelling, IP analysis, risk scoring, and so forth. These agents operate concurrently on different subgraphs of the SKG and sequentially on evaluation stages.

The SKG serves as the shared, persistent memory that enables coordination among these agents without requiring direct agent-to-agent communication. An agent that completes its evaluation of the technology subgraph writes its findings — confidence scores, flagged anomalies, derived attributes — back into the graph. A subsequent agent operating on the financial subgraph can then read the technology confidence scores as contextual inputs without needing to re-invoke the technology agent or access any source document.

This shared memory architecture has three critical properties.

**Persistence.** The graph persists between agent invocations. No evaluation state is lost when an agent completes its task. An agent interrupted mid-evaluation can resume from the exact state recorded in the graph without loss of prior work.

**Provenance.** Every write to the graph is tagged with the identity of the writing agent, the timestamp of the write, and the source or reasoning that produced the value. This full provenance chain makes the graph auditable: any attribute value can be traced back to its originating source.

**Conflict Resolution.** When two agents write conflicting values to the same attribute — for example, two agents independently estimate the total addressable market and arrive at different figures — the graph applies a defined conflict resolution protocol based on source authority rankings and confidence weights, recording both values and the resolution decision as part of the versioning history.

---

### 1.4 Three Core Functions: Storage, Traversal, and Confidence Tracking

The SKG performs three core functions that distinguish it from both a relational database and a document store.

**Function 1: Structured Storage.** The graph stores all structured information about a startup as typed, validated, versioned entity attributes. Every attribute has a defined data type, a required/optional classification, a source provenance record, and a confidence score. Storage is write-once for any given version: once an attribute value is committed to the graph at a specific version, it is immutable. Updates create new versions; they do not overwrite existing values.

**Function 2: Relationship Traversal.** The graph enables agents to navigate from any entity to any related entity by following named, directed edges. Traversal is the primary mechanism by which agents discover latent relationships that are not explicitly stated in any single document. For example, the relationship between a startup's patent portfolio and its competitive moat is not stated in either the patent filing or the competitive analysis; it is revealed by traversing the graph from the IP Portfolio node through the Patent nodes to the Competitor nodes and computing the degree of overlap between claimed technology domains and the technologies used by competitors.

**Function 3: Confidence Tracking.** Every piece of information in the graph carries a confidence score between 0.0 and 1.0 at the attribute level. These scores are derived from source quality, corroboration count, logical consistency, and temporal freshness. They propagate upward from attributes to entities and from entities to aggregate evaluation scores. Confidence tracking enables the pipeline to produce not just a score for a startup but a calibrated statement of how reliable that score is.

---

### 1.5 How the Knowledge Graph Is Populated

The SKG is populated through three distinct channels, each with its own extraction, validation, and ingestion protocol.

**Channel 1: Document Parsing.** Unstructured and semi-structured documents — pitch decks, CVs, patent filings, financial statements, market reports, research papers — are processed by document extraction agents that identify and extract entity attributes from the text. Extracted values are mapped to graph schema fields, assigned a preliminary confidence score based on extraction certainty, and staged for validation before being committed to the graph. Document-sourced attributes carry a provenance tag that includes the document identifier, the page or section reference, and the extraction agent identifier.

**Channel 2: Structured Form Data.** During the intake process, founders and team members complete structured intake forms that capture standardised fields: company registration number, founding date, sector classification, funding stage, team size, and similar. Structured form data is ingested directly into graph attributes without an extraction step, as the data is already in typed, labelled form. Structured form data receives a higher baseline confidence score than document-extracted data, subject to cross-validation against other sources.

**Channel 3: AI Agent Outputs.** Agents that perform evaluation, synthesis, or inference write derived attributes back into the graph. These include confidence scores assigned by evaluation agents, risk records created by risk assessment agents, recommendations produced by scoring agents, and milestone assessments produced by progress tracking agents. Agent-produced values are tagged with the producing agent's identifier and version, the inputs used to produce the value, and the reasoning trace (in abstracted form) that led to the output.

All three channels feed into a staging area where values are subject to schema validation, type checking, range checking, and cross-entity consistency checks before being committed to the live graph.

---

### 1.6 How AI Agents Query the Graph

Agents in the TIDES pipeline do not access raw documents at evaluation time. They access the SKG through a defined set of query types that are described in full in Section 7. In summary, agents issue structured requests to the graph layer that specify:

- The starting entity or entities of interest.
- The attributes to retrieve from those entities.
- The relationships to traverse and to what depth.
- Any filters to apply on attribute values, confidence thresholds, or temporal constraints.
- The output format expected: single-value lookup, list of entities, subgraph, or similarity ranking.

The graph layer resolves these requests against the live graph state and returns typed, structured results. Agents never receive raw document text through graph queries; they receive structured data that has already been extracted, validated, and confidence-scored.

This separation between data extraction and data reasoning is fundamental to the reliability and auditability of the TIDES evaluation pipeline.

---

## 2. Entity Definitions

The following sections define every entity in the Startup Knowledge Graph. Entities are ordered from the root outward, beginning with the Startup entity and progressing through all associated entities.

Each entity definition includes: Entity Definition, Attributes, Relationships, Evidence Sources, Validation Methods, Update Rules, Confidence Tracking, and Versioning.

---

### 2.1 Startup

#### Entity Definition

The Startup entity is the root node of every SKG instance. It represents the company, venture, or project under evaluation. All other entities in the graph are directly or indirectly connected to the Startup node. The Startup entity carries the highest-level descriptive and classificatory attributes of the organisation and serves as the anchor point for all evaluation activity. Every graph traversal either begins at or terminates at the Startup node. Only one Startup node exists per SKG instance.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `startup_id` | UUID | Required | Globally unique identifier assigned at intake. Immutable. |
| `legal_name` | String | Required | Full registered legal name of the entity. |
| `trade_name` | String | Optional | Trading name or brand name, if different from legal name. |
| `registration_number` | String | Required | Company registration number from the registering authority. |
| `registration_jurisdiction` | String | Required | Country and state/province of registration. |
| `founding_date` | ISO 8601 Date | Required | Date the entity was legally incorporated or founded. |
| `sector_primary` | Enum (Sector Taxonomy) | Required | Primary sector classification per TIDES Sector Taxonomy v1.1. |
| `sector_secondary` | List<Enum> | Optional | One or more secondary sector classifications. |
| `stage` | Enum (Stage Taxonomy) | Required | Current funding/development stage: Ideation, Pre-Seed, Seed, Series A, Series B, Growth, Mature. |
| `headquarters_location` | Structured Address | Required | Registered office or primary operating location, structured as city, state, country. |
| `operational_status` | Enum | Required | One of: Active, Dormant, Dissolved, Acquired, Merged. |
| `website_url` | URL | Optional | Primary public-facing website. |
| `description_short` | String (≤ 280 chars) | Required | One-sentence description of the startup's value proposition. |
| `description_long` | String (≤ 2000 chars) | Optional | Extended description covering problem, solution, and target customer. |
| `employee_count_current` | Integer | Optional | Total headcount at the time of last update. |
| `intake_date` | ISO 8601 DateTime | Required | Timestamp when the startup was first registered in the TIDES system. |
| `evaluation_status` | Enum | Required | One of: Pending, In-Progress, Complete, Archived. |
| `graph_version` | Semantic Version | Required | Current version of this SKG instance (e.g., 1.4.2). |
| `composite_confidence_score` | Float [0.0–1.0] | Required | Aggregate confidence in the completeness and accuracy of the full graph. |
| `last_updated` | ISO 8601 DateTime | Required | Timestamp of the most recent write to any attribute of this entity. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `FOUNDED_BY` | Founder | One-to-Many | Identifies all individuals who founded the startup. |
| `HAS_TEAM_MEMBER` | Team Member | One-to-Many | All current and past employees and advisors. |
| `USES_TECHNOLOGY` | Technology | One-to-Many | All core technologies the startup's product or operations rely on. |
| `OPERATES_IN` | Market | One-to-Many | All markets the startup targets or participates in. |
| `HAS_PRODUCT` | Product | One-to-Many | All products or services offered. |
| `HAS_INVESTOR` | Investor | One-to-Many | All current and past investors. |
| `HAS_GRANT` | Grant | One-to-Many | All grants received or applied for. |
| `HAS_IP_PORTFOLIO` | IP Portfolio | One-to-One | The startup's consolidated intellectual property portfolio. |
| `HAS_FINANCIAL_STATEMENT` | Financial Statement | One-to-Many | All financial statements associated with the startup. |
| `HAS_EVALUATION` | Evaluation | One-to-Many | All evaluation records produced by the TIDES pipeline. |
| `HAS_ROADMAP` | Roadmap | One-to-One | The startup's current strategic and product roadmap. |
| `HAS_ESG_RECORD` | ESG Record | One-to-Many | Environmental, social, and governance compliance records. |
| `HAS_MILESTONE` | Milestone | One-to-Many | All tracked milestones, achieved or pending. |
| `HAS_RISK_RECORD` | Risk Record | One-to-Many | All identified risk records. |
| `HAS_DOCUMENT` | Document | One-to-Many | All documents associated with the startup in the document registry. |
| `HAS_COMPETITOR` | Competitor | One-to-Many | All identified competitors. |
| `MENTORED_BY` | Mentor | One-to-Many | Mentors formally associated with the startup. |

#### Evidence Sources

- Intake registration form (structured, primary authority for `legal_name`, `registration_number`, `founding_date`, `stage`)
- Company registry API cross-check for `registration_number` and `operational_status`
- Pitch deck (extracted `description_short`, `description_long`, `sector_primary`)
- Agent-computed fields: `composite_confidence_score`, `graph_version`, `evaluation_status`

#### Validation Methods

- `registration_number` is cross-validated against the applicable national company registry. Discrepancies generate a validation flag.
- `founding_date` must precede `intake_date`. Any record where `founding_date` is after `intake_date` is rejected as invalid.
- `stage` must be consistent with the financial history in linked Financial Statement entities. A startup claiming Series A with no linked investor of that stage generates a consistency warning.
- `description_short` is subject to automated length check and prohibited-content check (no profanity, no PII).
- `sector_primary` must resolve to a valid leaf node in the TIDES Sector Taxonomy v1.1.

#### Update Rules

- `startup_id`, `registration_number`, `founding_date`, and `intake_date` are immutable once written. No update rule may overwrite these.
- `stage`, `operational_status`, `employee_count_current`, and `evaluation_status` may be updated by authorised agents upon trigger events (new funding round closed, operational status change reported).
- Every update to any mutable attribute increments `graph_version` by a patch increment (e.g., 1.4.1 → 1.4.2) and records the timestamp in `last_updated`.
- Bulk updates resulting from a new evaluation run increment the minor version (e.g., 1.4.x → 1.5.0).

#### Confidence Tracking

Entity-level confidence is maintained as `composite_confidence_score`, computed as the weighted average of attribute-level confidence scores across all populated required attributes. The weight of each attribute in the composite is defined in the TIDES Confidence Weight Table (Appendix A of the TIDES Evaluation Model specification). Attributes that remain unpopulated reduce the composite score by their maximum possible contribution. Attributes corroborated by two or more independent sources receive a corroboration bonus of +0.05 (capped at 1.0).

#### Versioning

The Startup entity uses semantic versioning. The full version history is maintained as a linked list of version snapshots. Each snapshot records the complete state of all entity attributes at the time of that version. Snapshots are immutable. Agents querying historical state request the graph at a specified version or timestamp, and the system returns the snapshot that was current at that point.

---

### 2.2 Founder

#### Entity Definition

The Founder entity represents an individual who was directly involved in the founding of the startup as a co-founder, primary founder, or technical founder. Founders are distinguished from general team members by their equity stake, founding role designation, and inclusion in the company's founding documents. The Founder entity is among the highest-weighted entities in the evaluation graph because founder quality, experience, and credibility are primary determinants of early-stage startup success probability.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `founder_id` | UUID | Required | Globally unique identifier. Immutable. |
| `full_name` | String | Required | Legal full name. |
| `role_title` | String | Required | Role title at the startup (e.g., CEO, CTO, COO). |
| `equity_stake_percent` | Float | Optional | Percentage equity stake, as of last cap table update. |
| `prior_ventures` | List<String> | Optional | Names of prior startups founded or co-founded. |
| `prior_exits` | Integer | Optional | Number of prior ventures that resulted in acquisition or IPO. |
| `domain_expertise_years` | Integer | Optional | Years of experience in the startup's primary domain. |
| `highest_qualification` | Structured Object | Optional | Degree type, institution, field, and year of completion. |
| `linkedin_profile_url` | URL | Optional | Public LinkedIn profile for cross-validation. |
| `patents_held` | Integer | Optional | Count of patents held personally (distinct from the startup's IP portfolio). |
| `publications_count` | Integer | Optional | Count of peer-reviewed publications as author or co-author. |
| `advisory_roles` | List<String> | Optional | Organisations in which the founder holds or held advisory positions. |
| `criminal_record_declared` | Boolean | Required | Self-declared flag. True if the founder has declared any criminal record. |
| `conflict_of_interest_declared` | Boolean | Required | Self-declared flag for any conflict of interest with evaluation bodies. |
| `location_country` | String | Required | Country of primary residence. |
| `full_time_committed` | Boolean | Required | Whether the founder is full-time at the startup at the time of evaluation. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `FOUNDED` | Startup | Many-to-One | The startup this individual founded. |
| `AUTHORED` | Research Paper | Many-to-Many | Research papers authored or co-authored by this founder. |
| `HOLDS_PATENT` | Patent | Many-to-Many | Patents held in the founder's personal name. |
| `MENTORED_BY` | Mentor | Many-to-Many | Mentors who formally advise this founder. |
| `PREVIOUSLY_FOUNDED` | Startup (external reference) | Many-to-Many | Prior ventures. Represented as external reference nodes if not in TIDES. |
| `IS_TEAM_MEMBER` | Team Member | One-to-One | Dual-role: every Founder is also a Team Member for aggregation purposes. |
| `ASSOCIATED_WITH` | Investor | Many-to-Many | Investors who have previously backed this founder in prior ventures. |

#### Evidence Sources

- Founder intake form (primary, structured)
- CV / résumé document (extracted prior ventures, qualifications, publications)
- LinkedIn profile (cross-validation of employment history, publications)
- Company founding documents (equity stake, role)
- Patent database records (patents held)
- Academic publication databases (publications count)

#### Validation Methods

- `prior_exits` claimed must be cross-referenced against publicly available company records (acquisition announcements, IPO registrations). Unverified exits reduce the confidence score for this attribute.
- `equity_stake_percent` across all Founder and Team Member nodes linked to a Startup must not exceed 100.0%. Violations generate an integrity error.
- `highest_qualification` institution and degree are cross-referenced against publicly available university accreditation registries where possible.
- `criminal_record_declared` is a self-declaration flag and carries a confidence score of 0.5 (self-reported only); the pipeline flags this for manual review in all cases.

#### Update Rules

- `founder_id` and `full_name` are immutable.
- `equity_stake_percent` is updated upon each cap table update event, with the prior value preserved in version history.
- `full_time_committed` may be updated at any evaluation cycle based on founder-submitted information.
- `prior_exits` is immutable once verified by a human reviewer; it may only increase, never decrease.

#### Confidence Tracking

Founder entity confidence is particularly sensitive to the availability of verifiable external records. Attributes sourced from publicly verifiable records (patents, publications, company registries) receive confidence scores ≥ 0.80. Self-reported attributes (advisory roles, prior ventures without public verification) receive scores between 0.40 and 0.65. The entity-level confidence is the weighted average across all populated attributes, with verifiable attributes weighted at 3× relative to self-reported attributes.

#### Versioning

Snapshot versioning. Each update to the Founder entity creates a new snapshot linked to the Startup entity's graph version at the time of the update. The equity stake history is particularly critical and is maintained as a complete time-series of all recorded values, each timestamped and sourced.

---

### 2.3 Team Member

#### Entity Definition

The Team Member entity represents any individual associated with the startup in a formal capacity other than as a founding co-founder — including employees, technical staff, advisors, board members, and part-time contributors. Team Member entities collectively model the operational depth of the startup's human capital. Unlike the Founder entity, Team Members may have zero equity stakes and variable commitment levels. The Team Member entity set is evaluated as a whole for skill coverage, seniority distribution, and functional completeness.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `member_id` | UUID | Required | Globally unique identifier. Immutable. |
| `full_name` | String | Required | Legal full name. |
| `role_title` | String | Required | Current role title at the startup. |
| `role_category` | Enum | Required | One of: Engineering, Science, Business, Operations, Advisory, Board, Finance, Legal, Other. |
| `employment_type` | Enum | Required | One of: Full-Time, Part-Time, Contractor, Advisor, Board Member. |
| `start_date` | ISO 8601 Date | Required | Date the individual joined the startup in this role. |
| `end_date` | ISO 8601 Date | Optional | Date of departure, if no longer active. |
| `equity_stake_percent` | Float | Optional | Equity stake, if any. |
| `years_domain_experience` | Integer | Optional | Years of experience in the startup's primary domain. |
| `highest_qualification` | Structured Object | Optional | Degree type, institution, field, year. |
| `key_skills` | List<String> | Optional | Self-reported and extracted key technical or business skills. |
| `is_active` | Boolean | Required | Whether this individual is currently active with the startup. |
| `location_country` | String | Optional | Country of residence. |
| `prior_employers` | List<String> | Optional | Notable prior employers relevant to the startup's domain. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `WORKS_AT` | Startup | Many-to-One | The startup this individual is associated with. |
| `REPORTS_TO` | Team Member | Many-to-One | Organisational hierarchy reporting relationship. |
| `AUTHORED` | Research Paper | Many-to-Many | Research papers authored by this team member. |
| `MENTORED_BY` | Mentor | Many-to-Many | Mentor relationships applicable to this individual. |
| `IS_FOUNDER` | Founder | One-to-One | If this team member is also a founder, cross-link to Founder node. |

#### Evidence Sources

- Team member intake form (structured, primary)
- CV / résumé (extracted qualifications, prior employers, skills)
- LinkedIn profile (cross-validation)
- Organisational chart document (role, reporting structure)
- Cap table document (equity stake)

#### Validation Methods

- `start_date` must not be before the Startup's `founding_date`.
- `employment_type` of Advisory or Board Member is cross-checked: team members in these categories should have no `equity_stake_percent` exceeding threshold values defined in the TIDES Equity Reasonableness Table.
- Aggregate equity stakes across all Team Members and Founders must not exceed 100%.
- `is_active` must be consistent with `end_date`: if `end_date` is populated, `is_active` must be False.

#### Update Rules

- `member_id` and `full_name` are immutable.
- `role_title`, `employment_type`, and `equity_stake_percent` may be updated on role-change events.
- `is_active` is set to False and `end_date` is populated upon departure.
- Historical roles are preserved as version records linked to the member node.

#### Confidence Tracking

Confidence at the Team Member level follows the same dual weighting of verifiable vs. self-reported attributes as the Founder entity. An additional deduction of −0.10 is applied to the entity confidence if `employment_type` is Advisor or Board Member and no formal agreement document is linked through the Document entity.

#### Versioning

Delta versioning for non-equity attributes; snapshot versioning for equity stake changes. Role history is maintained as a list of role records, each with start and end dates, preserving the full employment trajectory.

---

### 2.4 Technology

#### Entity Definition

The Technology entity represents a discrete, named technology — whether proprietary, licensed, open, or in-development — that the startup uses, depends upon, or has developed. Technologies are foundational to the evaluation of the startup's competitive position, defensibility, and scalability. Each Technology node is typed by domain and linked to its maturity level through one or more TRL Record entities. A startup may depend on multiple technologies simultaneously, and the same technology may appear in multiple startup graphs.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `technology_id` | UUID | Required | Globally unique identifier. Immutable. |
| `technology_name` | String | Required | Human-readable name of the technology. |
| `technology_domain` | Enum | Required | Primary domain: Biotechnology, Software, Hardware, Materials, Energy, Agriculture, Other. |
| `technology_sub_domain` | String | Optional | More specific sub-domain descriptor. |
| `ownership_type` | Enum | Required | One of: Proprietary, Licensed, Open-Source, In-Development, Partnership. |
| `description` | String (≤ 1000 chars) | Required | Technical description of the technology and its role in the startup's offering. |
| `development_stage` | Enum | Required | Aligned to TRL scale: maps to the current TRL Record's level. |
| `is_core_technology` | Boolean | Required | Whether this technology is core to the startup's primary value proposition. |
| `license_expiry_date` | ISO 8601 Date | Optional | Applicable if `ownership_type` is Licensed. |
| `technology_readiness_level` | Integer [1–9] | Required | Current TRL as of the most recent TRL Record linked to this node. |
| `dependency_count` | Integer | Optional | Number of other technologies this technology depends upon. |
| `open_source_license_type` | String | Optional | Applicable if `ownership_type` is Open-Source (e.g., MIT, GPL-3.0). |
| `patent_protected` | Boolean | Required | Whether this technology is protected by one or more patents in the IP Portfolio. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `USED_BY` | Startup | Many-to-One | The startup(s) that use this technology. |
| `HAS_TRL_RECORD` | TRL Record | One-to-Many | All TRL assessments recorded for this technology over time. |
| `EMBODIED_IN` | Product | Many-to-Many | Products that incorporate this technology. |
| `PROTECTED_BY` | Patent | Many-to-Many | Patents that protect this technology. |
| `DEPENDS_ON` | Technology | Many-to-Many | Other technologies this technology builds upon or requires. |
| `REFERENCED_IN` | Research Paper | Many-to-Many | Research papers that describe or validate this technology. |
| `CONTESTED_BY` | Competitor | Many-to-Many | Competitors who use the same or closely substitutable technology. |

#### Evidence Sources

- Technical due diligence questionnaire (structured, primary)
- Pitch deck (extracted technology names and descriptions)
- Research papers (technical description, validation)
- Patent filings (patent protection status)
- Product documentation (embodiment in products)
- TRL assessment outputs from technology evaluation agents

#### Validation Methods

- `technology_readiness_level` must match the level recorded in the most recent linked TRL Record. Inconsistencies generate a validation flag.
- `patent_protected` must be True only if at least one linked Patent node exists with status Active or Granted.
- `license_expiry_date` is mandatory if `ownership_type` is Licensed. Absence of this field when ownership type is Licensed generates a completeness warning.
- `open_source_license_type` is mandatory if `ownership_type` is Open-Source.

#### Update Rules

- `technology_id` and `technology_name` are immutable.
- `technology_readiness_level` is updated when a new TRL Record is linked to this node.
- `patent_protected` is updated automatically when the linked IP Portfolio or Patent entities change.
- `ownership_type` may change (e.g., from Licensed to Proprietary) upon confirmed IP transfer, with version record.

#### Confidence Tracking

The confidence score for a Technology entity is heavily weighted by the `technology_readiness_level` attribute's confidence, as this is the most consequential value for evaluation. TRL assessments conducted by accredited independent reviewers receive a source quality score of 0.90; TRL assessments that are self-reported receive 0.50. The entity-level confidence also incorporates whether the technology is cross-referenced in peer-reviewed research papers (bonus of +0.07) and whether it has active patent protection (+0.05).

#### Versioning

Snapshot versioning. Each TRL Record linked to this entity is effectively a versioned TRL assessment. The Technology entity's own snapshot history records changes to ownership type, patent protection status, and core technology classification.

---

### 2.5 TRL Record

#### Entity Definition

The TRL Record entity captures a single, timestamped assessment of the Technology Readiness Level (TRL) of a specific technology, following the nine-point TRL scale standardised by international evaluation bodies. Each TRL Record is associated with exactly one Technology entity and records not just the TRL level assigned but the evidence basis for that assignment, the assessor's identity, and the confidence in the assessment. Multiple TRL Records may exist for a single Technology entity, forming a time-series of maturity progression.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `trl_record_id` | UUID | Required | Globally unique identifier. Immutable. |
| `technology_id` | UUID | Required | Foreign reference to the assessed Technology entity. |
| `trl_level` | Integer [1–9] | Required | Assigned TRL level per the nine-point scale. |
| `assessment_date` | ISO 8601 Date | Required | Date on which this TRL assessment was conducted. |
| `assessor_type` | Enum | Required | One of: Self-Assessment, Internal-Review, Independent-Expert, Accredited-Body. |
| `assessor_identity` | String | Optional | Name or organisation of the assessor, if not anonymous. |
| `evidence_summary` | String (≤ 2000 chars) | Required | Summary of the evidence basis for the assigned TRL level. |
| `evidence_documents` | List<UUID> | Optional | Document entity IDs for all supporting documents referenced in the assessment. |
| `next_trl_prerequisites` | String (≤ 1000 chars) | Optional | Description of what must be achieved to advance to the next TRL level. |
| `confidence_in_assessment` | Float [0.0–1.0] | Required | Confidence score for this assessment, set by the assessing agent or reviewer. |
| `is_current` | Boolean | Required | Whether this is the most recent TRL Record for the linked Technology entity. |
| `assessment_context` | String | Optional | Context in which the assessment was made (e.g., lab demonstration, field pilot). |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `ASSESSES` | Technology | Many-to-One | The technology this record assesses. |
| `SUPPORTED_BY` | Document | Many-to-Many | Documents that provide evidence for this TRL assessment. |
| `PRODUCED_BY` | Evaluation | Many-to-One | The evaluation run during which this record was created. |

#### Evidence Sources

- Technology evaluation agent outputs (primary)
- Supporting technical documents submitted by the startup (lab reports, field trial reports)
- Independent expert assessor reports
- Accredited body certification documents

#### Validation Methods

- `trl_level` must be an integer in the range [1, 9]. Out-of-range values are rejected.
- Only one TRL Record per Technology entity may have `is_current` set to True at any given time.
- `assessment_date` must not be in the future.
- Self-assessment records (`assessor_type` = Self-Assessment) automatically receive a confidence cap of 0.55.

#### Update Rules

- TRL Records are immutable once committed. New assessments create new TRL Record nodes.
- When a new TRL Record is committed with `is_current` = True, the prior current record's `is_current` flag is set to False.
- The linked Technology entity's `technology_readiness_level` attribute is updated to reflect the new current record's `trl_level`.

#### Confidence Tracking

The confidence score of a TRL Record is determined primarily by `assessor_type`. Accredited-Body assessments receive a baseline of 0.90; Independent-Expert assessments receive 0.80; Internal-Review assessments receive 0.65; Self-Assessments receive 0.50. The score is further adjusted based on the quality and completeness of `evidence_summary` and the number of linked supporting documents.

#### Versioning

Each TRL Record is a discrete, immutable version record. The full sequence of TRL Records for a given Technology entity constitutes the complete TRL history for that technology. No delta versioning is applied; each record is a full snapshot of the assessment at that point in time.

---

### 2.6 Market

#### Entity Definition

The Market entity represents a defined commercial or research market that the startup is targeting, operating in, or planning to enter. Markets are defined along multiple dimensions: geographic scope, sector, customer base, and regulatory environment. The Market entity captures both quantitative market sizing data (TAM, SAM, SOM) and qualitative characteristics such as growth trajectory and regulatory friction. Each startup may be associated with multiple market nodes representing different geographic or segment-level markets.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `market_id` | UUID | Required | Globally unique identifier. |
| `market_name` | String | Required | Human-readable name of the market (e.g., "Indian SME Cloud ERP Market"). |
| `geographic_scope` | Enum | Required | One of: Local, National, Regional, Global. |
| `geographic_region` | String | Required | Specific region(s) covered (e.g., South Asia, European Union). |
| `sector_classification` | Enum | Required | Sector per TIDES Sector Taxonomy. |
| `total_addressable_market_usd` | Float | Optional | TAM in USD. As of `sizing_reference_year`. |
| `serviceable_addressable_market_usd` | Float | Optional | SAM in USD. |
| `serviceable_obtainable_market_usd` | Float | Optional | SOM in USD, specific to the startup's realistic reach. |
| `sizing_reference_year` | Integer | Optional | The year to which all market size figures refer. |
| `sizing_source` | String | Optional | Named source for market sizing figures (e.g., report publisher name). |
| `cagr_percent` | Float | Optional | Compound Annual Growth Rate of the market over the next 3–5 years. |
| `market_maturity` | Enum | Optional | One of: Emerging, Growth, Mature, Declining. |
| `key_regulatory_bodies` | List<String> | Optional | Names of primary regulatory bodies governing this market. |
| `regulatory_complexity` | Enum | Optional | One of: Low, Medium, High, Very High. |
| `market_entry_barriers` | String (≤ 500 chars) | Optional | Description of primary barriers to entry. |
| `competitive_intensity` | Enum | Optional | One of: Fragmented, Moderate, Concentrated, Monopolistic. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `TARGETED_BY` | Startup | Many-to-Many | Startups targeting this market. |
| `CONTAINS` | Customer Segment | One-to-Many | Customer segments that exist within this market. |
| `OCCUPIED_BY` | Competitor | Many-to-Many | Competitors operating in this market. |
| `GOVERNED_BY_REGULATION` | Document | Many-to-Many | Key regulatory documents or frameworks governing this market. |

#### Evidence Sources

- Market sizing reports (extracted TAM, SAM, SOM, CAGR)
- Pitch deck (extracted market descriptions and size claims)
- Market assessment agent outputs (derived and validated figures)
- Regulatory filings and government databases

#### Validation Methods

- `total_addressable_market_usd` must be ≥ `serviceable_addressable_market_usd` ≥ `serviceable_obtainable_market_usd`. Violations generate integrity errors.
- `cagr_percent` must be within the range [−50.0, +200.0]. Out-of-range values generate validation flags.
- `sizing_source` is required if any market size figure is populated.
- `sizing_reference_year` must be within 5 years of the assessment date for the data to be considered current; older data receives a freshness penalty on confidence.

#### Update Rules

- Market entity attributes are updated when a new market sizing report is ingested or when the market assessment agent produces revised figures.
- `market_id` and `market_name` are immutable.
- Size figures are versioned; prior values are retained in version history.

#### Confidence Tracking

Market entity confidence is strongly influenced by source quality of sizing figures. Figures sourced from named, reputable market research publishers receive a base confidence of 0.75. Figures derived solely from startup claims in pitch decks receive 0.40. Corroboration from two or more independent sources raises confidence by +0.10 per additional corroborating source, capped at 0.95.

#### Versioning

Snapshot versioning at each market assessment update. TAM, SAM, and SOM figures are maintained as time-series with reference year, so evaluators can compare market size assumptions across evaluation cycles.

---

### 2.7 Customer Segment

#### Entity Definition

The Customer Segment entity represents a distinct, defined group of customers within a market that the startup is targeting with a specific value proposition. Customer segments are more granular than markets: a startup targeting the healthcare market may have customer segments defined as "private multi-specialty hospitals in Tier 1 Indian cities" and "rural primary health centres under government schemes." Each segment has distinct characteristics, willingness-to-pay profiles, and acquisition dynamics. Customer Segment entities capture the structure of the startup's go-to-market strategy at a granular level.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `segment_id` | UUID | Required | Globally unique identifier. |
| `segment_name` | String | Required | Descriptive name of the segment. |
| `segment_type` | Enum | Required | One of: B2B, B2C, B2G, B2B2C, D2C. |
| `geographic_scope` | String | Required | Geographic scope of this segment. |
| `estimated_segment_size` | Integer | Optional | Estimated number of potential customers in this segment. |
| `sizing_methodology` | String | Optional | Description of how segment size was estimated. |
| `average_revenue_per_customer_usd` | Float | Optional | Expected or observed average annual revenue per customer. |
| `customer_acquisition_cost_usd` | Float | Optional | Cost to acquire a single customer in this segment. |
| `customer_lifetime_value_usd` | Float | Optional | Expected lifetime value of a customer in this segment. |
| `pain_point_description` | String (≤ 500 chars) | Optional | Description of the primary problem faced by this segment. |
| `willingness_to_pay_validated` | Boolean | Required | Whether willingness to pay has been validated through customer interviews or pilots. |
| `validation_method` | String | Optional | Description of the validation approach (surveys, pilots, letters of intent). |
| `conversion_stage` | Enum | Optional | One of: Awareness, Consideration, Pilot, Active, Churned. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `EXISTS_IN` | Market | Many-to-One | The market this segment belongs to. |
| `TARGETED_BY` | Product | Many-to-Many | Products designed for this segment. |
| `GENERATES` | Revenue Record | One-to-Many | Revenue records attributed to this segment. |

#### Evidence Sources

- Customer discovery documentation (primary)
- Pilot program reports
- Letters of intent from prospective customers
- Sales CRM export data
- Market research primary data (surveys, interviews)
- Agent outputs from market segmentation analysis

#### Validation Methods

- `customer_lifetime_value_usd` must be ≥ `customer_acquisition_cost_usd` for the segment to be classified as viable. Segments where LTV < CAC generate a viability flag.
- `willingness_to_pay_validated` may only be True if `validation_method` is populated.
- `average_revenue_per_customer_usd` must be consistent with any linked Revenue Records attributed to this segment.

#### Update Rules

- `segment_id` is immutable.
- `conversion_stage` is updated as the startup progresses through sales pipeline stages.
- `willingness_to_pay_validated` may change from False to True; it may not revert to False once validated.

#### Confidence Tracking

The most consequential confidence determination is on `willingness_to_pay_validated`. Self-reported validation receives 0.50; pilot-based validation receives 0.80; signed letters of intent receive 0.85; closed contracts receive 0.95.

#### Versioning

Snapshot versioning. Segment size estimates and financial metrics are time-series tracked to observe how the startup's market understanding evolves across evaluation cycles.

---

### 2.8 Revenue Record

#### Entity Definition

The Revenue Record entity represents a discrete, timestamped record of revenue generated by the startup, attributed to a specific product, customer segment, geography, or revenue model. Revenue Records are the granular transactional evidence layer underlying the Financial Statement entity, which provides aggregate financial summaries. The distinction is important: a Financial Statement may report total revenue for a fiscal year, while individual Revenue Records capture the composition of that revenue — from which products, from which segments, through which channels. Revenue Records are the primary input for the revenue validation traversal pattern used by financial analysis agents.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `revenue_record_id` | UUID | Required | Globally unique identifier. |
| `period_start` | ISO 8601 Date | Required | Start date of the revenue period this record covers. |
| `period_end` | ISO 8601 Date | Required | End date of the revenue period. |
| `revenue_amount_usd` | Float | Required | Total revenue in USD for this period and classification. |
| `currency_original` | String (ISO 4217) | Optional | Original currency if not USD. |
| `amount_original_currency` | Float | Optional | Amount in original currency before conversion. |
| `exchange_rate_used` | Float | Optional | Exchange rate applied for USD conversion. |
| `revenue_type` | Enum | Required | One of: Recurring, One-Time, License, Grant, Deferred, Other. |
| `revenue_model` | Enum | Optional | One of: Subscription, Transaction-Fee, Service, Product-Sale, Royalty, Other. |
| `attributed_product_id` | UUID | Optional | Reference to the Product entity that generated this revenue. |
| `attributed_segment_id` | UUID | Optional | Reference to the Customer Segment that generated this revenue. |
| `verification_status` | Enum | Required | One of: Unverified, Self-Reported, Audited, Third-Party-Verified. |
| `supporting_document_id` | UUID | Optional | Document entity ID of the supporting invoice, contract, or bank statement. |
| `mrr_flag` | Boolean | Optional | Whether this record contributes to Monthly Recurring Revenue calculation. |
| `growth_rate_mom_percent` | Float | Optional | Month-over-month growth rate, if this is a recurring revenue record. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `GENERATED_BY` | Startup | Many-to-One | The startup that generated this revenue. |
| `ATTRIBUTED_TO_PRODUCT` | Product | Many-to-One | The product that generated this revenue. |
| `ATTRIBUTED_TO_SEGMENT` | Customer Segment | Many-to-One | The customer segment that generated this revenue. |
| `DOCUMENTED_IN` | Document | Many-to-One | Supporting document (invoice, contract, bank statement). |
| `AGGREGATED_IN` | Financial Statement | Many-to-One | The Financial Statement in which this revenue appears in aggregate. |

#### Evidence Sources

- Bank statements (highest confidence)
- Audited financial statements
- Invoices and contracts
- Accounting system exports
- Self-reported revenue declarations (lowest confidence)

#### Validation Methods

- `revenue_amount_usd` must be ≥ 0.
- `period_end` must be after `period_start`.
- Sum of all Revenue Records in a given period must be reconcilable with the total revenue line in the corresponding Financial Statement, within a 2% tolerance.
- `verification_status` = Audited requires a linked Document entity of type Audited Financial Statement.

#### Update Rules

- Revenue Records are generally immutable once committed with `verification_status` = Audited.
- Self-reported records may be upgraded in verification status as supporting documents are provided; this creates a new version of the record.

#### Confidence Tracking

Confidence is directly determined by `verification_status`: Audited = 0.95, Third-Party-Verified = 0.85, Self-Reported = 0.45, Unverified = 0.30.

#### Versioning

Delta versioning for verification status upgrades. Each version preserves the prior verification status and the timestamp of the upgrade, providing a clear audit trail of how revenue claims were progressively verified.

---

### 2.9 Investor

#### Entity Definition

The Investor entity represents any individual, institutional entity, fund, or organisation that has provided or is in the process of providing equity or debt capital to the startup. Investor entities capture not only the financial terms of the investment but also the strategic value of the investor relationship — sector expertise, portfolio network, follow-on capacity, and geographic reach. The presence of credible, domain-relevant investors is a significant positive signal in the TIDES evaluation framework.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `investor_id` | UUID | Required | Globally unique identifier. |
| `investor_name` | String | Required | Legal name of the investor entity or individual. |
| `investor_type` | Enum | Required | One of: Angel, VC-Fund, Corporate-VC, Family-Office, Government-Fund, Accelerator, Crowdfunding, Debt-Provider, Other. |
| `investment_amount_usd` | Float | Required | Total capital committed by this investor in this startup, in USD. |
| `investment_round` | Enum | Required | One of: Pre-Seed, Seed, Series A, Series B, Series C, Bridge, Convertible-Note, SAFE, Grant-Equity, Other. |
| `investment_date` | ISO 8601 Date | Required | Date of the investment transaction or agreement. |
| `equity_stake_percent` | Float | Optional | Equity percentage received in exchange for the investment. |
| `valuation_at_investment_usd` | Float | Optional | Post-money valuation at the time of investment. |
| `lead_investor_flag` | Boolean | Required | Whether this investor led the investment round. |
| `follow_on_capacity` | Enum | Optional | One of: None, Limited, Moderate, High. |
| `domain_expertise_sectors` | List<Enum> | Optional | Sectors in which this investor has domain expertise. |
| `portfolio_company_count` | Integer | Optional | Total number of portfolio companies (indicator of experience). |
| `verification_status` | Enum | Required | One of: Unverified, Startup-Reported, Agreement-Verified, Public-Record. |
| `investor_geography` | String | Optional | Primary geography of operation of the investor. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `INVESTED_IN` | Startup | Many-to-Many | Startups this investor has invested in. |
| `LED_ROUND` | Startup | Many-to-Many | Rounds the investor led. |
| `ASSOCIATED_WITH` | Founder | Many-to-Many | Founders the investor has previously backed. |
| `VERIFIED_BY` | Document | Many-to-One | Investment agreement or term sheet that verifies the investment. |

#### Evidence Sources

- Investment term sheets and shareholder agreements (primary)
- Cap table documents
- Public funding announcements
- Regulatory disclosures (e.g., company registry filings post-investment)
- Investor-provided data via due diligence forms

#### Validation Methods

- `investment_amount_usd` must be consistent with the equity stake and valuation: `investment_amount_usd` ÷ `equity_stake_percent` × 100 should approximate `valuation_at_investment_usd` within a 10% tolerance.
- `verification_status` = Agreement-Verified requires a linked Document entity of type Investment Agreement.
- Multiple investors in the same round must have equity stakes that, combined with founder and team equity, remain ≤ 100%.

#### Update Rules

- `investor_id`, `investment_date`, and `investment_amount_usd` are immutable once verified.
- `verification_status` may be upgraded as supporting documents are provided.
- Follow-on investments create new Investor entities (or new relationship edges with additional metadata) rather than updating the original investment record.

#### Confidence Tracking

Investor entity confidence is driven by `verification_status`. Public-Record verification (e.g., company registry) = 0.95; Agreement-Verified = 0.88; Startup-Reported = 0.50; Unverified = 0.25.

#### Versioning

Snapshot versioning per investment event. Each round is tracked as a separate set of Investor nodes linked to the startup, enabling the evaluation of the startup's full funding history and the progression of investor quality across rounds.

---

### 2.10 Grant

#### Entity Definition

The Grant entity represents a non-dilutive funding award received by or applied for by the startup from a government body, foundation, research council, or international development agency. Grants are significant not only for their financial value but as third-party validation signals: the awarding of a competitive grant indicates that the startup's technology or mission has passed the scrutiny of an independent expert review panel. The Grant entity captures the full lifecycle of a grant, from application through disbursement.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `grant_id` | UUID | Required | Globally unique identifier. |
| `grant_name` | String | Required | Official name of the grant scheme. |
| `granting_body` | String | Required | Name of the granting organisation or authority. |
| `grant_amount_usd` | Float | Required | Total grant value in USD. |
| `currency_original` | String (ISO 4217) | Optional | Original currency if not USD. |
| `amount_original_currency` | Float | Optional | Amount in original currency. |
| `grant_type` | Enum | Required | One of: Research, Commercialisation, Export, Social-Impact, Technology-Development, Other. |
| `application_date` | ISO 8601 Date | Required | Date the startup submitted its grant application. |
| `award_date` | ISO 8601 Date | Optional | Date the grant was formally awarded. |
| `disbursement_date` | ISO 8601 Date | Optional | Date of the first fund disbursement. |
| `grant_status` | Enum | Required | One of: Applied, Under-Review, Awarded, Disbursed, Rejected, Withdrawn. |
| `disbursement_tranche_count` | Integer | Optional | Number of tranches in which the grant is to be disbursed. |
| `milestone_conditions` | String (≤ 1000 chars) | Optional | Conditions the startup must meet for continued or future disbursements. |
| `grant_reference_number` | String | Optional | Official reference number assigned by the granting body. |
| `reporting_obligations` | String (≤ 500 chars) | Optional | Summary of reporting requirements attached to the grant. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `AWARDED_TO` | Startup | Many-to-One | The startup that received this grant. |
| `SUPPORTS` | Technology | Many-to-Many | Technologies whose development this grant is funding. |
| `SUPPORTS_PRODUCT` | Product | Many-to-Many | Products being developed with this grant. |
| `LINKED_TO_MILESTONE` | Milestone | Many-to-Many | Milestones required for grant disbursement. |
| `DOCUMENTED_BY` | Document | Many-to-Many | Grant agreement and award letters. |

#### Evidence Sources

- Grant award letters (primary)
- Government grant databases and public announcements
- Startup-submitted grant application documents
- Financial statements showing grant income

#### Validation Methods

- `award_date` must not precede `application_date`.
- `disbursement_date` must not precede `award_date`.
- `grant_reference_number` is cross-validated against the granting body's public grant registry where available.
- `grant_status` = Awarded requires either a linked award letter document or a public registry cross-check.

#### Update Rules

- `grant_id`, `grant_name`, `granting_body`, and `grant_amount_usd` are immutable once awarded.
- `grant_status` transitions along the defined lifecycle (Applied → Under-Review → Awarded → Disbursed) and may not reverse except to Rejected or Withdrawn.
- Disbursement events create new event records linked to the Grant node rather than updating the original node.

#### Confidence Tracking

Grant confidence is high when publicly verifiable. Public registry confirmation = 0.92; award letter linked = 0.85; startup-reported only = 0.50; applied only (not yet awarded) = 0.30.

#### Versioning

Snapshot versioning tied to grant status transitions. Each status change creates a new version snapshot of the Grant entity.

---

### 2.11 Patent

#### Entity Definition

The Patent entity represents a single patent application or granted patent that is associated with the startup's technology portfolio. Patents are a primary signal of technological defensibility and represent a legal barrier against competitor imitation. The Patent entity captures both the administrative details of the patent (filing number, jurisdiction, status) and the substantive scope of the patent's claims as they relate to the startup's technology and competitive positioning. Multiple Patent entities are aggregated through the IP Portfolio entity.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `patent_id` | UUID | Required | Globally unique identifier. |
| `application_number` | String | Required | Official application number assigned by the patent office. |
| `grant_number` | String | Optional | Official grant number, once granted. |
| `patent_title` | String | Required | Official title of the patent. |
| `filing_date` | ISO 8601 Date | Required | Date of filing. |
| `grant_date` | ISO 8601 Date | Optional | Date of grant. |
| `expiry_date` | ISO 8601 Date | Optional | Expected expiry date (typically 20 years from filing). |
| `status` | Enum | Required | One of: Filed, Published, Granted, Expired, Abandoned, Opposed. |
| `jurisdiction` | List<String> | Required | Countries or regions in which the patent is filed or granted. |
| `patent_type` | Enum | Required | One of: Utility, Design, Plant, Provisional. |
| `abstract_summary` | String (≤ 1000 chars) | Required | Plain-language summary of the patent's claims and inventive step. |
| `ipc_classification` | List<String> | Optional | International Patent Classification codes. |
| `claim_count` | Integer | Optional | Number of claims in the patent. |
| `inventor_names` | List<String> | Required | Names of all listed inventors. |
| `assignee_name` | String | Required | Legal entity to which the patent is assigned (should match startup legal name). |
| `prior_art_search_conducted` | Boolean | Optional | Whether a prior art search was conducted prior to filing. |
| `opposition_risk_level` | Enum | Optional | One of: Low, Medium, High — assessed risk of opposition post-grant. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `PROTECTS` | Technology | Many-to-Many | Technologies this patent covers. |
| `BELONGS_TO` | IP Portfolio | Many-to-One | The IP Portfolio that contains this patent. |
| `INVENTED_BY` | Founder | Many-to-Many | Founders listed as inventors. |
| `INVENTED_BY_MEMBER` | Team Member | Many-to-Many | Team members listed as inventors. |
| `REFERENCED_IN` | Research Paper | Many-to-Many | Research papers that cite this patent or are cited by it. |
| `CONTESTED_BY` | Competitor | Many-to-Many | Competitors who have filed overlapping or competing patents. |

#### Evidence Sources

- Patent office databases (primary — filing details, status, grant dates)
- Patent filing documents submitted by the startup
- IP attorney reports
- Prior art search reports

#### Validation Methods

- `application_number` is validated against the relevant national patent office database.
- `assignee_name` must match or be a legal variant of the Startup's `legal_name`. Discrepancies generate an IP ownership flag.
- `expiry_date` is computed as `filing_date` + 20 years (for utility patents). Discrepancies from this formula generate a validation flag.
- `status` = Granted requires `grant_number` to be populated.

#### Update Rules

- `patent_id`, `application_number`, `filing_date`, and `inventor_names` are immutable.
- `status` is updated upon receipt of patent office communications (publication, grant, opposition decisions).
- `grant_date` is populated when status transitions to Granted.

#### Confidence Tracking

Patent office database confirmation = 0.95. Startup-submitted documents only (no external database confirmation) = 0.70. Self-reported with no documentation = 0.35.

#### Versioning

Snapshot versioning. Status transitions are preserved in version history to track the patent's journey through the examination process.

---

### 2.12 Product

#### Entity Definition

The Product entity represents a discrete product or service offered by the startup to its customers or beneficiaries. Products are the primary interface between the startup's technology capabilities and its market. The Product entity captures the product's current development stage, its associated technologies, the customer segments it targets, and its pricing model. A startup may have multiple products at different stages of development. The Product entity is a central node in the graph, linking technology, market, revenue, and customer entities.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `product_id` | UUID | Required | Globally unique identifier. |
| `product_name` | String | Required | Commercial name of the product or service. |
| `product_type` | Enum | Required | One of: Physical, Software, SaaS, Platform, Service, Hybrid, Research-Tool. |
| `development_stage` | Enum | Required | One of: Concept, Prototype, Beta, Launched, Scaling, Discontinued. |
| `launch_date` | ISO 8601 Date | Optional | Date of commercial launch. |
| `description` | String (≤ 1000 chars) | Required | Description of what the product does and the problem it solves. |
| `pricing_model` | Enum | Optional | One of: One-Time-Purchase, Subscription, Usage-Based, Freemium, Licensing, Grant-Funded, Other. |
| `price_point_usd` | Float | Optional | Entry-level price point in USD. |
| `customer_count_active` | Integer | Optional | Number of active paying or engaged customers at time of last update. |
| `customer_count_pipeline` | Integer | Optional | Number of customers in active sales pipeline. |
| `net_promoter_score` | Integer [−100 to 100] | Optional | NPS score if measured. |
| `regulatory_approval_required` | Boolean | Required | Whether the product requires regulatory approval in its target market. |
| `regulatory_approval_status` | Enum | Optional | One of: Not-Required, Applied, In-Review, Approved, Rejected. |
| `pilot_conducted` | Boolean | Required | Whether a pilot or proof-of-concept has been conducted with real customers. |
| `pilot_outcome_summary` | String (≤ 500 chars) | Optional | Summary of pilot results if conducted. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `OFFERED_BY` | Startup | Many-to-One | The startup that offers this product. |
| `INCORPORATES` | Technology | Many-to-Many | Technologies embedded in this product. |
| `TARGETS` | Customer Segment | Many-to-Many | Customer segments this product addresses. |
| `COMPETES_WITH` | Competitor | Many-to-Many | Competing products offered by competitor entities. |
| `GENERATES` | Revenue Record | One-to-Many | Revenue attributed to this product. |
| `DESCRIBED_IN` | Document | Many-to-Many | Product documentation, brochures, datasheets. |

#### Evidence Sources

- Product documentation submitted by startup
- Pitch deck (product section extraction)
- Customer testimonials and pilot reports
- Regulatory approval documents
- Revenue records attributed to the product

#### Validation Methods

- `regulatory_approval_status` is required when `regulatory_approval_required` is True.
- `development_stage` = Launched requires `launch_date` to be populated.
- `pilot_outcome_summary` is required when `pilot_conducted` is True.
- `customer_count_active` must be consistent with linked Revenue Records: a product with `customer_count_active` > 0 should have at least one linked Revenue Record.

#### Update Rules

- `product_id` and `product_name` are immutable.
- `development_stage`, `customer_count_active`, `customer_count_pipeline` are updated at each evaluation cycle or upon confirmed trigger events.
- `regulatory_approval_status` transitions follow a strict lifecycle and are versioned.

#### Confidence Tracking

`pilot_conducted` = True with a linked pilot report document: confidence bonus +0.10. `customer_count_active` corroborated by Revenue Records: confidence bonus +0.08. `regulatory_approval_status` backed by official approval document: confidence bonus +0.15.

#### Versioning

Snapshot versioning. `development_stage` progression is time-series tracked as a key product lifecycle indicator.

---

### 2.13 Competitor

#### Entity Definition

The Competitor entity represents a company, product, or alternative solution that competes — directly or indirectly — with the startup's offering in one or more markets. Competitors are identified through market analysis, startup disclosure, patent analysis, and agent-driven research. The Competitor entity captures the competitive landscape that contextualises the startup's position and is a key input for the competitive moat assessment traversal pattern. Competitors may be commercial entities, research groups, open-source projects, or government-backed alternatives.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `competitor_id` | UUID | Required | Globally unique identifier. |
| `competitor_name` | String | Required | Name of the competing entity or product. |
| `competitor_type` | Enum | Required | One of: Direct, Indirect, Substitute, Potential-Entrant. |
| `entity_type` | Enum | Required | One of: Commercial-Company, Research-Institution, Open-Source-Project, Government-Programme, Individual. |
| `founding_year` | Integer | Optional | Year the competitor was founded or the project was initiated. |
| `headquarters_country` | String | Optional | Country of headquarters. |
| `estimated_funding_usd` | Float | Optional | Total estimated funding raised by the competitor. |
| `revenue_estimate_usd` | Float | Optional | Annual revenue estimate. |
| `market_share_percent` | Float | Optional | Estimated market share in shared markets. |
| `key_differentiator` | String (≤ 500 chars) | Optional | Primary competitive advantage of this competitor. |
| `primary_technology_domain` | Enum | Optional | Primary technology domain of the competitor's offering. |
| `patent_portfolio_size` | Integer | Optional | Estimated number of active patents held. |
| `threat_level` | Enum | Required | One of: Low, Medium, High, Critical — assessed threat to the startup. |
| `data_source` | String | Optional | Primary source from which this competitor data was derived. |
| `last_verified_date` | ISO 8601 Date | Optional | Date on which this competitor's data was last externally verified. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `COMPETES_IN` | Market | Many-to-Many | Markets in which this competitor operates. |
| `COMPETES_WITH_PRODUCT` | Product | Many-to-Many | Startup products this competitor's offering competes with. |
| `USES_TECHNOLOGY` | Technology | Many-to-Many | Technologies the competitor uses or relies upon. |
| `HOLDS_PATENT` | Patent | Many-to-Many | Patents held by the competitor (where publicly known). |
| `IDENTIFIED_BY` | Evaluation | Many-to-Many | Evaluation runs that identified and assessed this competitor. |

#### Evidence Sources

- Market research reports
- Pitch deck competitive landscape section (extracted)
- Patent database searches
- Public funding databases
- Agent-driven web research outputs
- Startup disclosure in competitive analysis forms

#### Validation Methods

- `competitor_type` = Direct requires that the startup and competitor share at least one linked Market and one linked Technology domain.
- `threat_level` must be assessed by the competitive analysis agent and may not be self-assigned by the startup.
- `last_verified_date` must be within 12 months of the current evaluation date for the data to be considered current; older data receives a freshness penalty.

#### Update Rules

- Competitor data is refreshed at each major evaluation cycle.
- `competitor_id` is immutable.
- `threat_level` may be re-assessed at any evaluation cycle.

#### Confidence Tracking

Competitor data sourced from named, reputable market intelligence platforms receives 0.75. Startup-disclosed data receives 0.50. Agent-inferred competitor data (no named external source) receives 0.45. Public patent database-confirmed patent counts receive 0.90.

#### Versioning

Snapshot versioning per evaluation cycle. The competitive landscape is expected to evolve, and version history preserves the baseline at each evaluation for trend analysis.

---

### 2.14 Financial Statement

#### Entity Definition

The Financial Statement entity represents a formal financial summary document for a defined accounting period — typically a fiscal year, half-year, or quarter. Financial Statements capture top-line revenue, cost structure, profitability (or loss), balance sheet position, and cash flow. They are the aggregate financial picture of the startup and serve as the anchor for all financial analysis in the evaluation pipeline. Financial Statements may be unaudited, internally prepared, or formally audited by a registered accounting firm.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `statement_id` | UUID | Required | Globally unique identifier. |
| `period_type` | Enum | Required | One of: Annual, Semi-Annual, Quarterly, Monthly. |
| `period_start` | ISO 8601 Date | Required | Start of the accounting period. |
| `period_end` | ISO 8601 Date | Required | End of the accounting period. |
| `total_revenue_usd` | Float | Required | Total revenue for the period. |
| `cost_of_goods_sold_usd` | Float | Optional | COGS for the period. |
| `gross_profit_usd` | Float | Optional | Gross profit (Revenue minus COGS). |
| `operating_expenses_usd` | Float | Optional | Total operating expenses excluding COGS. |
| `ebitda_usd` | Float | Optional | Earnings before interest, tax, depreciation, and amortisation. |
| `net_profit_loss_usd` | Float | Required | Net profit or loss. Negative values indicate losses. |
| `total_assets_usd` | Float | Optional | Total assets as at period end. |
| `total_liabilities_usd` | Float | Optional | Total liabilities as at period end. |
| `cash_and_equivalents_usd` | Float | Optional | Cash and near-cash balances as at period end. |
| `burn_rate_monthly_usd` | Float | Optional | Average monthly cash expenditure (for pre-revenue or loss-making startups). |
| `runway_months` | Float | Optional | Estimated months of operation remaining at current burn rate. |
| `audit_status` | Enum | Required | One of: Unaudited, Management-Accounts, Independently-Reviewed, Audited. |
| `auditor_name` | String | Optional | Name of the auditing firm, if `audit_status` = Audited. |
| `accounting_standard` | Enum | Optional | One of: IFRS, US-GAAP, Ind-AS, Other. |
| `currency` | String (ISO 4217) | Required | Currency in which the statement is prepared. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `BELONGS_TO` | Startup | Many-to-One | The startup this financial statement describes. |
| `CONTAINS` | Revenue Record | One-to-Many | Granular revenue records aggregated in this statement. |
| `DOCUMENTED_BY` | Document | Many-to-One | The source document (PDF, spreadsheet) from which this entity was populated. |
| `ASSESSED_IN` | Evaluation | Many-to-Many | Evaluation runs that analysed this financial statement. |

#### Evidence Sources

- Audited financial statements (highest confidence)
- CA-certified management accounts
- Founder-prepared financial summaries
- Accounting software export files

#### Validation Methods

- `gross_profit_usd` must equal `total_revenue_usd` − `cost_of_goods_sold_usd` within a 1% tolerance.
- `net_profit_loss_usd` must be derivable from gross profit and operating expenses within a 5% tolerance.
- `burn_rate_monthly_usd` must be consistent with `cash_and_equivalents_usd` and `runway_months`: `cash_and_equivalents_usd` ÷ `burn_rate_monthly_usd` must approximate `runway_months` within 10%.
- Sum of Revenue Records for the corresponding period must reconcile with `total_revenue_usd` within 2%.

#### Update Rules

- Financial Statement entities for closed accounting periods are immutable once `audit_status` = Audited.
- Management accounts for open periods may be updated with revised figures; updates create new versions.
- `audit_status` may only be upgraded (Unaudited → Independently-Reviewed → Audited); it cannot be downgraded.

#### Confidence Tracking

`audit_status` is the primary confidence driver: Audited = 0.95, Independently-Reviewed = 0.80, Management-Accounts = 0.65, Unaudited = 0.45.

#### Versioning

Snapshot versioning. Each version of a financial statement is a full snapshot. Version history enables comparison of management accounts to subsequently audited figures for the same period.

---

### 2.15 Document

#### Entity Definition

The Document entity is the registry node for any file or structured document that has been submitted by the startup or generated during the evaluation process. Documents are the raw source material that feeds the graph population pipeline. Every document that enters the TIDES system is registered as a Document entity, regardless of its format or content type. The Document entity does not store the document contents — it stores the metadata about the document and links to where the document is stored in the underlying document management system. All entities whose attributes were populated from a given document maintain a provenance link to the corresponding Document entity.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `document_id` | UUID | Required | Globally unique identifier. |
| `document_title` | String | Required | Human-readable title or filename of the document. |
| `document_type` | Enum | Required | One of: Pitch-Deck, Financial-Statement, Patent-Filing, Research-Paper, CV, Market-Report, Legal-Agreement, Grant-Document, Regulatory-Filing, Other. |
| `file_format` | Enum | Required | One of: PDF, DOCX, XLSX, PPTX, CSV, HTML, Other. |
| `file_size_bytes` | Integer | Optional | File size in bytes. |
| `submission_date` | ISO 8601 DateTime | Required | Date and time the document was submitted or received. |
| `submitted_by` | UUID | Optional | Identifier of the Founder or Team Member who submitted the document. |
| `document_language` | String (ISO 639-1) | Required | Primary language of the document. |
| `document_version` | String | Optional | Version label on the document (e.g., "v3", "Final", "Draft"). |
| `processing_status` | Enum | Required | One of: Received, Processing, Extracted, Failed, Archived. |
| `extraction_agent_id` | UUID | Optional | Identifier of the extraction agent that processed this document. |
| `extraction_completeness_score` | Float [0.0–1.0] | Optional | Fraction of expected extractable fields successfully extracted. |
| `storage_reference` | String | Required | Reference to the document location in the document management system. |
| `is_current_version` | Boolean | Required | Whether this is the most current version of this document type. |
| `confidentiality_classification` | Enum | Required | One of: Public, Internal, Confidential, Restricted. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `SUBMITTED_BY` | Startup | Many-to-One | The startup that submitted this document. |
| `PROVIDES_EVIDENCE_FOR` | Any entity | Many-to-Many | Entities whose attributes were populated from this document. |
| `SUPERSEDED_BY` | Document | One-to-One | A newer version of this document that replaces it. |
| `PROCESSED_INTO` | Any entity | Many-to-Many | Entities created or updated as a result of processing this document. |

#### Evidence Sources

- Startup submission portal uploads
- Email attachment processing
- System-generated documents (evaluation reports)
- Agent-generated documents

#### Validation Methods

- `file_format` must match the actual file format detected on upload.
- `is_current_version` must be False for all previous versions when a new version is submitted.
- `processing_status` must follow a valid transition sequence: Received → Processing → Extracted or Failed.

#### Update Rules

- `document_id`, `submission_date`, and `storage_reference` are immutable.
- `processing_status` is updated by the extraction pipeline.
- `is_current_version` is set to False when a superseding document is received.

#### Confidence Tracking

The Document entity itself carries an `extraction_completeness_score` that reflects how thoroughly the document was parsed. This score propagates as a source quality modifier to all entities that reference this document as an evidence source.

#### Versioning

Document entities are versioned through the `SUPERSEDED_BY` relationship chain. The full document version history is preserved and all prior extraction results are maintained, enabling retrospective analysis.

---

### 2.16 Pitch Deck

#### Entity Definition

The Pitch Deck entity is a specialised subtype of the Document entity, extended with additional attributes specific to investor presentation decks. The Pitch Deck is typically the first comprehensive document submitted by a startup and is a rich extraction target for the graph population pipeline. The Pitch Deck entity captures the structural and content characteristics of the deck itself — section coverage, claim types, completeness — as well as the specific claims made within it, which are cross-validated against other graph entities.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `pitch_deck_id` | UUID | Required | Globally unique identifier. |
| `document_id` | UUID | Required | Reference to the parent Document entity. |
| `version_label` | String | Optional | Deck version as labelled by the startup. |
| `total_slides` | Integer | Optional | Total number of slides. |
| `submission_purpose` | Enum | Optional | One of: Initial-Evaluation, Investor-Presentation, Accelerator-Application, Internal-Review. |
| `section_problem_present` | Boolean | Required | Whether a problem statement section is present. |
| `section_solution_present` | Boolean | Required | Whether a solution section is present. |
| `section_market_size_present` | Boolean | Required | Whether a market size section is present. |
| `section_traction_present` | Boolean | Required | Whether a traction/metrics section is present. |
| `section_team_present` | Boolean | Required | Whether a team section is present. |
| `section_financials_present` | Boolean | Required | Whether a financials section is present. |
| `section_ask_present` | Boolean | Required | Whether a funding ask section is present. |
| `claims_extracted_count` | Integer | Optional | Number of verifiable claims extracted from the deck. |
| `claims_verified_count` | Integer | Optional | Number of extracted claims cross-verified against other graph entities. |
| `overall_deck_completeness_score` | Float [0.0–1.0] | Required | Computed score representing coverage of required pitch sections. |
| `narrative_consistency_flag` | Boolean | Optional | Whether the deck's narrative was assessed as internally consistent by the evaluation agent. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `IS_DOCUMENT` | Document | One-to-One | Parent Document entity. |
| `SUBMITTED_BY` | Startup | Many-to-One | The startup that submitted this deck. |
| `CONTAINS_CLAIM_ABOUT` | Any entity | Many-to-Many | Entities whose attributes contain claims made in this deck (for cross-validation). |

#### Evidence Sources

- Startup-submitted presentation file (primary)
- Extraction agent output (section presence, claim extraction)

#### Validation Methods

- `overall_deck_completeness_score` is computed from the sum of `section_*_present` booleans against the expected set.
- `claims_verified_count` must be ≤ `claims_extracted_count`.
- `narrative_consistency_flag` requires that key metrics stated in the deck (revenue, market size, team size) are within 20% of values in corresponding graph entities.

#### Update Rules

When a new pitch deck is submitted, a new Pitch Deck entity is created. The old entity is retained in the graph with `IS_DOCUMENT` linking to the superseded Document entity.

#### Confidence Tracking

Pitch deck claims carry a baseline confidence of 0.45 (founder-authored, marketing-oriented). Cross-verification with independent sources upgrades the confidence of specific attributes to their source-appropriate levels.

#### Versioning

Each deck submission creates a new Pitch Deck entity. Version comparison traversal patterns enable agents to identify which claims changed between deck versions.

---

### 2.17 Research Paper

#### Entity Definition

The Research Paper entity represents a peer-reviewed or pre-print academic publication that is relevant to the startup's technology, market, or team. Research Papers serve two distinct functions in the graph: they provide scientific validation for technology claims (referenced by Technology entities and TRL Records), and they establish the academic credentials of founder and team members (referenced by Founder and Team Member entities). Research papers that directly underpin the startup's core technology are among the highest-confidence evidence sources available.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `paper_id` | UUID | Required | Globally unique identifier. |
| `title` | String | Required | Full title of the paper. |
| `authors` | List<String> | Required | Full names of all authors. |
| `publication_year` | Integer | Required | Year of publication or pre-print submission. |
| `journal_or_venue` | String | Optional | Name of the journal, conference, or pre-print server. |
| `doi` | String | Optional | Digital Object Identifier. |
| `peer_review_status` | Enum | Required | One of: Peer-Reviewed, Under-Review, Pre-Print, Conference-Paper, Working-Paper. |
| `impact_factor` | Float | Optional | Journal impact factor at time of publication. |
| `citation_count` | Integer | Optional | Number of citations as of last known count. |
| `citation_last_updated` | ISO 8601 Date | Optional | Date on which `citation_count` was last retrieved. |
| `relevance_to_startup` | Enum | Required | One of: Core-Technology, Supporting-Technology, Market-Evidence, Team-Credential, Peripheral. |
| `abstract_summary` | String (≤ 1000 chars) | Optional | Plain-language summary of the paper's findings and relevance. |
| `open_access` | Boolean | Optional | Whether the paper is publicly accessible without subscription. |
| `document_id` | UUID | Optional | Reference to a Document entity if a PDF copy has been submitted. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `VALIDATES` | Technology | Many-to-Many | Technologies scientifically validated or described in this paper. |
| `AUTHORED_BY` | Founder | Many-to-Many | Founders who authored this paper. |
| `AUTHORED_BY_MEMBER` | Team Member | Many-to-Many | Team members who authored this paper. |
| `CITED_BY_PATENT` | Patent | Many-to-Many | Patents that cite this paper. |
| `SUPPORTS_TRL_RECORD` | TRL Record | Many-to-Many | TRL assessments for which this paper is supporting evidence. |

#### Evidence Sources

- Academic database lookups by DOI or author name (primary verification)
- Startup-submitted PDFs of papers
- Founder/team member CV (claim of authorship)
- Patent filing citation lists

#### Validation Methods

- `doi` is validated against academic database registries. A valid DOI that resolves correctly receives full confidence on bibliographic attributes.
- `authors` must be cross-checked against Founder and Team Member `full_name` values when `relevance_to_startup` includes Team-Credential.
- `peer_review_status` = Peer-Reviewed must be supported by a confirmed journal of record.

#### Update Rules

- `paper_id`, `doi`, `title`, `authors`, and `publication_year` are immutable.
- `citation_count` is updated periodically (at minimum at each evaluation cycle).
- `relevance_to_startup` may be updated if the startup's technology focus changes.

#### Confidence Tracking

DOI-verified, peer-reviewed paper in high-impact journal = 0.95. Pre-print with DOI = 0.70. Self-reported paper without DOI = 0.45.

#### Versioning

Research Papers are fundamentally immutable records (published papers do not change). `citation_count` updates are tracked as time-series metadata, not as entity versions.

---

### 2.18 Mentor

#### Entity Definition

The Mentor entity represents a formally associated individual who provides guidance, domain expertise, or network access to the startup's founders or team members in an advisory capacity — without being a formal employee, investor, or board member. Mentors are distinguished from advisors (who may hold equity-based advisory roles) by the absence of a financial arrangement. Mentor relationships are significant evaluation signals: credible, domain-relevant mentors indicate that the startup has been vetted by established practitioners and has access to expert guidance.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `mentor_id` | UUID | Required | Globally unique identifier. |
| `full_name` | String | Required | Legal full name of the mentor. |
| `professional_title` | String | Optional | Current or most recent professional title. |
| `current_organisation` | String | Optional | Organisation the mentor is currently affiliated with. |
| `domain_expertise` | List<Enum> | Required | Domains in which this mentor has recognised expertise. |
| `years_experience` | Integer | Optional | Total years of professional experience. |
| `mentoring_since` | ISO 8601 Date | Optional | Date the mentor relationship with this startup commenced. |
| `engagement_frequency` | Enum | Optional | One of: Weekly, Monthly, Quarterly, Ad-Hoc. |
| `association_type` | Enum | Required | One of: Platform-Assigned, Self-Introduced, Programme-Matched, Organic. |
| `notable_achievements` | String (≤ 500 chars) | Optional | Key achievements establishing the mentor's credibility. |
| `conflict_of_interest_declared` | Boolean | Required | Whether any conflict of interest has been declared. |
| `linkedin_profile_url` | URL | Optional | Public LinkedIn for cross-validation. |
| `verification_status` | Enum | Required | One of: Unverified, Self-Reported, Platform-Verified, Publicly-Confirmed. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `MENTORS` | Startup | Many-to-Many | Startups this mentor is associated with. |
| `GUIDES` | Founder | Many-to-Many | Founders specifically guided by this mentor. |
| `GUIDES_MEMBER` | Team Member | Many-to-Many | Team members guided by this mentor. |
| `ASSOCIATED_WITH_PROGRAMME` | Grant | Many-to-Many | Grant programmes or accelerator programmes through which the mentor is associated. |

#### Evidence Sources

- Mentor intake form (structured, primary)
- LinkedIn profile (cross-validation of credentials)
- Platform assignment records (for Platform-Assigned mentors)
- Programme matching records

#### Validation Methods

- `domain_expertise` must overlap with the Startup's `sector_primary` or `sector_secondary` for the relationship to be assessed as relevant.
- `verification_status` = Platform-Verified requires a confirmation record in the platform's mentor registry.
- `conflict_of_interest_declared` is mandatory and must be explicitly set.

#### Update Rules

- `mentor_id` and `full_name` are immutable.
- `engagement_frequency` and `mentoring_since` may be updated.
- The mentor relationship edge is deactivated (with timestamp) rather than deleted when the mentoring relationship ends.

#### Confidence Tracking

Platform-Verified mentor with LinkedIn-confirmed credentials = 0.85. Self-Reported with LinkedIn profile = 0.60. Unverified = 0.35.

#### Versioning

Snapshot versioning for the Mentor entity. The engagement history (start/end dates, engagement frequency changes) is preserved in relationship edge metadata.

---

### 2.19 Evaluation

#### Entity Definition

The Evaluation entity represents a discrete, timestamped evaluation run conducted by the TIDES multi-agent pipeline on a specific startup. Each time the pipeline is triggered — whether for initial assessment, periodic re-evaluation, or event-triggered re-scoring — a new Evaluation entity is created. The Evaluation entity records which agents participated, which subgraphs were assessed, the composite score produced, and the evaluation's inputs and outputs. Evaluation entities are the audit trail of the pipeline's judgments over time.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `evaluation_id` | UUID | Required | Globally unique identifier. Immutable. |
| `startup_id` | UUID | Required | Reference to the evaluated Startup entity. |
| `evaluation_type` | Enum | Required | One of: Initial, Periodic, Event-Triggered, Appeal, Manual-Override. |
| `trigger_event` | String | Optional | Description of the event that triggered this evaluation, if applicable. |
| `evaluation_start_datetime` | ISO 8601 DateTime | Required | Timestamp of evaluation commencement. |
| `evaluation_end_datetime` | ISO 8601 DateTime | Optional | Timestamp of evaluation completion. |
| `graph_version_at_evaluation` | Semantic Version | Required | The SKG version against which this evaluation was conducted. |
| `composite_score` | Float [0.0–100.0] | Optional | Aggregate evaluation score produced by this run. |
| `composite_confidence` | Float [0.0–1.0] | Optional | Confidence in the composite score. |
| `evaluation_status` | Enum | Required | One of: Scheduled, Running, Complete, Failed, Cancelled. |
| `participating_agents` | List<String> | Required | Identifiers of all agents that participated in this evaluation run. |
| `dimensions_evaluated` | List<Enum> | Required | Evaluation dimensions covered (e.g., Technology, Market, Team, Financial, IP). |
| `flags_raised` | Integer | Optional | Number of validation or integrity flags raised during this run. |
| `human_review_required` | Boolean | Required | Whether a human reviewer must review the output of this evaluation. |
| `human_reviewer_id` | UUID | Optional | Identifier of the assigned human reviewer. |
| `review_completion_date` | ISO 8601 Date | Optional | Date human review was completed. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `EVALUATES` | Startup | Many-to-One | The startup being evaluated. |
| `PRODUCES` | Recommendation | One-to-Many | Recommendations produced by this evaluation. |
| `ASSESSES_TRL` | TRL Record | One-to-Many | TRL Records created or updated during this run. |
| `EXAMINES` | Financial Statement | Many-to-Many | Financial statements reviewed during this evaluation. |
| `IDENTIFIES` | Competitor | Many-to-Many | Competitors identified or assessed during this evaluation. |
| `REFERENCES` | Document | Many-to-Many | Documents consulted during this evaluation. |
| `SUPERSEDES` | Evaluation | One-to-One | The prior evaluation that this one replaces or updates. |

#### Evidence Sources

- Agent execution logs
- Graph state at time of evaluation (queried by agents)
- Human reviewer inputs

#### Validation Methods

- `evaluation_end_datetime` must be after `evaluation_start_datetime`.
- `composite_score` requires that all `dimensions_evaluated` have produced sub-scores.
- `human_review_required` must be True for any evaluation producing a `composite_score` below 40 or above 85 (extreme values require human confirmation).

#### Update Rules

- `evaluation_id`, `startup_id`, `evaluation_start_datetime`, and `graph_version_at_evaluation` are immutable.
- `evaluation_status` is updated as the pipeline progresses.
- `composite_score` is written once upon completion; it is immutable thereafter.

#### Confidence Tracking

The Evaluation entity's `composite_confidence` is the propagated confidence from all entity-level confidence scores, weighted by dimension weights as defined in the TIDES Evaluation Model specification.

#### Versioning

Each Evaluation entity is itself an immutable snapshot of a specific pipeline run. The `SUPERSEDES` chain provides the version history of evaluations over the startup's lifecycle.

---

### 2.20 Recommendation

#### Entity Definition

The Recommendation entity represents a structured, actionable output produced by the TIDES evaluation pipeline at the conclusion of or during an evaluation run. Recommendations are directed at specific audiences — funding committees, incubator programme managers, human reviewers — and contain a disposition (Approve, Reject, Conditional, Escalate), a rationale, and a confidence score. Recommendations are the primary decision-support outputs of the pipeline and must be fully traceable to the evaluation and graph state that produced them.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `recommendation_id` | UUID | Required | Globally unique identifier. Immutable. |
| `evaluation_id` | UUID | Required | Reference to the Evaluation that produced this recommendation. |
| `recommendation_type` | Enum | Required | One of: Funding-Decision, Programme-Admission, Stage-Advancement, Further-Due-Diligence, Rejection, Conditional-Approval. |
| `disposition` | Enum | Required | One of: Approve, Reject, Conditional, Escalate-to-Human, Defer. |
| `confidence_score` | Float [0.0–1.0] | Required | Confidence in this recommendation. |
| `primary_rationale` | String (≤ 2000 chars) | Required | Evidence-based rationale for the disposition. |
| `supporting_signals` | List<String> | Optional | Key positive signals that contributed to the recommendation. |
| `risk_signals` | List<String> | Optional | Key risk signals or concerns that moderated the recommendation. |
| `conditions` | String (≤ 1000 chars) | Optional | Conditions attached to a Conditional-Approval disposition. |
| `dimension_scores` | Map<Enum, Float> | Optional | Sub-scores by evaluation dimension that contributed to the overall recommendation. |
| `target_audience` | Enum | Required | One of: Funding-Committee, Programme-Manager, Human-Reviewer, Startup-Team. |
| `created_datetime` | ISO 8601 DateTime | Required | Timestamp of creation. Immutable. |
| `expiry_datetime` | ISO 8601 DateTime | Optional | Date after which this recommendation is considered stale and requires re-evaluation. |
| `actioned` | Boolean | Required | Whether this recommendation has been acted upon. |
| `action_taken` | String | Optional | Description of the action taken in response to this recommendation. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `PRODUCED_BY` | Evaluation | Many-to-One | The evaluation run that produced this recommendation. |
| `TARGETS` | Startup | Many-to-One | The startup this recommendation concerns. |
| `ADDRESSES_RISK` | Risk Record | Many-to-Many | Risk Records that this recommendation explicitly addresses. |
| `CITES_MILESTONE` | Milestone | Many-to-Many | Milestones cited as evidence or conditions. |

#### Evidence Sources

- Evaluation agent synthesis outputs
- Composite scoring model outputs
- Human reviewer override inputs (for Escalate-to-Human cases)

#### Validation Methods

- `confidence_score` must be consistent with `disposition`: a disposition of Approve with `confidence_score` < 0.60 generates a mandatory human review flag.
- `conditions` is mandatory when `disposition` = Conditional.
- `expiry_datetime` must be after `created_datetime`.

#### Update Rules

- Recommendation entities are immutable once created. Revised recommendations create new entities.
- `actioned` is updated when a human actor records the action taken.

#### Confidence Tracking

The Recommendation entity's `confidence_score` is the propagated and weighted confidence from the Evaluation entity, further modulated by the number and severity of flags raised during the evaluation run.

#### Versioning

Each recommendation is a discrete, immutable record. The history of recommendations for a startup (across all Evaluation runs) constitutes the longitudinal decision record for that startup.

---

### 2.21 Milestone

#### Entity Definition

The Milestone entity represents a specific, defined achievement or target that the startup has set, committed to (in a grant or investment agreement), or been assigned by the evaluation pipeline. Milestones may be product milestones (first working prototype), commercial milestones (first paying customer), regulatory milestones (clinical trial approval), or financial milestones (specific revenue targets). The Milestone entity tracks both the target and the actual outcome, enabling the pipeline to assess the startup's execution track record.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `milestone_id` | UUID | Required | Globally unique identifier. |
| `milestone_name` | String | Required | Descriptive name of the milestone. |
| `milestone_type` | Enum | Required | One of: Product, Commercial, Regulatory, Financial, Team, IP, ESG, Operational. |
| `description` | String (≤ 500 chars) | Required | Description of what achieving this milestone entails. |
| `target_date` | ISO 8601 Date | Required | Date by which this milestone was targeted to be achieved. |
| `actual_completion_date` | ISO 8601 Date | Optional | Date on which this milestone was actually achieved. |
| `status` | Enum | Required | One of: Planned, In-Progress, Achieved, Missed, Deferred, Cancelled. |
| `importance_level` | Enum | Required | One of: Critical, High, Medium, Low. |
| `success_criteria` | String (≤ 500 chars) | Required | Measurable criteria that define achievement of this milestone. |
| `verified_by` | Enum | Optional | One of: Self-Reported, Document-Supported, Third-Party-Verified, Agent-Assessed. |
| `delay_days` | Integer | Optional | Number of days by which achievement was delayed (if applicable). |
| `linked_grant_id` | UUID | Optional | Grant for which this milestone is a disbursement condition. |
| `linked_investment_id` | UUID | Optional | Investment for which this milestone is a tranche condition. |
| `outcome_description` | String (≤ 500 chars) | Optional | Description of the actual outcome, if different from expected. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `BELONGS_TO` | Startup | Many-to-One | The startup this milestone belongs to. |
| `PART_OF` | Roadmap | Many-to-One | The roadmap that includes this milestone. |
| `CONDITIONS` | Grant | Many-to-One | Grant disbursement conditioned on this milestone. |
| `REFERENCED_IN` | Recommendation | Many-to-Many | Recommendations that cite this milestone. |
| `DOCUMENTED_BY` | Document | Many-to-Many | Supporting documents evidencing achievement. |

#### Evidence Sources

- Roadmap documents (target dates, descriptions)
- Grant agreements (milestone conditions)
- Investment term sheets
- Agent-assessed milestone completion
- Third-party verification reports

#### Validation Methods

- `actual_completion_date` must not precede `target_date` by more than 3 years (extreme historical back-dating generates a validation flag).
- `status` = Achieved requires either a supporting document or `verified_by` ≠ Self-Reported.
- `delay_days` must equal `actual_completion_date` − `target_date` in calendar days, when both dates are populated.

#### Update Rules

- `milestone_id`, `milestone_name`, and `target_date` are immutable once committed (though `target_date` may be updated with explicit Deferred status and version record).
- `status` progresses along defined lifecycle paths and is versioned at each transition.

#### Confidence Tracking

Self-Reported achievement = 0.50. Document-Supported = 0.75. Third-Party-Verified = 0.90.

#### Versioning

Snapshot versioning at each status transition. The full history of status changes is preserved to enable assessment of the startup's execution discipline over time.

---

### 2.22 Risk Record

#### Entity Definition

The Risk Record entity represents a specific, identified risk factor that affects the startup's likelihood of success, viability, or compliance. Risk Records may be identified by evaluation agents, human reviewers, or derived from validation failures in other entities. Each Risk Record is typed by category (technology risk, market risk, regulatory risk, team risk, financial risk, etc.), assigned a severity and likelihood score, and linked to the entity or entities from which it was derived. Risk Records collectively form the startup's risk profile and are a key input to the Recommendation entity.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `risk_record_id` | UUID | Required | Globally unique identifier. |
| `risk_category` | Enum | Required | One of: Technology, Market, Financial, Team, Regulatory, IP, ESG, Operational, Reputational, Geopolitical. |
| `risk_title` | String | Required | Concise title of the risk. |
| `risk_description` | String (≤ 1000 chars) | Required | Detailed description of the risk, its nature, and its potential impact. |
| `severity` | Enum | Required | One of: Critical, High, Medium, Low. |
| `likelihood` | Enum | Required | One of: Near-Certain, Likely, Possible, Unlikely, Rare. |
| `risk_score` | Float [0.0–10.0] | Required | Numerical risk score (combination of severity and likelihood). |
| `identified_by` | Enum | Required | One of: Evaluation-Agent, Human-Reviewer, Integrity-Check, Document-Analysis. |
| `identified_date` | ISO 8601 DateTime | Required | Timestamp when the risk was identified. |
| `source_entity_id` | UUID | Optional | The entity from which this risk was derived. |
| `source_entity_type` | String | Optional | The entity type of `source_entity_id`. |
| `mitigation_status` | Enum | Required | One of: Unaddressed, In-Mitigation, Mitigated, Accepted, Transferred. |
| `mitigation_description` | String (≤ 500 chars) | Optional | Description of the mitigation actions being taken or planned. |
| `mitigation_deadline` | ISO 8601 Date | Optional | Target date for mitigation. |
| `residual_risk_score` | Float [0.0–10.0] | Optional | Expected risk score after mitigation measures are applied. |
| `is_blocking` | Boolean | Required | Whether this risk is assessed as blocking the startup's progress or a positive recommendation. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `AFFECTS` | Startup | Many-to-One | The startup to which this risk applies. |
| `DERIVED_FROM` | Any entity | Many-to-One | The specific entity that gave rise to this risk identification. |
| `ADDRESSED_IN` | Recommendation | Many-to-Many | Recommendations that address this risk. |
| `TRACKED_IN` | Roadmap | Many-to-Many | Roadmap items that are expected to reduce this risk. |

#### Evidence Sources

- Evaluation agent risk assessment outputs
- Human reviewer inputs
- Integrity check failures (automatically escalated as risk records)
- Market analysis outputs (market risks)
- Financial analysis outputs (financial risks)

#### Validation Methods

- `risk_score` must be derivable from `severity` and `likelihood` using the TIDES Risk Scoring Matrix (defined in TAES Appendix B).
- `is_blocking` = True for any risk with `severity` = Critical and `likelihood` = Near-Certain or Likely.
- `mitigation_description` is mandatory when `mitigation_status` = In-Mitigation or Mitigated.

#### Update Rules

- `risk_record_id`, `risk_title`, `risk_category`, and `identified_date` are immutable.
- `mitigation_status`, `mitigation_description`, and `residual_risk_score` are updated as mitigation actions progress.
- Risk Records are closed (status = Mitigated or Accepted) but never deleted. Historical risk records are preserved for audit.

#### Confidence Tracking

Agent-identified risks carry the confidence of the underlying agent assessment. Human-reviewer-identified risks carry confidence 0.90. Integrity-check-derived risks (mathematical or logical inconsistencies) carry confidence 0.95.

#### Versioning

Snapshot versioning at each status transition, providing the full risk lifecycle history.

---

### 2.23 Roadmap

#### Entity Definition

The Roadmap entity represents the startup's forward-looking strategic and operational plan — the structured sequence of goals, milestones, and resource commitments that define how the startup intends to progress from its current state to its target state over a defined planning horizon. The Roadmap entity is a parent container that organises Milestone entities into a coherent temporal and strategic sequence. It captures both the planning horizon and the strategic objectives that milestones are designed to achieve. The Roadmap is evaluated for realism, internal consistency, and alignment with the startup's resources and market conditions.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `roadmap_id` | UUID | Required | Globally unique identifier. |
| `roadmap_version` | String | Required | Version label of the roadmap (e.g., "2025-Q1-v2"). |
| `planning_horizon_months` | Integer | Required | Duration covered by this roadmap in months. |
| `roadmap_start_date` | ISO 8601 Date | Required | Start date of the planning horizon. |
| `roadmap_end_date` | ISO 8601 Date | Required | End date of the planning horizon. |
| `strategic_objectives` | List<String> | Required | High-level strategic objectives this roadmap is designed to achieve. |
| `total_milestones` | Integer | Required | Total number of milestones included in this roadmap. |
| `milestones_achieved` | Integer | Optional | Count of milestones achieved as of the last update. |
| `milestones_at_risk` | Integer | Optional | Count of milestones assessed as at-risk based on current trajectory. |
| `resource_plan_included` | Boolean | Required | Whether a resource plan (budget, headcount) is associated with this roadmap. |
| `funding_dependency` | Boolean | Required | Whether milestone achievement is dependent on future funding being secured. |
| `risk_adjusted` | Boolean | Required | Whether risk adjustments have been applied to milestone timelines. |
| `realism_score` | Float [0.0–1.0] | Optional | Agent-assessed score of roadmap realism based on resource constraints and historical execution data. |
| `last_reviewed_date` | ISO 8601 Date | Optional | Date of the most recent formal review of this roadmap. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `BELONGS_TO` | Startup | One-to-One | The startup this roadmap is for. |
| `CONTAINS` | Milestone | One-to-Many | All milestones included in this roadmap. |
| `DOCUMENTED_BY` | Document | Many-to-Many | Documents from which this roadmap was extracted or that describe it. |
| `ASSESSED_IN` | Evaluation | Many-to-Many | Evaluation runs that assessed this roadmap. |

#### Evidence Sources

- Roadmap document submitted by startup
- Pitch deck roadmap section
- Grant application milestones
- Investment term sheet milestone conditions

#### Validation Methods

- `roadmap_end_date` must be after `roadmap_start_date`.
- `total_milestones` must equal the count of Milestone entities linked to this roadmap.
- `milestones_achieved` + `milestones_at_risk` must not exceed `total_milestones`.
- `funding_dependency` = True combined with no confirmed future funding in linked Investor entities generates a risk flag.

#### Update Rules

- A new Roadmap entity is created for each roadmap version. Prior versions are retained in the graph.
- `milestones_achieved` and `milestones_at_risk` are updated at each evaluation cycle.

#### Confidence Tracking

Roadmap realism scores are agent-assessed and carry the confidence of the assessment agent. Roadmaps with `funding_dependency` = True and no confirmed funding receive a realism score penalty.

#### Versioning

Each roadmap version is a discrete Roadmap entity. The `BELONGS_TO` relationship to the Startup always points to the most current Roadmap entity; prior roadmap entities are retained in the graph with their superseded status noted.

---

### 2.24 ESG Record

#### Entity Definition

The ESG Record entity captures a structured assessment of the startup's environmental, social, and governance practices, commitments, and performance. As ESG compliance increasingly determines eligibility for government grants, institutional investment, and public-sector procurement, the ESG Record is a prerequisite entity for startups evaluated under the TIDES framework's full-standard pathway. ESG Records are assessed across three dimensions — Environmental, Social, and Governance — and produce both qualitative and quantitative outputs.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `esg_record_id` | UUID | Required | Globally unique identifier. |
| `assessment_date` | ISO 8601 Date | Required | Date this ESG assessment was conducted. |
| `assessment_type` | Enum | Required | One of: Self-Assessment, Internal-Review, Third-Party-Certified, Regulatory-Mandated. |
| `environmental_score` | Float [0.0–100.0] | Optional | Score on the environmental dimension. |
| `social_score` | Float [0.0–100.0] | Optional | Score on the social dimension. |
| `governance_score` | Float [0.0–100.0] | Optional | Score on the governance dimension. |
| `composite_esg_score` | Float [0.0–100.0] | Optional | Composite ESG score. |
| `carbon_footprint_tco2e` | Float | Optional | Estimated annual carbon footprint in tonnes CO₂ equivalent. |
| `carbon_reduction_target` | Boolean | Optional | Whether a formal carbon reduction target has been committed to. |
| `diversity_gender_percent_female` | Float | Optional | Percentage of workforce identifying as female. |
| `diversity_leadership_female_percent` | Float | Optional | Percentage of leadership roles held by women. |
| `board_independence_percent` | Float | Optional | Percentage of board members who are independent. |
| `whistleblower_policy` | Boolean | Required | Whether a formal whistleblower policy is in place. |
| `data_privacy_policy` | Boolean | Required | Whether a formal data privacy policy is in place. |
| `anti_corruption_policy` | Boolean | Required | Whether a formal anti-corruption policy is in place. |
| `esg_framework_applied` | String | Optional | Named ESG framework applied (e.g., GRI, SASB, UN SDG alignment). |
| `certifying_body` | String | Optional | Organisation that certified this assessment, if third-party certified. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `BELONGS_TO` | Startup | Many-to-One | The startup this ESG record describes. |
| `DOCUMENTED_BY` | Document | Many-to-Many | ESG reports and certification documents. |
| `ASSESSED_IN` | Evaluation | Many-to-Many | Evaluation runs that reviewed this ESG record. |

#### Evidence Sources

- ESG self-assessment form (structured)
- Third-party ESG certification reports
- Annual sustainability reports
- Governance policy documents

#### Validation Methods

- `composite_esg_score` must be the weighted average of the three dimension scores (equal weighting by default).
- `assessment_type` = Third-Party-Certified requires `certifying_body` to be populated.
- Policy booleans (`whistleblower_policy`, `data_privacy_policy`, `anti_corruption_policy`) require linked Document entities for verification.

#### Update Rules

- ESG Records are not modified; new assessments create new ESG Record entities.
- The most current ESG Record is identified by the most recent `assessment_date`.

#### Confidence Tracking

Third-Party-Certified = 0.90. Internal-Review = 0.70. Self-Assessment = 0.50.

#### Versioning

Each ESG Record is a discrete assessment snapshot. The time-series of ESG Records for a startup enables trend analysis of ESG performance over time.

---

### 2.25 IP Portfolio

#### Entity Definition

The IP Portfolio entity is an aggregate container that represents the entirety of a startup's intellectual property holdings. While individual Patent entities capture granular patent-level details, the IP Portfolio entity provides a consolidated, high-level view of the startup's IP position across all IP types — patents, trademarks, copyrights, trade secrets, and know-how. The IP Portfolio entity is the primary node for assessments of the startup's IP moat: the degree to which its intellectual property creates durable competitive barriers. There is exactly one IP Portfolio entity per Startup entity.

#### Attributes

| Attribute Name | Data Type | Required | Description |
|---|---|---|---|
| `ip_portfolio_id` | UUID | Required | Globally unique identifier. |
| `total_patents_filed` | Integer | Required | Total number of patents filed (all statuses). |
| `total_patents_granted` | Integer | Required | Total number of granted, active patents. |
| `total_trademarks` | Integer | Optional | Number of registered trademarks. |
| `total_copyrights` | Integer | Optional | Number of registered copyrights. |
| `trade_secrets_declared` | Boolean | Required | Whether the startup has declared the existence of trade secrets. |
| `trade_secret_description` | String (≤ 500 chars) | Optional | Generalised description of trade secrets (without disclosing protected information). |
| `ip_jurisdiction_coverage` | List<String> | Required | Countries or regions in which IP protection exists. |
| `ip_strategy_documented` | Boolean | Required | Whether a formal IP strategy document exists. |
| `licensing_revenue_generated` | Boolean | Optional | Whether any licensing revenue has been generated from this IP portfolio. |
| `freedom_to_operate_assessed` | Boolean | Required | Whether a freedom-to-operate analysis has been conducted. |
| `fto_outcome` | Enum | Optional | One of: Clear, Conditional, At-Risk, Not-Assessed. |
| `ip_moat_assessment_score` | Float [0.0–1.0] | Optional | Agent-assessed score of the strength of the IP moat. |
| `last_ip_audit_date` | ISO 8601 Date | Optional | Date of the most recent comprehensive IP audit. |
| `ip_attorney_engaged` | Boolean | Required | Whether a qualified IP attorney is engaged. |

#### Relationships

| Relationship Label | Target Entity | Cardinality | Business Meaning |
|---|---|---|---|
| `BELONGS_TO` | Startup | One-to-One | The startup this portfolio belongs to. |
| `CONTAINS` | Patent | One-to-Many | All patent entities in this portfolio. |
| `PROTECTS` | Technology | Many-to-Many | Technologies protected by this portfolio's combined IP. |
| `ASSESSED_IN` | Evaluation | Many-to-Many | Evaluations that assessed this portfolio. |
| `CONTESTED_BY` | Competitor | Many-to-Many | Competitors with overlapping or challenging IP positions. |

#### Evidence Sources

- Patent office database records (for `total_patents_filed`, `total_patents_granted`)
- IP attorney reports (freedom-to-operate, IP strategy)
- Trademark registry records
- Startup IP audit documentation

#### Validation Methods

- `total_patents_granted` must be ≤ `total_patents_filed`.
- `total_patents_granted` must match the count of linked Patent entities with `status` = Granted.
- `fto_outcome` is mandatory when `freedom_to_operate_assessed` = True.
- `ip_moat_assessment_score` must be produced by an authorised evaluation agent, not self-reported.

#### Update Rules

- `ip_portfolio_id` is immutable.
- Patent counts are updated automatically when Patent entity statuses change.
- `ip_moat_assessment_score` is updated at each evaluation cycle.

#### Confidence Tracking

The IP Portfolio entity's confidence is a composite of the confidence scores of all linked Patent entities and the quality of the IP attorney engagement. `ip_attorney_engaged` = True contributes a +0.08 confidence bonus to the entity-level score.

#### Versioning

Snapshot versioning at each evaluation cycle. The time-series of IP Portfolio snapshots enables trend analysis of IP portfolio growth and diversification.

---

## 3. Graph Traversal Patterns

Graph traversal patterns are named, parameterised paths through the SKG that AI agents use to answer specific evaluation questions. Each pattern is defined by a start node, a sequence of edge traversals with direction and label, and the insights revealed at the terminal node or set of nodes. Agents invoke traversal patterns by name, supplying the startup identifier as the root parameter.

---

### 3.1 Founder Credibility Path

**Start Node:** Startup  
**Traversal Steps:**
1. Startup → `FOUNDED_BY` → Founder (all founders)
2. Founder → `PREVIOUSLY_FOUNDED` → Prior Venture nodes
3. Founder → `HOLDS_PATENT` → Patent nodes
4. Founder → `AUTHORED` → Research Paper nodes
5. Founder → `ASSOCIATED_WITH` → Investor nodes (prior backers)

**What It Reveals:** The aggregate credibility of the founding team across five dimensions: prior entrepreneurial experience (depth and success rate of prior ventures), technical output (patents held), academic contribution (peer-reviewed publications), and investor confidence (whether credible investors have previously backed these founders in prior ventures). The pattern produces a structured credibility profile for each founder and a team-level credibility aggregate.

**Evaluation Use:** Used by the Founder Assessment Agent at the start of every evaluation run. The credibility profile is a primary input to the composite evaluation score.

---

### 3.2 Revenue Validation Path

**Start Node:** Startup  
**Traversal Steps:**
1. Startup → `HAS_FINANCIAL_STATEMENT` → Financial Statement nodes (all periods)
2. Financial Statement → `CONTAINS` → Revenue Record nodes
3. Revenue Record → `DOCUMENTED_IN` → Document nodes (supporting evidence)
4. Revenue Record → `ATTRIBUTED_TO_PRODUCT` → Product nodes
5. Product → `TARGETS` → Customer Segment nodes
6. Customer Segment → `GENERATES` → Revenue Record nodes (cross-check)

**What It Reveals:** The complete, evidence-backed revenue picture of the startup — which products and segments are generating revenue, whether that revenue is documented by supporting evidence, and whether the segment-level revenue attribution is internally consistent with the product-level attribution. This traversal identifies self-reported revenue without supporting documentation, revenue concentration risks (all revenue from one segment), and inconsistencies between financial statement totals and granular Revenue Records.

**Evaluation Use:** Used by the Financial Analysis Agent to validate revenue claims before producing any financial assessment output.

---

### 3.3 IP Moat Assessment Path

**Start Node:** Startup  
**Traversal Steps:**
1. Startup → `HAS_IP_PORTFOLIO` → IP Portfolio
2. IP Portfolio → `CONTAINS` → Patent nodes (Granted only)
3. Patent → `PROTECTS` → Technology nodes
4. Technology → `CONTESTED_BY` → Competitor nodes
5. Competitor → `USES_TECHNOLOGY` → Technology nodes (competitor's tech)
6. Technology → back-check → whether protected by Startup's Patents

**What It Reveals:** The degree to which the startup's granted patents protect technologies that competitors are actively using or developing. A strong moat is indicated when: (a) the startup holds granted patents, (b) those patents cover technologies in the competitor's core stack, and (c) the competitor does not hold overlapping patents that challenge the startup's claims. A weak moat is indicated when patent claims do not cover technologies that competitors are using, or when competitors hold overlapping patents.

**Evaluation Use:** Used by the IP Analysis Agent to produce the `ip_moat_assessment_score` for the IP Portfolio entity.

---

### 3.4 Market Entry Viability Path

**Start Node:** Startup  
**Traversal Steps:**
1. Startup → `OPERATES_IN` → Market nodes
2. Market → `CONTAINS` → Customer Segment nodes
3. Customer Segment → `GENERATES` → Revenue Record nodes (check for existing revenue)
4. Market → `OCCUPIED_BY` → Competitor nodes
5. Competitor → `COMPETES_IN` → Market (confirm overlap)
6. Market → `GOVERNED_BY_REGULATION` → Document nodes (regulatory documents)

**What It Reveals:** Whether the startup has a credible, evidence-backed path into its target markets. The traversal reveals market size, existing revenue in those markets, the intensity of competition, and the regulatory complexity of market entry. Gaps in Customer Segment → Revenue Record traversal (no revenue yet in a target market) combined with High competitive intensity and High regulatory complexity generate compound market entry risk flags.

**Evaluation Use:** Used by the Market Analysis Agent to assess go-to-market credibility.

---

### 3.5 Technology Validation Path

**Start Node:** Startup  
**Traversal Steps:**
1. Startup → `USES_TECHNOLOGY` → Technology nodes (core technologies only: `is_core_technology` = True)
2. Technology → `HAS_TRL_RECORD` → TRL Record nodes (current records only)
3. TRL Record → `SUPPORTED_BY` → Document nodes
4. Technology → `REFERENCED_IN` → Research Paper nodes
5. Technology → `EMBODIED_IN` → Product nodes (check if technology is embodied in a launched product)

**What It Reveals:** The validated maturity of each core technology and the quality of the evidence supporting that maturity claim. A technology with TRL 7+ that is supported by accredited body assessment, referenced in peer-reviewed papers, and embodied in a launched product presents a high-confidence technology readiness picture. A technology with TRL 3–4, self-assessed only, with no linked research papers or products is a low-confidence, high-risk technology position.

**Evaluation Use:** Used by the Technology Readiness Agent to produce TRL-based scoring.

---

### 3.6 Funding History and Investor Quality Path

**Start Node:** Startup  
**Traversal Steps:**
1. Startup → `HAS_INVESTOR` → Investor nodes (all rounds)
2. Investor → `VERIFIED_BY` → Document nodes (investment agreements)
3. Investor → `LED_ROUND` → Startup (confirm lead role)
4. Founder → `ASSOCIATED_WITH` → Investor nodes (prior investor relationships)

**What It Reveals:** The completeness and quality of the startup's funding history, the credibility of investors (type, sector expertise, portfolio size, follow-on capacity), and whether investors have pre-existing relationships with the founding team (warm relationships vs. arm's-length cold investments). Unverified investor records, self-reported round sizes without linked agreements, and investors with no domain expertise in the startup's sector all generate funding quality warnings.

**Evaluation Use:** Used by the Financial Analysis Agent and the Investor Due Diligence traversal at pre-investment evaluation stages.

---

### 3.7 Execution Track Record Path

**Start Node:** Startup  
**Traversal Steps:**
1. Startup → `HAS_MILESTONE` → Milestone nodes (all, ordered by `target_date`)
2. Milestone → compute: `actual_completion_date` vs `target_date` → `delay_days`
3. Milestone → `DOCUMENTED_BY` → Document nodes (verify achieved milestones)
4. Startup → `HAS_ROADMAP` → Roadmap → `CONTAINS` → Milestone nodes (current plan)
5. Roadmap → check `realism_score` attribute

**What It Reveals:** The startup's historical execution discipline — did it achieve milestones on time, with what frequency of delays, and how large were those delays? This traversal produces an execution reliability score that is a key predictor of future milestone achievement. It also compares the historical track record against the current roadmap's realism score to identify whether the startup's forward plan accounts for its historical execution patterns.

**Evaluation Use:** Used by the Milestone and Execution Agent and as a moderating factor in roadmap-dependent recommendation confidence.

---

### 3.8 Risk Aggregation Path

**Start Node:** Startup  
**Traversal Steps:**
1. Startup → `HAS_RISK_RECORD` → Risk Record nodes (all, unresolved)
2. Risk Record → filter by `is_blocking` = True
3. Risk Record → filter by `severity` = Critical
4. Risk Record → `DERIVED_FROM` → source entity (identify root cause entity type)
5. Risk Record → `ADDRESSED_IN` → Recommendation nodes (check if addressed)

**What It Reveals:** The complete risk landscape of the startup, stratified by severity and blocking status. The traversal identifies which risk categories dominate (technology, financial, team, etc.), which risks have been addressed in prior recommendations, and which blocking risks remain unresolved. The distribution of risk categories and severities is the primary input to the overall risk assessment dimension of the composite evaluation score.

**Evaluation Use:** Used by the Risk Assessment Agent at every evaluation run.

---

### 3.9 ESG and Compliance Verification Path

**Start Node:** Startup  
**Traversal Steps:**
1. Startup → `HAS_ESG_RECORD` → ESG Record nodes (most recent)
2. ESG Record → `DOCUMENTED_BY` → Document nodes (policy documents)
3. ESG Record → check `assessment_type` (was it self-assessed or third-party certified?)
4. Startup → `HAS_GRANT` → Grant nodes → check grant-specific ESG requirements
5. Startup → `HAS_INVESTOR` → Investor nodes → check investor ESG mandates (where captured)

**What It Reveals:** Whether the startup has substantive ESG practices or merely declaratory ones, the verification quality of those practices, and whether there is alignment between the ESG record and the ESG requirements of the startup's investors and grant providers. Misalignment between investor ESG mandates and actual ESG scores generates a compliance risk flag.

**Evaluation Use:** Used by the ESG Compliance Agent and factored into grant eligibility assessments.

---

### 3.10 Competitive Positioning and Differentiation Path

**Start Node:** Startup  
**Traversal Steps:**
1. Startup → `HAS_PRODUCT` → Product nodes
2. Product → `INCORPORATES` → Technology nodes
3. Technology → `CONTESTED_BY` → Competitor nodes
4. Competitor → `USES_TECHNOLOGY` → Technology nodes (competitor tech stack)
5. Startup's Technology → `PROTECTED_BY` → Patent nodes (defensive layer)
6. Competitor → `HOLDS_PATENT` → Patent nodes (offensive threat layer)

**What It Reveals:** The granular competitive differentiation position of the startup at the technology level. This traversal maps the overlap between the startup's technology stack and those of its competitors, identifies which of the startup's core technologies face direct competition, and assesses the degree to which patents (on both sides) create or erode competitive differentiation. The output is a differentiation map: which technology dimensions are strongly differentiated (protected, no competitor overlap), moderately differentiated, or parity/undifferentiated.

**Evaluation Use:** Used by the Competitive Analysis Agent to produce the competitive moat section of the evaluation report.

---

## 4. Confidence Propagation

Confidence in the TIDES SKG operates as a multi-level system: attribute-level confidence propagates to entity-level confidence, and entity-level confidence propagates to graph-level and evaluation-level confidence.

### 4.1 Attribute-Level Confidence

Every attribute in every entity carries a confidence score in the range [0.0, 1.0]. This score is assigned at the time of population and may be updated when:
- A new corroborating source is added (score increases)
- A contradicting value is discovered (score decreases, conflict flag raised)
- The value's age exceeds the freshness threshold defined for that attribute type (score decays)
- An extraction error is identified (score decreases)
- A human reviewer confirms the value (score increases to its verified ceiling)

The formula for attribute-level confidence is:

`C_attr = C_source × C_corroboration × C_freshness × C_consistency`

Where:
- `C_source` ∈ [0.0, 1.0]: Source quality score (self-reported=0.50, audited=0.95, etc.)
- `C_corroboration` ∈ [1.0, 1.15]: Multiplier based on number of independent corroborating sources (1 source = 1.0, 2 sources = 1.05, 3+ sources = 1.10, human-confirmed = 1.15), capped at 1.0 after applying to base.
- `C_freshness` ∈ [0.50, 1.0]: Decay function based on attribute age relative to its defined freshness window.
- `C_consistency` ∈ [0.70, 1.0]: Consistency of this value with logically related attributes in the same entity or linked entities.

### 4.2 Entity-Level Confidence

Entity-level confidence is the weighted average of attribute-level confidence scores across all required attributes that have been populated. The weight of each attribute is defined in the TIDES Confidence Weight Table (Appendix A of the Evaluation Model specification).

`C_entity = Σ(w_i × C_attr_i) / Σ(w_i)` for all populated required attributes i.

Required attributes that are not populated do not contribute to the numerator but their weights remain in the denominator, producing a penalty for incompleteness. Optional attributes that are populated contribute at half weight.

An entity may not receive a `C_entity` > 0.90 unless all required attributes are populated and at least two of them are corroborated by independent sources.

### 4.3 Evaluation Dimension Confidence

Each evaluation dimension (Technology, Market, Financial, Team, IP, ESG, Execution) aggregates the entity-level confidence scores of all entities relevant to that dimension. The dimension confidence is:

`C_dimension = Σ(entity_weight_d × C_entity) / Σ(entity_weight_d)`

Entity weights within each dimension are defined in the TIDES Evaluation Model specification by the relative importance of that entity type to the dimension's assessment.

### 4.4 Composite Evaluation Confidence

The composite evaluation confidence is:

`C_composite = Σ(dimension_weight × C_dimension) / Σ(dimension_weight)`

Dimension weights are defined in the TIDES Scoring Model and differ by evaluation stage (early-stage evaluations weight Team and Technology more heavily; growth-stage evaluations weight Financial and Market more heavily).

### 4.5 Confidence Floors and Ceilings

| Condition | Confidence Effect |
|---|---|
| Any required attribute unpopulated | Entity confidence capped at 0.75 |
| Any blocking risk record unresolved | Composite confidence capped at 0.70 |
| No audited financial statements (post-Seed stage) | Financial dimension confidence capped at 0.65 |
| Self-assessment only for TRL (core technology) | Technology dimension confidence capped at 0.60 |
| Human reviewer override (positive) | Ceiling raised by 0.05 |
| Integrity check failure (unresolved) | Composite confidence reduced by 0.10 per failure |

### 4.6 Confidence Decay

Time-sensitive attributes are subject to confidence decay at rates defined per attribute type:

| Attribute Type | Decay Threshold | Decay Rate |
|---|---|---|
| Market sizing figures | 24 months | −0.05 per 6 months beyond threshold |
| Revenue records | 18 months | −0.03 per 3 months beyond threshold |
| Competitor data | 12 months | −0.04 per 3 months beyond threshold |
| TRL assessments | 18 months | −0.04 per 6 months beyond threshold |
| Team attributes | 24 months | −0.02 per 6 months beyond threshold |
| ESG records | 12 months | −0.05 per 6 months beyond threshold |

Decayed confidence scores do not become negative; the floor is 0.10 for any populated attribute.

---

## 5. Graph Integrity Rules

Graph integrity rules are formal constraints that must be satisfied at all times. Any write to the graph that would violate an integrity rule is rejected with an error, and the attempted change is logged as an integrity violation. Unresolved integrity violations block the production of Evaluation outputs.

### 5.1 Mandatory Existence Constraints

| Rule ID | Constraint | Violation Consequence |
|---|---|---|
| IR-001 | A Startup entity must have at least one linked Founder via `FOUNDED_BY`. | Evaluation blocked. Integrity error. |
| IR-002 | A TRL Record must be linked to exactly one Technology entity via `ASSESSES`. | Write rejected. |
| IR-003 | An IP Portfolio must be linked to exactly one Startup via `BELONGS_TO`. | Write rejected. |
| IR-004 | A Recommendation must be linked to exactly one Evaluation via `PRODUCED_BY`. | Write rejected. |
| IR-005 | A Roadmap must be linked to exactly one Startup. Multiple current Roadmaps per Startup are prohibited. | Write rejected. |
| IR-006 | A Revenue Record must reference a valid `period_start` and `period_end`. | Write rejected. |
| IR-007 | Every Evaluation must have at least one linked Recommendation upon completion. | Evaluation flagged as incomplete. |

### 5.2 Cardinality Constraints

| Rule ID | Constraint | Violation Consequence |
|---|---|---|
| IR-010 | Each Startup may have at most one IP Portfolio entity. | Duplicate write rejected. |
| IR-011 | Each Startup may have at most one current Roadmap entity. | Second current Roadmap write rejected unless prior is versioned out. |
| IR-012 | Each TRL Record may be `is_current` = True for at most one record per Technology at any time. | Second True write rejected. |
| IR-013 | Each Document may have at most one `SUPERSEDED_BY` edge at any time. | Second supersession write rejected. |

### 5.3 Referential Integrity Constraints

| Rule ID | Constraint | Violation Consequence |
|---|---|---|
| IR-020 | All UUID references in attributes (e.g., `attributed_product_id`, `attributed_segment_id`) must resolve to an existing entity of the correct type. | Write rejected. |
| IR-021 | A Patent entity's `assignee_name` must match the Startup's `legal_name` or a legally documented variant thereof. | Integrity flag raised. Manual review required. |
| IR-022 | A Financial Statement's `period_start` must not overlap with another Financial Statement of the same `period_type` for the same Startup. | Write rejected. |
| IR-023 | An Investor's `equity_stake_percent` must not cause total equity across all Investors and Founders to exceed 100.0%. | Write rejected with conflict report. |

### 5.4 Logical Consistency Constraints

| Rule ID | Constraint | Violation Consequence |
|---|---|---|
| IR-030 | A Startup's `founding_date` must precede its `intake_date`. | Write rejected. |
| IR-031 | A Milestone's `actual_completion_date` must be after `founding_date` of the linked Startup. | Integrity flag raised. |
| IR-032 | A Grant's `award_date` must not precede its `application_date`. | Write rejected. |
| IR-033 | A Patent's `status` = Granted must be accompanied by a non-null `grant_date`. | Integrity flag raised. Write conditionally accepted; flag must be resolved. |
| IR-034 | A Customer Segment's `customer_lifetime_value_usd` must be ≥ `customer_acquisition_cost_usd`. If violated, a Viability risk record must be automatically created. | Integrity flag raised. Risk Record auto-created. |
| IR-035 | Revenue Records summed for a fiscal period must not deviate from the corresponding Financial Statement's `total_revenue_usd` by more than 5%. | Integrity warning. Reconciliation required before evaluation completion. |

### 5.5 Confidence Integrity Constraints

| Rule ID | Constraint | Violation Consequence |
|---|---|---|
| IR-040 | No entity may have `entity_confidence_score` > 0.90 with any unpopulated required attribute. | Confidence score automatically capped at 0.85 and flag raised. |
| IR-041 | A Recommendation with `disposition` = Approve must have `confidence_score` ≥ 0.65. | Recommendation auto-escalated to Human Review if confidence is below threshold. |
| IR-042 | A Recommendation's `confidence_score` must not exceed the `composite_confidence` of its linked Evaluation by more than 0.10. | Confidence discrepancy flag raised. |

---

## 6. Temporal Versioning

The Startup Knowledge Graph is designed to be a temporally consistent, replayable intelligence model. This means that the graph maintains sufficient historical information that the complete state of any entity at any past point in time can be reconstructed. This capability enables evaluators to replay historical evaluations, audit the basis for prior recommendations, and track the evolution of the startup's profile over time.

### 6.1 Versioning Strategies

The TIDES SKG employs two distinct versioning strategies, applied per entity type based on the expected volatility and audit sensitivity of the entity's attributes.

**Snapshot Versioning.** Under snapshot versioning, each write that produces a new entity version creates a complete copy of all entity attributes at the new version level. The full attribute set is stored for each version. Snapshot versioning is used for entities where the complete state at each version is needed for audit or replay: Startup, Founder, Evaluation, Recommendation, Financial Statement, ESG Record, TRL Record.

The version chain for a snapshotted entity is a linked list: each version node carries a `previous_version_id` reference pointing to the prior snapshot. The `is_current_version` flag is True only for the head of the chain.

**Delta Versioning.** Under delta versioning, only changed attributes are stored per version, along with a reference to the base version from which unchanged attributes are inherited. Delta versioning is used for entities where only a subset of attributes changes frequently: Team Member, Revenue Record, Milestone, Risk Record, Patent.

To reconstruct the full state of a delta-versioned entity at version N, the system applies the delta sequence from the base snapshot up to version N. The base snapshot is recreated (as a full snapshot) at minimum every 10 delta versions to bound reconstruction latency.

### 6.2 Graph Version Coordinates

Every entity version is identified by a two-part coordinate:
- **Entity Version:** The version number of the specific entity (e.g., Founder:3).
- **Graph Version:** The version of the Startup-level graph at the time of this entity update (e.g., SKG:1.5.2).

This allows any entity state to be addressed both individually and in the context of the full graph state at that moment.

### 6.3 Evaluation Replay

To replay an evaluation that was conducted at graph version V, the system:
1. Identifies all entities that existed at version V.
2. Reconstructs each entity's attribute state at version V using snapshot or delta reconstruction.
3. Executes the same traversal patterns and confidence propagation rules as were in effect at version V.
4. Returns the reconstructed evaluation inputs, which may be compared to the original evaluation outputs.

Evaluation replay is a mandatory capability for any appeal or dispute resolution process within the TIDES framework.

### 6.4 Temporal Query Interface

Agents and human reviewers may query the graph with a temporal constraint specified as either:
- **Point-in-time query:** "Return all entities and attributes as of timestamp T."
- **As-of-version query:** "Return all entities and attributes as of graph version V."
- **Range query:** "Return the time-series of values for attribute A of entity E between timestamps T1 and T2."

Temporal queries are read-only operations that do not modify the live graph. They execute against the version history store, which is maintained separately from the live graph to prevent performance degradation.

### 6.5 Immutability Guarantees

The versioning system enforces the following immutability guarantees:
- No version of any entity may be modified once committed.
- The `previous_version_id` chain may not be altered or reordered.
- Correction of errors in committed versions is accomplished by creating a new version with a correction flag, not by modifying the erroneous version.
- The correction version records the nature of the error, the correcting agent or reviewer, and the corrected value.

---

## 7. How AI Agents Query the Graph

AI agents in the TIDES pipeline do not access raw documents at evaluation time. All structured information retrieval is conducted through five defined query types that abstract the graph structure into parameterised operations. Each query type returns a typed, structured response that agents consume as input for their evaluation logic.

### 7.1 Query Type 1: Point Lookup

**Definition:** Retrieves the value of a specific attribute from a specific entity, identified by entity type and entity ID.

**Parameters:**
- Entity Type (e.g., Startup, Founder, Technology)
- Entity ID (UUID)
- Attribute Name (as defined in the schema)
- Optional: Version constraint (specific version or "current")

**Return:** Typed attribute value, source provenance record, confidence score, timestamp of last update.

**When Used:** When an agent needs a specific fact about a known entity — for example, retrieving the TRL level of a specific technology, or the audit status of a specific financial statement.

**Example Application:** The Financial Analysis Agent retrieves `total_revenue_usd` from all Financial Statement entities linked to the target startup before initiating its analysis.

---

### 7.2 Query Type 2: Neighbourhood Expansion

**Definition:** Retrieves all entities directly connected to a specified entity via outgoing, incoming, or both types of edges, optionally filtered by edge label or entity type.

**Parameters:**
- Start Entity Type and ID
- Edge Direction (Outgoing, Incoming, Both)
- Edge Label Filter (optional; one or more specific relationship labels)
- Target Entity Type Filter (optional)
- Confidence Threshold Filter (optional; exclude results below this confidence)

**Return:** A list of target entity stubs (entity type, ID, selected attributes) and the edge labels connecting them to the start entity.

**When Used:** When an agent needs to discover all related entities of a specific type without following a full multi-hop path — for example, retrieving all Risk Records linked to a startup, or all Patents in an IP Portfolio.

**Example Application:** The Risk Assessment Agent expands the neighbourhood of the Startup node along the `HAS_RISK_RECORD` edge to retrieve all open risk records at the start of the evaluation run.

---

### 7.3 Query Type 3: Path Traversal

**Definition:** Follows a named or custom multi-hop traversal path from a start entity through a defined sequence of edge labels to a set of terminal entities. This is the primary mechanism for executing the named traversal patterns defined in Section 3.

**Parameters:**
- Start Entity Type and ID
- Traversal Pattern Name (for named patterns) or Custom Path Specification (ordered list of edge labels and target entity types)
- Depth Limit (maximum number of hops)
- Attribute Projection (list of attributes to return at each node in the path)
- Filter Conditions (attribute value filters applicable at any hop)

**Return:** A traversal result set: for each path from start to terminal, the sequence of entities and edges traversed, with the requested attribute values at each node.

**When Used:** For all named traversal patterns (Section 3) and for custom agent-designed paths. This is the most powerful and frequently used query type in the pipeline.

**Example Application:** The IP Analysis Agent executes the IP Moat Assessment Path traversal to gather all inputs needed for the `ip_moat_assessment_score` computation.

---

### 7.4 Query Type 4: Subgraph Extraction

**Definition:** Extracts a bounded subgraph of the SKG centred on a specified entity, including all entities within a defined hop radius and all edges between those entities. The result is a complete local graph structure, not just a list of entities.

**Parameters:**
- Centre Entity Type and ID
- Hop Radius (number of hops from centre; typically 1–3)
- Entity Type Inclusion List (whitelist of which entity types to include)
- Edge Label Inclusion List (whitelist of which edge types to include)
- Confidence Threshold (minimum confidence for included entities)

**Return:** A complete subgraph structure: list of included entities with all requested attributes, and list of edges between them with labels and metadata.

**When Used:** When an agent needs a comprehensive view of a bounded region of the graph for holistic analysis — for example, extracting the complete technology-product-market subgraph for the technology readiness assessment, or extracting the founder-mentor-investor subgraph for the team quality assessment.

**Example Application:** The Evaluation Synthesis Agent extracts the full subgraph within 2 hops of the Startup node at the start of the synthesis phase to produce the narrative summary of the startup's profile.

---

### 7.5 Query Type 5: Similarity Matching

**Definition:** Identifies entities in the graph (or across multiple startup graphs in the TIDES platform) that are similar to a specified entity along one or more defined dimensions, returning a ranked list of similar entities and their similarity scores.

**Parameters:**
- Reference Entity Type and ID
- Similarity Dimensions (list of attribute names and edge patterns to use for comparison)
- Similarity Metric (Jaccard for categorical sets, cosine for numerical vectors, domain-specific for structured fields)
- Scope (within this startup's graph, or across all startup graphs in the platform)
- Top-K (number of most similar entities to return)

**Return:** Ranked list of entity IDs with similarity scores and the attribute-level contributions to the similarity score.

**When Used:** For benchmarking and comparative analysis — for example, finding the five most similar startups in the TIDES platform to use as performance benchmarks, identifying competitor entities that are most similar to the startup's product nodes, or matching a startup's customer segment profile to historical segments for which LTV data is available.

**Example Application:** The Market Analysis Agent performs cross-graph similarity matching to identify the five most comparable startups (by technology domain, sector, and stage) from the TIDES historical database and retrieves their validated revenue benchmarks for comparison.

---

## 8. Graph Population Pipeline

The Graph Population Pipeline is the structured process by which raw inputs — documents, forms, and agent outputs — are transformed into graph-structured entities and committed to the live SKG. The pipeline is sequential for a single entity and parallel across independent entities.

### 8.1 Pipeline Stages

The pipeline consists of five stages, each with defined inputs, processes, outputs, and quality gates.

---

#### Stage 1: Intake and Registration

**Trigger:** New document, form submission, or agent output is received by the TIDES system.

**Process:**
- The incoming item is classified by type: Document, Structured Form, or Agent Output.
- A Document entity is created (for all document-type inputs) with `processing_status` = Received.
- For Structured Form inputs, the form schema is mapped directly to target entity attribute names.
- For Agent Outputs, the output schema is validated against the expected agent output format.
- The item is assigned a processing job ID and placed in the extraction queue.

**Quality Gate:** File format validation, schema conformance check, duplicate detection (based on content hash). Duplicates are flagged for human review; they are not automatically rejected.

**Output:** Registered Document entity (for documents), validated form payload (for forms), validated agent payload (for agent outputs). Processing job created.

---

#### Stage 2: Extraction

**Trigger:** Processing job activated from extraction queue.

**Process:**
For document-type inputs:
- Document is parsed by the appropriate extraction agent (layout analysis, text extraction, table extraction).
- Extracted content is mapped to candidate attribute values for target entity types.
- Extraction certainty scores are assigned per extracted value.
- Candidate values are assembled into an extraction payload with schema field mappings.
- `processing_status` on the Document entity is updated to Processing.

For Structured Form inputs:
- Form payload is directly mapped to graph attribute fields. No extraction required.
- Extraction certainty = 1.0 for all form fields (deterministic mapping).

For Agent Outputs:
- Agent output payload is parsed and mapped to the target entity and attribute schema.
- Agent outputs carry explicit confidence scores assigned by the producing agent.

**Quality Gate:** Extraction completeness check. If fewer than 60% of expected fields for the target entity type are successfully extracted from a document, the Document entity is flagged `processing_status` = Failed and queued for manual review.

**Output:** Extraction payload containing candidate attribute values, field mappings, extraction certainty scores, and source document references.

---

#### Stage 3: Schema Validation and Type Checking

**Trigger:** Extraction payload complete.

**Process:**
- Each candidate value is type-checked against the defined data type of its target attribute.
- Enum values are validated against allowed enumeration members.
- Range checks are applied (e.g., TRL level 1–9, confidence scores 0.0–1.0).
- Required field presence is verified for the target entity type.
- Referential integrity checks are performed for UUID references.

**Quality Gate:** All type check failures are either corrected (for clearly parseable type mismatches, e.g., "9" as string converted to integer 9) or flagged for rejection. Values that fail type checking and cannot be auto-corrected are excluded from the payload with a flag.

**Output:** Validated attribute payload. Flagged exclusions list.

---

#### Stage 4: Cross-Entity Consistency Checking

**Trigger:** Validated attribute payload ready.

**Process:**
- The validated payload values are compared against existing values for the same attributes in the live graph.
- Logical consistency checks are performed across entities (e.g., founding date vs. intake date, equity totals, financial reconciliation).
- Conflicts with existing graph values are classified as: Minor (within tolerance), Significant (exceeds tolerance, requires review), or Critical (logical impossibility, must be resolved before commitment).
- Graph integrity rules (Section 5) are applied.

**Quality Gate:** Critical integrity violations block commitment. Significant conflicts are flagged and queued for conflict resolution. Minor conflicts are logged.

**Output:** Consistency-checked payload. Conflict report (if applicable).

---

#### Stage 5: Entity Creation or Update and Commitment

**Trigger:** Consistency-checked payload with no unresolved Critical conflicts.

**Process:**
- New entities are created with their initial attributes and the next available version number.
- For updates to existing entities, a new entity version is created (snapshot or delta, per entity type).
- Confidence scores are computed for each attribute from source quality, extraction certainty, corroboration status, and freshness.
- Entity-level confidence is computed from attribute confidence scores.
- The Startup's `graph_version` is incremented.
- `composite_confidence_score` on the Startup entity is recomputed.
- The Document entity's `processing_status` is updated to Extracted.
- All new entities and updated entities are committed to the live graph as an atomic operation.

**Quality Gate:** Atomic commit with rollback on any partial failure. Commit confirmation logged with timestamp, writing agent ID, and list of entity changes.

**Output:** Updated live graph. Updated version history. Commit log entry.

---

### 8.2 Conflict Resolution Protocol

When Stage 4 detects a Significant conflict between an incoming value and an existing graph value for the same attribute, the pipeline applies the following resolution protocol:

1. **Source Authority Check:** The source quality scores of the incoming value and the existing value are compared. The value with the higher source quality score is provisionally preferred.
2. **Recency Check:** If source quality scores are equal, the more recent value is provisionally preferred.
3. **Human Review Queue:** If neither check produces a clear winner (scores within 0.10 of each other), both values are committed as competing version candidates and the attribute is flagged for human review. The attribute-level confidence is reduced to the lower of the two competing confidence scores pending resolution.
4. **Resolution Record:** When a human reviewer selects the correct value, the rejected value is moved to the version history as a discarded candidate, and the accepted value is committed as the authoritative version.

---

### 8.3 Periodic Graph Maintenance Operations

Beyond the event-driven population pipeline, the following maintenance operations are performed on a scheduled basis:

| Operation | Frequency | Description |
|---|---|---|
| Confidence Decay Recalculation | Monthly | Recompute all attribute confidence scores for time-sensitive attributes based on current age. |
| Cross-Graph Consistency Audit | Quarterly | Verify that all cross-entity consistency rules are satisfied across the full graph. Flag newly emerged violations. |
| Competitor Data Refresh | Quarterly | Trigger external data refresh for all Competitor entities with `last_verified_date` > 12 months. |
| Citation Count Update | Quarterly | Update `citation_count` for all Research Paper entities. |
| IP Status Verification | Semi-Annual | Cross-check Patent entity statuses against patent office databases. |
| Orphan Entity Detection | Monthly | Identify entities with no valid edge connections and queue for human review or archival. |
| Version Compaction | Annual | Consolidate delta versioning chains that exceed 10 deltas without a full snapshot by creating a new base snapshot. |

---

*End of Document*

---

> **Document Control**
> This document is maintained by the TIDES Platform Architecture Team. All proposed amendments must be submitted through the TAES Change Management Process and reviewed by the Architecture Review Board before incorporation into a new document version. Approved changes are incorporated into the next minor or major version release of the TAES specification.
>
> **Version History**
>
> | Version | Date | Author | Summary of Changes |
> |---|---|---|---|
> | 1.0.0 | Initial Release | Architecture Team | First published version. |
> | 1.1.0 | 2026-06-24 | Architecture Team | Added ESG Record and IP Portfolio entities. Expanded confidence propagation model. Added Query Type 5 (Similarity Matching). Added temporal versioning section. Expanded integrity rules. |
