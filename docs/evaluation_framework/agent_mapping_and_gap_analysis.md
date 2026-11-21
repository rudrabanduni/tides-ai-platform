# Existing Agent Mapping & Gap Analysis

**TIDES-AI Startup Evaluation Platform**  
**Phase 2:** Architecture Modernization & Agent Restructuring  
**Status:** Audit & Recommendations (Read-Only)

---

## 1. Executive Summary

This document evaluates the existing 8 domain expert agents, graph engines, and orchestration pipelines in the TIDES-AI codebase against the 6 authoritative evaluation domains derived from the **LaunchIndex Incubation Application Pitch Deck**.

### Core Findings
1. **High Reusability of Core Engine Architecture**:
   - The foundational pipeline (`ObservationGraph`, `ClaimEngine`, `AssessmentValidator`, `PromptManager`, and `ReportSerializer`) is well-engineered and directly reusable.
2. **Structural Mismatch in Domain Alignment**:
   - The current 8-agent topology (`Founder`, `Product`, `Market`, `Financial`, `TRL`, `Competition`, `IP`, `Risk`) fragments several unified pitch deck sections. Specifically, `Product` and `TRL` both assess Slide 3–5 criteria, while `Market` and `Competition` split Slide 6–7 criteria.
3. **Absence of an Adversarial LLM Reviewer**:
   - Current committee and executive synthesis (`ExecutiveEngine`, `InvestmentEngine`, `CommitteeDecisionEngine`) relies strictly on deterministic Python rule heuristics over graph nodes. There is no conversational or adversarial AI agent that challenges unsupported claims, reconciles domain contradictions, or requests targeted re-checks.
4. **Information Extraction Gaps**:
   - The initial extraction model (`StartupProfileExtraction`) captures only 20 atomic fields, missing 39 of the 87 canonical criteria required by the LaunchIndex template (e.g. 6-quarter roadmaps, customer payback, signed agreements vs MOUs, mentorship requirements, and SDG impacts).

---

## 2. Agent Mapping Matrix: Existing Experts to 6 Target Domains

The table below maps each active component to the new 6-domain architecture:

```
TARGET DOMAIN 1: Problem & Solution       ◄─── [ProductExpert] + [TRLExpert] (Merge into ProblemSolutionExpert)
TARGET DOMAIN 2: Market Opportunity       ◄─── [MarketExpert] + [CompetitionExpert] (Merge into MarketOpportunityExpert)
TARGET DOMAIN 3: Founder & Team           ◄─── [FounderExpert] (Adapt for multi-founder & advisor depth)
TARGET DOMAIN 4: Business & Commercial    ◄─── [FinancialExpert] (Partial) + New Commercialisation Criteria
TARGET DOMAIN 5: Innovation, IP & Impact  ◄─── [IPExpert] (Adapt to include data advantage, network effects & SDG impact)
TARGET DOMAIN 6: Financials & Support     ◄─── [FinancialExpert] (Adapt for 3-yr model, roadmap & TIDES support)
CROSS-DOMAIN:   Risk & Conflict           ◄─── [RiskExpert] + [ConflictResolutionEngine] (Cross-cutting synthesis)
FINAL REVIEW:   Adversarial Reviewer      ◄─── NEW AI Stage (Supervisory evaluation, challenging evidence)
```

### Detailed Agent Evaluation Matrix

