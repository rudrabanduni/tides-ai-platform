# Current System Audit: TIDES AI Platform

> **Document:** TIE Integration / Current System Audit  
> **Classification:** Internal Engineering Standard  
> **Version:** 1.0.0  
> **Date:** June 24, 2026

This document presents a detailed architectural audit of the current TIDES AI Startup Evaluation Platform codebase. It analyzes the existing backend and frontend components, database schemas, AI completion capabilities, and report generation systems, identifying technical debt, bottlenecks, and constraints to prepare for the TIDES Intelligence Engine (TIE) integration.

---

## 1. Current Architecture Overview

The TIDES AI Platform is built as a multi-tier web application using a modular **Repository-Service pattern** for the backend and a standard route-based structure for the frontend.

```
+-------------------------------------------------------------+
|                     Next.js Frontend                        |
|   (App Router: /upload, /startups, /evaluations, /rankings) |
+------------------------------+------------------------------+
                               | API Requests (JSON / HTTP)
                               v
+-------------------------------------------------------------+
|                     FastAPI Backend                         |
|   (Modular Structure: Auth, Intake, Profiles, Evaluations)  |
+------------------------------+------------------------------+
                               | SQLAlchemy ORM
                               v
+-------------------------------------------------------------+
|                  Database Layer (SQLite)                     |
|     (Tables: startups, profiles, evaluations, evidence)     |
+-------------------------------------------------------------+
```

### Backend Structure
- **Framework:** FastAPI (`uvicorn` server) with Pydantic v2 for data validation and schema serialization.
- **Data Access:** SQLAlchemy 2.0 ORM using a Repository-Service pattern. Repositories manage database access logic, while Services manage transaction boundaries and business logic.
- **Migrations:** Alembic is used to manage database schema updates.
- **Modules (`app/modules/`):** Code is split into domain-specific modules:
  - `auth`: User authentication, registration, token generation, and password hashing.
  - `users` & `audit`: User model and entity audit logs tracking actions across the system.
  - `startups` & `founders` & `company_profiles`: Handles raw application data, founder info, and company details.
  - `intake`: Handles spreadsheet parsing and startup ingestion via `openpyxl`.
  - `startup_profiles`: Versioned summaries and simple assessments (`AIAssessmentRecord`).
  - `evaluations`: Rubrics, criteria, scores, and evidence logs.
  - `recommendation_rules`: Configurable score bands for automated recommendations.
  - `reviews`: Score overrides, committee comments, and reviewer annotations.
- **AI Gateway:** A provider-agnostic completion interface (`app/services/ai/gateway.py`) wrapping LiteLLM. It defaults to Claude (`claude-3-5-sonnet-20241022`) and supports JSON schema response validation via Pydantic models.
- **Reporting:** reportlab-based PDF generation (`app/services/report/pdf.py`) that exports evaluation summaries into formatted documents.

### Frontend Structure
- **Framework:** Next.js (version 16.2.9) with React 19, configured using App Router (`src/app/`).
- **Styling:** TailwindCSS v4 with class-variance-authority for custom UI variants and Shadcn components.
- **State & Data Fetching:** Axios for HTTP client operations and `@tanstack/react-query` for API cache management.

---

## 2. Platform Strengths

1. **Clear Modular Boundaries:** The Repository-Service pattern per module (e.g., `app/modules/evaluations/repository.py` and `service.py`) isolates domain logic cleanly. This permits modular extensions (like TIE) without refactoring unrelated components.
2. **Robust Audit Logging:** The system contains a dedicated `AuditLog` table and `AuditService` that logs database changes (e.g., `startup_profile_created`, `evaluation_finalized`) with JSON payloads. This serves as a foundation for evidence-tracking audits.
3. **Structured AI Integration:** The current LiteLLM gateway uses Pydantic schema validation to verify LLM outputs (`complete_json`). This prevents structural failures when calling model interfaces.
4. **Strong Schema Separation:** The separation of raw startup applications (`startup_applications`), processed profiles (`startup_profiles`), and scoring metrics (`evaluations`) maintains clear boundaries between data states.
5. **Decoupled Scoring Logic:** Score overrides (`ScoreOverride`), reviewer comments (`ReviewerComment`), and recommendation rules (`RecommendationRules`) are isolated from the core evaluation models, preserving audit trails when humans adjust scores.

