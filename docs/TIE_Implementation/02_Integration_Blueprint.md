# Integration Blueprint: TIDES Intelligence Engine (TIE)

> **Document:** TIE Integration / Integration Blueprint  
> **Classification:** Internal Engineering Standard  
> **Version:** 1.0.0  
> **Date:** June 24, 2026

This document maps out the integration points for the TIDES Intelligence Engine (TIE) within the existing TIDES AI codebase. It outlines how the current modules, services, and routes will be evolved without replacing their existing structures, establishing a progressive, non-destructive migration path.

---

## 1. Module Integration Map

The TIDES Intelligence Engine (TIE) integrates as a orchestration layer that sits on top of the repository layer, communicating with external model APIs via the LiteLLM gateway, and storing structured evidence and score results within the existing relational database.

```
       +--------------------------------------------------------+
       |                  TIE Orchestrator                      |
       |  (Manages multi-agent execution, routing, & state DAG) |
       +----+-----------------+------------------+--------------+
            |                 |                  |
            v                 v                  v
     +------------+    +------------+    +---------------+
     | Knowledge  |    |  Evidence  |    | Normalisation |
     | Extraction |    |   Engine   |    |    Engine     |
     +-----+------+    +-----+------+    +-------+-------+
           |                 |                   |
           v                 v                   v
+------------------+ +-----------------+ +---------------+
| Document Service | | Evaluation Serv | | Recomm Service|
| & parsed_text    | | & criteria db   | | & Rules DB    |
+------------------+ +-----------------+ +---------------+
```

---

## 2. Integration Details by Module

