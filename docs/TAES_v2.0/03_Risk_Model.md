# TAES Common Evaluation Ontology: 03_Risk Model

The **Risk** model provides a structured representation of threats and weaknesses identified by domain expert agents. By standardizing risk entries, downstream engines can run risk aggregation, sensitivity analysis, and mitigation tracking.

---

## 1. Schema Definition

Every Risk record must conform to the following schema:

| Field Name | Type | Description |
| :--- | :--- | :--- |
| `risk_id` | `UUID` / `String` | Unique identifier (e.g. `RISK-TRL-304`) |
| `category` | `Enum` | Classification: `Technical`, `Market`, `Regulatory`, `Execution`, `Financial`, `Legal_IP` |
| `severity` | `Enum` | Combined priority indicator: `Critical`, `High`, `Medium`, `Low` |
| `likelihood` | `Enum` | Probability of risk occurrence: `High`, `Medium`, `Low` |
| `impact` | `Enum` | Impact on startup viability if occurred: `High`, `Medium`, `Low` |
| `affected_area` | `String` | Specific domain or department affected (e.g., `'manufacturing'`, `'clinical_trials'`) |
| `evidence` | `List[UUID]` | Linked Evidence IDs that substantiate this risk |
| `reasoning` | `String` | Rationale detailing why this risk exists and how it was calculated |
| `mitigation` | `String` | Detailed, actionable mitigation strategy to reduce or eliminate the risk |
| `estimated_time` | `String` | Time required to implement the mitigation (e.g., `'3 months'`) |
| `estimated_cost` | `String` | Cost range required to mitigate (e.g., `'INR 50,000 - 1,00,000'`) |
| `owner` | `String` | Designated entity responsible for mitigation (e.g. `'CTO'`, `'Founder'`) |
| `dependencies` | `List[String]` | Prerequisites or other risks that must be resolved first |

---

## 2. Risk Matrix Mapping (Severity Calculation)

The `severity` field is dynamically mapped from `impact` and `likelihood` coordinates:

| Impact \ Likelihood | High | Medium | Low |
| :--- | :--- | :--- | :--- |
| **High** | Critical | High | Medium |
| **Medium** | High | Medium | Low |
| **Low** | Medium | Low | Low |

---

## 3. Serialization Example (JSON)

```json
{
  "risk_id": "RISK-TRL-304",
  "category": "Technical",
  "severity": "High",
  "likelihood": "Medium",
  "impact": "High",
  "affected_area": "Product Reliability",
  "evidence": ["EVID-TXT-904"],
  "reasoning": "Prototype testing has only occurred in a laboratory setting. No outdoor or environmental stress testing has been performed on the core hardware.",
  "mitigation": "Conduct field deployment testing under varying heat and humidity conditions for at least 100 hours.",
  "estimated_time": "2 months",
  "estimated_cost": "INR 75,000",
  "owner": "CTO",
  "dependencies": ["OBS-TRL-002"]
}
```
