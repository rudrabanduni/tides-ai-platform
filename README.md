# TIDES-AI — Startup Incubation Due-Diligence Platform

TIDES-AI evaluates startup incubation applications for the **Technology Incubation and
Entrepreneurship Development Society (TIEDS), IIT Roorkee**. It scores each application against
the LaunchIndex Startup Incubation Application rubric: **87 criteria**, made up of six cover/intake
criteria (CM-01..CM-06) and 81 domain criteria. Six specialist domains assess the 81 criteria, a
supervisory reviewer synthesises them, and the result is a validated institutional due-diligence
report with PDF export.

```
APPLICATION → DOCUMENT UPLOAD → EVALUATION → DOCUMENT EXTRACTION → CLAIMS & EVIDENCE
  → SIX DOMAIN SPECIALISTS → SUPERVISORY REVIEW → 87-CRITERION VALIDATION → REPORT → PDF
```

| Domain | Criteria |
|---|---:|
| Problem & Solution (PS) | 13 |
| Market Opportunity (MO) | 10 |
| Founder & Team (FT) | 13 |
| Business Model & Commercialisation (BC) | 13 |
| Innovation & Impact (II) | 11 |
| Financials & Incubation Support (FI) | 21 |
| Cover & intake metadata (CM) | 6 |
| **Total** | **87** |

## Two separate modes

| | Offline demonstration | Live provider evaluation |
|---|---|---|
| AI responses | `MockAIGateway`: deterministic, document-grounded, every rationale labelled `MOCK:` | Anthropic Claude via LiteLLM |
| Database | `tides_demo.db` (resettable) | an explicitly configured database |
| Cost | $0 | budget ceiling `AI_MAX_EVALUATION_BUDGET_USD` (default $0.35) |
| Disclosure | `MOCK DEMONSTRATION — OFFLINE SYNTHETIC RESULTS — NOT A REAL AI EVALUATION` on every screen and PDF page | none |
| From the web app | yes | refused unless `ALLOW_UI_LIVE_EVALUATIONS=true` |

The live mode has **not** been verified end to end with the v1.1 fixes. See
[docs/REAL_PROVIDER_READINESS.md](docs/REAL_PROVIDER_READINESS.md).

## Quick start (Windows, offline demonstration)

Prerequisites already in the repository: `.venv\` (Python 3.14) and `.node\node-v22.11.0-win-x64\`.

```powershell
powershell -ExecutionPolicy Bypass -File scripts\start_demo.ps1 -Reset
```

- Frontend: http://localhost:3000
- Backend API: http://127.0.0.1:8000 · API docs: http://127.0.0.1:8000/docs
- Login: `analyst@tides.ai`. Print the generated local password with
  `.venv\Scripts\python.exe scripts\init_demo_db.py --show-credentials`.
- Sample deck: `demo_fixtures\cleanpower_systems_pitch_deck.pdf` (fictional company).
- Stop: `powershell -ExecutionPolicy Bypass -File scripts\stop_demo.ps1`

The full walkthrough is in [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md).

## Repository map

| Path | Purpose |
|---|---|
| `app/api/` | FastAPI app factory, routers, middleware |
| `app/modules/applications/` | intake submissions, evaluation runs, results, PDF report, routes |
| `app/modules/ai/orchestrator/pipeline.py` | evaluation pipeline (extraction → domains → supervisory → report) |
| `app/modules/evaluation/domains/` | criterion registry, six domain specialists, batching |
| `app/modules/evaluation/supervisory/` | fail-closed supervisory reviewer |
| `app/services/ai/` | AI gateway (mock + LiteLLM), pricing, cost ledger |
| `app/modules/documents/validation.py` | upload safety checks |
| `frontend/` | Next.js 15 application |
| `scripts/` | demo launcher, database initialisers, synthetic deck generator, live-pilot CLI |
| `tests/` | backend pytest suite · `frontend/tests/` Vitest + Playwright |
| `docs/` | architecture, operations, security, readiness, release report |

## Tests

```powershell
$env:AI_PROVIDER="mock"; .venv\Scripts\python.exe -m pytest tests -p no:warnings --junitxml=reports\test_results\backend_junit.xml
cd frontend; $env:PATH="..\.node\node-v22.11.0-win-x64;$env:PATH"
npx tsc --noEmit; npx eslint .; npx vitest run; npx next build
npx playwright test --workers=1   # requires the running demo stack
```

## Documentation

- [CLAUDE.md](CLAUDE.md): engineering handbook and checkpoint
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md)
- [docs/OPERATOR_GUIDE.md](docs/OPERATOR_GUIDE.md)
- [docs/SECURITY_AND_DATA_HANDLING.md](docs/SECURITY_AND_DATA_HANDLING.md)
- [docs/REAL_PROVIDER_READINESS.md](docs/REAL_PROVIDER_READINESS.md)
- [docs/FINAL_RELEASE_REPORT.md](docs/FINAL_RELEASE_REPORT.md)

## Data protection

`tides_ai.db` (protected snapshot) and `tides_dev.db` (PETREVOLT history) must never be modified.
The application refuses to start against `tides_ai.db`, and the test suite fails if either file or
the historical telemetry changes. Details are in
[docs/SECURITY_AND_DATA_HANDLING.md](docs/SECURITY_AND_DATA_HANDLING.md).
