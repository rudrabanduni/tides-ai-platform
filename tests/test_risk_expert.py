import pytest
from uuid import uuid4
from typing import Any
from datetime import datetime

from app.modules.intelligence.events import dispatcher
from app.modules.intelligence.models import StartupIntelligenceProfile
from app.services.ai.schemas import AICompletionResult, AICompletionMetadata
from app.services.ai.exceptions import AIProviderError

from app.modules.evaluation.risk_expert import RiskExpert
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
        DummyClaim("claim-risk-1", "technical_risk_claims", "TRL is unvalidated", 0.95),
        DummyClaim("claim-risk-2", "market_risk_claims", "Customer concentration risk present", 0.9),
    ]


@pytest.fixture
def mock_evidence() -> list[Any]:
    class DummyEvidence:
        def __init__(self, id: str, claim_id: str, document_id: str):
            self.id = id
            self.claim_id = claim_id
            self.document_id = document_id
            self.evidence_snippet = "TRL 3 laboratory test results not documented."
            self.section_name = "Product Tech"
            self.page_number = 3

    return [
        DummyEvidence("evidence-risk-1", "claim-risk-1", "doc-risk-1"),
        DummyEvidence("evidence-risk-2", "claim-risk-2", "doc-risk-1"),
    ]


@pytest.fixture
def valid_risk_assessment() -> AgentAssessment:
    return AgentAssessment(
        domain="risk",
        summary="Technical validation and customer dependencies represent active risks.",
        observations=[
            Observation(
                observation_id="OBS-RSK-001",
                observation="Startup TRL level remains at TRL 3 without documented laboratory proof.",
                claim_ids=["claim-risk-1"],
                evidence_ids=["evidence-risk-1"],
                reasoning="The tech logs show a lack of physical laboratory validator logs.",
                confidence=0.85
            ),
            Observation(
                observation_id="OBS-RSK-002",
                observation="Single client controls over 70 percent of projected revenue.",
                claim_ids=["claim-risk-2"],
                evidence_ids=["evidence-risk-2"],
                reasoning="Revenue tables show extreme concentration in client A.",
                confidence=0.9
            )
        ],
        risks=[
            Risk(
                id="RISK-RSK-001",
                description="Technical validation is incomplete at current prototype stage.",
                supporting_observations=["OBS-RSK-001"],
                supporting_claims=["claim-risk-1"],
                supporting_evidence=["evidence-risk-1"],
                severity="High",
                likelihood="Medium",
                impact="High",
                mitigation="Publish prototype validation data.",
                risk_id="RISK-RSK-001",
                category="technical",
                confidence=0.85,
                reasoning="No verification results are found in doc archives."
            )
        ],
        questions=[
            Question(
                id="QST-RSK-001",
                question="Can you provide the raw test reports?",
                purpose="To verify TRL claims.",
                priority="High",
                expected_evidence="Lab test report logs",
                blocking=True,
                generated_by="risk"
            )
        ],
        confidence=ConfidenceHierarchy(
            finding_confidence=0.9,
            evidence_confidence=0.8,
            reasoning_confidence=0.9,
            overall_domain_confidence=0.87
        ),
        reasoning="Startup possesses execution risks in tech development.",
        missing_evidence=[
            MissingEvidence(
                description="Raw lab reports",
                importance="High",
                expected_document="Lab Test Results"
            )
        ],
        prompt_name="Risk Analysis Prompt",
        prompt_version="1.0.0",
        prompt_hash="dummy-hash",
        agent_version="1.0.0",
        generated_at=datetime.utcnow()
    )


def test_risk_expert_success(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_risk_assessment: AgentAssessment
) -> None:
    completion_result = AICompletionResult(
        data=valid_risk_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = RiskExpert(gateway=gateway)

    emitted_events = []
    def track_events(evt: Any) -> None:
        emitted_events.append(evt)

    dispatcher.register("RiskAssessmentStarted", track_events)
    dispatcher.register("RiskAssessmentCompleted", track_events)
    dispatcher.register("RiskAssessmentFailed", track_events)

    try:
        assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})

        assert assessment is not None
        assert assessment.domain == "risk"
        assert len(assessment.observations) == 2
        assert assessment.confidence.overall_domain_confidence == 0.87
        
        # Verify prompt metadata injection
        assert assessment.prompt_name is not None
        assert assessment.prompt_version is not None
        assert assessment.prompt_hash is not None
        assert assessment.agent_version == "1.0.0"
        assert assessment.generated_at is not None

        # Verify event emission
        assert len(emitted_events) == 2
        assert emitted_events[0].event_name == "RiskAssessmentStarted"
        assert emitted_events[0].payload["startup_id"] == str(mock_profile.startup_id)
        assert emitted_events[1].event_name == "RiskAssessmentCompleted"
        assert emitted_events[1].payload["startup_id"] == str(mock_profile.startup_id)

    finally:
        dispatcher.unregister("RiskAssessmentStarted", track_events)
        dispatcher.unregister("RiskAssessmentCompleted", track_events)
        dispatcher.unregister("RiskAssessmentFailed", track_events)


def test_risk_expert_empty_profile() -> None:
    expert = RiskExpert(gateway=MockAIGateway())
    
    with pytest.raises(ValueError, match="Startup Intelligence Profile is missing"):
        expert.evaluate(None, [], [], [], {})

    class DummyProfile:
        startup_id = uuid4()
    
    with pytest.raises(ValueError, match="Claims context must be provided"):
        expert.evaluate(DummyProfile(), None, [], [], {})


