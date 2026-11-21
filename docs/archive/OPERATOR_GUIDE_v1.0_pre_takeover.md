# TIDES-AI Operator & Developer Guide

This document provides a verified operational and engineering manual for the TIDES-AI due-diligence platform. All file paths, symbols, commands, and limits below reflect the actual codebase state audited offline through 2026-11-12.

---

## 1. System Architecture

TIDES-AI is an agentic venture-capital due-diligence evaluation platform tailored for deep-tech and early-stage startup incubation.

```
[Uploaded Documents] (PDF, Pitch Decks, Application Forms, CVs)
         │
         ▼
[Staged Document Extractor] ──► Extracts canonical profile claims across 10 stages (live pilot config)
         │
         ▼
[Observation Graph (DAG)] ──► Nodes: Evidence, Claims, Risks, Decisions
         │
         ├──► Domain Specialist 1: Problem & Solution (PS: 13 criteria)
         ├──► Domain Specialist 2: Market Opportunity (MO: 10 criteria)
         ├──► Domain Specialist 3: Founder & Team Capability (FT: 13 criteria)
         ├──► Domain Specialist 4: Business Model & Commercialisation (BC: 13 criteria)
         ├──► Domain Specialist 5: Innovation, IP & Impact (II: 11 criteria)
         └──► Domain Specialist 6: Financials & Incubation Support (FI: 21 criteria)
         │
         ▼
[Supervisory Reviewer] ──► Cross-domain reconciliation & contradiction detection
         │
         ▼
[Investment Diligence & Committee] ──► Multi-body verdicts (e.g., WATCHLIST, CONDITIONAL, SEEK_MORE_INFORMATION)
         │
         ▼
[Report Engine] ──► Dynamic, startup-agnostic synthesis (11 mandatory sections)
         │
         ▼
[Report Validator] ──► Completeness, traceability, cross-contamination, and governance audit
         │
         ▼
[Handoff Exporter] ──► JSON review package + Markdown report
```

### Core Components
- **API Server**: FastAPI exposed via `app/main.py` (re-exporting `app` from `app/api/main.py`), Pydantic v2 schemas.
- **Workflow Engine**: State machine with thread-safe transition locking (`_transition_lock = threading.Lock()` wrapping `execute_transition` and `rollback_workflow` in `app/modules/workflow/workflow_engine.py`).
- **AI Gateway**: `create_ai_gateway` in `app/services/ai/gateway.py` routing between `LiteLLMGateway` (`app/services/ai/litellm.py`, providers `"litellm"` or `"anthropic"`) and offline `MockAIGateway` (`app/services/ai/mock.py`, provider `"mock"`).
- **Knowledge Graph**: Observation Graph DAG (`app/modules/evaluation/graph/`).
- **Frontend**: Next.js 15.1.0 (`next: 15.1.0`), React 19.0.0, Tailwind CSS (`frontend/`).

---

## 2. Evaluation Flow

1. **Intake & PII Sanitization**: Startup application metadata and submitted source materials are registered; `app/modules/intelligence/pii_sanitizer.py` scrubs Aadhaar numbers, phone numbers, email addresses, and sensitive application columns before prompts/exports.
2. **Staged Extraction**: In the controlled evaluation orchestrator (`app/modules/ai/orchestrator/pipeline.py`, `startup_profile_extraction.py`, and `extraction_checkpoint.py`), documents are parsed across 10 bounded extraction stages (`2,400` output tokens for Stages 1–9; `4,096` output tokens for Stage 10 `financials_support`; `25,696` total cap) with atomic per-stage checkpointing (`uploads/extraction_checkpoints/{startup_id}_{evaluation_id}.json`).
3. **Canonical Profile & Claims**: Assertions are stored as structured claims linked to source provenance and evidence snippets.
4. **Observation Graph Assembly**: Directed edges link evidence citations to claims, risks, assessments, and committee decisions.
5. **Specialist Evaluation**: 6 canonical domain specialists evaluate the 81 domain criteria across PS, MO, FT, BC, II, and FI.
6. **Supervisory Review**: Reconciles contradictions and missing evidence across the 6 domains without fabricating findings.
7. **Investment Diligence & Committee Synthesis**: Generates viability metrics and institutional decisions while preserving distinct institutional roles.
8. **Report Generation**: `DueDiligenceReportEngine` (`app/modules/evaluation/report/report_engine.py`) compiles structured markdown and JSON reports dynamically from the startup's observation graph without hardcoded startup prose.
9. **Automated Validation**: `ReportValidator` (`app/modules/evaluation/report/report_validator.py`) audits section completeness, traceability, referential integrity, recommendation consistency, and cross-startup contamination.
10. **Handoff Packaging**: Review packages in `reports/hand_off/` provide structured JSON and Markdown dossiers.