| Existing Agent / Component | Current Responsibility | Current Input Schema | Current Output Schema | Assigned Canonical Criteria IDs | Architecture Recommendation | Dependencies & Implementation Risks | Recommended Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`FounderExpert`** (`app/modules/evaluation/founder_expert.py`) | Evaluates founder background, domain expertise, leadership, commitment, recruitment risk | `profile`, `claims`, `evidence`, `conflicts` filtered by `FounderContextFilter` | `AgentAssessment` (`domain="founder"`) | `FT-01` to `FT-13` (Domain 3) | **Adapt** | • Assumes single founder profile in several sub-checks.<br>• Missing mentor/advisor verification. | **Adapt & Expand**: Update prompts and context filter to evaluate all co-founders systematically, LinkedIn URLs, team skill gaps, and named advisors. |
| **`ProductExpert`** (`app/modules/evaluation/product_expert.py`) | Evaluates problem solved, solution value prop, product roadmap | `profile`, `claims`, `evidence`, `conflicts` filtered by `ProductContextFilter` | `AgentAssessment` (`domain="product"`) | `PS-01` to `PS-08`, `PS-11`, `PS-12` (Domain 1) | **Merge** | • Overlaps directly with `TRLExpert`.<br>• Does not evaluate conditional prototype evidence. | **Merge into `ProblemSolutionExpert`**: Combine with `TRLExpert` to create a unified Domain 1 evaluator covering problem, solution, 3 features, UVP, architecture, and prototype validation. |
| **`TRLExpert`** (`app/modules/evaluation/trl_expert.py`) | Evaluates Technology Readiness Level (TRL 1–9), technical validation | `profile`, `claims`, `evidence`, `conflicts` filtered by `TRLContextFilter` | `AgentAssessment` (`domain="trl"`) | `PS-09`, `PS-10`, `PS-13` (Domain 1) | **Merge** | • Evaluating TRL in isolation from product architecture produces repetitive report sections. | **Merge into `ProblemSolutionExpert`**: Absorb TRL analysis as a core dimension of the Problem & Solution domain. |
| **`MarketExpert`** (`app/modules/evaluation/market_expert.py`) | Evaluates target market, TAM/SAM/SOM, demographics | `profile`, `claims`, `evidence`, `conflicts` filtered by `MarketContextFilter` | `AgentAssessment` (`domain="market"`) | `MO-01` to `MO-06` (Domain 2) | **Merge** | • Market analysis without competitive positioning lacks strategic depth. | **Merge into `MarketOpportunityExpert`**: Combine with `CompetitionExpert` to assess market size, growth drivers, geographic focus, and the 3-competitor benchmark matrix in one coherent flow. |
| **`CompetitionExpert`** (`app/modules/evaluation/competition_expert.py`) | Evaluates competitor names, defensibility, and competitive moats | `profile`, `claims`, `evidence`, `conflicts` filtered by `CompetitionContextFilter` | `AgentAssessment` (`domain="competition"`) | `MO-07` to `MO-10` (Domain 2) | **Merge** | • Template requires exactly 3 competitors (including international), currently not enforced. | **Merge into `MarketOpportunityExpert`**: Enforce the 3-competitor requirement (including global players) within the combined market domain. |
| **`FinancialExpert`** (`app/modules/evaluation/financial_expert.py`) | Evaluates revenue model, funding raised, burn rate, runway | `profile`, `claims`, `evidence`, `conflicts` filtered by `FinancialContextFilter` | `AgentAssessment` (`domain="financial"`) | Split across:<br>• `BC-01` to `BC-06` (Domain 4)<br>• `FI-01` to `FI-09` (Domain 6) | **Split & Adapt** | • Conflates GTM commercialization (pricing, CAC, pilots) with financial accounting (burn, 3-yr model, break-even). | **Split Responsibilities**: Formulate a dedicated `CommercialisationExpert` for Domain 4 (GTM, customer pipeline, pricing, pilots) and adapt `FinancialExpert` for Domain 6 (3-yr model, burn, support needs, 6-quarter roadmap). |
| **`IPExpert`** (`app/modules/evaluation/ip_expert.py`) | Evaluates patents, trademarks, licensing, and IP defensibility | `profile`, `claims`, `evidence`, `conflicts` filtered by `IPContextFilter` | `AgentAssessment` (`domain="ip"`) | `II-01` to `II-11` (Domain 5) | **Adapt & Expand** | • Currently focuses almost solely on filed patents.<br>• Fails to evaluate non-patent innovation, data moats, switching costs, or ESG/SDG impact. | **Adapt into `InnovationImpactExpert`**: Retain patent analysis but expand prompt and schema to evaluate data moats, switching costs, SDG alignment (`II-09`), and measurable impact metrics (`II-10`). |
| **`RiskExpert`** (`app/modules/evaluation/risk_expert.py`) | Identifies, classifies, and scores cross-domain risks | `profile`, `claims`, `evidence`, `conflicts` filtered by `RiskContextFilter` | `AgentAssessment` (`domain="risk"`) | Cross-domain risk synthesis | **Retain as Cross-Domain Auditor** | • Running as an isolated early domain expert duplicates domain-level risk findings in the other 7 agents. | **Reposition to Post-Domain Risk Synthesis**: Execute after domain experts to aggregate, deduplicate, and stress-test composite risks across the entire knowledge graph. |
| **`ConflictResolutionEngine`** (`app/modules/evaluation/conflict_resolution/`) | Resolves factual, numeric, and temporal conflicts in the graph | `ObservationGraph` | Resolved `ObservationGraph` | Cross-domain conflict resolution | **Retain & Extend** | • Currently deterministic rule engine; does not synthesize narrative explanations for complex contradictions. | **Retain**: Keep as deterministic pre-filter for the final review stage. |
| **`ExecutiveEngine` & `InvestmentEngine`** | Compiles executive assessment and calculates investment score (0–100) | `ObservationGraph` | Enriched `ObservationGraph` | Cross-domain executive conclusions | **Retain & Align** | • Scoring formulas must be aligned with approved committee criteria rather than arbitrary heuristics. | **Retain**: Provide deterministic baseline scores feeding into the final review stage. |
| **`CommitteeDecisionEngine`** | Generates recommendation (`INCUBATE`, `DEFER`, `REJECT`) | `ObservationGraph` | Enriched `ObservationGraph` with committee decision | Final recommendation rationale | **Retain & Extend** | • Purely deterministic logic based on thresholds. | **Retain**: Keep deterministic governance logic while allowing the Final Reviewer to validate conditionality. |

