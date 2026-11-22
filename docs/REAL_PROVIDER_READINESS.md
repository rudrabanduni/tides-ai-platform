# Real-Provider Readiness (Anthropic Claude via LiteLLM)

**Status (2026-11-23): VERIFIED ON ONE REAL APPLICANT.** First authorised live pilot, STETHAIM Private
Limited (application `TIDES-2026-F46A13`, evaluation `f597f2b2…`), ran end to end with Claude Haiku 5.5
(extraction) and Sonnet 5.5 (six specialists + supervisory review):

| Attempt | Evaluation | Outcome | Cost | Finding → fix |
|---|---|---|---:|---|
| Canary ×3 | — | passed; `between_tools` / `disabled` thinking accepted | 3 × $0.00106 | thinking setting verified live |
| 1 | `3da1b9ca` | FAILED at extraction stage 9A | $0.0043 | schema rejected `jurisdiction: null` (deck: "patent filed", no country); 7 nullable fields fixed, invented defaults removed |
| 2 | `9594441a` | BLOCKED by strict validator (all 6 domains + supervisory completed, no truncation) | $0.1992 | CM-05/CM-06 absent from deck but on the intake form → filled from form as applicant-reported; evidence matcher improved for real PDF text |
| 3 | `f597f2b2` | **COMPLETED, report valid, 87/87** | **$0.2122** | re-run read the earlier run's claims too → each run now assesses only its own extraction |

Total live spend for the pilot: **$0.42**, every evaluation within the $0.60 ceiling. The applicant's score,
recommendation and report are confidential and kept only in the gitignored `reports/live/` folder.
One deck is not a statistical sample: watch cost and output tokens on the next few applicants. The historical sections below are kept as the reference procedure.

**Previous status: NOT VERIFIED.** No live provider call was made during the v1.1 work. Everything below was
verified offline (code inspection, unit and integration tests with mocked transports) or is listed as
unverified. Passing mock tests does **not** establish live readiness.

## 1. What failed in the last live pilot (PETREVOLT, evaluation `1a8036ae-0e37-4fb0-b241-680d2bb62b8d`)
- 10/10 extraction stages succeeded (12 Haiku operations, $0.014993), producing 281 claims.
- All 14 Sonnet domain operations stopped at exactly 900 output tokens (`finish_reason=length`). Each
  truncated batch was resent unchanged and failed again: 7 batches × 2 = $0.236902 with no usable output.
- The supervisory review was correctly blocked. Cumulative spend $0.251895, remaining $0.098105.
- **This evaluation is a preserved, incomplete historical pilot. It must not be resumed, duplicated or
  used to spend the remaining budget.**

## 2. Root causes identified offline

| Cause | Evidence | v1.1 change |
|---|---|---|
| Adaptive thinking on by default for Claude 5.5 models; thinking tokens count toward `max_tokens` | Anthropic API behaviour for Sonnet/Haiku 5.5; every call ended at the exact cap | `AI_STRUCTURED_THINKING_MODE=off`: Sonnet 5.5 → `thinking={"type":"between_tools"}`, Haiku 5.5 → `{"type":"disabled"}` |
| `response_format` silently dropped | litellm 1.49.0 Anthropic `get_supported_openai_params` lacks it; `drop_params=True` | documented; strict local Pydantic validation; compact format in prompt |
| Full UUID evidence IDs in output (~15–20 tokens each, several per criterion) | prompt/response structure | per-batch handles `E1…`, mapped back and validated server-side |
| ~870-token JSON schema repeated in every request | measured | ~120-token compact format (`DOMAIN_BATCH_COMPACT_SCHEMA`) |
| 5 criteria × 180 tokens allowance | 900-token cap | 3 criteria/batch, cap `80 + 220n` (740 for 3) |
| Identical retry of deterministic truncation | telemetry (`_1`/`_1` pairs) | never resend identical truncated requests; one budget-checked split recovery |

## 3. Cost model (measured prompt sizes on the demo deck; Sonnet 5.5 $2/$10, Haiku 5.5 $0.10/$0.50 per MTok)