---

## 3. Canonical 87-Criterion Rubric

The canonical directory in `app/modules/evaluation/domains/registry.py` (`CRITERIA_DIRECTORY`) defines **87 criteria** (`6` cover/intake + `81` domain criteria):
- **Intake / Cover Metadata (`intake_completeness`, CM-01 to CM-06)**: **6 criteria** (company name, tagline, sector, stage, geography, submission date).
- **Domain 1 — Problem & Solution (`problem_solution`, PS-01 to PS-13)**: **13 criteria** (core problem, persona, workarounds, pain metrics, persistence barrier, solution, features/benefits, UVP, TRL, demo link, maturity stage, architecture, lab validation).
- **Domain 2 — Market Opportunity (`market_opportunity`, MO-01 to MO-10)**: **10 criteria** (TAM/SAM/SOM, CAGR & citations, drivers, geographic focus, 3 competitors, moat).
- **Domain 3 — Founder & Team Capability (`founder_team`, FT-01 to FT-13)**: **13 criteria** (founder identity/LinkedIn/education/experience/exits, co-founders, core team, self-identified skill gaps, hiring plan, mentors/advisors, institutional affiliations).
- **Domain 4 — Business Model & Commercialisation (`commercialisation`, BC-01 to BC-13)**: **13 criteria** (business model, pricing, GTM channels, CAC, gross margin, payback, path to first ₹10L/$10k, users/paying customers, revenue, pilots/LOIs, awards/grants, research validation, customer feedback).
- **Domain 5 — Innovation, IP & Impact (`innovation_impact`, II-01 to II-11)**: **11 criteria** (tech moat, data flywheel, network effects, switching costs, brand moat, regulatory barriers, IP status, primary impact, UN SDGs, KPIs, negative externality risks).
- **Domain 6 — Financials & Incubation Support (`financials_support`, FI-01 to FI-21)**: **21 criteria** (3-year forecasts, monthly cash burn, break-even timing, unit assumptions, external funding, opex breakdown, lab/faculty/corporate/legal/trial-bed/training support needs, 6-quarter roadmaps, representative/declaration).

---

## 4. Evidence Provenance & Discipline

Strict evidentiary rules are enforced by `app/modules/evaluation/domains/base.py`:
1. **Documented Evidence (`VERIFIED_DOCUMENTED`)**: Assigned when supported by evidence objects containing a non-null `evidence_snippet`.
2. **Self-Reported Claims (`SELF_REPORTED_ONLY`)**: Assertions lacking independent or authentic evidence snippets.
3. **Missing Information Discipline (`MISSING_INFORMATION` / `NOT_APPLICABLE`)**: Absence of evidence is flagged as missing (`score=None`) or conditional not-applicable, never fabricated into negative evidence.
4. **Provenance Demotion Guard**: In `CanonicalDomainExpert.build_criterion_assessments_from_compact` (`app/modules/evaluation/domains/base.py`), if a specialist returns `VERIFIED_DOCUMENTED` while attached `ev_list` evidence objects all have `evidence_snippet is None`, the status is automatically downgraded to `SELF_REPORTED_ONLY`.
5. **Contradiction Flag (`CONTRADICTED`)**: Used when submitted evidence conflicts internally or against domain records.

---