---

## 3. Analysis of the Final Review Stage

### Current Implementation Status: **Missing as an AI Agent**
In the existing codebase, the "final review" is split between two purely deterministic Python classes:
1. `ExecutiveEngine.generate(graph)`: Concatenates domain strengths/weaknesses and picks highest-severity risks.
2. `CommitteeDecisionEngine.generate(graph)`: Applies hardcoded mathematical rules (e.g. if investment score $\ge 70$ and critical risks $== 0 \implies \text{INCUBATE}$).

### Why an AI Final Reviewer is Required
1. **Adversarial Scrutiny**: Domain expert agents tend to accept pitch deck statements at face value within their narrow domain. An AI Final Reviewer evaluates whether individual conclusions are *justified by the underlying evidence*.
2. **Cross-Domain Contradiction Detection**: If `ProductExpert` reports that the product is a finished enterprise SaaS platform, while `FinancialExpert` reports ₹0 R&D spend and `FounderExpert` notes no software engineering capability, the Final Reviewer catches this material contradiction.
3. **Targeted Re-Checks (Without Full Re-Execution)**: Rather than restarting the entire 6-agent evaluation, the Final Reviewer can flag an unsupported claim and request a single domain re-check with specific adversarial prompts.
4. **Distinction Between Claims and Proof**: Ensures that non-binding MOUs are not treated as guaranteed revenue, and trial users are not reported as paying customers.

---

## 4. Architectural Gaps & Mitigation Strategy

```
┌────────────────────────────────────────────────────────────────────────┐
│                          Identified Codebase Gaps                      │
└────────────────────────────────────────────────────────────────────────┘
                                    │
    ┌───────────────────────────────┼───────────────────────────────┐
    ▼                               ▼                               ▼
[GAP 1: Ingestion Depth]        [GAP 2: Agent Topology]       [GAP 3: Review Stage]
• 39 missing criteria           • 8 fragmented agents         • No adversarial review
• Single-founder assumption     • Duplicate TRL/Product       • Purely heuristic rules
• No pilot/LOI distinction      • Isolated competition        • No targeted re-checks
```

### Gap 1: Ingestion & Extraction Schema Deficiencies
- **Problem**: `StartupProfileExtraction` currently has only 20 fields. Essential criteria such as the 6-quarter roadmaps (`FI-16` to `FI-19`), SDG alignment (`II-09`), verified LinkedIn profiles (`FT-02`), and mentor details (`FT-10`) are dropped during initial deck extraction.
- **Mitigation**: Expand `StartupProfileExtraction` into modular domain sub-schemas matching the 87 canonical criteria defined in `canonical_criteria_registry.md`.

### Gap 2: Inappropriate Domain Boundaries
- **Problem**: 8 agents lead to fragmentation, context duplication, and higher token latency. `Product` and `TRL` inspect the same slides (3–5); `Market` and `Competition` inspect the same slides (6–7).
- **Mitigation**: Consolidate into **6 Domain Specialist Agents**:
  1. `ProblemSolutionExpert` (Slides 3–5)
  2. `MarketOpportunityExpert` (Slides 6–7)
  3. `FounderTeamExpert` (Slides 8–10)
  4. `CommercialisationExpert` (Slides 11–12)
  5. `InnovationImpactExpert` (Slides 13–14)
  6. `FinancialsSupportExpert` (Slides 15–18)

### Gap 3: Lack of Evidence Severity in Commercial Claims
- **Problem**: Current parsers do not distinguish between unsigned expressions of interest and signed commercial contracts (`BC-10`), or between active paying customers and free community users (`BC-08`).
- **Mitigation**: Enforce evidence typing in `ClaimEngine` and `CommercialisationExpert` prompt constraints:
  - `CONTRACT_SIGNED` vs `MOU_NON_BINDING` vs `VERBAL_INTEREST`
  - `REVENUE_AUDITED` vs `REVENUE_SELF_REPORTED` vs `PROJECTED`

### Gap 4: Deterministic-Only Governance
- **Problem**: Committee recommendation cannot explain nuanced or conditional edge cases (e.g. strong science venture with unbuilt commercial roadmap).
- **Mitigation**: Introduce a supervisory **Committee Review Agent** that operates on the complete `ObservationGraph`, reconciles cross-domain findings, and generates a defensible recommendation memorandum before PDF serialization.