---

## 3. Platform Weaknesses

1. **Single-Agent Bottleneck:** The current AI assessment (`StartupProfileAgentService.assess_startup`) uses a single monolithic prompt combining Innovation, Market, and Execution criteria. This approach hits context limitations, cannot utilize specialized domain logic, and lacks verification paths.
2. **Synchronous File Parsing:** Excel ingestion (`ExcelIntakeService`) runs synchronously within the FastAPI request-response thread. Ingesting large files blocks the worker loop, leading to gateway timeouts.
3. **Flat Profile Snapshots:** The `StartupProfileVersion` model stores the entire profile state as a raw JSON blob (`profile_snapshot`). This design prevents relational querying, indexing, and historical diff tracking of individual fields.
4. **Simplistic PDF Generation:** The ReportLab PDF generator (`pdf.py`) builds reports synchronously in memory. The layout is hardcoded to a simple structure (Innovation, Market, Execution) and cannot dynamically adapt to the complex multi-page reports required by the TAES v1.0 standard.
5. **No Graph or Vector Support:** The platform lacks a vector store or graph database interface. The database cannot capture complex entity relationships (like competitors or founders) or conduct semantic search over extracted startup documents.

---

## 4. Technical Debt

1. **Hardcoded Evaluation Logic in Profiles:** The profile generator (`startup_profiles/agent.py`) contains manual Python scoring rules (e.g., checks if `solution_summary` exists and adds 3 points to `innovation_score`). This rule-based logic is coupled to the profile agent service instead of reading from the `evaluations` rubric database.
2. **Disabled Token Authentication:** Route files (e.g., `/intake/upload-applications` and `/startups/{id}/assess`) contain comments noting that OAuth2/JWT token verification has been bypassed or stubbed out due to Swagger UI integration conflicts.
3. **Lack of Domain-Specific Exceptions:** Services raise generic database exceptions or return HTTP status errors directly, rather than using structured custom exceptions.
4. **Incomplete Document Status Transitions:** The document upload pipeline creates records in the `documents` table but leaves processing statuses (e.g., `DocumentProcessingStatus.PARSED`) as placeholders or requires manual API updates. No automated OCR or parsing pipeline is registered.
5. **Limited Frontend Error Boundaries:** The frontend lacks component-level error boundaries, causing network or API formatting errors to crash entire views.

---

## 5. Scalability Issues

1. **SQLite Database Limitations:** SQLite locks the entire database file during writes. In a multi-tenant or concurrent SaaS environment, simultaneous excel uploads or AI evaluations will result in `Database locked` or query timeout errors.
2. **Blocking Network Calls:** The LiteLLM gateway calls models synchronously within the route handlers. Under high traffic, long LLM inference times (often 5–20 seconds) block event loops and exhaust server connection pools.
3. **Synchronous PDF Generation:** Building PDF files in memory via ReportLab during a GET request is computationally heavy. If multiple users attempt to export large evaluation reports simultaneously, the backend CPU utilization will spike, slowing down API performance.
4. **Monolithic Data Loading:** The `/rankings` page loads all evaluation results at once. As the number of applications grows from tens to thousands, this will cause memory issues on both the backend (SQL serialization) and the frontend (virtual DOM rendering).
5. **No Event Bus or Message Queue:** The platform lacks a message broker (e.g., Redis or RabbitMQ) and asynchronous task execution framework (e.g., Celery). There is no mechanism to handle long-running, multi-step AI orchestrations in the background.

---

## 6. Performance Bottlenecks

```
[Incoming Request] ──> [FastAPI Route] ──> [LiteLLM Sync Call (5-20s)] ──> [DB Write] ──> [Response]
                                               |
                                     (Blocks Event Loop)
```