def test_risk_expert_gateway_failure(mock_profile: Any, mock_claims: list[Any]) -> None:
    gateway = MockAIGateway(should_fail=True)
    expert = RiskExpert(gateway=gateway)

    emitted_events = []
    def track_events(evt: Any) -> None:
        emitted_events.append(evt)

    dispatcher.register("RiskAssessmentStarted", track_events)
    dispatcher.register("RiskAssessmentFailed", track_events)

    try:
        with pytest.raises(AIProviderError):
            expert.evaluate(mock_profile, mock_claims, [], [], {})

        assert len(emitted_events) == 2
        assert emitted_events[0].event_name == "RiskAssessmentStarted"
        assert emitted_events[1].event_name == "RiskAssessmentFailed"

    finally:
        dispatcher.unregister("RiskAssessmentStarted", track_events)
        dispatcher.unregister("RiskAssessmentFailed", track_events)


def test_risk_expert_malformed_response(mock_profile: Any, mock_claims: list[Any]) -> None:
    from pydantic import BaseModel
    class DummyModel(BaseModel):
        test: str
        
    completion_result = AICompletionResult(
        data=DummyModel(test="malformed"),
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=10.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = RiskExpert(gateway=gateway)

    with pytest.raises(ValueError, match="AI Gateway response data is not a valid AgentAssessment"):
        expert.evaluate(mock_profile, mock_claims, [], [], {})


def test_risk_expert_confidence_validation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_risk_assessment: AgentAssessment
) -> None:
    # Set invalid overall confidence score
    valid_risk_assessment.confidence.overall_domain_confidence = 1.5
    
    completion_result = AICompletionResult(
        data=valid_risk_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = RiskExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert any("Confidence score" in err for err in exc_info.value.errors)


def test_risk_expert_registry_discovery() -> None:
    registry = AgentRegistry()
    count = discover_and_register_experts(registry)
    
    assert count >= 8
    assert registry.exists("RiskExpert")
    assert registry.exists("IPExpert")
    assert registry.exists("CompetitionExpert")
    assert registry.exists("TRLExpert")
    assert registry.exists("FinancialExpert")
    assert registry.exists("MarketExpert")
    assert registry.exists("FounderExpert")
    assert registry.exists("ProductExpert")
    
    assert registry.get("RiskExpert") is RiskExpert


def test_technical_risk_detection(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_risk_assessment: AgentAssessment
) -> None:
    valid_risk_assessment.risks[0].category = "technical"
    completion_result = AICompletionResult(
        data=valid_risk_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=15.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = RiskExpert(gateway=gateway)

    assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    assert assessment.risks[0].category == "technical"


def test_market_risk_detection(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_risk_assessment: AgentAssessment
) -> None:
    valid_risk_assessment.risks[0].category = "market"
    completion_result = AICompletionResult(
        data=valid_risk_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=15.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = RiskExpert(gateway=gateway)

    assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    assert assessment.risks[0].category == "market"


def test_regulatory_risk_detection(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_risk_assessment: AgentAssessment
) -> None:
    valid_risk_assessment.risks[0].category = "regulatory"
    completion_result = AICompletionResult(
        data=valid_risk_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=15.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = RiskExpert(gateway=gateway)

    assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    assert assessment.risks[0].category == "regulatory"


def test_execution_risk_detection(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_risk_assessment: AgentAssessment
) -> None:
    valid_risk_assessment.risks[0].category = "execution"
    completion_result = AICompletionResult(
        data=valid_risk_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=15.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = RiskExpert(gateway=gateway)

    assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    assert assessment.risks[0].category == "execution"


def test_missing_evidence_generation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_risk_assessment: AgentAssessment
) -> None:
    completion_result = AICompletionResult(
        data=valid_risk_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=15.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = RiskExpert(gateway=gateway)

    assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    assert len(assessment.missing_evidence) > 0
    assert assessment.missing_evidence[0].description == "Raw lab reports"


def test_risk_requires_traceability(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_risk_assessment: AgentAssessment
) -> None:
    # Clear supporting observations to break traceability
    valid_risk_assessment.risks[0].supporting_observations = []
    
    completion_result = AICompletionResult(
        data=valid_risk_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = RiskExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
        
    assert any("is missing mandatory 'supporting_observations'" in err for err in exc_info.value.errors)


def test_risk_requires_reasoning(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_risk_assessment: AgentAssessment
) -> None:
    # Set reasoning to empty string
    valid_risk_assessment.risks[0].reasoning = ""
    
    completion_result = AICompletionResult(
        data=valid_risk_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = RiskExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
        
    assert any("is missing mandatory 'reasoning'" in err for err in exc_info.value.errors)


def test_risk_expert_ontology_violation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_risk_assessment: AgentAssessment
) -> None:
    # Set prohibited funding verdict phrase in reasoning
    valid_risk_assessment.reasoning = "We recommend that the committee do not incubate because of financial runway uncertainty."
    
    completion_result = AICompletionResult(
        data=valid_risk_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = RiskExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert any("Ontology breach" in err for err in exc_info.value.errors)


def test_risk_expert_confidence_bounds_check(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_risk_assessment: AgentAssessment
) -> None:
    # Set invalid local confidence value on the risk object
    valid_risk_assessment.risks[0].confidence = 5.0
    
    completion_result = AICompletionResult(
        data=valid_risk_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=15.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = RiskExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
        
    assert any("must be between 0.0 and 1.0" in err or "confidence" in err.lower() for err in exc_info.value.errors)


def test_risk_expert_traceability_validation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_risk_assessment: AgentAssessment
) -> None:
    # Set invalid claim link in observations
    valid_risk_assessment.observations[0].claim_ids = ["broken-claim-link"]
    
    completion_result = AICompletionResult(
        data=valid_risk_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=15.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = RiskExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
        
    assert any("Broken Reference" in err for err in exc_info.value.errors)
