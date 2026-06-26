# Data Flow Architecture: TIDES Intelligence Engine (TIE)

> **Document:** TIE Integration / Data Flow Architecture  
> **Classification:** Internal Engineering Standard  
> **Version:** 1.0.0  
> **Date:** June 24, 2026

This document designs the future data flow pipeline of the TIDES Intelligence Engine (TIE) integration. It outlines the end-to-end data lifecycle from startup ingestion to cohort benchmarking and analytics, specifying the input/output contracts and recovery procedures for each transition.

---

## 1. Architectural Data Pipeline

The data pipeline processes unstructured and structured startup applications through a series of enrichment, extraction, evaluation, and synthesis stages:

```
[Startup Upload]
      │
      ▼ (Excel / ZIP / PDF Ingestion)
[Knowledge Extraction] 
      │
      ▼ (Extracted Entities: Founders, Tech, Finances)
[Knowledge Graph] 
      │
      ▼ (Queried Entities, Relationships, & Context)
[Evidence Engine] 
      │
      ▼ (Segmented & Verified Text Snippets)
[Evaluation Agents] 
      │
      ▼ (Pillar-Specific Analyses & Scoring Proposals)
[Scoring Engine] 
      │
      ▼ (Weighted Pillar Scores & Aggregated Confidence)
[Normalization Engine] 
      │
      ▼ (Normalized Scores against Sector Benchmarks)
[Recommendation Engine] 
      │
      ▼ (Actionable Recommendations, Red Flags, & Roadmap)
[Report Generator] ───► [Dashboard] ───► [Benchmark Database] ───► [Analytics]
 (PDF/Web Output)      (Cohort Leaderboard)    (Historical Scores)      (Aggregated Insights)
```

---

## 2. Pipeline Transitions and Contracts

### 2.1 Startup Upload ──► Knowledge Extraction
*   **Description:** The startup registers via Excel sheet intake or document upload (PDF/Word/ZIP pitch decks, financial templates). Uploading triggers a background task that reads file streams and updates the document status to `UPLOADED`.
*   **Process:** The system extracts the file metadata and sends the document bytes to the file parsing queue.
*   **Input Data:** Excel spreadsheet row values or multipart binary file streams.
*   **Output Data (Contract):**
    ```json
    {
      "startup_id": "uuid-v4-string",
      "documents": [
        {
          "document_id": "uuid-v4-string",
          "file_path": "uploads/uuid/deck.pdf",
          "document_type": "pitch_deck",
          "status": "UPLOADED"
        }
      ]
    }
    ```
*   **Failure Recovery:** If file uploads fail (e.g., due to format errors or connection loss), the status is marked as `FAILED`. A notification is sent to the user, and files are cleaned up to prevent disk clutter.

---

### 2.2 Knowledge Extraction ──► Knowledge Graph
*   **Description:** The Knowledge Extraction Agent processes the uploaded files to extract key startup metrics, entity definitions, and operational details.
*   **Process:** The agent uses LLM completion with Pydantic output schemas to extract structured details from unstructured document text. These extracted entities (e.g., team completeness, intellectual property, target market size) are mapped into database records.
*   **Input Data:** Parsed plain text chunks from documents.
*   **Output Data (Contract):**
    ```json
    {
      "startup_id": "uuid-v4-string",
      "extracted_entities": {
        "founders": [{"name": "Jane Doe", "role": "CEO", "experience": "5 years ML"}],
        "product": {"description": "SaaS Platform", "trl_proposed": 4},
        "market": {"tam": 12000000000, "sam": 450000000, "som": 50000000},
        "financials": {"revenue_y1": 0, "funding_raised": 50000}
      }
    }
    ```
*   **Failure Recovery:** If formatting or extraction fails, the system falls back to a rule-based parser that reads the Excel application sheet, marking missing document values as "Unknown" with a confidence score of 0.0.

---