## 5. Database Safety & Isolation

- **Protected Production/Workspace Database**: `tides_ai.db`
  - Canonical SHA-256: `D9659F4E8C1058C5D5F4511E1BB22D3ABE6CB12101C16CE397416051A38176C7`
  - **Rule**: Never run automated tests, dev servers, or pilot runners against `tides_ai.db`.
- **Dedicated Development Database**: `tides_dev.db`
  - Default `Settings.database_url` (`app/core/config.py`), `.env`, `.env.example`, `scripts/init_dev_db.py`, `scripts/run_dev_backend.py`, `scripts/run_dev_backend.ps1`, `scripts/run_one_time_live_eval.py`, and `scripts/run_live_eval.ps1` all target `tides_dev.db`.
  - Fail-closed guards (`resolve_sqlite_db_path`, `validate_database_configuration`, and `@model_validator(mode="after") def _enforce_database_policy` in `app/core/config.py`, invoked on `Settings` construction and `create_app()` in `app/api/main.py`, plus dev script guards) reject `DATABASE_URL` values pointing to `tides_ai.db` across all environments.
- **Production Environment Guardrails (`.env.production.example`)**:
  - When `APP_ENV=production`, `validate_database_configuration` requires an explicitly configured non-SQLite `DATABASE_URL` and refuses SQLite or `tides_dev.db`, while `create_ai_gateway` (`app/services/ai/gateway.py`) blocks `ai_provider="mock"` (unless `force_mock=True`) and aborts without falling back to `MockAIGateway` if `ANTHROPIC_API_KEY` is missing.
  - `.env.production.example` provides a zero-secret template (`APP_ENV=production`, `AI_ENABLED=true`, `AI_PROVIDER=anthropic`, `AI_MAX_EVALUATION_BUDGET_USD=0.35`, `AI_MAX_RETRIES=0`, `RESEARCH_PROVIDER=disabled`, blank API keys, PostgreSQL placeholder).
- **Pytest Isolation (`tests/conftest.py`)**:
  - Creates a temporary directory (`tempfile.mkdtemp(prefix="tides_test_db_")`) with `isolated_test_tides.db` and sets `os.environ["DATABASE_URL"]` before importing app DB sessions.
  - Session fixture `enforce_database_isolation` and autouse fixture `isolate_test_environment` restore env vars, clear `get_settings` cache, and assert byte-for-byte SHA-256 preservation of `tides_ai.db` (`tests/test_database_isolation.py`).

---

## 6. Budget Enforcement & Cost Governance

- **Production Evaluation Ceiling (`app/core/config.py`, `app/services/ai/cost_ledger.py`, `scripts/check_live_readiness.py`)**:
  - `AI_MAX_EVALUATION_BUDGET_USD = 0.35` USD (`₹96.0/USD * 1.18 = ₹39.65 INR` buffered vs `₹70.00 INR` hard business ceiling; explicit overrides up to $0.55 supported).
- **Controlled Pilot Runner Ceiling (`scripts/run_one_time_live_eval.py`, `scripts/run_live_eval.ps1`)**:
  - Enforces hard cap of **$0.35 USD** (~`₹39.65 INR` buffered at `96.0` INR/USD x `1.18`).
  - Pre-request reservations check projected costs against remaining headroom via `EvaluationCostLedger` (`app/services/ai/cost_ledger.py`) and raise `AIBudgetExhaustedError` before exceeding the ceiling.
  - Output token caps: 10 extraction stages at `2,400` tokens each (`cover_intake`..`innovation_impact`) plus Stage 10 (`financials_support`) at `4,096` tokens (`25,696` total Haiku cap); canonical domain specialists (`claude-sonnet-5-5`) criterion-batched at `<= 5` criteria/batch and `<= 900` tokens/batch across 19 batches (`problem_solution`: 3, `market_opportunity`: 2, `founder_team`: 3, `commercialisation`: 3, `innovation_impact`: 3, `financials_support`: 5); supervisory reviewer at `2,400` tokens.
  - Cost Model:
    - Typical evaluation: ~$0.1361 USD (~`₹15.42 INR` buffered)
    - Expected evaluation: ~$0.2035 USD (~`₹23.05 INR` buffered)
    - Worst-case evaluation at all token caps: $0.3248 USD (~`₹36.79 INR` buffered), strictly below the $0.35 USD ceiling.
