import pytest
from uuid import uuid4
from typing import Any
from datetime import datetime

from app.modules.intelligence.events import dispatcher
from app.modules.intelligence.models import StartupIntelligenceProfile
from app.services.ai.schemas import AICompletionResult, AICompletionMetadata
from app.services.ai.exceptions import AIProviderError

from app.modules.evaluation.founder_expert import FounderExpert
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
        DummyClaim("claim-founder-1", "founder_names", "John Doe, Jane Smith", 0.9),
        DummyClaim("claim-founder-2", "leadership_experience", "10 years in tech management", 0.8),
        DummyClaim("claim-founder-3", "commitment_level", "Full-time", 0.95),
    ]


@pytest.fixture
def mock_evidence() -> list[Any]:
    class DummyEvidence:
        def __init__(self, id: str, claim_id: str, document_id: str):
            self.id = id
            self.claim_id = claim_id
            self.document_id = document_id
            self.evidence_snippet = "10 years in tech management"
            self.section_name = "Team"
            self.page_number = 1

    return [
        DummyEvidence("evidence-founder-1", "claim-founder-1", "doc-founder-1"),
        DummyEvidence("evidence-founder-2", "claim-founder-2", "doc-founder-1"),
    ]


@pytest.fixture
def valid_assessment() -> AgentAssessment:
    return AgentAssessment(
        domain="founder",
        summary="Founding team is highly capable.",
        observations=[
            Observation(
                observation_id="OBS-FOUNDER-001",
                observation="Founders John Doe and Jane Smith have solid domain and leadership expertise.",
                claim_ids=["claim-founder-1"],
                evidence_ids=["evidence-founder-1"],
                reasoning="Longer leadership tenure reduces execution risks.",
                confidence=0.9
            )
        ],
        risks=[
            Risk(
                id="RISK-FOUNDER-001",
                description="Solo director in initial company registry.",
                severity="Low",
                likelihood="Low",
                impact="Medium",
                mitigation="Appoint Jane Smith as a co-director.",
                supporting_observations=["OBS-FOUNDER-001"],
                supporting_claims=["claim-founder-1"],
                supporting_evidence=["evidence-founder-1"]
            )
        ],
        questions=[
            Question(
                id="QST-FOUNDER-001",
                question="What is the equity split between John and Jane?",
                purpose="To verify founder alignment and long-term retention vesting.",
                priority="Medium",
                expected_evidence="Equity Shareholder Agreement",
                blocking=False,
                generated_by="founder"
            )
        ],
        confidence=ConfidenceHierarchy(
            finding_confidence=0.9,
            evidence_confidence=0.85,
            reasoning_confidence=0.9,
            overall_domain_confidence=0.88
        ),
        reasoning="The team shows high competency and strong initial commitment.",
        missing_evidence=[
            MissingEvidence(
                description="Shareholding split documents",
                importance="Medium",
                expected_document="Shareholder Agreement"
            )
        ],
        prompt_name="Founder Analysis Prompt",
        prompt_version="1.0.0",
        prompt_hash="dummy-hash",
        agent_version="1.0.0",
        generated_at=datetime.utcnow()
    )


def test_founder_expert_success(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_assessment: AgentAssessment
) -> None:
    completion_result = AICompletionResult(
        data=valid_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = FounderExpert(gateway=gateway)

    emitted_events = []
    def track_events(evt: Any) -> None:
        emitted_events.append(evt)

    dispatcher.register("FounderAssessmentStarted", track_events)
    dispatcher.register("FounderAssessmentCompleted", track_events)
    dispatcher.register("FounderAssessmentFailed", track_events)

    try:
        assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})

        assert assessment is not None
        assert len(assessment.observations) == 1
        assert assessment.confidence.overall_domain_confidence == 0.88
        assert len(assessment.questions) == 1
        assert assessment.questions[0].blocking is False

        assert len(emitted_events) == 2
        assert emitted_events[0].event_name == "FounderAssessmentStarted"
        assert emitted_events[0].payload["startup_id"] == str(mock_profile.startup_id)
        assert emitted_events[1].event_name == "FounderAssessmentCompleted"
        assert emitted_events[1].payload["startup_id"] == str(mock_profile.startup_id)

    finally:
        dispatcher.unregister("FounderAssessmentStarted", track_events)
        dispatcher.unregister("FounderAssessmentCompleted", track_events)
        dispatcher.unregister("FounderAssessmentFailed", track_events)


