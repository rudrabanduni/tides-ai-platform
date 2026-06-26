import pytest
from uuid import uuid4
from typing import Any
from datetime import datetime

from app.modules.intelligence.events import dispatcher
from app.modules.intelligence.models import StartupIntelligenceProfile
from app.services.ai.schemas import AICompletionResult, AICompletionMetadata
from app.services.ai.exceptions import AIProviderError

from app.modules.evaluation.financial_expert import FinancialExpert
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
        DummyClaim("claim-fin-1", "burn_rate", "50,000 USD/month", 0.9),
        DummyClaim("claim-fin-2", "runway", "12 months", 0.8),
    ]


@pytest.fixture
def mock_evidence() -> list[Any]:
    class DummyEvidence:
        def __init__(self, id: str, claim_id: str, document_id: str):
            self.id = id
            self.claim_id = claim_id
            self.document_id = document_id
            self.evidence_snippet = "Runway is 12 months based on burn"
            self.section_name = "Financial Summary"
            self.page_number = 3

    return [
        DummyEvidence("evidence-fin-1", "claim-fin-1", "doc-fin-1"),
        DummyEvidence("evidence-fin-2", "claim-fin-2", "doc-fin-1"),
    ]


@pytest.fixture
def valid_financial_assessment() -> AgentAssessment:
    return AgentAssessment(
        domain="financial",
        summary="Runway is stable but capital efficiency can be improved.",
        observations=[
            Observation(
                observation_id="OBS-FIN-001",
                observation="Monthly burn rate is 50,000 USD with 12 months runway.",
                claim_ids=["claim-fin-1"],
                evidence_ids=["evidence-fin-1"],
                reasoning="Longer runway reduces near-term insolvency risks.",
                confidence=0.9
            )
        ],
        risks=[
            Risk(
                id="RISK-FIN-001",
                description="High burn relative to early validation traction.",
                severity="High",
                likelihood="Medium",
                impact="High",
                mitigation="Reduce non-essential contractor spend.",
                supporting_observations=["OBS-FIN-001"],
                supporting_claims=["claim-fin-1"],
                supporting_evidence=["evidence-fin-1"]
            )
        ],
        questions=[
            Question(
                id="QST-FIN-001",
                question="What is the detailed breakdown of the cost structure?",
                purpose="To verify software licensing versus staffing costs.",
                priority="Medium",
                expected_evidence="Detailed budget sheet",
                blocking=False,
                generated_by="financial"
            )
        ],
        confidence=ConfidenceHierarchy(
            finding_confidence=0.9,
            evidence_confidence=0.8,
            reasoning_confidence=0.9,
            overall_domain_confidence=0.87
        ),
        reasoning="Runway is moderate, requiring funding efforts in parallel.",
        missing_evidence=[
            MissingEvidence(
                description="Cost structure detailed sheet",
                importance="Medium",
                expected_document="Operating Budget"
            )
        ],
        prompt_name="Financial Analysis Prompt",
        prompt_version="1.0.0",
        prompt_hash="dummy-hash",
        agent_version="1.0.0",
        generated_at=datetime.utcnow()
    )


def test_financial_expert_success(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_financial_assessment: AgentAssessment
) -> None:
    completion_result = AICompletionResult(
        data=valid_financial_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = FinancialExpert(gateway=gateway)

    emitted_events = []
    def track_events(evt: Any) -> None:
        emitted_events.append(evt)

    dispatcher.register("FinancialAssessmentStarted", track_events)
    dispatcher.register("FinancialAssessmentCompleted", track_events)
    dispatcher.register("FinancialAssessmentFailed", track_events)

    try:
        assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})

        assert assessment is not None
        assert assessment.domain == "financial"
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
        assert emitted_events[0].event_name == "FinancialAssessmentStarted"
        assert emitted_events[0].payload["startup_id"] == str(mock_profile.startup_id)
        assert emitted_events[1].event_name == "FinancialAssessmentCompleted"
        assert emitted_events[1].payload["startup_id"] == str(mock_profile.startup_id)

    finally:
        dispatcher.unregister("FinancialAssessmentStarted", track_events)
        dispatcher.unregister("FinancialAssessmentCompleted", track_events)
        dispatcher.unregister("FinancialAssessmentFailed", track_events)


def test_financial_expert_empty_profile() -> None:
    expert = FinancialExpert(gateway=MockAIGateway())
    
    with pytest.raises(ValueError, match="Startup Intelligence Profile is missing"):
        expert.evaluate(None, [], [], [], {})

    class DummyProfile:
        startup_id = uuid4()
    
    with pytest.raises(ValueError, match="Claims context must be provided"):
        expert.evaluate(DummyProfile(), None, [], [], {})


def test_financial_expert_gateway_failure(mock_profile: Any, mock_claims: list[Any]) -> None:
    gateway = MockAIGateway(should_fail=True)
    expert = FinancialExpert(gateway=gateway)

    emitted_events = []
    def track_events(evt: Any) -> None:
        emitted_events.append(evt)

    dispatcher.register("FinancialAssessmentStarted", track_events)
    dispatcher.register("FinancialAssessmentFailed", track_events)

    try:
        with pytest.raises(AIProviderError):
            expert.evaluate(mock_profile, mock_claims, [], [], {})

        assert len(emitted_events) == 2
        assert emitted_events[0].event_name == "FinancialAssessmentStarted"
        assert emitted_events[1].event_name == "FinancialAssessmentFailed"
        assert "timeout" in emitted_events[1].payload["error"].lower()

    finally:
        dispatcher.unregister("FinancialAssessmentStarted", track_events)
        dispatcher.unregister("FinancialAssessmentFailed", track_events)


def test_financial_expert_malformed_response(mock_profile: Any, mock_claims: list[Any]) -> None:
    from pydantic import BaseModel
    class DummyModel(BaseModel):
        test: str
        
    completion_result = AICompletionResult(
        data=DummyModel(test="malformed"),
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=10.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = FinancialExpert(gateway=gateway)

    with pytest.raises(ValueError, match="AI Gateway response data is not a valid AgentAssessment"):
        expert.evaluate(mock_profile, mock_claims, [], [], {})


def test_financial_expert_ontology_violation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_financial_assessment: AgentAssessment
) -> None:
    # Prohibited funding verdict term in reasoning
    valid_financial_assessment.reasoning = "We recommend funding approval based on burn rate."
    
    completion_result = AICompletionResult(
        data=valid_financial_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = FinancialExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert any("Ontology breach" in err for err in exc_info.value.errors)


def test_financial_expert_confidence_validation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_financial_assessment: AgentAssessment
) -> None:
    # Set invalid overall confidence score
    valid_financial_assessment.confidence.overall_domain_confidence = 1.5
    
    completion_result = AICompletionResult(
        data=valid_financial_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = FinancialExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert any("Confidence score" in err for err in exc_info.value.errors)


def test_financial_expert_traceability_validation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_financial_assessment: AgentAssessment
) -> None:
    # Set an unlinked claim id to breach traceability rules
    valid_financial_assessment.observations[0].claim_ids = ["unlinked-claim-id"]
    
    completion_result = AICompletionResult(
        data=valid_financial_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = FinancialExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert any("Broken Reference" in err for err in exc_info.value.errors)


def test_financial_expert_registry_discovery() -> None:
    registry = AgentRegistry()
    count = discover_and_register_experts(registry)
    
    assert count >= 4
    assert registry.exists("FinancialExpert")
    assert registry.exists("MarketExpert")
    assert registry.exists("FounderExpert")
    assert registry.exists("ProductExpert")
    
    assert registry.get("FinancialExpert") is FinancialExpert