- **Reconciled Telemetry Reference (No Mock Cost Equated to Real Spend)**:
  - **STETHAIM Historical Completed Pilot (`4dae8d45-5da1-4f6d-b964-95138c333c3f`)**: **$0.269917 USD** (`₹30.5762 INR` buffered across 19 `EXACT_REPORTED` ops; subsequent v2.1 offline report regeneration added `$0.00`).
  - **PETREVOLT Partial Live Extraction (`21d60370-d7cf-43d8-9c14-05b0cd5078a2`)**: **$0.012323 USD** (`₹1.3959 INR` buffered across `10` Haiku ops; `9/10` stages succeeded before pre-fix `2,400`-token truncation on `extraction_financials_support`; `$0.337677 USD` remaining of `$0.35` ceiling; downstream domains & supervisory not yet invoked).
  - **PETREVOLT Development/Mock Pilot (`f099fa55...`, with superseded copy `1b5de317...` archived)**: **$0.095286 USD** (`$0.0953` rounded in `PETREVOLT_FINAL_REVIEW_PACKAGE.json`, `ESTIMATED_FROM_TOKENS`, `AI_PROVIDER=mock`), representing **`$0.00 USD` actual provider spend**.
  - See `reports/FINAL_PRODUCT_READINESS_REPORT.md` for full reconciliation including historical CleanPower Systems and earlier aborted extraction attempts.

---

## 7. Recovery System

1. **Targeted Domain Recovery (`recover_failed_domain_evaluation` in `app/modules/ai/orchestrator/pipeline.py`)**:
   - Loads persisted graph checkpoint (`uploads/graphs/<startup_id>.json`) and metadata/run telemetry to restore cumulative prior spend into the cost ledger.
   - Verifies evaluation ID and startup ID prerequisites before dispatching any model request (`validate_recovery_prerequisites` in `scripts/run_one_time_live_eval.py`).
   - Reassesses only the requested failed domain and reruns supervisory review/report generation.
2. **Targeted Extraction Recovery (`recover_failed_extraction_evaluation` & `extraction_checkpoint.py`)**:
   - Restores cumulative prior spend from `reports/live_eval_run_report.json` or `reports/telemetry/eval_<id>*.json` without resetting the `$0.35` ledger (`_find_cost_summary_for_evaluation` & `_restore_evaluation_cost_ledger`).
   - Selects `CHECKPOINT_RESUME` (reusing saved stage payloads from `uploads/extraction_checkpoints/{startup_id}_{evaluation_id}.json` in place with zero duplicate API calls) when prior stages exist; when prior stages are unrecoverable (as with pre-checkpoint partial run `21d60370-d7cf-43d8-9c14-05b0cd5078a2`), selects `CONTINUATION_REPLACEMENT` — preserving the original attempt untouched as `PRESERVED_PARTIAL_FAILURE`, creating one linked continuation evaluation ID with `parent_evaluation_id` lineage, carrying `$0.012323` prior spend forward into the `$0.35` ledger, and persisting atomic checkpoints going forward.
   - Executes missing/targeted extraction stages (Stage 10 `financials_support` now `4,096` tokens + compact minified JSON instructions), runs `ClaimEngine`, completes all 6 domain specialists + supervisory reviewer, and archives per-evaluation telemetry via `_persist_telemetry_report`.

---

## 8. Dynamic Report Generation

Reports are built deterministically by `DueDiligenceReportEngine` (`app/modules/evaluation/report/report_engine.py`) with models defined in `app/modules/evaluation/report/report_models.py` (`DueDiligenceReport`):
- **11 Mandatory Structured Sections**:
  1. `executive_summary`
  2. `investment_recommendation`
  3. `founder_assessment`
  4. `product_technology`
  5. `market_opportunity`
  6. `business_model`
  7. `competition`
  8. `financial_overview`
  9. `risks`
  10. `investment_thesis`
  11. `follow_up_questions`