1. **Synchronous AI Inference:** The LiteLLM gateway does not support async completions (`complete_json` is synchronous). This is the single largest performance bottleneck.
2. **Unindexed JSON Fields:** Querying keys within `StartupProfileVersion.profile_snapshot` or `AIAssessmentRecord.strengths` requires full table scans because these JSON fields are not indexed.
3. **Inline OCR & Document Text Extraction:** Extracting text from uploaded PDFs/Word files is done inline during the upload request. If the document is large or requires OCR, the client connection will time out.
4. **Inefficient N+1 Queries:** The evaluations service fetches scores, criteria, evidence, and documents via multiple sequential queries instead of using optimized eager loading (`joinedload` or `subqueryload`).

---

## 7. Database Design Audit

The existing database contains the following tables:

| Table Name | Primary Purpose | Key Weakness / Risk |
| :--- | :--- | :--- |
| `users`, `roles` | Authentication and user RBAC. | Simple RBAC schema; does not support multi-tenant organization levels. |
| `audit_logs` | System audit trails. | Stores detail payloads as string representations instead of structured JSON columns. |
| `startup_applications` | Holds raw intake entries. | Stages are hardcoded text. Does not contain structural sector categorization. |
| `founders` | Tracks founder records. | Flat records. Gaps in experience, education, and credentials columns. |
| `company_profiles` | Incorporations and team size. | Unstructured summaries. Gaps in revenue and IP status details. |
| `documents` | Tracks file paths. | `parsed_text` is stored in a single large text column, leading to heavy index retrieval. |
| `document_sources` | Maps document sections. | Lacks versioning or link association to specific parsed text paragraphs. |
| `evaluations` | Stores score summaries. | Relies on single-stage evaluations; no support for multi-version assessments. |
| `evaluation_scores` | Breakdown of rubric items. | Highly coupled to active evaluation records. No historical revision logging. |
| `evaluation_evidence` | Text citations for scores. | Citations are plain text; lacks vector coordinate or section index mappings. |
| `recommendation_rules` | Outcome mapping rules. | Rules are global; cannot be configured per sector, stage, or tenant. |
| `reviewer_comments` | Reviewer notes. | Flat structure; does not support threads or replies. |
| `score_overrides` | Audit overrides. | Tracks target score changes but does not link back to source evidence. |

---

## 8. AI Integration Review

1. **LiteLLM Gateway:** The integration is functional, wrapping `litellm.completion` and managing exponential backoff retries. However, it lacks support for async operations.
2. **Missing Token Tracking:** The gateway does not log prompt tokens, completion tokens, or cumulative API costs. This prevents cost monitoring, budget tracking, or optimization per cohort.
3. **Hardcoded Prompt Structure:** Prompts are built dynamically using f-strings inside the service layer (`agent.py`). This couples system prompts to backend logic, preventing updates without redeploying code.
4. **Lack of Model Fallbacks:** The gateway does not implement fallback model routing. If the primary API provider (e.g., Anthropic) is down, the system raises an exception rather than failing over to an alternative provider (e.g., Azure OpenAI or Google Vertex AI).

---

## 9. Future Constraints & SaaS Evolution

1. **Multi-Tenancy Isolation:** Evolving TIDES into a multi-tenant SaaS requires complete data isolation. Every table must support an `organization_id` column, and database queries must enforce tenant filters to prevent data leaks.
2. **PostgreSQL Migration:** Evolving to PostgreSQL requires modifying SQLite-specific column declarations (like native JSON handling vs SQLite JSON text representation) and handling dialect-specific transaction behaviors.
3. **API Rate Limiting:** The platform currently has no rate-limiting middleware. A SaaS model will require tenant-level rate limiting to prevent API abuse and control LLM costs.
4. **Compliance & Privacy:** Document processing will intake sensitive intellectual property, pitch decks, and financial audits. The system must support data retention, encrypted storage at rest, and audit logs that comply with regional regulations (GDPR, DPDPA).
5. **Cost Allocation:** Running multi-agent evaluations is resource-intensive. The system must track usage per organization to enable usage-based billing or cohort quota enforcement.
