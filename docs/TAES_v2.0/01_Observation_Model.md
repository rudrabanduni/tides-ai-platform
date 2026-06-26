# TAES Common Evaluation Ontology: 01_Observation Model

The **Observation** is the fundamental knowledge unit of domain intelligence in the TIDES AI Evaluation System (TAES). It represents a structured deduction made by a specialized AI agent based on validated startup claims.

---

## 1. Schema Definition

Every Observation must conform to the following schema:

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `observation_id` | `UUID` / `String` | Unique identifier (e.g. `OBS-FOUNDER-001`) |
| `title` | `String` | Short, descriptive title of the observation |
| `category` | `String` | Categorized domain sub-area (e.g., `'technical_expertise'`, `'cash_runway'`) |
| `description` | `String` | Detailed qualitative analysis and observations |
| `domain` | `String` | The domain of the evaluating expert agent (e.g. `'Founder'`, `'TRL'`, `'Market'`) |
| `severity` | `Enum` | Severity level of the observation: `Critical`, `High`, `Medium`, `Low` |
| `supporting_claims` | `List[UUID]` | Database IDs of validated claims that support this observation |
| `supporting_evidence`| `List[UUID]` | Database IDs of evidence snippets linked to the claims |
| `reasoning` | `String` | Detailed logical logic explaining why the claims/evidence lead to this observation |
| `confidence` | `Float` | The calculated confidence score (0.0 to 1.0) for this observation |
| `affected_dimensions`| `List[String]` | Dimensions of the startup affected (e.g. `'management'`, `'scalability'`, `'technology'`) |
| `dependencies` | `List[String]` | IDs of other observations that must be validated for this observation to hold |
| `related_observations`| `List[String]` | IDs of other observations connected to this observation |
| `suggested_actions` | `List[String]` | Immediate actionable suggestions to address or verify this observation |

---

## 2. Severity Categorization

* **Critical**: Observations that point to existential threats (e.g., solo founder with no commercial backup, zero cash runway, unproven core science).
* **High**: Serious concerns that will bottleneck development or incubation progress (e.g., missing key regulatory approval, un-mitigated key competitor).
* **Medium**: Standard early-stage concerns that require monitoring (e.g., product-market fit is still in user-testing phase).
* **Low**: Minor anomalies or areas for standard optimization.

---

## 3. Serialization Example (JSON)

```json
{
  "observation_id": "OBS-FOUNDER-102",
  "title": "Technical Founder Lacks Commercial Co-Founder",
  "category": "team_composition",
  "description": "The startup is led by a single technical founder who holds all equity. There is no commercial, sales, or business development leadership on the core team.",
  "domain": "Founder",
  "severity": "High",
  "supporting_claims": ["claim-7c5e-4b9d-a111"],
  "supporting_evidence": ["evidence-8f2a-4c8d-b222"],
  "reasoning": "While technical expertise is high, a lack of commercial leadership increases execution risk in sales pipeline setup and market entry strategies.",
  "confidence": 0.88,
  "affected_dimensions": ["execution_capability", "market_entry"],
  "dependencies": [],
  "related_observations": ["OBS-MARKET-204"],
  "suggested_actions": ["Recruit a business development lead", "Onboard a commercial advisor"]
}
```
