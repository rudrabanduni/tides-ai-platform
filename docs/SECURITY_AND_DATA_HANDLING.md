# Security and Data Handling

Startup application data is confidential. This document describes the controls that exist in code
(v1.1) and the limits of what has been verified.

## Authentication and sessions
- Passwords are hashed with bcrypt (passlib `CryptContext`, `app/core/security.py`). API keys are
  stored as bcrypt hashes and shown once.
- JWT access tokens expire after `ACCESS_TOKEN_EXPIRE_MINUTES` (default 60), and refresh tokens rotate.
- With `APP_ENV=production` the app **refuses to start** if `JWT_SECRET_KEY` is a known default or shorter
  than 32 characters (`validate_production_secrets`), uses SQLite or a dev database, or has an implicit
  `DATABASE_URL`.
- The login page never prefills or displays a password. The local demo password is generated per
  machine and stored in the gitignored `.env.demo`.

## Authorisation
- Role-based access (`app/modules/auth/dependencies.py`). Submitting applications, uploading and
  starting evaluations require admin, incubation manager, evaluator or analyst roles. Read endpoints
  require a staff role (viewer and up). Unauthenticated API calls return 401 (Playwright-verified).
- `DEV_MODE=true` bypasses role checks outside tests. It must never be enabled on shared or production
  systems; the demo launcher forces `DEV_MODE=false`.

## Uploads (`app/modules/documents/validation.py`)
- Extension allow-list, 25 MB limit, empty-file rejection.
- Content signature must match the extension (`%PDF-`, OOXML zip with the correct part folder, OLE for
  legacy Office, text without NUL bytes). Executables (MZ/ELF/Mach-O) and scripts are rejected.
- Corrupt or password-protected PDFs are rejected. Macro-enabled OOXML (`vbaProject.bin`) and zip
  entries with unsafe paths are rejected.
- Filenames are sanitised (no path components, NTFS `:` stream syntax neutralised, reserved device
  names prefixed, bounded length). Files are stored as `<uuid><ext>` inside the startup's folder, with
  a resolved-path containment check.
- Documents cannot be changed while an evaluation is running.

## Cross-startup isolation
- Evidence lookups are joined through the startup's own profile (`results.evidence_records`), so IDs
  belonging to another startup return nothing (API test `test_cross_startup_evidence_isolation_and_incomplete_reports`).
- Claim grounding only searches documents of the same startup.
- Domain prompts include only the batch's claims and evidence (`tests/test_cross_startup_contamination.py`).

## Personal data
- Audit log entries for application submission carry identifiers only.
- The pipeline no longer prints the extracted profile (founder names and contacts) to stdout. Gateway
  error logs no longer include raw model output snippets.
- Applicant contact details that appeared in mock source code were removed.
- `app/modules/intelligence/pii_sanitizer.py` redacts PII in AI-bound text where it is applied.
  Founder names are still sent to the model on live runs, because team assessment needs them.
- PDF reports omit founder and contact personal details. Company-level information is included.

## Evidence integrity
- An extracted value gets a document snippet only when the value is found in the submitted
  document's text (`evidence_locator.py`). Previously every claim carried a synthetic "Disclosed in
  pitch deck: <value>" snippet.
- Models cite per-batch evidence handles. Unknown handles or IDs are rejected and never copied into
  reports.
- "Independently verified" requires a recorded, non-synthetic third-party source. No such source exists
  in offline mode.
- Reports never claim regulatory compliance, patent grant, ethics approval or traction beyond the
  evidence class shown.

## Secrets
- No key is committed. `.env`, `.env.*` (except the two examples), `.env.demo` and `frontend/.env.local`
  are gitignored.
- Provider keys are read only from the environment or settings. Their values are never logged or
  printed; readiness checks report presence only.
- The frontend bundle contains no provider configuration. It knows only the backend URL and the demo
  flag.

## Protected data
| Asset | Protection |
|---|---|
| `tides_ai.db` (SHA-256 `D9659F4E…76C7`) | refused by `Settings`; hash asserted by the test suite and printed by the demo backend |
| `tides_dev.db` (SHA-256 `96564C17…F78960`) | hash asserted by the test suite (added v1.1 after a test was found mutating its schema; file restored byte-for-byte) |
| `reports/telemetry/*`, `reports/live_eval_run_report.json`, STETHAIM graph | hash asserted by the test suite; never written by the demo |
| Demo data | `tides_demo.db`, `uploads_demo/`: resettable, gitignored |

## Known limitations
- The in-memory rate limiter and API-key store are per process, not shared across instances.
- The CSP header (`default-src 'self'`) applies to API responses only. The Next.js frontend needs its own
  production security headers.
- SQLite is development/demo only. Production requires PostgreSQL (enforced).
- No external penetration test has been performed.
