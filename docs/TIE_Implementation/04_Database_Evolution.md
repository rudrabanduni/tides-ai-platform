# Database Evolution: TIDES Intelligence Engine (TIE)

> **Document:** TIE Integration / Database Evolution  
> **Classification:** Internal Engineering Standard  
> **Version:** 1.0.0  
> **Date:** June 24, 2026

This document specifies the database migration and evolution plan for integrating the TIDES Intelligence Engine (TIE). It reviews existing schemas and designs additive, backward-compatible tables, index optimizations, caching strategies, and multi-tenant scaling models.

---

## 1. Schema Architecture Overview

To ensure zero downtime and prevent breaking existing functionality, TIE introduces **purely additive schema expansions**. Existing tables are unchanged, and new capabilities (such as knowledge graphs, agent execution logs, and normalized benchmarks) are implemented in new tables linked by foreign keys.

```
       +------------------------------------------------------+
       |                  startup_applications                |
       +--------------------------+---------------------------+
                                  |
         +------------------------+------------------------+
         | 1                                               | 1
         v                                                 v
+--------+-----------+                             +-------+-----------+
|  startup_profiles  |                             |    evaluations    |
+--------+-----------+                             +-------+-----------+
         |                                                 |
         | 1..*                                            | 1..*
         v                                                 v
+--------+-----------+                             +-------+-----------+
|  profile_versions  |                             | evaluation_scores |
+--------------------+                             +-------+-----------+
                                                           |
                                                           | 1..*
                                                           v
                                                   +-------+-----------+
                                                   |  evaluation_evid  |
                                                   +-------------------+
                                                             ▲
                                                             │ 1..*
                                                             │ (New Association)
=============================================================│=========================
TIE ADDITIVE LAYER                                           │
                                                             │
+--------------------+             +-------------------+     │
| knowledge_g_nodes  |<----------->| knowledge_g_edges |     │
+--------------------+ 1..*   1..* +-------------------+     │
         ▲                                                   │
         │ 1..*                                              │
         v                                                   │
+--------------------+                                       │
|    documents       |---------------------------------------+
+--------------------+ 1
         ▲
         │ 1..*
         v
+--------------------+             +-------------------+
|   tie_agent_runs   |             |  sector_benchmark |
+--------------------+             +-------------------+
```

---

## 2. Additive Schema Definitions

### 2.1 Agent Run Logging (`tie_agent_runs`)
This table tracks individual agent execution attempts within a multi-agent run. It logs prompt versions, latencies, API costs, token usage, and errors, serving as a core monitoring tool for the AI Orchestration layer.

```sql
CREATE TYPE agent_run_status AS ENUM ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED');

CREATE TABLE tie_agent_runs (
    id UUID PRIMARY KEY,
    evaluation_id UUID NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    agent_name VARCHAR(128) NOT NULL,
    status agent_run_status NOT NULL DEFAULT 'PENDING',
    prompt_version VARCHAR(64) NOT NULL,
    inputs JSONB,
    outputs JSONB,
    token_count_prompt INTEGER,
    token_count_completion INTEGER,
    api_cost NUMERIC(10, 6),
    latency_ms INTEGER,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT uq_agent_run_eval_agent UNIQUE (evaluation_id, agent_name, prompt_version)
);
```

### 2.2 Knowledge Graph Nodes (`knowledge_graph_nodes`)
Stores key entities extracted from startup applications and documents (e.g., founders, competitors, market metrics, IP patents) as nodes in a graph.

