import pytest
from uuid import uuid4
from typing import Any
from datetime import datetime

from app.modules.intelligence.events import dispatcher
from app.modules.intelligence.models import StartupIntelligenceProfile
from app.services.ai.schemas import AICompletionResult, AICompletionMetadata
from app.services.ai.exceptions import AIProviderError

from app.modules.evaluation.market_expert import MarketExpert
from app.modules.evaluation.schemas import (
    AgentAssessment,
    Observation,
    Risk,
    Question,
    ConfidenceHierarchy,
    MissingEvidence
)
from app.modules.evaluation.registry import AgentRegistry, discover_and_register_experts
from app.modules.evaluation.validation.validation_exceptions import AssessmentValidationError


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
        DummyClaim("claim-market-1", "tam", "10 Billion USD", 0.9),
        DummyClaim("claim-market-2", "market_growth", "CAGR of 15%", 0.8),
    ]


@pytest.fixture
def mock_evidence() -> list[Any]:
    class DummyEvidence:
        def __init__(self, id: str, claim_id: str, document_id: str):
            self.id = id
            self.claim_id = claim_id
            self.document_id = document_id
            self.evidence_snippet = "10 Billion USD TAM"
            self.section_name = "Market Size"
            self.page_number = 2

    return [
        DummyEvidence("evidence-market-1", "claim-market-1", "doc-market-1"),
        DummyEvidence("evidence-market-2", "claim-market-2", "doc-market-1"),
    ]


@pytest.fixture
def valid_market_assessment() -> AgentAssessment:
    return AgentAssessment(
        domain="market",
        summary="Market size is large with attractive growth prospects.",
        observations=[
            Observation(
                observation_id="OBS-MARKET-001",
                observation="TAM is estimated at 10 Billion USD.",
                claim_ids=["claim-market-1"],
                evidence_ids=["evidence-market-1"],
                reasoning="Calculated using top-down analysis from industry reports.",
                confidence=0.9
            )
        ],
        risks=[
            Risk(
                id="RISK-MARKET-001",
                description="High market entry barriers due to legacy systems.",
                severity="Medium",
                likelihood="Medium",
                impact="Medium",
                mitigation="Target niche early adopters first.",
                supporting_observations=["OBS-MARKET-001"],
                supporting_claims=["claim-market-1"],
                supporting_evidence=["evidence-market-1"]
            )
        ],
        questions=[
            Question(
                id="QST-MARKET-001",
                question="What are the specific SOM targets for year 1?",
                purpose="To verify immediate execution plan viability.",
                priority="High",
                expected_evidence="Business plan document",
                blocking=False,
                generated_by="market"
            )
        ],
        confidence=ConfidenceHierarchy(
            finding_confidence=0.9,
            evidence_confidence=0.8,
            reasoning_confidence=0.9,
            overall_domain_confidence=0.87
        ),
        reasoning="Strong growth CAGR and validation signals reduce timing risk.",
        missing_evidence=[
            MissingEvidence(
                description="Year 1 SOM calculations",
                importance="High",
                expected_document="Financial projection deck"
            )
        ],
        prompt_name="Market Analysis Prompt",
        prompt_version="1.0.0",
        prompt_hash="dummy-hash",
        agent_version="1.0.0",
        generated_at=datetime.utcnow()
    )


def test_market_expert_success(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_market_assessment: AgentAssessment
) -> None:
    completion_result = AICompletionResult(
        data=valid_market_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = MarketExpert(gateway=gateway)

    emitted_events = []
    def track_events(evt: Any) -> None:
        emitted_events.append(evt)

    dispatcher.register("MarketAssessmentStarted", track_events)
    dispatcher.register("MarketAssessmentCompleted", track_events)
    dispatcher.register("MarketAssessmentFailed", track_events)

    try:
        assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})

        assert assessment is not None
        assert assessment.domain == "market"
        assert len(assessment.observations) == 1
        assert assessment.confidence.overall_domain_confidence == 0.87
        assert len(assessment.questions) == 1
        
        # Verify prompt metadata injection
        assert assessment.prompt_name is not None
        assert assessment.prompt_version is not None
        assert assessment.prompt_hash is not None
        assert assessment.agent_version == "1.0.0"
        assert assessment.generated_at is not None

        # Verify event emission
        assert len(emitted_events) == 2
        assert emitted_events[0].event_name == "MarketAssessmentStarted"
        assert emitted_events[0].payload["startup_id"] == str(mock_profile.startup_id)
        assert emitted_events[1].event_name == "MarketAssessmentCompleted"
        assert emitted_events[1].payload["startup_id"] == str(mock_profile.startup_id)

    finally:
        dispatcher.unregister("MarketAssessmentStarted", track_events)
        dispatcher.unregister("MarketAssessmentCompleted", track_events)
        dispatcher.unregister("MarketAssessmentFailed", track_events)


