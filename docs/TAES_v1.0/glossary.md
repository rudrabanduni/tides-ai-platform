# Glossary — TIDES AI Evaluation Standard (TAES v1.0)

> **Document:** TAES v1.0 / Glossary  
> **Classification:** Internal Technical Standard  
> **Version:** 1.0.0

---

This glossary defines every significant term used across the TAES v1.0 documentation suite. Terms are listed alphabetically within their category. Where a term is used with a specific technical meaning within the TIDES platform that differs from its common usage, the TIDES-specific definition takes precedence.

---

## A

**Addressable Market**  
The portion of the Total Addressable Market (TAM) that a specific business can realistically target given its product scope, geography, and distribution capability. See also: SAM, SOM.

**Agent Output Contract**  
The formal specification that defines what structured data every AI evaluation agent must produce, including required fields, evidence citations, confidence scores, and metadata. No agent may deviate from the output contract. Defined in [07_AI_Evaluation_Agent_Architecture.md](./07_AI_Evaluation_Agent_Architecture.md).

**Audit Log**  
A time-stamped, immutable record of every action taken on the platform. Audit logs capture who performed an action, when, what the input was, and what the output was. All AI evaluation steps must be recorded in the audit log to support retrospective review and reproducibility.

---

## B

**Benchmark**  
A quantitative reference point derived from aggregated, anonymised evaluation data across multiple startups in a defined sector and lifecycle stage. Benchmarks are used to contextualise individual startup scores and identify relative strengths and weaknesses. Benchmarks are not available in Phase 1 and will be introduced progressively as the data set grows.

**BRL (Business Readiness Level)**  
A parallel readiness scale to TRL that assesses how commercially ready a technology or product is, independent of its technical maturity. A product can be at TRL 7 but BRL 3 (technically proven but not yet commercially viable). The TIDES platform uses TRL as its primary technology maturity indicator; BRL is discussed as a complementary concept in [04_TRL_Assessment_Standard.md](./04_TRL_Assessment_Standard.md).

**Burn Rate**  
The rate at which a startup consumes its cash reserves in the absence of sufficient revenue to cover operating costs, typically expressed as a monthly figure. High burn rate relative to runway is a financial risk signal. Formula: `Monthly Burn = Beginning Cash Balance − Ending Cash Balance (for the period)`.

---

## C

**CAC (Customer Acquisition Cost)**  
The total cost of acquiring a single new paying customer, including all marketing and sales expenses divided by the number of new customers acquired in a period. High CAC relative to LTV is a critical red flag in the Financial pillar. Formula: `CAC = Total Sales & Marketing Spend / Number of New Customers Acquired`.

**Cohort**  
A defined group of startups processed through the evaluation pipeline together, typically corresponding to an incubator intake batch. All startups in a cohort are evaluated under the same TAES version and (unless sector normalisation applies) the same default pillar weights.

**Committee Agent**  
See: *Committee Preparation Agent*.

**Committee Preparation Agent**  
The AI agent responsible for synthesising all individual agent outputs into a structured briefing document for the evaluation committee. This agent does not evaluate; it organises, prioritises, and presents. Defined in [07_AI_Evaluation_Agent_Architecture.md](./07_AI_Evaluation_Agent_Architecture.md).

**Confidence Interval**  
A range within which the true score of a startup is estimated to fall, given the completeness and quality of available evidence. Not used as a statistical confidence interval in the formal sense, but as an operationally meaningful range: e.g., "the Founder score is 6.5 ± 1.0 at 70% confidence."

**Confidence Score**  
A value between 0.0 and 1.0 that expresses how much the AI evaluation trusts its own output for a given finding, criterion, or pillar score. A confidence score of 1.0 means all required evidence was present, unambiguous, and internally consistent. A confidence score of 0.3 means the finding is based on very limited or contradictory evidence and should be treated as provisional. Every AI output on the TIDES platform must carry a confidence score.

**Context Object**  
The structured data package assembled by the `StartupProfileContextBuilder` that contains all available information about a startup in a single, agent-consumable format. The context object is the primary input for all AI evaluation agents.

**Commercial Readiness**  
The degree to which a startup's product, team, and go-to-market capabilities are prepared for commercial deployment. Commercial readiness is distinct from technical readiness (TRL). A startup may have high TRL and low commercial readiness. Assessed through the Product, Business Model, and Market pillars.

**Customer Validation**  
Documented evidence that real, identified customers have engaged with, used, paid for, or expressed strong intent to pay for the startup's product or service. Customer validation is a high-weight evidence type for multiple evaluation pillars. Letters of intent, signed contracts, pilot agreements, and payment receipts are all forms of customer validation evidence.

