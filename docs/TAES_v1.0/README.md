# TIDES AI Evaluation Standard (TAES) v1.0

> **Classification:** Internal Technical Standard  
> **Version:** 1.0.0  
> **Effective Date:** June 2026  
> **Maintained by:** TIDES Platform Engineering Team  
> **Status:** Active — Governs all AI evaluation pipelines

---

## What Is TAES?

The **TIDES AI Evaluation Standard (TAES)** is the governing technical specification that defines how every AI-driven startup evaluation must be conducted on the TIDES platform.

TAES is not a product feature. It is an **institutional standard** — a binding contract between the platform's AI infrastructure, its human operators, and the startups being evaluated. It establishes the rules of evidence, the structure of judgment, the calibration of confidence, and the architecture of every AI agent that participates in the evaluation process.

TAES v1.0 covers:

- The philosophical principles that underpin every evaluation
- The lifecycle model every startup is mapped against
- The technology readiness framework used to classify innovation maturity
- The scoring methodology applied across all evaluation pillars
- The sector normalization rules that ensure cross-domain fairness
- The multi-agent architecture that powers the evaluation engine
- The report standard that governs every final output
- The system architecture governing how all components interact
- The product roadmap that defines the evolution of the platform

---

## Why TAES Exists

Startup evaluation is a high-stakes judgment process. When done without discipline, it produces:

- **Inconsistent verdicts** — two similar startups receive opposite outcomes because different evaluators applied different criteria
- **Unexplainable scores** — numbers that cannot be traced back to specific evidence
- **Sector bias** — deep-tech startups penalized for not showing early revenue that their sector does not yet support
- **Hallucination risk** — AI systems that generate confident-sounding assessments without evidence
- **Irreproducibility** — evaluations that cannot be repeated or audited

TAES solves each of these failures by imposing a formal evaluation grammar. Every evaluation output produced by the TIDES platform must be traceable to:

1. A defined evaluation pillar (e.g., Founder, Product, Technology)
2. A defined sub-criterion within that pillar
3. Specific evidence extracted from source documents or structured fields
4. A confidence score that reflects how complete that evidence is
5. A recommendation that is explicitly separated from the AI score

This traceability chain is not optional. It is the minimum acceptable output.

---

## How TAES Governs AI Evaluation

Every AI agent that operates within the TIDES platform is bound by this standard. Compliance is enforced through three mechanisms:

### 1. Structural Compliance
Each AI agent must produce outputs that conform to the schema defined in this standard. No agent may emit a final score, recommendation, or risk flag without also emitting the evidence bundle and confidence score that justify it.

### 2. Principle Compliance
Each evaluation step must adhere to the principles defined in [02_Evaluation_Principles.md](./02_Evaluation_Principles.md). No agent may generate an assessment that violates the principle of evidence primacy, explainability, or human override authority.

### 3. Process Compliance
The sequence in which agents execute, consume each other's outputs, and contribute to the final report must follow the process architecture defined in [07_AI_Evaluation_Agent_Architecture.md](./07_AI_Evaluation_Agent_Architecture.md). No agent may short-circuit the defined pipeline.

---

## How Every AI Agent Must Follow These Standards

All agents in the TIDES evaluation pipeline — whether they assess founders, technology readiness, financial health, or market opportunity — must:

| Requirement | Description |
|---|---|
| **Evidence-first output** | Every finding must cite the source field, document section, or structured record from which it was derived |
| **Confidence declaration** | Every score must be accompanied by a confidence value (0.0–1.0) and a short justification of why that confidence level was assigned |
| **No hallucination** | If evidence is absent, the agent must state "Insufficient evidence" rather than infer or fabricate an answer |
| **Explainability** | Every score must be decomposable into the sub-criteria that contributed to it |
| **Human override path** | Every agent output is advisory. The platform must preserve a clear mechanism by which a human reviewer can override, amend, or reject any AI finding |
| **Sector awareness** | Agents must apply sector normalization as defined in [06_Sector_Normalization_Standard.md](./06_Sector_Normalization_Standard.md) before emitting any comparison-based finding |
| **Lifecycle awareness** | Agents must interpret metrics relative to the startup's declared lifecycle stage as defined in [03_Startup_Lifecycle_Framework.md](./03_Startup_Lifecycle_Framework.md) |
| **TRL anchoring** | Any technology assessment must reference the TRL framework defined in [04_TRL_Assessment_Standard.md](./04_TRL_Assessment_Standard.md) |
| **Scoring compliance** | All numerical scores must follow the methodology in [05_Scoring_Standard.md](./05_Scoring_Standard.md) |