def test_founder_expert_empty_profile() -> None:
    expert = FounderExpert(gateway=MockAIGateway())
    
    with pytest.raises(ValueError, match="Startup Intelligence Profile is missing"):
        expert.evaluate(None, [], [], [], {})

    class DummyProfile:
        startup_id = uuid4()
    
    with pytest.raises(ValueError, match="Claims context must be provided"):
        expert.evaluate(DummyProfile(), None, [], [], {})


def test_founder_expert_gateway_failure(mock_profile: Any, mock_claims: list[Any]) -> None:
    gateway = MockAIGateway(should_fail=True)
    expert = FounderExpert(gateway=gateway)

    emitted_events = []
    def track_events(evt: Any) -> None:
        emitted_events.append(evt)

    dispatcher.register("FounderAssessmentStarted", track_events)
    dispatcher.register("FounderAssessmentFailed", track_events)

    try:
        with pytest.raises(AIProviderError):
            expert.evaluate(mock_profile, mock_claims, [], [], {})

        assert len(emitted_events) == 2
        assert emitted_events[0].event_name == "FounderAssessmentStarted"
        assert emitted_events[1].event_name == "FounderAssessmentFailed"
        assert "timeout" in emitted_events[1].payload["error"].lower()

    finally:
        dispatcher.unregister("FounderAssessmentStarted", track_events)
        dispatcher.unregister("FounderAssessmentFailed", track_events)


def test_founder_expert_malformed_response(mock_profile: Any, mock_claims: list[Any]) -> None:
    from pydantic import BaseModel
    class DummyModel(BaseModel):
        test: str
        
    completion_result = AICompletionResult(
        data=DummyModel(test="malformed"),
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=10.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = FounderExpert(gateway=gateway)

    with pytest.raises(ValueError, match="AI Gateway response data is not a valid AgentAssessment"):
        expert.evaluate(mock_profile, mock_claims, [], [], {})


def test_founder_expert_missing_founder_info(mock_profile: Any) -> None:
    missing_assessment = AgentAssessment(
        domain="founder",
        summary="No founder claims found.",
        observations=[],
        risks=[],
        questions=[
            Question(
                id="QST-FOUNDER-001",
                question="Who are the founders of this startup?",
                purpose="To establish initial team composition records.",
                priority="High",
                expected_evidence="Intake Application form",
                blocking=True,
                generated_by="founder"
            )
        ],
        missing_evidence=[
            MissingEvidence(
                description="Founder CV and credentials",
                importance="High",
                expected_document="Founder CV"
            )
        ],
        confidence=ConfidenceHierarchy(
            finding_confidence=0.0,
            evidence_confidence=0.0,
            reasoning_confidence=0.0,
            overall_domain_confidence=0.0
        ),
        reasoning="No claims exist to form a technical or management observation.",
        prompt_name="Founder Analysis Prompt",
        prompt_version="1.0.0",
        prompt_hash="dummy-hash",
        agent_version="1.0.0",
        generated_at=datetime.utcnow()
    )
    
    completion_result = AICompletionResult(
        data=missing_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = FounderExpert(gateway=gateway)

    assessment = expert.evaluate(mock_profile, [], [], [], {})
    assert assessment is not None
    assert len(assessment.observations) == 0
    assert len(assessment.risks) == 0
    assert len(assessment.missing_evidence) == 1
    assert assessment.questions[0].blocking is True