def test_market_expert_empty_profile() -> None:
    expert = MarketExpert(gateway=MockAIGateway())
    
    with pytest.raises(ValueError, match="Startup Intelligence Profile is missing"):
        expert.evaluate(None, [], [], [], {})

    class DummyProfile:
        startup_id = uuid4()
    
    with pytest.raises(ValueError, match="Claims context must be provided"):
        expert.evaluate(DummyProfile(), None, [], [], {})


def test_market_expert_gateway_failure(mock_profile: Any, mock_claims: list[Any]) -> None:
    gateway = MockAIGateway(should_fail=True)
    expert = MarketExpert(gateway=gateway)

    emitted_events = []
    def track_events(evt: Any) -> None:
        emitted_events.append(evt)

    dispatcher.register("MarketAssessmentStarted", track_events)
    dispatcher.register("MarketAssessmentFailed", track_events)

    try:
        with pytest.raises(AIProviderError):
            expert.evaluate(mock_profile, mock_claims, [], [], {})

        assert len(emitted_events) == 2
        assert emitted_events[0].event_name == "MarketAssessmentStarted"
        assert emitted_events[1].event_name == "MarketAssessmentFailed"
        assert "timeout" in emitted_events[1].payload["error"].lower()

    finally:
        dispatcher.unregister("MarketAssessmentStarted", track_events)
        dispatcher.unregister("MarketAssessmentFailed", track_events)


def test_market_expert_malformed_response(mock_profile: Any, mock_claims: list[Any]) -> None:
    from pydantic import BaseModel
    class DummyModel(BaseModel):
        test: str
        
    completion_result = AICompletionResult(
        data=DummyModel(test="malformed"),
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=10.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = MarketExpert(gateway=gateway)

    with pytest.raises(ValueError, match="AI Gateway response data is not a valid AgentAssessment"):
        expert.evaluate(mock_profile, mock_claims, [], [], {})


def test_market_expert_ontology_violation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_market_assessment: AgentAssessment
) -> None:
    # Prohibited rating/verdict term in reasoning
    valid_market_assessment.reasoning = "The score shows high viability and we decide to accept it."
    
    completion_result = AICompletionResult(
        data=valid_market_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = MarketExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert any("Ontology breach" in err for err in exc_info.value.errors)


def test_market_expert_confidence_validation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_market_assessment: AgentAssessment
) -> None:
    # Set invalid overall confidence score
    valid_market_assessment.confidence.overall_domain_confidence = 1.5
    
    completion_result = AICompletionResult(
        data=valid_market_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = MarketExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert any("Confidence score" in err for err in exc_info.value.errors)


def test_market_expert_traceability_validation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_market_assessment: AgentAssessment
) -> None:
    # Set an unlinked claim id to breach traceability rules
    valid_market_assessment.observations[0].claim_ids = ["unlinked-claim-id"]
    
    completion_result = AICompletionResult(
        data=valid_market_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = MarketExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert any("Broken Reference" in err for err in exc_info.value.errors)


def test_market_expert_registry_discovery() -> None:
    registry = AgentRegistry()
    count = discover_and_register_experts(registry)
    
    assert count >= 3
    assert registry.exists("MarketExpert")
    assert registry.exists("FounderExpert")
    assert registry.exists("ProductExpert")
    
    assert registry.get("MarketExpert") is MarketExpert