---

## Long-Term Vision

TAES v1.0 is the foundation of a multi-year intellectual project. The standard is designed to evolve across successive versions:

| Version | Scope |
|---|---|
| **v1.0** | Internal incubator evaluation standard (current) |
| **v1.5** | Multi-incubator deployment with configurable weights |
| **v2.0** | Investor-grade evaluation with benchmark normalization |
| **v2.5** | Government startup programs with regulatory compliance layer |
| **v3.0** | International standard with cross-border sector calibration |

The platform is being built from the ground up to support this evolution. Every architectural decision made today must be validated against the question: *Does this decision allow TAES v2.0 and beyond to be implemented without rewriting the core?*

The answer must always be yes.

---

## Document Index

| File | Purpose |
|---|---|
| [README.md](./README.md) | This document. Entry point to the standard. |
| [01_Product_Vision.md](./01_Product_Vision.md) | Mission, vision, target users, and long-term product strategy |
| [02_Evaluation_Principles.md](./02_Evaluation_Principles.md) | Core principles every evaluation must follow |
| [03_Startup_Lifecycle_Framework.md](./03_Startup_Lifecycle_Framework.md) | Stage definitions from Idea to Scale |
| [04_TRL_Assessment_Standard.md](./04_TRL_Assessment_Standard.md) | Technology Readiness Level framework TRL 1–9 |
| [05_Scoring_Standard.md](./05_Scoring_Standard.md) | Complete scoring methodology across all pillars |
| [06_Sector_Normalization_Standard.md](./06_Sector_Normalization_Standard.md) | Sector-specific evaluation adjustments |
| [07_AI_Evaluation_Agent_Architecture.md](./07_AI_Evaluation_Agent_Architecture.md) | Multi-agent system design |
| [08_Report_Standard.md](./08_Report_Standard.md) | Official startup report design specification |
| [09_System_Architecture.md](./09_System_Architecture.md) | Platform architecture and data flow |
| [10_Product_Roadmap.md](./10_Product_Roadmap.md) | Phased roadmap from incubator to government platform |
| [glossary.md](./glossary.md) | Definitions of all technical and domain terms |

---

## Implementation Sequence

The recommended sequence for implementing TAES capabilities in the TIDES platform, designed to minimize technical debt and avoid disruption to existing functionality:

1. **Internalize this standard** — All engineering work from this point references TAES documents before any implementation begins
2. **Implement scoring schema** — Extend the database to store evidence-linked scores per pillar (05_Scoring_Standard)
3. **Implement lifecycle tagging** — Every startup record must carry a validated lifecycle stage (03_Startup_Lifecycle_Framework)
4. **Implement TRL fields** — Add TRL declarations to startup profiles (04_TRL_Assessment_Standard)
5. **Build sector normalization layer** — Introduce sector configuration as a runtime parameter (06_Sector_Normalization_Standard)
6. **Deploy evaluation agents incrementally** — Follow agent dependency order in 07_AI_Evaluation_Agent_Architecture
7. **Implement report renderer** — Build the report engine to the specification in 08_Report_Standard
8. **Expand to multi-incubator** — Gate on stable v1.0 operation before introducing multi-tenant architecture (10_Product_Roadmap Phase 3)

---

*This document and all documents in the `TAES_v1.0/` folder are authoritative. Conflicts between implementation code and this standard must be resolved in favour of this standard unless a formal exception is recorded and approved.*
