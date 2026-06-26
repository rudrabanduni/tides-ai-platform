# 01 — Product Vision

> **Document:** TAES v1.0 / Product Vision  
> **Classification:** Internal Technical Standard  
> **Version:** 1.0.0

---

## Mission

To provide every startup — regardless of sector, stage, or geography — with a rigorous, evidence-backed, AI-assisted evaluation that is as credible and reproducible as a well-designed institutional due diligence process.

The TIDES platform exists to eliminate the inconsistency, subjectivity, and opacity that characterises how most incubators, accelerators, and early-stage investors assess startups today.

---

## Vision

To become the world's most trusted AI-powered incubation intelligence infrastructure — adopted by incubators, academic institutions, venture capital firms, and government startup programs as the canonical framework for evaluating early-stage innovation.

The platform is not a tool. It is an institution. It is being designed to carry the credibility of a professional evaluation standard, not the permissiveness of a general-purpose AI assistant.

---

## Target Users

TIDES is designed to serve multiple stakeholder groups simultaneously, each with distinct needs and interaction patterns.

### Primary Users (Current Phase)

| User Type | Role | Primary Need |
|---|---|---|
| **Incubator Program Managers** | Upload startups, monitor evaluations, review scores | Efficient batch processing of large cohorts |
| **Incubator Mentors** | Review AI-generated assessments, add expert commentary | Evidence-quality assessment, human annotation |
| **Evaluation Committee Members** | Review final reports, approve or reject recommendations | Structured, consistent reports with clear reasoning |
| **Platform Administrators** | Manage users, configure rules, monitor system health | Operational control and auditability |

### Secondary Users (Near-Term Roadmap)

| User Type | Role | Primary Need |
|---|---|---|
| **Venture Capital Analysts** | Access evaluation reports on startups in deal pipeline | Pre-diligence intelligence, benchmark comparison |
| **Startup Founders** | Submit applications, receive feedback reports | Objective assessment of their current position |
| **Academic Researchers** | Access anonymised aggregate data for research | Validated datasets with methodology transparency |

### Tertiary Users (Long-Term Roadmap)

| User Type | Role | Primary Need |
|---|---|---|
| **Government Programme Officers** | Evaluate grant and scheme applicants at scale | Standardised, auditable evaluation with policy compliance |
| **Angel Networks** | Screen deal flow against investment-readiness criteria | Rapid filtering across a large, diverse deal pipeline |
| **Corporate Innovation Teams** | Evaluate startup partnerships and acquisition targets | Structured technology and IP readiness assessment |

---

## Problem Statement

The current state of startup evaluation is characterised by five structural failures:

### 1. Inconsistency at Scale
When an incubator cohort contains fifty startups evaluated across multiple mentors and committee members, each evaluator applies their own implicit framework. Two startups with similar fundamentals will receive materially different scores depending on who evaluated them and on which day.

### 2. Opaque Scoring
Most evaluation frameworks produce a number — a score, a rank, a grade — without a traceable chain of reasoning. A startup that scores 6.2 cannot determine which aspects of their business drove the score, which evidence was considered, or what they must change to score higher.

### 3. Sector Blindness
A biotech startup at TRL 4 with no revenue is not a failing startup — it is a completely normal biotech startup at an early clinical stage. Evaluating it against the same revenue metrics as a SaaS startup produces structurally misleading results. Most evaluation frameworks do not account for sector-specific maturity expectations.

### 4. AI Hallucination Risk
General-purpose AI tools applied to startup evaluation tend to produce confident-sounding assessments that are not grounded in the evidence actually provided. Without an evidence-first evaluation architecture, AI outputs are not trustworthy enough for institutional use.

### 5. No Institutional Memory
Each evaluation cohort starts from scratch. The platform accumulates no structured learning about what characteristics predict success in different sectors, stages, or markets. Every evaluation is isolated from every other.

---

## Product Philosophy

The TIDES platform is governed by the following philosophical commitments:

### Evidence Before Opinion
Every finding must be traceable to a specific piece of evidence. The platform does not permit AI agents to generate assessments based on pattern inference alone when specific evidence is absent. Absence of evidence must be declared, not papered over.