```sql
CREATE TABLE knowledge_graph_nodes (
    id UUID PRIMARY KEY,
    startup_id UUID NOT NULL REFERENCES startup_applications(id) ON DELETE CASCADE,
    node_type VARCHAR(64) NOT NULL, -- e.g., 'FOUNDER', 'COMPETITOR', 'TRL_METRIC', 'IP_ASSET'
    label VARCHAR(255) NOT NULL,
    properties JSONB NOT NULL DEFAULT '{}',
    source_document_id UUID REFERENCES documents(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 2.3 Knowledge Graph Edges (`knowledge_graph_edges`)
Stores directional relationships between entities (e.g., founder "co_founded" startup, startup "competes_with" competitor).

```sql
CREATE TABLE knowledge_graph_edges (
    id UUID PRIMARY KEY,
    startup_id UUID NOT NULL REFERENCES startup_applications(id) ON DELETE CASCADE,
    source_node_id UUID NOT NULL REFERENCES knowledge_graph_nodes(id) ON DELETE CASCADE,
    target_node_id UUID NOT NULL REFERENCES knowledge_graph_nodes(id) ON DELETE CASCADE,
    relationship_type VARCHAR(64) NOT NULL, -- e.g., 'CO_FOUNDED_WITH', 'COMPETES_IN', 'INVENTED'
    properties JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT chk_self_loop CHECK (source_node_id <> target_node_id)
);
```

### 2.4 Sector Benchmarks (`sector_benchmarks`)
Holds historical metrics and aggregates per industry sector, enabling normalizations without running heavy analytics queries during evaluations.

```sql
CREATE TABLE sector_benchmarks (
    id UUID PRIMARY KEY,
    sector VARCHAR(64) UNIQUE NOT NULL, -- e.g., 'AI_ML', 'BIOTECH', 'SAAS'
    cohort_count INTEGER NOT NULL DEFAULT 0,
    averages JSONB NOT NULL, -- e.g., {"founder": 7.2, "product": 6.8}
    standard_deviations JSONB NOT NULL, -- e.g., {"founder": 1.1, "product": 1.3}
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

### 2.5 Evaluation Cohorts (`evaluation_cohorts`)
Groups multiple startup applications (e.g., "TIDES Summer 2026 Batch") to calculate ranking lists and run comparative analytics.

```sql
CREATE TABLE evaluation_cohorts (
    id UUID PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

---

## 3. Schema Extensions to Existing Tables

To link new features, the following columns are added to existing tables:

1.  **`evaluations` Table:**
    - Add `normalized_score` (`FLOAT`, nullable) - to store normalized rating.
    - Add `normalized_scores_snapshot` (`JSONB`, nullable) - breakdown of normalized scores.
    - Add `cohort_id` (`UUID`, FK to `evaluation_cohorts.id`, nullable) - to assign evaluations to cohorts.
2.  **`evaluation_evidence` Table:**
    - Add `text_block_coordinate` (`VARCHAR(128)`, nullable) - to store paragraph or vector references inside a document.

---

## 4. Indexing Strategy

To maintain sub-second API responses as data scales, the following database indexes are required:

1.  **Agent Runs Logs:**
    - `CREATE INDEX idx_tie_runs_eval_status ON tie_agent_runs (evaluation_id, status);`
    - Speeds up status checks and aggregations during orchestrations.
2.  **Knowledge Graph Queries:**
    - `CREATE INDEX idx_kg_nodes_startup_type ON knowledge_graph_nodes (startup_id, node_type);`
    - Accelerates entity searches during evaluation contexts.
    - `CREATE INDEX idx_kg_edges_source ON knowledge_graph_edges (source_node_id);`
    - `CREATE INDEX idx_kg_edges_target ON knowledge_graph_edges (target_node_id);`
    - Speeds up relational traversals of nodes.
3.  **JSONB Operations:**
    - `CREATE INDEX idx_kg_nodes_properties_gin ON knowledge_graph_nodes USING gin (properties);`
    - Enables indexing inside JSONB property maps.

---

## 5. Caching Layer Architecture

TIE uses a **Redis caching layer** to store slow-changing metrics and avoid database roundtrips:

```
                  +-----------------------------------+
                  |             API Request           |
                  +-----------------+-----------------+
                                    |
                    Cache Hit?      v
             +----------------------+----------------------+
             | Yes                                         | No
             v                                             v
+------------+------------+                  +------------+------------+
|    Return Redis Data    |                  | Query PostgreSQL/SQLite |
+-------------------------+                  +------------+------------+
                                                          |
                                                          v
                                             +------------+------------+
                                             |  Write to Cache & Return|
                                             +-------------------------+
```

### Cache Key Definitions
- **Sector Benchmarks:** `cache:sector_benchmarks:{sector_name}`
  - *TTL:* 24 Hours.
  - *Invalidation:* Automatically cleared when a new evaluation is finalized in that sector.
- **Cohort Stats:** `cache:cohort:{cohort_id}:stats`
  - *TTL:* 1 Hour.
  - *Invalidation:* Cleared when evaluations are finalized or added to a cohort.
- **Extracted Profiles:** `cache:startup_profiles:{startup_id}`
  - *TTL:* 30 Days.
  - *Invalidation:* Cleared when the startup profile is updated by a user.

---

## 6. Multi-Tenant Scalability (PostgreSQL Migration)

As TIDES transitions from SQLite to a PostgreSQL SaaS model, the following database design choices are implemented:

1.  **Row-Level Multi-Tenancy:** Every tenant record contains an `organization_id` column. Views and API routes query tables using filters on this tenant identifier.
2.  **Schema Isolation (Optional):** Large enterprise customers use isolated database schemas (`tenant_1_schema`, `tenant_2_schema`). TIE routes connection pools dynamically based on client authentication payloads.
3.  **Database Connection Pooling:** Integrates `pgbouncer` to manage connection limits during concurrent agent executions, preventing database socket exhaustion.
