> **Document:** TAES v1.0 / Sector Normalization Standard
> **Classification:** Internal Technical Standard
> **Version:** 1.0.0
> **Maintained By:** TIDES Evaluation Engine Working Group
> **Effective Date:** 2026-06-23
> **Review Cycle:** Annual or upon major framework revision
> **Document ID:** TAES-v1.0-006

---

# TAES v1.0 — Sector Normalization Standard

## Table of Contents

1. [Introduction](#1-introduction)
   - 1.1 [Why Sector Normalization Is Essential, Not Optional](#11-why-sector-normalization-is-essential-not-optional)
   - 1.2 [Structural Differences Between Sector Maturity Cycles](#12-structural-differences-between-sector-maturity-cycles)
   - 1.3 [How Normalization Affects Evaluation Parameters](#13-how-normalization-affects-evaluation-parameters)
   - 1.4 [The Risk of Non-Normalized Evaluation](#14-the-risk-of-non-normalized-evaluation)
   - 1.5 [Technical Application of Sector Normalization](#15-technical-application-of-sector-normalization)

2. [Sector Profiles](#2-sector-profiles)
   - 2.1 [AI / Machine Learning](#21-ai--machine-learning)
   - 2.2 [SaaS / Enterprise Software](#22-saas--enterprise-software)
   - 2.3 [DeepTech (Hardware-Intensive, Non-Biotech)](#23-deeptech-hardware-intensive-non-biotech)
   - 2.4 [Biotech](#24-biotech)
   - 2.5 [MedTech](#25-medtech)
   - 2.6 [SpaceTech](#26-spacetech)
   - 2.7 [Defence / DualUse Tech](#27-defence--dualuse-tech)
   - 2.8 [AgriTech](#28-agritech)
   - 2.9 [ClimateTech / CleanTech](#29-climatetech--cleantech)
   - 2.10 [FinTech](#210-fintech)
   - 2.11 [Manufacturing / Industry 4.0](#211-manufacturing--industry-40)
   - 2.12 [Consumer Tech](#212-consumer-tech)
   - 2.13 [D2C (Direct-to-Consumer)](#213-d2c-direct-to-consumer)

3. [Cross-Sector Evaluation](#3-cross-sector-evaluation)

4. [Sector Classification Methodology](#4-sector-classification-methodology)

5. [Sector Normalization Configuration Model](#5-sector-normalization-configuration-model)

---

## 1. Introduction

### 1.1 Why Sector Normalization Is Essential, Not Optional

The TIDES AI Evaluation Standard (TAES) operates across a diverse portfolio of startup sectors — from pharmaceutical discovery pipelines to direct-to-consumer apparel brands. These sectors differ not merely in their subject matter but in their foundational economic logic, capital structures, regulatory environments, time-to-revenue profiles, intellectual property frameworks, and technology readiness expectations. Applying a single, undifferentiated evaluation rubric to all of them is not a simplification — it is an error that systematically disadvantages sectors with longer development horizons and rewards sectors with fast commercialization cycles, regardless of underlying innovation quality.

Sector normalization is the process of adjusting evaluation parameters — including scoring weights, benchmarks, TRL expectations, revenue milestones, and validation timelines — to reflect the intrinsic structural realities of a given sector. It is a calibration mechanism, not a favoritism mechanism. A Biotech startup at TRL 4 is not being graded on a curve; it is being graded against the correct standard for what TRL 4 means within a pharmaceutical discovery context, where TRL 4 may represent years of laboratory work and hundreds of thousands of dollars in validated research investment.

Without sector normalization, every evaluation becomes implicitly biased toward the sector for which the default metrics were designed. In most general-purpose incubator and VC evaluation frameworks, that default sector is effectively SaaS or Consumer Tech — sectors with short feedback loops, low capital intensity, and early revenue signals. Any startup that does not fit this profile is penalized not for being weak but for being different.

TAES mandates sector normalization as a required, non-negotiable configuration step that must be completed before any scored evaluation is generated. A sector-agnostic evaluation output from the TAES engine is considered incomplete and must not be used for funding, admission, or ranking decisions.

### 1.2 Structural Differences Between Sector Maturity Cycles

The concept of a "startup maturity cycle" refers to the sequence of development phases a company passes through from ideation to commercial scale. While these phases are universal — ideation, research, prototyping, validation, early traction, scale — the duration, capital intensity, regulatory checkpoints, and market-entry conditions at each phase vary dramatically across sectors. The table below illustrates the structural range:

| Dimension | D2C / Consumer Tech | SaaS | DeepTech | Biotech | SpaceTech |
|---|---|---|---|---|---|
| Time to First Revenue | 3–9 months | 6–18 months | 2–5 years | 7–15 years | 5–12 years |
| Capital to First Revenue | $50K–$500K | $100K–$2M | $2M–$20M | $20M–$200M | $50M–$500M |
| Regulatory Checkpoint | None or light | GDPR/data compliance | Patent, safety | IND, Phase I/II/III | FAA/ISRO/ESA licensing |
| IP Structure | Brand, trademark | Trade secret, SaaS terms | Patents, trade secrets | Patents, exclusivity periods | Patents, dual-use controls |
| Primary Validation Signal | Sales, retention | ARR, churn, NPS | Working prototype, pilot | Clinical trial data | Payload delivery, orbit test |
| First Market Entry Model | Direct consumer | Freemium/enterprise | System integrator | Pharma licensing | Government contract |
| Typical First Institutional Raise | Pre-seed, $250K–$1M | Seed, $500K–$3M | Seed–Series A, $2M–$10M | Series A–B, $10M–$50M | Series A–B, $20M–$100M |

These are not minor differences. They represent fundamentally different business models, risk profiles, and capital strategies. An evaluation framework that treats all of these as equivalent is not neutral — it is wrong.

Sector maturity cycles also interact with macroeconomic cycles differently. D2C startups are highly sensitive to consumer confidence and logistics costs. Biotech startups are sensitive to FDA policy, patent cliffs, and Big Pharma acquisition appetite. SpaceTech is sensitive to government space policy and launch vehicle availability. These external dependencies must be accounted for when interpreting a startup's current stage relative to its peers.

### 1.3 How Normalization Affects Evaluation Parameters

Sector normalization within TAES affects four primary categories of evaluation parameters:

**1. Scoring Weights (Pillar Weights)**
TAES evaluates startups across multiple pillars: Technology, Market, Team, Traction, Financial Health, Regulatory Readiness, and Innovation. In a SaaS evaluation, Traction (measured by ARR, MRR growth, churn) carries high weight because evidence of market adoption is available early and is highly predictive. In a Biotech evaluation, Traction carries minimal weight — it is structurally impossible to have commercial traction before clinical trials conclude, and penalizing for its absence provides no useful information. Instead, the Technology and Regulatory pillars carry significantly higher weight.

Normalization adjusts the relative importance of each pillar to match the information that is actually meaningful and available at the startup's sector-stage intersection.

**2. TRL Expectations**
Technology Readiness Levels (TRL 1–9) are used uniformly across TAES but their meaning and typical range at application varies by sector. A SaaS startup applying to an accelerator at TRL 7 (system prototype demonstration in operational environment) is not unusual. A SpaceTech startup at TRL 7 at application to an early incubator would be exceptional. Sector normalization sets the expected TRL range for "strong," "adequate," and "weak" performance in each sector, preventing misclassification.

**3. Lifecycle Stage Expectations**
TAES recognizes five lifecycle stages: Ideation, Pre-Product, MVP/Prototype, Early Traction, and Growth. The stage at which it is appropriate for a startup to apply to a given program, and the stage at which commercial metrics should be expected, varies by sector. Normalizing lifecycle stage expectations ensures that a Biotech startup at Ideation stage is not penalized for lacking a product when it has a validated scientific hypothesis and a strong IP filing strategy — both of which are the appropriate deliverables for that stage in that sector.

**4. Financial Metrics**
Financial benchmarks — burn rate, runway, revenue, margin, ARR — must be interpreted in sector context. A $500K monthly burn rate is alarming for a two-person SaaS startup and completely ordinary for a 20-person MedTech startup running clinical device trials. Sector normalization sets the benchmark ranges within which financial metrics are interpreted as healthy, concerning, or critical, rather than applying a single universal scale.

### 1.4 The Risk of Non-Normalized Evaluation

To illustrate the systemic risk of non-normalized evaluation, consider a concrete scenario: a DeepTech startup developing a novel solid-state battery chemistry is evaluated using the same metrics as a D2C skincare brand.

The DeepTech startup has:
- No revenue (expected; it has been operating for 18 months in a university spin-out)
- TRL 4 (validated in lab environment)
- Two patents filed
- A team of four PhD-level researchers
- A $1.2M seed round
- A 12-month pilot MOU with an automotive OEM

The D2C skincare brand has:
- ₹40 lakhs in monthly revenue
- 3,200 active customers
- 68% gross margin
- D2C website, active Instagram presence, repeat purchase rate of 31%

Under a non-normalized evaluation, the D2C brand scores dramatically higher on Traction, Financial Health, and Market Validation — not because it is a more fundable or more innovative business, but because those metrics happen to apply to its business model. The DeepTech startup is penalized for being in a sector where those metrics are structurally inapplicable at its stage.

The consequences of this error include:

- **Systematic exclusion of high-innovation, long-horizon startups** from incubation and funding pipelines
- **Portfolio concentration risk** as programs inadvertently select for low-capital, fast-return models
- **Misallocation of national R&D investment** when government-backed evaluators use non-normalized frameworks
- **Reputational damage** to evaluation programs that are later found to have rejected scientifically excellent applications based on inapplicable financial criteria
- **Loss of deep-tech and strategic-sector founders** to international programs that correctly evaluate their work

The inverse error is equally dangerous: a D2C startup being admitted to a deep-tech incubator because it was evaluated on technology readiness criteria it cannot meet, leading to a mismatch between program resources and startup needs.

Non-normalized evaluation is not a minor inefficiency. It is a structural failure mode of the evaluation system.

### 1.5 Technical Application of Sector Normalization

Within the TAES architecture, sector normalization is implemented as a **configuration layer**, not as a scoring bias or manual override. This distinction is critical to the integrity of the evaluation system.

**What this means:**
- The underlying evaluation engine, scoring algorithms, and pillar definitions remain identical across all sectors
- Sector normalization modifies the *input configuration* supplied to that engine: the weight vector, benchmark tables, TRL expectation ranges, and lifecycle stage maps
- No score is artificially inflated or deflated based on sector membership
- Two startups from the same sector with the same characteristics will receive the same score
- The normalization ensures that the evaluation criteria themselves are appropriate for the sector, not that the sector gets preferential treatment

**Runtime implementation:**
At the start of each evaluation session, the TAES engine reads the `sector_id` from the startup's structured profile. It then loads the corresponding sector configuration file from the normalization registry. This configuration file specifies:

1. `pillar_weights`: a weight vector across all evaluation pillars
2. `trl_benchmarks`: expected TRL ranges for each lifecycle stage in this sector
3. `financial_benchmarks`: sector-appropriate ranges for burn, revenue, margin, and runway
4. `validation_timeline`: expected time ranges for each validation phase
5. `lifecycle_expectations`: which lifecycle stages are expected at which program types
6. `regulatory_flags`: known regulatory requirements that must be checked
7. `red_flags`: sector-specific disqualifying conditions

These configuration values are version-controlled, peer-reviewed by domain experts, and updated on an annual review cycle. They are not editable by individual evaluators. This ensures that normalization is systematic, auditable, and reproducible.

**Audit trail:**
Every evaluation output includes a `normalization_applied` field in its metadata, recording the sector configuration version used. This enables retrospective analysis of how normalization parameters affected scoring distributions across program cohorts.

---

## 2. Sector Profiles

---

### 2.1 AI / Machine Learning

#### 2.1.1 Sector Overview

AI/ML startups develop products and services whose primary value proposition is derived from machine learning models, predictive analytics, natural language processing, computer vision, or other algorithmic intelligence capabilities. This sector encompasses a wide range of business models: AI-native SaaS platforms, vertical AI applications (AI for legal, AI for healthcare), AI infrastructure and tooling, foundational model providers, data labeling and annotation services, MLOps platforms, and AI-powered automation solutions.

The sector is characterized by rapid capability evolution (model performance benchmarks shift quarterly), high data dependency, and a wide spectrum of technical depth — from thin wrappers on foundation model APIs to proprietary, deeply trained domain-specific models. Evaluators must distinguish between these ends of the spectrum, as they represent fundamentally different risk and value profiles.

Key characteristics of the sector:
- Strong reliance on proprietary or licensed training data as a competitive moat
- Model performance is often the primary technical differentiator, but is difficult to evaluate without benchmarking
- The commoditization risk is high: open-source models and API providers rapidly close performance gaps
- Switching costs depend heavily on the depth of integration and the uniqueness of the model
- Many AI startups operate as horizontal platforms seeking vertical deployment, creating GTM complexity
- Compute cost is a significant and often underestimated operational expense that directly affects unit economics

#### 2.1.2 Expected Maturity at Application

At incubator or seed-stage application, AI/ML startups are typically at the **MVP/Prototype to Early Traction** lifecycle stage. Given the relatively low capital cost of building an initial AI model (compared to hardware sectors), the field has a fast iteration cycle. Evaluators should expect:

- **Incubator application (pre-seed):** A working proof-of-concept model with preliminary benchmark results, a defined use case, and at minimum 1–2 pilot discussions or letters of intent.
- **Seed-stage application:** A deployed or deployable model, at least 1–3 paying customers or active pilots generating usage data, and evidence of model improvement over a documented baseline.
- **Series A application:** Demonstrated product-market fit, measurable model performance improvements tied to customer outcomes, and ARR of at least $250K–$1M depending on the vertical.

Founders in this sector often come from research backgrounds (academia, Big Tech AI labs), and the presence of strong technical credentials in the team compensates partially for limited commercial traction at early stages.

#### 2.1.3 Expected Financial Profile

| Stage | Monthly Burn | Expected Revenue | Key Financial Indicators |
|---|---|---|---|
| Ideation / Pre-product | $5K–$30K | None | F&F funding or research grant; minimal overhead |
| MVP / Prototype | $20K–$80K | $0–$10K MRR (pilot contracts) | Compute costs emerging as major line item |
| Early Traction | $50K–$200K | $10K–$100K MRR | Gross margin 50–80%; compute vs. revenue ratio is critical |
| Growth | $150K–$500K+ | $100K+ MRR | Net revenue retention >100% target; CAC payback <18 months |

A critically important financial metric for AI startups is the **compute-to-revenue ratio** — the proportion of revenue consumed by cloud compute and inference costs. Startups where this ratio exceeds 30–40% are in a structurally vulnerable position unless they have a clear path to model efficiency gains or dedicated hardware investment. This metric should be explicitly tracked in TAES financial evaluation for this sector.

Revenue at early stages may take the form of paid pilots, consulting engagements with model delivery, or per-seat SaaS subscriptions. Pure model API revenue is an acceptable early-stage model but requires clear differentiation from commodity API providers.

#### 2.1.4 Expected Validation Cycle

AI/ML startups have relatively short technical validation cycles compared to hardware or regulated sectors, but have a nuanced commercial validation process:

| Validation Phase | Typical Duration | Validation Milestone |
|---|---|---|
| Model proof-of-concept | 1–4 months | Benchmark performance against baseline (rule-based system or incumbent) |
| Pilot deployment | 2–6 months | Integration with customer environment; initial usage data |
| Production validation | 3–9 months | Customer outcome data; model in active use on live data |
| Market validation | 6–18 months | Repeat customers, renewals, expansion revenue, NPS |

A key validation challenge specific to AI is the gap between model performance metrics (accuracy, F1, AUC-ROC) and business outcome metrics (reduction in error rate, time saved, revenue generated). Strong AI startups can articulate how the former drives the latter. Evaluators should be skeptical of teams that can only speak to model performance without connecting it to measurable customer outcomes.

#### 2.1.5 Expected TRL Range

| TRL | Description | Expected for AI/ML at Stage |
|---|---|---|
| TRL 3 | Proof of concept, lab validated | Acceptable at ideation/pre-product for incubator entry |
| TRL 4 | Component validation in lab | Minimum expected for seed-stage application |
| TRL 5 | Component validation in relevant environment | Expected for seed-stage with strong team |
| TRL 6 | System prototype in relevant environment | Expected for Series A readiness |
| TRL 7 | System prototype in operational environment | Strong for pre-Series A; required for enterprise pilots |
| TRL 8 | System complete and qualified | Expected at Series A and beyond |
| TRL 9 | Proven in operational environment | Series B+ |

**Strong indicator for early stage:** TRL 5–6 with a documented pilot deployment and at least one customer generating outcome data.

#### 2.1.6 Weight Adjustments

| Evaluation Pillar | Directive | Rationale |
|---|---|---|
| Technology / IP | **Increase weight** | Model architecture, training data provenance, and performance differentiation are the primary moat; must be assessed rigorously |
| Team | **Increase weight** | AI/ML requires specialized expertise that is scarce; team quality is highly predictive of execution capability |
| Market | **Standard weight** | Market size is important but sector has demonstrated tendency toward overstatement; apply structured skepticism |
| Traction | **Moderate weight** | Early traction exists and is meaningful, but should not dominate scoring at pre-seed/seed stage |
| Financial Health | **Reduce weight** | AI startups may have strong unit economics in construction even with low early revenue |
| Regulatory | **Context-dependent** | High weight if the AI application is in healthcare, finance, or government; standard weight for horizontal tooling |

#### 2.1.7 Evaluation Considerations

1. **Data moat assessment:** Evaluators must determine whether the startup has access to proprietary training data that competitors cannot easily replicate. A model trained on publicly available data provides a weak moat and is at high risk of commoditization.

2. **Foundation model dependency risk:** Many AI startups are built on top of OpenAI, Anthropic, Google, or Meta foundation models. The evaluator must assess what happens to the startup's value proposition if the underlying API provider changes pricing, terms, or releases a competing product.

3. **Model explainability in regulated contexts:** If the AI is used in hiring, lending, healthcare, or government decisions, explainability and bias auditing are not optional. The startup must demonstrate awareness and a compliance roadmap.

4. **Benchmark gaming:** AI teams from academic backgrounds often present model performance metrics that are technically accurate but practically misleading (evaluated on curated test sets, not real-world distributions). Evaluators should ask for performance data from live deployments, not only benchmark datasets.

5. **Compute scaling economics:** Evaluators should model what happens to gross margin as usage scales. For startups relying on third-party LLM APIs, inference cost grows linearly with usage. The startup must articulate either a path to fine-tuned smaller models, on-premise deployment, or negotiated compute contracts.

6. **Vertical vs. horizontal positioning:** Horizontal AI platforms (AI for everyone) face intense competition from well-funded incumbents. Evaluators should assess whether the startup has a defensible vertical focus with deep domain expertise.

7. **AI governance posture:** As regulatory frameworks like the EU AI Act mature, startups without an AI governance posture (risk classification, human oversight mechanisms, model versioning) face compliance liability. This is increasingly relevant even at early stages.

#### 2.1.8 Common Evaluation Errors

1. **Treating benchmark performance as a proxy for market readiness.** A model with 94% accuracy on a benchmark dataset is not a validated product. Evaluators routinely over-score AI startups based on technical metrics that have not been validated in customer environments.

2. **Ignoring compute cost in financial projections.** Many AI startups present revenue projections without modeling the compute cost associated with serving those revenues. Evaluators who do not probe this produce inaccurate financial assessments.

3. **Failing to distinguish between AI-native and AI-enhanced businesses.** An incumbent SaaS product that added an AI feature is not an AI startup. Evaluators sometimes classify AI-enhanced businesses as AI-native and apply inappropriate high-technology scoring.

4. **Underweighting the data acquisition strategy.** The long-term success of an AI product depends more on data acquisition pipelines than on model architecture. Evaluators who focus on the model without assessing the data strategy miss the primary value driver.

5. **Overweighting academic credentials at the expense of deployment experience.** A team of PhD researchers who have never deployed a production system presents significant execution risk that is underweighted when evaluators are impressed by institutional affiliations.

---

### 2.2 SaaS / Enterprise Software

#### 2.2.1 Sector Overview

Software as a Service (SaaS) and enterprise software startups deliver software products on a subscription basis, hosted on cloud infrastructure and accessed via web or API interfaces. This sector includes horizontal SaaS platforms (project management, CRM, HR, finance), vertical SaaS (industry-specific workflow management), developer tools and infrastructure, API-first products, and enterprise software sold through multi-year contracts.

SaaS is arguably the best-understood sector in the modern startup ecosystem. Its metrics are well-defined, benchmarks are widely published, and investor expectations are codified. The key characteristics of the sector are:

- Recurring revenue model (MRR/ARR) creates predictable cash flows
- Gross margins are structurally high (70–90%) due to low marginal cost of serving additional users
- Customer acquisition cost (CAC) and lifetime value (LTV) are the primary unit economics framework
- Enterprise SaaS has long sales cycles (3–12 months) but high contract values and low churn
- SMB SaaS has short sales cycles but higher churn and lower ACV
- Network effects can create strong moats in collaboration tools and marketplace-adjacent products

#### 2.2.2 Expected Maturity at Application

SaaS startups are expected to have progressed further at application than most other sectors, because the tools and infrastructure for building SaaS products are widely available and cheap.

- **Incubator application:** MVP deployed, at minimum 2–5 pilot or beta users providing structured feedback, clear articulation of ICP (Ideal Customer Profile)
- **Seed stage:** Product in production, 5–20 paying customers, $5K–$50K MRR, defined sales motion
- **Series A:** $1M–$3M ARR, defined GTM, monthly churn below 2% (SMB) or annual churn below 10% (enterprise), documented CAC and LTV

At pre-seed and seed stages, evaluators should expect and require a deployed product. The absence of a production-ready MVP at seed stage in SaaS is a significant negative signal, unlike in capital-intensive sectors where pre-product fundraising is normal.

#### 2.2.3 Expected Financial Profile

| Stage | Monthly Burn | MRR / ARR | Gross Margin | Key Metrics |
|---|---|---|---|---|
| Pre-seed | $10K–$40K | $0–$5K MRR | N/A | Pilot agreements, early LOIs |
| Seed | $30K–$150K | $5K–$100K MRR | 60–80% | CAC, LTV, churn rate |
| Series A | $150K–$500K | $1M–$5M ARR | 70–85% | Net Revenue Retention, CAC payback |
| Series B | $500K–$2M+ | $5M–$20M+ ARR | 75–90% | Rule of 40, NRR >120% |

**Critical metric — Rule of 40:** At Series A and beyond, the sum of ARR growth rate (%) and EBITDA margin (%) should equal or exceed 40. This is the primary health indicator for scaling SaaS businesses.

**Net Revenue Retention (NRR):** The single most important SaaS metric at growth stages. NRR >100% means existing customers are expanding their subscriptions faster than churn, enabling growth without new customer acquisition. NRR >120% is world-class. NRR <80% indicates severe product-market fit issues.

#### 2.2.4 Expected Validation Cycle

| Validation Phase | Duration | Milestone |
|---|---|---|
| Problem-solution fit | 1–3 months | Customer interviews, willingness-to-pay evidence |
| MVP development | 1–4 months | Deployed MVP with beta users |
| Product-market fit | 3–12 months | Paying customers with low churn, organic referrals |
| GTM validation | 6–18 months | Repeatable, scalable sales motion; documented CAC |

SaaS validation cycles are the shortest of any sector considered in this standard. This is a feature, not a flaw — it allows rapid iteration and learning. Evaluators should apply higher standards for what counts as "validated" in this sector because the tools for validation are cheap and fast.

#### 2.2.5 Expected TRL Range

| TRL | Description | Expected for SaaS at Stage |
|---|---|---|
| TRL 5 | Validated in relevant environment | Minimum for incubator consideration |
| TRL 6 | System prototype in relevant environment | Expected at seed stage |
| TRL 7 | System prototype in operational environment | Strong signal; indicates real customer usage |
| TRL 8 | System complete and qualified | Expected at Series A |
| TRL 9 | Proven in operational environment | Expected at Series B |

TRL 1–4 is inappropriate for most SaaS programs. If a SaaS startup is below TRL 5, the issue is not technology readiness but market validation and execution.

#### 2.2.6 Weight Adjustments

| Evaluation Pillar | Directive | Rationale |
|---|---|---|
| Traction | **Increase weight significantly** | Quantitative traction metrics are available, meaningful, and highly predictive in SaaS |
| Financial Health | **Increase weight** | SaaS financial metrics (ARR, NRR, CAC payback) are well-defined and directly predictive of fundability |
| Market | **Standard weight** | TAM/SAM/SOM analysis is important but must be grounded in ICP definition, not macro-market sizing |
| Technology / IP | **Reduce weight** | Most SaaS technology is not patentable; moat comes from GTM, network effects, and data |
| Team | **Standard weight** | Execution capability matters but domain expertise less critical than in deep-tech |
| Regulatory | **Reduce weight (unless vertical-specific)** | Most horizontal SaaS operates with minimal regulatory burden |

#### 2.2.7 Evaluation Considerations

1. **ICP definition quality:** Startups that have a precisely defined Ideal Customer Profile (company size, industry, pain point, decision-maker role) are significantly more likely to build repeatable sales motions than those targeting a vague horizontal market.

2. **Enterprise vs. SMB motion:** These are fundamentally different businesses with different burn profiles, sales cycles, and churn dynamics. Evaluators must assess whether the startup has selected a motion and built the team and product for it.

3. **Build vs. buy competitive landscape:** Evaluators must probe whether the target customer could reasonably build an equivalent internal tool. This is particularly relevant for developer-facing SaaS and workflow automation tools.

4. **Integration ecosystem:** Enterprise SaaS products that integrate deeply with existing tools (Salesforce, Slack, SAP, Workday) have higher switching costs and are more competitive. Evaluators should assess integration strategy.

5. **Pricing model alignment:** Many SaaS startups underprice early contracts to acquire customers, then struggle with price elasticity as they try to increase rates. Evaluators should assess whether pricing is sustainable and consistent with value delivered.

6. **Multi-year contract vs. month-to-month:** For enterprise SaaS, the proportion of ARR under multi-year contracts is a significant risk indicator. Monthly contracts from enterprise customers indicate low commitment and high churn risk.

7. **Support and implementation cost:** Some enterprise SaaS products have high implementation costs (integration, training, data migration) that reduce net margins and create customer success bottlenecks at scale.

#### 2.2.8 Common Evaluation Errors

1. **Accepting MRR without probing quality.** Not all MRR is equal. Evaluators frequently accept MRR figures without asking what proportion is from pilot/trial agreements, whether contracts have cancellation clauses, and what the effective churn is.

2. **Confusing large TAM with addressable market.** SaaS startups frequently cite trillion-dollar market sizes that bear no relationship to their actual ICP. Evaluators must require bottoms-up TAM analysis based on customer count and ACV.

3. **Overweighting technical differentiation.** Most SaaS products are not technically differentiated. Their moats come from GTM strategy, customer success, and data network effects. Evaluators who score heavily on technical novelty misallocate scores in this sector.

4. **Ignoring enterprise sales cycle length in financial projections.** Startups targeting enterprise clients with 6–12 month sales cycles often have optimistic revenue projections that assume deals close in 2–3 months. Evaluators who do not probe pipeline velocity produce inaccurate financial assessments.

---

### 2.3 DeepTech (Hardware-Intensive, Non-Biotech)

#### 2.3.1 Sector Overview

DeepTech hardware-intensive startups develop products based on fundamental scientific or engineering innovations that require significant physical R&D investment, specialized manufacturing processes, and long development timelines before market entry. This sector encompasses: semiconductor design and fabrication, advanced materials, quantum computing hardware, photonics, solid-state energy storage, robotics systems, industrial sensing and actuation, novel computing architectures, and precision engineering components.

The sector is characterized by:
- Capital intensity significantly higher than software sectors at all stages
- Long time-to-market (3–8 years from founding to first commercial deployment)
- Strong IP position as a primary moat (patents, trade secrets, manufacturing know-how)
- Dependency on specialized manufacturing infrastructure (cleanrooms, foundries, specialized testing equipment)
- Often requires government or strategic industrial partners to reach commercialization
- Team composition typically includes PhD-level researchers and engineers with very specialized domain expertise
- Supply chain dependencies that are non-trivial to establish and manage

#### 2.3.2 Expected Maturity at Application

DeepTech startups require longer runways before they can demonstrate commercial readiness. Evaluators must recalibrate their expectations accordingly:

- **Incubator application:** A working laboratory prototype demonstrating the core technical innovation, with foundational IP filed or in process, and a team with demonstrable domain expertise
- **Seed stage:** TRL 4–5, laboratory-validated performance data, IP protection in place, pilot partnership discussions with industrial players
- **Series A:** TRL 5–7, working prototype in relevant operational environment, at least one strategic partnership or pilot agreement signed, manufacturing pathway identified
- **Series B:** TRL 7–8, pilot manufacturing, initial commercial deployments or purchase orders from anchor customers

The absence of revenue at seed stage in DeepTech is normal and expected. Evaluators who require revenue evidence at this stage are applying the wrong framework.

#### 2.3.3 Expected Financial Profile

| Stage | Monthly Burn | Expected Revenue | Key Financial Indicators |
|---|---|---|---|
| Ideation | $20K–$80K | None | Research grant, university TTO funding |
| Seed | $80K–$300K | None to negligible | Grant + equity funding mix; IP portfolio development |
| Series A | $200K–$800K | $0–$500K (pilot contracts or government grants) | Burn relative to technical milestone progress |
| Series B | $500K–$3M | $500K–$5M (early commercial contracts) | Path to manufacturing scale economics |

Revenue benchmarks for DeepTech at early stages are completely different from software sectors. The correct financial health indicator is not revenue but **milestone efficiency** — the ability to achieve technical milestones on budget and on schedule. Grant funding (SBIR, DST, DRDO, BIRAC, EU Horizon) is a positive signal, as it represents independent technical validation.

Capital structure also differs: DeepTech startups typically have a higher proportion of non-dilutive grant funding, which is a strength, not a weakness.

#### 2.3.4 Expected Validation Cycle

| Validation Phase | Duration | Milestone |
|---|---|---|
| Lab proof of concept | 6–18 months | Laboratory demonstration of core physics/chemistry/material |
| Sub-system integration | 12–24 months | Integrated components working under controlled conditions |
| Prototype in relevant environment | 18–36 months | Performance data in conditions approaching real deployment |
| Pilot manufacturing | 24–48 months | Small-batch production capability; yield and cost data |
| Commercial deployment | 36–72 months | First anchor customer deployment; field performance data |

These timelines are not negotiable and cannot be accelerated by funding alone. They reflect the physical reality of developing new materials, devices, or systems. Evaluators must treat these timelines as constraints, not as evidence of slow execution.

#### 2.3.5 Expected TRL Range

| TRL | Description | Expected for DeepTech at Stage |
|---|---|---|
| TRL 2 | Technology concept formulated | Acceptable for incubator entry with strong team and IP |
| TRL 3 | Proof of concept | Strong for incubator entry |
| TRL 4 | Component validated in lab | Minimum for seed-stage funding |
| TRL 5 | Component validated in relevant environment | Strong for seed-stage |
| TRL 6 | System prototype in relevant environment | Milestone for Series A |
| TRL 7 | System prototype in operational environment | Strong for Series A/B |
| TRL 8 | System complete and qualified | Series B milestone |
| TRL 9 | Proven in operational environment | Commercial scale |

**Important note:** TRL 3–4 in DeepTech may represent 2–4 years of intense research and $2–5M of investment. Evaluators must not interpret low TRL as lack of progress — they must evaluate TRL relative to time and capital invested.

#### 2.3.6 Weight Adjustments

| Evaluation Pillar | Directive | Rationale |
|---|---|---|
| Technology / IP | **Increase weight significantly** | The patent portfolio, trade secrets, and manufacturing know-how are the primary value drivers |
| Team | **Increase weight** | Deep domain expertise is rare and irreplaceable; team quality is the single most predictive factor |
| Traction | **Reduce weight significantly** | Commercial traction is structurally unavailable at early stages; its absence carries no informational value |
| Financial Health | **Reduce weight** | Standard financial metrics are inapplicable; replace with milestone efficiency assessment |
| Market | **Increase weight moderately** | Addressable market and customer adoption pathway need to be realistic for large-capital-requirement products |
| Regulatory | **Increase weight moderately** | Patent landscape, export control compliance, and manufacturing safety approvals are critical |

#### 2.3.7 Evaluation Considerations

1. **Manufacturing pathway realism:** A brilliant laboratory prototype is worthless without a credible path to manufacturable product. Evaluators must probe the team's understanding of manufacturing scale, yield rates, cost of goods, and supply chain.

2. **IP freedom-to-operate analysis:** DeepTech startups often operate in dense patent landscapes. A startup with a strong invention but no freedom-to-operate analysis may face licensing costs or injunctions that destroy the business model.

3. **Foundry and fabrication dependencies:** Semiconductor, photonics, and materials startups are often dependent on external foundries or specialized fabrication partners. The availability, cost, and exclusivity of these relationships are critical risk factors.

4. **Government funding ecosystem:** In India, DRDO, DST, BIRAC, ISRO, and Ministry of Electronics have active grant programs for DeepTech. A startup that has not explored these has a gap in its funding strategy. In global contexts, SBIR (US), EU Horizon, and Innovate UK are analogous.

5. **University TTO relationship:** Many DeepTech startups are university spin-outs with complex IP licensing arrangements with their parent institutions. Evaluators must assess whether the IP is cleanly licensed, who retains what rights, and whether the licensing terms allow commercial exploitation.

6. **Team-technology lock-in:** A startup where the core IP is entirely embodied in one or two technical founders who remain at the university or have not committed full-time presents serious execution risk.

7. **Customer validation vs. technology validation:** DeepTech customers (industrial OEMs, defense prime contractors, energy companies) typically conduct their own extensive due diligence before signing pilot agreements. An MOU or LOI from a credible industrial partner is a significantly stronger signal than a customer letter from a startup-friendly early adopter.

#### 2.3.8 Common Evaluation Errors

1. **Applying revenue expectations from software sectors.** The single most common error. A DeepTech startup at seed stage with no revenue is completely normal and should not be penalized on financial metrics.

2. **Treating low TRL as evidence of insufficient progress.** TRL must be evaluated relative to time, capital invested, and sector norms. TRL 4 after 18 months and $1.5M in a semiconductor startup is good progress. Evaluators who compare this to SaaS TRL 8 at the same stage are making a category error.

3. **Underweighting patent landscape risk.** Evaluators who take the IP section at face value without probing freedom-to-operate, claim breadth, and prosecution status miss critical liability.

4. **Overweighting the lab demonstration.** A technology that works in a university lab may face profound challenges at manufacturing scale due to yield, cost, material purity, or environmental sensitivity. The lab demo is necessary but not sufficient.

5. **Ignoring manufacturing cost of goods.** Even a technically successful DeepTech product can fail commercially if the bill of materials cost is too high to support a viable customer price point. Evaluators must probe cost of goods projections even at early stages.

---

### 2.4 Biotech

#### 2.4.1 Sector Overview

Biotech startups develop products and services based on biological systems, living organisms, or their derivatives for applications in human health, agriculture, industrial processes, or environmental remediation. Within TAES, the Biotech sector is specifically focused on life sciences applications excluding medical devices (covered under MedTech): drug discovery, biopharmaceuticals, gene therapy, cell therapy, synthetic biology, diagnostics platforms, genomics, microbiome therapeutics, and biologics manufacturing.

Key characteristics:
- Extremely long development timelines: 10–15 years from discovery to market for novel drugs
- Regulatory pathway is the central organizing principle of the entire business strategy (FDA, EMA, CDSCO)
- Intellectual property (composition of matter patents, method patents) provides time-bounded exclusivity windows
- The primary exit path for early-stage Biotech is acquisition by or licensing to a large pharmaceutical company — not standalone IPO
- Clinical trial design is a core competency as important as the underlying science
- Failure rates are very high: approximately 90% of drugs entering Phase I trials never reach market approval

#### 2.4.2 Expected Maturity at Application

Biotech startups have the longest development timelines of any sector in this standard. Lifecycle stage expectations must be calibrated accordingly:

- **Incubator application:** A validated scientific hypothesis supported by peer-reviewed literature, preliminary in vitro or in silico data, a founding team with relevant domain expertise (PhD/MD level), and an IP filing strategy
- **Seed stage:** In vitro proof of concept, foundational IP filed, IND-enabling studies in progress, initial regulatory strategy articulated
- **Series A:** IND filing or approval, Phase I trial design finalized, sufficient cash to fund Phase I plus 12 months
- **Series B:** Phase I results, Phase II design, partnership or licensing discussions with pharma

It is entirely appropriate and expected for a Biotech startup to apply to an incubator with no product, no revenue, and no customers — only a scientific hypothesis, preliminary data, and a team qualified to pursue it.

#### 2.4.3 Expected Financial Profile

| Stage | Monthly Burn | Expected Revenue | Key Financial Indicators |
|---|---|---|---|
| Pre-seed / Incubator | $30K–$150K | None | Government research grants (BIRAC, NIH, Wellcome) |
| Seed | $100K–$400K | None | Grant + equity; IND-enabling study budget |
| Series A | $500K–$2M | None (or milestone payments from pharma partners) | Cash runway relative to Phase I completion |
| Series B | $1M–$5M | Possible: licensing upfront payments | Runway to Phase II readout |
| Series C+ | $3M–$20M+ | Possible milestone payments; no commercial revenue until approval | |

Biotech financial health is measured entirely by runway-to-next-milestone, not by revenue. An evaluator who penalizes a Biotech startup for zero revenue is applying an entirely inapplicable metric.

Non-dilutive funding sources are critically important: BIRAC (India), NIH SBIR (US), Wellcome Trust, ICMR, DBT grants represent genuine validation of scientific merit and are strong positive signals.

#### 2.4.4 Expected Validation Cycle

| Validation Phase | Duration | Milestone |
|---|---|---|
| Target identification | 6–18 months | Published or unpublished biological target validation data |
| Hit identification / Lead discovery | 12–24 months | Compound or molecule with demonstrated activity against target |
| Lead optimization | 12–24 months | Optimized candidate with ADMET profile |
| IND-enabling studies | 12–18 months | Toxicology, pharmacology, formulation; IND submission |
| Phase I clinical trial | 12–24 months | Safety, tolerability, PK/PD data in humans |
| Phase II clinical trial | 18–36 months | Proof of efficacy in patient population |
| Phase III clinical trial | 24–60 months | Large-scale efficacy and safety for registration |

Total timeline from discovery to approval for a novel small molecule: 10–15 years. For biologics and gene/cell therapies: potentially longer.

#### 2.4.5 Expected TRL Range

Biotech applies a modified TRL framework (often aligned with the Biotechnology-specific TRL scale used by EU Horizon programs):

| TRL | Description | Expected at Stage |
|---|---|---|
| TRL 1–2 | Basic principles observed; technology concept | Acceptable for incubator with strong team |
| TRL 3 | Proof of concept in vitro / in silico | Strong for incubator; minimum for early grant funding |
| TRL 4 | Proof of concept in animal models | Seed stage |
| TRL 5 | IND-enabling studies; regulatory preclinical package | Pre-Series A milestone |
| TRL 6 | Phase I clinical data | Series A milestone |
| TRL 7 | Phase II data | Series B milestone |
| TRL 8 | Phase III complete | Pre-IPO / large pharma licensing stage |
| TRL 9 | Regulatory approval, commercialization | Exit or post-IPO commercialization |

#### 2.4.6 Weight Adjustments

| Evaluation Pillar | Directive | Rationale |
|---|---|---|
| Technology / IP | **Increase weight significantly** | Composition of matter patents and scientific data package are the primary assets |
| Regulatory | **Increase weight significantly** | The regulatory pathway IS the business strategy; every decision flows from it |
| Team | **Increase weight** | Scientific and clinical expertise is rare and irreplaceable |
| Traction | **Remove from early-stage scoring** | Commercial traction is structurally impossible at pre-Phase II stages |
| Financial Health | **Replace with runway-to-milestone** | Standard financial health metrics are not applicable; replace with milestone budget adequacy |
| Market | **Moderate weight** | Market opportunity is relevant but must be calculated using epidemiology data, not general industry reports |

#### 2.4.7 Evaluation Considerations

1. **Scientific advisory board quality:** The Scientific Advisory Board (SAB) in a Biotech startup is not decorative. Evaluators must assess whether SAB members are domain experts (not general biotech advisors), have reviewed the data, and have committed to substantive ongoing involvement.

2. **IP composition and expiry:** Patents in Biotech are time-limited. A drug discovery startup whose core patents expire in 5 years faces a commercialization window problem unless they have supplementary or continuation patents. Evaluators must assess the effective patent life relative to the regulatory timeline.

3. **Regulatory strategy specificity:** Many Biotech startups say they will "engage with the FDA" without specifying a pathway. Evaluators must probe: Is this a 505(b)(2), new molecular entity (NME), or orphan drug designation pathway? What pre-IND meetings have been held? What is the primary endpoint strategy for Phase II?

4. **CMO/CDO relationships:** Contract Manufacturing Organizations and Contract Development Organizations are essential partners for clinical-stage Biotech. Evaluators should assess whether the startup has identified appropriate CMO/CDO partners for clinical supply manufacture and whether the agreements are in place or in negotiation.

5. **Animal model translatability:** Many drug candidates demonstrate strong activity in mouse models and fail in humans. Evaluators should probe the translatability of animal model data and whether any models closer to human physiology have been tested.

6. **Combination therapy risks:** If the therapeutic is intended as a combination with an existing approved drug, the regulatory pathway and IP landscape become significantly more complex. Evaluators should flag this scenario and assess whether it has been addressed.

7. **Exit strategy alignment with development stage:** A Biotech startup that plans to pursue a standalone IPO without Phase III data is pursuing a high-risk strategy. Most successful early-stage Biotech exits are through licensing or acquisition by Pharma. Evaluators should assess whether the exit strategy is realistic.

#### 2.4.8 Common Evaluation Errors

1. **Penalizing zero revenue at early stages.** This is the most disqualifying error. A Biotech startup at seed stage with peer-reviewed preclinical data, a filed patent, and a Phase I design is at the correct stage of development for that investment level. No revenue is expected or appropriate.

2. **Evaluating clinical trial design without domain expertise.** Phase I/II/III trial design is highly specialized. Generic evaluators who lack clinical trial expertise often accept inadequate primary endpoint choices or sample size calculations without challenge.

3. **Treating animal model data as clinical validation.** Animal data is hypothesis-supporting, not clinically validated. Evaluators who conflate the two overestimate a program's development stage.

4. **Ignoring the regulatory pathway document.** A Biotech startup that does not have a documented regulatory pathway strategy (even a 2-page summary) is not investment-ready. Evaluators who do not specifically probe this overlook a fundamental readiness indicator.

5. **Underweighting CMC (Chemistry, Manufacturing, and Controls) readiness.** The ability to manufacture the therapeutic at clinical-grade quality and quantity is a gating factor for IND filing. CMC readiness is frequently overlooked by evaluators focused on the science and ignored until it becomes a blocking issue.

---

### 2.5 MedTech

#### 2.5.1 Sector Overview

MedTech startups develop medical devices, diagnostic tools, digital health platforms, surgical instruments, implantable systems, and associated software (Software as a Medical Device — SaMD) intended for diagnosis, prevention, monitoring, or treatment of medical conditions. This sector is regulated by the FDA in the United States, CE marking under EU MDR in Europe, CDSCO under the Medical Devices Rules in India, and equivalent bodies in other jurisdictions.

Key characteristics of the sector:
- Device classification (Class I / II / III in FDA terminology) determines the regulatory burden and timeline
- Software as a Medical Device (SaMD) has its own regulatory framework that is evolving rapidly
- Clinical evidence requirements vary by device class but are always present for Class II and III
- Post-market surveillance and adverse event reporting create ongoing regulatory obligations
- Reimbursement pathway (CPT codes, insurance coverage, government scheme inclusion) is as important as regulatory approval for commercial success
- Hospital procurement cycles are long (6–18 months), driven by committee approvals, budget cycles, and clinical champion identification

#### 2.5.2 Expected Maturity at Application

- **Incubator / Pre-seed:** Device concept with preliminary bench testing, user need validation (clinician interviews), device classification assessment, and a team that includes clinical or regulatory expertise
- **Seed stage:** Working bench prototype, usability study data, ISO 13485 roadmap in place, regulatory pre-submission meeting held
- **Series A:** 510(k)-submitted or 510(k)-cleared (for Class II), or IDE-approved for Class III; initial clinical data; pilot hospital deployments
- **Series B:** Regulatory clearance, first commercial deployments, reimbursement pathway established or in progress

#### 2.5.3 Expected Financial Profile

| Stage | Monthly Burn | Expected Revenue | Key Indicators |
|---|---|---|---|
| Incubator / Pre-seed | $20K–$100K | None | Research grants, clinical validation partnerships |
| Seed | $80K–$300K | None to $20K (paid clinical pilots) | Regulatory milestone progress |
| Series A | $200K–$800K | $0–$500K (early commercial sales) | Gross margin on device; regulatory status |
| Series B | $500K–$2M | $500K–$5M ARR equivalent | Hospital penetration rate; reimbursement status |

MedTech devices often have complex revenue models: device sale plus disposables/consumables, SaaS subscription for accompanying software, or service contract models. Evaluators must understand the specific revenue model and its margin implications.

#### 2.5.4 Expected Validation Cycle

| Validation Phase | Duration | Milestone |
|---|---|---|
| Bench testing (V&V) | 6–18 months | Performance against technical specifications; biocompatibility |
| Usability and human factors | 3–9 months | Simulated use testing per IEC 62366 |
| Pre-clinical (animal studies) for Class III | 12–24 months | Safety in animal models |
| Clinical feasibility study | 6–18 months | First-in-human safety and feasibility |
| Pivotal clinical trial | 12–36 months | Efficacy evidence for regulatory submission |
| Regulatory review | 6–24 months | FDA or CE review and clearance/approval |

#### 2.5.5 Expected TRL Range

| TRL | Description | Expected at Stage |
|---|---|---|
| TRL 3–4 | Proof of concept; bench prototype | Incubator entry |
| TRL 5 | Validated in bench/laboratory environment | Seed stage |
| TRL 6 | System prototype demonstrated | Strong at seed; minimum for Series A discussion |
| TRL 7 | Prototype in clinical/operational environment | Pre-Series A |
| TRL 8 | Clinical-grade device; regulatory submission | Series A milestone |
| TRL 9 | Regulatory cleared, in commercial use | Series A/B |

#### 2.5.6 Weight Adjustments

| Evaluation Pillar | Directive | Rationale |
|---|---|---|
| Regulatory | **Increase weight significantly** | Device classification and regulatory pathway are deterministic of timeline, cost, and market access |
| Technology / IP | **Increase weight** | Device design, manufacturing know-how, and clinical data are the primary moats |
| Team | **Increase weight** | Clinical and regulatory expertise in the team is non-negotiable |
| Market | **Standard weight** | Market sizing should be done per indication and per geography |
| Traction | **Reduce weight at early stage** | Clinical pilots are the appropriate early traction signal; commercial sales premature pre-clearance |
| Financial Health | **Moderate weight** | Burn relative to regulatory milestones; device COGS is critical for margin assessment |

#### 2.5.7 Evaluation Considerations

1. **Device classification determination:** The regulatory strategy and timeline are entirely different for a Class I exempt, 510(k), or PMA pathway. Evaluators must confirm that the founding team has made an informed device classification determination and has documentation to support it.

2. **Predicate device selection for 510(k):** Class II 510(k) submissions require a predicate device showing substantial equivalence. Weak or inappropriate predicate selection is a common cause of 510(k) rejection. Evaluators should probe whether legal/regulatory counsel has reviewed the predicate strategy.

3. **Reimbursement pathway as a second regulatory burden:** Device clearance does not guarantee reimbursement. Many MedTech startups reach market with an cleared device only to find that hospitals cannot or will not pay for it without CPT code coverage or government scheme inclusion. Evaluators must assess whether the reimbursement strategy has been mapped.

4. **Clinical champion strategy:** Hospital adoption of new devices is driven by clinical champions — surgeons, physicians, or clinical administrators who advocate for procurement. Evaluators should assess whether the startup has identified and engaged clinical champions and whether those relationships are formalized.

5. **Quality management system readiness:** ISO 13485 certification (quality management for medical devices) is required for regulatory submission in most jurisdictions. Evaluators should assess whether the QMS is in place, in progress, or absent.

6. **Post-market surveillance obligations:** Once cleared, the startup has ongoing MDR (Medical Device Reporting) obligations. Evaluators should assess whether the team is aware of these obligations and has planned the infrastructure to manage them.

7. **SaMD classification and cybersecurity:** For devices with significant software components, Software as a Medical Device classification and cybersecurity requirements (FDA guidance, IEC 81001-5-1) add a distinct compliance layer that is frequently underestimated.

#### 2.5.8 Common Evaluation Errors

1. **Confusing CE marking with FDA clearance.** These are separate processes with different requirements, timelines, and costs. Evaluators who treat one as evidence of the other make a fundamental regulatory error.

2. **Underestimating regulatory timeline.** FDA 510(k) review officially takes 90 days but practically takes 6–18 months due to Additional Information requests. PMA can take 3–5 years. Evaluators who accept optimistic regulatory timelines in financial projections produce systematically inaccurate assessments.

3. **Ignoring COGS for physical devices.** Unlike software, MedTech products have a real cost of goods that must be managed to sustain margins. Evaluators who focus on top-line revenue projections without probing device COGS miss a critical profitability driver.

4. **Treating clinical pilot as commercial validation.** Hospitals frequently run clinical pilots of devices under research agreements at no charge. Evaluators who count pilot usage as commercial traction misrepresent the startup's commercial readiness.

---

### 2.6 SpaceTech

#### 2.6.1 Sector Overview

SpaceTech startups develop space systems, launch vehicles, satellite platforms, ground infrastructure, in-orbit services, space data analytics, and related technologies for commercial, government, or defense applications. The sector spans a wide range from nanosatellite constellations to launch vehicle development, in-space propulsion, space situational awareness, Earth observation analytics, satellite communication services, and in-situ resource utilization (ISRU) for lunar and planetary applications.

Key characteristics of the sector:
- Extreme capital intensity: launch costs, satellite manufacturing, and test infrastructure require tens to hundreds of millions of dollars before revenue is possible
- Long development cycles: 3–10 years from concept to orbital operation
- Government is the primary early customer in most categories (defense, Earth observation, communications)
- The space economy is bifurcating: a "new space" sector with lower-cost, high-frequency launch cycles and a "legacy space" sector with government prime contractors
- New space startups face competition from well-funded incumbents (SpaceX, Rocket Lab, Planet, Maxar) and must identify defensible niches
- Dual-use considerations are pervasive: most space technology has potential defense applications, creating export control and licensing complexity

#### 2.6.2 Expected Maturity at Application

- **Incubator / Pre-seed:** Defined mission concept, preliminary systems design, team with relevant aerospace/space engineering credentials, initial government agency engagement (ISRO-IN-SPACe in India, NASA in US, ESA in Europe)
- **Seed stage:** Subsystem prototypes, preliminary design review (PDR) completed, demonstration mission design, government grant or ISRO support secured
- **Series A:** Critical design review (CDR) completed, manufacture of flight-ready hardware in progress, launch agreement in place
- **Series B:** Hardware delivered to launch provider, in-orbit demonstration, first commercial data or service contracts

#### 2.6.3 Expected Financial Profile

| Stage | Monthly Burn | Expected Revenue | Key Indicators |
|---|---|---|---|
| Incubator | $50K–$200K | None | Government grants; IN-SPACe, ISRO, DST funding |
| Seed | $200K–$1M | None | Non-dilutive space agency funding; equity seed round |
| Series A | $800K–$5M | $0–$2M (government contracts, data licensing) | Technical milestone achievement; launch agreement value |
| Series B | $3M–$15M | $2M–$20M | Revenue from constellation services; contract backlog |

Given the extreme capital requirements, non-dilutive funding from space agencies is not supplementary — it is often the foundation that makes early-stage SpaceTech commercially viable. Evaluators must treat government grants and contracts as primary capital sources and evaluate their presence or absence accordingly.

#### 2.6.4 Expected Validation Cycle

| Validation Phase | Duration | Milestone |
|---|---|---|
| Concept of operations (ConOps) | 3–9 months | Mission architecture defined; technical feasibility confirmed |
| Preliminary design review (PDR) | 6–18 months | System design to 30% completion; heritage components identified |
| Critical design review (CDR) | 12–24 months | Complete system design; manufacturing drawings released |
| Hardware integration and test | 12–36 months | Environmental testing (thermal vacuum, vibration, EMI) |
| Launch and early orbit operations | 3–12 months | Launch, orbit insertion, commissioning |
| In-orbit demonstration | 6–18 months | Mission payload operational; first commercial data delivery |

#### 2.6.5 Expected TRL Range

| TRL | Description | Expected at Stage |
|---|---|---|
| TRL 2–3 | Concept and proof of concept | Incubator entry |
| TRL 3–4 | Component lab validation | Seed stage |
| TRL 5 | Subsystem validated in relevant environment | Strong for seed; minimum for Series A |
| TRL 6 | System prototype in relevant environment (thermal vacuum, vibration) | Series A milestone |
| TRL 7 | Prototype demonstrated in space or analog environment | Strong for Series A |
| TRL 8 | Flight-proven hardware | Series B milestone |
| TRL 9 | Operational in space | Commercial service launch |

#### 2.6.6 Weight Adjustments

| Evaluation Pillar | Directive | Rationale |
|---|---|---|
| Technology / IP | **Increase weight significantly** | Systems heritage, proprietary subsystem designs, and mission data represent the primary asset |
| Team | **Increase weight significantly** | Space engineering expertise is extremely rare; team composition is highly predictive |
| Regulatory | **Increase weight significantly** | IN-SPACe authorization, ITU frequency filing, export control (MTCR, ITAR, EAR), and spectrum licenses are gating factors |
| Market | **Increase weight** | Government contract pipeline and anchor commercial customers must be realistic and near-term |
| Financial Health | **Reduce standard weight** | Apply capital efficiency metric relative to technical milestones, not revenue |
| Traction | **Reduce to negligible early-stage weight** | Commercial traction is structurally impossible before orbital demonstration |

#### 2.6.7 Evaluation Considerations

1. **IN-SPACe authorization (India):** Under the Indian Space Policy 2023, all private space activities require IN-SPACe authorization. Evaluators must confirm the startup has initiated or completed this process and understands the authorization scope.

2. **Launch agreement realism:** Many early-stage SpaceTech startups list planned launches without confirmed launch agreements. The evaluator must distinguish between a confirmed rideshare contract (with SpaceX, Rocket Lab, ISRO, or others) and aspirational launch plans.

3. **ITU frequency coordination:** Satellite operators must coordinate frequencies with the ITU (International Telecommunication Union) through their national administration. This is a multi-year process that must be started early. Evaluators should confirm whether frequency filing is in progress.

4. **Export control compliance:** Dual-use space technologies are subject to MTCR (Missile Technology Control Regime), US ITAR/EAR, and Indian SCOMET export controls. Startups that have not assessed their export control obligations are carrying significant legal risk.

5. **Heritage vs. novel components:** The space industry relies heavily on "heritage" components (previously space-qualified hardware) to reduce risk. Startups that propose to use novel, unqualified components for their first mission face higher failure probability. Evaluators should assess the heritage ratio.

6. **Spectrum and orbit slot availability:** Low Earth Orbit is increasingly congested. Evaluators should assess whether the proposed orbital parameters are still available and whether debris mitigation compliance (25-year deorbit rule) has been addressed.

7. **Government customer pipeline:** For most early-stage SpaceTech companies, the government (defense or civilian space agency) is the first customer. The quality and specificity of government engagement — letters of support, MOU, SBIR contract — must be evaluated carefully.

#### 2.6.8 Common Evaluation Errors

1. **Treating lab prototype performance as flight-readiness.** Space hardware must survive launch vibration, thermal cycling in vacuum, radiation exposure, and years of operation without maintenance. Lab performance data does not predict flight performance without environmental qualification testing.

2. **Underestimating launch cost in financial models.** Small satellite launch costs range from $5,000–$10,000 per kilogram on current rideshare missions. Evaluators who accept launch cost estimates without verifying against current market rates often endorse financially unrealistic models.

3. **Ignoring regulatory authorization timelines.** IN-SPACe authorization, ITU coordination, and spectrum licensing can take 12–36 months. Evaluators who accept mission timelines that do not account for regulatory lead time produce materially inaccurate assessments.

4. **Overweighting academic publications.** Space research teams often have strong publication records that do not translate to hardware execution capability. Publications are positive signals but must be accompanied by evidence of hardware build and test experience.

---

### 2.7 Defence / DualUse Tech

#### 2.7.1 Sector Overview

Defence and DualUse Tech startups develop technologies with direct military or homeland security applications, or technologies originally developed for civilian use that have significant defense applicability (and vice versa). Applications include: unmanned aerial and ground vehicles, autonomous systems, cybersecurity and electronic warfare, communications and C4ISR systems, surveillance and reconnaissance systems, advanced materials for armor and ballistics, directed energy systems, simulation and training platforms, and logistics and supply chain systems for defence.

Key characteristics:
- The primary customer is a government defense ministry, armed force, paramilitary organization, or defence public sector undertaking (DPSU)
- Procurement cycles in defense are among the longest of any sector: 3–10 years from qualification to purchase order
- iDEX (Innovations for Defence Excellence) in India and DARPA, DIU, AFWERX in the US have significantly accelerated early-stage engagement but do not eliminate the long procurement cycle
- Export is governed by stringent export control regimes (ITAR/EAR in the US; SCOMET in India; similar in EU)
- Dual-use technology requires careful management of both civilian and defense commercialization pathways
- Security clearances may be required for founders, team members, and facilities
- Intellectual property created under government contracts may be subject to government rights provisions

#### 2.7.2 Expected Maturity at Application

- **Incubator / Pre-seed:** A defined defence problem statement (ideally from a formal iDEX DPP statement or direct military engagement), preliminary concept design, and at least one team member with operational defense knowledge or experience
- **Seed stage:** Working prototype, iDEX DISC or SPRINT grant received, at least one user trial with an armed force unit
- **Series A:** iDEX DPP winner or equivalent, formal GSQR (General Service Quality Requirement) engagement, procurement pipeline visible
- **Series B:** Production order received, or large-scale pilot with armed forces operational

#### 2.7.3 Expected Financial Profile

| Stage | Monthly Burn | Expected Revenue | Key Indicators |
|---|---|---|---|
| Incubator | $20K–$100K | None | iDEX grant; angel / strategic investor |
| Seed | $80K–$400K | $0–$500K (iDEX milestone payments, trial contracts) | Milestone-based grant drawdown |
| Series A | $300K–$1.5M | $500K–$5M (small production orders or contract R&D) | Procurement pipeline value; qualification status |
| Series B | $1M–$5M | $5M–$50M (production contracts) | Order backlog; export potential |

Defence startups operate in a milestone-driven, contract-based revenue model. Standard commercial metrics like MRR and churn are not applicable. Contract backlog, pipeline of qualified opportunities, and position on Defence Acquisition Procedure (DAP) procurement lists are the relevant financial indicators.

#### 2.7.4 Expected Validation Cycle

| Validation Phase | Duration | Milestone |
|---|---|---|
| Concept validation | 3–9 months | Feasibility demonstration against GSQR preliminary requirements |
| User trial (Phase 1) | 6–18 months | Controlled military environment testing; user feedback |
| Extended user trial (Phase 2) | 12–24 months | Operational deployment trial in field conditions |
| Quality and reliability testing | 12–18 months | Testing against MIL-SPEC or equivalent; formal GSQR qualification |
| Type approval / DPD clearance | 6–24 months | Formal defence procurement division clearance |
| Production order | 12–24 months post-qualification | First production run |

#### 2.7.5 Expected TRL Range

| TRL | Description | Expected at Stage |
|---|---|---|
| TRL 3–4 | Proof of concept | Incubator entry; iDEX DISC application |
| TRL 5 | Validated in relevant environment | Seed stage; iDEX DPP milestone |
| TRL 6 | System prototype in representative environment | Strong seed; pre-Series A |
| TRL 7 | System prototype in operational environment (user trial) | Series A; formal qualification process |
| TRL 8 | System qualified and tested | Series B; production order eligibility |
| TRL 9 | Deployed in operational service | Full commercialization |

#### 2.7.6 Weight Adjustments

| Evaluation Pillar | Directive | Rationale |
|---|---|---|
| Technology / IP | **Increase weight** | Technical performance against military specifications is the primary qualification criterion |
| Regulatory | **Increase weight significantly** | Export controls, security classifications, and Defence Acquisition Procedure compliance are non-negotiable |
| Team | **Increase weight** | Operational defence expertise (ex-military, DRDO background) provides critical GTM access |
| Market | **Increase weight** | Defence procurement pipeline is specific and governable; evaluators must assess GSQR alignment |
| Traction | **Reduce weight at early stage** | Procurement cycles preclude early commercial traction; iDEX grant and trial invitations are proxy signals |
| Financial Health | **Adjust to contract model** | Evaluate contract backlog, milestone payment schedule, and production order pipeline rather than MRR |

#### 2.7.7 Evaluation Considerations

1. **iDEX program alignment:** For India-based defence startups, iDEX (under MoD) provides the primary structured pathway for early-stage defense engagement. Evaluators should determine whether the startup has applied to or been selected under iDEX DISC, iDEX Prime, or SPRINT schemes, as these provide both funding and operational validation access.

2. **GSQR and user requirement traceability:** The General Service Quality Requirement (GSQR) defines what a military system must do. A defence startup that cannot trace its product specifications to a GSQR or equivalent operational requirement is not commercially aligned with the procurement process.

3. **Export control classification (SCOMET):** In India, SCOMET (Special Chemicals, Organisms, Materials, Equipment, and Technologies) controls govern the export of dual-use and defence technologies. Startups that have not classified their technology against SCOMET Schedule 2 are carrying unquantified legal risk.

4. **Security infrastructure requirements:** Some defence contracts require certified physical security infrastructure (secure server rooms, classified document handling facilities). Evaluators should assess whether the startup's facilities meet or can meet these requirements.

5. **Offset obligations and ToT (Transfer of Technology):** Large defence contracts in India include mandatory offset obligations and ToT requirements. For a startup selling to a prime contractor, understanding the offset credit and ToT implications is important for business model design.

6. **Founder background screening:** Investors and government program officers in defence are increasingly conducting background screening of founding teams. Evaluators should flag any conflict-of-interest risks (foreign government ties, dual citizenship in sensitive jurisdictions) as a due diligence item.

7. **Dual-use commercialization strategy:** Startups with both defence and civilian applications often underexploit the civilian side due to focus on defence procurement. Evaluators should assess whether the dual-use opportunity is explicitly planned and resourced.

#### 2.7.8 Common Evaluation Errors

1. **Applying commercial procurement timelines to defence sales.** Defence procurement does not move like commercial B2B sales. Evaluators who accept 6–12 month sales cycle assumptions for defence are building fundamentally incorrect financial models.

2. **Treating iDEX selection as revenue.** iDEX DISC and DPP grants are milestone-based and non-dilutive, but they are not revenue. Evaluators who count grant disbursements as product revenue misrepresent the startup's commercial validation.

3. **Ignoring export control risk.** A defence startup with no documented SCOMET or ITAR assessment is carrying material legal risk. Evaluators who do not specifically probe export control status are missing a potential deal-breaker.

4. **Underweighting the value of ex-military founders.** In defence, relationships, operational understanding, and insider access to procurement processes are primary GTM assets. Evaluators from commercial backgrounds frequently undervalue founding team members with military service records.

---

### 2.8 AgriTech

#### 2.8.1 Sector Overview

AgriTech startups develop technologies that improve agricultural productivity, efficiency, sustainability, or value chain integration across the food and farming ecosystem. Applications include: precision agriculture (sensors, drones, satellite imagery, IoT), crop protection solutions (biopesticides, biocontrol agents), novel seed technology, controlled environment agriculture (vertical farming, greenhouse technology), agricultural fintech (farmer credit, insurance, input procurement), supply chain and market linkage platforms, post-harvest technology, and livestock management systems.

The AgriTech sector has unique structural characteristics that set it apart from most other technology sectors:

- **Seasonality:** Agricultural cycles (Kharif, Rabi, Zaid in India; planting/harvest cycles globally) create seasonal demand patterns that directly affect testing, deployment, and revenue timing
- **Last-mile distribution complexity:** Reaching smallholder farmers in India requires distribution networks and trust-building that are substantially different from urban tech deployment
- **Government influence:** Agricultural markets in India are heavily regulated (MSP, APMC, FCI), and policy changes can profoundly affect addressable market
- **Low digital penetration among end users:** Many farmers, particularly smallholders, have limited smartphone literacy, requiring simplified UX, voice interfaces, or intermediary-driven deployment
- **High pilot-to-scale failure rate:** Many AgriTech solutions that perform well in controlled pilots fail to scale due to farm diversity, soil variation, and behavioral resistance

#### 2.8.2 Expected Maturity at Application

- **Incubator application:** A pilot with at least 20–50 farmers, seasonal cycle data (at minimum one full crop cycle), and a clear value proposition that the farmer perceives (not just the aggregator or buyer)
- **Seed stage:** 100–500 farmer users, at least one full agricultural season of data, a distribution partnership (FPO, agri-input company, government scheme), and preliminary revenue
- **Series A:** 10,000+ farmer reach, demonstrable yield improvement or cost reduction data, established distribution channel, MRR from subscriptions or transaction fees

#### 2.8.3 Expected Financial Profile

| Stage | Monthly Burn | Expected Revenue | Key Indicators |
|---|---|---|---|
| Incubator | $10K–$50K | $0–$5K | Pilot farmer count; full-season data |
| Seed | $30K–$150K | $5K–$50K | Farmer retention across seasons; revenue per farmer |
| Series A | $100K–$400K | $50K–$300K | CAC per farmer acquisition; LTV over 3 seasons |
| Series B | $300K–$1M | $300K–$2M | Revenue per district; government partnership revenues |

Revenue models in AgriTech include: SaaS subscriptions per farm, transaction fees on input procurement platforms, insurance premium sharing, premium crop marketing fees, and government scheme implementation fees. Evaluators must identify which model is in use and whether unit economics are sustainable.

**Key metric — Revenue per farmer per season:** This should be tracked explicitly. AgriTech businesses with revenue per farmer below the farmer's perceived switching cost (typically ₹200–₹500 per season for smallholders) face high attrition.

#### 2.8.4 Expected Validation Cycle

| Validation Phase | Duration | Milestone |
|---|---|---|
| Pilot with 20–50 farmers | 1 agricultural season (3–6 months) | User adoption, data quality, farmer feedback |
| Scale pilot with 200–500 farmers | 1–2 seasons | Retention across seasons; yield/income data |
| District-level deployment | 1–2 seasons | Distribution scalability; partner engagement |
| State-level deployment | 2–4 seasons | Revenue scale; government scheme integration |

The minimum meaningful validation cycle for an AgriTech startup is **one full agricultural season** from planting to harvest to income realization. Evaluators must not count user counts or downloads that have not been validated across a complete cycle.

#### 2.8.5 Expected TRL Range

| TRL | Description | Expected at Stage |
|---|---|---|
| TRL 4 | Validated in controlled field conditions | Incubator entry |
| TRL 5 | Validated on 50–200 farms in realistic conditions | Seed stage |
| TRL 6 | Deployed with multiple farmer groups; seasonally validated | Strong for seed |
| TRL 7 | Multi-season, multi-crop deployment at scale | Pre-Series A |
| TRL 8 | Commercial deployment with defined distribution channel | Series A milestone |
| TRL 9 | Full commercial operation at district/state scale | Series B |

#### 2.8.6 Weight Adjustments

| Evaluation Pillar | Directive | Rationale |
|---|---|---|
| Market | **Increase weight** | India's agricultural market is large but highly fragmented; market accessibility, not size, is the key question |
| Team | **Increase weight** | Agricultural domain expertise and farmer community trust are critical execution enablers not reflected in generic team metrics |
| Traction | **Increase weight (with seasonality adjustment)** | Farmer retention across multiple seasons is the most meaningful signal; single-season traction is insufficient |
| Technology / IP | **Moderate weight** | Technology differentiation matters but distribution and trust often matter more in this sector |
| Financial Health | **Reduce weight at early stage** | Revenue is highly seasonal; monthly burn and MRR metrics must be interpreted with crop cycle awareness |
| Regulatory | **Increase weight for biopesticide/seed products** | CIBRC approvals for biopesticide and biocontrol products are gating factors; standard for digital AgriTech |

#### 2.8.7 Evaluation Considerations

1. **Smallholder vs. large farm targeting:** Solutions designed for 50-acre commercial farms in Punjab are not applicable to 1-acre smallholders in Bihar. Evaluators must confirm that the solution's design, pricing, and distribution model match the actual target farmer segment.

2. **Seasonal revenue distortion:** AgriTech revenue is inherently seasonal. A startup showing ₹10 lakhs in revenue in October (post-harvest) and ₹0 in May may be completely healthy. Evaluators must use annualized and seasonally-adjusted metrics, not monthly snapshots.

3. **Government scheme integration:** Many successful AgriTech platforms in India derive significant revenue from government scheme implementation (PM-KISAN, soil health cards, crop insurance under PMFBY). Evaluators should assess whether the startup's revenue model is dependent on government schemes and what the risks of scheme discontinuation are.

4. **Farmer data rights and privacy:** Farmer data (soil health, cropping pattern, yield records, financial behavior) is sensitive and increasingly regulated. Evaluators should assess whether the startup has a clear data governance policy and farmer consent mechanism.

5. **Language and interface accessibility:** In India, effective farmer interfaces require support for regional languages (Hindi, Marathi, Telugu, Punjabi, Kannada) and voice-first or IVR interfaces for farmers with limited smartphone literacy. Evaluators should assess the UX accessibility specifically for the target farmer segment.

6. **Distribution partner dependency:** Many AgriTech startups are dependent on FPOs, agri-input dealers, or rural banking correspondents for farmer reach. The quality, exclusivity, and stability of these distribution partnerships directly affects scalability.

7. **Climate variability impact on product efficacy claims:** AgriTech products that claim yield improvements must demonstrate performance under variable weather conditions (drought, unseasonal rain, pest pressure). Claims based on one good-weather season are not reliable.

#### 2.8.8 Common Evaluation Errors

1. **Counting app downloads or registrations as active users.** Many AgriTech platforms show large registration numbers with very low actual usage rates. Evaluators must require data on active users per season, not total registered users.

2. **Ignoring seasonality in financial health assessment.** An AgriTech startup with zero revenue in January may be completely healthy and working through the Rabi season. Evaluators who assess monthly burn without seasonal context produce inaccurate assessments.

3. **Accepting yield improvement claims without statistical rigor.** "Farmers using our platform achieved 25% higher yields" is a meaningful claim only if it includes comparison to a control group, sample size, crop and region specification, and weather conditions. Anecdotal yield improvement claims are frequently accepted without this rigor.

4. **Underestimating last-mile distribution cost.** The cost of acquiring and servicing farmers in rural India is substantially higher than urban tech customer acquisition. Evaluators who apply urban SaaS CAC benchmarks to AgriTech significantly underestimate the true customer acquisition cost.

---

### 2.9 ClimateTech / CleanTech

#### 2.9.1 Sector Overview

ClimateTech and CleanTech startups develop solutions that reduce greenhouse gas emissions, sequester carbon, increase energy efficiency, enable the energy transition, or build resilience to climate impacts. The sector encompasses: solar energy systems and components, wind technology, energy storage solutions, green hydrogen production and distribution, carbon capture, utilization and storage (CCUS), sustainable aviation fuel (SAF), electric mobility and charging infrastructure, industrial decarbonization, building efficiency, sustainable materials, water technology, and climate data and analytics platforms.

Key structural characteristics:
- Policy and regulation (carbon credits, renewable purchase obligations, PLI schemes) are primary market drivers — market size changes with policy
- The sector has a bimodal structure: software/analytics companies with SaaS-like economics and deep-tech hardware companies with capital intensity comparable to DeepTech
- Carbon credit market linkage is increasingly a revenue supplement for many startups
- Project finance (not venture equity) is the appropriate funding structure for large infrastructure deployments
- Customer categories include utilities, industrial corporates, municipalities, and governments — all with long procurement cycles

#### 2.9.2 Expected Maturity at Application

- **Incubator / Pre-seed:** Defined technology approach, preliminary energy/emissions performance data, understanding of applicable policy/incentive framework, and a pilot site or partnership
- **Seed stage:** Working pilot (even at small scale), measurable performance data, first commercial discussion, clear understanding of energy project economics (LCOE, payback period, IRR)
- **Series A:** At least one operational installation or deployment, demonstrable performance data, signed commercial contract or LOI, project financing strategy defined

#### 2.9.3 Expected Financial Profile

| Stage | Monthly Burn | Expected Revenue | Key Indicators |
|---|---|---|---|
| Incubator | $20K–$100K | None | Government grant; MNRE, SECI funding; carbon market interest |
| Seed | $80K–$400K | $0–$200K (pilot revenue, TOTEX) | Pilot site performance; LCOE or decarbonization cost |
| Series A | $300K–$1.5M | $200K–$3M (project contracts, O&M, subscription) | Project IRR; contract pipeline value |
| Series B | $1M–$5M | $3M–$30M | Cumulative GHG emissions avoided; GW deployed |

**Sector-specific metrics:**
- **LCOE (Levelized Cost of Energy)** for energy generation technologies
- **Cost per ton of CO₂ avoided** for decarbonization solutions
- **Project IRR** for energy project deployments
- **Carbon credits generated** (voluntary or compliance market)

#### 2.9.4 Expected Validation Cycle

| Validation Phase | Duration | Milestone |
|---|---|---|
| Lab or bench prototype | 3–12 months | Energy/material performance data under controlled conditions |
| Pilot installation (small scale) | 6–18 months | Performance in real-world conditions; LCOE or cost-per-ton data |
| Demonstration project | 12–36 months | Full-scale operating unit; bankability assessment |
| Commercial deployment | 24–60 months | Revenue-generating installation; replication across sites |

Energy and climate projects must demonstrate bankability — the ability to obtain project financing from banks or infrastructure funds based on demonstrated performance. This is a validation milestone unique to this sector.

#### 2.9.5 Expected TRL Range

| TRL | Description | Expected at Stage |
|---|---|---|
| TRL 3–4 | Proof of concept | Incubator entry for deep-tech ClimateTech |
| TRL 5 | Validated in relevant environment | Seed stage |
| TRL 6 | Pilot installation operational | Strong for seed |
| TRL 7 | Demonstration project operational | Pre-Series A |
| TRL 8 | Commercial-scale deployment | Series A |
| TRL 9 | Full commercial operation at scale | Series B |

For software/analytics ClimateTech (carbon accounting platforms, grid optimization software), TRL expectations follow the SaaS framework: TRL 6–7 at seed, TRL 8–9 at Series A.

#### 2.9.6 Weight Adjustments

| Evaluation Pillar | Directive | Rationale |
|---|---|---|
| Technology / IP | **Increase weight for hardware** | Novel materials, processes, or system designs are the primary differentiator |
| Market | **Increase weight** | Policy-driven market sizing requires detailed analysis of regulatory trajectory; not static |
| Regulatory | **Increase weight** | Grid connection approvals, MNRE permits, carbon credit certification (VCS, Gold Standard) are gating factors |
| Team | **Standard weight** | Mix of technical, policy, and project finance expertise required |
| Traction | **Adjust to project milestones** | Signed project contracts, LOIs, and operational installations are the appropriate traction signals |
| Financial Health | **Apply project finance lens** | LCOE, IRR, payback period are more meaningful than MRR for energy project businesses |

#### 2.9.7 Evaluation Considerations

1. **Policy risk assessment:** ClimateTech market sizes are determined by policy (renewable purchase obligations, carbon tax levels, PLI scheme eligibility, FAME subsidies). Evaluators must assess what happens to the market if the key supporting policy is modified or withdrawn.

2. **Grid interconnection and permitting:** Renewable energy systems require grid interconnection agreements, which are complex and jurisdiction-specific. Evaluators should assess whether the startup has experience navigating the interconnection process and what lead times are expected.

3. **Additionality for carbon credits:** Carbon credit buyers increasingly require proof of "additionality" — that the emission reductions would not have occurred without the project. Evaluators assessing carbon market-linked revenue must probe the additionality methodology and third-party verification status.

4. **Energy storage integration:** Many ClimateTech solutions (solar, wind) require integration with storage to provide dispatchable power. Evaluators should assess whether the storage strategy is integrated into the technical and financial model.

5. **Financing stack complexity:** Large-scale energy projects require layered financing (equity, debt, mezzanine, government grants). A startup that plans to self-fund or rely solely on equity investors for large installations has a structurally inadequate financing strategy.

6. **Lifecycle environmental impact:** Some CleanTech solutions (battery manufacturing, solar panel production) have significant embedded carbon or material toxicity. Evaluators should assess whether the startup's lifecycle environmental claim holds up to LCA (Life Cycle Assessment) scrutiny.

7. **Supply chain for critical materials:** Many ClimateTech products depend on critical minerals (lithium, cobalt, neodymium, indium). Evaluators must assess supply chain security and exposure to material price volatility.

#### 2.9.8 Common Evaluation Errors

1. **Treating pilot performance data as commercial performance.** Pilot installations often operate under favorable conditions (optimal site selection, close team monitoring) that do not replicate at scale. Evaluators who accept pilot-stage performance claims without asking about the generalizability to commercial deployments overstate product readiness.

2. **Ignoring project finance requirements.** Equity investors cannot fund large-scale energy deployments alone. Evaluators who assess a ClimateTech startup's financial plan without asking whether it is bankable — whether commercial banks will lend against projected cash flows — miss a fundamental execution risk.

3. **Accepting carbon credit projections without verification methodology.** Carbon credit revenue projections are frequently included in ClimateTech financial models without specifying the certification standard, MRV (Monitoring, Reporting, and Verification) methodology, or third-party auditor.

4. **Overweighting laboratory efficiency metrics.** Solar cell efficiency measured in a laboratory setting (NREL standards) consistently exceeds real-world field efficiency by 15–30%. The same principle applies to many energy storage and conversion technologies. Lab efficiency numbers, presented without field efficiency data, overstate commercial performance.

---

### 2.10 FinTech

#### 2.10.1 Sector Overview

FinTech startups develop technology-driven financial services across a wide spectrum of applications: digital payments and wallets, lending (consumer credit, MSME lending, buy-now-pay-later), wealth management and robo-advisory, insurance technology (InsurTech), regulatory technology (RegTech), blockchain and digital assets, international remittances, credit scoring and underwriting, banking-as-a-service (BaaS) platforms, and embedded finance solutions.

Key characteristics of the FinTech sector:
- Regulatory licensing is a hard requirement in most sub-sectors: NBFC license, PA license (Payment Aggregator), insurance broker license, PPI (Prepaid Payment Instrument) license — these are gating prerequisites, not optional
- RBI (in India), SEBI, IRDAI, and PFRDA regulate different FinTech sub-sectors with distinct compliance regimes
- Financial intermediation creates direct balance sheet risk that pure technology companies do not carry
- Customer trust and data security are existential requirements — a single major data breach or fraud incident can destroy a FinTech business permanently
- Distribution through existing financial institution partnerships (banks, NBFCs, insurers) is often faster and cheaper than direct consumer acquisition for B2B FinTech
- Credit portfolio quality (NPA rate, loss given default, vintage curves) is the primary performance metric for lending FinTech, not revenue alone

#### 2.10.2 Expected Maturity at Application

- **Incubator / Pre-seed:** Defined regulatory pathway, legal entity with appropriate corporate structure for licensing, at least one regulatory consultation completed, and if applicable, an RBI Regulatory Sandbox application or SEBI Innovation Sandbox participation
- **Seed stage:** Regulatory license obtained or in-process, working product, 1,000–10,000 active users or ₹50L–₹5Cr in transaction volume, defined risk management framework
- **Series A:** Licensed, operational at scale, demonstrable unit economics, defined credit risk model (for lending), AUM of ₹50Cr+ (for wealth), GMV of ₹100Cr+ (for payments)
- **Series B:** Profitability pathway clear, diversified revenue streams, regulatory capital adequacy maintained

#### 2.10.3 Expected Financial Profile

| Stage | Monthly Burn | Expected Revenue / GMV | Key Metrics |
|---|---|---|---|
| Incubator | $15K–$60K | Minimal | Regulatory license timeline; risk model design |
| Seed | $50K–$200K | $5K–$100K NTR or GMV-based revenue | Active users; transaction volume; NPA rate if lending |
| Series A | $200K–$700K | ₹1Cr–₹20Cr NTR | Net Interest Margin; take rate; CAC/LTV; NPA |
| Series B | $500K–$2M | ₹20Cr–₹200Cr NTR | Adjusted NIM; credit cost; NNPA; RAROC |

**Sector-specific metrics for lending FinTech:**
- **GNPA / NNPA:** Gross and Net Non-Performing Asset ratios (regulatory thresholds apply)
- **Net Interest Margin (NIM):** Revenue minus cost of funds
- **Credit cost:** Provision expense as % of AUM
- **Vintage curves:** Default rates by loan origination cohort over time

For payments FinTech, **GMV (Gross Merchandise Value)** and **take rate** are primary metrics. For InsurTech, **premium in force** and **loss ratio** are critical.

#### 2.10.4 Expected Validation Cycle

| Validation Phase | Duration | Milestone |
|---|---|---|
| Regulatory pathway mapping | 2–6 months | License type identified; legal structure established |
| License application | 3–18 months | RBI/SEBI/IRDAI license application filed |
| Product development | 3–9 months | MVP with core financial transaction flow |
| Pilot with limited users | 3–9 months | Controlled user base under regulatory oversight or sandbox |
| Commercial launch | 6–18 months | Full commercial operation post-licensing |
| Credit/risk model validation | 6–24 months | Minimum 6–12 month vintage data on credit book |

#### 2.10.5 Expected TRL Range

| TRL | Description | Expected at Stage |
|---|---|---|
| TRL 5 | Product validated in sandbox/pilot | Seed stage minimum |
| TRL 6 | Licensed product operational with limited users | Pre-Series A |
| TRL 7 | Operational at commercial scale, risk model functioning | Series A |
| TRL 8 | Proven at scale with multiple product lines | Series A/B |
| TRL 9 | Full commercial operation; regulatory compliance demonstrated | Series B+ |

#### 2.10.6 Weight Adjustments

| Evaluation Pillar | Directive | Rationale |
|---|---|---|
| Regulatory | **Increase weight significantly** | Regulatory license is a hard prerequisite for operation; compliance track record is a primary quality signal |
| Financial Health | **Increase weight significantly** | Unit economics (NIM, take rate, CAC/LTV, NPA) are directly and immediately measurable in FinTech |
| Technology / IP | **Moderate weight** | Technology advantage is important but often less durable than regulatory moats and network effects |
| Market | **Standard weight** | Market size well-documented; ICP specificity and regulatory market access are the key questions |
| Traction | **Increase weight** | Transaction volume, AUM, or premium in force are available and meaningful at early stages |
| Team | **Increase weight** | Finance domain expertise (risk, treasury, compliance, regulation) is as important as technical expertise |

#### 2.10.7 Evaluation Considerations

1. **Regulatory license status and timeline:** Evaluators must specifically verify the status of required licenses (RBI NBFC, PA license, PPI license, insurance broker license). A FinTech that is operating without required licenses is in violation of law, regardless of product quality.

2. **Credit risk model sophistication:** For lending FinTech, the credit scoring model is the core IP. Evaluators should probe: What features are used? What is the model's performance on a holdout dataset? How is model drift monitored? Is bureau data (CIBIL, CRIF, Experian) integrated?

3. **AML/KYC compliance:** Anti-Money Laundering and Know Your Customer compliance is mandatory and operationally complex. A startup that has not implemented RBI-compliant KYC and AML monitoring is carrying significant regulatory risk.

4. **Cybersecurity and data protection posture:** Financial data is among the most sensitive personal data. RBI Master Directions on Cybersecurity Framework, CERT-In incident reporting requirements, and proposed DPDP Act obligations create a dense compliance environment. Evaluators must probe the startup's cybersecurity framework.

5. **Co-lending and banking partnership strategy:** Many lending FinTech companies in India rely on co-lending arrangements with banks (RBI co-lending model) for capital access and cost of funds reduction. The quality and stability of these banking partnerships are primary operational risk factors.

6. **UPI/NPCI compliance for payments:** FinTech operating in the payments space must adhere to NPCI operational guidelines, UPI system eligibility requirements, and MDR frameworks. Non-compliance with NPCI guidelines is a reason for platform ejection.

7. **BNPL and consumer credit risk:** Buy-now-pay-later products carry significant consumer credit risk that manifests only after 6–12 months of deployment (vintage lag). Early financial projections that assume low NPA rates without vintage data supporting them should be treated with skepticism.

#### 2.10.8 Common Evaluation Errors

1. **Treating GMV as revenue.** In payments FinTech, GMV is the transaction value flowing through the platform. Revenue is the take rate applied to GMV (typically 0.1–1.5% in India). Evaluators who conflate GMV with revenue over-assess the startup's financial performance by 50–1000x.

2. **Ignoring regulatory licensing risk.** Some FinTech startups operate in a grey area, relying on partnerships with licensed entities. Evaluators who do not specifically probe the regulatory structure and whether the startup's specific activity requires its own license miss a potential existential risk.

3. **Accepting early-vintage NPA rates as predictive.** A lending portfolio less than 12 months old has not yet revealed its true credit quality. Early-vintage NPA rates are meaningless as predictors of portfolio health. Evaluators who treat early NPA data as validation make a classic lending evaluation error.

4. **Underweighting the cost of funds.** The spread between a lending FinTech's cost of capital and its lending rate determines profitability. Evaluators who focus on lending yield without probing cost of funds produce inaccurate NIM assessments.

---

### 2.11 Manufacturing / Industry 4.0

#### 2.11.1 Sector Overview

Manufacturing and Industry 4.0 startups develop technologies that transform traditional manufacturing operations through digitization, automation, and advanced analytics. Applications include: Industrial IoT (IIoT) platforms, predictive maintenance systems, digital twin technology, industrial automation and robotics, smart factory management systems (MES, SCADA), quality inspection systems using computer vision, supply chain visibility and optimization, additive manufacturing (3D printing) for production, energy management in industrial settings, and workforce productivity platforms for shop floor operations.

Key characteristics:
- The primary customer (large-scale manufacturers, industrial enterprises) has a long, conservative procurement cycle
- ROI demonstration is the central purchase criterion — manufacturers require clear financial justification before adoption
- Operational continuity is paramount: industrial customers will not adopt technology that creates production risk
- Legacy system integration is complex: manufacturers operate legacy SCADA, ERP (SAP, Oracle), and MES systems that new technology must integrate with non-disruptively
- Industry 4.0 adoption is highly heterogeneous — large enterprises are at different stages of digitization, creating a fragmented market

#### 2.11.2 Expected Maturity at Application

- **Incubator / Pre-seed:** A working prototype of the IIoT sensor system, software platform, or robotics module with bench test results and at least one manufacturing plant visit/assessment conducted
- **Seed stage:** Pilot deployment in an industrial setting (1–3 plants), quantified ROI data (OEE improvement, downtime reduction, defect rate reduction), and a clear integration roadmap with standard industrial protocols (OPC-UA, MQTT, Modbus)
- **Series A:** 5–20 production plant deployments, ARR from SaaS or hardware+subscription model, quantified ROI across multiple customers, channel partnership with system integrator

#### 2.11.3 Expected Financial Profile

| Stage | Monthly Burn | Expected Revenue | Key Indicators |
|---|---|---|---|
| Incubator | $15K–$60K | None | Manufacturing plant access for pilot |
| Seed | $50K–$250K | $10K–$100K (pilot contracts, POC fees) | OEE improvement data; integration success rate |
| Series A | $200K–$800K | $100K–$1M ARR | ACV per plant; contract length; upsell rate |
| Series B | $600K–$2.5M | $1M–$10M ARR | System integrator channel revenue; plant expansion within accounts |

Revenue models include: hardware sale plus software subscription, pure SaaS subscription, implementation project fees plus ongoing SaaS, and outcome-based pricing (% of savings generated). Evaluators must understand the specific model and its implications for revenue recognition and gross margin.

#### 2.11.4 Expected Validation Cycle

| Validation Phase | Duration | Milestone |
|---|---|---|
| Proof of concept (plant trial) | 2–6 months | System installed on limited production line; baseline established |
| Pilot deployment | 3–9 months | Full system operational; ROI data collected against baseline |
| Full plant rollout | 6–18 months | End-to-end deployment across full plant; full ROI demonstrated |
| Multi-plant expansion | 12–24 months | Deployment replicated at 3+ plants; standard integration playbook |

The critical validation milestone for Industry 4.0 startups is a **quantified ROI demonstration in a live production environment** — not a lab simulation, not a demo environment, but a real factory floor with real production data.

#### 2.11.5 Expected TRL Range

| TRL | Description | Expected at Stage |
|---|---|---|
| TRL 5 | Validated in controlled industrial environment | Incubator entry |
| TRL 6 | System validated in relevant industrial environment | Seed stage |
| TRL 7 | System deployed in operational manufacturing environment | Strong for seed; pre-Series A |
| TRL 8 | System deployed at 5+ plants; repeatable | Series A |
| TRL 9 | Proven at scale across multiple manufacturing sectors | Series B |

#### 2.11.6 Weight Adjustments

| Evaluation Pillar | Directive | Rationale |
|---|---|---|
| Traction | **Increase weight** | Pilot deployments in real manufacturing environments are the primary validation signal |
| Market | **Standard weight** | Manufacturing market is large and well-quantified; ICP definition is the key question |
| Technology / IP | **Increase weight** | Industrial protocol integration, edge computing architecture, and AI model performance in noisy industrial environments are key differentiators |
| Team | **Increase weight** | Manufacturing domain expertise (operations, process engineering) combined with software expertise is rare and highly predictive |
| Financial Health | **Moderate weight** | ARR and gross margin are relevant but must account for hardware component and implementation costs |
| Regulatory | **Standard weight** | Industrial safety certifications (ATEX for hazardous environments, CE/UL for electrical safety) may apply |

#### 2.11.7 Evaluation Considerations

1. **OPC-UA / MQTT / legacy protocol integration:** Industrial facilities operate diverse communication protocols. A startup that cannot demonstrate integration with OPC-UA (the industry standard) and legacy protocols (Modbus, PROFIBUS) will face deployment barriers in most manufacturing environments.

2. **Edge vs. cloud architecture:** In manufacturing environments with limited or unreliable internet connectivity, cloud-dependent architectures create reliability risks. Evaluators must assess whether the solution supports edge computing and offline operation modes.

3. **Industrial cybersecurity:** ICS/OT (Industrial Control System/Operational Technology) networks have unique cybersecurity requirements (IEC 62443, NERC CIP for utilities). A startup connecting IIoT devices to plant networks without an ICS security assessment creates liability for its industrial customers.

4. **Change management and workforce adoption:** Industry 4.0 solutions often fail not because of technology but because of workforce resistance, inadequate training, or process redesign requirements that were not anticipated. Evaluators should probe the startup's change management methodology.

5. **System integrator (SI) channel strategy:** Most large manufacturing enterprises procure through System Integrators (Siemens, Rockwell, Honeywell, TCS, HCL). A startup without an SI channel partnership faces severe GTM barriers with enterprise manufacturing customers.

6. **Implementation timeline and cost for the customer:** Long implementation timelines and high implementation costs create a barrier to adoption. Evaluators should probe the typical time-to-value for a new plant deployment and what implementation cost falls on the customer.

7. **Data sovereignty and competitive sensitivity:** Manufacturers are extremely sensitive about production data (capacity utilization, defect rates, maintenance schedules) leaving their network. Evaluators must assess the startup's data residency architecture and contractual data protection commitments.

#### 2.11.8 Common Evaluation Errors

1. **Accepting demo environment performance as production validation.** Many Industry 4.0 startups demonstrate their solution in controlled environments or on decommissioned equipment. Performance in a live production environment with real variability, EMI, and operational constraints is substantially different.

2. **Underestimating implementation complexity and cost.** Industrial deployments require network infrastructure work, legacy system integration, safety assessments, and change management that are frequently underestimated in both time and cost. Evaluators who accept quick-deployment timelines without probing integration complexity are optimistic to the point of error.

3. **Ignoring the system integrator gatekeeping role.** Enterprise manufacturers almost universally require that new technology is either validated by or delivered through a trusted SI. Startups without an SI strategy have a GTM gap that directly affects revenue projections.

4. **Treating pilot ROI data from friendly customers as generalizable.** Early pilots are often run with cooperative customers (co-founders' network, accelerator connections) who provide optimal conditions. Evaluators must ask whether the ROI result can be replicated with cold-start customers in diverse manufacturing environments.

---

### 2.12 Consumer Tech

#### 2.12.1 Sector Overview

Consumer Tech startups build technology products and platforms consumed directly by individual consumers, typically delivered via mobile applications, web platforms, or connected physical devices. Applications include: mobile gaming, social and community platforms, digital entertainment and streaming, health and fitness applications, personal finance apps, productivity tools, dating and relationship apps, travel and hospitality platforms, food delivery and restaurant tech, and connected consumer hardware (wearables, smart home devices).

Key characteristics of the sector:
- Network effects are the primary moat in social, community, and marketplace applications
- Mobile-first distribution through app stores (Apple App Store, Google Play Store) creates both scale opportunity and platform dependency risk
- User acquisition economics (CAC, paid vs. organic ratio, viral coefficient) are primary early indicators of scalability
- Consumer attention is finite and competed for intensely — retention and engagement metrics are existential
- Revenue models vary widely: freemium, subscription, in-app purchases, advertising, marketplace commission
- The sector has the fastest feedback loops of any sector: product experiments can generate statistically significant results in days

#### 2.12.2 Expected Maturity at Application

- **Incubator / Pre-seed:** Mobile app or web platform live on app stores, 500–5,000 users, preliminary retention and engagement data
- **Seed stage:** 10,000–100,000 MAU, defined retention curve (D1/D7/D30), at least one revenue stream generating ≥$1K MRR, clear hypothesis on growth levers
- **Series A:** 500K–5M MAU or $1M+ ARR, proven retention, defined monetization model, payback period <12 months for paid channels

#### 2.12.3 Expected Financial Profile

| Stage | Monthly Burn | Expected Revenue | Key Metrics |
|---|---|---|---|
| Incubator | $10K–$40K | $0–$1K | Downloads, DAU, D1/D7 retention |
| Seed | $30K–$150K | $1K–$50K MRR | MAU, DAU/MAU ratio, LTV, CAC, churn |
| Series A | $100K–$500K | $50K–$500K MRR | ARPU, paid conversion rate, viral coefficient |
| Series B | $500K–$3M | $500K–$5M MRR | Revenue per MAU, LTV/CAC ratio, payback period |

**Engagement metrics are primary leading indicators:**
- **D1 retention:** % of users returning the day after first use. Strong: >40%; weak: <20%
- **D30 retention:** % of users returning 30 days after first use. Strong: >15%; weak: <5%
- **DAU/MAU ratio (Stickiness):** >25% is considered strong for most consumer apps
- **Viral coefficient (K-factor):** K > 1 indicates organic viral growth; K < 1 means the user base is not self-sustaining through referrals

#### 2.12.4 Expected Validation Cycle

| Validation Phase | Duration | Milestone |
|---|---|---|
| Product launch and initial users | 1–4 months | App store live; first 500–1,000 organic users |
| Retention validation | 2–6 months | D1/D7/D30 retention curves established from cohort data |
| Monetization validation | 3–9 months | First paying users; conversion funnel defined |
| Growth model validation | 6–18 months | Repeatable paid or organic growth channel identified |
| Scale preparation | 12–24 months | Infrastructure and team scaled ahead of exponential growth |

#### 2.12.5 Expected TRL Range

| TRL | Description | Expected at Stage |
|---|---|---|
| TRL 6 | App live; users engaged | Minimum for incubator consideration |
| TRL 7 | Demonstrated retention; monetization experiment | Seed stage |
| TRL 8 | Proven growth model; paying users | Strong for seed; pre-Series A |
| TRL 9 | Scaled commercial operation | Series A |

Consumer Tech startups below TRL 6 (no live product, no real users) are not ready for commercial evaluation. The barrier to building an MVP in Consumer Tech is lower than any other sector.

#### 2.12.6 Weight Adjustments

| Evaluation Pillar | Directive | Rationale |
|---|---|---|
| Traction | **Increase weight significantly** | Engagement, retention, and growth metrics are available and highly predictive |
| Market | **Increase weight** | Consumer market sizing must be realistic for the specific category; TAM overstatement is pervasive |
| Team | **Standard weight** | Product and growth expertise is critical; technical depth less so for most consumer apps |
| Technology / IP | **Reduce weight** | Consumer Tech moats come from brand, network effects, and UX, not patents |
| Financial Health | **Increase weight** | Unit economics (LTV/CAC, payback) are directly measurable and must be demonstrated |
| Regulatory | **Low weight (with exceptions)** | Most Consumer Tech is lightly regulated; exceptions include fintech features, health data |

#### 2.12.7 Evaluation Considerations

1. **Platform dependency risk:** Consumer apps distributed through Apple App Store and Google Play are subject to platform policy changes, 30% commission on in-app purchases, and the risk of app removal. Evaluators should assess the startup's exposure to platform risk and whether there are mitigating strategies (progressive web app, direct billing relationships).

2. **Category competition intensity:** Consumer Tech categories are frequently winner-take-all or winner-take-most. Evaluators must assess what defensible position the startup can occupy against well-funded incumbents in the same category.

3. **Content moderation liability (for social/UGC platforms):** Platforms with user-generated content carry content moderation obligations under IT Rules 2021 in India, DSA in Europe, and Section 230 concerns in the US. Evaluators should assess whether the startup has the moderation capability required for its content model.

4. **App store optimization and organic acquisition:** Evaluators should probe the startup's ASO (App Store Optimization) strategy and organic versus paid install ratio. Apps that are almost entirely dependent on paid acquisition for growth are structurally fragile.

5. **Subscription revenue quality:** For subscription Consumer Tech, the annual vs. monthly subscription mix matters significantly for cash flow. Annual subscriptions provide upfront cash and lower churn; monthly subscriptions have higher measured churn.

6. **Creator/content flywheel (for content platforms):** Platforms that depend on creator or user-generated content must assess the health of their content flywheel — whether the creator supply is growing, diversified, and producing content that retains audiences.

7. **Regulatory landscape for health/mental health apps:** Consumer health apps that make medical claims or process health data are subject to DPDP Act, HIPAA (if US-accessible), and potential CDSCO regulation as SaMD. Evaluators must assess whether health claims or data processing create regulatory obligations.

#### 2.12.8 Common Evaluation Errors

1. **Treating download counts as active user evidence.** Download numbers in Consumer Tech are meaningless without active user retention data. A 1-million-download app with 2% D30 retention has 20,000 active users, not 1 million. Evaluators frequently over-assess based on total downloads.

2. **Ignoring D30 retention in favor of D1.** D1 retention tests initial interest; D30 retention tests habit formation. Consumer apps with strong D1 but weak D30 (>30% D1, <5% D30) are experiencing a product-habit mismatch that is a strong negative signal for long-term growth.

3. **Accepting TAM without category-specific segmentation.** "The Indian mobile app market is worth $X billion" tells an evaluator nothing. Evaluators must require category-specific, bottom-up market sizing based on comparable apps' actual revenue data.

4. **Underweighting platform risk.** Apps built entirely on one platform (iOS or Android only, or monetized exclusively through in-app purchase without a web alternative) carry concentration risk that is frequently not quantified in standard evaluations.

---

### 2.13 D2C (Direct-to-Consumer)

#### 2.13.1 Sector Overview

Direct-to-Consumer (D2C) startups build branded product businesses that sell directly to end consumers, bypassing traditional retail intermediaries. This model has been enabled by digital marketing platforms (Meta, Google), e-commerce infrastructure (Shopify, Amazon, Meesho, Flipkart), and direct brand community building. D2C categories in India include: personal care and beauty, nutraceuticals and wellness, food and beverages (packaged, specialty, organic), apparel and fashion, home goods, pet care, and baby products.

Key characteristics:
- Brand building is the primary strategic activity — the product is often the vehicle, but the brand is the asset
- Customer Acquisition Cost (CAC), repeat purchase rate, and Customer Lifetime Value (LTV) are the central unit economics
- Gross margin management is critical: between raw material cost, packaging, fulfillment, and advertising spend, D2C gross margins in India typically range from 40–70%, with sustainable businesses targeting 50–65%
- Inventory management and working capital intensity are structural challenges, especially for product businesses
- Multi-channel evolution (D2C to omnichannel: own website + marketplaces + offline retail) is the typical growth trajectory
- Brand-to-shelf in India now takes 18–36 months: time to reach significant modern trade (MT) distribution

#### 2.13.2 Expected Maturity at Application

D2C startups should be expected to demonstrate commercial traction early. The barriers to launching a D2C brand are low (Shopify store, Instagram presence, white-label product), so the evaluation bar is rightly higher for commercial validation:

- **Incubator / Pre-seed:** Product launched, first sales (minimum ₹5–10L total revenue), defined brand positioning, initial digital presence
- **Seed stage:** ₹15–50L monthly revenue (GMV), repeat purchase rate >25%, CAC below gross margin per first order, a defined hero SKU with market feedback
- **Series A:** ₹1Cr–₹5Cr monthly revenue, repeat rate >35%, LTV/CAC > 3x, defined expansion strategy (new categories, new channels, or international)

#### 2.13.3 Expected Financial Profile

| Stage | Monthly Revenue (GMV) | Gross Margin | Key Metrics |
|---|---|---|---|
| Incubator | ₹2L–₹15L | 40–60% | First cohort repeat rate; CAC by channel |
| Seed | ₹15L–₹1Cr | 45–65% | CAC, LTV, repeat rate, return rate, contribution margin |
| Series A | ₹1Cr–₹10Cr | 50–70% | Net revenue retention; AOV growth; channel mix |
| Series B | ₹10Cr–₹100Cr | 55–70% | EBITDA margin progress; offline retail expansion |

**Critical D2C unit economics:**
- **Contribution Margin (CM1/CM2):** Revenue minus variable costs (COGS + fulfillment + marketing). CM1 > 0 is minimum for viability; CM2 > 0 means even central overhead allocation is covered per order
- **Repeat purchase rate:** % of customers making more than one purchase within 12 months. Below 25% indicates low product loyalty; above 40% indicates strong brand stickiness
- **Return rate:** E-commerce return rates in India average 20–30%. Startups with return rates above 35% have quality or expectation-setting issues
- **Working capital cycle:** Product businesses have negative working capital dynamics (pay for inventory before selling it). Evaluators must assess inventory turnover and working capital adequacy

#### 2.13.4 Expected Validation Cycle

| Validation Phase | Duration | Milestone |
|---|---|---|
| Product development and launch | 3–9 months | First SKU live; initial sales |
| Initial market validation | 3–6 months | First cohort of 100–500 customers; repeat purchase data |
| Brand-product fit | 6–18 months | Organic word-of-mouth; community growth; return customer rate |
| Channel expansion | 12–24 months | Marketplace presence (Amazon, Flipkart, Meesho); extended distribution |
| Offline retail entry | 24–48 months | Modern trade or general trade distribution; retail shelf presence |

#### 2.13.5 Expected TRL Range

TRL in the traditional sense is less applicable to D2C — there is no technology readiness ladder for a consumer product brand. However, TAES adapts TRL for D2C as a **Market Readiness Level** framework:

| MRL (TAES Adaptation) | Description | Expected at Stage |
|---|---|---|
| MRL 4 | Product formulated; initial customer testing | Incubator entry |
| MRL 5 | Product launched; first commercial sales | Seed-stage entry |
| MRL 6 | Hero SKU validated with repeat cohort data | Strong seed |
| MRL 7 | Multi-channel distribution; defined brand narrative | Pre-Series A |
| MRL 8 | Offline retail present; margin positive | Series A |
| MRL 9 | National omnichannel; brand defensible | Series B |

#### 2.13.6 Weight Adjustments

| Evaluation Pillar | Directive | Rationale |
|---|---|---|
| Traction | **Increase weight significantly** | Revenue, repeat rate, and CAC/LTV data are available and directly predictive of scale |
| Financial Health | **Increase weight significantly** | Gross margin, contribution margin, and working capital management are existential in D2C |
| Market | **Standard weight** | Category market size is relevant; brand differentiation within the category is the key question |
| Team | **Increase weight for brand** | Brand building, community management, and supply chain capability are rare combinations |
| Technology / IP | **Reduce weight significantly** | Product formula, design, and brand are the assets; patentable IP is rare in consumer products |
| Regulatory | **Context-specific** | FSSAI for food; CDSCO for cosmetics claiming drug-like effects; BIS for certain product categories |

#### 2.13.7 Evaluation Considerations

1. **Supply chain resilience and vendor concentration:** D2C businesses often source from 1–3 manufacturing partners. Concentration risk (one vendor going offline disrupts the entire business) must be assessed. Evaluators should probe vendor diversification strategy.

2. **Meta/Google ad dependence:** Many D2C brands are built almost entirely on paid social advertising. A business where >70% of revenue comes from Facebook/Instagram paid ads and no meaningful organic or community-driven acquisition exists is in a fragile position. Platform algorithm changes or CPM increases directly affect revenue.

3. **FSSAI / regulatory compliance for food and nutraceuticals:** D2C food and health supplement brands must comply with FSSAI licensing, labeling standards, and claims restrictions. Nutraceuticals making drug-like efficacy claims without proper FSSAI or CDSCO categorization carry regulatory risk.

4. **Return on ad spend (RoAS) trajectory:** As a D2C brand scales, performance marketing RoAS typically declines as the addressable audience saturates. Evaluators must probe the RoAS trend curve and whether the brand has a plan to build organic, community, or offline channels as paid marketing efficiency decreases.

5. **SKU rationalization and portfolio strategy:** D2C brands often launch with too many SKUs, diluting marketing spend and inventory capital. Evaluators should assess whether the brand has identified its hero SKU, is focused on building it, and has a rational new SKU introduction strategy.

6. **Quality consistency across manufacturing batches:** Consumer product quality variations across manufacturing batches drive negative reviews, returns, and brand damage. Evaluators should ask how quality control is managed, particularly as volume scales and manufacturing partners are added.

7. **D2C to retail transition economics:** The transition from pure D2C (direct shipping, full margin capture) to retail (distributor margin 20–30%, retailer margin 30–40%) dramatically affects gross margin. Evaluators must ensure the brand's margin structure is viable in offline retail and that pricing has been designed with full-channel economics in mind.

#### 2.13.8 Common Evaluation Errors

1. **Treating GMV as revenue.** D2C businesses often report GMV (total order value before returns). Net revenue (after returns, before COGS) is lower, and contribution margin (after COGS, fulfillment, and marketing) is the operationally relevant number. Evaluators who conflate GMV with revenue systematically overstate D2C financial health.

2. **Ignoring contribution margin in favor of gross margin.** Gross margin in D2C (revenue minus COGS) can look healthy at 55–60%, while contribution margin after fulfillment and marketing spend is negative. A D2C business with positive gross margin and negative contribution margin is losing money on every sale.

3. **Accepting repeat purchase rate claims without cohort data.** Repeat purchase rate must be calculated from a defined cohort (e.g., "of customers who made their first purchase in Q1 2024, what % made a second purchase within 12 months?"). Overall aggregate repeat purchase rates can be manipulated by timing and are not comparable across cohorts. Evaluators must require cohort-level data.

4. **Underestimating working capital requirements at scale.** D2C product businesses require increasing inventory investment as they scale. A business growing 3x in revenue typically requires 2.5–3x more working capital. Evaluators who do not model working capital requirements in growth scenarios miss a common D2C scaling failure mode.

5. **Over-indexing on social media following as brand validation.** Instagram followers and engagement metrics are leading indicators of brand interest, not lagging indicators of purchase intent. Evaluators who heavily weight social metrics over financial metrics overvalue early-stage D2C brand appeal at the expense of commercial viability.

---

## 3. Cross-Sector Evaluation

### 3.1 Overview

An increasing number of startup applications to incubators and funding programs cannot be cleanly assigned to a single sector classification. Common cross-sector cases include:

- **AI + FinTech (AI-powered lending, fraud detection):** The startup uses ML models (AI sector) to power a financial product (FinTech sector)
- **MedTech + AI (AI-powered diagnostic device):** The startup builds a physical medical device (MedTech) whose clinical function depends on an AI model (AI sector)
- **AgriTech + ClimateTech (carbon farming platform):** A platform that helps farmers optimize crop practices both for productivity (AgriTech) and for generating carbon credits (ClimateTech)
- **Defence + SpaceTech (satellite-based defence surveillance):** A payload or satellite system developed for defense applications
- **D2C + Consumer Tech (subscription app with physical product bundle):** A consumer brand that combines a physical product with an app-based subscription service

Cross-sector startups are common, growing, and must be handled explicitly rather than assigned to a single sector by default. Incorrect sector assignment is a primary source of evaluation error for multi-sector startups.

### 3.2 Cross-Sector Classification Protocol

When a startup operates across multiple sectors, the TAES engine applies the following protocol:

**Step 1: Primary Sector Identification**
Identify the sector from which the startup derives its primary value proposition — the core innovation or the primary customer value. This is the Primary Sector.

**Step 2: Secondary Sector Identification**
Identify any additional sectors that materially affect the startup's evaluation on at least two of the following dimensions: regulatory requirements, TRL expectations, validation cycle, financial metrics, or team expertise requirements. This is the Secondary Sector.

**Step 3: Weight Blending**
Construct a blended pillar weight vector using the following formula:

```
Blended Weight(pillar) = (Primary_Weight × α) + (Secondary_Weight × (1 - α))
```

Where `α` is the Primary Sector Attribution Factor, set by the evaluator based on the proportion of value created in the primary sector. Default value: α = 0.70 unless explicitly overridden with documented rationale.

**Step 4: Benchmark Selection**
For each evaluation dimension, select the benchmark from the sector whose standards are more demanding or more appropriate to the startup's actual situation. The "most demanding applicable benchmark" principle prevents cross-sector classification from being used to evade rigorous evaluation.

**Step 5: Regulatory Overlay**
Apply all regulatory requirements from both sectors. Cross-sector startups must meet regulatory obligations in every sector they operate in — there is no regulatory averaging. An AI-powered medical device must meet both FDA SaMD requirements and any applicable AI governance requirements.

### 3.3 Cross-Sector Evaluation Red Flags

Evaluators must be alert to the following patterns in cross-sector startups:

1. **Sector-hopping narrative:** A startup that repositions itself across multiple sectors to avoid the most demanding sector's standards. Each repositioning should trigger a re-evaluation using the new primary sector's standards without relaxing requirements from the previous sector.

2. **Regulatory gap exploitation:** A startup that uses a cross-sector label to argue it does not squarely fall under any specific regulator's jurisdiction. This is a red flag, not a competitive advantage.

3. **Misaligned team composition:** A cross-sector startup (e.g., AI + Biotech) that has a strong AI team but no clinical or regulatory expertise in its Biotech component is carrying a team capability gap that directly affects execution risk.

4. **Inconsistent TRL claims across sectors:** A startup that claims TRL 7 in its primary sector while the cross-sector component is at TRL 3 has an unresolved technical integration challenge that directly threatens the primary product.

---

## 4. Sector Classification Methodology

### 4.1 Overview

Accurate sector classification is a prerequisite for all TAES normalization to function correctly. The sector classification process is a three-layer mechanism that draws from structured data, document analysis, and AI inference, each with different confidence levels and review requirements.

### 4.2 Layer 1: Structured Field Classification

The highest-confidence classification source is the startup's self-declared sector from the application's structured data fields. TAES application forms present the following structured fields for sector classification:

- **Primary Sector** (required, single-select from the 13 TAES sectors)
- **Secondary Sector** (optional, single-select from the 13 TAES sectors)
- **Sub-sector** (optional free text, normalized post-input)
- **NAICS / NIC Code** (optional; automatically classified if provided)
- **Application Domain** (free text, used for secondary validation)

**Confidence Level:** High, subject to verification in document analysis.

**Override Conditions:** Structured classification is overridden if document analysis returns a contradicting classification with confidence > 85%, or if AI inference returns a contradicting classification with confidence > 90%, in both cases subject to evaluator review.

### 4.3 Layer 2: Document Analysis Classification

Document analysis operates on the uploaded pitch deck, product description, executive summary, and financial model. The classification system performs:

1. **Keyword extraction and frequency analysis** across a domain-specific lexicon for all 13 sectors
2. **Entity recognition** for regulatory bodies (FDA, RBI, ISRO, CDSCO, BIS), market identifiers, technical standards, and customer types
3. **Financial metric identification** — the presence of NIM, ARPU, AUM, burn rate, OEE, LCOE, and other sector-specific financial metrics signals sector alignment
4. **Citation pattern analysis** — references to specific regulatory filings, clinical trial identifiers, patent numbers, or government program names (iDEX, BIRAC, SBIR) provide strong sector signals

**Output:** A sector probability distribution across all 13 sectors with confidence scores.

**Minimum confidence threshold for automatic classification:** 80% on primary sector.

**Below-threshold action:** Request structured sector confirmation from the applicant, or flag for human evaluator review.

### 4.4 Layer 3: AI Inference Classification

When Layer 1 and Layer 2 produce conflicting or low-confidence classifications, the TAES AI inference module applies a multi-modal classification approach:

1. **Business model inference:** The revenue model described in the application is mapped to sector-characteristic models
2. **Customer archetype recognition:** The described customer base is matched against sector-typical customer profiles
3. **Technology stack inference:** Programming languages, hardware components, materials, or biological systems described are mapped to sector characteristics
4. **Team background inference:** Academic and professional backgrounds of founders are mapped to sector expertise profiles

**Output:** A ranked sector classification with confidence scores and evidence citations from the input documents.

**Human review requirement:** All AI-inferred sector classifications that override a structured field must be reviewed and confirmed by a human evaluator before scoring begins.

### 4.5 Classification Confidence Standards

| Classification Source | Confidence Threshold | Action |
|---|---|---|
| Structured field (self-declared) | N/A (accepted by default) | Verify via document analysis |
| Document analysis — primary sector | ≥ 80% | Auto-classify; note in metadata |
| Document analysis — primary sector | 60–79% | Confirm with AI inference; human review |
| Document analysis — primary sector | < 60% | Human review required before normalization |
| AI inference — override | ≥ 90% | Flag for human review; do not auto-override |
| AI inference — support | Any level | Use as evidence, not as primary classification |

### 4.6 Classification Audit Trail

Every sector classification decision must generate an audit record containing:

- `classification_timestamp`: ISO 8601 timestamp
- `classification_source`: structured_field | document_analysis | ai_inference | human_reviewer
- `primary_sector_id`: sector identifier
- `secondary_sector_id`: sector identifier or null
- `confidence_score`: 0.00–1.00
- `evidence_citations`: list of document excerpts supporting the classification
- `override_reason`: if structured field was overridden, the documented reason
- `human_reviewer_id`: if human review was conducted

This audit trail is retained with the evaluation record and available for quality assurance review.

---

## 5. Sector Normalization Configuration Model

### 5.1 Overview

The sector normalization configuration model defines how sector-specific parameters are stored, versioned, loaded, and applied at evaluation runtime. This model ensures that normalization is systematic, reproducible, and auditable.

### 5.2 Configuration Storage Architecture

Each sector configuration is stored as a versioned JSON/YAML document in the TAES normalization registry. The registry is a version-controlled repository (Git-based) with the following directory structure:

```
taes-normalization-registry/
├── sectors/
│   ├── ai_ml/
│   │   ├── config_v1.0.0.yaml
│   │   ├── config_v1.1.0.yaml
│   │   └── current.yaml  → symlink to active version
│   ├── saas_enterprise/
│   ├── deeptech_hardware/
│   ├── biotech/
│   ├── medtech/
│   ├── spacetech/
│   ├── defence_dualuse/
│   ├── agritech/
│   ├── climatetech_cleantech/
│   ├── fintech/
│   ├── manufacturing_i40/
│   ├── consumer_tech/
│   └── d2c/
├── cross_sector/
│   └── blending_rules.yaml
├── metadata/
│   └── registry_version.yaml
└── CHANGELOG.md
```

### 5.3 Sector Configuration File Structure

Each sector configuration file follows a standardized schema. A representative sector configuration (abbreviated for documentation clarity; full schema defined in TAES-SCHEMA-001) has the following structure:

```yaml
sector_id: "ai_ml"
sector_name: "AI / Machine Learning"
schema_version: "1.0.0"
config_version: "1.0.0"
effective_date: "2026-06-23"
reviewed_by:
  - domain: "AI/ML"
    reviewer_id: "SME-AI-001"
  - domain: "Venture Capital"
    reviewer_id: "VC-REVIEW-003"

pillar_weights:
  technology_ip: 0.28
  team: 0.22
  market: 0.18
  traction: 0.14
  financial_health: 0.10
  regulatory: 0.08
  weight_sum: 1.00
  notes: "Technology and team significantly weighted; traction and financial health reduced at early stage"

trl_benchmarks:
  incubator_entry:
    minimum: 3
    expected: 4
    strong: 5
  seed_stage:
    minimum: 4
    expected: 5
    strong: 6
  series_a:
    minimum: 6
    expected: 7
    strong: 8

financial_benchmarks:
  burn_rate:
    pre_seed:
      low: 5000    # USD/month
      high: 30000
    seed:
      low: 20000
      high: 80000
  revenue:
    pre_seed:
      expected: 0
      acceptable_max: 10000
    seed:
      expected_mrr_low: 0
      expected_mrr_high: 100000
  gross_margin_target:
    seed: 0.60
    series_a: 0.72
  compute_revenue_ratio:
    warning_threshold: 0.35
    critical_threshold: 0.50

validation_timeline:
  proof_of_concept:
    min_months: 1
    max_months: 4
  pilot_deployment:
    min_months: 2
    max_months: 6
  production_validation:
    min_months: 3
    max_months: 9
  market_validation:
    min_months: 6
    max_months: 18

lifecycle_expectations:
  incubator_programs:
    typical_stage: ["pre_product", "mvp_prototype"]
    acceptable_stage: ["ideation", "early_traction"]
  seed_funding:
    typical_stage: ["mvp_prototype", "early_traction"]
    acceptable_stage: ["pre_product"]
  series_a:
    typical_stage: ["early_traction", "growth"]
    minimum_required: "early_traction"

regulatory_flags:
  required_checks:
    - flag_id: "AI_GOVERNANCE_001"
      description: "EU AI Act risk classification assessment required for EU market"
      applies_if: "target_market includes EU"
    - flag_id: "DATA_PRIVACY_001"
      description: "Training data provenance and consent documentation required"
      applies_always: true
  conditional_checks:
    - flag_id: "SaMD_001"
      description: "FDA SaMD framework applies if AI application is diagnostic or treatment-related"
      applies_if: "application_domain includes healthcare"

sector_specific_metrics:
  required_for_financial_eval:
    - metric_id: "COMPUTE_REVENUE_RATIO"
      name: "Compute-to-Revenue Ratio"
      formula: "monthly_compute_cost / monthly_revenue"
      warning_threshold: 0.35
    - metric_id: "MODEL_PERFORMANCE_VALIDATED"
      name: "Model Performance Validation Flag"
      type: "boolean"
      description: "Has model performance been validated on live customer data (not benchmark datasets only)?"

red_flags:
  - flag_id: "RF_AI_001"
    description: "No proprietary training data; entirely dependent on public datasets"
    severity: "warning"
  - flag_id: "RF_AI_002"
    description: "No live customer usage; only benchmark evaluations presented"
    severity: "warning"
  - flag_id: "RF_AI_003"
    description: "Compute-to-revenue ratio exceeds 50% with no stated path to efficiency"
    severity: "critical"
  - flag_id: "RF_AI_004"
    description: "AI used in regulated domain with no explainability or bias assessment"
    severity: "critical"
```

### 5.4 Runtime Configuration Loading

At evaluation session initialization, the TAES engine executes the following configuration loading sequence:

1. **Resolve sector classification:** Read `primary_sector_id` and `secondary_sector_id` from the startup profile
2. **Load primary sector config:** Load `sectors/{primary_sector_id}/current.yaml` from the normalization registry
3. **Load secondary sector config (if applicable):** Load `sectors/{secondary_sector_id}/current.yaml`
4. **Apply blending rules (if cross-sector):** Load `cross_sector/blending_rules.yaml` and compute the blended weight vector using `α` (default 0.70, configurable)
5. **Resolve lifecycle stage:** Match the startup's declared and inferred lifecycle stage against `lifecycle_expectations` in the loaded config
6. **Initialize benchmark tables:** Load applicable benchmark ranges for burn rate, revenue, gross margin, and sector-specific metrics
7. **Apply regulatory flags:** Run all required checks from `regulatory_flags.required_checks`; run conditional checks where applicable
8. **Initialize red flag monitor:** Load `red_flags` into the evaluation session's active monitoring list
9. **Log session metadata:** Record the configuration version, sector IDs, blending α, and timestamp to the evaluation session audit record

### 5.5 Configuration Versioning and Governance

**Version format:** Semantic versioning (MAJOR.MINOR.PATCH)
- **MAJOR:** Changes to pillar weight structure, benchmark category additions, or red flag threshold changes with material scoring impact
- **MINOR:** New sector-specific metrics added, regulatory flag additions, benchmark range adjustments within ±10%
- **PATCH:** Documentation corrections, typo fixes, annotation updates

**Review and approval process:**
1. Proposed configuration changes are submitted as pull requests to the normalization registry
2. Each change must include a justification document referencing industry data, expert consultation, or policy changes
3. MAJOR and MINOR changes require review and sign-off by at least two domain-qualified SMEs and one TAES Working Group member
4. PATCH changes require review by one TAES Working Group member
5. All approved changes are tagged with the reviewer IDs and effective date
6. Configuration changes do not apply retroactively to evaluations completed before the effective date

**Annual review cycle:**
Each sector configuration undergoes a mandatory annual review in Q4 of each calendar year. The review assesses:
- Changes in sector-typical financial benchmarks (sourced from public investor reports, industry databases)
- Regulatory environment changes that affect required checks or red flags
- TRL benchmark recalibration based on cohort scoring data from the prior year
- Feedback from evaluators and domain experts who have used the configuration in the prior year

### 5.6 Configuration Override Policy

Individual evaluation session configurations may not be modified by evaluators without documented justification. The following override process applies:

1. Evaluator identifies a configuration parameter that is not appropriate for the specific startup being evaluated (e.g., a startup that operates in a highly unusual sub-sector with materially different characteristics)
2. Evaluator documents the override request in the evaluation session log, specifying: the parameter being overridden, the original configured value, the proposed override value, and the justification
3. Override request is reviewed and approved or rejected by a senior evaluator within the TAES Working Group
4. Approved overrides are recorded in the evaluation audit trail with the approver ID
5. Recurring override patterns for the same parameter trigger a configuration review proposal for that sector

Configuration overrides are tracked and analyzed in the annual review cycle to identify systematic gaps between the normalization configuration and observed startup realities.

### 5.7 Backward Compatibility and Evaluation Reproducibility

The TAES normalization registry maintains complete version history. For evaluation reproducibility:

- Every completed evaluation record stores the exact configuration version used (`normalization_config_version` field)
- A historical evaluation can be reproduced by loading the exact configuration version from the registry archive
- Cross-cohort score comparisons must account for configuration version differences when comparing scores produced under different versions
- Score migration (recomputing historical scores under a new configuration version) is only performed when explicitly authorized by the TAES Working Group and only for specific analytical purposes — never for individual startup re-ranking

---

*End of Document*

---

**Document Control**

| Field | Value |
|---|---|
| Document ID | TAES-v1.0-006 |
| Version | 1.0.0 |
| Status | Active |
| Author | TIDES Evaluation Engine Working Group |
| Effective Date | 2026-06-23 |
| Next Review Date | 2027-06-23 |
| Supersedes | None (initial version) |
| Classification | Internal Technical Standard |
| Distribution | TIDES Evaluation Team, Program Directors, Technical Advisory Board |

---

*This document is part of the TIDES AI Evaluation Standard (TAES) v1.0 documentation suite. It must be read in conjunction with TAES-v1.0-001 (Framework Overview), TAES-v1.0-002 (Scoring Methodology), TAES-v1.0-003 (TRL Reference Standard), TAES-v1.0-004 (Lifecycle Stage Definitions), and TAES-v1.0-005 (Pillar Weight Reference).*