### 2.1 Intake & Upload Pipeline
*   **Current Behaviour:** Accepts an Excel spreadsheet via `POST /api/v1/intake/upload-applications`. The `ExcelIntakeService` parses the spreadsheet synchronously using `openpyxl`, validating rows and creating `StartupApplication`, `Founder`, `StartupProfile`, and `StartupProfileVersion` (v1) records.
*   **Future Behaviour:** Retains the Excel upload. In addition, it supports multi-file ZIP or raw document uploads (pitch decks, business plans, financials) per startup. Upon successful creation of database records, the pipeline publishes an event (e.g., `STARTUP_RECORD_CREATED`) to trigger background document processing and AI extraction asynchronously.
*   **Required Changes:**
    - Update `ExcelIntakeService` to emit asynchronous tasks (using Python's `asyncio.create_task` or a background task queue) rather than executing parsing steps inline.
    - Expose a multi-document upload route under `app/modules/documents/routes.py` that associates uploaded PDFs/documents with the newly created `StartupApplication` ID.
*   **Expected Benefits:** Removes synchronous bottlenecks. Users get immediate feedback on upload status while document processing runs in the background.
*   **Migration Difficulty:** Low
*   **Risk Level:** Low
*   **Dependencies:** `app.modules.documents`, `app.modules.startups`

---

### 2.2 Document Processing & Storage
*   **Current Behaviour:** Files are stored in a local directory (`settings.upload_dir`). Metadata is persisted in the `documents` table, and `parsed_text` is saved as a single plain text field when updated via API.
*   **Future Behaviour:** Uploaded documents are queued for asynchronous processing. An extraction agent parses the document structure (extracting headings, sections, page coordinates, and tables) and stores the parsed structure along with text block coordinates.
*   **Required Changes:**
    - Integrate an asynchronous worker task in `DocumentService` that triggers when a file is uploaded.
    - Implement a text segmentation utility to split parsed text into logical blocks (paragraphs, sections) for chunking.
    - Add support for indexing document text blocks with metadata (e.g., page numbers, section headers) to enable targeted evidence sourcing.
*   **Expected Benefits:** Structured text chunks allow downstream AI agents to quote specific sections, pages, and context paragraphs rather than referencing the whole file.
*   **Migration Difficulty:** Medium
*   **Risk Level:** Medium
*   **Dependencies:** `app.modules.documents`, `app.services.ai`

---

### 2.3 Startup Profiles & Versioning
*   **Current Behaviour:** `StartupProfileService` performs simple CRUD operations on startup details. On every update, it creates a new `StartupProfileVersion` by serializing the fields into a JSON snapshot (`profile_snapshot`).
*   **Future Behaviour:** Profile generation is initiated by the Knowledge Extraction Agent. The agent extracts details from unstructured documents and populates the profile fields (e.g., problem statement, solution, market size). The versioning system records whether fields were filled by user import, AI extraction, or manual human editing.
*   **Required Changes:**
    - Extend `StartupProfilePayload` and the `StartupProfile` model with metadata fields (e.g., `extracted_by_agent_id`, `extraction_confidence`, `last_verified_by`).
    - Update `StartupProfileService.upsert` to allow partial updates of fields during the multi-agent extraction phase without overwriting existing, human-verified data.
*   **Expected Benefits:** Dynamic profile generation that automatically digests new documents and maintains audit histories for every field.
*   **Migration Difficulty:** Medium
*   **Risk Level:** Low
*   **Dependencies:** `app.modules.startup_profiles`, `app.modules.documents`

---

### 2.4 Evaluations & Scoring Pipeline
*   **Current Behaviour:** `EvaluationService` manages evaluations, scoring criteria, and evidence. Rubrics are created manually. final scores are calculated by averaging criteria weights. `StartupProfileAgentService` runs a basic evaluation script that checks field presence or calls a single LLM completion route to populate scores.
*   **Future Behaviour:** The evaluation pipeline executes a DAG of specialized agents (Founder, Product, Market, Finance, IP, etc.) orchestrated by TIE. The agents fetch criteria and rubrics from `evaluation_rubrics` and write structured scores and text evidence back to `evaluation_scores` and `evaluation_evidence`.
*   **Required Changes:**
    - Replace the single-agent call in `StartupProfileAgentService.evaluate_startup_with_ai` with an invocation of the TIE Orchestrator.
    - Evolve `EvaluationService.add_score` and `finalize` to handle asynchronous score arrivals from concurrent agents.
    - Ensure `EvaluationEvidence` records are automatically populated with direct citations, including page numbers, section headers, and snippet texts.
*   **Expected Benefits:** Transition to specialized, multi-perspective assessments that comply with the rigorous TAES standard.
*   **Migration Difficulty:** High
*   **Risk Level:** High
*   **Dependencies:** `app.modules.evaluations`, `app.modules.startup_profiles`, `app.services.ai`

---

### 2.5 Recommendation Engine
*   **Current Behaviour:** `RecommendationRuleService` finds matching recommendation records based on the overall evaluation score threshold (e.g., if overall score is > 70%, recommend "Incubate").
*   **Future Behaviour:** The Recommendation Agent runs after all scoring agents complete. It consumes the multi-pillar score matrix, confidence scores, and identified red flags. It then applies rule-based decision trees and normalizations to output a structured recommendation with clear conditions.
*   **Required Changes:**
    - Evolve `RecommendationRuleService` to support multi-variable rules (e.g., matching on stage, sector, and risk flags, in addition to overall score).
    - Update `Evaluation.recommendation` to store structured recommendation metadata (conditions, timeline, and risk mitigations) in a JSON configuration rather than a simple string.
*   **Expected Benefits:** Recommendations adapt to the startup's lifecycle stage and industry, preventing generic "yes/no" results.
*   **Migration Difficulty:** Medium
*   **Risk Level:** Medium
*   **Dependencies:** `app.modules.recommendation_rules`, `app.modules.evaluations`

---

### 2.6 Reviews, Overrides & Comments
*   **Current Behaviour:** Humans add reviewer comments or override scores. The `ScoreOverride` model tracks the original score, new score, and override reason. Overriding recalculates the overall score.
*   **Future Behaviour:** Reviewers can inspect the specific evidence chunks cited by the AI. When overriding a score, the reviewer can link their change to a specific document source or log an evidence discrepancy, which is fed back to the AI orchestration layer for system tuning.
*   **Required Changes:**
    - Update `ScoreOverride` model to include optional relationships to `DocumentSource` or `EvaluationEvidence` IDs.
    - Create a route in `app/modules/reviews/routes.py` that allows reviewers to tag specific AI evidence citations as "invalid" or "accurate."
*   **Expected Benefits:** Establishes a closed feedback loop that records human feedback to improve agent performance over time.
*   **Migration Difficulty:** Low
*   **Risk Level:** Low
*   **Dependencies:** `app.modules.reviews`, `app.modules.evaluations`

---

### 2.7 Dashboard & Rankings
*   **Current Behaviour:** Frontend lists startups, basic metrics, and overall scores in a table. It allows simple ranking based on overall scores.
*   **Future Behaviour:** Frontend displays cohort leaderboards with multi-pillar score distributions, normalizations, and sector benchmark comparisons. It allows filtering startups by stage, technology readiness level (TRL), sector, and overall confidence scores.
*   **Required Changes:**
    - Update backend routes (`app/modules/dashboard/routes.py` and `app/modules/evaluations/routes.py`) to return paginated lists containing full score matrices, confidence scores, stages, and normalized benchmark rankings.
    - Modify the frontend `/rankings` page to render interactive radar charts and normalizations.
*   **Expected Benefits:** Provides program directors with clear cohort analytics, making it easy to identify top performers and outliers.
*   **Migration Difficulty:** Medium
*   **Risk Level:** Low
*   **Dependencies:** `app.modules.dashboard`, `app.modules.evaluations`

---

### 2.8 Report Generation & PDF Renderer
*   **Current Behaviour:** `pdf.py` renders a 1-2 page ReportLab document displaying Innovation, Market, Execution scores, strengths, weaknesses, and recommendations.
*   **Future Behaviour:** Generates a 5-6 page report conforming to the `TAES v1.0 / Report Standard`, including an executive dashboard, spider charts, detailed pillar tables, founder credentials, competitive analyses, and risk matrices.
*   **Required Changes:**
    - Refactor `app/services/report/pdf.py` to use a modular, multi-page layout engine.
    - Incorporate standard ReportLab drawing tools to generate dynamic radar charts representing the 8-pillar score matrix.
    - Change the PDF generation route to run asynchronously, returning a processing status and caching generated PDFs.
*   **Expected Benefits:** Professional, investor-ready evaluation documents matching the official TAES v1.0 guidelines.
*   **Migration Difficulty:** High
*   **Risk Level:** Medium
*   **Dependencies:** `app.services.report`, `app.modules.evaluations`

---

## 3. Backward Compatibility & Evolution Guardrails

To prevent breaking existing configurations during the TIE integration, the following guardrails must be enforced:

1. **Non-Destructive DB Schema Changes:** Do not rename or delete existing columns. New attributes must be added as nullable columns or separated into new tables linked by foreign keys.
2. **Endpoint Versioning:** The existing endpoint `/api/v1/startups/{id}/assess` must remain active and functional, using the legacy single-agent logic if necessary. TIE evaluations must be exposed under a new route path (e.g., `/api/v1/startups/{id}/evaluate-tie`).
3. **Preserve Manual Upload Flow:** The spreadsheet intake format cannot be modified. The Knowledge Extraction Agent must parse the same columns, adding document parsing as an optional, secondary step.
4. **Graceful Fallbacks:** If the multi-agent engine fails due to API limits or context errors, the system must degrade gracefully by falling back to the rule-based scoring module, ensuring the client receives a valid evaluation score.