### 2.3 Knowledge Graph ──► Evidence Engine
*   **Description:** Extracted entities are linked in a relational network (representing the startup's Knowledge Graph) to map connections between founders, target markets, competitor matrices, and technologies.
*   **Process:** Entity properties are registered in the relational database. The Evidence Engine queries this graph to locate supporting text segments within the source documents that validate these entities.
*   **Input Data:** Extracted entities and document coordinates.
*   **Output Data (Contract):**
    ```json
    {
      "startup_id": "uuid-v4-string",
      "graph_context": {
        "nodes": [
          {"id": "node_1", "label": "Jane Doe", "type": "FOUNDER"},
          {"id": "node_2", "label": "Competitor X", "type": "COMPETITOR"}
        ],
        "edges": [
          {"source": "node_1", "target": "node_2", "relationship": "COMPETED_WITH"}
        ]
      }
    }
    ```
*   **Failure Recovery:** If the graph query returns empty results, the Evidence Engine performs a fallback regex and semantic search over the raw `parsed_text` in the `documents` table to locate relevant paragraphs.

---

### 2.4 Evidence Engine ──► Evaluation Agents
*   **Description:** Segmented text blocks, cited document passages, and entity records are packaged into a structured context object and routed to domain-specific evaluation agents.
*   **Process:** The Evidence Engine generates a schema-validated prompt payload. It routes the payload to the respective agents (Founder Agent, Product Agent, Market Agent, etc.) based on the target rubric criteria.
*   **Input Data:** Segmented text chunks and citation references.
*   **Output Data (Contract):**
    ```json
    {
      "evaluation_id": "uuid-v4-string",
      "criteria": [
        {
          "criterion_id": "uuid-v4-string",
          "name": "Founder Domain Expertise",
          "context_citations": [
            {
              "source_id": "uuid-v4-string",
              "snippet": "Jane Doe led AI research at X Corp for 4 years.",
              "page": 12,
              "confidence": 0.95
            }
          ]
        }
      ]
    }
    ```
*   **Failure Recovery:** If the prompt payload exceeds context limits, the engine applies text summarization to compact the context, prioritizing sections that contain direct keyword matches.

---

### 2.5 Evaluation Agents ──► Scoring Engine
*   **Description:** Individual domain agents analyze their assigned criteria, assign preliminary scores (0–10), and provide supporting reasoning based on the cited evidence.
*   **Process:** Domain agents evaluate the criteria and submit their structured evaluation proposals to the Scoring Engine.
*   **Input Data:** Domain evaluations and confidence scores.
*   **Output Data (Contract):**
    ```json
    {
      "evaluation_id": "uuid-v4-string",
      "agent_proposals": [
        {
          "agent_name": "FounderEvaluationAgent",
          "pillar": "Founder",
          "proposed_score": 8.0,
          "confidence": 0.90,
          "reasoning": "Strong team background with clear technical credentials.",
          "citations": ["evidence_id_1"]
        }
      ]
    }
    ```
*   **Failure Recovery:** If an agent fails to return a valid response, the Scoring Engine triggers a retry using a fallback model. If the retry fails, the engine assigns a default score of 0.0 with a confidence rating of 0.0, flagging the record for manual review.

---

### 2.6 Scoring Engine ──► Normalization Engine
*   **Description:** The Scoring Engine aggregates the domain-specific scores, applying the rubric's configured weights to calculate overall pillar scores and the baseline evaluation rating.
*   **Process:** The Scoring Engine persists the scores in the database and routes the raw score matrix to the Normalization Engine.
*   **Input Data:** Aggregated raw scores and pillar weights.
*   **Output Data (Contract):**
    ```json
    {
      "evaluation_id": "uuid-v4-string",
      "raw_scores": {
        "Founder": 8.0,
        "Product": 7.0,
        "Technology": 6.0,
        "Market": 8.0,
        "BusinessModel": 7.0,
        "Financial": 5.0,
        "IP": 8.0,
        "Risk": 6.0
      },
      "overall_raw_score": 68.75
    }
    ```
*   **Failure Recovery:** If the overall score cannot be calculated (e.g., due to missing pillar weights), the engine rolls back the evaluation transaction, logs an validation error, and resets the evaluation status to `FAILED`.

---

### 2.7 Normalization Engine ──► Recommendation Engine
*   **Description:** The Normalization Engine adjusts the raw scores using sector-specific configurations and cohort averages, preventing startups in complex industries (like Biotech) from being penalized compared to faster-scaling sectors (like SaaS).
*   **Process:** The engine applies normalization formulas using cohort statistics and outputs the normalized score matrix.
*   **Input Data:** Raw scores and sector profile configuration.
*   **Output Data (Contract):**
    ```json
    {
      "evaluation_id": "uuid-v4-string",
      "raw_scores": {"Founder": 8.0, "Product": 7.0},
      "normalized_scores": {
        "Founder": 8.5,
        "Product": 8.0,
        "Technology": 7.5,
        "Market": 8.2,
        "BusinessModel": 7.0,
        "Financial": 6.5,
        "IP": 9.0,
        "Risk": 7.0
      },
      "overall_normalized_score": 77.12
    }
    ```
*   **Failure Recovery:** If sector profile data is missing, the Normalization Engine bypasses adjustment, setting the normalized scores equal to the raw scores and logging a system warning.

---

### 2.8 Recommendation Engine ──► Report Generator & Dashboard
*   **Description:** The Recommendation Engine processes the normalized score matrix, confidence scores, and risk flags to determine the incubation recommendation and generate a list of actionable improvements.
*   **Process:** The engine queries `recommendation_rules` to find score matches and compiles the final recommendation model.
*   **Input Data:** Normalized scores, confidence levels, and risk metrics.
*   **Output Data (Contract):**
    ```json
    {
      "evaluation_id": "uuid-v4-string",
      "overall_score": 77.12,
      "recommendation": "Incubate",
      "confidence": 0.88,
      "red_flags": ["No registered incorporation details"],
      "improvement_roadmap": [
        {"pillar": "Financial", "action": "Define pricing strategy", "priority": "CRITICAL"}
      ]
    }
    ```
*   **Failure Recovery:** If recommendation logic fails, the system applies a default recommendation of "Conditional Review," logs the failure, and flags the evaluation for manual admin intervention.

---

### 2.9 Report Generator ──► PDF / Web Output
*   **Description:** The Report Generator compiles the evaluation scores, agent summaries, citations, risk matrices, and recommendations into standard formats.
*   **Process:** The generator builds a structured ReportLab document flow asynchronously and writes the PDF bytes to file storage.
*   **Input Data:** Comprehensive evaluation records, recommendations, and evidence logs.
*   **Output Data (Contract):** PDF bytes written to `uploads/uuid/report_v1.pdf` and status updated to `COMPLETED`.

---

### 2.10 Dashboard & Rankings ──► Benchmark Database & Analytics
*   **Description:** Finalized evaluation details, sector tags, and stage metrics are sent to the benchmarking database to update global cohort averages.
*   **Process:** The system calculates updated statistics (means, standard deviations) for the cohort and updates the analytics database.
*   **Input Data:** Finalized scoring matrices and metadata.
*   **Output Data (Contract):** Updated sector benchmark tables.
