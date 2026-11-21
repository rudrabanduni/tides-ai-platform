# TIDES-AI — engineering handbook & checkpoint

Startup incubation due-diligence platform for TIEDS, IIT Roorkee. Evaluates applications against the
LaunchIndex rubric: **87 criteria = 6 cover (CM-01..06) + 81 domain** (PS 13, MO 10, FT 13, BC 13,
II 11, FI 21). Registry: `app/modules/evaluation/domains/registry.py` (authoritative; never edit IDs).

## Branches
- `release/v1.0.0` — untouched baseline (commit b0fbc67).
- `release/v1.1-product-completion` — all takeover work (UNCOMMITTED in working tree as of checkpoint).
- Pre-takeover backup (DBs + full worktree tgz): `C:\Users\gajab\Documents\tides-ai-backups\2026-11-22-takeover\`.

## Data protection rules (mandatory)
- `tides_ai.db` protected, SHA-256 `D9659F4E8C1058C5D5F4511E1BB22D3ABE6CB12101C16CE397416051A38176C7`. Runtime refuses it.
- `tides_dev.db` = PETREVOLT history, SHA-256 `96564C17CD29005FD27FFEF0CF9F84E84B17377233BEC7B9E77FCC496EF78960`.
  Never run the app, `scripts/run_dev_backend.py` or `scripts/init_dev_db.py` against it (create_all would add tables).
  `tests/conftest.py` now fails the suite if it changes.
- Demo uses `tides_demo.db` + `uploads_demo/` only (gitignored, resettable).
- PETREVOLT eval `1a8036ae-0e37-4fb0-b241-680d2bb62b8d`: incomplete live pilot, spent $0.251895, remaining $0.098105.
  Do NOT resume, duplicate or spend. Telemetry in `reports/telemetry/` is immutable.
- Never read/print/commit API keys. Zero live provider calls without explicit user authorisation.

## Architecture (key entry points)
- Backend FastAPI: `app/api/main.py` (routes at `/` and `/api/v1`). Settings: `app/core/config.py`.
- **Application workflow (new, v1.1):** `app/modules/applications/`
  - `models.py` ApplicationSubmission (intake form, idempotency key, `TIDES-YYYY-XXXXXX` ref), EvaluationRun (DB-backed progress).
  - `service.py` intake + dashboard counts; `runner.py` starts the real pipeline in a worker thread
    (`EVALUATION_RUNNER_MODE=thread|inline`), records progress from `app/modules/workflow/progress.py` events;
    live-provider runs refused from the UI unless `ALLOW_UI_LIVE_EVALUATIONS=true`.
  - `results.py` six domains, 87-criterion coverage, deterministic cover assessment, supervisory synthesis,
    strict `ReportValidator.validate_canonical_87_report`; `pdf_report.py` 20-section ReportLab PDF
    (page X of Y, IDs, evidence appendix, methodology, confidentiality, mock disclosure on every page).
  - `routes.py`: `/applications`, `/applications/{id}/documents`, `/applications/{id}/evaluations`,
    `/evaluation-runs/{id}` (+`/results`, `/evidence`, `/report.pdf`), `/applications-dashboard`, `/runtime-mode`.
- Pipeline: `app/modules/ai/orchestrator/pipeline.py::coordinate_evaluation_pipeline` (10 staged extractions →
  claims/evidence → 6 domain specialists → fail-closed supervisory gate → graph `uploads/graphs/{evaluation_id}.json`).
- Domain batching: `app/modules/evaluation/domains/{batching,base}.py`. Gateway: `app/services/ai/{gateway,litellm,mock}.py`.
- Evidence grounding: `app/modules/intelligence/evidence_locator.py` (snippet stored only if found in document text).
- Upload safety: `app/modules/documents/validation.py` (signatures, corrupt/encrypted PDF, macro OOXML, ADS/traversal names).
- Frontend Next.js 15: new pages `frontend/app/applications/{page,new,[id]}`, `frontend/app/evaluations/run/[runId]`,
  rewritten `dashboard`, `login`; API client `frontend/services/applications.ts`; UI kit `frontend/components/workflow/ui.tsx`.

## Provider path fixes (v1.1, offline-verified only)
- Root cause of PETREVOLT 900-token truncation: Claude 5.5 adaptive thinking on by default (counts toward max_tokens)
  + UUID evidence IDs in output + LiteLLM 1.49 silently drops `response_format` for Anthropic.
- Fixes: thinking disabled for JSON calls (`AI_STRUCTURED_THINKING_MODE=off`: Sonnet 5.5 `between_tools`,
  Haiku 5.5 `disabled`); short evidence handles E1..En mapped back + unknown refs rejected; provenance resolved
  locally; compact wire schema (~120 vs ~870 tokens); 3 criteria/batch (30 batches), cap 80+220n (≤900).
- One retry policy: gateway retries transport errors only (each attempt reserved + ledger row, distinct op IDs);
  domain layer never resends identical truncated requests; one budget-checked split-to-single-criterion recovery.
- Measured cost (demo deck, Sonnet 5.5 domains): expected $0.144, worst-case $0.248 (+~$0.015 extraction,
  ~$0.03 supervisory). Larger real decks may approach the $0.35 ceiling; Haiku 5.5 domains would cost ~$0.01 (user decision).
- `between_tools` acceptance under litellm's anthropic-version header is NOT live-verified.

## Commands (Windows)
- Demo: `powershell -ExecutionPolicy Bypass -File scripts\start_demo.ps1 [-Reset] [-Rebuild]`; stop: `scripts\stop_demo.ps1`.
  Frontend http://localhost:3000 · backend http://127.0.0.1:8000 · docs /docs. Login email analyst@tides.ai;
  password: `.venv\Scripts\python.exe scripts\init_demo_db.py --show-credentials` (stored in gitignored `.env.demo`).
- Synthetic deck: `scripts/generate_synthetic_deck.py` → `demo_fixtures/cleanpower_systems_pitch_deck.pdf` (fictional).
- Backend tests: `$env:AI_PROVIDER="mock"; .venv\Scripts\python.exe -m pytest tests/ -p no:warnings --junitxml=reports/test_results/backend_junit.xml`
  (terminal summary line is suppressed in this env; use the exit code / junit file).
- Frontend (PATH += `.node\node-v22.11.0-win-x64`): `npx tsc --noEmit`, `npx eslint .`, `npx vitest run`, `npx next build`,
  `npx playwright test --workers=1` (needs running demo stack).

## Status (2026-11-22, release v1.1)
- Authoritative summary: `docs/FINAL_RELEASE_REPORT.md`. Offline demo READY; real-provider pilot NOT VERIFIED;
  production NOT READY.
- Verified: backend suite (see release report for counts; `reports/test_results/backend_junit.xml`), tsc clean,
  ESLint 0 errors (config was previously EMPTY), Vitest 36/36, next build OK, Playwright 5/5 incl. full browser
  journey (`reports/demo_acceptance/acceptance_report.pdf`, 18 pages, disclosure on every page, all 87 IDs).
- Alembic head `20261122_0004` (application_submissions, evaluation_runs), upgrade/downgrade verified.
- Production refuses default/short `JWT_SECRET_KEY`.
- `test_large_graph_performance` is wall-clock sensitive: run the backend suite with the demo servers stopped.
- Known remaining: see release report §8 (live thinking-param acceptance, worst-case live cost, literal evidence
  grounding, production items, legacy pages/overrides).

## Next steps
1. Commit on `release/v1.1-product-completion` only after user approval.
2. Authorised live pilot: follow `docs/REAL_PROVIDER_READINESS.md` §4 (canary first). Never use PETREVOLT `1a8036ae`.
