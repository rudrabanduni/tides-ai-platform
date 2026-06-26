import pytest
from uuid import uuid4
from typing import Any
from datetime import datetime

from app.modules.intelligence.events import dispatcher
from app.modules.intelligence.models import StartupIntelligenceProfile
from app.services.ai.schemas import AICompletionResult, AICompletionMetadata
from app.services.ai.exceptions import AIProviderError

from app.modules.evaluation.product_expert import ProductExpert
from app.modules.evaluation.schemas import (
    AgentAssessment,
    Observation,
    Risk,
    Question,
    ConfidenceHierarchy,
    MissingEvidence
)


# --- Mock AI Gateway for Testing ---
class MockAIGateway:
    def __init__(self, mock_result: Any = None, should_fail: bool = False) -> None:
        self.mock_result = mock_result
        self.should_fail = should_fail
        self.last_request = None

    def complete_json(self, request: Any, response_model: type) -> Any:
        self.last_request = request
        if self.should_fail:
            raise AIProviderError("Gateway timeout simulating provider failure")
        return self.mock_result


@pytest.fixture
def mock_profile() -> StartupIntelligenceProfile:
    class DummyProfile:
        id = uuid4()
        startup_id = uuid4()
    return DummyProfile()


@pytest.fixture
def mock_claims() -> list[Any]:
    class DummyField:
        def __init__(self, key: str):
            self.field_key = key

    class DummyClaim:
        def __init__(self, id: Any, field_key: str, val: Any, conf: float):
            self.id = id
            self.field = DummyField(field_key)
            self.value_string = val if isinstance(val, str) else None
            self.value_number = val if isinstance(val, (int, float)) else None
            self.value_boolean = val if isinstance(val, bool) else None
            self.value_json = val if isinstance(val, (dict, list)) else None
            self.value_date = None
            self.confidence_score = conf
            self.validation_status = "VALIDATED"

    return [
        DummyClaim("claim-product-1", "product_description", "AI powered startup analytics", 0.9),
        DummyClaim("claim-product-2", "problem_statement", "SME funding is extremely slow", 0.8),
    ]


@pytest.fixture
def mock_evidence() -> list[Any]:
    class DummyEvidence:
        def __init__(self, id: str, claim_id: str, document_id: str):
            self.id = id
            self.claim_id = claim_id
            self.document_id = document_id
            self.evidence_snippet = "AI powered startup analytics"
            self.section_name = "Product Overview"
            self.page_number = 1

    return [
        DummyEvidence("evidence-product-1", "claim-product-1", "doc-product-1"),
        DummyEvidence("evidence-product-2", "claim-product-2", "doc-product-1"),
    ]


@pytest.fixture
def valid_product_assessment() -> AgentAssessment:
    return AgentAssessment(
        domain="product",
        summary="Product problem clarity is high.",
        observations=[
            Observation(
                observation_id="OBS-PRODUCT-001",
                observation="Solves a clear speed problem for SME funding.",
                claim_ids=["claim-product-1"],
                evidence_ids=["evidence-product-1"],
                reasoning="Automation of workflow reduces ingestion times.",
                confidence=0.9
            )
        ],
        risks=[
            Risk(
                id="RISK-PRODUCT-001",
                description="Integration overhead with legacy bank APIs.",
                severity="High",
                likelihood="Medium",
                impact="High",
                mitigation="Use pre-built open banking adapters.",
                supporting_observations=["OBS-PRODUCT-001"],
                supporting_claims=["claim-product-1"],
                supporting_evidence=["evidence-product-1"]
            )
        ],
        questions=[
            Question(
                id="QST-PRODUCT-001",
                question="What legacy core banking systems are supported?",
                purpose="To verify technical compatibility and scalability.",
                priority="Medium",
                expected_evidence="API documentation",
                blocking=False,
                generated_by="product"
            )
        ],
        confidence=ConfidenceHierarchy(
            finding_confidence=0.9,
            evidence_confidence=0.85,
            reasoning_confidence=0.9,
            overall_domain_confidence=0.88
        ),
        reasoning="Product shows clear differentiation and solid initial validation.",
        missing_evidence=[
            MissingEvidence(
                description="API integration maps",
                importance="Medium",
                expected_document="Technical Architecture Document"
            )
        ],
        prompt_name="Product Analysis Prompt",
        prompt_version="1.0.0",
        prompt_hash="dummy-hash",
        agent_version="1.0.0",
        generated_at=datetime.utcnow()
    )


