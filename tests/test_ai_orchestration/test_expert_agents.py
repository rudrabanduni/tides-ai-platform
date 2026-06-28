import pytest
from app.modules.ai.agents.founder_agent import FounderExpert
from app.modules.ai.agents.product_agent import ProductExpert
from app.modules.ai.agents.market_agent import MarketExpert
from app.modules.ai.agents.models import AgentAssessment
from app.modules.ai.orchestrator.context import build_context
from app.modules.ai.gateway.gateway import AIGateway
from app.modules.ai.prompts.registry import PromptRegistry

def test_expert_agents_initialization():
    founder = FounderExpert()
    product = ProductExpert()
    market = MarketExpert()
    
    assert founder.agent_name == "FounderExpert"
    assert "FounderExpert" in product.dependencies
    assert "ProductExpert" in market.dependencies
    
    assert "founders" in founder.relevant_fields
    assert "product_roadmap" in product.relevant_fields
    assert "gtm" in market.relevant_fields

@pytest.mark.anyio
async def test_expert_agents_run():
    gateway = AIGateway()
    prompt_registry = PromptRegistry()
    
    founder = FounderExpert()
    product = ProductExpert()
    market = MarketExpert()
    
    startup_profile = {"id": "startup-123", "name": "AI Startup"}
    claims = [{"id": "c1", "field_key": "founders", "value_string": "Experienced team"}]
    evidence = [{"id": "e1", "claim_id": "c1", "evidence_snippet": "Founded 2 startups"}]
    
    context = build_context(
        startup_profile=startup_profile,
        claims=claims,
        evidence=evidence,
        previous_outputs={},
        relevant_fields=founder.relevant_fields
    )
    
    # Test Founder Expert execution
    founder_result = await founder.run(context, gateway, prompt_registry)
    assert isinstance(founder_result, AgentAssessment)
    assert founder_result.domain == "founder"
    assert founder_result.overall_score == 0.95
    assert len(founder_result.observations) > 0
    
    # Test Product Expert execution
    context_prod = build_context(
        startup_profile=startup_profile,
        claims=claims,
        evidence=evidence,
        previous_outputs={"FounderExpert": founder_result.model_dump()},
        relevant_fields=product.relevant_fields
    )
    product_result = await product.run(context_prod, gateway, prompt_registry)
    assert isinstance(product_result, AgentAssessment)
    assert product_result.domain == "product"
    
    # Test Market Expert execution
    context_mkt = build_context(
        startup_profile=startup_profile,
        claims=claims,
        evidence=evidence,
        previous_outputs={"ProductExpert": product_result.model_dump()},
        relevant_fields=market.relevant_fields
    )
    market_result = await market.run(context_mkt, gateway, prompt_registry)
    assert isinstance(market_result, AgentAssessment)
    assert market_result.domain == "market"