---

## D

**DPIIT (Department for Promotion of Industry and Internal Trade)**  
The Indian government department responsible for startup recognition, policy, and scheme eligibility. DPIIT recognition is a formal validation signal relevant to Indian startups and is recorded as evidence in the startup profile.

**Due Diligence**  
The investigative process by which an investor, incubator, or institution systematically verifies the claims made by a startup before making a commitment. The TIDES evaluation pipeline is designed to automate and structure the first layer of this process.

---

## E

**Evidence**  
Any verifiable, source-attributed piece of information used to support or contradict a claim in a startup evaluation. Evidence must be traceable to a specific source: a document page, a structured field, a verified URL, or a recorded human statement. Unverified claims are not evidence. Inferences without cited sources are not evidence.

**Evidence Bundle**  
The collection of specific evidence items that support a particular finding, score, or recommendation. Every AI output on the TIDES platform must carry an evidence bundle. An evidence bundle without source attribution is invalid.

**Evidence Score**  
A normalised measure of how much valid evidence exists to support a particular evaluation finding or pillar score. Distinct from the pillar score itself: a startup might have a high evidence score (plenty of evidence available) but a low pillar score (the evidence reveals weaknesses). Evidence score directly determines the confidence score.

**Evaluation Cycle**  
A complete pass of a startup through the TAES evaluation pipeline, producing a full set of pillar scores, a confidence assessment, and a final recommendation. A startup may go through multiple evaluation cycles at different points in time.

**Evaluation Pillar**  
One of the eight primary dimensions along which startups are assessed in the TIDES platform: Founder, Product, Technology, Market, Business Model, Financial, IP, and Risk. Each pillar has a defined scoring methodology, evidence requirements, and configurable weight. Defined in [05_Scoring_Standard.md](./05_Scoring_Standard.md).

**Exit**  
The event by which an investor realises a return on their investment in a startup, typically through acquisition, merger, or initial public offering (IPO). Exit probability and timeline are future analytics capabilities planned for Phase 4 of the roadmap.

---

## F

**Fairness**  
In the context of TAES, fairness means that no startup is penalised for characteristics that are structurally normal for its sector and lifecycle stage. A biotech startup with no revenue at TRL 4 should not receive a low Financial score simply because it has no revenue — it should be evaluated against sector-appropriate expectations. Fairness is operationalised through sector normalisation. Defined in [02_Evaluation_Principles.md](./02_Evaluation_Principles.md) and [06_Sector_Normalization_Standard.md](./06_Sector_Normalization_Standard.md).

**False Positive (Evaluation)**  
A startup that the AI evaluation rates highly but which subsequently fails to meet expected milestones. False positives are tracked over time to refine scoring calibration.

**False Negative (Evaluation)**  
A startup that the AI evaluation rates poorly but which subsequently achieves significant success. False negatives are equally tracked to refine scoring calibration, and to prevent systematic bias against certain types of startups.

**Founder-Market Fit**  
The degree to which a startup's founding team has the background, domain expertise, network, and lived experience to address the specific problem and market they are targeting. Founder-market fit is a key sub-criterion in the Founder evaluation pillar.

---

## G

**Go-to-Market (GTM) Strategy**  
The plan by which a startup intends to acquire its first customers, grow its customer base, and achieve commercial scale. A clearly articulated GTM strategy is evidence in the Market and Business Model pillars.

**Governance**  
The set of rules, standards, and oversight mechanisms that ensure the TIDES platform operates consistently, transparently, and in accordance with its stated principles. TAES is the primary governance instrument.

---

## H

**Hallucination**  
In the context of AI evaluation, a hallucination is any AI-generated assertion about a startup that is not grounded in evidence present in the startup's submission. Hallucination is explicitly prohibited by TAES. When evidence is insufficient, the agent must declare the gap, not fill it with inference. Defined as a principle in [02_Evaluation_Principles.md](./02_Evaluation_Principles.md).

**Human-in-the-Loop (HITL)**  
The design principle that ensures a human reviewer is always present and empowered in the evaluation process. In the TIDES platform, HITL means: (a) AI outputs are always advisory; (b) human reviewers can override any AI score; (c) human decisions are recorded separately from AI recommendations; (d) the final recommendation on a startup is a human decision. Defined in [02_Evaluation_Principles.md](./02_Evaluation_Principles.md).

---

## I

**Incubation Readiness**  
A composite assessment of how ready a startup is to benefit from and contribute to an incubation programme. Incubation readiness considers stage, TRL, team completeness, and identified gaps that the incubation programme could address. It is one of the factors that informs the final recommendation.

