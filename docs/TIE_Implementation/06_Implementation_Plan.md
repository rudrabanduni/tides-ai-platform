# Implementation Plan: TIDES Intelligence Engine (TIE)

> **Document:** TIE Integration / Implementation Plan  
> **Classification:** Internal Engineering Standard  
> **Version:** 1.0.0  
> **Date:** June 24, 2026

This document presents the engineering roadmap for integrating the TIDES Intelligence Engine (TIE) into the existing TIDES AI Startup Evaluation Platform. It breaks down the implementation into five milestones, detailing files affected, backend and frontend tasks, database modifications, testing plans, rollback strategies, and success criteria.

---

## 1. Milestone Roadmap Overview

```
                  +-----------------------------------+
                  |   Milestone 1: Database & OCR     |
                  |     (PostgreSQL & Async Ingest)   |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  |   Milestone 2: Orchestration      |
                  |     (TIE Core State Machine)      |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  |   Milestone 3: Domain Agents      |
                  |     (Evaluation & Scoring)        |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  |   Milestone 4: Normalisation      |
                  |     (Sector & Recommendation)     |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  |   Milestone 5: UI & PDF Reports   |
                  |     (Frontend & PDF Renderer)     |
                  +-----------------------------------+
```

---

## 2. Milestone Details

### 2.1 Milestone 1: Database Setup & Document OCR Pipeline (Foundations)
*   **Objective:** Set up PostgreSQL database models, integrate Redis for caching, and implement asynchronous document processing.
*   **Files Affected:**
    - `app/core/config.py` (database connections, Redis configurations)
    - `app/db/session.py` (PostgreSQL engine setup)
    - `app/modules/documents/service.py` (OCR integration)
    - `app/modules/documents/models.py` (document storage)
*   **Backend Modules:** `app.core`, `app.db`, `app.modules.documents`
*   **Frontend Modules:** None (Infrastructure phase)
*   **Database Changes:** Migrate current SQLite schema to PostgreSQL. Generate Alembic migrations for new document tables.
*   **Testing:** Unit tests verifying document upload limits, text extraction, and connection pooling performance.
*   **Rollback Strategy:** Revert Alembic migrations to restore previous SQLite database compatibility and reset the database connection string.
*   **Estimated Complexity:** Medium
*   **Dependencies:** Dockerized PostgreSQL and Redis.
*   **Risk:** Medium (Potential schema migration compatibility issues between SQLite and PostgreSQL).
*   **Success Criteria:**
    - Document uploads process asynchronously without blocking the client thread.
    - Extracted plain text is parsed and saved correctly in PostgreSQL.
    - Alembic migration scripts run successfully.

---

### 2.2 Milestone 2: Multi-Agent Orchestrator & Logging Layer (TIE Core)
*   **Objective:** Build the core TIE State Machine, implement parallel task group execution, and add run logging support.
*   **Files Affected:**
    - `app/services/ai/gateway.py` (async LiteLLM gateway support)
    - `app/services/ai/litellm.py` (async completions implementation)
    - `app/services/ai/orchestrator.py` [NEW] (TIE DAG State Machine)
    - `app/services/ai/models.py` [NEW] (orchestrator schemas)
    - `app/modules/evaluations/models.py` (adding agent runs logging relationship)
*   **Backend Modules:** `app.services.ai`, `app.modules.evaluations`
*   **Frontend Modules:** None
*   **Database Changes:** Add `tie_agent_runs` table via Alembic migration.
*   **Testing:** Mock testing of Orchestrator state transitions, error retry limits, and run logging details.
*   **Rollback Strategy:** Disable async gateway flags in `app/core/config.py` and run Alembic rollback for `tie_agent_runs`.
*   **Estimated Complexity:** High
*   **Dependencies:** Milestone 1 complete.
*   **Risk:** Medium (Handling concurrent LLM requests and rate limits).
*   **Success Criteria:**
    - The Orchestrator runs dummy agent tasks concurrently using asyncio.
    - Gateway failures trigger exponential backoffs.
    - Agent execution details (token count, cost, latency) log correctly in the database.

---

### 2.3 Milestone 3: Specialized Domain Evaluation Agents & Rubric Updates
*   **Objective:** Develop the core domain evaluation agents and update database rubrics to match the 8 scoring pillars.
*   **Files Affected:**
    - `app/services/ai/agents/founder.py` [NEW] (Founder Agent business logic)
    - `app/services/ai/agents/product.py` [NEW] (Product Agent business logic)
    - `app/services/ai/agents/market.py` [NEW] (Market Agent business logic)
    - `app/services/ai/agents/financial.py` [NEW] (Financial Agent business logic)
    - `app/services/ai/agents/ip.py` [NEW] (IP/Patent Agent business logic)
    - `app/services/ai/agents/risk.py` [NEW] (Risk Agent business logic)
    - `app/modules/evaluations/service.py` (saving agent-derived scores)
