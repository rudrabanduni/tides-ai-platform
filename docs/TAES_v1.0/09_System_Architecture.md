> **Document:** TAES v1.0 / System Architecture
> **Classification:** Internal Technical Standard
> **Version:** 1.0.0
> **Status:** Active
> **Maintained By:** TIDES Platform Engineering
> **Last Updated:** 2026-06-23
> **Replaces:** None (inaugural edition)

---

# 09 — System Architecture: TIDES Platform as a Modular Intelligence Engine

## Table of Contents

1. [Current Platform Architecture](#1-current-platform-architecture)
2. [Evolution Strategy](#2-evolution-strategy)
3. [Current Upload Flow — Existing → Evolved](#3-current-upload-flow--existing--evolved)
4. [Current Assessment Flow — Existing → Evolved](#4-current-assessment-flow--existing--evolved)
5. [Current Dashboard — Existing → Evolved](#5-current-dashboard--existing--evolved)
6. [Current Rankings — Existing → Evolved](#6-current-rankings--existing--evolved)
7. [Current Report Generation — Existing → Evolved](#7-current-report-generation--existing--evolved)
8. [Complete Architecture Diagram](#8-complete-architecture-diagram)
9. [Data Flow Diagram](#9-data-flow-diagram)
10. [AI Flow Diagram](#10-ai-flow-diagram)
11. [How to Add New Modules Without Breaking Existing Functionality](#11-how-to-add-new-modules-without-breaking-existing-functionality)
12. [Infrastructure Considerations](#12-infrastructure-considerations)

---

## Preamble

This document defines the system architecture of the TIDES platform as it evolves from a structured startup profiling system into a full modular Intelligence Engine compliant with the TIDES AI Evaluation Standard (TAES v1.0). The guiding principle of this document is **preservation through extension**: the existing platform is not replaced, redesigned, or refactored at its core. Every capability added by TAES v1.0 is added as a new module, new endpoint, new database table, or new agent pipeline that integrates with the existing service layer without modifying its contracts.

Engineers, reviewers, and evaluators reading this document should understand:

- What exists today and why it was designed that way
- Where new capabilities attach to the existing system
- How the platform can evolve incrementally without disrupting active operations
- How to add, configure, or disable new modules safely

This document is the authoritative architectural reference for TIDES platform implementers and for external validators applying the TAES v1.0 standard.

---

## 1. Current Platform Architecture

### 1.1 Technology Stack

The TIDES platform is a purpose-built startup evaluation system implemented using a Python-based backend and a React-based frontend. The current stack is as follows:

| Layer | Technology | Role |
|---|---|---|
| API Framework | FastAPI | REST API routing, request validation, dependency injection |
| ORM | SQLAlchemy (async) | Database abstraction and model definition |
| Migrations | Alembic | Database schema versioning and migration management |
| Database (Dev) | SQLite | Lightweight relational storage for local development |
| Database (Target) | PostgreSQL | Production-grade relational database (in transition) |
| Frontend | Next.js | Server-rendered React frontend for evaluation dashboards |
| AI Gateway | LiteLLM (planned) | Provider-agnostic AI model gateway |
| Default AI Model | Claude (Anthropic) | Primary inference engine for startup evaluation |
| Auth | JWT via FastAPI dependency | Token-based authentication and role authorization |

### 1.2 Backend Module Structure

The backend is organized as a collection of domain modules. Each module encapsulates its own models, schemas, repository, service, and router. The current modules are:

```
app/
├── auth/               # Authentication, JWT issuance, token refresh
├── users/              # User management, role assignment
├── intake/             # Excel upload parsing, StartupApplication creation
├── startup_profiles/   # Startup profile management, versioning
├── evaluations/        # Evaluation lifecycle, scores, evidence
├── founders/           # Founder identity and background data
├── company_profiles/   # Legal entity, incorporation, sector classification
├── documents/          # Document storage references and metadata
├── recommendation_rules/  # Configurable scoring rules per pillar
├── dashboard/          # Aggregated metrics and cohort analytics endpoints
├── reviews/            # Reviewer comments, committee notes, score overrides
├── audit/              # System-wide audit log (who did what, when)
```

Each module directory follows a consistent internal structure:

```
<module>/
├── models.py           # SQLAlchemy ORM model definitions
├── schemas.py          # Pydantic request/response schemas
├── repository.py       # Database access layer (CRUD operations)
├── service.py          # Business logic layer
├── router.py           # FastAPI route definitions
└── dependencies.py     # Module-specific dependency injection (optional)
```

### 1.3 The Repository-Service Pattern

The TIDES platform implements the **Repository-Service pattern** as its primary architectural discipline. This pattern was chosen for the following reasons:

**Reason 1 — Separation of Persistence from Logic**
The repository layer (`repository.py`) is the sole location where SQL queries are constructed and executed. The service layer (`service.py`) operates on domain objects returned by the repository. Business rules are never embedded in queries, and queries are never constructed in business logic.

**Reason 2 — Testability**
The repository interface can be mocked in unit tests without requiring a live database connection. Service logic is testable in isolation from the persistence layer.

**Reason 3 — AI Integration Safety**
When AI agents need to read or write data, they interact through service methods, not directly through the ORM. This ensures that all AI-originated writes pass through the same validation, authorization, and audit logging that human-originated writes do.

**Reason 4 — Consistent Dependency Injection**
FastAPI's dependency injection system is used at the router level to inject database sessions, authenticated users, and service instances. This keeps route handlers thin and fully auditable.

The pattern as implemented in TIDES:

```
HTTP Request
    ↓
Router (validates schema, resolves dependencies)
    ↓
Service (applies business rules, orchestrates operations)
    ↓
Repository (executes SQL, returns ORM objects)
    ↓
Database (SQLite / PostgreSQL)
```

### 1.4 Current Data Model

The TIDES data model is organized into four logical domains:

#### 1.4.1 Identity and Access Domain

| Model | Purpose | Key Fields |
|---|---|---|
| `Users` | Platform user accounts | id, email, hashed_password, is_active, created_at |
| `Roles` | User roles for RBAC | id, name, description, permissions_json |
| `AuditLogs` | Immutable action log | id, user_id, action, resource_type, resource_id, timestamp, detail_json |

#### 1.4.2 Intake and Profile Domain

| Model | Purpose | Key Fields |
|---|---|---|
| `StartupApplications` | Raw intake record from Excel upload | id, cohort_id, raw_data_json, upload_batch_id, created_at |
| `StartupProfiles` | Canonical startup record | id, application_id, name, sector, stage, status, created_at |
| `StartupProfileVersions` | Immutable snapshot of a profile at a point in time | id, profile_id, version_number, snapshot_json, created_at |
| `Founders` | Founder identity and background | id, profile_id, name, role, linkedin_url, bio_text |
| `CompanyProfiles` | Legal entity details | id, profile_id, registration_number, incorporation_country, registered_name |

#### 1.4.3 Document Domain

| Model | Purpose | Key Fields |
|---|---|---|
| `Documents` | Uploaded file metadata and storage reference | id, profile_id, document_type, file_path, mime_type, upload_at |
| `DocumentSources` | Source attribution for AI-extracted content | id, document_id, page_number, excerpt_text, extraction_method |

#### 1.4.4 Evaluation Domain

| Model | Purpose | Key Fields |
|---|---|---|
| `Evaluations` | Evaluation record per startup per cycle | id, profile_id, cycle_id, status, overall_score, created_at |
| `EvaluationScores` | Per-pillar scores within an evaluation | id, evaluation_id, pillar_name, raw_score, weighted_score, rationale_text |
| `EvaluationEvidence` | Evidence items supporting a score | id, evaluation_id, pillar_name, claim_text, source_document_id, confidence |
| `RecommendationRules` | Configurable scoring thresholds and rules | id, pillar_name, rule_type, condition_json, action_json, is_active |
| `ReviewerComments` | Human reviewer notes on an evaluation | id, evaluation_id, reviewer_id, comment_text, created_at |
| `CommitteeNotes` | Formal committee-level deliberation notes | id, evaluation_id, committee_member_id, note_text, stage, created_at |
| `ScoreOverrides` | Audited manual score adjustments | id, evaluation_id, pillar_name, original_score, override_score, reason, overridden_by |

### 1.5 Current Evaluation Pipeline

The current pipeline processes a startup from raw Excel data to a versioned, evaluable profile:

```
Step 1: Excel file uploaded via POST /api/v1/intake/upload
Step 2: intake/service.py parses rows using openpyxl
Step 3: For each row → creates StartupApplication record
Step 4: intake/service.py calls startup_profiles/service.py
Step 5: startup_profiles/service.py creates StartupProfile record
Step 6: startup_profiles/service.py creates Founder record(s)
Step 7: startup_profiles/service.py creates StartupProfileVersion (version 1)
Step 8: Profile is now visible in the dashboard with status = "intake_complete"
Step 9: Evaluator triggers evaluation via POST /api/v1/evaluations/
Step 10: evaluations/service.py creates Evaluation record (status = "pending")
Step 11: StartupProfileContextBuilder assembles context object
Step 12: Context object passed to AI placeholder → score placeholders created
```

The `StartupProfileContextBuilder` is a critical service component that aggregates all available data about a startup into a structured context dictionary. It collects from: `StartupProfiles`, `StartupProfileVersions`, `Founders`, `CompanyProfiles`, `Documents`, and `EvaluationScores`. This context object is the primary input to any AI agent that evaluates a startup. Its design is deliberately provider-agnostic — it contains only structured data, not model-specific prompt templates.

---

## 2. Evolution Strategy

### 2.1 Why the Current Architecture Does Not Need to Be Replaced

The TIDES platform was designed with modularity as a first-class concern. The Repository-Service pattern enforces clean interfaces between layers. The module-per-domain structure means new domains can be added without touching existing ones. FastAPI's dependency injection means new services can be wired into existing routes without changing those routes. SQLAlchemy with Alembic means new tables can be added without disrupting existing schemas.

The architecture has four qualities that make replacement unnecessary and undesirable:

| Quality | Evidence |
|---|---|
| **Interface isolation** | Each module exposes services, not internal queries. AI agents consume services, not raw SQL. |
| **Schema extensibility** | Alembic migrations are additive by design. New tables do not alter existing ones. |
| **Dependency inversion** | The AI layer depends on the service layer, not the reverse. The core platform is unaware of AI agents. |
| **Stateless API design** | FastAPI endpoints are stateless. New endpoints can be added to any router without affecting existing ones. |

### 2.2 The Principle of Additive Evolution

TAES v1.0 defines **additive evolution** as the governing principle for platform enhancement:

> *Every new capability is implemented as an addition to the existing system. No existing module, table, endpoint, or contract is modified unless it is strictly necessary for backwards compatibility, and all such modifications must pass through the formal migration and review process defined in Section 11.*

In practice, this means:

- New AI agents are new Python classes in a new `intelligence/` module
- New pillar scorers are new services registered against the existing `Evaluations` schema
- New dashboard analytics are new endpoints in a new `analytics/` router
- New report templates are new rendering services that read from existing `Evaluations` and `EvaluationEvidence` tables
- New document processing capabilities are new services in the existing `documents/` module

### 2.3 Integration Points: Where New AI Agents Plug Into Existing Services

The following integration points are where the AI layer attaches to the existing platform. These are connection points, not modification points.

| Integration Point | Existing Service | AI Component That Attaches |
|---|---|---|
| Context construction | `StartupProfileContextBuilder` | All agents receive this context as their primary input |
| Score storage | `evaluations/service.py → create_score()` | Agent Orchestrator writes scores via service, not direct ORM |
| Evidence storage | `evaluations/service.py → create_evidence()` | Individual agents write evidence items via service |
| Document access | `documents/service.py → get_documents_for_profile()` | Document Analysis Agent retrieves files via service |
| Audit logging | `audit/service.py → log_action()` | Agent Orchestrator logs every agent invocation |
| Profile status update | `startup_profiles/service.py → update_status()` | Orchestrator updates profile status after pipeline completes |

### 2.4 Data Model Extension Strategy

New tables introduced by TAES v1.0 are additive. They reference existing tables via foreign keys but do not alter existing table schemas. The extension tables follow this convention:

- Table names are prefixed to indicate they belong to the intelligence layer (e.g., `agent_runs`, `agent_outputs`, `pillar_assessments`, `cohort_benchmarks`)
- All new tables have their own Alembic migration scripts
- Existing tables gain no new columns unless explicitly approved through the migration review process
- Where new columns are unavoidable on existing tables, they are nullable with a server-side default

### 2.5 API Extension Strategy

New endpoints introduced by TAES v1.0 are additive to the existing API surface:

- New routes are mounted under versioned prefixes (`/api/v1/intelligence/`, `/api/v1/analytics/`, `/api/v1/reports/`)
- No existing endpoint signatures are changed
- Existing endpoints are not deprecated without a formal deprecation notice and migration path
- New endpoints follow the same authentication and authorization conventions as existing endpoints
- New endpoints are documented in the same OpenAPI schema (`/docs`) alongside existing endpoints

---

## 3. Current Upload Flow — Existing → Evolved

### 3.1 Current Upload Flow

The current upload flow is a synchronous, linear process that transforms a structured Excel file into versioned database records.

```
[User] → POST /api/v1/intake/upload (multipart/form-data, Excel file)
          ↓
[intake/router.py] → calls intake/service.py → parse_excel_upload()
          ↓
[intake/service.py] → reads rows using openpyxl
          ↓
          For each row:
          ├─ Creates StartupApplication record
          ├─ Calls startup_profiles/service.py → create_profile_from_application()
          │     ├─ Creates StartupProfile
          │     ├─ Creates Founder records
          │     ├─ Creates CompanyProfile
          │     └─ Creates StartupProfileVersion (v1, snapshot_json = profile data)
          └─ Records AuditLog entry
          ↓
[Response] → { batch_id, profiles_created: N, errors: [] }
```

**What the current flow does not do:**
- It does not process attached documents (pitch decks, financials, patents)
- It does not trigger any AI evaluation upon upload
- It does not extract text from any file beyond the Excel sheet
- It does not assign any scores at upload time

### 3.2 Evolved Upload Flow

The evolved upload flow extends the current flow with document ingestion and asynchronous agent pipeline triggering. The core Excel parsing path is unchanged.

```
[User] → POST /api/v1/intake/upload (multipart/form-data, Excel + optional documents)
          ↓
[intake/router.py] → calls intake/service.py → parse_excel_upload()  [UNCHANGED]
          ↓
[intake/service.py] → reads rows using openpyxl [UNCHANGED]
          ↓
          For each row:
          ├─ Creates StartupApplication record [UNCHANGED]
          ├─ Calls startup_profiles/service.py → create_profile_from_application() [UNCHANGED]
          │     ├─ Creates StartupProfile [UNCHANGED]
          │     ├─ Creates Founder records [UNCHANGED]
          │     ├─ Creates CompanyProfile [UNCHANGED]
          │     └─ Creates StartupProfileVersion (v1) [UNCHANGED]
          │
          ├─ [NEW] Calls documents/service.py → ingest_batch_documents()
          │     ├─ Stores files to configured document storage (local/S3/GCS)
          │     ├─ Creates Document records with file_path, mime_type, document_type
          │     └─ Enqueues OCR/text-extraction tasks per document
          │
          └─ [NEW] Calls intelligence/service.py → enqueue_evaluation_pipeline()
                ├─ Creates AgentRun record (status = "queued")
                └─ Pushes task to background task queue (Celery / FastAPI BackgroundTasks)
          ↓
[Response] → { batch_id, profiles_created: N, documents_ingested: M, pipelines_queued: N, errors: [] }

[Async / Background]
          ↓
[Document Processor] → OCR / text extraction per Document
          ├─ Creates DocumentSources records (excerpt_text, page_number, extraction_method)
          └─ Marks Document as "text_extracted"
          ↓
[Agent Orchestrator] → triggered when all documents for a profile are extracted
          ├─ Calls StartupProfileContextBuilder → assembles full context [EXISTING]
          ├─ Appends extracted document text to context
          └─ Initiates multi-agent evaluation pipeline (see Section 4)
```

**Key design decisions in the evolved flow:**

1. The synchronous response to the user is still fast — it returns after record creation and queue submission, not after AI evaluation completes.
2. Document extraction and AI evaluation are fully asynchronous and do not block the upload response.
3. The existing Excel parse path is entirely unchanged. The evolved flow adds branches after the existing operations complete.
4. Failure in the document extraction or AI pipeline does not roll back the profile creation. Profiles always exist; evaluations are populated progressively.

---

## 4. Current Assessment Flow — Existing → Evolved

### 4.1 Current Assessment Flow

```
[Evaluator] → POST /api/v1/evaluations/  { profile_id, cycle_id }
          ↓
[evaluations/service.py] → create_evaluation()
          ├─ Creates Evaluation record (status = "pending")
          └─ Calls StartupProfileContextBuilder → context_object
          ↓
[AI Placeholder] → receives context_object
          └─ Returns stub scores → EvaluationScores created (placeholder values)
          ↓
[Evaluation status] → "complete" (placeholder scores saved)
```

**Limitations of the current flow:**
- Scores are placeholder values, not grounded in analysis
- No evidence items are created — `EvaluationEvidence` table is populated by no process
- No document text is incorporated into scoring
- No reasoning chain or audit trail for score derivation exists

### 4.2 Evolved Assessment Flow

The evolved flow replaces the AI placeholder with a structured multi-agent pipeline while preserving the existing evaluation record lifecycle.

```
[Evaluator] → POST /api/v1/evaluations/  { profile_id, cycle_id }       [UNCHANGED]
          ↓
[evaluations/service.py] → create_evaluation()                            [UNCHANGED]
          ├─ Creates Evaluation record (status = "pending")                [UNCHANGED]
          └─ Calls StartupProfileContextBuilder → context_object           [UNCHANGED]
          ↓
[intelligence/orchestrator.py] → run_evaluation_pipeline(evaluation_id, context_object)
          ↓
          ┌──────────────────────────────────────────────────────────────┐
          │  MULTI-AGENT PIPELINE (parallel execution where possible)    │
          │                                                              │
          │  Agent 1: TechnicalReadinessAgent                            │
          │    Input:  context_object.technology_section                 │
          │            context_object.documents["patent", "technical"]   │
          │    Output: TRL score (1–9), evidence_items[], rationale       │
          │    Writes: EvaluationScores (pillar="TRL")                   │
          │            EvaluationEvidence (N items, pillar="TRL")        │
          │                                                              │
          │  Agent 2: MarketOpportunityAgent                              │
          │    Input:  context_object.market_section                     │
          │            context_object.documents["pitch_deck"]            │
          │    Output: Market score (0–100), evidence_items[], rationale  │
          │    Writes: EvaluationScores (pillar="Market")                │
          │            EvaluationEvidence (N items, pillar="Market")     │
          │                                                              │
          │  Agent 3: TeamCapabilityAgent                                 │
          │    Input:  context_object.founders[]                         │
          │            context_object.company_profile                    │
          │    Output: Team score (0–100), evidence_items[], rationale   │
          │    Writes: EvaluationScores (pillar="Team")                  │
          │            EvaluationEvidence (N items, pillar="Team")       │
          │                                                              │
          │  Agent 4: BusinessModelAgent                                  │
          │    Input:  context_object.financials_section                 │
          │            context_object.documents["financial_projection"]  │
          │    Output: BizModel score (0–100), evidence_items[], rationale│
          │    Writes: EvaluationScores (pillar="BusinessModel")         │
          │            EvaluationEvidence (N items, pillar="BusinessModel")│
          │                                                              │
          │  Agent 5: ImpactAlignmentAgent                                │
          │    Input:  context_object.impact_section                     │
          │            context_object.sdg_tags[]                         │
          │    Output: Impact score (0–100), evidence_items[], rationale  │
          │    Writes: EvaluationScores (pillar="Impact")                │
          │            EvaluationEvidence (N items, pillar="Impact")     │
          │                                                              │
          │  Agent 6: ScalabilityAgent                                    │
          │    Input:  context_object.market_section                     │
          │            context_object.technology_section                 │
          │    Output: Scale score (0–100), evidence_items[], rationale  │
          │    Writes: EvaluationScores (pillar="Scalability")           │
          │            EvaluationEvidence (N items, pillar="Scalability")│
          └──────────────────────────────────────────────────────────────┘
          ↓
[intelligence/orchestrator.py] → aggregate_scores(evaluation_id)
          ├─ Applies RecommendationRules weights to pillar scores         [USES EXISTING TABLE]
          ├─ Computes overall_score
          ├─ Updates Evaluation.overall_score                             [EXISTING FIELD]
          ├─ Updates Evaluation.status = "complete"                      [EXISTING FIELD]
          └─ Logs AgentRun.status = "success"                            [NEW TABLE]
          ↓
[Report Generator] → triggered automatically on evaluation completion
          └─ Generates TAES-compliant PDF report (see Section 7)
```

**Key design decisions in the evolved flow:**

1. `evaluations/service.py` is not modified. The multi-agent pipeline is a new component that writes *through* the existing service interface, using the same `create_score()` and `create_evidence()` service methods that a human evaluator would use.
2. Agents are independent — they run in parallel where the task queue permits. They do not communicate with each other during execution.
3. Each agent writes its own evidence items. The `EvaluationEvidence` table, already defined in the existing schema, becomes the authoritative evidence store.
4. The `RecommendationRules` table, already defined, is used by the orchestrator to apply weighting. This means operators can adjust scoring weights through the existing rules interface without touching agent code.

---

## 5. Current Dashboard — Existing → Evolved

### 5.1 Current Dashboard

The current dashboard (`dashboard/` module) provides:

- A paginated list of startups with status badges
- Basic aggregate counts: total applications, pending evaluations, completed evaluations
- Filter by cohort batch and status
- Individual startup profile links

The current dashboard reads from: `StartupProfiles`, `Evaluations` (status only), `StartupApplications`.

### 5.2 Evolved Intelligence Dashboard

The evolved dashboard extends the existing dashboard with cohort-level analytics, score distributions, and sector benchmarks. All new data is computed from tables that the evolved evaluation pipeline populates.

**New dashboard panels and the data they require:**

| Panel | Data Source | New Data Required |
|---|---|---|
| **Overall Score Distribution** | `Evaluations.overall_score` | Scores populated by evolved pipeline (previously placeholder) |
| **Pillar Heatmap** | `EvaluationScores` per pillar | Evidence-grounded pillar scores from evolved pipeline |
| **Sector Benchmarking** | `StartupProfiles.sector` + `EvaluationScores` | Sector classification + pillar scores |
| **Stage Cohort Analysis** | `StartupProfiles.stage` + `Evaluations.overall_score` | Stage classification + overall scores |
| **TRL Distribution** | `EvaluationScores` (pillar="TRL") | TRL scores from TechnicalReadinessAgent |
| **Evidence Density** | `EvaluationEvidence` COUNT per evaluation | Evidence items written by agents |
| **Pipeline Status Monitor** | `AgentRun` table | New table: tracks agent pipeline execution status per evaluation |
| **Score Override Tracker** | `ScoreOverrides` | Populated by reviewers using existing override mechanism |
| **Top-Ranked Startups** | `Evaluations.overall_score` ORDER BY DESC | Same table, new query |
| **Weakest Pillar by Cohort** | `EvaluationScores` aggregated | Statistical aggregation across cohort |

**New data the evolved dashboard requires that does not currently exist:**

1. **Grounded overall scores** — `Evaluations.overall_score` is currently a placeholder. The evolved pipeline populates it with a weighted composite of pillar scores.
2. **Per-pillar scores** — `EvaluationScores` rows exist in schema but are not populated by any current process. The evolved pipeline writes one row per pillar per evaluation.
3. **Evidence counts** — `EvaluationEvidence` is empty in the current system. The evolved pipeline writes evidence items, making evidence density a computable metric.
4. **Agent run metadata** — A new `AgentRuns` table (see Section 11) tracks pipeline status, duration, and error states per evaluation. This is required for the pipeline monitor panel.
5. **TRL scores as a first-class pillar** — The evolved pipeline writes TRL scores as a named pillar in `EvaluationScores`, enabling TRL-based filtering and sorting.

**New API endpoints required for the Intelligence Dashboard:**

```
GET /api/v1/analytics/cohort/{cohort_id}/summary
GET /api/v1/analytics/cohort/{cohort_id}/score-distribution
GET /api/v1/analytics/cohort/{cohort_id}/sector-benchmarks
GET /api/v1/analytics/pillar-heatmap?cohort_id={id}
GET /api/v1/analytics/trl-distribution?cohort_id={id}
GET /api/v1/intelligence/pipeline-status/{evaluation_id}
```

These endpoints are new additions to the API surface. They do not modify any existing endpoint.

---

## 6. Current Rankings — Existing → Evolved

### 6.1 Current Rankings

The current platform presents startups in list order, sorted by submission timestamp or cohort batch order. No numerical ranking exists. The `StartupProfiles` list endpoint returns profiles ordered by `created_at` descending by default.

Rankings in the current system are informal — evaluators visually compare profiles or sort by status. No composite score drives any ordering.

### 6.2 Evolved TAES Rankings

The evolved ranking system produces a definitive ordered ranking of startups within a cohort based on their TAES evaluation scores. The ranking is computed from the `Evaluations` and `EvaluationScores` tables, which the evolved pipeline populates.

**Ranking computation:**

```
Overall TAES Score = Σ (pillar_score_i × weight_i) for all pillars i

where weights are defined in RecommendationRules and sum to 1.0
```

**Ranking dimensions and filters:**

| Dimension | Source Field | Filter Type |
|---|---|---|
| **Overall TAES Score** | `Evaluations.overall_score` | Numeric, ordinal ranking |
| **TRL Level** | `EvaluationScores.raw_score` (pillar="TRL") | Range filter (1–9) |
| **Sector** | `StartupProfiles.sector` | Categorical filter |
| **Stage** | `StartupProfiles.stage` | Categorical filter (Idea/MVP/Growth/Scale) |
| **Market Score Quartile** | `EvaluationScores.weighted_score` (pillar="Market") | Quartile filter |
| **Team Score Quartile** | `EvaluationScores.weighted_score` (pillar="Team") | Quartile filter |
| **Impact Alignment Band** | `EvaluationScores.raw_score` (pillar="Impact") | Band filter (Low/Medium/High) |

**New data the evolved rankings require:**

1. **Populated `Evaluations.overall_score`** — This field exists in the current schema but holds placeholder values. The evolved pipeline writes the computed composite score.
2. **Populated `EvaluationScores` per pillar** — Each pillar score row must exist and be grounded in agent analysis for the ranking to be meaningful.
3. **`RecommendationRules` with weight definitions** — The weighting configuration must be populated for the scoring formula to compute correctly. Default weights are defined in the system configuration.
4. **Sector and stage classifications on `StartupProfiles`** — These fields exist in the current schema and are populated from the Excel intake. The evolved ranking system uses them as first-class filter dimensions.

**New API endpoints for rankings:**

```
GET /api/v1/rankings/?cohort_id={id}&sector={s}&stage={s}&trl_min={n}&trl_max={n}
GET /api/v1/rankings/{profile_id}/pillar-breakdown
GET /api/v1/rankings/export?cohort_id={id}&format=csv
```

**Ranking display requirements for the frontend:**

- Overall rank number within cohort (1st, 2nd, … Nth)
- Overall score with ±confidence interval (derived from `EvaluationEvidence` density)
- Pillar radar chart data (six scores)
- Score vs. cohort average delta per pillar
- Rank position change if re-evaluated (requires prior `StartupProfileVersion` scores)

---

## 7. Current Report Generation — Existing → Evolved

### 7.1 Current Report Generation

The current platform generates a basic PDF assessment document (`assessment.pdf`) using a simple template renderer. The current report contains:

- Startup name and cohort batch
- Status and evaluation date
- Evaluator name
- Placeholder score table (populated with stub values)
- No evidence citations
- No pillar-level narratives

The current report is generated by a single service call that reads from `StartupProfiles` and `Evaluations` and renders a fixed template. It is functional but does not meet the evidence standards required by TAES v1.0.

### 7.2 Evolved TAES-Compliant Report Generation

The evolved report renderer produces a 5–6 page TAES-compliant evaluation report per the structure defined in `08_Report_Standard.md`. The evolved renderer reads from the same tables the evolved pipeline writes to — it is a pure reader, not a writer.

**What the evolved report renderer requires from the agent pipeline:**

| Report Section | Required Data | Source Table | Agent Responsible |
|---|---|---|---|
| Cover Page | Profile name, sector, stage, cohort, evaluation date | `StartupProfiles`, `Evaluations` | N/A (existing data) |
| Executive Summary | Overall TAES score, recommendation, top 3 strengths, top 3 risks | `Evaluations.overall_score`, `EvaluationEvidence` | Orchestrator aggregation |
| Pillar 1: TRL | TRL level (1–9), technical description, evidence citations | `EvaluationScores`, `EvaluationEvidence` | TechnicalReadinessAgent |
| Pillar 2: Market | Market score, TAM/SAM estimates, evidence citations | `EvaluationScores`, `EvaluationEvidence` | MarketOpportunityAgent |
| Pillar 3: Team | Team score, founder profiles, experience highlights, evidence citations | `EvaluationScores`, `EvaluationEvidence`, `Founders` | TeamCapabilityAgent |
| Pillar 4: Business Model | BizModel score, revenue model assessment, evidence citations | `EvaluationScores`, `EvaluationEvidence` | BusinessModelAgent |
| Pillar 5: Impact | Impact score, SDG alignment, social/environmental evidence | `EvaluationScores`, `EvaluationEvidence` | ImpactAlignmentAgent |
| Pillar 6: Scalability | Scale score, growth constraints, evidence citations | `EvaluationScores`, `EvaluationEvidence` | ScalabilityAgent |
| Reviewer Notes | Human-authored commentary and overrides | `ReviewerComments`, `ScoreOverrides` | N/A (human input) |
| Appendix | Document sources, extraction metadata, confidence levels | `Documents`, `DocumentSources`, `EvaluationEvidence` | Document Processor |

**Evidence citation format in reports:**

Every claim in the evolved report must be traceable to an `EvaluationEvidence` record. Evidence items are rendered as footnotes or inline citations with the following information:
- Source document type (e.g., "Pitch Deck, Slide 7")
- Extracted text excerpt (from `DocumentSources.excerpt_text`)
- Confidence level (from `EvaluationEvidence.confidence`)
- Agent that produced the claim

**Report generation trigger sequence:**

```
Evaluation status → "complete"
    ↓
reports/service.py → generate_taes_report(evaluation_id)
    ↓
Reads: Evaluation, EvaluationScores (all pillars), EvaluationEvidence (all items)
       StartupProfile, Founders, CompanyProfile, Documents, DocumentSources
       ReviewerComments, CommitteeNotes, ScoreOverrides
    ↓
Renders: Jinja2 / WeasyPrint HTML → PDF
    ↓
Stores: Documents record (document_type = "taes_report", file_path = "reports/{eval_id}.pdf")
    ↓
Notifies: Evaluator via dashboard notification
```

**New API endpoints for report generation:**

```
POST /api/v1/reports/generate  { evaluation_id }
GET  /api/v1/reports/{evaluation_id}/status
GET  /api/v1/reports/{evaluation_id}/download
GET  /api/v1/reports/{evaluation_id}/evidence-index
```

---

## 8. Complete Architecture Diagram

The following text diagram represents the complete evolved TIDES platform architecture as a layered system. Read from top (data entry) to bottom (output delivery).

```
╔══════════════════════════════════════════════════════════════════════════════════╗
║                         TIDES INTELLIGENCE ENGINE — TAES v1.0                  ║
║                                ARCHITECTURE LAYERS                              ║
╚══════════════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: DATA INGESTION                                                         │
│                                                                                  │
│  ┌─────────────────────┐    ┌──────────────────────┐    ┌──────────────────────┐│
│  │  Excel Upload        │    │  Document Upload      │    │  Manual Entry        ││
│  │  (.xlsx, .csv)       │    │  (PDF, DOCX, PPTX)    │    │  (Form UI)           ││
│  │  → intake/service   │    │  → documents/service  │    │  → profiles/service  ││
│  └─────────────────────┘    └──────────────────────┘    └──────────────────────┘│
│           │                           │                           │              │
│           ▼                           ▼                           ▼              │
│  StartupApplication          Document (stored)             StartupProfile        │
│  (parsed rows)               DocumentSource (OCR'd)        (manually entered)   │
└──────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 2: DATA STORAGE                                                           │
│                                                                                  │
│  ┌─────────────────┐  ┌───────────────────────┐  ┌───────────────────────────┐  │
│  │  Relational DB  │  │  File Storage          │  │  Vector Store (planned)   │  │
│  │  (PostgreSQL)   │  │  (Local / S3 / GCS)    │  │  (pgvector / Pinecone)    │  │
│  │                 │  │                        │  │                           │  │
│  │  • Users/Roles  │  │  • PDF files           │  │  • Document embeddings    │  │
│  │  • AuditLogs    │  │  • PPTX files          │  │  • Semantic search index  │  │
│  │  • Applications │  │  • DOCX files          │  │  • Claim deduplication    │  │
│  │  • Profiles     │  │  • Generated reports   │  └───────────────────────────┘  │
│  │  • Founders     │  └───────────────────────┘                                  │
│  │  • Documents    │                                                              │
│  │  • Evaluations  │                                                              │
│  │  • EvalScores   │                                                              │
│  │  • EvalEvidence │                                                              │
│  │  • AgentRuns    │                                                              │
│  │  • RecommRules  │                                                              │
│  │  • Reviews      │                                                              │
│  └─────────────────┘                                                             │
└──────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 3: AI EVALUATION (MULTI-AGENT PIPELINE)                                   │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │  StartupProfileContextBuilder (existing service — UNCHANGED)               │  │
│  │  Input: profile_id → Output: structured context_object                     │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                        │                                         │
│                                        ▼                                         │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │  Agent Orchestrator (intelligence/orchestrator.py)                          │  │
│  │  Distributes context to agents, collects outputs, applies weighting        │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│           │           │           │           │           │           │           │
│           ▼           ▼           ▼           ▼           ▼           ▼           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│  │Technical │ │Market    │ │Team      │ │Business  │ │Impact    │ │Scale-    │ │
│  │Readiness │ │Opport.   │ │Capability│ │Model     │ │Alignment │ │ability   │ │
│  │Agent     │ │Agent     │ │Agent     │ │Agent     │ │Agent     │ │Agent     │ │
│  │(TRL 1-9) │ │(0-100)   │ │(0-100)   │ │(0-100)   │ │(0-100)   │ │(0-100)   │ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│           │           │           │           │           │           │           │
│           ▼           ▼           ▼           ▼           ▼           ▼           │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │  LiteLLM Gateway (intelligence/llm_client.py)                              │  │
│  │  Provider: Claude (default) | Switchable via config                        │  │
│  │  Features: rate limiting, retry, token tracking, provider fallback         │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 4: API LAYER                                                              │
│                                                                                  │
│  FastAPI Application — Versioned REST API                                        │
│                                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │  /api/v1/    │  │  /api/v1/    │  │  /api/v1/    │  │  /api/v1/            │ │
│  │  intake/     │  │  evaluations/│  │  analytics/  │  │  intelligence/       │ │
│  │  profiles/   │  │  reports/    │  │  rankings/   │  │  (pipeline mgmt)     │ │
│  │  documents/  │  │  reviews/    │  │  dashboard/  │  │                      │ │
│  │  auth/       │  │  audit/      │  │              │  │                      │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────────────┘ │
│  [EXISTING — UNCHANGED]              [NEW — ADDITIVE]   [NEW — ADDITIVE]         │
└──────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 5: FRONTEND                                                               │
│                                                                                  │
│  Next.js Application                                                             │
│                                                                                  │
│  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────────────────────┐    │
│  │  Startup List    │  │  Evaluation View  │  │  Intelligence Dashboard      │    │
│  │  (existing)      │  │  (existing)       │  │  (NEW: analytics, heatmaps)  │    │
│  │                  │  │                   │  │                              │    │
│  │  Profile Detail  │  │  Reviewer Panel   │  │  Rankings Board (NEW)        │    │
│  │  (existing)      │  │  (existing)       │  │                              │    │
│  │                  │  │                   │  │  Pipeline Monitor (NEW)       │    │
│  └─────────────────┘  └──────────────────┘  └──────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│  LAYER 6: REPORT GENERATION                                                      │
│                                                                                  │
│  ┌────────────────────────────────────────────────────────────────────────────┐  │
│  │  reports/service.py                                                        │  │
│  │  → Reads: Evaluations, EvaluationScores, EvaluationEvidence,              │  │
│  │           Founders, Documents, DocumentSources, ReviewerComments           │  │
│  │  → Renders: Jinja2 HTML template → WeasyPrint PDF                         │  │
│  │  → Stores: Generated PDF as Document record                                │  │
│  │  → Delivers: Via /api/v1/reports/{evaluation_id}/download                  │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────────────────┘
```

---

## 9. Data Flow Diagram

The following numbered sequence describes the complete data flow from Excel upload through final report delivery. Each step identifies the component responsible and the data artifact produced.

```
COMPLETE DATA FLOW: EXCEL UPLOAD → FINAL TAES REPORT

Step 01: [User] uploads Excel file via POST /api/v1/intake/upload
         → Artifact: multipart HTTP request with .xlsx attachment

Step 02: [intake/router.py] validates request, extracts file, calls service
         → Artifact: in-memory openpyxl workbook object

Step 03: [intake/service.py] iterates Excel rows
         → Artifact: row_dict per startup (Python dictionary from worksheet)

Step 04: [intake/service.py] creates StartupApplication per row
         → Artifact: StartupApplication record in DB (id, cohort_id, raw_data_json)

Step 05: [startup_profiles/service.py] creates StartupProfile from application
         → Artifact: StartupProfile record (id, name, sector, stage, status="intake_complete")

Step 06: [startup_profiles/service.py] creates Founder records
         → Artifact: N × Founder records linked to profile_id

Step 07: [startup_profiles/service.py] creates CompanyProfile
         → Artifact: CompanyProfile record (registration, country, legal name)

Step 08: [startup_profiles/service.py] creates StartupProfileVersion v1
         → Artifact: StartupProfileVersion (version=1, snapshot_json=full profile dict)

Step 09: [documents/service.py] stores uploaded supporting documents
         → Artifact: Document records (file_path, mime_type, document_type)
         → Artifact: Files written to document_storage/{profile_id}/

Step 10: [document_processor.py] extracts text from each document (async)
         → Method: OCR (Tesseract/AWS Textract) for PDFs; direct extraction for DOCX/PPTX
         → Artifact: DocumentSource records (excerpt_text, page_number, extraction_method)
         → Artifact: Document.status updated to "text_extracted"

Step 11: [intelligence/service.py] enqueues evaluation pipeline for profile
         → Artifact: AgentRun record (evaluation_id, status="queued", queued_at=now)

Step 12: [evaluations/service.py] creates Evaluation record (triggered by evaluator or auto)
         → Artifact: Evaluation record (profile_id, cycle_id, status="pending")

Step 13: [StartupProfileContextBuilder] assembles structured context object
         → Inputs: StartupProfile, Founders, CompanyProfile, Documents, DocumentSources
         → Artifact: context_object (Python dict with sections: technology, market,
                     team, financials, impact, documents[])

Step 14: [intelligence/orchestrator.py] distributes context to 6 agents in parallel
         → Artifact: 6 × agent task submissions to LiteLLM gateway

Step 15: [LiteLLM gateway] routes requests to Claude (or configured provider)
         → Artifact: 6 × structured AI responses (JSON: score, evidence[], rationale)

Step 16: [Each Agent] parses AI response and writes results via service layer
         → Artifact: EvaluationScores (6 rows, one per pillar, for this evaluation)
         → Artifact: EvaluationEvidence (N rows per pillar, total 20–60 evidence items)

Step 17: [intelligence/orchestrator.py] aggregates scores using RecommendationRules weights
         → Formula: overall_score = Σ(weighted_score_i) for i in 6 pillars
         → Artifact: Evaluation.overall_score updated, Evaluation.status = "complete"

Step 18: [audit/service.py] logs pipeline completion
         → Artifact: AuditLog record (action="evaluation_pipeline_complete", resource_id=eval_id)

Step 19: [reports/service.py] triggered automatically on evaluation completion
         → Reads: All evaluation data, evidence, founders, documents
         → Renders: Jinja2 template → HTML → WeasyPrint → PDF bytes

Step 20: [reports/service.py] stores generated PDF
         → Artifact: Document record (document_type="taes_report",
                     file_path="reports/{eval_id}/taes_report.pdf")

Step 21: [Frontend notification] evaluator sees "Report Ready" status in dashboard
         → Data: Evaluation.status = "complete", Report document_id available

Step 22: [Evaluator] optionally adds ReviewerComments or ScoreOverrides
         → Artifact: ReviewerComments and/or ScoreOverrides records
         → Artifact: Report can be regenerated incorporating human review

Step 23: [Committee] adds CommitteeNotes for shortlisted startups
         → Artifact: CommitteeNotes records linked to evaluation

Step 24: [User] downloads TAES report via GET /api/v1/reports/{evaluation_id}/download
         → Artifact: 5–6 page PDF per 08_Report_Standard.md, delivered to browser
```

---

## 10. AI Flow Diagram

The following diagram describes the AI evaluation flow in detail, showing agent orchestration, data consumption, inter-agent isolation, and output production.

```
AI EVALUATION FLOW — DETAILED

INPUT STAGE
───────────────────────────────────────────────────────────────────────────────────
Trigger: Orchestrator receives (evaluation_id, context_object)

context_object structure:
{
  "profile": { name, sector, stage, trl_claim, sdg_tags[] },
  "founders": [ { name, role, linkedin, bio, experience_years } ],
  "company": { registration, country, stage, employees, founded_year },
  "technology": { description, ip_status, trl_self_reported, key_innovations[] },
  "market": { target_market, tam_estimate, sam_estimate, competitors[], differentiators[] },
  "financials": { revenue_model, mrr, burn_rate, runway_months, funding_stage },
  "impact": { problem_statement, beneficiaries, sdg_alignment[], impact_metrics[] },
  "documents": {
    "pitch_deck": { text_chunks[], page_count, extraction_confidence },
    "financial_projection": { text_chunks[], extraction_confidence },
    "patent": { text_chunks[], extraction_confidence },
    "technical_report": { text_chunks[], extraction_confidence }
  }
}

AGENT ORCHESTRATION STAGE
───────────────────────────────────────────────────────────────────────────────────
Orchestrator dispatches 6 parallel agent tasks:

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  AGENT 1: TechnicalReadinessAgent                                           │
  │                                                                             │
  │  Consumes:   context.technology, context.documents["patent", "technical"]   │
  │  System prompt section: TRL rubric (ESA/EU Commission TRL 1–9 definitions) │
  │  Task: Assess technology maturity level, assign TRL 1–9                     │
  │                                                                             │
  │  LiteLLM call:                                                              │
  │    model: claude-3-5-sonnet (default via LiteLLM config)                   │
  │    messages: [system=TRL_rubric, user=technology_context_json]              │
  │    response_format: { trl_level: int, rationale: str, evidence: [          │
  │      { claim, source_doc, source_page, confidence }                        │
  │    ]}                                                                       │
  │                                                                             │
  │  Produces:                                                                  │
  │    → EvaluationScores(pillar="TRL", raw_score=TRL_level, rationale=...)    │
  │    → EvaluationEvidence(N items, pillar="TRL", claim, confidence, source)  │
  └─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  AGENT 2: MarketOpportunityAgent                                            │
  │                                                                             │
  │  Consumes:   context.market, context.documents["pitch_deck"]               │
  │  System prompt section: Market scoring rubric (TAM/SAM/SOM, growth rate,  │
  │                          competitive positioning, market timing)            │
  │  Task: Score market opportunity on 0–100 scale                             │
  │                                                                             │
  │  LiteLLM call:                                                              │
  │    model: claude-3-5-sonnet                                                 │
  │    messages: [system=market_rubric, user=market_context_json]               │
  │    response_format: { score: int, tam_usd: float, sam_usd: float,         │
  │      competitive_position: str, rationale: str, evidence: [...] }          │
  │                                                                             │
  │  Produces:                                                                  │
  │    → EvaluationScores(pillar="Market", raw_score=score, rationale=...)     │
  │    → EvaluationEvidence(N items, pillar="Market")                          │
  └─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  AGENT 3: TeamCapabilityAgent                                               │
  │                                                                             │
  │  Consumes:   context.founders[], context.company                            │
  │  System prompt section: Team scoring rubric (domain expertise, founding    │
  │                          experience, team completeness, advisor quality)   │
  │  Task: Score team capability on 0–100 scale                                │
  │                                                                             │
  │  LiteLLM call:                                                              │
  │    model: claude-3-5-sonnet                                                 │
  │    messages: [system=team_rubric, user=founders_context_json]               │
  │    response_format: { score: int, team_strengths: [], gaps: [],            │
  │      rationale: str, evidence: [...] }                                      │
  │                                                                             │
  │  Produces:                                                                  │
  │    → EvaluationScores(pillar="Team", raw_score=score, rationale=...)       │
  │    → EvaluationEvidence(N items, pillar="Team")                            │
  └─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  AGENT 4: BusinessModelAgent                                                │
  │                                                                             │
  │  Consumes:   context.financials, context.documents["financial_projection"] │
  │  System prompt section: Business model rubric (revenue model clarity,     │
  │                          unit economics, monetisation path, sustainability)│
  │  Task: Score business model viability on 0–100 scale                       │
  │                                                                             │
  │  LiteLLM call:                                                              │
  │    model: claude-3-5-sonnet                                                 │
  │    messages: [system=bizmodel_rubric, user=financials_context_json]         │
  │    response_format: { score: int, revenue_model_type: str,                 │
  │      unit_economics_quality: str, rationale: str, evidence: [...] }        │
  │                                                                             │
  │  Produces:                                                                  │
  │    → EvaluationScores(pillar="BusinessModel", raw_score=score, ...)        │
  │    → EvaluationEvidence(N items, pillar="BusinessModel")                   │
  └─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  AGENT 5: ImpactAlignmentAgent                                              │
  │                                                                             │
  │  Consumes:   context.impact, context.profile.sdg_tags[]                    │
  │  System prompt section: Impact scoring rubric (SDG alignment specificity,  │
  │                          beneficiary definition, impact measurability,     │
  │                          environmental and social risk assessment)          │
  │  Task: Score impact alignment on 0–100 scale                               │
  │                                                                             │
  │  LiteLLM call:                                                              │
  │    model: claude-3-5-sonnet                                                 │
  │    messages: [system=impact_rubric, user=impact_context_json]               │
  │    response_format: { score: int, sdg_match_quality: str,                  │
  │      impact_band: "Low|Medium|High", rationale: str, evidence: [...] }     │
  │                                                                             │
  │  Produces:                                                                  │
  │    → EvaluationScores(pillar="Impact", raw_score=score, rationale=...)     │
  │    → EvaluationEvidence(N items, pillar="Impact")                          │
  └─────────────────────────────────────────────────────────────────────────────┘

  ┌─────────────────────────────────────────────────────────────────────────────┐
  │  AGENT 6: ScalabilityAgent                                                  │
  │                                                                             │
  │  Consumes:   context.market, context.technology, context.financials        │
  │  System prompt section: Scalability rubric (geographic expansion potential,│
  │                          technical scalability, capital efficiency,        │
  │                          regulatory barriers, partnership leverage)         │
  │  Task: Score scalability potential on 0–100 scale                          │
  │                                                                             │
  │  LiteLLM call:                                                              │
  │    model: claude-3-5-sonnet                                                 │
  │    messages: [system=scale_rubric, user=scalability_context_json]           │
  │    response_format: { score: int, primary_growth_lever: str,               │
  │      key_constraint: str, rationale: str, evidence: [...] }                │
  │                                                                             │
  │  Produces:                                                                  │
  │    → EvaluationScores(pillar="Scalability", raw_score=score, ...)          │
  │    → EvaluationEvidence(N items, pillar="Scalability")                     │
  └─────────────────────────────────────────────────────────────────────────────┘

AGGREGATION STAGE
───────────────────────────────────────────────────────────────────────────────────
Orchestrator waits for all 6 agent tasks to complete (timeout: 120 seconds).

On success of all 6:
  1. Load RecommendationRules where pillar IN (6 pillars) AND rule_type = "weight"
  2. Compute: weighted_score_i = raw_score_i × weight_i
  3. Compute: overall_score = Σ(weighted_score_i) / Σ(weight_i)
  4. Write: Evaluation.overall_score = overall_score
  5. Write: Evaluation.status = "complete"
  6. Write: AgentRun.status = "success", AgentRun.completed_at = now()
  7. Trigger: Report generation pipeline

On partial failure (1 or more agents fail):
  1. Write: EvaluationScores for successful agents
  2. Write: EvaluationScores with status="agent_error" for failed agents
  3. Write: Evaluation.status = "partial" (new status value, backwards compatible)
  4. Write: AgentRun.status = "partial", error_detail_json = { failed_agents: [...] }
  5. Alert: Dashboard notification to evaluator for manual review

PROVIDER ABSTRACTION LAYER
───────────────────────────────────────────────────────────────────────────────────
All agent LiteLLM calls pass through the configured gateway:

  intelligence/llm_client.py
  │
  ├── Provider: "anthropic/claude-3-5-sonnet-20241022" (default)
  ├── Fallback: "anthropic/claude-3-haiku" (cost-optimized fallback)
  ├── Max tokens: 4096 (per agent call)
  ├── Temperature: 0.1 (deterministic scoring)
  ├── Retry policy: 3 attempts, exponential backoff
  ├── Rate limit: 10 concurrent agent calls (configurable)
  └── Token tracking: per evaluation_id, logged to AgentRun.token_usage_json
```

---

## 11. How to Add New Modules Without Breaking Existing Functionality

### 11.1 The Module Contract

Any new module added to the TIDES platform must satisfy the following integration contract. This contract is binding for all TAES v1.0-compliant implementations.

**Required components:**

| Component | File | Requirement |
|---|---|---|
| ORM Models | `models.py` | Must define all new tables. Must not alter any existing table schema. |
| Pydantic Schemas | `schemas.py` | Must define all request and response schemas. Must not redefine schemas from other modules. |
| Repository | `repository.py` | Must be the sole SQL access layer for new module data. Must not issue queries against other modules' tables except via those modules' repositories. |
| Service | `service.py` | Must contain all business logic. Must interact with other modules only via their service layer, never via their repository. |
| Router | `router.py` | Must define all new API endpoints. Must use FastAPI's `APIRouter` and mount under a new versioned prefix. |
| Alembic Migration | `alembic/versions/*.py` | Must be provided for all new tables. Must be a pure addition (no `op.drop_column`, `op.alter_column` on existing tables without migration review approval). |
| Configuration | `config.py` (module-level) or `settings.py` (global) | Must be configurable. Must define an `enabled` flag that, when set to `False`, causes the module router to not be mounted and the module services to not be initialized. |

**Optional but recommended:**

| Component | File | Purpose |
|---|---|---|
| Tests | `tests/test_{module}.py` | Unit tests for service layer; integration tests for router |
| README | `{module}/README.md` | Module-level documentation including data model, API surface, and integration notes |

### 11.2 The Dependency Rule

New modules may depend on core modules. Core modules must not depend on new modules. This is a strict one-directional dependency constraint.

**Core modules** (must never be modified to depend on new modules):
- `auth`
- `users`
- `intake`
- `startup_profiles`
- `evaluations`
- `audit`

**Permitted dependency directions:**

```
intelligence/  →  evaluations/, startup_profiles/, documents/, audit/   ✓ ALLOWED
analytics/     →  evaluations/, startup_profiles/                        ✓ ALLOWED
reports/       →  evaluations/, startup_profiles/, documents/            ✓ ALLOWED
intake/        →  intelligence/                                          ✗ FORBIDDEN
evaluations/   →  intelligence/                                          ✗ FORBIDDEN
startup_profiles/ → analytics/                                           ✗ FORBIDDEN
```

If a new module's functionality is required inside a core module, the correct approach is to define a protocol (abstract interface) in the core module that the new module implements, and use dependency injection to provide the implementation at runtime. The core module remains unaware of the concrete implementing class.

### 11.3 The Versioning Rule

New modules must not change existing API contracts. This means:

- **No removal of existing fields from response schemas.** Fields may be added (with defaults); they may not be removed.
- **No change to existing HTTP method semantics.** A `GET` endpoint must remain `GET`. A `POST` that creates a resource must continue to create that resource.
- **No change to existing URL structures.** A URL that exists must continue to work identically.
- **No new required parameters on existing endpoints.** New parameters on existing endpoints must be optional with sensible defaults.
- **No change to existing status codes.** If a 200 was returned, a 200 must continue to be returned for the same input.

If a breaking change is unavoidable, a new API version prefix (`/api/v2/`) must be introduced. The existing v1 routes must continue to function until a formally announced sunset date.

### 11.4 The Database Rule

New modules add tables; they do not modify existing tables except under the following strictly controlled conditions:

**Permitted operations on existing tables (with migration review approval):**
- Adding a nullable column with a `server_default` value
- Adding an index on an existing column
- Adding a foreign key from a new table to an existing table

**Prohibited operations on existing tables (require architectural review board approval):**
- Dropping any column
- Renaming any column
- Changing the data type of any column
- Dropping any table
- Adding a non-nullable column without a `server_default`
- Removing or changing any existing index that affects query plans

**Migration review process:**
1. New module author submits Alembic migration script for review
2. A senior engineer and a database administrator review for safety and reversibility
3. Every migration must have a `downgrade()` function that fully reverses all changes
4. Migrations must be tested against both SQLite (development) and PostgreSQL (staging) before production deployment

### 11.5 The Configuration Rule

New modules must be configurable and must be disableable without affecting core platform operation. The configuration rule is enforced as follows:

```python
# In app/config.py (global settings) — example pattern:
class Settings(BaseSettings):
    # ... existing settings unchanged ...

    # New module flags — all optional with defaults
    intelligence_module_enabled: bool = True
    analytics_module_enabled: bool = True
    reports_module_enabled: bool = True
    vector_store_enabled: bool = False  # Not yet available in all environments

# In app/main.py — conditional router mounting:
if settings.intelligence_module_enabled:
    from app.intelligence.router import router as intelligence_router
    app.include_router(intelligence_router, prefix="/api/v1/intelligence")

if settings.analytics_module_enabled:
    from app.analytics.router import router as analytics_router
    app.include_router(analytics_router, prefix="/api/v1/analytics")
```

When a new module is disabled:
- Its router is not mounted (endpoints return 404)
- Its service is not initialized (no startup overhead)
- Its database tables still exist (migrations have already run; disabling does not drop tables)
- The core pipeline continues to function without the disabled module's output

This property is critical for staged rollouts and for environments (testing, development) where not all modules are available.

### 11.6 New Module Registration Checklist

Before a new module is merged to the main branch, the following checklist must be satisfied:

```
□ models.py defines all new tables (no modifications to existing tables)
□ Alembic migration provided and reviewed
□ Migration downgrade() function implemented and tested
□ schemas.py defines all request/response models
□ repository.py contains all SQL, no SQL in service.py
□ service.py contains all business logic, no raw SQL
□ router.py mounts under a new prefix not used by any existing module
□ Configuration flag added to Settings; module disables cleanly
□ No import of new module from any core module
□ All new endpoints documented in OpenAPI (auto-generated from FastAPI)
□ Unit tests provided for service layer (≥80% coverage)
□ Integration tests provided for at least the happy path of each new endpoint
□ Module-level README.md written
□ Dependency direction verified (no core module imports new module)
□ Versioning rule verified (no existing API signatures changed)
```

---

## 12. Infrastructure Considerations

### 12.1 Database: SQLite to PostgreSQL Migration Path

**Current state:** The TIDES platform uses SQLite for local development. SQLite is suitable for development environments where simplicity is preferred over concurrency and production features.

**Target state:** PostgreSQL is the designated production database. The transition is underway.

**Migration path:**

| Step | Action | Risk | Mitigation |
|---|---|---|---|
| 1 | Install `asyncpg` and `psycopg2-binary` dependencies | Low | Add to requirements.txt |
| 2 | Add `DATABASE_URL` environment variable to settings, defaulting to SQLite for development | Low | Use Pydantic settings with env override |
| 3 | Configure SQLAlchemy engine creation to detect dialect from `DATABASE_URL` | Low | Standard SQLAlchemy pattern |
| 4 | Run all existing Alembic migrations against PostgreSQL staging database | Medium | Test with `alembic upgrade head` on empty PostgreSQL; compare schema |
| 5 | Migrate existing SQLite data (if any production data exists in SQLite) | High | Use `pgloader` or custom migration script with full backup before execution |
| 6 | Update Alembic `env.py` to support both SQLite and PostgreSQL targets | Low | Dialect-aware env.py |
| 7 | Enable PostgreSQL-specific features: JSONB columns, full-text search, pg_trgm | Medium | New Alembic migration per feature adoption |
| 8 | Configure connection pooling (`asyncpg` pool settings, `max_overflow`, `pool_size`) | Medium | Start with conservative pool: size=10, overflow=20 |
| 9 | Enable SSL connections to PostgreSQL in production | Low | Add `ssl=require` to DATABASE_URL |

**SQLite-specific code to audit before migration:**

- Any use of `sqlite_autoincrement=True` in model definitions (PostgreSQL uses SERIAL/BIGSERIAL)
- Any direct use of SQLite-specific functions in queries (e.g., `strftime()` — replace with PostgreSQL equivalents)
- Any column types using `JSON` (acceptable in both) versus `JSONB` (PostgreSQL-only, preferred for queryability)
- Any use of `TEXT` for large columns that should be `TEXT` in PostgreSQL (same type, verify encoding)

### 12.2 AI Infrastructure: LiteLLM Gateway Design

The LiteLLM gateway is the AI provider abstraction layer. Its design is as follows:

**Gateway configuration file** (`intelligence/llm_config.yaml`):

```yaml
model_list:
  - model_name: claude-primary
    litellm_params:
      model: anthropic/claude-3-5-sonnet-20241022
      api_key: os.environ/ANTHROPIC_API_KEY
      max_tokens: 4096
      temperature: 0.1
    model_info:
      mode: chat
      cost_per_token_input: 0.000003
      cost_per_token_output: 0.000015

  - model_name: claude-fallback
    litellm_params:
      model: anthropic/claude-3-haiku-20240307
      api_key: os.environ/ANTHROPIC_API_KEY
      max_tokens: 2048
      temperature: 0.1
    model_info:
      mode: chat

router_settings:
  routing_strategy: fallback
  fallback_models: ["claude-fallback"]
  num_retries: 3
  retry_after: 2
  timeout: 60
  allowed_fails: 2

litellm_settings:
  set_verbose: false
  success_callback: ["langfuse"]    # Optional: LLM observability
  failure_callback: ["langfuse"]
```

**Provider switching:** To switch providers, only `llm_config.yaml` needs to be updated. Agent code calls `litellm.completion(model="claude-primary", ...)` — the gateway resolves this to the configured provider. Switching to GPT-4o requires only adding a new model entry to the config and changing the `model_name` referenced in agent code.

**Rate limiting:** LiteLLM enforces rate limits at the gateway level:
- `max_parallel_requests: 10` — no more than 10 concurrent LLM calls across all agents
- `tpm_limit: 100000` — tokens per minute ceiling to stay within Anthropic tier limits
- Per-evaluation budget tracking via `AgentRun.token_usage_json`

**Token tracking:** Each `AgentRun` record stores `token_usage_json`:
```json
{
  "TechnicalReadinessAgent": { "input_tokens": 1200, "output_tokens": 800 },
  "MarketOpportunityAgent":  { "input_tokens": 1400, "output_tokens": 900 },
  ...
  "total_input_tokens": 7500,
  "total_output_tokens": 5100,
  "estimated_cost_usd": 0.099
}
```

### 12.3 Document Storage Strategy

Uploaded documents must be stored durably and retrievably. The storage strategy is tiered by deployment environment:

| Environment | Storage Backend | Configuration |
|---|---|---|
| Development | Local filesystem | `DOCUMENT_STORAGE_BACKEND=local`, `DOCUMENT_STORAGE_PATH=./uploads/` |
| Staging | Local filesystem or S3-compatible (MinIO) | `DOCUMENT_STORAGE_BACKEND=s3`, `DOCUMENT_STORAGE_BUCKET=tides-staging` |
| Production | AWS S3 or Google Cloud Storage | `DOCUMENT_STORAGE_BACKEND=s3`, `DOCUMENT_STORAGE_BUCKET=tides-production` |

**Storage path convention:**
```
{storage_root}/
  {profile_id}/
    {document_type}/
      {uuid}_{original_filename}
  reports/
    {evaluation_id}/
      taes_report_{version}.pdf
```

**Document access:** All document file access goes through `documents/service.py → get_document_url(document_id)`. This method returns either a local file path (development) or a pre-signed URL (S3 production). Agent code and report renderers never construct file paths directly — they call the document service.

**Retention policy:** Documents are retained indefinitely by default. A `document_retention_days` configuration can trigger archival or deletion of documents older than the configured period. Deletion must be preceded by verification that no `EvaluationEvidence` record references the document.

### 12.4 Caching Strategy

Caching reduces redundant computation and LiteLLM API costs. The following caching layers apply:

| Cache Target | Cache Type | TTL | Rationale |
|---|---|---|---|
| `StartupProfileContextBuilder` output | In-memory (per-request) | Request lifetime | Context is assembled once per agent run, not per agent |
| `RecommendationRules` weights | In-memory (application-level) | 5 minutes | Rules rarely change; avoids repeated DB reads per scoring cycle |
| Cohort analytics aggregates | Redis / PostgreSQL materialized view | 15 minutes | Expensive GROUP BY queries on large cohorts |
| Dashboard summary stats | Redis / PostgreSQL materialized view | 5 minutes | Total counts and averages; acceptable staleness |
| Generated TAES PDF reports | Filesystem / S3 (already stored as Document) | Permanent | Reports are generated once; stored as Document record |
| LiteLLM response cache | LiteLLM built-in (Redis) | 24 hours | Identical context sent to same model returns cached response; avoids duplicate spend on retry |

**Cache invalidation events:**

| Event | Caches Invalidated |
|---|---|
| `RecommendationRules` updated | Rules weights cache |
| New `EvaluationScores` written | Cohort analytics cache, dashboard stats cache |
| `ScoreOverrides` applied | Cohort analytics cache, dashboard stats cache, related report invalidated |
| New `StartupProfile` created | Dashboard stats cache |
| Profile `status` updated | Dashboard stats cache |

**Redis configuration (for production):**

```
REDIS_URL=redis://localhost:6379/0
CACHE_RECOMMENDATION_RULES_TTL=300       # 5 minutes
CACHE_COHORT_ANALYTICS_TTL=900           # 15 minutes
CACHE_DASHBOARD_STATS_TTL=300            # 5 minutes
LITELLM_REDIS_CACHE_ENABLED=true
LITELLM_REDIS_URL=redis://localhost:6379/1  # Separate DB for LiteLLM
```

For development environments without Redis, all caches fall back to in-memory Python dictionaries with the same TTL semantics, implemented via `cachetools.TTLCache`.

---

## Appendix A: New Tables Introduced by TAES v1.0

The following tables are added by the intelligence layer. All are additive — no existing table is modified.

| Table | Purpose | Key Fields |
|---|---|---|
| `agent_runs` | Tracks each execution of the multi-agent pipeline | id, evaluation_id, status, queued_at, started_at, completed_at, token_usage_json, error_detail_json |
| `agent_outputs` | Raw output from each individual agent (for auditability) | id, agent_run_id, agent_name, raw_response_json, parsed_score, parsed_evidence_count, duration_ms |
| `cohort_benchmarks` | Cached aggregate statistics per cohort | id, cohort_id, pillar_name, mean_score, median_score, stddev_score, p25_score, p75_score, computed_at |
| `document_processing_jobs` | Tracks OCR/text-extraction task status per document | id, document_id, processor_type, status, started_at, completed_at, error_message |
| `report_generations` | Tracks report generation job per evaluation | id, evaluation_id, status, triggered_at, completed_at, document_id (FK to documents), error_message |

---

## Appendix B: Environment Variables Reference

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./tides.db` | Database connection string |
| `ANTHROPIC_API_KEY` | (required) | Anthropic Claude API key |
| `LITELLM_PRIMARY_MODEL` | `anthropic/claude-3-5-sonnet-20241022` | Default model for all agents |
| `LITELLM_FALLBACK_MODEL` | `anthropic/claude-3-haiku-20240307` | Fallback model on primary failure |
| `LITELLM_REDIS_CACHE_ENABLED` | `false` | Enable Redis response caching for LiteLLM |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection URL for application cache |
| `DOCUMENT_STORAGE_BACKEND` | `local` | Storage backend: `local`, `s3`, `gcs` |
| `DOCUMENT_STORAGE_PATH` | `./uploads/` | Local storage base path |
| `DOCUMENT_STORAGE_BUCKET` | (required if S3/GCS) | S3 or GCS bucket name |
| `INTELLIGENCE_MODULE_ENABLED` | `true` | Enable/disable the AI intelligence module |
| `ANALYTICS_MODULE_ENABLED` | `true` | Enable/disable the analytics module |
| `REPORTS_MODULE_ENABLED` | `true` | Enable/disable the report generation module |
| `AGENT_PIPELINE_TIMEOUT_SECONDS` | `120` | Maximum duration for a full 6-agent pipeline run |
| `AGENT_MAX_CONCURRENT_CALLS` | `10` | Maximum concurrent LiteLLM API calls |
| `SECRET_KEY` | (required) | JWT signing secret |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | JWT access token lifetime |

---

## Appendix C: Glossary

| Term | Definition |
|---|---|
| **Additive Evolution** | The architectural principle that new capabilities are implemented as additions (new modules, tables, endpoints) rather than modifications to existing components. |
| **Agent Orchestrator** | The component in `intelligence/orchestrator.py` that dispatches context to individual agents, collects their outputs, applies weighting, and writes final scores. |
| **AgentRun** | A database record that tracks the execution lifecycle of a multi-agent evaluation pipeline for a single evaluation. |
| **Context Object** | The structured Python dictionary produced by `StartupProfileContextBuilder` that aggregates all available data about a startup for consumption by AI agents. |
| **Integration Point** | A specific location in the existing service layer where a new module attaches without modifying the existing code. |
| **LiteLLM Gateway** | The provider-agnostic AI model gateway that routes inference requests to Claude or other configured providers. |
| **Module Contract** | The set of required components and constraints that a new TIDES module must satisfy to integrate correctly with the platform. |
| **Repository-Service Pattern** | The architectural pattern used by TIDES where repositories handle all SQL and services handle all business logic. |
| **StartupProfileContextBuilder** | The existing TIDES service that assembles a complete structured context from all data associated with a startup profile. |
| **TAES** | TIDES AI Evaluation Standard — the formal standard defining evaluation methodology, scoring criteria, report format, and platform architecture requirements. |
| **TRL** | Technology Readiness Level — a scale from 1 (basic research) to 9 (proven system) used to assess the maturity of a technology. Defined by NASA, adopted by ESA and EU Commission. |