- **Multi-Body Institutional Roles Preserved**: Investment Assessment (e.g., `WATCHLIST`), Supervisory Review (e.g., `CONDITIONAL`), and Committee Decision (e.g., `SEEK_MORE_INFORMATION`) remain distinct while reconciling an operational policy without contradictory `DEFER` overrides.

---

## 9. Validation (`ReportValidator`)

`ReportValidator` in `app/modules/evaluation/report/report_validator.py` exposes two classmethods:
- **`ReportValidator.validate(graph)`**: Audits all 11 required sections for presence/minimum content length (`>= 50` chars), confidence bounds `[0.0, 1.0]`, traceability entries, referential integrity of `supporting_nodes`, duplicate section/appendix IDs or titles, domain assessment count parity, stale `final_review` recommendations, and invokes `validate_cross_contamination(graph)`.
- **`ReportValidator.validate_cross_contamination(graph)`**: Enforces sector-specific forbidden term checks (MedTech vs CleanTech/energy), foreign entity mentions (`CleanPower`, `STETHAIM`, `PETREVOLT`), positive MedTech terminology, supervisory rationale/recommendation consistency, governance reconciliation presence, unsupported `clean cap table` / `verified TRL 4` claims, and conflicting `DEFER` narratives.

---

## 10. Handoff Packages

Existing review packages live under `reports/hand_off/`:
- Frozen STETHAIM v2.1 dossier: `reports/hand_off/STETHAIM_FINAL_REVIEW_PACKAGE_v2.1.json` & `.md` (regenerated offline by `scripts/generate_stethaim_handoff_v2_1.py`).
- PETREVOLT mock pilot dossier: `reports/hand_off/PETREVOLT_FINAL_REVIEW_PACKAGE.json` & `.md` (`v1.1.0-reconciled-mock`, `REPORT-1826F99C`, generated from mock-mode pilot data; superseded `1b5de317...` copy archived under `reports/hand_off/archive/`).

---

## 11. Verified Operator Commands

All scripts below were checked against the actual `scripts/` directory and `app/api/routers/evaluation.py` during the 2026-11-11 offline audit. Note that there is **no standalone generic `--file` evaluation CLI script** (`scripts/run_evaluation.py` does not exist).

### A. Non-Destructive Live-Readiness Check (Verified Offline)
Reads runtime configuration (`app/core/config.py`) and `PricingCatalog` without network calls or DB mutations:
```powershell
.venv\Scripts\python.exe scripts/check_live_readiness.py
```
- **Provider / Env**: Inspects `AI_FAST_MODEL`, `AI_REASONING_MODEL`, `RESEARCH_PROVIDER`, `ANTHROPIC_API_KEY`, `TAVILY_API_KEY`, and `$0.55 USD` platform default budget.
- **Database**: Does not connect to or mutate `tides_ai.db` or `tides_dev.db`.
- **Audit Status**: **VERIFIED** (exited `0`, returned `READY_FOR_CREDENTIALS`).

### B. Local Development Database & Backend Server (Mock AI, Verified CLI/Config)
1. Initialize isolated dev database (`tides_dev.db`, refuses `tides_ai.db`):
   ```powershell
   .venv\Scripts\python.exe scripts/init_dev_db.py
   ```
   - **Env/DB**: Sets `DATABASE_URL=sqlite:///<repo>/tides_dev.db` (or `DEV_DATABASE_URL`).
   - **Audit Status**: **VERIFIED** (code inspected; prior run initialized `tides_dev.db` with demo user `analyst@tides.ai` / `password`).