| Stage | Expected | Worst case |
|---|---:|---:|
| Extraction (10 stages, Haiku 5.5) | ~$0.015 (PETREVOLT actual: $0.014993) | ~$0.03 |
| Domains, 30 batches, Sonnet 5.5 | $0.144 | $0.248 |
| Supervisory review (Sonnet 5.5, ≤2400 out) | ~$0.03 | ~$0.03 |
| **Total** | **≈ $0.19** | **≈ $0.31** |

PETREVOLT-sized decks have about 2× the per-batch input of the demo deck, so the expected total is about
$0.27 and the worst case can exceed $0.35. The ledger reserves every call before dispatch, so the
ceiling cannot be breached: a run that reaches it stops, and its report is BLOCKED (never labelled
complete). Running the domain specialists on Haiku 5.5 would cost about $0.01. That trade-off between
model quality and budget is the operator's decision.

## 4. Pre-pilot checklist (all must be ticked by an authorised operator)

**Update 2026-11-23:** the user authorised live evaluations with a **$0.60** ceiling, Sonnet 5.5
specialists, and a real applicant deck as the first test. `scripts\start_live.ps1` automates the key
entry (hidden prompt, never stored), the single-call canary per model (`scripts\live_canary.py`, with
an automatic `low_effort` fallback if the thinking setting is rejected) and the separate live database
`tides_live.db`. The items below remain the reference procedure.

- [ ] Written authorisation for a paid run, naming the startup and the budget ceiling.
- [ ] A **new** startup/evaluation (not PETREVOLT `1a8036ae`), on a database other than `tides_ai.db`.
- [ ] `ANTHROPIC_API_KEY` supplied through a masked prompt or a secret store, never typed into chat, files
      or tickets. `RESEARCH_PROVIDER=disabled` unless a Tavily budget is also approved.
- [ ] `AI_STRUCTURED_THINKING_MODE=off`, `AI_DOMAIN_BATCH_MAX_CRITERIA=3`, `AI_DOMAIN_BATCH_MAX_RETRIES=0`,
      `AI_MAX_RETRIES=1`, `AI_MAX_EVALUATION_BUDGET_USD=0.35`.
- [ ] Dry run first, without `--execute-live`:
      `.venv\Scripts\python.exe scripts\run_one_time_live_eval.py --startup-id <uuid>`. It must report
      the target, database, budget and projected cost without calling the provider.
- [ ] `.venv\Scripts\python.exe scripts\check_live_readiness.py` reports configuration presence only.
- [ ] **Single-call canary** before a full run: one cheap extraction stage. Confirm the provider accepts
      `thinking: {type: "between_tools"}` through LiteLLM's Anthropic request (a 400 here is not billed),
      `usage.completion_tokens` is well below `max_tokens`, `finish_reason=stop`, and the ledger records
      exactly one operation.
- [ ] One full evaluation with `--execute-live`, monitored. Afterwards: ledger total ≤ ceiling, no
      `TRANSIENT_ERROR` storms, every domain COMPLETED, 87/87 coverage, validation valid.
- [ ] Archive the telemetry (`reports/telemetry/`) and record the run in the release report.

## 5. Verified offline
- Gateway sends the thinking kwargs, retries only transport errors, reserves before every attempt, and
  records failed attempts (`tests/test_live_eval_safety.py`).
- Gateway fails closed without a key (`anthropic` provider or production) and refuses the mock provider
  in production (`tests/test_runtime_guards_and_cli.py`).
- The web app refuses live runs unless `ALLOW_UI_LIVE_EVALUATIONS=true`, and `litellm.completion` is never
  reached (`tests/test_application_workflow.py`).
- Domain batching, evidence-handle resolution, split recovery and the supervisory gate
  (`tests/test_domain_batching.py`, `tests/test_domain_recovery.py`, `tests/test_supervisory_gating_and_audit.py`).

## 6. Not verified (requires an authorised live run)
- Provider acceptance of `between_tools` / `disabled` under litellm's `anthropic-version: 2023-06-01` header.
- Real output-token distribution for 3-criterion batches (expected ~350–450 with thinking off).
- Live extraction quality with the new evidence-grounding rule: claims whose values are not literally
  present in the document lose their snippet and become applicant-reported.
- End-to-end supervisory review on real model output.
- Native structured outputs (`output_config.format`) are **not** used. Enabling them would need
  schema adaptation and a live check.
