# Offline Stakeholder Demonstration Guide

> **MOCK DEMONSTRATION — OFFLINE SYNTHETIC RESULTS — NOT A REAL AI EVALUATION.**
> The demo runs the production workflow, persistence, validation and report code with the offline
> `MockAIGateway`. No API key is used, no external service is called, and nothing is spent.

## 1. Start (about 1–3 minutes)

```powershell
cd C:\Users\gajab\Documents\tides-ai-platform
powershell -ExecutionPolicy Bypass -File scripts\start_demo.ps1 -Reset
```

`-Reset` wipes **only** `tides_demo.db` and `uploads_demo\`. Leave it out to keep previous demo
applications. The script prints `UP` for both services when they are ready.

| | URL |
|---|---|
| Application | http://localhost:3000 |
| Backend | http://127.0.0.1:8000 |
| API docs | http://127.0.0.1:8000/docs |

Login email: `analyst@tides.ai`. The password is generated locally on first start and kept in the
gitignored `.env.demo`. To print it:

```powershell
.venv\Scripts\python.exe scripts\init_demo_db.py --show-credentials
```

## 2. Walkthrough (about 5 minutes)

1. **Login**: an amber disclosure bar appears on every workflow page.
2. **Dashboard**: counts come from the database. Synthetic records are labelled.
3. **New Application**: click **Fill synthetic CleanPower sample** (or type your own), tick the three
   declarations, then **Submit application**. Validation errors are shown inline. The application
   reference (`TIDES-2026-…`) appears after submission.
4. **Documents**: choose *Pitch deck* and upload `demo_fixtures\cleanpower_systems_pitch_deck.pdf`.
   Optional rejection demo: upload `demo_fixtures\malicious_binary.exe` (blocked in the browser) or any
   non-PDF file renamed `.pdf` (blocked by the server's content check).
5. **Continue → Open application → Start evaluation**. Stage indicators update from the backend:
   ten extraction stages, claims and evidence, six domains, supervisory review, report and validation.
   The run takes about 5–15 seconds in mock mode.
6. **View assessment & report**:
   - *Overview*: 87/87 criteria, 6/6 domains, validation status, committee recommendation.
   - *Six-domain assessment*: per-criterion score, evidence class, rationale. Click **evidence** to see
     the exact deck passage and page.
   - *Cover criteria*: CM-01…CM-06.
   - *Supervisory review*: cited strengths, weaknesses, risks, questions, conditions.
   - *Due-diligence report*: **Open due-diligence report** shows the PDF inline. **Download PDF** saves
     `MOCK_DEMO_TIDES_Due_Diligence_….pdf`.

## 3. What to say about the results

- Every rationale starts with `MOCK:`. Scores are deterministic functions of the criterion ID, and the
  evidence class depends on whether the deck actually contains the value.
- *Documentary evidence* means a passage was found in the uploaded deck. *Applicant-reported* means the
  value was stated without a supporting document. Nothing is shown as *Independently verified* in offline
  mode.
- A reference copy of a generated report is at `reports\demo_acceptance\acceptance_report.pdf`.

## 4. Stop / reset

```powershell
powershell -ExecutionPolicy Bypass -File scripts\stop_demo.ps1
powershell -ExecutionPolicy Bypass -File scripts\start_demo.ps1 -Reset -Rebuild
```

## 5. Troubleshooting

| Symptom | Fix |
|---|---|
| `NOT RESPONDING` after start | read `logs\demo_backend.err.log` / `logs\demo_frontend.err.log` |
| Port 3000/8000 in use | `scripts\stop_demo.ps1`, or close the other program; ports are parameters (`-BackendPort`, `-FrontendPort`) |
| Login fails | re-print the password (`--show-credentials`); if `.env.demo` was deleted, run `start_demo.ps1 -Reset` |
| Frontend calls the wrong backend | `start_demo.ps1 -Rebuild` (API URL is compiled into the build) |
| Evaluation shows BLOCKED/FAILED | open the run; the failing stage and error are shown. Start a new run after fixing the documents |
