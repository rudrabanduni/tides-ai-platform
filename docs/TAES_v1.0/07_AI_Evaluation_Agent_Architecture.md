> **Document:** TAES v1.0 / AI Evaluation Agent Architecture
> **Classification:** Internal Technical Standard
> **Version:** 1.0.0
> **Status:** Ratified
> **Authored by:** TIDES Platform Architecture Board
> **Last Revised:** 2026-06-23
> **Document ID:** TAES-DOC-007

---

# TAES v1.0 — AI Evaluation Agent Architecture

## Table of Contents

1. [Introduction](#1-introduction)
   1. [Multi-Agent Evaluation Philosophy](#11-multi-agent-evaluation-philosophy)
   2. [Why Multi-Agent over Monolithic Evaluation](#12-why-multi-agent-over-monolithic-evaluation)
   3. [The Principle of Specialisation](#13-the-principle-of-specialisation)
   4. [The Dependency Graph](#14-the-dependency-graph)
   5. [The Coordination Model](#15-the-coordination-model)
   6. [The Governance Model](#16-the-governance-model)
   7. [The Output Contract](#17-the-output-contract)
2. [Agent Definitions](#2-agent-definitions)
   1. [Knowledge Extraction Agent](#21-knowledge-extraction-agent)
   2. [Founder Evaluation Agent](#22-founder-evaluation-agent)
   3. [Product Evaluation Agent](#23-product-evaluation-agent)
   4. [TRL Assessment Agent](#24-trl-assessment-agent)
   5. [Market Intelligence Agent](#25-market-intelligence-agent)
   6. [Competition Analysis Agent](#26-competition-analysis-agent)
   7. [Financial Analysis Agent](#27-financial-analysis-agent)
   8. [Patent and IP Agent](#28-patent-and-ip-agent)
   9. [Risk Assessment Agent](#29-risk-assessment-agent)
   10. [Recommendation Agent](#210-recommendation-agent)
   11. [Mentorship Matching Agent](#211-mentorship-matching-agent)
   12. [Committee Preparation Agent](#212-committee-preparation-agent)
3. [Agent Orchestration](#3-agent-orchestration)
4. [Error Handling and Low-Confidence Management](#4-error-handling-and-low-confidence-management)
5. [Agent Output Contract — Standard Schema](#5-agent-output-contract--standard-schema)
6. [TAES Compliance Enforcement](#6-taes-compliance-enforcement)
7. [Data Flow Pipeline](#7-data-flow-pipeline)
8. [Extensibility — Adding New Agents](#8-extensibility--adding-new-agents)
9. [Glossary](#9-glossary)

---

## 1. Introduction

### 1.1 Multi-Agent Evaluation Philosophy

The TIDES AI Evaluation Standard (TAES v1.0) is built on the foundational premise that a startup evaluation is not a single cognitive act — it is a structured inquiry across multiple independent but interlocking knowledge domains. A founding team assessment requires expertise in human capital analysis, career trajectory pattern recognition, and team composition theory. A market analysis requires domain knowledge of sector-specific growth drivers, addressable market calculation methodologies, and timing pattern recognition. A technology evaluation requires familiarity with readiness level frameworks, engineering risk models, and validation milestone standards.

No single evaluation system, human or artificial, is equally authoritative across all of these domains simultaneously. This is not a limitation of intelligence — it is the nature of deep domain knowledge. The TAES multi-agent architecture is designed to honour this reality by decomposing the evaluation problem into specialised agents, each responsible for one well-bounded domain, each capable of producing its outputs with the rigour of a domain expert, and each contributing its findings to a coordinated synthesis that constitutes the final evaluation.

The philosophy is not one of parallel redundancy — agents are not evaluating the same information from different angles. The philosophy is one of serial dependency and structured synthesis. Each agent contributes unique findings. Each agent's output is a primary input for one or more downstream agents. The final Recommendation Agent sees the world through the combined lens of all upstream agents, armed with structured, evidence-grounded findings it could not have produced alone.

This architecture treats evaluation as a knowledge pipeline, not a prompt. It is the architectural embodiment of the TAES principle that every claim must be traceable to evidence, every score must be supported by a justification, and every recommendation must be auditable from input to output.

### 1.2 Why Multi-Agent over Monolithic Evaluation

A monolithic evaluation approach — one in which a single agent receives all application materials and produces a complete evaluation — suffers from fundamental structural weaknesses that make it unsuitable for enterprise-grade startup evaluation.

**Context dilution.** A monolithic agent processing all materials simultaneously is forced to attend to all domains at once. This produces evaluations that are broad but shallow. The depth of analysis required to assess a founder's CTO-adequacy, for example, requires sustained, domain-focused reasoning. A monolithic agent cannot maintain equivalent depth across twelve separate domains within a single inference.

**Untraceability.** When a monolithic agent produces a final score or recommendation, the reasoning path from evidence to conclusion is collapsed into a single output. It is not possible to audit which document informed which score. A multi-agent architecture, by contrast, makes reasoning traceable at every step: the Founder Evaluation Agent's score is derived from specific founder record fields; that score is then consumed — explicitly, by reference — by the Recommendation Agent.

**Hallucination amplification.** A monolithic agent operating across many domains is more prone to filling knowledge gaps with generated content, because the volume of material and the breadth of required expertise creates more opportunities for the model to depart from evidence. Specialised agents, by contrast, have narrower attention windows and are constrained by their domain-specific output schemas to report absences of evidence explicitly rather than invent content.

**Maintainability.** When evaluation criteria change — for example, when the TRL framework updates, or when the financial evaluation adds a new unit economics component — a monolithic architecture requires the entire evaluation system to be re-validated. A modular multi-agent architecture allows individual agents to be updated, re-validated, and re-deployed without affecting unrelated agents.

**Parallelism.** Many evaluation domains are independent of one another. Market analysis and IP evaluation, for example, can proceed concurrently without waiting for each other. A multi-agent architecture enables genuine parallel computation, reducing total evaluation latency.

**Specialisation fidelity.** Agents that are architecturally scoped to a single domain can be engineered, tested, and benchmarked against domain-specific evaluation standards. This enables quality assurance at the domain level, which is not possible with a monolithic agent.

For all of these reasons, TAES v1.0 specifies a twelve-agent architecture as the normative evaluation infrastructure for the TIDES platform.

### 1.3 The Principle of Specialisation

Specialisation in the TAES architecture is defined architecturally, not merely by prompt framing. Each agent is assigned a formal domain boundary. Domain boundaries are defined by three criteria:

1. **Input exclusivity.** Each agent has a defined set of input fields and documents it is authorised to reason over. An agent cannot introduce information from outside its assigned input set into its reasoning.

2. **Output scope.** Each agent produces a structured output schema that covers only its domain. The Financial Analysis Agent does not produce a score on founder quality. The Founder Evaluation Agent does not produce financial runway estimates. Scope discipline is enforced by the output schema, not by instruction alone.

3. **Evaluation criteria ownership.** Each agent is the sole owner of the evaluation criteria relevant to its domain. The TRL Assessment Agent owns the TRL scale definition and its application. No other agent may produce a TRL score. Downstream agents consume the TRL Assessment Agent's output but do not recompute or re-interpret it.

Specialisation has a further important consequence: it enables domain-specific confidence calibration. A confidence score produced by the Founder Evaluation Agent is calibrated against the evidence density typical of founder evaluation domains. A confidence score produced by the Financial Analysis Agent is calibrated against the evidence requirements typical of financial evaluation. Cross-domain confidence scores are not directly comparable in magnitude — they are comparable in meaning, because each has the same structural interpretation: the degree to which available evidence supports the agent's conclusions.

### 1.4 The Dependency Graph

The TAES multi-agent architecture is structured around a formal dependency graph. The dependency graph specifies which agents must complete execution before a downstream agent may begin. The graph has three tiers:

**Tier 0 — Foundation Layer.** The Knowledge Extraction Agent occupies Tier 0. It is the only agent that reads directly from raw application materials. All other agents consume the structured output of the Knowledge Extraction Agent as their primary data source. No agent in Tiers 1 or 2 reads raw documents directly.

**Tier 1 — Domain Analysis Layer.** Seven agents operate in Tier 1, all consuming Knowledge Extraction Agent outputs as their foundation, plus, where applicable, outputs from peer Tier 1 agents. These agents are: Founder Evaluation Agent, Product Evaluation Agent, TRL Assessment Agent, Market Intelligence Agent, Competition Analysis Agent, Financial Analysis Agent, and Patent and IP Agent. Within Tier 1, where a peer dependency exists — for example, the Competition Analysis Agent consuming market segmentation outputs from the Market Intelligence Agent — a partial ordering is observed. The majority of Tier 1 agents can execute concurrently.

**Tier 2 — Synthesis Layer.** The Risk Assessment Agent operates at the boundary of Tier 1 and Tier 2. It requires all Tier 1 domain agents to complete before it can execute, because it synthesises risks across all dimensions. Above Risk Assessment, the Recommendation Agent, Mentorship Matching Agent, and Committee Preparation Agent occupy full Tier 2 positions and require all Tier 1 and Tier 2 prerequisite agents to complete.

The dependency graph is formally specified in the Orchestration section (Section 3) and represented as a step-by-step pipeline in the Data Flow section (Section 7).

### 1.5 The Coordination Model

The TAES architecture uses a centralised orchestration model. A dedicated orchestration controller — referred to throughout this document as the Orchestration Controller — is responsible for:

1. Receiving the raw evaluation trigger for a specific startup application.
2. Invoking the Knowledge Extraction Agent and waiting for its structured output.
3. Determining which Tier 1 agents can be invoked in parallel, based on the dependency graph.
4. Routing the appropriate structured outputs from upstream agents to each downstream agent as inputs.
5. Monitoring agent completion status and confidence levels.
6. Escalating to human review queues when an agent reports a confidence score below the TAES minimum threshold or encounters an unresolvable data gap.
7. Collecting the outputs of all agents and routing them to the Recommendation Agent, Mentorship Matching Agent, and Committee Preparation Agent.
8. Assembling the final evaluation package.

The Orchestration Controller is not itself an evaluation agent. It does not produce evaluation outputs, scores, or recommendations. Its sole responsibility is coordination. This separation ensures that evaluation logic cannot be contaminated by coordination logic and vice versa.

The coordination model does not use peer-to-peer agent communication. Agents do not call one another directly. All communication flows through the Orchestration Controller, which acts as the message bus, input router, and output collector. This design enables complete auditability of all inter-agent data flows, since every transmission is logged by the Orchestration Controller.

### 1.6 The Governance Model

TAES governance over the multi-agent architecture is enforced through three mechanisms:

**Schema enforcement.** Every agent must produce output that conforms to the TAES Agent Output Contract (Section 5). Outputs that do not validate against the schema are rejected by the Orchestration Controller and the agent is flagged for re-execution or human escalation.

**Evidence traceability requirements.** Every scored field in every agent output must reference the specific input field, document identifier, or upstream agent output field from which the score was derived. Scores produced without traceable evidence references are treated as unvalidated and are quarantined from the final evaluation package.

**Confidence floor enforcement.** TAES specifies a system-wide minimum confidence floor. Any agent producing a confidence score below this floor on any primary output field triggers the escalation protocol. The Orchestration Controller routes the flagged field and its associated evidence gaps to a human reviewer. The reviewer either supplements the evidence and re-triggers the agent or records a formal evidence-absent notation in the final report.

The governance model ensures that the TAES principles of evidence-first evaluation, no-hallucination output, and auditable scoring are structurally enforced — not merely stated as aspirations. Compliance is not dependent on agent instruction adherence alone; it is enforced by the schema, the evidence traceability requirement, and the confidence floor mechanism operating together as a three-layer governance stack.

### 1.7 The Output Contract

Every agent in the TAES architecture must conform to the Agent Output Contract. The Output Contract is a formal schema that specifies the required fields, data types, and metadata every agent output must contain, regardless of domain-specific content. The full schema is specified in Section 5. In summary, every agent output must include:

- **Agent identity fields:** Agent name, agent version, execution timestamp, and execution duration.
- **Input manifest:** A list of every input field, document, and upstream agent output consumed during execution, with identifiers.
- **Primary output fields:** Domain-specific scored and narrative fields, each tagged with a confidence score and an evidence reference list.
- **Data gap register:** A structured list of information items that were absent, ambiguous, or unverifiable, with an assessment of the impact of each gap on output confidence.
- **Confidence summary:** An aggregate confidence score for the agent's primary output, computed from the field-level confidence scores.
- **Escalation flag:** A boolean field indicating whether the agent's confidence summary falls below the TAES minimum confidence floor and therefore requires human review.
- **Downstream routing manifest:** A list of downstream agents that are expected to consume this agent's output, enabling the Orchestration Controller to manage handoffs.

The Output Contract is the structural mechanism through which the governance model is operationalised. An agent that cannot produce a valid Output Contract-compliant output is considered to have failed execution, regardless of the content of its domain-specific fields.

---

## 2. Agent Definitions

---

### 2.1 Knowledge Extraction Agent

#### Mission

The Knowledge Extraction Agent is the foundation of the entire TAES evaluation pipeline. Its mission is to ingest all raw application materials submitted by a startup — including structured forms, uploaded documents, pitch decks, financial statements, CVs, patent filings, and any supplementary attachments — and to transform that heterogeneous collection of raw information into a single, normalised, structured data object that all downstream agents can consume without further parsing or interpretation of raw documents. The Knowledge Extraction Agent is the only agent in the TAES architecture that reads raw source materials directly. It acts as the data normalisation and entity extraction layer for the entire evaluation system.

#### Responsibilities

1. Ingest all raw application materials received from the startup application intake system, including structured form submissions, uploaded file attachments, and any linked external documents.
2. Parse structured form fields and map each field value to its canonical TAES data schema identifier, flagging any fields submitted in non-standard formats.
3. Extract unstructured text from uploaded documents — including PDFs, Word documents, presentations, and spreadsheets — using document parsing protocols, and segment the extracted text into named document sections.
4. Identify and extract named entities from all source materials, including: person names and roles, organisation names and relationships, geographic locations, dates and time periods, monetary figures and currencies, product names and descriptions, technology names, and competitor names.
5. Normalise all extracted monetary figures to a common currency and reporting period, flagging inconsistencies between figures reported across different documents.
6. Identify and record all factual claims made in source materials that are capable of independent verification, tagging each claim with its source document identifier and page or section reference.
7. Detect and record all internal inconsistencies across source materials — for example, a revenue figure stated differently in the application form and the financial statement — and flag each inconsistency with its source references for downstream agent attention.
8. Produce a data completeness assessment identifying which expected data fields across all evaluation domains are present, absent, or partially provided, enabling downstream agents to know in advance the evidence landscape they will encounter.
9. Assign a unique document identifier and version stamp to each source document, maintaining a document registry that downstream agents reference when citing evidence.
10. Produce the normalised Startup Evaluation Data Object (SEDO) that serves as the universal input for all Tier 1 domain agents.

#### Inputs

- **Raw application form submission:** All structured fields submitted by the startup through the TIDES application intake system, including company details, founder details, product description, market description, traction data, funding history, and any other form sections defined in the active TIDES application form version.
- **Uploaded document attachments:** All files uploaded by the startup as part of their application, including but not limited to: pitch deck, financial model or statements, founder CVs or LinkedIn exports, product roadmap documents, customer references or letters of intent, patent filings or IP certificates, team organisation chart, and any supplementary materials.
- **Application metadata:** Application submission timestamp, application form version, TIDES intake cohort identifier, and any reviewer notes recorded during initial intake screening.
- **TAES Canonical Data Schema:** The schema definition specifying all expected data fields, their types, validation rules, and domain classifications.

#### Outputs

The Knowledge Extraction Agent produces one primary structured output: the **Startup Evaluation Data Object (SEDO)**. The SEDO contains the following sections:

- **Company Profile Block:** Normalised company registration details, incorporation date and jurisdiction, registered address, primary sector classification (using TAES sector taxonomy), stage designation, and contact information.
- **Founder Record Set:** A structured record for each founder including: full name, role, equity percentage, prior company history (name, role, duration, outcome), educational background (institution, degree, year), domain expertise claims, and LinkedIn or public profile URL.
- **Product Description Block:** Normalised product name, product category, problem statement, solution description, unique value proposition statement, current development status, primary technology stack description, and list of customer validation evidence items.
- **Market Data Block:** Primary target market, total addressable market (TAM) figure and source, serviceable addressable market (SAM) figure and source, serviceable obtainable market (SOM) figure and source, market growth rate claim and source, and geographic scope.
- **Financial Data Block:** All monetary figures extracted from financial documents and forms, normalised to common currency and period, with source document references for each figure.
- **Traction Evidence Block:** List of all traction claims made in source materials, each tagged with: claim type (revenue, users, pilots, LOIs, partnerships), claimed value, period, and source document reference.
- **IP Data Block:** All IP assets identified in source materials, including patent application numbers, registration jurisdictions, filing dates, and any trade secret or proprietary technology claims.
- **Document Registry:** A list of all source documents, each with a unique identifier, document type classification, file name, ingestion timestamp, and extraction quality score.
- **Inconsistency Register:** A structured list of detected internal inconsistencies, each specifying the conflicting claims, their source document identifiers, and a severity classification.
- **Data Completeness Map:** A field-by-field map of all expected TAES input fields, indicating for each field whether it is: present and verified, present and unverified, partially provided, or absent.

#### Dependencies

The Knowledge Extraction Agent has no upstream agent dependencies. It is the entry point of the evaluation pipeline and may begin execution as soon as a valid application package is received and validated by the Orchestration Controller. Its only prerequisite is the successful reception of at least a minimum complete application submission, as defined by the TIDES Application Completeness Policy.

#### Evaluation Rules

1. **No interpretation rule.** The Knowledge Extraction Agent must not evaluate, score, or interpret the quality of any information it extracts. Its role is exclusively extraction, normalisation, and structuring. Any evaluative judgement — whether a founder's background is strong or weak, whether a market size claim is credible — belongs exclusively to domain evaluation agents in Tier 1.
2. **Source attribution mandatory.** Every extracted data point in the SEDO must carry a reference to its source document identifier and, where applicable, the specific page, section, or field within that document. Extracted data without a traceable source must be marked as source-unattributed and flagged in the Inconsistency Register.
3. **Conflict recording, not resolution.** Where the same data point appears with different values in different source documents, the agent must record all conflicting values with their respective sources. It must not resolve the conflict by selecting one value as authoritative. Conflict resolution is delegated to the relevant domain agent.
4. **Absence recording.** Where an expected data field is absent from all source materials, the agent must record its absence explicitly in the Data Completeness Map. It must not substitute a default value, estimate, or inferred value for any absent field.
5. **Currency normalisation standard.** All monetary figures must be converted to the reporting currency specified in the TAES Platform Configuration (default: INR and USD dual-reported). Conversion must use the exchange rate as of the application submission date, with the rate source and date recorded in the SEDO Financial Data Block.
6. **Document extraction quality scoring.** For each source document, the agent must produce an extraction quality score (0–100) indicating the degree to which the document's content was successfully parsed and extracted. Documents scoring below the extraction quality threshold specified in the TAES Platform Configuration must be flagged for manual review.
7. **Structured field priority.** Where the same information is present in both a structured form field and an unstructured document, the structured form field value takes precedence for populating the SEDO. The document-sourced value is recorded as a supplementary reference.

#### Expected Deliverables

The Knowledge Extraction Agent's primary deliverable to the overall evaluation is the Startup Evaluation Data Object (SEDO), which constitutes the universal data layer for the entire evaluation. The quality of all downstream agent outputs is bounded by the quality of the SEDO. The agent also delivers the Document Registry, the Inconsistency Register, and the Data Completeness Map, each of which is consumed by multiple downstream agents and included in the final evaluation package as audit artefacts.

#### Interaction with Other Agents

The SEDO is the primary input for all seven Tier 1 domain evaluation agents: Founder Evaluation Agent, Product Evaluation Agent, TRL Assessment Agent, Market Intelligence Agent, Competition Analysis Agent, Financial Analysis Agent, and Patent and IP Agent. Each of these agents receives a domain-scoped projection of the SEDO — only the sections and fields relevant to their domain — rather than the full SEDO, to enforce the input exclusivity principle of specialisation. The Document Registry is consumed by all downstream agents for source citation. The Inconsistency Register is consumed by the Risk Assessment Agent as a primary risk input. The Data Completeness Map is consumed by the Risk Assessment Agent and the Recommendation Agent to characterise evidence gaps.

---

### 2.2 Founder Evaluation Agent

#### Mission

The Founder Evaluation Agent exists to produce a rigorous, evidence-grounded assessment of the founding team of a startup applying to the TIDES programme. Its mission is to evaluate the collective and individual quality of the founding team across the dimensions most predictive of startup success: prior entrepreneurial and professional experience, domain expertise, leadership and execution capability, team composition and complementarity, equity and commitment structure, and team completeness relative to the startup's current stage and needs. The agent must produce findings that a human investment committee member could use to form a well-grounded view of whether this team has the capability to build and scale the company they are proposing.

#### Responsibilities

1. Evaluate each founder's prior professional experience, identifying roles, tenures, seniority levels, and the nature of organisations they have worked in, with particular attention to startup, high-growth, or sector-relevant experience.
2. Assess each founder's domain expertise in the startup's stated primary sector, distinguishing between claimed expertise and verifiable expertise supported by employment history, publications, patents, advisory roles, or other documented evidence.
3. Evaluate each founder's prior entrepreneurial experience, including the number, nature, funding levels, and outcomes of prior ventures, distinguishing between first-time founders and serial founders.
4. Assess the team's educational background, noting institutions, degree types, fields of study, and advanced degrees, with attention to their relevance to the startup's technology and market domain.
5. Evaluate team composition for coverage of the key functional roles required at the startup's current stage — typically technology leadership, business development and sales leadership, and product leadership — and identify any critical functional gaps.
6. Assess the completeness and complementarity of the founding team, identifying whether the combination of founder skills, experiences, and networks collectively covers the key execution challenges the startup faces.
7. Evaluate the equity distribution and vesting structure of the founding team, identifying concentration risks, absent vesting schedules, or founder commitment signals.
8. Assess the founding team's network quality in the relevant sector and geography, using advisory board composition, prior investor relationships, and documented partnerships as proxies.
9. Identify any red flags in the founder record set — including undisclosed gaps in employment history, inconsistencies between claimed and documented experience, or very short tenures at multiple prior organisations.
10. Produce a structured team assessment score across all evaluated dimensions, with per-dimension justifications and an overall team quality designation.

#### Inputs

- **Founder Record Set** from the SEDO, containing all normalised founder data including names, roles, equity percentages, professional histories, educational backgrounds, and domain expertise claims.
- **Company Profile Block** from the SEDO, for context on the startup's sector, stage, and primary technology domain.
- **Document Registry** from the Knowledge Extraction Agent, for referencing CVs, LinkedIn exports, and any other founder-related documents during evidence citation.
- **Data Completeness Map** from the Knowledge Extraction Agent, indicating which founder data fields are absent or partially provided.
- **Inconsistency Register** from the Knowledge Extraction Agent, filtered for entries related to founder information.

#### Outputs

The Founder Evaluation Agent produces the **Founder Evaluation Report (FER)**, containing:

- **Individual Founder Profiles:** For each founder: a structured assessment of professional experience (years, seniority, sector relevance, startup experience), domain expertise rating (0–10 with justification), entrepreneurial experience rating (0–10 with justification), educational relevance rating (0–10 with justification), and red flag notations.
- **Team Composition Assessment:** Evaluation of functional coverage (which key roles are present and which are absent), team complementarity score (0–10), team size assessment relative to stage, and identification of critical hiring needs.
- **Team Quality Scores:** Numerical scores (0–10) for each of: prior experience, domain expertise, entrepreneurial track record, educational background, network quality, team completeness, and commitment structure.
- **Overall Team Quality Designation:** A categorical designation from the TAES Founder Quality Scale: Exceptional, Strong, Adequate, Developing, or Insufficient, with a written justification.
- **Critical Gaps Register:** A structured list of identified team capability gaps, each classified by severity (Critical, Significant, Minor) and associated with a recommended mitigation (hire, advisory appointment, or mentorship).
- **Evidence Reference Map:** For each scored dimension, the specific SEDO fields, document identifiers, and page references from which the score was derived.
- **Confidence Scores:** Field-level and aggregate confidence scores for all primary output fields.

#### Dependencies

- **Knowledge Extraction Agent** must complete execution and produce a valid SEDO before the Founder Evaluation Agent can begin.
- No other Tier 1 agent outputs are required as inputs for the Founder Evaluation Agent. It operates independently of peer domain agents.

#### Evaluation Rules

1. **Claimed vs. evidenced experience distinction.** Every experience or expertise claim made by a founder must be classified as either "evidenced" (supported by a verifiable document or structured data field) or "claimed" (present only in the founder's own narrative). Scores must reflect only evidenced claims at full weight; claimed-only items must be scored at a discounted weight, documented in the output.
2. **No inferential credential assignment.** The agent must not infer credentials or experience that are not explicitly documented. For example, if a founder's CV does not state their role at a prior company, the agent must not infer the role from the company's industry or stage.
3. **Consistent scaling.** All numerical scores must be produced on the same 0–10 scale with the same anchor definitions as specified in the TAES Founder Scoring Rubric. No agent-internal re-scaling is permitted.
4. **Red flag mandatory reporting.** All identified red flags — including employment gaps, inconsistencies, very short tenures, and absent vesting schedules — must be reported, regardless of the overall team quality designation. Red flags must not be suppressed or minimised in the interest of producing a favourable overall designation.
5. **Team gap neutrality.** The agent must report team capability gaps objectively. A finding that the team lacks a CTO-equivalent must be reported and scored as a gap even if the founding team's overall quality is otherwise high.
6. **No outcome prediction.** The agent must not make predictive statements about whether the founders will succeed. It produces an assessment of current team quality, not a forecast of outcomes.
7. **Equity structure completeness.** If vesting schedules, cliff periods, or advisor equity structures are absent from the submission, the agent must record their absence as a data gap and reduce confidence on commitment structure scoring accordingly.
8. **Comparative benchmarking reference.** Where the agent applies a quality designation, the output must reference the typical characteristics of that designation level as defined in the TAES Founder Quality Scale, enabling the committee to understand the designation in a standardised context.

#### Expected Deliverables

The Founder Evaluation Agent delivers the Founder Evaluation Report as a standalone section of the final evaluation package. This report is used directly by the investment committee to form their view of team quality. It also serves as a primary input for the Risk Assessment Agent (team risk dimension), the Recommendation Agent (team quality dimension of the final score), and the Mentorship Matching Agent (which uses the Critical Gaps Register to identify mentorship needs).

#### Interaction with Other Agents

- **Risk Assessment Agent** consumes the Critical Gaps Register, individual founder red flag notations, and the Overall Team Quality Designation as inputs to the team risk dimension of its risk assessment.
- **Recommendation Agent** consumes the Overall Team Quality Designation and the Team Quality Scores as inputs to the team quality component of the final recommendation.
- **Mentorship Matching Agent** consumes the Critical Gaps Register and the Team Composition Assessment to identify functional and domain gaps that require mentorship support.
- **Committee Preparation Agent** consumes the full Founder Evaluation Report for inclusion in committee briefing materials.

---

### 2.3 Product Evaluation Agent

#### Mission

The Product Evaluation Agent exists to produce a structured, evidence-grounded assessment of the startup's product or service offering. Its mission is to evaluate whether the product is clearly defined, meaningfully differentiated from alternatives, at an appropriate stage of development for the startup's claimed stage, and validated by real or prospective customers. The agent applies a consistent evaluation framework to assess product clarity, value proposition strength, differentiation depth, development maturity, and the quality and quantity of customer validation evidence. It translates diverse product descriptions and claims into a standardised assessment that enables investment committee members who are not domain technologists to form a well-grounded view of the product's strength and readiness.

#### Responsibilities

1. Evaluate the clarity and specificity of the product description, assessing whether the problem being solved is clearly articulated, the target customer is specifically identified, and the solution mechanism is concretely described.
2. Assess the strength of the stated unique value proposition, determining whether it identifies a specific, quantifiable benefit to the customer and distinguishes the product from the status quo.
3. Evaluate the product's differentiation from existing alternatives, identifying the specific features, mechanisms, or positioning dimensions on which the product claims to differ from substitutes and alternatives.
4. Assess the product's development maturity, classifying it against the TAES Product Maturity Scale: Concept, Prototype, Beta, Generally Available, or Scaled — and verifying that the classification is consistent with the evidence provided.
5. Evaluate the depth and credibility of customer validation evidence, distinguishing between tiers of validation: letters of intent, pilot agreements, paying customers, long-term contracts, and unsolicited inbound demand.
6. Assess the quality of the product roadmap, evaluating whether near-term and medium-term development priorities are clearly defined, rationally sequenced, and aligned with identified customer needs.
7. Evaluate the product's fit with the stated target market segment, assessing whether the value proposition directly addresses the most significant pain point of the identified customer segment.
8. Identify any product-related red flags: vague or generic problem statements, value propositions that are indistinguishable from existing products, claimed development stages inconsistent with the evidence, or customer validation claims without supporting documentation.
9. Assess whether the product has a defensible core — a feature, mechanism, network effect, or operational model that would be difficult for a well-resourced competitor to replicate quickly.

#### Inputs

- **Product Description Block** from the SEDO, containing the normalised product name, category, problem statement, solution description, value proposition, development status, technology stack description, and customer validation evidence list.
- **Traction Evidence Block** from the SEDO, for evaluating customer validation claims.
- **Company Profile Block** from the SEDO, for stage context relevant to development maturity assessment.
- **Document Registry** from the Knowledge Extraction Agent, for referencing pitch decks, roadmap documents, customer letters, and pilot agreement documents.
- **Data Completeness Map** from the Knowledge Extraction Agent, indicating which product data fields are absent or partially provided.

#### Outputs

The Product Evaluation Agent produces the **Product Evaluation Report (PER)**, containing:

- **Product Definition Assessment:** Scores (0–10 each) for problem clarity, solution clarity, and target customer specificity, each with a written justification and evidence references.
- **Value Proposition Assessment:** A score (0–10) for value proposition strength, with a written analysis of the proposition's specificity, measurability, and distinctiveness.
- **Differentiation Assessment:** A differentiation score (0–10) with an analysis of claimed differentiators, their verifiability, and their defensibility. Differentiation dimensions identified and assessed.
- **Development Maturity Classification:** A classification on the TAES Product Maturity Scale with a written justification citing specific evidence items.
- **Customer Validation Assessment:** A tiered summary of validation evidence by validation tier, a customer validation score (0–10), and a written assessment of the strength and credibility of the validation evidence.
- **Roadmap Assessment:** An evaluation of the product roadmap's clarity, sequencing, and customer alignment.
- **Defensibility Assessment:** A defensibility score (0–10) with an analysis of the product's core defensibility mechanisms.
- **Product Red Flag Register:** A structured list of all identified product-related red flags, classified by severity.
- **Overall Product Quality Designation:** A categorical designation from the TAES Product Quality Scale with a written justification.
- **Evidence Reference Map and Confidence Scores** for all primary output fields.

#### Dependencies

- **Knowledge Extraction Agent** must complete execution and produce a valid SEDO before the Product Evaluation Agent can begin.
- **TRL Assessment Agent** is a peer agent and its output is not required as an input for the Product Evaluation Agent. However, the Orchestration Controller routes both outputs to the Risk Assessment Agent together, and the agents' findings on development maturity should be consistent. Any discrepancy between the Product Maturity Classification (Product Evaluation Agent) and the TRL level (TRL Assessment Agent) is flagged by the Orchestration Controller for review.

#### Evaluation Rules

1. **Maturity classification evidence requirement.** The TAES Product Maturity Scale classification must be supported by at least one concrete evidence item per classification level claimed. A "Beta" classification requires evidence that at least one external user or pilot customer has used the product. A "Prototype" classification requires evidence that a working prototype exists. Unsubstantiated classifications must be downgraded to the highest level for which evidence exists.
2. **Customer validation tier discipline.** Customer validation evidence must be classified by tier and scored accordingly. A letter of intent from a potential customer does not carry the same evidential weight as a paid contract with a live customer. The scoring must reflect these distinctions, not aggregate all validation evidence at equal weight.
3. **Value proposition specificity standard.** A value proposition that is expressed in generic language — "we help businesses improve efficiency" or "we reduce costs using AI" — must be scored at a maximum of 3 out of 10 for specificity, regardless of other positive indicators. A strong value proposition must name the specific customer, the specific problem, the specific mechanism, and the specific quantified benefit.
4. **Differentiation verifiability requirement.** Claimed differentiators that cannot be assessed from the submitted materials — for example, proprietary algorithm performance claims without benchmark data — must be recorded as unverified differentiators and scored at reduced weight.
5. **No gap filling.** The agent must not construct a value proposition, differentiator, or customer validation narrative from implicit or inferential reading of the materials. If the startup has not articulated a clear differentiation dimension, the agent must record its absence, not fill it in.
6. **Roadmap alignment check.** If a product roadmap is provided, the agent must check whether the roadmap priorities are consistent with the identified customer pain points and validation evidence. Misalignments must be noted.
7. **Red flag non-suppression.** All product red flags must be reported, including when they occur in an otherwise strong product submission.

#### Expected Deliverables

The Product Evaluation Report is a standalone section of the final evaluation package used directly by the investment committee. It also serves as a primary input for the Risk Assessment Agent (product risk dimension), the Recommendation Agent (product quality component), and the Competition Analysis Agent (for understanding stated differentiation claims against competitive alternatives).

#### Interaction with Other Agents

- **Competition Analysis Agent** consumes the Differentiation Assessment and the value proposition analysis to contextualise stated differentiators against actual competitor offerings.
- **TRL Assessment Agent** shares context with the Product Evaluation Agent through the Orchestration Controller's consistency reconciliation mechanism, though neither agent directly receives the other's output as an input.
- **Risk Assessment Agent** consumes the Product Red Flag Register, the Development Maturity Classification, and the Customer Validation Assessment as inputs to product and market risk dimensions.
- **Recommendation Agent** consumes the Overall Product Quality Designation and all primary scores.
- **Committee Preparation Agent** consumes the full Product Evaluation Report.

---

### 2.4 TRL Assessment Agent

#### Mission

The TRL Assessment Agent exists to assign and formally justify a Technology Readiness Level (TRL) designation to the startup's core technology, based on the evidence available in the submitted application materials. Its mission is to apply the TAES TRL Framework — a nine-level readiness scale adapted from NASA and ESA standards for the startup evaluation context — with rigorous evidential discipline. The agent must produce a TRL assignment that accurately reflects the demonstrated state of the technology, not the claimed state, and must explicitly document the gap between the assigned TRL and the next level, providing the investment committee with a clear picture of the technical milestones required to advance readiness.

#### Responsibilities

1. Identify the startup's core technology — the primary technical mechanism or system on which the product is built — from the SEDO Product Description Block and technology stack description.
2. Apply the TAES TRL Framework definitions to determine the highest TRL level for which the submitted evidence provides adequate support, proceeding from TRL 1 upward and stopping at the highest evidentially justified level.
3. Document the specific evidence items that support each TRL level claimed, citing source document identifiers and specific claims within those documents.
4. Identify the evidence required to justify the next TRL level beyond the assigned level, specifying what technical milestone or validation activity would need to be demonstrated.
5. Assess and document the gap between the assigned TRL and the TRL level claimed by the startup in their application, if a discrepancy exists.
6. Evaluate the reliability and completeness of the technology evidence provided, noting whether evidence consists of independent third-party validation, internal claims, prototype demonstrations, or theoretical descriptions.
7. Identify any technology-related risks specific to the current TRL level — technical risks that are common and significant at this stage of development.
8. Assess the plausibility of the startup's stated technology development timeline relative to their current TRL level and stated resources.

#### Inputs

- **Product Description Block** from the SEDO, particularly the technology stack description and development status fields.
- **Traction Evidence Block** from the SEDO, for identifying technology validation evidence such as pilot deployments and proof of concept demonstrations.
- **IP Data Block** from the SEDO, for identifying any patent filings or technical disclosures that corroborate technology claims.
- **Document Registry** from the Knowledge Extraction Agent, for referencing technical specifications, pitch deck technology slides, and prototype documentation.
- **TAES TRL Framework Definition:** The canonical nine-level TRL scale with detailed level definitions, evidence criteria, and example indicators, as specified in the TAES Platform Configuration.

#### Outputs

The TRL Assessment Agent produces the **TRL Assessment Report (TRLR)**, containing:

- **Core Technology Identification:** A normalised description of the startup's core technology, its primary mechanism, and its novelty classification (established technology applied in a new context, incremental improvement on existing technology, or novel technical approach).
- **Assigned TRL Level:** The assigned TRL level (1–9) with a categorical label.
- **TRL Justification Matrix:** A structured table mapping each TRL level from 1 through the assigned level, with: the level definition, the specific evidence item(s) supporting achievement of that level, the source document reference, and an evidence quality rating (Independent Third-Party Validation, Internal Claim with Supporting Documentation, Internal Claim Only).
- **Claimed vs. Assigned TRL Comparison:** Where the startup claimed a TRL level in their application that differs from the assigned level, a structured explanation of the discrepancy and the missing evidence.
- **Next-Level Advancement Requirements:** A structured description of the specific technical milestones, validation activities, and evidence types required to advance to the next TRL level.
- **Technology Risk Register:** A list of technology risks specific to the current TRL level.
- **Timeline Plausibility Assessment:** An assessment of whether the startup's stated technology development timeline is consistent with the current TRL level and available evidence on resources and team technical capability.
- **Aggregate TRL Confidence Score** and field-level confidence scores for all primary outputs.

#### Dependencies

- **Knowledge Extraction Agent** must complete execution and produce a valid SEDO before the TRL Assessment Agent can begin.
- No peer Tier 1 agent outputs are required as primary inputs. However, as noted in Section 2.3, consistency between the TRL Assignment and the Product Maturity Classification is checked by the Orchestration Controller after both agents complete.

#### Evaluation Rules

1. **Evidential floor requirement.** The assigned TRL level must not exceed the level for which at least one concrete, documentable evidence item exists. TRL levels above the evidential floor may be noted as plausible based on team capability or sector norms, but the formally assigned level must be the evidentially supported level.
2. **Evidence quality weighting.** Evidence items must be weighted by quality. Independent third-party validation — such as a documented pilot with a paying customer, an academic publication, or a certified test result — carries full evidential weight. Internal claims without supporting documentation carry minimal evidential weight and cannot alone support a TRL assignment above TRL 3.
3. **Claim-level assessment.** The agent must assess every technology claim in the source materials and classify each as: supported, partially supported, or unsupported. Unsupported claims must be noted in the output and must not influence the TRL assignment.
4. **No projection-based assignment.** The agent must assess current TRL, not projected TRL. A startup that credibly plans to reach TRL 7 in six months is still assigned the TRL level supported by current evidence, with a timeline assessment note.
5. **Novelty impact.** For novel technical approaches (as opposed to established technology applied in a new context), the agent must note that higher TRL levels require proportionally stronger evidence because external validation benchmarks are less available.
6. **Technology scope discipline.** The TRL assessment applies to the startup's primary core technology. If the startup uses multiple technologies at different readiness levels, the agent assigns the TRL of the least advanced critical technology, with a note on the full technology maturity profile.
7. **Discrepancy mandatory reporting.** Any discrepancy between the startup's claimed TRL and the agent's assigned TRL must be documented clearly and unambiguously, including the specific evidence items that were absent or insufficient to support the claimed level.

#### Expected Deliverables

The TRL Assessment Report is a standalone section of the final evaluation package. It provides the investment committee with an objective, evidence-grounded technology readiness picture that is frequently not available from the startup's own narrative. The Technology Risk Register is consumed by the Risk Assessment Agent. The Timeline Plausibility Assessment is consumed by the Risk Assessment Agent and the Recommendation Agent.

#### Interaction with Other Agents

- **Risk Assessment Agent** consumes the Technology Risk Register and Timeline Plausibility Assessment as inputs to the technology risk dimension.
- **Risk Assessment Agent** also uses the Claimed vs. Assigned TRL Comparison as evidence of potential founder overstatement risk.
- **Recommendation Agent** consumes the Assigned TRL Level and the Next-Level Advancement Requirements.
- **Committee Preparation Agent** consumes the full TRL Assessment Report, particularly the TRL Justification Matrix, for committee briefing.

---

### 2.5 Market Intelligence Agent

#### Mission

The Market Intelligence Agent exists to produce a structured, evidence-grounded evaluation of the market opportunity that the startup is pursuing. Its mission is to assess the size, growth, addressability, and timing of the market, and to evaluate the quality of the startup's own market analysis as submitted. The agent does not perform independent market research from external databases during individual evaluation runs — it works from the evidence provided in the submitted materials, supplemented by the TIDES Market Reference Database where applicable. Its role is to assess whether the startup's market claims are credible, internally consistent, and appropriately sized for the investment opportunity being evaluated, while identifying gaps, overstatements, or methodology weaknesses in the startup's market sizing approach.

#### Responsibilities

1. Evaluate the startup's stated TAM, SAM, and SOM figures for internal consistency, ensuring that each level of the market hierarchy is a proper subset of the level above and that the ratios between levels are plausible.
2. Assess the methodology used to produce each market size figure — distinguishing between top-down (market research report-based), bottom-up (customer count times average revenue per unit), and value theory approaches — and evaluate the methodological appropriateness for the stated market.
3. Evaluate the credibility and recency of the market data sources cited, identifying whether sources are reputable research firms, industry associations, government statistical databases, or unverified internet sources.
4. Assess the market growth rate claim, including the stated growth driver mechanisms, the time horizon, and the source, evaluating whether the growth claim is consistent with established sector knowledge in the TIDES Market Reference Database.
5. Evaluate the geographic scope of the market claim, assessing whether the startup's operational geography and the market geography are aligned, and whether geographic assumptions are realistic for the startup's current resources and stage.
6. Assess the startup's stated target customer segment within the market, evaluating the specificity of the segment definition and its alignment with the product's value proposition.
7. Evaluate market timing — assessing whether there is evidence of a timing catalyst that makes the current period particularly opportune for this market entry.
8. Identify any market sizing red flags: implausibly large TAM claims, SAM-to-TAM ratios that suggest the startup does not understand the competitive structure of the market, or SOM figures that are inconsistent with the startup's go-to-market capacity.

#### Inputs

- **Market Data Block** from the SEDO, containing all normalised market size figures, growth rate claims, geographic scope definitions, and source citations.
- **Product Description Block** from the SEDO, for understanding the product's target customer and value proposition, which is necessary to evaluate SAM and SOM claims.
- **Company Profile Block** from the SEDO, for stage and geography context.
- **TIDES Market Reference Database:** The TAES platform's curated reference dataset of sector-level market size benchmarks, growth rate benchmarks, and typical SAM/TAM ratios by sector — used to cross-reference startup claims.
- **Document Registry** from the Knowledge Extraction Agent, for referencing the pitch deck market slide and any market research documents.

#### Outputs

The Market Intelligence Agent produces the **Market Intelligence Report (MIR)**, containing:

- **Market Sizing Evaluation:** An assessment of each market size figure (TAM, SAM, SOM) with: the stated value, the methodology classification, the source credibility rating, an internal consistency check result, and a credibility score (0–10) per figure.
- **Market Growth Assessment:** An evaluation of the growth rate claim with a credibility score (0–10), source quality assessment, and comparison to TIDES Market Reference Database benchmarks where available.
- **Market Timing Assessment:** An evaluation of timing factors with a timing score (0–10) and an analysis of stated timing catalysts.
- **Geographic Scope Assessment:** An evaluation of geographic alignment between the market claim and the startup's operational scope.
- **Segment Definition Assessment:** An evaluation of target customer segment specificity.
- **Market Red Flag Register:** A structured list of all identified market sizing or analysis red flags.
- **Overall Market Opportunity Score:** A composite score (0–10) representing the overall quality and credibility of the market opportunity, with a written justification.
- **Confidence Scores** and evidence references for all primary output fields.

#### Dependencies

- **Knowledge Extraction Agent** must complete execution and produce a valid SEDO.
- No peer Tier 1 agent outputs are required as primary inputs. However, the Market Intelligence Report's market segmentation output — specifically the SAM definition and target customer segment — is consumed by the Competition Analysis Agent as a prerequisite input for competitive positioning analysis.

#### Evaluation Rules

1. **Methodology classification mandatory.** Every market size figure must have its derivation methodology classified. Figures without an identifiable methodology must be scored as "unverified" and cannot receive a credibility score above 3 out of 10.
2. **Source credibility tiering.** Market data sources must be classified into one of four tiers: Tier 1 (recognised global research firms such as Gartner, IDC, McKinsey, government statistical databases), Tier 2 (sector-specific industry associations and regional research bodies), Tier 3 (startup's own survey or customer interview data), and Tier 4 (unidentified or unverifiable sources). Credibility scores must reflect the tier of the supporting source.
3. **TAM plausibility floor.** A TAM figure that implies the startup is targeting a larger market than the entire global market for their sector, or a SOM figure that implies capturing more than 10% of the SAM within three years without extraordinary evidence, must be flagged as implausible and scored at a maximum credibility of 2 out of 10.
4. **Internal consistency requirement.** The agent must verify that SAM ≤ TAM and SOM ≤ SAM. Any violation of this hierarchy must be flagged as a data error in the Market Red Flag Register.
5. **Benchmark referencing.** Where the TIDES Market Reference Database contains a benchmark for the startup's sector, the agent must reference the benchmark in its assessment. Where the startup's claim significantly exceeds or falls below the benchmark, the agent must note the discrepancy and assess whether the deviation is explained by the submission materials.
6. **No market research generation.** The agent must not generate market size figures from general knowledge when they are absent from the submission. Absent market size figures must be recorded as data gaps.
7. **Geographic conservatism.** Where a startup claims a global or multi-continent market but shows no evidence of multi-geographic operations or partnerships, the agent must note this as a scope risk in the Market Red Flag Register.

#### Expected Deliverables

The Market Intelligence Report is a standalone section of the final evaluation package. The SAM definition and market segmentation findings are consumed by the Competition Analysis Agent. The Overall Market Opportunity Score, Market Red Flag Register, and Market Growth Assessment are consumed by the Risk Assessment Agent and the Recommendation Agent.

#### Interaction with Other Agents

- **Competition Analysis Agent** receives the SAM definition and target customer segment from the Market Intelligence Agent as inputs to competitive positioning analysis. This is the primary inter-Tier-1 agent dependency in the TAES architecture.
- **Risk Assessment Agent** consumes the Market Red Flag Register and the Overall Market Opportunity Score.
- **Recommendation Agent** consumes the Overall Market Opportunity Score and the Market Growth Assessment.
- **Committee Preparation Agent** consumes the full Market Intelligence Report.

---

### 2.6 Competition Analysis Agent

#### Mission

The Competition Analysis Agent exists to produce a structured, evidence-grounded evaluation of the startup's competitive landscape, competitive positioning, and differentiation strategy. Its mission is to identify the actual competitors operating in the startup's market — both direct and indirect — to assess the startup's stated differentiation claims against the actual product or positioning attributes of those competitors, and to evaluate the quality of the startup's competitive awareness and strategy. The agent works from evidence provided in the submitted materials and from the TIDES Competitive Reference Database, which contains structured profiles of known competitors in sectors commonly addressed by TIDES applicants. The agent is the primary judge of whether the startup's claimed differentiation is real, substantial, and defensible.

#### Responsibilities

1. Identify all competitors named by the startup in their submission materials and classify each as direct (same product category, same target customer) or indirect (alternative solutions to the same problem, or same product category but different customer segment).
2. Identify any significant competitors in the startup's market that are not named by the startup in their submission — using the TIDES Competitive Reference Database and the market context established by the Market Intelligence Agent — and flag any significant omissions.
3. For each identified competitor, produce a structured competitor profile: category, known founding date, known funding status, known market presence, and primary product/positioning attributes available from the TIDES Competitive Reference Database.
4. Evaluate the startup's stated differentiation claims against each named competitor, assessing whether the claimed differentiator is real (i.e., whether the competitor genuinely lacks the claimed attribute), substantial (i.e., whether the difference is meaningful to the target customer), and defensible (i.e., whether the differentiator is protected by a barrier that prevents easy replication).
5. Assess the startup's awareness of the competitive landscape, evaluating whether the competitor analysis in their submission is comprehensive, accurate, and strategically sophisticated or superficial and incomplete.
6. Evaluate the startup's competitive positioning strategy — the specific customer segment, value dimension, and market tier they are targeting — for coherence and viability.
7. Assess the level of competition intensity in the startup's target market segment: whether the segment is crowded, moderately competitive, or underserved.
8. Identify any competitive blind spots: significant competitors or competitive dynamics that the startup appears to be unaware of.

#### Inputs

- **Product Description Block** from the SEDO, including the value proposition, differentiation claims, and competitor names mentioned in the submission.
- **Market Intelligence Report** from the Market Intelligence Agent — specifically the SAM definition and target customer segment — required to accurately scope the competitive landscape to the startup's actual target segment, not the broader market.
- **TIDES Competitive Reference Database:** A structured database of competitor profiles maintained by the TIDES programme for sectors commonly represented in the applicant pool.
- **Document Registry** from the Knowledge Extraction Agent, for referencing competitive analysis slides or documents in the submission.
- **Data Completeness Map** from the Knowledge Extraction Agent, indicating whether a competitive analysis section was provided.

#### Outputs

The Competition Analysis Agent produces the **Competition Analysis Report (CAR)**, containing:

- **Competitor Registry:** A structured table of all identified competitors (named by the startup and identified by the agent), with columns for: competitor name, category (direct/indirect), known attributes relevant to the startup's market, and data source (startup submission or TIDES Competitive Reference Database).
- **Differentiation Assessment Matrix:** A structured matrix with competitors as rows and claimed differentiation dimensions as columns, indicating for each cell whether the startup's claimed advantage over that competitor on that dimension is: Real and Evidenced, Real but Unverified, Overstated, or Inapplicable.
- **Competitive Awareness Score:** A score (0–10) reflecting the comprehensiveness and accuracy of the startup's competitor awareness.
- **Competitive Positioning Assessment:** An evaluation of the startup's positioning strategy with a positioning coherence score (0–10).
- **Competitive Intensity Assessment:** An assessment of the competition level in the startup's target segment, with a competition intensity rating.
- **Blind Spot Register:** A structured list of significant competitive blind spots identified by the agent.
- **Overall Competitive Position Designation:** A categorical designation from the TAES Competitive Position Scale: Strongly Differentiated, Meaningfully Differentiated, Modestly Differentiated, or Undifferentiated — with written justification.
- **Confidence Scores** and evidence references.

#### Dependencies

- **Knowledge Extraction Agent** must complete execution and produce a valid SEDO.
- **Market Intelligence Agent** must complete execution and produce the Market Intelligence Report. The Competition Analysis Agent cannot begin execution until the Market Intelligence Report is available, because the SAM definition and target customer segment are required inputs for scoping the competitive analysis correctly. This is the primary sequenced inter-Tier-1 dependency in the TAES architecture.

#### Evaluation Rules

1. **Scope discipline.** The competitive analysis must be scoped to the startup's actual target segment as defined by the Market Intelligence Report SAM definition. Competitors in adjacent segments should be noted as potential future competitive threats but must not be included in the primary competitive position assessment.
2. **No constructed competitor profiles.** The agent must not generate competitor attributes from general knowledge beyond what is available in the TIDES Competitive Reference Database or the startup's submitted materials. Competitor attributes not present in these sources must be recorded as unknown.
3. **Differentiation claim verification standard.** A differentiation claim is classified as "Real and Evidenced" only when the evidence either explicitly demonstrates the startup possesses the claimed attribute or explicitly shows the competitor lacks it. Claims that are plausible but unverified from the available evidence are classified as "Real but Unverified."
4. **Omission mandatory reporting.** Significant competitors identified in the TIDES Competitive Reference Database that are absent from the startup's submission must be explicitly noted. The agent must not assume the startup is aware of competitors they have not named.
5. **Competitive intensity objectivity.** The competition intensity assessment must be based on the number, funding level, and market maturity of known competitors, not on the startup's own characterisation of the competitive landscape.
6. **Positioning coherence assessment.** A positioning strategy that targets a segment too crowded to penetrate with the startup's resources, or that attempts to compete on a dimension where the startup has no demonstrable advantage, must be flagged as a coherence failure in the Blind Spot Register.
7. **Blind spot severity classification.** Each blind spot must be classified by severity: Critical (the omitted competitor directly threatens the startup's viability in their target segment), Significant (the omitted competitor creates meaningful competitive pressure), or Minor (limited current relevance but worth noting).

#### Expected Deliverables

The Competition Analysis Report is a standalone section of the final evaluation package. The Differentiation Assessment Matrix and Overall Competitive Position Designation are used directly by the investment committee. The Blind Spot Register and competitive intensity assessment are consumed by the Risk Assessment Agent. The Overall Competitive Position Designation and Differentiation Assessment Matrix are consumed by the Recommendation Agent.

#### Interaction with Other Agents

- **Risk Assessment Agent** consumes the Blind Spot Register, competition intensity assessment, and Overall Competitive Position Designation.
- **Recommendation Agent** consumes the Overall Competitive Position Designation and the Differentiation Assessment Matrix.
- **Committee Preparation Agent** consumes the full Competition Analysis Report, particularly the Competitor Registry and Differentiation Assessment Matrix.

---

### 2.7 Financial Analysis Agent

#### Mission

The Financial Analysis Agent exists to produce a structured, evidence-grounded assessment of the startup's financial health, financial model quality, and the credibility of its financial projections. Its mission is to evaluate the startup's current financial position — including revenue status, burn rate, cash runway, and capitalisation — against its claims and the evidence provided. Where financial projections are submitted, the agent evaluates the underlying assumptions for reasonableness, internal consistency, and alignment with the startup's stated go-to-market strategy and market opportunity. The agent produces findings that enable the investment committee to form a clear view of the startup's financial risk, resource adequacy, and the efficiency of its capital deployment.

#### Responsibilities

1. Evaluate the startup's current revenue status, distinguishing between pre-revenue, early revenue (under 12 months), and recurring revenue, and assessing the quality of revenue evidence provided.
2. Assess the startup's current monthly burn rate and cash position, computing or verifying the cash runway in months, and flagging any runway positions that fall below TAES minimum viability thresholds.
3. Evaluate the revenue model: assess whether the startup's stated revenue model (SaaS subscription, transaction fee, service fee, licensing, marketplace, etc.) is appropriate for their product and market, and whether the pricing structure is consistent with market norms.
4. Evaluate unit economics where data is provided: calculate or verify Customer Acquisition Cost (CAC), Lifetime Value (LTV), LTV:CAC ratio, gross margin, and payback period, assessing whether these metrics indicate a viable and scalable business model.
5. Assess the quality and reasonableness of financial projections where provided, evaluating the underlying growth rate assumptions, cost assumptions, and the internal arithmetic consistency of the financial model.
6. Evaluate the startup's capitalisation table for structural health: identify founder equity dilution levels, existing investor terms and liquidation preferences, and any structural features that could create misaligned incentives.
7. Assess the use of funds stated in the application, evaluating whether the allocation is appropriate for the startup's stated priorities and whether the stated funding amount is consistent with achieving the stated milestones within the stated timeframe.
8. Identify financial red flags: negative gross margins, revenue recognition irregularities, implausible growth rate projections, excessive burn relative to revenue, or capitalisation structures with problematic existing terms.

#### Inputs

- **Financial Data Block** from the SEDO, containing all normalised monetary figures with source document references.
- **Traction Evidence Block** from the SEDO, for cross-referencing revenue claims with traction evidence.
- **Company Profile Block** from the SEDO, for stage and sector context relevant to financial benchmarking.
- **Document Registry** from the Knowledge Extraction Agent, for referencing financial model files, financial statements, and use-of-funds slides.
- **Inconsistency Register** from the Knowledge Extraction Agent, filtered for financial figure discrepancies.
- **TAES Financial Benchmark Database:** Sector and stage-specific benchmarks for burn rate, runway, gross margin, and unit economics used to contextualise the startup's financial profile.

#### Outputs

The Financial Analysis Agent produces the **Financial Analysis Report (FAR)**, containing:

- **Revenue Status Assessment:** Revenue stage classification, revenue evidence quality score (0–10), and written assessment.
- **Cash Position and Runway Assessment:** Computed or verified monthly burn rate, cash position, runway in months, and a runway adequacy rating.
- **Revenue Model Assessment:** A revenue model classification, model appropriateness score (0–10), and written assessment.
- **Unit Economics Assessment:** Computed or stated values for CAC, LTV, LTV:CAC ratio, gross margin, and payback period, each with a credibility rating. Where data is insufficient, each metric is recorded as a data gap.
- **Financial Projection Assessment:** A projection reasonableness score (0–10) with an analysis of key assumptions, arithmetic consistency check result, and growth rate reasonableness assessment.
- **Capitalisation Table Assessment:** A structural health assessment of the cap table with any concerns noted.
- **Use of Funds Assessment:** An evaluation of fund allocation appropriateness and milestone alignment.
- **Financial Red Flag Register:** All identified financial red flags, classified by severity.
- **Overall Financial Health Designation:** A categorical designation from the TAES Financial Health Scale: Sound, Adequate, Fragile, or Critical — with written justification.
- **Confidence Scores** and evidence references.

#### Dependencies

- **Knowledge Extraction Agent** must complete execution and produce a valid SEDO.
- No peer Tier 1 agent outputs are required as primary inputs. The Financial Analysis Agent operates independently of peer domain agents.

#### Evaluation Rules

1. **Arithmetic verification mandatory.** Where a financial model is submitted, the agent must verify the arithmetic consistency of the model — confirming that stated figures are internally consistent and that projections can be reproduced from stated assumptions. Arithmetic errors must be flagged and their direction (overstatement or understatement) noted.
2. **Runway computation standard.** Cash runway must be computed as: current cash balance divided by monthly cash burn rate. Where only quarterly or annual burn is stated, it must be converted to monthly before runway is computed. The agent must not accept a startup's stated runway figure without computing or verifying it from the underlying components.
3. **Growth rate reasonableness standard.** Year-on-year revenue growth projections above 3× in year one, above 5× in year two, or above 10× in year three for a pre-seed or seed stage startup — without extraordinary specific evidence justifying the growth rate — must be flagged as implausible in the Financial Red Flag Register.
4. **Absent data gap recording.** Where unit economics components are absent from the submission, the agent must record each absent metric as a data gap and note the impact on the LTV:CAC assessment. The agent must not estimate or impute unit economics from sector benchmarks.
5. **Revenue quality distinction.** The agent must distinguish between committed recurring revenue (contracts with defined payment terms), recognised revenue (received cash or invoiced amounts), and projected revenue. Financial assessments must clearly attribute each figure to its appropriate category.
6. **Cap table structural red flags.** Any capitalisation table feature that would create a structural disincentive for founders to pursue an exit — such as a very high liquidation preference multiplier held by existing investors — must be flagged as a structural risk, regardless of the overall financial health designation.
7. **Benchmark referencing.** Where the TAES Financial Benchmark Database contains sector and stage benchmarks, the agent must reference them in its unit economics and burn rate assessments, noting whether the startup's metrics are above, at, or below benchmark.

#### Expected Deliverables

The Financial Analysis Report is a standalone section of the final evaluation package. The Financial Red Flag Register and Overall Financial Health Designation are consumed by the Risk Assessment Agent. All primary financial scores are consumed by the Recommendation Agent. The full report is consumed by the Committee Preparation Agent.

#### Interaction with Other Agents

- **Risk Assessment Agent** consumes the Financial Red Flag Register, runway assessment, and Overall Financial Health Designation.
- **Recommendation Agent** consumes the Overall Financial Health Designation and all primary financial scores.
- **Mentorship Matching Agent** consumes the unit economics assessment and financial model quality scores to identify financial mentorship needs.
- **Committee Preparation Agent** consumes the full Financial Analysis Report.

---

### 2.8 Patent and IP Agent

#### Mission

The Patent and IP Agent exists to produce a structured, evidence-grounded assessment of the startup's intellectual property position. Its mission is to evaluate the nature, scope, and strength of any IP assets the startup claims to possess — including granted patents, pending patent applications, trade secrets, proprietary datasets, copyrighted materials, and trademarks — and to assess whether the startup's IP strategy is coherent, appropriate for its technology and market stage, and adequately protective of its core innovation. The agent also evaluates potential IP risks, including freedom-to-operate concerns, claims of IP that appear inconsistent with the startup's technology description, or IP positions that would be difficult to defend given the startup's resources.

#### Responsibilities

1. Identify and classify all IP assets claimed by the startup in their submission, categorising each by type: granted patent, pending patent application, provisional patent application, trade secret, proprietary dataset, copyright, trademark, or other.
2. For each patent or patent application, record the application number, filing jurisdiction, filing date, current status, and stated claims scope, as available in the submission materials.
3. Assess the alignment between the startup's IP claims and their product or technology description — evaluating whether the claimed IP actually protects the core innovation of the product.
4. Evaluate the breadth and strategic relevance of the IP portfolio, assessing whether the portfolio covers the startup's most commercially valuable innovations or peripheral aspects of the technology.
5. Assess the jurisdictional coverage of the IP portfolio relative to the startup's target markets, identifying geographic gaps in protection.
6. Identify any potential IP risks: claims of proprietary technology without supporting IP documentation, technology developed by founders at prior employers that may not be exclusively owned by the startup, or freedom-to-operate concerns suggested by the technology description.
7. Evaluate the adequacy of the startup's stated IP strategy — their plan for IP development, protection, and enforcement — relative to their technology and market stage.
8. Assess the startup's trade secret posture, evaluating whether the submission indicates awareness of trade secret protection practices where patents are not applicable.

#### Inputs

- **IP Data Block** from the SEDO, containing all IP assets identified from the submission materials.
- **Product Description Block** from the SEDO, for understanding the core technology and assessing alignment between IP claims and product innovation.
- **Founder Record Set** from the SEDO, for assessing IP ownership risk related to prior employer assignments.
- **Document Registry** from the Knowledge Extraction Agent, for referencing patent documents, IP assignment agreements, or IP strategy descriptions.
- **TAES IP Reference Framework:** The TAES standard definitions for IP asset types, evaluation criteria, and IP strategy adequacy criteria.

#### Outputs

The Patent and IP Agent produces the **IP Assessment Report (IPAR)**, containing:

- **IP Asset Registry:** A structured table of all claimed IP assets with columns for: asset type, identifier (patent number or application number if applicable), filing jurisdiction, filing date, current status, and alignment score with core product innovation.
- **IP Coverage Assessment:** An evaluation of the IP portfolio's breadth and strategic relevance, with a portfolio strength score (0–10).
- **Jurisdictional Coverage Assessment:** A map of IP protection coverage against the startup's stated target markets, with gap identification.
- **IP-Product Alignment Assessment:** An assessment of whether the claimed IP protects the startup's core innovation, with an alignment score (0–10).
- **IP Risk Register:** A structured list of identified IP risks, each classified by severity and type (ownership risk, freedom-to-operate risk, coverage gap risk, or enforcement capacity risk).
- **IP Strategy Assessment:** An evaluation of the startup's IP strategy adequacy, with a strategy coherence score (0–10).
- **Overall IP Position Designation:** A categorical designation: Strong, Adequate, Limited, or Absent — with written justification.
- **Confidence Scores** and evidence references.

#### Dependencies

- **Knowledge Extraction Agent** must complete execution and produce a valid SEDO.
- No peer Tier 1 agent outputs are required as primary inputs.

#### Evaluation Rules

1. **Document-grounded assessment only.** IP asset claims must be grounded in documentation present in the submission. The agent must not verify patent status against external patent databases during evaluation runs. It records what is present in the submission and flags missing documentation as a data gap.
2. **Ownership risk identification.** If any founder's employment history includes a prior employer in the same technology domain, and the submission does not include an IP assignment agreement or equivalent documentation, the agent must flag a potential IP ownership risk in the IP Risk Register.
3. **Absence recording.** Where the submission contains no IP documentation, the agent must record this as an IP position of "Absent" — it must not infer the presence of IP protection from the sophistication of the technology description alone.
4. **Alignment scope discipline.** The IP-Product Alignment Assessment must focus on whether the claimed IP protects the startup's commercially most valuable innovation. Peripheral IP that does not protect the core value driver must be noted as providing limited strategic value.
5. **Trade secret posture assessment requirement.** Even where patents are not relevant to the startup's technology (for example, in software-heavy startups in jurisdictions with limited software patent protection), the agent must assess whether the startup demonstrates awareness of trade secret protection practices. Absence of any IP protection discussion in the submission must be noted.
6. **Jurisdictional gap standard.** A patent portfolio that does not include protection in the startup's primary target market must be flagged as a jurisdictional gap, regardless of the quality of protection in other jurisdictions.
7. **No freedom-to-operate analysis generation.** The agent must not generate a freedom-to-operate analysis from general knowledge. Freedom-to-operate concerns must be flagged only when the submission materials, the startup's technology description, or the founder's prior employer history provides specific grounds for concern.

#### Expected Deliverables

The IP Assessment Report is a standalone section of the final evaluation package. The IP Risk Register is consumed by the Risk Assessment Agent. The Overall IP Position Designation and portfolio strength score are consumed by the Recommendation Agent. The full report is consumed by the Committee Preparation Agent.

#### Interaction with Other Agents

- **Risk Assessment Agent** consumes the IP Risk Register and the Overall IP Position Designation.
- **Recommendation Agent** consumes the Overall IP Position Designation and the portfolio strength score.
- **Mentorship Matching Agent** consumes the IP Strategy Assessment and IP Risk Register to identify IP advisory needs.
- **Committee Preparation Agent** consumes the full IP Assessment Report.

---

### 2.9 Risk Assessment Agent

#### Mission

The Risk Assessment Agent exists to produce a comprehensive, structured risk profile of the startup by synthesising the risk-relevant outputs of all upstream domain evaluation agents. Its mission is to identify, classify, and assess the severity of all risks — across team, product, technology, market, competition, financial, and IP dimensions — and to evaluate their interactions, producing an integrated risk picture that the investment committee can use to make a well-informed decision. The Risk Assessment Agent does not re-evaluate the domain-specific evidence that has already been assessed by upstream agents. It synthesises the risk-relevant findings from upstream agents into a coherent, cross-dimensional risk register, identifies compound risks that emerge from the interaction of multiple domain risks, and produces an overall risk designation for the startup.

#### Responsibilities

1. Consume all risk-relevant outputs from every Tier 1 domain evaluation agent — including their red flag registers, confidence gaps, and domain-specific risk indicators — and normalise them into a unified risk taxonomy.
2. Classify all identified risks by dimension: Team Risk, Product Risk, Technology Risk, Market Risk, Competitive Risk, Financial Risk, and IP Risk.
3. Assess the severity of each identified risk on the TAES Risk Severity Scale: Critical, High, Medium, Low, and Informational — applying consistent criteria across all risk dimensions.
4. Assess the likelihood of each identified risk materialising, distinguishing between risks that are already materialised, risks with a high probability of materialising within 12 months, and risks that are conditional or speculative.
5. Identify compound risks: risks that emerge from the interaction of multiple domain risks. For example, a technology risk that is amplified by a financial risk if the runway is insufficient to complete the technical milestone required to de-risk the technology.
6. Evaluate the startup's demonstrated risk awareness, assessing whether the submission materials indicate that the founders are aware of the key risks identified and have plausible mitigation strategies in place.
7. Assess the adequacy of the startup's stated risk mitigation strategies for each identified Critical and High severity risk.
8. Produce an Overall Risk Designation for the startup from the TAES Risk Designation Scale.
9. Identify the single most critical risk — the risk that, if not mitigated, would most significantly threaten the startup's ability to achieve its next major milestone — and provide a detailed written assessment of it.

#### Inputs

- **Founder Evaluation Report** (Founder Evaluation Agent): Critical Gaps Register, red flag notations, Overall Team Quality Designation.
- **Product Evaluation Report** (Product Evaluation Agent): Product Red Flag Register, Development Maturity Classification, Customer Validation Assessment, Overall Product Quality Designation.
- **TRL Assessment Report** (TRL Assessment Agent): Technology Risk Register, Timeline Plausibility Assessment, Claimed vs. Assigned TRL Comparison.
- **Market Intelligence Report** (Market Intelligence Agent): Market Red Flag Register, Overall Market Opportunity Score.
- **Competition Analysis Report** (Competition Analysis Agent): Blind Spot Register, competitive intensity assessment, Overall Competitive Position Designation.
- **Financial Analysis Report** (Financial Analysis Agent): Financial Red Flag Register, runway assessment, Overall Financial Health Designation.
- **IP Assessment Report** (Patent and IP Agent): IP Risk Register, Overall IP Position Designation.
- **Inconsistency Register** from the Knowledge Extraction Agent (as a cross-dimensional risk indicator for submission quality and founder candour).
- **Data Completeness Map** from the Knowledge Extraction Agent (as an input to information asymmetry risk).

#### Outputs

The Risk Assessment Agent produces the **Risk Assessment Report (RAR)**, containing:

- **Unified Risk Register:** A structured table of all identified risks, each with: risk identifier, dimension, source agent, severity classification, likelihood assessment, current status (materialised, probable, conditional), and a written description.
- **Compound Risk Analysis:** A structured description of all identified compound risks, with an explanation of the interaction mechanism and the compounded severity assessment.
- **Risk Awareness Assessment:** An evaluation of the startup's demonstrated awareness of its key risks and the adequacy of its stated mitigations.
- **Most Critical Risk Assessment:** A detailed written assessment of the single most critical risk identified, including its source, severity rationale, likelihood, and recommended mitigation pathway.
- **Overall Risk Designation:** A categorical designation from the TAES Risk Designation Scale: Low Risk, Moderate Risk, Elevated Risk, High Risk, or Very High Risk — with written justification.
- **Risk Heat Map Summary:** A structured summary presenting risks by dimension and severity, enabling rapid visual assessment of the risk profile.
- **Confidence Scores** and source agent references for all primary outputs.

#### Dependencies

All seven Tier 1 domain evaluation agents must complete execution and produce valid outputs before the Risk Assessment Agent can begin. The Risk Assessment Agent requires:
- Founder Evaluation Report (complete)
- Product Evaluation Report (complete)
- TRL Assessment Report (complete)
- Market Intelligence Report (complete)
- Competition Analysis Report (complete)
- Financial Analysis Report (complete)
- IP Assessment Report (complete)

The Orchestration Controller enforces this dependency before routing inputs to the Risk Assessment Agent.

#### Evaluation Rules

1. **Synthesis only, no re-evaluation.** The Risk Assessment Agent must not re-evaluate domain-specific evidence. It must accept upstream agents' domain findings as its inputs and synthesise from them. It may note confidence gaps in upstream outputs but must not override domain agent scores.
2. **Severity consistency standard.** The severity classification criteria — what constitutes a Critical versus High versus Medium risk — must be applied consistently across all risk dimensions. Severity is determined by the potential impact on the startup's viability, not by the domain of origin.
3. **Compound risk identification requirement.** The agent must actively assess whether any pair of domain risks, when considered together, creates a compound risk with a higher effective severity than either risk alone. This assessment must be explicit in the output, not implied.
4. **Materialised risk distinction.** Risks that have already materialised — for example, a founder having departed the team, or runway falling below three months — must be explicitly distinguished from risks that are potential or probable.
5. **Mitigation adequacy standard.** For each Critical and High severity risk for which the startup has stated a mitigation strategy, the agent must assess whether the mitigation is: adequate and credible, partially adequate, or inadequate. Mitigation adequacy assessments must be written, not just scored.
6. **Information asymmetry risk.** The agent must treat significant data gaps identified in the Data Completeness Map as an information asymmetry risk — the risk that material negative information is present but has not been disclosed. This risk must be included in the Unified Risk Register when the number or nature of data gaps is above the TAES Information Gap Threshold.
7. **No risk suppression.** All risks identified from upstream inputs must be included in the Unified Risk Register, regardless of the overall risk designation. Risk suppression — omitting risks to improve the overall designation — is a violation of TAES governance standards.

#### Expected Deliverables

The Risk Assessment Report is a standalone section of the final evaluation package and is one of the most heavily used documents in the investment committee deliberation process. The Unified Risk Register, Most Critical Risk Assessment, and Overall Risk Designation are key inputs to the Recommendation Agent. The full report is consumed by the Committee Preparation Agent.

#### Interaction with Other Agents

- **Recommendation Agent** consumes the Overall Risk Designation, Most Critical Risk Assessment, and Unified Risk Register as primary inputs to the final recommendation.
- **Mentorship Matching Agent** consumes the Unified Risk Register to identify risk areas requiring mentorship support.
- **Committee Preparation Agent** consumes the full Risk Assessment Report, particularly the Risk Heat Map Summary and Most Critical Risk Assessment.

---

### 2.10 Recommendation Agent

#### Mission

The Recommendation Agent is the synthesis apex of the TAES evaluation pipeline. Its mission is to consume the structured outputs of all upstream evaluation agents — domain quality scores, risk designations, evidence gaps, and IP, financial, product, team, market, and competitive assessments — and to produce a final, integrated, evidence-grounded recommendation for the investment committee. The recommendation must address whether the startup is suitable for acceptance into the TIDES programme, with what conditions if applicable, and must provide a clear, structured rationale that traces the recommendation directly to the upstream agent findings. The Recommendation Agent does not gather new information. It reasons from the structured knowledge assembled by all upstream agents to produce a recommendation that reflects the totality of the evaluation.

#### Responsibilities

1. Receive and validate the complete structured output set from all upstream agents, confirming that all required inputs are present and that no escalation flags requiring human review have been left unresolved.
2. Compute the TAES Composite Evaluation Score by applying the TAES Scoring Weights Framework to the primary domain scores from each domain evaluation agent, producing a weighted aggregate score.
3. Assess whether the Composite Evaluation Score and the pattern of domain scores support one of the four TAES recommendation categories: Accept, Conditional Accept, Waitlist, or Decline.
4. Where a Conditional Accept is the recommendation, define the specific conditions — concrete, measurable milestones or information items — that the startup must satisfy before acceptance is confirmed.
5. Assess the coherence of the startup's overall profile: whether the strengths and weaknesses identified across all domains form a coherent picture of a startup at a specific developmental stage with specific addressable gaps, or whether the profile is internally inconsistent in ways that raise credibility concerns.
6. Identify the startup's primary strengths — the two or three domain areas in which the evaluation evidence is strongest — and articulate these clearly in the final recommendation narrative.
7. Identify the startup's primary concerns — the two or three domain areas or specific risk items that most significantly qualify the positive findings — and articulate these clearly and specifically in the recommendation narrative.
8. Produce the executive summary of the evaluation, synthesising all domain findings into a coherent narrative of the startup's overall quality and fit for the TIDES programme.
9. Assess the startup's fit with the TIDES programme specifically — not just investment readiness in general — based on the programme's stated focus sectors, stage criteria, and strategic priorities.
10. Produce a final scoring summary table presenting all domain scores, the TAES Composite Evaluation Score, and the recommendation, in a format suitable for inclusion in the committee briefing package.

#### Inputs

- **Founder Evaluation Report** (Founder Evaluation Agent): Overall Team Quality Designation and all primary team quality scores.
- **Product Evaluation Report** (Product Evaluation Agent): Overall Product Quality Designation and all primary product scores.
- **TRL Assessment Report** (TRL Assessment Agent): Assigned TRL Level and Next-Level Advancement Requirements.
- **Market Intelligence Report** (Market Intelligence Agent): Overall Market Opportunity Score.
- **Competition Analysis Report** (Competition Analysis Agent): Overall Competitive Position Designation and Differentiation Assessment Matrix summary.
- **Financial Analysis Report** (Financial Analysis Agent): Overall Financial Health Designation and all primary financial scores.
- **IP Assessment Report** (Patent and IP Agent): Overall IP Position Designation and portfolio strength score.
- **Risk Assessment Report** (Risk Assessment Agent): Overall Risk Designation, Most Critical Risk Assessment, and Unified Risk Register.
- **Data Completeness Map** from the Knowledge Extraction Agent: for characterising the degree of information asymmetry in the evaluation.
- **TAES Scoring Weights Framework:** The canonical domain weighting specification for computing the Composite Evaluation Score.
- **TIDES Programme Criteria:** The current TIDES programme admission criteria, stage requirements, and sector priorities.

#### Outputs

The Recommendation Agent produces the **Final Evaluation Recommendation (FER)**, containing:

- **TAES Composite Evaluation Score:** The weighted aggregate score (0–100) with a breakdown showing each domain's weighted contribution.
- **Domain Score Summary Table:** A structured table presenting all domain scores, their weights, weighted contributions, and confidence levels.
- **Recommendation Category:** One of: Accept, Conditional Accept, Waitlist, or Decline — with a written one-paragraph primary justification.
- **Conditions Register (if Conditional Accept):** A structured list of specific, measurable conditions, each with a clear milestone definition and a recommended verification mechanism.
- **Primary Strengths Summary:** A written narrative (maximum three items) identifying the startup's most significant strengths with specific evidence references.
- **Primary Concerns Summary:** A written narrative (maximum three items) identifying the most significant concerns with specific evidence references and upstream agent source citations.
- **Coherence Assessment:** A written assessment of whether the startup's overall profile is internally coherent.
- **TIDES Programme Fit Assessment:** A specific assessment of the startup's fit with current TIDES programme priorities.
- **Executive Summary:** A concise narrative (400–600 words) suitable for distribution to committee members who have not read the full evaluation package.
- **Confidence Score:** An aggregate confidence level for the final recommendation, reflecting the completeness and quality of the evidence base across all domains.

#### Dependencies

- All Tier 1 domain evaluation agents must complete.
- The Risk Assessment Agent must complete (Tier 2 dependency).
- All escalation flags from any upstream agent must be resolved (by human review supplementation or by formal evidence-absent notation) before the Recommendation Agent can produce a recommendation.

#### Evaluation Rules

1. **Composite score discipline.** The Composite Evaluation Score must be computed strictly according to the TAES Scoring Weights Framework. The agent must not apply discretionary adjustments to individual domain scores or weights. Any departure from the framework's specified weights requires a formal TAES governance exception.
2. **Recommendation category threshold compliance.** The mapping from Composite Evaluation Score ranges to recommendation categories must follow the TAES Recommendation Threshold Table. The agent must not produce a recommendation category inconsistent with the score range, except where a disqualifying risk condition overrides the score-based recommendation (in which case this override must be explicitly documented).
3. **Disqualifying risk override.** Where the Risk Assessment Report identifies a Critical severity risk with a materialised status, the recommendation must reflect this, regardless of the Composite Evaluation Score. A startup with a high composite score but a materialised Critical risk cannot receive an unconditional Accept recommendation.
4. **Evidence traceability requirement.** Every claim in the recommendation narrative — whether a strength or a concern — must reference the upstream agent output and specific field from which it is derived. Recommendation narratives that cannot be fully traced to upstream agent outputs are non-compliant.
5. **Conditions specificity standard.** Conditions attached to a Conditional Accept recommendation must be specific and measurable. A condition such as "improve financial documentation" is non-compliant. A compliant condition specifies the exact documentation required, the minimum acceptable standard, and the verification mechanism.
6. **No new evaluation.** The Recommendation Agent must not introduce new findings or evidence assessments that are not present in any upstream agent output. Its role is synthesis and recommendation, not additional evaluation.
7. **Coherence assessment mandatory.** Every final recommendation must include a coherence assessment, even if the overall coherence is high. Coherence issues — for example, a team claiming strong domain expertise in a market that their actual experience profile does not support — must be noted.
8. **Score confidence floor.** Where the aggregate confidence of upstream agent outputs — weighted by domain — falls below the TAES Recommendation Confidence Floor, the recommendation must be accompanied by a confidence advisory noting the information gaps that limit recommendation quality.

#### Expected Deliverables

The Final Evaluation Recommendation is the primary output of the entire TAES evaluation pipeline. It constitutes the pre-committee written position that will be reviewed, challenged, and deliberated by the investment committee. The Committee Preparation Agent receives this output and packages it with all upstream agent reports for committee distribution.

#### Interaction with Other Agents

- **Committee Preparation Agent** consumes the full Final Evaluation Recommendation, along with all upstream domain reports, to assemble the complete committee briefing package.
- The Recommendation Agent is the terminal node of the evaluation pipeline and does not route outputs to any further evaluation agents.

---

### 2.11 Mentorship Matching Agent

#### Mission

The Mentorship Matching Agent exists to produce structured, evidence-grounded mentorship pairing recommendations for startups that are accepted or conditionally accepted into the TIDES programme. Its mission is to analyse the startup's identified capability gaps, risk dimensions, and strategic needs — as surfaced across all upstream domain evaluation agents — and to match these needs against the TIDES Mentor Registry to identify mentor profiles whose expertise most directly addresses the startup's most significant development needs. The agent applies a structured matching framework to produce a ranked list of mentor profile types, enabling the TIDES programme management team to assign appropriate mentors with high relevance and low misalignment.

#### Responsibilities

1. Synthesise all capability gap and risk findings from upstream domain agents — including the Critical Gaps Register from the Founder Evaluation Agent, the IP Risk Register, the Financial Red Flag Register, and the Risk Assessment Agent's Unified Risk Register — into a structured list of startup development needs.
2. Classify each identified need by domain: Team and Leadership, Product and Technology, Market and Business Development, Financial Management, IP and Legal, Regulatory and Compliance, or Sector-Specific Expertise.
3. Prioritise identified needs by their impact on the startup's ability to achieve its next major milestone, producing a ranked needs list.
4. Consult the TIDES Mentor Registry to identify mentor profiles whose documented expertise areas, sector experience, and mentorship availability align with the startup's top-ranked needs.
5. For each mentor profile match, produce a structured rationale explaining which specific startup gap or need the mentor's expertise addresses and what the expected mentorship outcome is.
6. Identify the minimum mentor coverage required — the combination of mentor profiles that collectively addresses all Critical and High priority needs — and flag any needs for which no adequate mentor profile is available in the current TIDES Mentor Registry.
7. Produce a structured mentor gap report identifying needs for which the current TIDES Mentor Registry has insufficient coverage, enabling the programme management team to proactively recruit additional mentors.
8. Assess whether any identified needs are better addressed by specialised advisory services, industry partnerships, or external expert engagements rather than mentorship relationships.

#### Inputs

- **Founder Evaluation Report** (Founder Evaluation Agent): Critical Gaps Register, Team Composition Assessment.
- **Financial Analysis Report** (Financial Analysis Agent): Unit economics assessment, financial model quality assessment.
- **IP Assessment Report** (Patent and IP Agent): IP Risk Register, IP Strategy Assessment.
- **Risk Assessment Report** (Risk Assessment Agent): Unified Risk Register (filtered for addressable gaps rather than structural market risks).
- **Final Evaluation Recommendation** (Recommendation Agent): Primary Concerns Summary and Conditions Register.
- **TIDES Mentor Registry:** The current, maintained database of TIDES programme mentor profiles, including each mentor's expertise areas, sector experience, stage specialisation, and current availability status.

#### Outputs

The Mentorship Matching Agent produces the **Mentorship Matching Report (MMR)**, containing:

- **Startup Development Needs Register:** A structured, prioritised list of all identified development needs, classified by domain and priority (Critical, High, Medium).
- **Mentor Match Recommendations:** A ranked list of mentor profile matches, each specifying: the mentor profile attributes matched, the specific startup need addressed, the matching rationale, and the expected mentorship engagement type (advisory, coaching, technical, network facilitation).
- **Coverage Map:** A structured assessment of whether the recommended mentor set collectively covers all Critical and High priority needs.
- **Mentor Registry Gap Report:** A structured list of needs for which the TIDES Mentor Registry does not have adequate coverage.
- **Non-Mentorship Recommendations:** Identification of needs better addressed by specialist advisors, industry partnerships, or structured programmes.
- **Confidence Scores** for match quality ratings.

#### Dependencies

- **Founder Evaluation Report** (complete)
- **Financial Analysis Report** (complete)
- **IP Assessment Report** (complete)
- **Risk Assessment Report** (complete)
- **Final Evaluation Recommendation** (complete — the Mentorship Matching Agent runs only for startups that receive an Accept or Conditional Accept recommendation)

#### Evaluation Rules

1. **Needs-first matching.** Mentor matches must be driven by the startup's identified needs, not by the availability of mentors in the Registry. Where no adequate mentor match exists for a Critical priority need, this must be reported as a Registry gap rather than a lower-priority mentor being recommended as a substitute.
2. **Specificity requirement.** Each mentor match recommendation must specify the exact startup gap being addressed. Generic mentor recommendations — "this startup needs a mentor with marketing experience" — are non-compliant. A compliant recommendation specifies the specific gap (e.g., "absence of a B2B SaaS go-to-market strategy capability, as identified in the Team Composition Assessment") and the specific mentor attribute that addresses it.
3. **Availability verification.** The agent must only recommend mentor profiles whose current availability status in the TIDES Mentor Registry is Active or Available. Unavailable mentors must not be recommended.
4. **Conflict of interest flag.** If a mentor profile in the Registry has a documented connection to a competitor of the startup being evaluated, this conflict must be flagged in the match recommendation and must not be recommended without explicit programme management approval.
5. **Stage appropriateness.** Mentor profiles must be matched with consideration of the startup's current stage. A mentor specialising in Series B operational scaling is not an appropriate match for a pre-seed startup working on product validation.
6. **Coverage sufficiency standard.** The recommended mentor set must be evaluated for whether it collectively provides coverage of all Critical priority needs. A recommended mentor set that leaves any Critical priority need uncovered is non-compliant unless the gap is documented in the Mentor Registry Gap Report.

#### Expected Deliverables

The Mentorship Matching Report is provided to the TIDES programme management team as a programme operations document. It is not included in the core investment committee briefing package, but a summary of key mentorship recommendations is included in the Committee Preparation Agent's programme management section. The Mentor Registry Gap Report is delivered to the TIDES Mentor Recruitment function as a programme development input.

#### Interaction with Other Agents

The Mentorship Matching Agent is a terminal node in the evaluation pipeline for accepted startups. Its outputs are consumed by the Committee Preparation Agent (for the programme management annex of the committee briefing package) but are not routed to any further evaluation agents.

---

### 2.12 Committee Preparation Agent

#### Mission

The Committee Preparation Agent is the final stage of the TAES evaluation pipeline. Its mission is to assemble, structure, and format all upstream agent outputs into a coherent, committee-ready briefing package that enables investment committee members to review, deliberate, and decide on the startup application efficiently and with full access to the evaluation evidence. The agent does not produce new evaluative content — it organises, summarises, and presents existing agent outputs in formats appropriate for different committee audiences and deliberation stages. It produces multiple output formats: an executive briefing for rapid pre-meeting review, a full evaluation dossier for deep-dive review, and a structured deliberation facilitation guide for committee chairs.

#### Responsibilities

1. Receive and validate the complete set of agent outputs from all upstream agents, confirming that every required section is present, that no unresolved escalation flags remain, and that the Final Evaluation Recommendation is present and complete.
2. Assemble the full evaluation dossier by integrating all upstream agent reports into a single, consistently structured document with a standardised section ordering, a unified table of contents, and consistent formatting.
3. Produce the executive briefing document — a concise summary (maximum eight pages) covering: startup identity, the Executive Summary from the Recommendation Agent, the Domain Score Summary Table, the Overall Risk Designation, the Recommendation Category, and the top three strengths and top three concerns.
4. Produce the committee deliberation guide — a structured document that presents the key decision points, the most significant evidence on each side of each decision point, and suggested deliberation questions for the committee chair.
5. Produce the score verification appendix — a document that presents the evidence trail behind each domain score, enabling any committee member to trace a score back to its underlying evidence in the source documents.
6. Produce the conditions verification worksheet for Conditional Accept recommendations — a structured form that enables the programme management team to track and verify completion of each condition attached to a conditional acceptance.
7. Produce the programme management annex — a document summarising the mentorship matching recommendations and any non-mentorship programme support recommendations from the Mentorship Matching Agent.
8. Format all output documents for the TIDES platform's committee briefing distribution system, applying the document metadata schema required for indexing and archival.
9. Generate the evaluation completion record — a formal log entry recording the execution of every agent in the pipeline, their completion timestamps, confidence levels, any escalations, and the final recommendation category — for compliance and audit purposes.

#### Inputs

- **Final Evaluation Recommendation** (Recommendation Agent): Full document.
- **Founder Evaluation Report** (Founder Evaluation Agent): Full document.
- **Product Evaluation Report** (Product Evaluation Agent): Full document.
- **TRL Assessment Report** (TRL Assessment Agent): Full document.
- **Market Intelligence Report** (Market Intelligence Agent): Full document.
- **Competition Analysis Report** (Competition Analysis Agent): Full document.
- **Financial Analysis Report** (Financial Analysis Agent): Full document.
- **IP Assessment Report** (Patent and IP Agent): Full document.
- **Risk Assessment Report** (Risk Assessment Agent): Full document.
- **Mentorship Matching Report** (Mentorship Matching Agent): Full document (for accepted startups).
- **Document Registry and Data Completeness Map** from the Knowledge Extraction Agent: for the score verification appendix.
- **Orchestration Controller Execution Log:** The complete log of agent executions, timestamps, confidence levels, and escalations — for the evaluation completion record.
- **TIDES Committee Briefing Template:** The current TIDES programme committee briefing document format specification.

#### Outputs

The Committee Preparation Agent produces the **Committee Briefing Package (CBP)**, consisting of five components:

1. **Executive Briefing Document:** Maximum eight pages. Startup identity, executive summary, domain score summary table, overall risk designation, recommendation category, top strengths and concerns, and TIDES fit assessment.
2. **Full Evaluation Dossier:** The complete integrated evaluation, containing all domain evaluation reports in standardised order, with a unified table of contents and consistent formatting.
3. **Committee Deliberation Guide:** Key decision points, evidence summary for each decision point, and suggested deliberation questions.
4. **Score Verification Appendix:** Evidence trail for each domain score, with source document citations.
5. **Conditions Verification Worksheet** (for Conditional Accept): Structured tracking form for each condition.
6. **Programme Management Annex:** Mentorship matching recommendations and programme support recommendations.
7. **Evaluation Completion Record:** Formal audit log of the evaluation pipeline execution.

#### Dependencies

- All upstream agents must complete, including:
  - All Tier 1 domain agents (complete)
  - Risk Assessment Agent (complete)
  - Recommendation Agent (complete)
  - Mentorship Matching Agent (complete, for accepted startups)
- All escalation flags must be resolved.
- The Orchestration Controller must confirm pipeline completion before routing all outputs to the Committee Preparation Agent.

#### Evaluation Rules

1. **No content modification.** The Committee Preparation Agent must not alter, summarise in a way that changes meaning, or reframe any finding from any upstream agent. Its role is presentation and organisation, not interpretation. Any condensation of content for the executive briefing must preserve the original finding's meaning and evidence grounding.
2. **Completeness verification.** Before producing any output document, the agent must verify that all required upstream agent outputs are present and complete. A briefing package produced from an incomplete input set is non-compliant and must be flagged as incomplete in the evaluation completion record.
3. **Escalation resolution verification.** The agent must verify that all escalation flags recorded in the Orchestration Controller execution log have been resolved — either by human review supplementation or by formal evidence-absent notation. An unresolved escalation flag must be disclosed in the executive briefing and the evaluation completion record.
4. **Audit trail preservation.** The evaluation completion record must contain the complete Orchestration Controller execution log, unmodified. This record is a compliance artefact and must not be edited.
5. **Template conformance.** All output documents must conform to the current TIDES Committee Briefing Template version. Any deviation from the template requires a formal programme management approval.
6. **Conditions specificity verification.** In the Conditions Verification Worksheet, each condition from the Recommendation Agent's Conditions Register must be reproduced exactly as stated. The worksheet must not paraphrase, simplify, or modify conditions.
7. **Deliberation question neutrality.** The deliberation questions in the Committee Deliberation Guide must be neutral and open-ended, presenting both supportive and challenging evidence perspectives. The guide must not steer the committee toward a predetermined conclusion.

#### Expected Deliverables

The Committee Briefing Package is the final output of the entire TAES evaluation pipeline. It is distributed to investment committee members before the committee session. The Evaluation Completion Record is archived in the TIDES compliance repository. The Programme Management Annex is delivered to the TIDES programme management team.

#### Interaction with Other Agents

The Committee Preparation Agent is the terminal node of the TAES evaluation pipeline. It does not route outputs to any further agents. Its outputs are delivered to human stakeholders: investment committee members, the committee chair, and the TIDES programme management team.

---

## 3. Agent Orchestration

### 3.1 Orchestration Architecture Overview

The TAES evaluation pipeline is managed by the Orchestration Controller — a dedicated coordination layer that is responsible for agent scheduling, input routing, output collection, dependency enforcement, and escalation management. The Orchestration Controller operates as a stateful workflow engine. For each evaluation run, it maintains an execution state record that tracks the status of every agent in the pipeline: Pending, Running, Completed, Failed, or Escalated.

The Orchestration Controller does not make evaluation decisions. It is a pure coordination layer. Its logic is deterministic: given the defined dependency graph and the completion status of each agent, the Orchestration Controller's next action is always uniquely determined. This determinism is essential for pipeline auditability.

### 3.2 Execution Tiers

The TAES pipeline is divided into three execution tiers, each with a defined parallelism profile:

**Tier 0 — Sequential, no parallelism.** The Knowledge Extraction Agent is the sole Tier 0 agent. It must complete fully before any Tier 1 agent can begin. There is no parallelism within Tier 0.

**Tier 1 — Parallel with internal sequencing.** The seven domain evaluation agents constitute Tier 1. The majority of these agents can execute concurrently, sharing the same SEDO inputs from the Knowledge Extraction Agent. The exception is the internal sequencing constraint between the Market Intelligence Agent and the Competition Analysis Agent: the Competition Analysis Agent requires the Market Intelligence Report (specifically the SAM definition and target customer segment) as an input, and therefore cannot begin until the Market Intelligence Agent completes. All other Tier 1 agents are independent of one another and execute in parallel.

Tier 1 parallelism order:
- Phase 1A (concurrent): Founder Evaluation Agent, Product Evaluation Agent, TRL Assessment Agent, Market Intelligence Agent, Financial Analysis Agent, Patent and IP Agent.
- Phase 1B (begins when Market Intelligence Agent completes): Competition Analysis Agent.

**Tier 2 — Sequential with late-stage parallelism.** The Tier 2 agents execute in the following order:
- Phase 2A: Risk Assessment Agent (requires all Tier 1 agents to complete).
- Phase 2B (concurrent, begin when Risk Assessment Agent completes): Recommendation Agent and Mentorship Matching Agent.
- Phase 2C (begins when both Recommendation Agent and Mentorship Matching Agent complete): Committee Preparation Agent.

### 3.3 Input Routing

The Orchestration Controller is responsible for routing the correct subset of upstream agent outputs to each downstream agent. Input routing is governed by the Input Routing Table, a static configuration that maps, for each agent, the exact output fields from each upstream agent that constitute its inputs. Input routing is not dynamic — the Orchestration Controller does not select inputs based on content. The routing table is a fixed configuration and is subject to TAES version control.

### 3.4 Execution Monitoring

The Orchestration Controller monitors the execution state of every agent in real time. It records, for each agent execution: the start timestamp, the end timestamp, the output validation result (schema-compliant or non-compliant), the aggregate confidence score, whether any escalation flag was set, and the dependency resolution status. All of this data is recorded in the Execution Log, which is delivered to the Committee Preparation Agent as an input for the Evaluation Completion Record.

### 3.5 Confidence Monitoring

After each agent completes, the Orchestration Controller reads the agent's aggregate confidence score from its output. If the confidence score is below the TAES Minimum Confidence Floor (as specified in the TAES Platform Configuration), the Orchestration Controller sets the escalation flag for that agent and initiates the human review escalation protocol. The evaluation pipeline does not halt during escalation — other agents that do not depend on the escalated agent's output continue to execute. Agents that depend on an escalated agent's output are held in Pending state until the escalation is resolved.

---

## 4. Error Handling and Low-Confidence Management

### 4.1 Agent Failure Classification

Agent failures in the TAES pipeline are classified into three categories:

**Category 1 — Schema Non-Compliance:** The agent produces output that does not conform to the TAES Agent Output Contract schema. This is treated as a hard failure. The Orchestration Controller rejects the output, logs the failure, and queues the agent for re-execution. If re-execution also fails, the evaluation pipeline is escalated to human review and the committee session is postponed until the failure is resolved.

**Category 2 — Low Confidence Output:** The agent produces schema-compliant output but with an aggregate confidence score below the TAES Minimum Confidence Floor on one or more primary output fields. This is treated as a soft failure triggering escalation. The pipeline continues; human review is requested for the flagged fields.

**Category 3 — Incomplete Input:** The agent detects that a required input is absent or incomplete — for example, an upstream agent's output is missing a required section. The agent must not proceed with partial inputs. It must report an incomplete input error to the Orchestration Controller, which investigates whether the upstream agent experienced a failure or whether the field is a legitimate data absence.

### 4.2 Human Review Escalation Protocol

When an agent escalation flag is set, the Orchestration Controller initiates the following protocol:

1. The flagged agent output, its data gap register, and the specific fields triggering the confidence floor breach are packaged into a human review request and routed to the TIDES Evaluation Review Queue.
2. A human evaluator reviews the flagged fields, supplements the evidence where possible from sources available to the programme team, and either: re-triggers the agent with supplemented inputs, or records a formal evidence-absent notation for the flagged field and clears the escalation flag with an evidence-absent status.
3. The cleared output — whether re-executed or evidence-absent — is returned to the Orchestration Controller, which routes it to all dependent downstream agents.
4. The escalation event, its resolution type, and the human reviewer's identity are recorded in the Execution Log.

### 4.3 Evidence-Absent Notation

When a human reviewer confirms that a data gap cannot be supplemented — because the information genuinely does not exist in the evaluation context — the evidence-absent notation is applied. Fields marked as evidence-absent are included in all downstream agent inputs with their evidence-absent status clearly flagged. Downstream agents must treat evidence-absent fields as confirmed absences rather than data errors. The Recommendation Agent must reflect the presence of evidence-absent fields in its confidence advisory and must note their potential impact on the final recommendation.

### 4.4 Pipeline Partial Execution Policy

Under certain circumstances — for example, a startup that submits a minimal application with few documents — multiple agents may produce low-confidence outputs simultaneously. The TAES partial execution policy specifies that:

- The pipeline always completes to the Committee Preparation Agent stage, even if multiple escalation flags are active.
- The Executive Briefing must clearly identify all dimensions where confidence is below the minimum floor.
- The Final Evaluation Recommendation must carry a confidence advisory if the aggregate confidence across all domains is below the TAES Recommendation Confidence Floor.
- The investment committee receives the evaluation package with all confidence limitations clearly disclosed, and the committee chair is informed of the escalation history.

---

## 5. Agent Output Contract — Standard Schema

Every agent in the TAES pipeline must produce output that conforms to the following standard schema. Domain-specific output fields are appended to this schema within each agent's designated content block. The schema is version-controlled under the TAES Platform Configuration.

### 5.1 Schema Structure

Every agent output document must contain the following top-level sections:

**Section 1: Agent Execution Metadata**
- Agent name (from the TAES Agent Registry)
- Agent version identifier
- Execution start timestamp (ISO 8601)
- Execution end timestamp (ISO 8601)
- Execution duration in seconds
- Orchestration Controller session identifier
- Evaluation run identifier (unique per startup application evaluation)
- Startup application identifier

**Section 2: Input Manifest**
A structured list of every input consumed during execution. For each input:
- Input source type (SEDO field, document, upstream agent output)
- Input source identifier (field name, document ID, or agent name and output field)
- Input version or timestamp
- Whether the input was received as complete, partial, or absent

**Section 3: Domain Content Block**
The agent-specific evaluation output, as defined in the agent's individual specification in Section 2 of this document. All domain content blocks must follow the evidence attribution standard specified in Section 5.2.

**Section 4: Data Gap Register**
A structured list of information items that were expected but absent, ambiguous, or unverifiable. For each gap:
- Gap identifier
- Description of the missing information
- Expected data source
- Impact on output confidence (Critical, Significant, Minor)
- Whether a data gap flag was set for this item

**Section 5: Field-Level Confidence Scores**
For each primary output field in the Domain Content Block:
- Field identifier
- Confidence score (0.0–1.0)
- Confidence basis (list of evidence items that support the field value)
- Confidence limiting factors (data gaps or quality issues reducing confidence)

**Section 6: Aggregate Confidence Summary**
- Aggregate confidence score (0.0–1.0), computed as the weighted mean of field-level confidence scores using the field weights specified in the agent's domain specification
- Escalation flag (boolean): true if aggregate confidence is below the TAES Minimum Confidence Floor
- Escalation reason (if escalation flag is true): a written description of the primary factors driving low confidence

**Section 7: Downstream Routing Manifest**
A list of downstream agents that are expected to consume this output, with the specific output fields they consume, enabling the Orchestration Controller to verify routing completeness.

### 5.2 Evidence Attribution Standard

Every scored or classified field in the Domain Content Block must carry an evidence reference block containing:
- A list of evidence items, each identified by: source type (SEDO field, document section, upstream agent output field), source identifier, and the specific claim or value within that source that supports the field value.
- An evidence quality rating for each evidence item: Independent Third-Party Validation, Internal Claim with Supporting Documentation, or Internal Claim Only.
- A statement of any conflicting evidence — evidence items that point to a different value or classification than the one assigned — and the rationale for the resolution.

Fields produced without conforming evidence references are non-compliant with the Output Contract and must not be included in downstream agent inputs.

---

## 6. TAES Compliance Enforcement

### 6.1 The Three-Layer Compliance Architecture

TAES compliance is enforced through three independent, layered mechanisms that operate simultaneously:

**Layer 1 — Schema Validation.** The Orchestration Controller validates every agent output against the Agent Output Contract schema before accepting it and routing it to downstream agents. Schema validation is syntactic and structural: it verifies that all required sections are present, that all fields have the required data types, and that evidence reference blocks are present for all scored fields. Schema validation does not assess the quality or truthfulness of the content — it assesses structural compliance.

**Layer 2 — Confidence Floor Enforcement.** The Orchestration Controller reads the aggregate confidence score from every agent output and compares it to the TAES Minimum Confidence Floor. Outputs below the floor trigger the escalation protocol. Confidence floor enforcement is a runtime quality gate that prevents low-quality, low-evidence outputs from flowing through the pipeline unchallenged.

**Layer 3 — Evidence Traceability Audit.** The Committee Preparation Agent's Score Verification Appendix enables post-execution human audit of the evidence trail behind every domain score. This is a retrospective compliance mechanism: after the evaluation completes, any committee member may request that a score be traced back to its originating evidence in the source documents. The evidence reference blocks produced by each agent enable this trace. Any score that cannot be traced through the evidence reference chain is flagged as a compliance failure in the post-evaluation audit.

### 6.2 Hallucination Prevention Architecture

The TAES architecture prevents hallucination through structural design, not instruction alone:

**Input scope restriction.** Each agent receives only the SEDO sections and upstream agent output fields relevant to its domain. An agent that has not received information about a topic cannot hallucinate that topic into its output because the topic is not within its input scope.

**Output schema constraint.** Agent outputs must conform to the Agent Output Contract schema, which requires every scored field to have an associated evidence reference. A hallucinated claim that cannot be referenced to a specific input source fails schema validation and is rejected.

**Absence recording requirement.** The Data Gap Register requires agents to explicitly record the absence of expected information. This structural requirement creates a positive incentive for agents to record absences rather than fill them with generated content.

**Evidence quality classification.** The evidence quality classification system — which distinguishes between third-party validation, internal claim with documentation, and internal claim only — creates a structured record of evidence quality that downstream agents and human reviewers can use to assess the degree of inference in each finding.

### 6.3 Evidence-First Principle Enforcement

The evidence-first principle — that every evaluation finding must be grounded in available evidence and must not precede or substitute for evidence — is enforced through:

- The requirement that every field carry an evidence reference block before it is accepted by the schema validator.
- The confidence scoring system, which produces lower scores for fields supported only by low-quality evidence, creating a natural quantification of the evidence base's strength.
- The Recommendation Agent's constraint that it cannot introduce new findings not present in upstream agent outputs — ensuring that the final recommendation is always downstream of, not concurrent with, the evidence.

### 6.4 No-Hallucination Principle Compliance Records

The Evaluation Completion Record produced by the Committee Preparation Agent includes a compliance attestation section. This section records, for each agent in the pipeline:
- Whether the agent's output passed schema validation on first submission.
- The agent's aggregate confidence score.
- Whether any escalation was triggered and how it was resolved.
- The evidence attribution completeness ratio (the proportion of scored fields that carry complete evidence reference blocks).

This compliance attestation constitutes the audit record for TAES principle adherence and is retained in the TIDES compliance repository for the duration specified in the TIDES Data Retention Policy.

---

## 7. Data Flow Pipeline

The following describes the complete data flow of the TAES evaluation pipeline as a numbered, step-by-step sequence. Each step identifies what is transmitted, from which source, to which destination, and what action is taken.

**Step 1 — Evaluation Trigger.** The TIDES Application Management System receives a completed startup application submission and transmits an evaluation trigger event to the Orchestration Controller. The trigger event contains: the startup application identifier, a pointer to the application package (all form data and uploaded documents), the application submission timestamp, and the TIDES intake cohort identifier.

**Step 2 — Application Package Validation.** The Orchestration Controller validates the application package against the TIDES Application Completeness Policy, confirming that minimum required fields and documents are present. If the package fails completeness validation, the applicant is notified of missing materials and the evaluation is held. If the package passes, the Orchestration Controller proceeds to Step 3.

**Step 3 — Knowledge Extraction Initiation.** The Orchestration Controller transmits the complete application package — all form data and document attachments — to the Knowledge Extraction Agent, along with the TAES Canonical Data Schema and the Document Registry initialisation template. The Orchestration Controller marks the Knowledge Extraction Agent status as Running.

**Step 4 — Knowledge Extraction Execution.** The Knowledge Extraction Agent processes all application materials, performs entity extraction, normalisation, inconsistency detection, and completeness assessment, and produces the Startup Evaluation Data Object (SEDO), the Document Registry, the Inconsistency Register, and the Data Completeness Map. The agent produces its output in conformance with the Agent Output Contract schema.

**Step 5 — SEDO Schema Validation.** The Orchestration Controller receives the Knowledge Extraction Agent output and validates it against the Agent Output Contract schema. If validation fails, the agent is queued for re-execution. If validation passes, the Orchestration Controller marks the Knowledge Extraction Agent status as Completed and proceeds to Step 6.

**Step 6 — Tier 1 Phase 1A Dispatch.** The Orchestration Controller dispatches inputs to six Tier 1 agents simultaneously. Each agent receives its domain-scoped projection of the SEDO (only the sections relevant to its domain), the Document Registry, and the Data Completeness Map:
- Founder Evaluation Agent receives: Founder Record Set, Company Profile Block, Document Registry, Completeness Map.
- Product Evaluation Agent receives: Product Description Block, Traction Evidence Block, Company Profile Block, Document Registry, Completeness Map.
- TRL Assessment Agent receives: Product Description Block, Traction Evidence Block, IP Data Block, Document Registry, TAES TRL Framework Definition.
- Market Intelligence Agent receives: Market Data Block, Product Description Block, Company Profile Block, Document Registry, TIDES Market Reference Database reference.
- Financial Analysis Agent receives: Financial Data Block, Traction Evidence Block, Company Profile Block, Document Registry, Inconsistency Register (financial), TAES Financial Benchmark Database reference.
- Patent and IP Agent receives: IP Data Block, Product Description Block, Founder Record Set, Document Registry, TAES IP Reference Framework.

All six agents are marked Running simultaneously by the Orchestration Controller.

**Step 7 — Market Intelligence Agent Completion.** The Market Intelligence Agent completes first among the Tier 1 Phase 1A agents (or in parallel with others — the Orchestration Controller monitors for its completion specifically). Upon completion and schema validation, the Market Intelligence Report is marked available. This event triggers Step 8.

**Step 8 — Tier 1 Phase 1B Dispatch.** The Orchestration Controller dispatches inputs to the Competition Analysis Agent: it receives its domain-scoped SEDO projection (Product Description Block), the Market Intelligence Report (SAM definition and target customer segment), the TIDES Competitive Reference Database reference, and the Document Registry. The Competition Analysis Agent is marked Running.

**Step 9 — Tier 1 Completion Monitoring.** The Orchestration Controller monitors the remaining Tier 1 Phase 1A agents and the Competition Analysis Agent for completion. As each completes, its output is schema-validated, its confidence score is read, and if the confidence score is below the TAES Minimum Confidence Floor, an escalation is triggered. The agent is marked Completed (or Escalated). This step continues until all seven Tier 1 agents are marked Completed or Escalated-Resolved.

**Step 10 — Risk Assessment Dispatch.** Once all seven Tier 1 domain agents are in Completed or Escalated-Resolved status, the Orchestration Controller assembles the Risk Assessment Agent inputs — the risk-relevant output sections from all seven Tier 1 agents, plus the Inconsistency Register and Data Completeness Map from the Knowledge Extraction Agent — and dispatches them to the Risk Assessment Agent. The Risk Assessment Agent is marked Running.

**Step 11 — Risk Assessment Completion.** The Risk Assessment Agent completes and produces the Risk Assessment Report. The Orchestration Controller schema-validates the output, reads the confidence score, and marks the agent Completed or Escalated.

**Step 12 — Tier 2 Phase 2B Dispatch.** Once the Risk Assessment Agent is in Completed or Escalated-Resolved status, the Orchestration Controller dispatches inputs simultaneously to the Recommendation Agent and the Mentorship Matching Agent:
- The Recommendation Agent receives all domain evaluation report primary outputs, the Risk Assessment Report, the Data Completeness Map, the TAES Scoring Weights Framework, and the TIDES Programme Criteria.
- The Mentorship Matching Agent receives the Founder Evaluation Report, Financial Analysis Report, IP Assessment Report, Risk Assessment Report, and TIDES Mentor Registry reference.

Both agents are marked Running simultaneously.

**Step 13 — Recommendation and Mentorship Completion.** The Recommendation Agent and Mentorship Matching Agent complete and produce their outputs. The Orchestration Controller schema-validates each output, reads confidence scores, and marks each agent Completed or Escalated.

**Step 14 — Committee Preparation Dispatch.** Once both the Recommendation Agent and Mentorship Matching Agent are in Completed or Escalated-Resolved status, the Orchestration Controller assembles all agent outputs — the complete output set from all twelve agents — and dispatches them to the Committee Preparation Agent, along with the Orchestration Controller Execution Log and the TIDES Committee Briefing Template. The Committee Preparation Agent is marked Running.

**Step 15 — Committee Briefing Package Assembly.** The Committee Preparation Agent assembles the full Committee Briefing Package, produces all five output components, and transmits them to the TIDES Committee Briefing Distribution System.

**Step 16 — Evaluation Completion Notification.** The Orchestration Controller receives confirmation that the Committee Briefing Package has been successfully delivered. It marks the evaluation run as Completed, finalises the Execution Log, and transmits an evaluation completion notification to the TIDES Application Management System, which updates the startup's application status to Evaluation Complete.

**Step 17 — Compliance Record Archival.** The Orchestration Controller transmits the complete Execution Log and the Evaluation Completion Record (produced by the Committee Preparation Agent) to the TIDES Compliance Repository, where they are archived per the TIDES Data Retention Policy.

---

## 8. Extensibility — Adding New Agents

### 8.1 The Extension Design Principle

The TAES multi-agent architecture is designed for extensibility. New evaluation dimensions — for example, a Regulatory Compliance Agent, an ESG Assessment Agent, or a Geographic Market Agent — can be added to the pipeline without modifying or disrupting existing agents. The extension design principle requires that new agents must conform to all existing architectural constraints: they must produce Agent Output Contract-compliant outputs, they must consume inputs only through the Orchestration Controller's routing mechanism, and they must declare their dependencies explicitly in the dependency graph.

### 8.2 Extension Procedure

Adding a new agent to the TAES pipeline requires the following formal steps:

**Step 1 — Agent Specification.** The new agent must be fully specified according to the agent definition format established in Section 2 of this document. The specification must include all required subsections: Mission, Responsibilities, Inputs, Outputs, Dependencies, Evaluation Rules, Expected Deliverables, and Interaction with Other Agents. The specification must be reviewed and ratified by the TAES Platform Architecture Board before implementation.

**Step 2 — Dependency Graph Update.** The new agent's position in the dependency graph must be formally defined: which tier it occupies, which upstream agents it depends on, and which downstream agents will consume its outputs. If the new agent introduces a new inter-Tier-1 dependency, the dependency must be validated to ensure it does not create a circular dependency or an incompatible execution ordering.

**Step 3 — Input Routing Table Update.** The Orchestration Controller's Input Routing Table must be updated to include the new agent: the inputs it receives (with source identifiers) and the downstream agents that will receive its outputs (with the specific output fields to be routed).

**Step 4 — Schema Extension.** If the new agent introduces new output fields that will be consumed by existing downstream agents — for example, if an ESG Assessment Agent's ESG Risk Designation will be consumed by the existing Recommendation Agent — the affected downstream agents' input schemas must be formally updated. The TAES Scoring Weights Framework must be updated to accommodate the new dimension if the new agent contributes to the Composite Evaluation Score.

**Step 5 — Backward Compatibility Verification.** The updated pipeline must be verified to ensure that all existing agents remain functionally unmodified. Existing agents must not be required to change their input consumption, output production, or dependency declarations to accommodate a new agent. New agents must be additive, not modifying.

**Step 6 — Validation and Testing.** The new agent must be validated against a set of reference evaluation cases before production deployment. Validation must confirm: schema compliance, confidence scoring behaviour across evidence-rich and evidence-sparse inputs, correct escalation flag behaviour, and correct output routing.

**Step 7 — Version Update.** The addition of a new agent constitutes a minor version increment to the TAES architecture (e.g., TAES v1.0 → TAES v1.1). The new agent's addition, its specification, and the updated pipeline configuration must be recorded in the TAES Platform Change Log.

### 8.3 Extensibility Constraints

To maintain pipeline integrity, the following constraints apply to all agent extensions:

- **No modification of existing agent outputs.** A new agent must not require any existing agent to modify its output schema to accommodate the new agent's input requirements. The new agent must work with existing agent outputs as they are.
- **No new Tier 0 agents.** The Knowledge Extraction Agent is the sole Tier 0 agent. No additional Tier 0 agent may be introduced without a major version revision of the TAES architecture.
- **Scoring weight conservation.** If a new agent introduces a new domain score that contributes to the Composite Evaluation Score, the TAES Scoring Weights Framework must be updated so that all domain weights continue to sum to 100%. Existing domain weights may be reduced proportionally, but any reduction of more than 5 percentage points in any existing domain's weight requires formal TAES governance approval.
- **Escalation protocol conformance.** All new agents must conform to the existing escalation protocol. No new agent may introduce a custom escalation pathway that bypasses the Orchestration Controller.

---

## 9. Glossary

| Term | Definition |
|---|---|
| **Agent Output Contract** | The standard schema that every TAES evaluation agent must produce, specifying required fields, evidence attribution requirements, confidence scoring structure, and routing manifest. |
| **TAES** | TIDES AI Evaluation Standard — the evaluation framework governing AI-assisted startup assessment on the TIDES platform. |
| **TIDES** | The incubator/accelerator programme platform for which the TAES architecture is the primary evaluation infrastructure. |
| **SEDO** | Startup Evaluation Data Object — the normalised, structured data object produced by the Knowledge Extraction Agent from raw application materials and consumed by all Tier 1 domain evaluation agents. |
| **Orchestration Controller** | The centralised coordination layer responsible for agent scheduling, input routing, output collection, dependency enforcement, and escalation management. |
| **TRL** | Technology Readiness Level — a nine-level scale used to classify the maturity of a technology from basic research (TRL 1) to proven deployment (TRL 9). |
| **TAM** | Total Addressable Market — the total revenue opportunity available if a product achieved 100% market share in its target market. |
| **SAM** | Serviceable Addressable Market — the portion of the TAM that a startup can realistically target given its current product scope and geographic reach. |
| **SOM** | Serviceable Obtainable Market — the portion of the SAM that a startup can realistically capture given its current resources and competitive position. |
| **CAC** | Customer Acquisition Cost — the total cost incurred to acquire a single new customer. |
| **LTV** | Lifetime Value — the total net revenue expected from a customer over the full duration of their relationship with the company. |
| **Confidence Floor** | The minimum acceptable aggregate confidence score for any agent output, as specified in the TAES Platform Configuration. Outputs below this floor trigger escalation. |
| **Evidence-Absent Notation** | A formal record indicating that a specific data field is confirmed to be absent from all available evaluation sources, applied after human review confirms the absence. |
| **Escalation Protocol** | The standardised procedure triggered when an agent output falls below the confidence floor or fails schema validation, routing the flagged output to human review. |
| **TIDES Mentor Registry** | The maintained database of TIDES programme mentor profiles used by the Mentorship Matching Agent for matching. |
| **TAES Scoring Weights Framework** | The canonical specification of the weights assigned to each domain evaluation score for the computation of the Composite Evaluation Score. |
| **Compound Risk** | A risk that arises from the interaction of two or more domain-specific risks, with an effective severity greater than either risk alone. |
| **Composite Evaluation Score** | The weighted aggregate score (0–100) produced by the Recommendation Agent by applying the TAES Scoring Weights Framework to all domain scores. |
| **Committee Briefing Package** | The complete set of documents produced by the Committee Preparation Agent for distribution to investment committee members. |
| **Execution Log** | The complete record of the Orchestration Controller's activities during an evaluation run, including all agent execution timestamps, confidence scores, escalations, and resolutions. |
| **Tier 0 / Tier 1 / Tier 2** | The three execution tiers of the TAES pipeline: Tier 0 (Knowledge Extraction), Tier 1 (domain evaluation), and Tier 2 (synthesis and preparation). |
| **TIDES Market Reference Database** | A curated reference dataset maintained by the TIDES programme containing sector-level market size and growth benchmarks used by the Market Intelligence Agent. |
| **TIDES Competitive Reference Database** | A structured database of competitor profiles for sectors commonly represented in TIDES applicants, used by the Competition Analysis Agent. |
| **TAES Financial Benchmark Database** | Sector and stage-specific financial benchmarks used by the Financial Analysis Agent to contextualise startup financial metrics. |
| **Information Asymmetry Risk** | The risk that material negative information about a startup has not been disclosed in the application, inferred from significant data gaps in the submission. |
| **Input Routing Table** | The static Orchestration Controller configuration mapping each agent's required inputs to their sources in upstream agent outputs and SEDO sections. |

---

*End of Document — TAES v1.0 / AI Evaluation Agent Architecture — Version 1.0.0*

*This document is subject to version control under the TAES Platform Architecture Board. Amendments require formal governance review. The next scheduled review date is 2027-06-23.*
