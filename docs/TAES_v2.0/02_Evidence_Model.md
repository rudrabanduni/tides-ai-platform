# TAES Common Evaluation Ontology: 02_Evidence Model

The **Evidence** model represents the raw, verified citations extracted from uploaded documents. It is the concrete anchor that connects higher-level agent observations back to their physical files.

---

## 1. Schema Definition

Every Evidence record must conform to the following schema:

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `evidence_id` | `UUID` / `String` | Unique identifier of the evidence record (e.g. `EVID-PDF-402`) |
| `document` | `Dict` | Details of the source document: `document_id` and `filename` |
| `page` | `Integer` / `Null` | Page number in the document where the evidence was located |
| `section` | `String` | Section or header name where the evidence was located (e.g. `'financials'`, `'milestones'`) |
| `chunk` | `UUID` / `Null` | Semantic text chunk ID containing the source text |
| `source_type` | `String` | Classification type of the source document (e.g. `'Pitch Deck'`, `'Patent'`, `'Financial Statement'`) |
| `evidence_text` | `String` | The raw text snippet quoted directly from the parsed document |
| `extraction_confidence` | `Float` | The confidence score (0.0 to 1.0) of the AI extraction process |
| `freshness` | `DateTime` | Timestamp indicating when the document was uploaded or when it was created |
| `reliability` | `Float` | Numerical rating (0.0 to 1.0) based on document classification type |
| `validation_status` | `Enum` | Verification status: `UNVALIDATED`, `VALIDATED`, `CONTRADICTED` |
| `linked_claims` | `List[UUID]` | Claims that reference or are supported by this evidence record |

---

## 2. Document Reliability Mappings

Reliability weights are pre-defined by document classification to reflect the legal or administrative weight of the source:

* **Financial Statement (0.95)**: Audited or official balance sheets.
* **Patent (0.90)**: Registered patent application or certificate.
* **Excel Intake Application (0.85)**: Self-reported structured founder application data.
* **Pitch Deck / Business Plan (0.80)**: Self-reported qualitative presentations.
* **Generic Document (0.70)**: Unstructured PDFs, reports, or brochures.

---

## 3. Serialization Example (JSON)

```json
{
  "evidence_id": "EVID-PDF-402",
  "document": {
    "document_id": "doc-5a3d-4c22-b981",
    "filename": "audited_balance_sheet_2025.pdf"
  },
  "page": 4,
  "section": "Notes to Financial Statements",
  "chunk": "chunk-b129-44d5-a82f",
  "source_type": "Financial Statement",
  "evidence_text": "The company has outstanding short-term borrowings of INR 15,00,000 as of December 31, 2025.",
  "extraction_confidence": 0.98,
  "freshness": "2026-06-24T05:20:00Z",
  "reliability": 0.95,
  "validation_status": "VALIDATED",
  "linked_claims": ["claim-9e2b-45cf-812e"]
}
```
