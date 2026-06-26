import pytest
from uuid import uuid4
from typing import Any
from datetime import datetime

from app.modules.intelligence.events import dispatcher
from app.modules.intelligence.models import StartupIntelligenceProfile
from app.services.ai.schemas import AICompletionResult, AICompletionMetadata
from app.services.ai.exceptions import AIProviderError

from app.modules.evaluation.trl_expert import TRLExpert
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
        DummyClaim("claim-trl-1", "claimed_trl", "TRL 4", 0.95),
        DummyClaim("claim-trl-2", "prototype_maturity", "Laboratory prototype validated", 0.8),
    ]


@pytest.fixture
def mock_evidence() -> list[Any]:
    class DummyEvidence:
        def __init__(self, id: str, claim_id: str, document_id: str):
            self.id = id
            self.claim_id = claim_id
            self.document_id = document_id
            self.evidence_snippet = "Laboratory prototype validated"
            self.section_name = "Tech Readiness"
            self.page_number = 4

    return [
        DummyEvidence("evidence-trl-1", "claim-trl-1", "doc-trl-1"),
        DummyEvidence("evidence-trl-2", "claim-trl-2", "doc-trl-1"),
    ]


@pytest.fixture
def valid_trl_assessment() -> AgentAssessment:
    return AgentAssessment(
        domain="trl",
        summary="Technology is validated in laboratory environment (TRL 4).",
        observations=[
            Observation(
                observation_id="OBS-TRL-001",
                observation="Laboratory prototype has been validated.",
                claim_ids=["claim-trl-2"],
                evidence_ids=["evidence-trl-2"],
                reasoning="Evidence demonstrates function in laboratory environment.",
                confidence=0.9
            )
        ],
        risks=[
            Risk(
                id="RISK-TRL-001",
                description="Scale-up manufacturing readiness is low.",
                supporting_observations=["OBS-TRL-001"],
                supporting_claims=["claim-trl-2"],
                supporting_evidence=["evidence-trl-2"],
                severity="Medium",
                likelihood="Medium",
                impact="Medium",
                mitigation="Initiate design for manufacturing study."
            )
        ],
        questions=[
            Question(
                id="QST-TRL-001",
                question="What are the main component dependencies?",
                purpose="To verify supply chain scaling constraints.",
                priority="Medium",
                expected_evidence="Component list and dependencies map",
                blocking=False,
                generated_by="trl"
            )
        ],
        confidence=ConfidenceHierarchy(
            finding_confidence=0.9,
            evidence_confidence=0.8,
            reasoning_confidence=0.9,
            overall_domain_confidence=0.87
        ),
        reasoning="Technology validation matches official TRL 4 definitions.",
        missing_evidence=[
            MissingEvidence(
                description="Dependencies map document",
                importance="Medium",
                expected_document="System Architecture Document"
            )
        ],
        prompt_name="TRL Analysis Prompt",
        prompt_version="1.0.0",
        prompt_hash="dummy-hash",
        agent_version="1.0.0",
        generated_at=datetime.utcnow()
    )


def test_trl_expert_success(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_trl_assessment: AgentAssessment
) -> None:
    completion_result = AICompletionResult(
        data=valid_trl_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = TRLExpert(gateway=gateway)

    emitted_events = []
    def track_events(evt: Any) -> None:
        emitted_events.append(evt)

    dispatcher.register("TRLAssessmentStarted", track_events)
    dispatcher.register("TRLAssessmentCompleted", track_events)
    dispatcher.register("TRLAssessmentFailed", track_events)

    try:
        assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})

        assert assessment is not None
        assert assessment.domain == "trl"
        assert len(assessment.observations) == 1
        assert assessment.confidence.overall_domain_confidence == 0.87
        
        # Verify prompt metadata injection
        assert assessment.prompt_name is not None
        assert assessment.prompt_version is not None
        assert assessment.prompt_hash is not None
        assert assessment.agent_version == "1.0.0"
        assert assessment.generated_at is not None

        # Verify event emission
        assert len(emitted_events) == 2
        assert emitted_events[0].event_name == "TRLAssessmentStarted"
        assert emitted_events[0].payload["startup_id"] == str(mock_profile.startup_id)
        assert emitted_events[1].event_name == "TRLAssessmentCompleted"
        assert emitted_events[1].payload["startup_id"] == str(mock_profile.startup_id)

    finally:
        dispatcher.unregister("TRLAssessmentStarted", track_events)
        dispatcher.unregister("TRLAssessmentCompleted", track_events)
        dispatcher.unregister("TRLAssessmentFailed", track_events)


