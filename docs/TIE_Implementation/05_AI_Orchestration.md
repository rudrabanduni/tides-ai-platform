# AI Orchestration: TIDES Intelligence Engine (TIE)

> **Document:** TIE Integration / AI Orchestration  
> **Classification:** Internal Engineering Standard  
> **Version:** 1.0.0  
> **Date:** June 24, 2026

This document defines the architecture of the AI Orchestration layer in the TIDES Intelligence Engine (TIE). It outlines how specialized evaluation agents communicate, coordinate, handle errors, optimize costs, and aggregate scoring confidence, establishing human-in-the-loop review boundaries without implementing code or prompt logic.

---

## 1. Centralized State DAG Orchestrator

TIE uses a **Centralized State DAG Orchestrator** to run assessments. The orchestrator maintains an in-memory execution state, tracking which tasks have completed, which are running, and what data dependencies remain.

```
                  +-----------------------------------+
                  |        [1] Start Evaluation       |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  |     [2] Knowledge Extraction      |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  |       [3] Knowledge Graph         |
                  +--------+-----------------+--------+
                           |                 |
         +-----------------+                 +-----------------+
         v                                                     v
+------------------+                                  +------------------+
| Founder Agent    |                                  |   Product Agent  |
+--------+---------+                                  +--------+---------+
         |                                                     |
         +-----------------+                 +-----------------+
                           |                 |
                           v                 v
                  +-----------------------------------+
                  |         [4] Evidence Engine       |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  |      [5] Evaluation Agents        |
                  |     (Market, Fin, Risk, IP)       |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  |       [6] Scoring Engine          |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  |    [7] Normalisation Engine       |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  |   [8] Recommendation Engine       |
                  +-----------------+-----------------+
                                    |
                                    v
                  +-----------------------------------+
                  |      [9] PDF Report Gen           |
                  +-----------------------------------+
```

### Dependency Rules:
1.  **Knowledge Extraction** must complete before constructing the **Knowledge Graph**.
2.  **Evidence Engine** runs next, verifying text snippets against the graph.
3.  **Founder & Product Agents** run in parallel as they only depend on extracted profiles.
4.  **Market, Financial, Risk, and IP Agents** run in parallel after the Product Agent completes, consuming product definitions.
5.  **Scoring & Normalization Engines** run sequentially once all domain agents complete.
6.  **Recommendation Engine** runs after normalizations.
7.  **PDF Report Gen** runs last.

---

## 2. Parallel Execution & Event Communication

### Asyncio Task Groups
The Orchestrator utilizes Python's asynchronous event loops (`asyncio.TaskGroup`) to manage concurrent LLM calls. This prevents threads from blocking during network wait times, allowing up to 10 agents to run in parallel.

### Communication Pattern
Agents do not communicate directly. They use a **Pub/Sub Broker** pattern via an event bus:
- Every agent is triggered by a specific event (e.g., `STARTUP_PROFILE_READY`).
- Upon completion, the agent publishes a structured event payload (e.g., `FOUNDER_EVALUATION_COMPLETED`).
- The Orchestrator listens to these events, updates the run log, and triggers downstream dependencies.

---

## 3. Resiliency & Failure Recovery

```
                      +-----------------------------+
                      |       Call LLM API          |
                      +--------------+--------------+
                                     |
                       Success?      v
                 +-------------------+-------------------+
                 | Yes                                   | No
                 v                                       v
     +-----------+-----------+               +-----------+-----------+
     |   Return JSON Result  |               |  Exponential Backoff  |
     +-----------------------+               |      (Tenacity)       |
                                             +-----------+-----------+
                                                         |
                                           Success?      v
                                     +-------------------+-------------------+
                                     | Yes                                   | No (Max Retries)
                                     v                                       v
                         +-----------+-----------+               +-----------+-----------+
                         |   Return JSON Result  |               | Fallback Provider/Mod |
                         +-----------------------+               +-----------+-----------+
                                                                             |
                                                               Success?      v
                                                         +-------------------+-------------------+
                                                         | Yes                                   | No
                                                         v                                       v
                                             +-----------+-----------+               +-----------+-----------+
                                             |   Return JSON Result  |               | Assign Default Score  |
                                             +-----------------------+               |   & Flag for Review   |
                                                                                     +-----------------------+
```

