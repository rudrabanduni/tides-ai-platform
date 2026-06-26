# TAES Common Evaluation Ontology: 08_Traceability Model

TAES enforces strict, bi-directional traceability. Every cell in a scorecard or sentence in a PDF report must be traceable back to the raw source document, section, and text snippet.

---

## 1. Traceability Path

```
  Document [document_id]
     │
     ▼ (parsed to)
  Evidence [evidence_id] (contains section, page, raw snippet)
     │
     ▼ (claims built from)
  Claim [claim_id] (typed values: string, number, etc.)
     │
     ▼ (analyzed by domain agents to create)
  Observation [observation_id] (references claim_id & doc_id)
     │
     ▼ (wrapped inside)
  Agent Assessment (group of observations per domain)
     │
     ▼ (aggregated by)
  Consensus (agreement/disagreement maps)
     │
     ▼ (evaluated by)
  Committee Decision (verdict)
     │
     ▼ (scored by)
  Score (Overall & Domain ratings)
     │
     ▼ (mitigated by)
  Recommendation (actionable plan)
     │
     ▼ (rendered in)
  Report (PDF output)
```

---

## 2. Link Keys and Mappings

| Current Node | Previous Node | Link Key / Mechanism |
| :--- | :--- | :--- |
| **Evidence** | Document | `source_document_id` foreign key inside `startup_evidence` table |
| **Claim** | Evidence | `claim_id` foreign key inside `startup_evidence` table |
| **Observation** | Claim | `supporting_claims` list containing `claim_id` UUIDs |
| **Observation** | Document | `supporting_documents` list containing `document_id` UUIDs |
| **Agent Assessment** | Observation | `observations` list of inline structured `Observation` schemas |
| **Consensus** | Agent Assessment | Map key matching domain names (e.g. `'founder'`, `'trl'`) |
| **Committee Decision** | Consensus | Maps consensus alignment keys to decision matrices |
| **Score** | Consensus | Computes numeric grades based on consensus metrics |
| **Recommendation** | Score | `affected_dimension` matching specific scoring fields |
| **Report** | Committee Decision | Injects final decision summary and logs consensus tables |

---

## 3. Auditing Example (Backward Tracing)

1.  **Report**: PDF states that "TRL readiness is at early prototype stage."
2.  **Score**: Score Engine lists `trl_score` of `3.0` based on this finding.
3.  **Committee Decision**: Committee resolved high risk on technology development.
4.  **Consensus**: TRL and Product agents both observed prototype testing gaps.
5.  **Agent Assessment**: TRL Agent's assessment contains `OBS-TRL-304`.
6.  **Observation**: `OBS-TRL-304` lists `supporting_claims` = `["claim-uuid-1"]` and `supporting_evidence` = `["evidence-uuid-1"]`.
7.  **Claim**: Claim lists `trl_level` = `3`.
8.  **Evidence**: Evidence lists snippet `"The system has only been tested in simulated environments."` on page 3 of `pitch_deck.pdf`.
9.  **Document**: `pitch_deck.pdf` uploaded on 2026-06-24.