2. Start FastAPI backend in Mock AI Mode (`127.0.0.1:8000`):
   ```powershell
   .\scripts\run_dev_backend.ps1
   # or directly:
   .venv\Scripts\python.exe scripts/run_dev_backend.py --host 127.0.0.1 --port 8000
   ```
   - **Provider / Env**: Forces `DATABASE_URL=sqlite:///<repo>/tides_dev.db`, `AI_PROVIDER=mock`, `AI_ENABLED=true`, `APP_ENV=development`, `RESEARCH_PROVIDER=mock` (`setdefault`), and refuses to run if `DATABASE_URL` points to `tides_ai.db`.
   - **Audit Status**: CLI `--help` **VERIFIED**; interactive daemon server startup not kept running during batch closeout audit.

3. Trigger evaluation on arbitrary uploaded documents via FastAPI REST API (`app/api/routers/evaluation.py`, mounted at `/api/v1` and `/`):
   - **End-to-end multipart upload + pipeline**: `POST /api/v1/evaluate-startup` (form fields `startup_name`, `sector`, `stage`, `files`) -> invokes `coordinate_evaluation_pipeline`.
   - **Queue evaluation for existing startup**: `POST /api/v1/evaluate` (`{"startup_id": "<UUID>"}`) or `POST /api/v1/evaluate/{startup_id}`.
   - **Retrieve graph & reports**: `GET /api/v1/evaluation/{startup_id}`, `GET /api/v1/reports/{startup_id}`, `GET /api/v1/reports/{startup_id}/markdown`, `GET /api/v1/reports/{startup_id}/download`.
   - **Provider / DB**: Uses configured `DATABASE_URL` and `AI_PROVIDER` (`mock` when started via `run_dev_backend.py` or default `.env`).
   - **Audit Status**: Verified in offline mock mode via `pytest` API integration tests; live external-provider HTTP evaluation via these endpoints is **UNVERIFIED (no live API key in environment)**.

### C. Controlled Live Pilot & Recovery Runner (`scripts/run_one_time_live_eval.py` & `scripts/run_live_eval.ps1`)
Verified `--help` supported flags:
`--execute-live`, `--stethaim-pilot`, `--startup-id <UUID>`, `--petrevolt`, `--reuse-startup-id <UUID>`, `--reuse-existing-extraction`, `--recover-evaluation-id <UUID>`, `--recover-startup-id <UUID>`, `--recover-domain <DOMAIN>`, `--recover-extraction-stage <STAGE>` (PowerShell switches `-ExecuteLive`, `-StethaimPilot`, `-StartupId`, `-Petrevolt`, `-ReuseStartupId`, `-ReuseExistingExtraction`, `-RecoverEvaluationId`, `-RecoverStartupId`, `-RecoverDomain`, `-RecoverExtractionStage`).