### Explainability as a Requirement
A score that cannot be explained to the startup being evaluated is not a valid score. Every numerical output must be decomposable into the sub-criteria that produced it, expressed in language that a non-technical reader can understand.

### The AI Is a Clerk, Not a Judge
The AI evaluation engine produces a structured brief — a comprehensive, evidence-organised dossier — that a human reviewer uses to make a decision. The AI does not decide. This is not a limitation; it is a design principle. The human decision-maker's judgment, experience, and accountability cannot and should not be replaced.

### Fairness Requires Normalisation
Comparing a SpaceTech startup at TRL 5 with an e-commerce startup at Revenue Stage using the same weights is not fair. Fairness in evaluation requires applying different expectations to different sectors and stages. The platform encodes this explicitly.

### The Platform Gets Smarter With Every Evaluation
Every evaluation that passes through the platform is an opportunity to refine benchmarks, calibrate confidence thresholds, and improve sector-specific expectations. The platform must be designed from the outset to accumulate institutional knowledge.

---

## Long-Term Roadmap

The platform is planned across six phases. The boundaries between phases are capability milestones, not calendar dates.

### Phase 1 — Internal Incubator Platform
**Status:** Active  
**Scope:** Single incubator, internal use only  
Core pipeline: intake → AI evaluation → report → human review

### Phase 2 — Enterprise Evaluation Engine
**Status:** Planned  
**Scope:** Multi-cohort, configurable scoring, benchmark analytics  
Introduces: configurable pillar weights, historical comparisons, mentor collaboration tools

### Phase 3 — Multi-Incubator SaaS
**Status:** Planned  
**Scope:** Multi-tenant architecture, per-organisation configuration  
Introduces: white-label reports, cross-incubator benchmarking, subscription model

### Phase 4 — Investor Intelligence Platform
**Status:** Future  
**Scope:** VC and angel network integration  
Introduces: investment readiness index, portfolio analytics, deal comparison

### Phase 5 — Government Startup Evaluation Platform
**Status:** Future  
**Scope:** Grant and scheme evaluation at national scale  
Introduces: policy compliance layer, audit trails meeting regulatory requirements, regional benchmarking

### Phase 6 — Founder Self-Evaluation Platform
**Status:** Future  
**Scope:** Direct-to-founder product  
Introduces: self-service evaluation, improvement tracking, mentor marketplace

---

## Why This Platform Is Different From Generic AI Evaluators

### Generic AI Tools
- Apply general language model reasoning to startup documents
- Produce plausible-sounding assessments without formal evidence anchoring
- Have no sector normalisation, lifecycle awareness, or TRL framework
- Cannot be audited or reproduced
- Are not trusted by institutional decision-makers

### TIDES Platform
- Applies a formal, versioned evaluation standard (TAES)
- Every output is evidence-anchored and confidence-scored
- Sector normalisation is a first-class platform feature
- Every evaluation is fully auditable and reproducible
- Designed to meet the credibility requirements of institutional stakeholders

---

## Path to SaaS for Incubators, VCs, Government, and Founders

The TIDES platform is architecturally positioned to become a multi-tenant SaaS product. The following considerations govern the SaaS expansion:

### For Incubators
- Dedicated tenant workspace with per-cohort configuration
- Configurable pillar weights matching the incubator's investment thesis
- White-label report branding
- Cohort benchmarking against anonymised peer data

### For Venture Capital Firms
- Evaluation API accessible from existing deal management systems
- Investment readiness indices calibrated to specific stage and sector
- Portfolio monitoring with periodic re-evaluation
- Benchmark comparisons against sector-specific acquisition and exit data

### For Government Agencies
- Multi-scheme support with distinct eligibility criteria per scheme
- Full audit log meeting public accountability standards
- Bulk evaluation at national programme scale
- Policy compliance layers that can be configured per regulation

### For Founders
- Self-service onboarding with guided data submission
- Preliminary evaluation before incubator application
- Improvement roadmap with specific, actionable guidance
- Progress tracking across evaluation cycles

---

*This document is authoritative for product strategy decisions. Engineering teams should validate all architectural choices against the long-term vision described here before committing to implementation.*
