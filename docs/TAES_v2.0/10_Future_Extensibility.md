# TAES Common Evaluation Ontology: 10_Future Extensibility

The TAES Multi-Agent Evaluation Framework is designed for dynamic extensibility. Adding new expert agents requires **zero** modifications to the registry, database, or existing execution pipelines.

---

## 1. How to Add a New Domain Agent

Developers can introduce new expert agents in three simple steps:

### Step 1: Subclass `BaseAgent`
Create a new agent file in `app/modules/evaluation/agents/` (e.g. `esg_agent.py`) and inherit from `BaseAgent`:

```python
from app.modules.evaluation.agents.base_agent import BaseAgent
from app.modules.evaluation.schemas import AgentAssessment

class ESGAgent(BaseAgent):
    def validate_inputs(self, profile, claims, evidence, conflicts, doc_metadata) -> bool:
        # Verify if ESG-related claims exist in the profile
        return True

    def build_prompt(self, profile, claims, evidence, conflicts, doc_metadata) -> tuple[str, str]:
        system_prompt = "You are an ESG Incubation expert. Analyze environmental, social, and governance footprint..."
        user_prompt = self.generate_reasoning(profile, claims, evidence, conflicts, doc_metadata)
        return system_prompt, user_prompt
```

### Step 2: Register in `__init__.py`
Register the new agent with the dynamic registry in `app/modules/evaluation/agents/__init__.py`:

```python
from app.modules.evaluation.agents.agent_registry import AgentRegistry
from app.modules.evaluation.agents.esg_agent import ESGAgent

registry = AgentRegistry()
registry.register("esg", ESGAgent)
```

### Step 3: Run the Pipeline
The next execution of the evaluation pipeline will automatically discover, instantiate, and invoke the new agent, merging its `AgentAssessment` into the consensus context.

---

## 2. Examples of Future Agents

* **Legal Agent**: Analyzes company incorporation documents, founder vesting agreements, and legal dispute histories.
* **Manufacturing Agent**: Analyzes bill of materials (BOM), production scalability, and supply chain bottlenecks.
* **ESG Agent**: Evaluates carbon footprint, social impact metrics, diversity indices, and corporate governance practices.
* **Grant Agent**: Focuses on eligibility for government incubation schemes, science fund grants, and academic support.
* **Cybersecurity Agent**: Analyzes codebase audits, data protection compliance (e.g. GDPR/DPDP), and server vulnerabilities.
* **Regulatory Agent**: Focuses on compliance certifications, clinical trial guidelines, or environmental clearances.
* **International Expansion Agent**: Evaluates compliance and readiness for global scaling.
* **Policy Agent**: Assesses public policy risks, government tariff implications, or trade limitations.