1. **Dry-Run Mode (Default — 0 API calls, 0 DB mutations, Verified Offline)**:
   ```powershell
   # CleanPower Systems PDF fixture dry-run (default target: tests\fixtures\valid_pitch_deck.pdf)
   .venv\Scripts\python.exe scripts/run_one_time_live_eval.py
   powershell -ExecutionPolicy Bypass -File scripts/run_live_eval.ps1

   # PETREVOLT ENERGY SOLUTIONS PVT LTD dry-run on isolated tides_dev.db (1b5de317-6e56-4dcb-ada9-28ab9adf8c0c)
   .venv\Scripts\python.exe scripts/run_one_time_live_eval.py --petrevolt
   .venv\Scripts\python.exe scripts/run_one_time_live_eval.py --startup-id 1b5de317-6e56-4dcb-ada9-28ab9adf8c0c
   powershell -ExecutionPolicy Bypass -File scripts/run_live_eval.ps1 -Petrevolt

   # STETHAIM multi-document pilot dry-run (requires files in private/pilot_inputs/stethaim)
   .venv\Scripts\python.exe scripts/run_one_time_live_eval.py --stethaim-pilot
   powershell -ExecutionPolicy Bypass -File scripts/run_live_eval.ps1 -StethaimPilot

   # Targeted domain recovery dry-run example
   .venv\Scripts\python.exe scripts/run_one_time_live_eval.py --recover-evaluation-id <EVAL_UUID> --recover-startup-id <STARTUP_UUID> --recover-domain founder_team

   # PETREVOLT targeted extraction recovery dry-run (reads $0.012323 prior spend, projects $0.2822 cumulative <= $0.35)
   .venv\Scripts\python.exe scripts/run_one_time_live_eval.py --recover-evaluation-id 21d60370-d7cf-43d8-9c14-05b0cd5078a2 --recover-startup-id 1b5de317-6e56-4dcb-ada9-28ab9adf8c0c --recover-extraction-stage financials_support
   powershell -ExecutionPolicy Bypass -File scripts/run_live_eval.ps1 -RecoverEvaluationId 21d60370-d7cf-43d8-9c14-05b0cd5078a2 -RecoverStartupId 1b5de317-6e56-4dcb-ada9-28ab9adf8c0c -RecoverExtractionStage financials_support
   ```
   - **Database**: Configured for `tides_dev.db` (protected `tides_ai.db` untouched). Existing-startup runs preserve registered UUIDs and historical assessments without duplicating founders via `coordinate_evaluation_pipeline(..., existing_startup_id=..., max_budget_usd=0.35)`.
   - **Budget Ceiling**: Enforces **$0.35 USD** (~`₹39.65 INR` buffered).
   - **Audit Status**: `--help`, `--petrevolt`, `--startup-id 1b5de317-6e56-4dcb-ada9-28ab9adf8c0c`, `--stethaim-pilot`, PowerShell `-RecoverExtractionStage` & `--recover-evaluation-id 21d60370-d7cf-43d8-9c14-05b0cd5078a2 ...` dry-runs **VERIFIED** offline; `--execute-live` without `ANTHROPIC_API_KEY` verified fail-closed (`exit 1`).

2. **Live Paid Execution & Recovery (Requires Operator Authorization & Interactive Anthropic Key)**:
   ```powershell
   # Securely prompts for ANTHROPIC_API_KEY in-memory, sets AI_PROVIDER=anthropic, clears key on exit
   .\scripts\run_live_eval.ps1 -ExecuteLive -RecoverEvaluationId 21d60370-d7cf-43d8-9c14-05b0cd5078a2 -RecoverStartupId 1b5de317-6e56-4dcb-ada9-28ab9adf8c0c -RecoverExtractionStage financials_support
   .\scripts\run_live_eval.ps1 -ExecuteLive -Petrevolt
   .\scripts\run_live_eval.ps1 -ExecuteLive -StartupId 1b5de317-6e56-4dcb-ada9-28ab9adf8c0c
   .\scripts\run_live_eval.ps1 -ExecuteLive
   .\scripts\run_live_eval.ps1 -ExecuteLive -StethaimPilot
   ```
   - **Provider / Env**: Sets `AI_PROVIDER=anthropic` and temporary `ANTHROPIC_API_KEY` in process memory only; clears key in `finally` block. Targets `tides_dev.db`.
   - **Audit Status**: Prior live attempt (`21d60370-d7cf-43d8-9c14-05b0cd5078a2`, `2026-11-12 00:10:45`) halted on Stage-10 `financials_support` pre-fix (`$0.012323` spent). Post-fix live resumption awaits interactive `ANTHROPIC_API_KEY` entry (`--execute-live` fails closed `exit 1` without a key).

---

## 12. How to Run Tests

