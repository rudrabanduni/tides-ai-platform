# TIDES-AI Architecture (v1.1)

## Components

```
Browser (Next.js 15, frontend/)
   │  JWT bearer, axios (frontend/services/applications.ts)
   ▼
FastAPI (app/api/main.py)  — routes mounted at / and /api/v1
   ├── auth / users / RBAC                       app/modules/auth, users, security
   ├── applications workflow (v1.1)              app/modules/applications
   │     routes → service (intake, idempotency) → runner (worker thread)
   │                                               │
   │                                               ▼
   ├── evaluation pipeline                       app/modules/ai/orchestrator/pipeline.py
   │     documents → parse → 10 staged extractions → claims + grounded evidence
   │       → 6 domain specialists (criterion batches) → supervisory gate + reviewer
   │       → observation graph → report engine → PDF
   │     progress events → app/modules/workflow/progress.py → evaluation_runs row
   ├── AI gateway                                app/services/ai (MockAIGateway | LiteLLMGateway)
   │     pricing catalog, cost ledger (pre-dispatch reservations, per-attempt records)
   └── persistence                               SQLAlchemy 2.x; SQLite (dev/demo) or PostgreSQL
         artifacts: uploads/graphs/{evaluation_id}.json, uploads/reports/{evaluation_id}.pdf
```

## Data model (workflow-relevant)

| Table | Role |
|---|---|
| `startup_applications` | the venture and its lifecycle status |
| `application_submissions` | full intake form, `application_ref`, unique `idempotency_key`, synthetic flag (1:1 with startup) |
| `founders`, `company_profiles` | founder and company details from the intake form |
| `documents` | uploaded files (UUID stored name, sanitised original name, type, size, parsed text) |
| `startup_intelligence_profiles`, `startup_claims`, `startup_evidence` | extracted claims; evidence carries a snippet **only** when located in document text |
| `evaluation_runs` | one pipeline execution: status, mode, per-stage progress, summary, report id, cost |
| `audit_logs` | identifiers-only audit trail (no founder/contact PII) |

Migration: `alembic/versions/20261122_0004_application_workflow.py` (head).

## Evaluation run lifecycle

`QUEUED → RUNNING → COMPLETED | BLOCKED | FAILED`

- **COMPLETED** only when the pipeline status is `COMPLETED`, all 87 criteria are accounted for with no
  duplicates or unknown IDs, all six domains completed, and `ReportValidator.validate_canonical_87_report`
  passes.
- **BLOCKED**: a report exists, but supervisory review was blocked or validation failed. It is never
  labelled complete, and no PDF is served (HTTP 409).
- Starting an evaluation is idempotent. An active run, or a completed one (unless `?rerun=true`), is
  returned instead of creating a duplicate.
- Progress is read only from the `evaluation_runs` row, which the pipeline's real stage transitions
  update. Nothing in the UI simulates progress.

## Domain assessment design

- Registry-driven batches of **3 criteria** (`AI_DOMAIN_BATCH_MAX_CRITERIA`), which gives 30 batches for 81
  criteria.
- Output cap per batch: `80 + 220 × n` tokens, floor 350, ceiling `AI_DOMAIN_BATCH_MAX_OUTPUT_TOKENS` (900).
- Prompt shows only the batch's claims and evidence. Evidence is shown as per-batch handles (`E1`…), and
  the model cites handles.
- `_resolve_batch_evidence` maps handles to real evidence IDs and rejects unknown references. Provenance
  (document / page / section) is resolved from evidence metadata, never from model text.
- Compact wire-format schema in the prompt (~120 tokens). Responses are still validated strictly against
  `DomainCriterionBatchOutput`, with no unexpected, duplicate or missing criteria allowed.
- Deterministic local merge and domain synthesis. No model call is used to merge.
- Consistency rules: VERIFIED_DOCUMENTED requires cited evidence with a real snippet. MISSING_INFORMATION
  becomes SELF_REPORTED_ONLY when an applicant value exists.

### Domain batch sizing (measured on the demo deck, Sonnet 5.5 at $2/$10 per MTok)

| Criteria / batch | Batches | Input tok | Expected out | Expected $ | Worst-case $ |
|---:|---:|---:|---:|---:|---:|
| 1 | 81 | 50,930 | 12,150 | 0.223 | 0.385 |
| 2 | 43 | 28,758 | 10,630 | 0.164 | 0.273 |
| **3** | **30** | **21,636** | **10,110** | **0.144** | **0.248** |
| 5 | 19 | 16,028 | 9,670 | 0.129 | 0.187 (but 164 tok/criterion → truncation risk) |

Three criteria per batch is the smallest size that keeps the worst case under the $0.35 ceiling with room
for extraction (~$0.015) and supervisory review (~$0.03). On Haiku 5.5 the same 30 batches cost about $0.007.

## Retry policy (single, consistent)

| Layer | Behaviour |
|---|---|
| LiteLLM | `num_retries=0` |
| Gateway (`LiteLLMGateway`) | retries **only** transient transport errors (429/5xx/timeout/connection), at most `AI_MAX_RETRIES` (default 1). Each attempt reserves budget before dispatch, gets a distinct operation ID, and is written to the ledger (failed attempts as zero-token `TRANSIENT_ERROR` rows). Logged as `[RETRY DISPATCH]`. |
| Domain specialist | never resends an identical request after truncation. `AI_DOMAIN_BATCH_MAX_RETRIES` (default 0) controls parse-failure retries. A truncated multi-criterion batch gets **one** budget-checked split into single-criterion requests. |
| Pipeline / orchestration | no automatic re-runs. Recovery happens only via explicit operator commands (`scripts/run_one_time_live_eval.py`). |

## Structured output and thinking

- LiteLLM 1.49 drops `response_format` for Anthropic (verified in `llms/anthropic/chat/transformation.py`).
  Structure is enforced by the injected format plus strict Pydantic validation.
- Claude 5.5 models think adaptively by default, and thinking tokens count toward `max_tokens`. With
  `AI_STRUCTURED_THINKING_MODE=off` (default), JSON calls send `thinking: {type: "between_tools"}` (Sonnet
  5.5) or `{type: "disabled"}` (Haiku 5.5). LiteLLM passes these kwargs through to the request body.

## Report and PDF

`app/modules/applications/pdf_report.py` builds the 20-section institutional report from persisted
artifacts only:
- cover
- executive summary
- company overview
- six domain sections
- 87-criterion table
- evidence quality
- strengths, concerns, contradictions, risk register, missing information
- priority questions, incubation support
- supervisory synthesis
- final recommendation and conditions
- methodology and evidence appendices

Every page carries a header with the evaluation ID, "Page X of Y", a confidentiality footer and, in mock
mode, the disclosure. The PDF is generated once, stored atomically, and its SHA-256 is recorded on the run.

## Evidence classes (shown everywhere)

| Verification status | Evidence class |
|---|---|
| VERIFIED_DOCUMENTED | Documentary evidence |
| VERIFIED_DOCUMENTED + recorded non-synthetic third-party source | Independently verified |
| SELF_REPORTED_ONLY | Applicant-reported |
| PLAUSIBLE_ESTIMATE / UNSUPPORTED_ASSUMPTION / CONTRADICTED | Not verified |
| MISSING_INFORMATION | Missing |
| NOT_APPLICABLE | Not applicable |