**IP (Intellectual Property)**  
Legally recognised exclusive rights over creations of the mind. In the context of startup evaluation, IP includes patents (granted and pending), trademarks, trade secrets, copyrights, and proprietary data sets. IP status is one of the eight evaluation pillars. A strong IP position can constitute a competitive moat.

**Investment Readiness**  
A composite assessment of how prepared a startup is to receive and effectively deploy external investment. Investment readiness considers financial discipline, market clarity, product maturity, and team capability. Distinct from incubation readiness, though related. Relevant from Phase 4 of the platform roadmap.

---

## K

**Knowledge Extraction Agent**  
The first agent in the TIDES evaluation pipeline, responsible for parsing all structured and unstructured startup data into a normalised, agent-consumable evidence base. All downstream agents consume the output of this agent. Defined in [07_AI_Evaluation_Agent_Architecture.md](./07_AI_Evaluation_Agent_Architecture.md).

---

## L

**Lifecycle Stage**  
One of nine defined stages — Idea, Research, Prototype, MVP, Pilot, Early Revenue, Product Market Fit, Growth, Scale — that describes where a startup is in its development journey. Lifecycle stage is a primary context variable that affects scoring expectations, pillar weights, and evidence requirements. Defined in [03_Startup_Lifecycle_Framework.md](./03_Startup_Lifecycle_Framework.md).

**LiteLLM**  
An open-source AI gateway library that provides a unified API for interacting with multiple large language model providers (Claude, GPT, Gemini, etc.). The TIDES platform uses LiteLLM as its AI infrastructure layer to enable provider-agnostic AI agent execution.

**LTV (Lifetime Value)**  
The total revenue a business expects to generate from a single customer over the entire duration of the relationship. The LTV:CAC ratio is a critical unit economics indicator. Formula: `LTV = Average Revenue Per User × Average Customer Lifespan`. A ratio of LTV:CAC ≥ 3 is generally considered healthy for SaaS businesses.

---

## M

**Mentorship Matching Agent**  
The AI agent responsible for recommending appropriate mentor profiles for a startup based on identified gaps in the team, product, market knowledge, and execution capability. This agent consumes the outputs of all pillar evaluation agents. Defined in [07_AI_Evaluation_Agent_Architecture.md](./07_AI_Evaluation_Agent_Architecture.md).

**Moat**  
A structural competitive advantage that makes it difficult for competitors to replicate a startup's business. A moat can be technological (proprietary IP, trade secrets), network-based (platform effects), cost-based (economies of scale), regulatory (licences, approvals), or brand-based. Moat assessment is a sub-criterion in both the Technology and Market pillars.

**MRR (Monthly Recurring Revenue)**  
The predictable, normalised monthly revenue generated from subscription-based customers. MRR is a primary financial metric for SaaS startups. It excludes one-time payments and is the basis for growth rate calculations.

---

## N

**Normalisation**  
In the TIDES context, the process of adjusting evaluation criteria, scoring weights, and benchmark expectations based on the startup's sector and lifecycle stage. Normalisation ensures that startups are evaluated against appropriate peer comparators, not a single universal standard. Defined in [06_Sector_Normalization_Standard.md](./06_Sector_Normalization_Standard.md).

---

## P

**Pillar Score**  
The numerical score (0–10) assigned to one of the eight evaluation pillars for a specific startup in a specific evaluation cycle. Each pillar score is accompanied by an evidence bundle and a confidence score.

**PMF (Product Market Fit)**  
The state in which a startup's product satisfies a strong and real market demand such that the market is pulling the product forward. PMF is evidenced by strong retention, organic growth, increasing NPS, and customer willingness to pay without heavy discounting. PMF is both a lifecycle stage in TAES and a sub-criterion in the Product and Market pillars.

**Profile Version**  
A time-stamped snapshot of a startup's profile data. Each time the startup is re-evaluated or submits new information, a new profile version is created. The platform maintains a full history of profile versions, enabling longitudinal tracking and comparison.

---

## R

**Recommendation**  
The formal output of the final evaluation step, expressing what the platform suggests should happen with this startup. Valid recommendations in TAES v1.0 are: **Incubate**, **Conditional Incubation**, **Defer**, and **Reject**. The recommendation is produced by the Recommendation Agent and is advisory — a human reviewer makes the final decision.

**Recommendation Rules**  
Configurable rules that govern how pillar scores, confidence scores, and risk signals are translated into a recommendation. Recommendation rules are stored as structured configuration in the database (`RecommendationRules` model) and can be updated without changing application code.

**Repeatability**  
The property of an evaluation process that guarantees materially identical outputs when run on identical inputs. TAES requires that every evaluation be repeatable: the same startup data, the same agent versions, and the same configuration must produce scores within a defined tolerance band. Defined in [02_Evaluation_Principles.md](./02_Evaluation_Principles.md).