### Backend Test Suite (`pytest`, Verified Offline)
```powershell
# Run complete offline test suite (74 test_*.py files: 673 passed, 0 failed, 0 skipped, 342 third-party warnings in 96.16s)
.venv\Scripts\python.exe -m pytest tests/ --tb=short

# Targeted extraction recovery & safety verification suites (84 passed)
.venv\Scripts\python.exe -m pytest tests/test_extraction_recovery.py tests/test_extraction_reliability.py tests/test_stethaim_pilot_preflight.py tests/test_domain_recovery.py tests/test_live_eval_safety.py tests/test_runtime_guards_and_cli.py --tb=short
.venv\Scripts\python.exe -m pytest tests/test_security_hardening.py
.venv\Scripts\python.exe -m pytest tests/test_multi_sector_generalization.py
.venv\Scripts\python.exe -m pytest tests/test_cross_startup_contamination.py
.venv\Scripts\python.exe -m pytest tests/test_report_integrity_stethaim.py
.venv\Scripts\python.exe -m pytest tests/test_workflow_engine.py
.venv\Scripts\python.exe -m pytest tests/test_database_isolation.py
```
> **Telemetry Isolation Guarantee**: Recovery tests and `pytest tests/` isolate telemetry via `TIDES_LIVE_EVAL_REPORT_PATH` and checkpoint storage via `resolve_extraction_checkpoint_path` (temp dir under `PYTEST_CURRENT_TEST`). `reports/live_eval_run_report.json` (`7,372` bytes, `2026-11-12 00:10:45`, `SHA-256: 80E8D0DE02A11BC12621CCBCA9AF12B358D04B3B8C3C227EFD1CE4064A0A1D2B`) and `reports/telemetry/eval_21d60370-d7cf-43d8-9c14-05b0cd5078a2_partial_extraction_failed.json` remain byte-for-byte unchanged across `pytest tests/`.

### Frontend Verification (`vitest`, `tsc`, `eslint`, `next build`, Playwright)
`frontend/package.json` defines `"test": "vitest run"`, `"build": "next build"`, and `"lint": "next lint"`.
If `npm` / Node.js is on `PATH`:
```powershell
cd frontend
npm test
npm run lint
npm run build
```
In this workspace where global `node`/`npm` is absent from default `PATH`, prepend repo-local `.node\node-v22.11.0-win-x64` (`v22.11.0`) cleanly in the current shell:
```powershell
$env:PATH = (Resolve-Path ".node\node-v22.11.0-win-x64").Path + ";" + $env:PATH
Push-Location frontend
.\node_modules\.bin\vitest.cmd run
.\node_modules\.bin\tsc.cmd --noEmit
npm run lint
npm run build
Pop-Location
```
- **Audit Status**:
  - `vitest run`: **VERIFIED** (`4 test files passed (4)`, `30 tests passed (30)`: `auth.test.ts` 3, `api.test.ts` 9, `domain_mapping.test.ts` 5, `components.test.ts` 13; exit `0`).
  - `tsc --noEmit`: **VERIFIED** (exit `0`, `0` TypeScript errors).
  - `npm run lint`: **VERIFIED** (exit `0`, upstream `ESLintEmptyConfigWarning` in `frontend/eslint.config.mjs`).
  - `next build`: **VERIFIED** (exit `0`, Next.js `15.1.0` generated `12/12` routes cleanly).
  - Playwright browser E2E specs (`frontend/tests/e2e.spec.ts`, `frontend/tests/smoke.spec.ts` using Playwright bundled `node.exe` `v24.11.1` & `chromium-1228`): **VERIFIED** (`6 passed (8.9s)` against an isolated temporary FastAPI `AI_PROVIDER=mock` backend + `next start` server using temporary DB/uploads/telemetry).

---

## 13. Failure Recovery & Troubleshooting

1. **Cached Settings Pollution**:
   ```python
   from app.core.config import get_settings
   get_settings.cache_clear()
   ```
2. **Database Lock in Development**:
   - Ensure `WorkflowEngine` uses `_transition_lock` (`app/modules/workflow/workflow_engine.py`) and automated tests remain bound to isolated temp databases in `tests/conftest.py`.
3. **Graph Restoration Helper (Offline)**:
   - `scripts/restore_stethaim_graph.py` restores baseline STETHAIM metadata and the CleanPower stub artifact (`uploads/graphs/REPORT-BBD93B93.json`) if overwritten; do not run casually against modified packages without checking checksums.
4. **Budget Exhausted Halt**:
   - Inspect cost reservations in `app/services/ai/cost_ledger.py` and confirm whether prior aborted spend or token caps exceed `$0.35 USD` (live pilot runner) or `$0.55 USD` (platform default).
