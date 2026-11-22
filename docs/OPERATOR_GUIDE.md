# Operator Guide

For incubation staff and administrators running TIDES-AI. The pre-takeover version of this guide is
kept at `docs/archive/OPERATOR_GUIDE_v1.0_pre_takeover.md`.

## Clean Windows machine setup

1. Install Python 3.12+ (3.14 is used locally) and Node.js 22 (or use the bundled `.node\` folder).
2. From the project folder:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   cd frontend; npm ci; npx playwright install chromium; cd ..
   ```
3. Offline demonstration: `powershell -ExecutionPolicy Bypass -File scripts\start_demo.ps1 -Reset`
   (see [DEMO_GUIDE.md](DEMO_GUIDE.md)).

## Live mode (real Claude evaluations)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_live.ps1
```

1. The script asks for your Anthropic API key in a **hidden** prompt. The key is never shown, saved or
   logged, and only the running backend holds it. Never paste the key into chat, email or a file.
2. It runs a two-call canary (under $0.01) to prove the key and model settings work. If the canary
   fails, nothing starts; details are in `logs\live_canary.json`.
3. It starts the app at http://localhost:3000 on the separate live database `tides_live.db`.
   Login: `evaluator@tides.ai`. Print the password with
   `.venv\Scripts\python.exe scripts\live_instance.py --show-credentials`.
4. Each evaluation is capped at **$0.60**. Extraction uses Claude Haiku 5.5; the six section specialists
   and supervisory review use Claude Sonnet 5.5. The run's actual spend is shown on the evaluation page.

Stop with `powershell -ExecutionPolicy Bypass -File scripts\stop_live.ps1`. Starting the demo stops live
mode, and the other way round, because both use ports 3000/8000. After a reboot, run `start_live.ps1`
again and re-enter the key. Real applicant documents in live mode are sent to Anthropic for evaluation.

## Scoring standard (section weightage)

`app/modules/evaluation/scoring_standard.json` holds TIDES' weightage: section weights (must add up to
100), optional per-criterion weights, the missing-information policy, decision thresholds and knockout
rules. The weighted score and the standard's version and status are shown on every result and PDF.
Until TIDES supplies its approved weightage (see `docs/CHATGPT_CRITERIA_PROMPT.md`), the file holds
**provisional equal weights** and no thresholds, and reports say so.

## Daily workflow

1. **New Application**: enter the full LaunchIndex form (company, contacts, founders, venture,
   financials, support needs, declarations). A retried submission never creates a duplicate
   (Idempotency-Key).
2. **Upload documents**: pitch deck, founder CVs, product/technical, financial and supporting
   documents. Accepted types: PDF, PPTX, PPT, DOCX, DOC, XLSX, XLS, CSV, TXT, MD, up to 25 MB each.
   Rejected uploads show the exact reason.
3. **Start evaluation** from the application page. One active run per application. Restarting a
   completed run requires **Start a new run**, which keeps earlier runs.
4. **Review** the six domains, cover criteria, supervisory synthesis and evidence. Only runs with status
   COMPLETED have a downloadable final report.

## User administration

Roles: admin, incubation_manager, evaluator, analyst (can submit and evaluate), reviewer,
committee_member and viewer (read-only). Admins manage users at `/api/v1/users`. Tokens expire after
`ACCESS_TOKEN_EXPIRE_MINUTES` (default 60), and refresh tokens rotate.

## Configuration reference (non-secret)

| Variable | Default | Meaning |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./tides_dev.db` | must be explicit and non-SQLite when `APP_ENV=production`; `tides_ai.db` always refused |
| `UPLOAD_DIR` | `uploads` | documents, graphs, PDFs, checkpoints |
| `AI_PROVIDER` | `mock` | `mock` or `anthropic`/`litellm` |
| `ALLOW_UI_LIVE_EVALUATIONS` | `false` | allow paid runs from the web app |
| `AI_MAX_EVALUATION_BUDGET_USD` | `0.35` | hard per-evaluation ceiling |
| `AI_MAX_RETRIES` | `1` | transport retries in the gateway |
| `AI_DOMAIN_BATCH_MAX_CRITERIA` | `3` | criteria per domain request |
| `AI_DOMAIN_BATCH_MAX_OUTPUT_TOKENS` | `900` | per-batch output ceiling |
| `AI_DOMAIN_BATCH_MAX_RETRIES` | `0` | identical-request retries on parse failure |
| `AI_DOMAIN_SPLIT_ON_TRUNCATION` | `true` | one split recovery for truncated batches |
| `AI_STRUCTURED_THINKING_MODE` | `off` | disable model thinking for JSON calls |
| `EVALUATION_RUNNER_MODE` | `thread` | `inline` for tests |
| `MAX_UPLOAD_SIZE_MB` | `25` | upload limit |

Secrets (`JWT_SECRET_KEY`, `ANTHROPIC_API_KEY`, `TAVILY_API_KEY`) belong in the environment or in a
gitignored `.env*` file only. Never put them in documentation, tickets or chat.

## Database migrations

```powershell
$env:DATABASE_URL="postgresql+psycopg://..."   # target database
.\.venv\Scripts\python.exe -m alembic upgrade head
```
Head revision: `20261122_0004` (application_submissions, evaluation_runs). Never point Alembic at
`tides_ai.db` or `tides_dev.db`.

## Common failures and recovery

| Failure | Meaning | Action |
|---|---|---|
| Upload rejected "not a valid PDF / corrupt / executable" | content check failed | export the document again as a standard PDF |
| "Upload at least one supporting document" | no documents yet | upload a deck, then start |
| Run **FAILED** at an extraction stage | provider/parse failure | read the stage error; start a new run (live mode: follow the recovery procedure in REAL_PROVIDER_READINESS.md, never rerun blindly) |
| Run **BLOCKED** | a domain was incomplete or validation failed; supervisory review was correctly refused | inspect partial results; no final report is issued |
| "Live-provider evaluations are disabled" | `ALLOW_UI_LIVE_EVALUATIONS=false` | intended outside authorised pilots |
| Budget exhausted | ledger ceiling reached | the run stops; spend is recorded; do not raise the ceiling without approval |

## Backups

Copy the database file (SQLite) or take a dump (PostgreSQL), together with `uploads\` (documents,
graphs, PDFs). A run's PDF is reproducible from its graph file.
