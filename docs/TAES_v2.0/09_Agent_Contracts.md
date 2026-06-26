# TAES Common Evaluation Ontology: 09_Agent Contracts

To guarantee system stability, decoupling, and security, every domain expert agent operates under a strict, immutable **Agent Contract**. This contract defines what data an agent can see, what it must return, and what actions it is strictly prohibited from executing.

---

## 1. Input Specifications (What Agents Receive)

Agents are executed within a sandboxed context and receive only:
* **Validated claims** for the target startup.
* **Evidence snippets** (and their coordinates) linked to those claims.
* **Document metadata** (classification, title, size).
* **Field conflict histories** and their resolutions.

---

## 2. Output Specifications (What Agents Return)

Every agent must return **only** a single `AgentAssessment` schema containing:
* `observations`: List of structured `Observation` objects.
* `strengths` / `weaknesses`: Qualitative summaries.
* `critical_risks` / `medium_risks` / `low_risks`: Structured risk objects.
* `missing_evidence`: Specific document name lists.
* `questions_for_founder`: Specific text questions.
* `recommendations`: Actionable advice list.
* `confidence_hierarchy`: Finding, evidence, reasoning, and overall domain confidences.

---

## 3. Negative Constraints (What Agents Cannot Do)

To maintain system integrity, all agents must comply with the following boundaries:

* **Cannot Access Raw Files**: Agents are prohibited from reading raw uploaded documents (PDFs, Excels, Word documents). They only read the parsed, validated claims and metadata.
* **Cannot Score**: Agents cannot generate numeric ratings, weights, or overall score grades. All scoring is deferred to the Score Engine.
* **Cannot Decide Verdicts**: Agents cannot make final recommendations to accept, incubate, defer, or reject a startup.
* **Cannot Modify Database**: Agents are read-only processors. They cannot write claims, update startup applications, or modify database models directly.
* **Cannot Infer Beyond Evidence**: Agents cannot hallucinate or infer metrics not supported by the input claims. If a metric is missing, they must request it in the `missing_evidence` or `questions_for_founder` fields.