*   **Backend Modules:** `app.services.ai`, `app.modules.evaluations`
*   **Frontend Modules:** None
*   **Database Changes:** Populate `evaluation_rubrics` and `evaluation_criteria` tables with updated TAES v1.0 standard criteria.
*   **Testing:** Validate agent scoring accuracy using mock data, and test that scores and evidence link correctly in evaluations.
*   **Rollback Strategy:** Delete new criteria records from `evaluation_criteria` and restore the legacy single-agent service configuration.
*   **Estimated Complexity:** High
*   **Dependencies:** Milestone 2 complete.
*   **Risk:** High (Ensuring LLMs return valid JSON formats matching Pydantic schemas).
*   **Success Criteria:**
    - All 8 domain-specific agents run successfully and log scores in the database.
    - Every score contains cited evidence referencing source documents.

---

### 2.4 Milestone 4: Normalization Engine & Recommendation System
*   **Objective:** Implement sector-specific normalizations and update the recommendation engine to evaluate multi-pillar scoring inputs.
*   **Files Affected:**
    - `app/services/ai/normalization.py` [NEW] (normalization formulas)
    - `app/modules/recommendation_rules/service.py` (rule matching updates)
    - `app/modules/evaluations/service.py` (save normalized score ratings)
*   **Backend Modules:** `app.modules.recommendation_rules`, `app.modules.evaluations`
*   **Frontend Modules:** None
*   **Database Changes:** Add `sector_benchmarks` and `evaluation_cohorts` tables. Add normalization columns to `evaluations`.
*   **Testing:** Validate normalization output using mock scores, and test rule matching logic for correct outputs.
*   **Rollback Strategy:** Revert database modifications and update configurations to skip normalization calculations, using raw scores directly.
*   **Estimated Complexity:** Medium
*   **Dependencies:** Milestone 3 complete.
*   **Risk:** Medium (Ensuring normalization statistics do not distort startup scores).
*   **Success Criteria:**
    - Normalized scores calculate correctly based on cohort metrics.
    - Recommendation routing identifies and flags risks correctly.

---

### 2.5 Milestone 5: Enterprise PDF Generator, Cohort Dashboard & Admin Approvals
*   **Objective:** Update the ReportLab engine to generate 6-page reports, modify frontend rankings pages, and add human approval screens.
*   **Files Affected:**
    - `app/services/report/pdf.py` (ReportLab layout update)
    - `tides-ai-frontend/src/app/evaluations/page.tsx` (evaluation details view)
    - `tides-ai-frontend/src/app/rankings/page.tsx` (cohort filters, leaderboard view)
    - `tides-ai-frontend/src/app/startups/[id]/page.tsx` (profile update view)
*   **Backend Modules:** `app.services.report`, `app.modules.reviews`
*   **Frontend Modules:** `/evaluations`, `/rankings`, `/startups/[id]`
*   **Database Changes:** None
*   **Testing:** End-to-end integration tests verifying PDF rendering, rankings filters, and review approvals.
*   **Rollback Strategy:** Revert frontend pages to previous code commits and restore the simple 1-page PDF layout script.
*   **Estimated Complexity:** Medium
*   **Dependencies:** Milestone 4 complete.
*   **Risk:** Low (Aesthetic adjustments in PDF rendering and UI page layouts).
*   **Success Criteria:**
    - The PDF generator outputs a 5-6 page report matching the TAES v1.0 standard.
    - The rankings page displays leaderboards sorted by normalized scores.
    - Reviewers can approve or override scores in the UI.

---

## 3. Recommended Implementation Sequence

Engineering should implement the milestones in the following order:

```
[Phase 1: Foundations] ──► [Phase 2: Core TIE] ──► [Phase 3: Domain Agents] ──► [Phase 4: Optimization] ──► [Phase 5: UI Integration]
     (Milestone 1)             (Milestone 2)             (Milestone 3)             (Milestone 4)              (Milestone 5)
```

1.  **Phase 1: Foundations (Milestone 1)** - Must be done first to establish the PostgreSQL database schema and asynchronous document storage, which are required for document parsing.
2.  **Phase 2: Core TIE (Milestone 2)** - Implements the state orchestrator and API logging framework before adding domain-specific agents.
3.  **Phase 3: Domain Agents (Milestone 3)** - Deploys specialized agents to calculate scores, populating the database structure set up in Phase 2.
4.  **Phase 4: Optimization (Milestone 4)** - Adds normalization and cohort calculations on top of domain agent scores.
5.  **Phase 5: UI Integration (Milestone 5)** - Once all backend data processing layers are verified, update the frontend views and PDF generation tools to render the data.