**Repository-Service Pattern**  
The architectural pattern used in the TIDES backend. Repositories handle all database interactions; services contain business logic and orchestrate repositories. This pattern is used throughout the existing platform and must be maintained as new modules are added.

**Risk Matrix**  
A structured representation of identified risks, categorised by type and rated by both likelihood and impact. The Risk Matrix appears in every TIDES report and is produced by the Risk Assessment Agent.

**Runway**  
The number of months a startup can continue operating at its current burn rate before running out of cash. Formula: `Runway (months) = Current Cash Balance / Monthly Burn Rate`. Runway below 6 months is a critical financial risk signal.

---

## S

**SAM (Serviceable Addressable Market)**  
The portion of the Total Addressable Market that a startup can realistically reach with its current product, distribution strategy, and geographic focus. SAM is narrower than TAM and broader than SOM.

**Score Override**  
The action by which a human reviewer replaces an AI-generated pillar score with a score based on their own judgment. Score overrides are permitted under TAES but must be formally recorded, including the reviewer's identity, the rationale for the override, and the original AI score. Override records are stored in the `ScoreOverrides` database table.

**Sector**  
The industry domain in which a startup operates. Sector classification affects normalisation, TRL expectations, scoring weight configuration, and benchmark comparisons. Current supported sectors are defined in [06_Sector_Normalization_Standard.md](./06_Sector_Normalization_Standard.md).

**SOM (Serviceable Obtainable Market)**  
The portion of the SAM that a startup can realistically capture within a defined timeframe, given its competitive position, resources, and execution capability. SOM is the most conservative and operationally relevant market size estimate.

**Startup Profile**  
The canonical, structured record that represents a startup's current state on the platform. The Startup Profile is the primary input to the AI evaluation pipeline. It is versioned, enabling historical comparison.

**StartupProfileContextBuilder**  
A Python class in the TIDES backend (`app/modules/startup_profiles/context.py`) that assembles the complete evaluation context object from all available startup data. The context object it produces is the primary input for all AI agents.

---

## T

**TAES (TIDES AI Evaluation Standard)**  
The governing technical specification that defines how every AI-driven startup evaluation must be conducted on the TIDES platform. This document suite constitutes TAES v1.0.

**TAM (Total Addressable Market)**  
The total global market demand for a product or service, expressed as the maximum possible revenue if the business captured 100% market share. TAM is used as a directional indicator of market potential, not as an achievable target.

**TIDES**  
The name of the AI-powered startup evaluation platform that this standard governs.

**TRL (Technology Readiness Level)**  
A standardised scale from TRL 1 to TRL 9 that classifies the maturity of a technology. Originally developed by NASA, adapted for startup evaluation by the TIDES platform. TRL 1 represents basic principles observed; TRL 9 represents proven deployment in operational environments. The complete framework is defined in [04_TRL_Assessment_Standard.md](./04_TRL_Assessment_Standard.md).

**Transparency**  
The principle that every aspect of an evaluation — data used, agents involved, scores produced, confidence levels, evidence cited, and human overrides applied — is logged, inspectable, and auditable by authorised stakeholders. Defined in [02_Evaluation_Principles.md](./02_Evaluation_Principles.md).

---

## U

**Unit Economics**  
The revenue and cost model at the level of a single unit of business activity — typically a single customer or transaction. Key unit economics metrics include CAC, LTV, gross margin, and payback period. Strong unit economics is a primary green flag in the Financial pillar.

---

## V

**Validation**  
The process of verifying, through defined activities and with defined parties, that a technology, product, or business assumption performs as claimed. Different types of validation carry different evidential weight: internal testing < external testing < independent lab validation < regulatory approval < commercial customer payment.

**Version (TAES)**  
TAES follows semantic versioning. v1.0.0 is the initial release. Minor versions (1.1, 1.2) add new content without changing existing standards. Major versions (2.0) may introduce breaking changes to evaluation methodology and must be applied to all new evaluations from the effective date.

---

## W

**Weight**  
The relative importance assigned to an evaluation pillar in calculating the overall startup score. Weights are expressed as percentages that sum to 100. In TAES v1.0, weights are configurable at the organisation, cohort, and sector level. No weight is hardcoded. Weights may be adjusted by evaluation committee decisions and must be recorded when changed. Defined in [05_Scoring_Standard.md](./05_Scoring_Standard.md).

---

*This glossary is a living document. New terms must be added as new features, modules, and evaluation dimensions are introduced. All team members are responsible for flagging undefined or ambiguous terms for inclusion in the next glossary update.*