def test_product_expert_success(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_product_assessment: AgentAssessment
) -> None:
    completion_result = AICompletionResult(
        data=valid_product_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = ProductExpert(gateway=gateway)

    emitted_events = []
    def track_events(evt: Any) -> None:
        emitted_events.append(evt)

    dispatcher.register("ProductAssessmentStarted", track_events)
    dispatcher.register("ProductAssessmentCompleted", track_events)
    dispatcher.register("ProductAssessmentFailed", track_events)

    try:
        assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})

        assert assessment is not None
        assert len(assessment.observations) == 1
        assert assessment.confidence.overall_domain_confidence == 0.88
        assert len(assessment.questions) == 1
        assert assessment.questions[0].blocking is False

        assert len(emitted_events) == 2
        assert emitted_events[0].event_name == "ProductAssessmentStarted"
        assert emitted_events[0].payload["startup_id"] == str(mock_profile.startup_id)
        assert emitted_events[1].event_name == "ProductAssessmentCompleted"
        assert emitted_events[1].payload["startup_id"] == str(mock_profile.startup_id)

    finally:
        dispatcher.unregister("ProductAssessmentStarted", track_events)
        dispatcher.unregister("ProductAssessmentCompleted", track_events)
        dispatcher.unregister("ProductAssessmentFailed", track_events)


def test_product_expert_empty_profile() -> None:
    expert = ProductExpert(gateway=MockAIGateway())
    
    with pytest.raises(ValueError, match="Startup Intelligence Profile is missing"):
        expert.evaluate(None, [], [], [], {})

    class DummyProfile:
        startup_id = uuid4()
    
    with pytest.raises(ValueError, match="Claims context must be provided"):
        expert.evaluate(DummyProfile(), None, [], [], {})


def test_product_expert_gateway_failure(mock_profile: Any, mock_claims: list[Any]) -> None:
    gateway = MockAIGateway(should_fail=True)
    expert = ProductExpert(gateway=gateway)

    emitted_events = []
    def track_events(evt: Any) -> None:
        emitted_events.append(evt)

    dispatcher.register("ProductAssessmentStarted", track_events)
    dispatcher.register("ProductAssessmentFailed", track_events)

    try:
        with pytest.raises(AIProviderError):
            expert.evaluate(mock_profile, mock_claims, [], [], {})

        assert len(emitted_events) == 2
        assert emitted_events[0].event_name == "ProductAssessmentStarted"
        assert emitted_events[1].event_name == "ProductAssessmentFailed"
        assert "timeout" in emitted_events[1].payload["error"].lower()

    finally:
        dispatcher.unregister("ProductAssessmentStarted", track_events)
        dispatcher.unregister("ProductAssessmentFailed", track_events)


def test_product_expert_malformed_response(mock_profile: Any, mock_claims: list[Any]) -> None:
    from pydantic import BaseModel
    class DummyModel(BaseModel):
        test: str
        
    completion_result = AICompletionResult(
        data=DummyModel(test="malformed"),
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=10.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = ProductExpert(gateway=gateway)

    with pytest.raises(ValueError, match="AI Gateway response data is not a valid AgentAssessment"):
        expert.evaluate(mock_profile, mock_claims, [], [], {})


def test_product_expert_ontology_violation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_product_assessment: AgentAssessment
) -> None:
    # Introduce scoring/verdict term in reasoning
    valid_product_assessment.reasoning = "We recommend funding approval based on score."
    
    completion_result = AICompletionResult(
        data=valid_product_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = ProductExpert(gateway=gateway)

    from app.modules.evaluation.validation.validation_exceptions import AssessmentValidationError
    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert any("Ontology breach" in err for err in exc_info.value.errors)

