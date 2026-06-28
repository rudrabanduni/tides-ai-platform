import json
import time
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel, ValidationError

from app.services.ai.exceptions import AIResponseParseError
from app.services.ai.schemas import AICompletionMetadata, AICompletionRequest, AICompletionResult


ResponseFactory = Callable[[AICompletionRequest], dict[str, Any] | BaseModel]


class MockAIGateway:
    """Deterministic AI gateway for development and tests."""

    provider_name = "mock"

    def __init__(
        self,
        *,
        model: str = "mock-model",
        response_factory: ResponseFactory | None = None,
        fixed_response: dict[str, Any] | BaseModel | None = None,
        latency_ms: float = 0.0,
    ) -> None:
        self._model = model
        self._response_factory = response_factory
        self._fixed_response = fixed_response
        self._latency_ms = latency_ms

    def complete_json(
        self,
        request: AICompletionRequest,
        response_model: type[BaseModel],
    ) -> AICompletionResult[BaseModel]:
        started = time.perf_counter()
        
        schema_name = response_model.__name__
        if schema_name == "StartupProfileExtraction" and self._response_factory is None and self._fixed_response is None:
            user_prompt_lower = request.user_prompt.lower()
            if "cleanenergy" in user_prompt_lower or "hydrogen" in user_prompt_lower:
                data = response_model(
                    company_name="CleanEnergy Corp",
                    founders=["John Doe", "Jane Smith"],
                    founder_roles=["Co-Founder & CEO", "Co-Founder & CTO"],
                    problem_statement="Industrial power grid outages cost billions.",
                    solution="Modular hydrogen fuel cells for backup industrial power.",
                    technology="Proprietary hydrogen fuel cell stack.",
                    patents="Two patents filed for cell stack design.",
                    market="Clean energy storage and backup power market.",
                    market_size="$12 Billion globally",
                    business_model="Hardware sales plus maintenance contracts.",
                    revenue_model="High margin hardware sales.",
                    competition="Diesel generators and hydrogen battery rivals.",
                    traction="TRL 6 readiness level validated in pilot.",
                    team="Founders have 15 years experience in clean technology.",
                    financial_information="Pre-revenue; raised $2.5 Million seed funding.",
                    funding_ask="$2.5 Million seed",
                    funding_raised="$2.5 Million",
                    current_revenue="$0.0",
                    burn_rate="Not specified",
                    runway="24 months"
                )
            elif "petrevolt" in user_prompt_lower:
                data = response_model(
                    company_name="PETREVOLT ENERGY SOLUTIONS PVT LTD",
                    founders=["Princya Polin S", "Ashwin Kumar P"],
                    founder_roles=["Co-Founder & CEO", "Co-Founder & CTO"],
                    problem_statement="India depends on imported lithium-ion batteries, creating high costs and supply chain risk.",
                    solution="Solid-state sodium-ion batteries manufactured from recycled PET plastic waste.",
                    technology="Solid-state sodium-ion battery using disodium terephthalate derived from PET solvolysis.",
                    patents="Patent applied for PET to liquid electrolyte conversion mechanism.",
                    market="Electric 2W and 3W manufacturers seeking low-cost LFP alternatives.",
                    market_size="1.3 TWh India battery storage demand by 2047",
                    business_model="B2B battery cell sales to EV OEMs and stationary storage integrators.",
                    revenue_model="Per-unit cell sales with long-term supply agreements.",
                    competition="Imported lithium-ion battery suppliers and emerging domestic SIB players.",
                    traction="Rechargeable PoC demonstrating reversible Na-ion intercalation built and patent applied.",
                    team="Founders have domain expertise in electrochemistry and battery prototype validation.",
                    financial_information="Pre-revenue; seeking seed investment for solid-state sodium R&D.",
                    funding_ask="Rs 5 crore seed round",
                    funding_raised="None",
                    current_revenue="0.0",
                    burn_rate="Not specified",
                    runway="Not specified"
                )
            else:
                from app.modules.ai.gateway.provider import generate_mock_pydantic
                data = generate_mock_pydantic(response_model)
            raw_text = data.model_dump_json()
        elif schema_name == "AgentAssessment" and self._response_factory is None and self._fixed_response is None:
            domain = "founder"
            if request.metadata and request.metadata.get("domain") and request.metadata.get("domain") != "evaluation":
                domain = request.metadata.get("domain")
            elif request.system_prompt:
                sys_prompt_lower = request.system_prompt.lower()
                if "financial" in sys_prompt_lower:
                    domain = "financial"
                elif "trl" in sys_prompt_lower:
                    domain = "trl"
                elif "competition" in sys_prompt_lower:
                    domain = "competition"
                elif "ip" in sys_prompt_lower:
                    domain = "ip"
                elif "risk" in sys_prompt_lower:
                    domain = "risk"
                elif "founder" in sys_prompt_lower:
                    domain = "founder"
                elif "market" in sys_prompt_lower:
                    domain = "market"
                elif "product" in sys_prompt_lower:
                    domain = "product"
            from app.services.ai.real_pipeline import generate_assessment_from_context
            data = generate_assessment_from_context(request.user_prompt, domain, response_model)
            raw_text = data.model_dump_json()
        else:
            payload = self._resolve_payload(request)
            raw_text = self._serialize_payload(payload)
            try:
                if isinstance(payload, BaseModel):
                    data = response_model.model_validate(payload.model_dump())
                else:
                    if not payload and response_model.model_fields:
                        from app.modules.ai.gateway.provider import generate_mock_pydantic
                        data = generate_mock_pydantic(response_model)
                    else:
                        data = response_model.model_validate(payload)
            except ValidationError as exc:
                raise AIResponseParseError("Response does not match the expected schema") from exc

        elapsed_ms = self._latency_ms or ((time.perf_counter() - started) * 1000)
        metadata = AICompletionMetadata(
            model=request.model or self._model,
            provider=self.provider_name,
            latency_ms=round(elapsed_ms, 3),
            prompt_version=request.prompt_version,
        )
        return AICompletionResult(data=data, metadata=metadata, raw_text=raw_text)

    def _resolve_payload(self, request: AICompletionRequest) -> dict[str, Any] | BaseModel:
        if self._response_factory is not None:
            return self._response_factory(request)
        if self._fixed_response is not None:
            return self._fixed_response
        return {}

    @staticmethod
    def _serialize_payload(payload: dict[str, Any] | BaseModel) -> str:
        if isinstance(payload, BaseModel):
            return payload.model_dump_json()
        return json.dumps(payload)