### Retry Strategy
- Integrates `tenacity` for model API calls.
- **Backoff Method:** Exponential backoff (`wait_exponential(multiplier=1, min=2, max=10)`).
- **Max Retries:** 3 attempts.
- **Failures handled:** Network timeouts, HTTP 429 (Rate Limits), HTTP 503 (Overloaded API).

### Model Failover
If the primary model API fails after 3 retries, the orchestrator switches to a fallback model:
1.  *Primary:* Anthropic Claude 3.5 Sonnet (`claude-3-5-sonnet-20241022`).
2.  *Secondary:* Azure OpenAI GPT-4o (`gpt-4o`).
3.  *Tertiary:* Google Vertex Gemini 1.5 Pro (`gemini-1.5-pro`).

### Partial Run Preservation
If a critical failure occurs during execution, the orchestrator saves all completed agent scores. When restarted, it resumes the evaluation from the failed node, avoiding duplicate API calls and costs.

---

## 4. Cost Optimization & Model Routing

### Model Routing Matrix
To manage LLM costs, tasks are routed to models based on complexity:

| Agent / Service | Complexity | Primary Model Routing | Fallback Model Routing |
| :--- | :--- | :--- | :--- |
| **Knowledge Extraction** | Medium | GPT-4o-mini | Llama-3-8B (Self-hosted) |
| **Founder Agent** | Medium | Claude 3.5 Sonnet | GPT-4o-mini |
| **Product Agent** | Medium | Claude 3.5 Sonnet | GPT-4o-mini |
| **Market Agent** | High | Claude 3.5 Sonnet | GPT-4o |
| **Financial Agent** | High | Claude 3.5 Sonnet | GPT-4o |
| **IP / Patent Agent** | High | Claude 3.5 Sonnet | GPT-4o |
| **Risk Agent** | High | Claude 3.5 Sonnet | GPT-4o |
| **Recommendation Engine** | Medium | GPT-4o-mini | Claude 3.5 Haiku |

### Prompt Caching
- Enables prompt caching (e.g., Anthropic Prompt Caching) for system prompts and rubrics, reducing input token costs by up to 50% for repeated assessments.
- Compresses document texts by removing boilerplates (disclaimers, headers) before feeding them into prompt contexts.

---

## 5. Confidence Aggregation Methodology

Confidence scores are not simple averages. They are calculated dynamically using the following hierarchical method:

```
[Overall Confidence: 0.77]
   ├── [Founder Pillar: 0.85] (Weight: 15%)
   │      ├── Evidence Completeness: 0.90
   │      └── Source Integrity: 0.80
   └── [IP Pillar: 0.60] (Weight: 10%)
          ├── Evidence Completeness: 0.40
          └── Source Integrity: 0.80 (Missing Primary Patent Docs)
```

1.  **Confidence Dimensions:** Every agent outputs two confidence values:
    - *Evidence Completeness (0.0 - 1.0):* Measures whether all primary evidence items were present.
    - *Source Integrity (0.0 - 1.0):* Derived from the document trust rating (e.g., government registry is 1.0, founder self-statement is 0.5).
2.  **Pillar-Level Aggregation:** Derived as the product of completeness and source integrity:
    $$\text{Pillar Confidence} = \text{Completeness} \times \text{Source Integrity}$$
3.  **Overall Confidence Aggregation:** Calculated as the weighted sum of pillar confidence values:
    $$\text{Overall Confidence} = \frac{\sum (\text{Pillar Confidence} \times \text{Pillar Weight})}{\sum \text{Pillar Weight}}$$
4.  **Evidence Penalties:** If key documents (e.g., financials, patent filings) are missing, the overall confidence is penalized by a multiplier (e.g., $\times\ 0.80$).

---

## 6. Human-in-the-Loop (HITL) Review Boundaries

TIE enforces three distinct system boundaries where human reviews and approvals are required:

1.  **Low Confidence Triggers:** If the overall evaluation confidence falls below **0.60**, the evaluation is set to `NEEDS_REVIEW` status. The system flags the scorecard in the dashboard, indicating which evidence gaps caused the low rating.
2.  **Significant Discrepancy Alerts:** If a reviewer overrides a pillar score by more than **2.0 points** compared to the agent's proposed score, the evaluation is flagged. The reviewer must select a reason code and link the override to a specific document section.
3.  **Final Approval Gate:** No recommendation is finalized automatically. Recommendations generated by TIE are marked as "Recommendations." The status is updated to `FINALIZED` only after a program manager signs off via the route `POST /api/v1/reviews/{evaluation_id}/approve`.