def test_trl_expert_unsupported_trl_claim(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_trl_assessment: AgentAssessment
) -> None:
    # Modify assessment to reflect that the high TRL claim is unsupported by evidence, generating a risk
    valid_trl_assessment.risks.append(
        Risk(
            id="RISK-TRL-002",
            description="Claimed TRL 9 has no matching validation evidence.",
            supporting_observations=["OBS-TRL-001"],
            supporting_claims=["claim-trl-2"],
            supporting_evidence=["evidence-trl-2"],
            severity="High",
            likelihood="High",
            impact="High",
            mitigation="Provide field trial validation reports."
        )
    )
    completion_result = AICompletionResult(
        data=valid_trl_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = TRLExpert(gateway=gateway)

    assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert assessment is not None
    # Verify that the unsupported TRL claim is flagged as a risk
    unsupported_risks = [r for r in assessment.risks if "no matching validation evidence" in r.description]
    assert len(unsupported_risks) == 1


def test_trl_expert_insufficient_evidence(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_trl_assessment: AgentAssessment
) -> None:
    # Insufficient evidence results in missing evidence and questions
    valid_trl_assessment.questions.append(
        Question(
            id="QST-TRL-002",
            question="Where is the data log from the field trial?",
            purpose="To verify claimed TRL 6 status.",
            priority="High",
            expected_evidence="Field pilot data logs",
            blocking=True,
            generated_by="trl"
        )
    )
    valid_trl_assessment.missing_evidence.append(
        MissingEvidence(
            description="Field trial pilot logs",
            importance="High",
            expected_document="Pilot Operations Report"
        )
    )
    completion_result = AICompletionResult(
        data=valid_trl_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = TRLExpert(gateway=gateway)

    assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert assessment is not None
    assert any(q.blocking for q in assessment.questions)
    assert any(m.importance == "High" for m in assessment.missing_evidence)


def test_trl_expert_empty_profile() -> None:
    expert = TRLExpert(gateway=MockAIGateway())
    
    with pytest.raises(ValueError, match="Startup Intelligence Profile is missing"):
        expert.evaluate(None, [], [], [], {})

    class DummyProfile:
        startup_id = uuid4()
    
    with pytest.raises(ValueError, match="Claims context must be provided"):
        expert.evaluate(DummyProfile(), None, [], [], {})


def test_trl_expert_gateway_failure(mock_profile: Any, mock_claims: list[Any]) -> None:
    gateway = MockAIGateway(should_fail=True)
    expert = TRLExpert(gateway=gateway)

    emitted_events = []
    def track_events(evt: Any) -> None:
        emitted_events.append(evt)

    dispatcher.register("TRLAssessmentStarted", track_events)
    dispatcher.register("TRLAssessmentFailed", track_events)

    try:
        with pytest.raises(AIProviderError):
            expert.evaluate(mock_profile, mock_claims, [], [], {})

        assert len(emitted_events) == 2
        assert emitted_events[0].event_name == "TRLAssessmentStarted"
        assert emitted_events[1].event_name == "TRLAssessmentFailed"
        assert "timeout" in emitted_events[1].payload["error"].lower()

    finally:
        dispatcher.unregister("TRLAssessmentStarted", track_events)
        dispatcher.unregister("TRLAssessmentFailed", track_events)


def test_trl_expert_malformed_response(mock_profile: Any, mock_claims: list[Any]) -> None:
    from pydantic import BaseModel
    class DummyModel(BaseModel):
        test: str
        
    completion_result = AICompletionResult(
        data=DummyModel(test="malformed"),
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=10.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = TRLExpert(gateway=gateway)

    with pytest.raises(ValueError, match="AI Gateway response data is not a valid AgentAssessment"):
        expert.evaluate(mock_profile, mock_claims, [], [], {})


def test_trl_expert_ontology_violation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_trl_assessment: AgentAssessment
) -> None:
    # Prohibited rating/verdict term in reasoning
    valid_trl_assessment.reasoning = "We recommend incubation approval based on TRL status."
    
    completion_result = AICompletionResult(
        data=valid_trl_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = TRLExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert any("Ontology breach" in err for err in exc_info.value.errors)


def test_trl_expert_confidence_validation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_trl_assessment: AgentAssessment
) -> None:
    # Set invalid overall confidence score
    valid_trl_assessment.confidence.overall_domain_confidence = 1.5
    
    completion_result = AICompletionResult(
        data=valid_trl_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = TRLExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert any("Confidence score" in err for err in exc_info.value.errors)


def test_trl_expert_traceability_validation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_trl_assessment: AgentAssessment
) -> None:
    # Set an unlinked claim id to breach traceability rules
    valid_trl_assessment.observations[0].claim_ids = ["unlinked-claim-id"]
    
    completion_result = AICompletionResult(
        data=valid_trl_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = TRLExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert any("Broken Reference" in err for err in exc_info.value.errors)


def test_trl_expert_registry_discovery() -> None:
    registry = AgentRegistry()
    count = discover_and_register_experts(registry)
    
    assert count >= 5
    assert registry.exists("TRLExpert")
    assert registry.exists("FinancialExpert")
    assert registry.exists("MarketExpert")
    assert registry.exists("FounderExpert")
    assert registry.exists("ProductExpert")
    
    assert registry.get("TRLExpert") is TRLExpert
