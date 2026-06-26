import pytest
from uuid import uuid4
from typing import Any
from datetime import datetime

from app.modules.intelligence.events import dispatcher
from app.modules.intelligence.models import StartupIntelligenceProfile
from app.services.ai.schemas import AICompletionResult, AICompletionMetadata
from app.services.ai.exceptions import AIProviderError

from app.modules.evaluation.competition_expert import CompetitionExpert
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
        DummyClaim("claim-comp-1", "competitor_names", "Competitor A, Competitor B", 0.95),
        DummyClaim("claim-comp-2", "differentiation_claims", "Proprietary automated workflow", 0.8),
        DummyClaim("claim-comp-3", "moat_claims", "Data advantage with 10M records", 0.85),
    ]


@pytest.fixture
def mock_evidence() -> list[Any]:
    class DummyEvidence:
        def __init__(self, id: str, claim_id: str, document_id: str):
            self.id = id
            self.claim_id = claim_id
            self.document_id = document_id
            self.evidence_snippet = "Proprietary automated workflow differentiation"
            self.section_name = "Competition"
            self.page_number = 5

    return [
        DummyEvidence("evidence-comp-1", "claim-comp-1", "doc-comp-1"),
        DummyEvidence("evidence-comp-2", "claim-comp-2", "doc-comp-1"),
        DummyEvidence("evidence-comp-3", "claim-comp-3", "doc-comp-1"),
    ]


@pytest.fixture
def valid_competition_assessment() -> AgentAssessment:
    return AgentAssessment(
        domain="competition",
        summary="Startup exhibits clear workflow differentiation and moderate defensibility.",
        observations=[
            Observation(
                observation_id="OBS-COMP-001",
                observation="Automation differentiation claimed over Competitor A and B.",
                claim_ids=["claim-comp-2"],
                evidence_ids=["evidence-comp-2"],
                reasoning="Evidence validates that automated workflow exists in the prototype.",
                confidence=0.9
            )
        ],
        risks=[
            Risk(
                id="RISK-COMP-001",
                description="Competitor B could easily copy the workflow features.",
                supporting_observations=["OBS-COMP-001"],
                supporting_claims=["claim-comp-2"],
                supporting_evidence=["evidence-comp-2"],
                severity="Medium",
                likelihood="High",
                impact="Medium",
                mitigation="Patent key automation workflow steps."
            )
        ],
        questions=[
            Question(
                id="QST-COMP-001",
                question="What specific features differentiate from Competitor A?",
                purpose="To map detailed feature-by-feature positioning.",
                priority="Medium",
                expected_evidence="Competitive feature matrix",
                blocking=False,
                generated_by="competition"
            )
        ],
        confidence=ConfidenceHierarchy(
            finding_confidence=0.9,
            evidence_confidence=0.8,
            reasoning_confidence=0.9,
            overall_domain_confidence=0.87
        ),
        reasoning="Defensibility relies mostly on execution speed and patents.",
        missing_evidence=[
            MissingEvidence(
                description="Competitive feature matrix document",
                importance="Medium",
                expected_document="Product Road Map"
            )
        ],
        prompt_name="Competition Analysis Prompt",
        prompt_version="1.0.0",
        prompt_hash="dummy-hash",
        agent_version="1.0.0",
        generated_at=datetime.utcnow()
    )


def test_competition_expert_success(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_competition_assessment: AgentAssessment
) -> None:
    completion_result = AICompletionResult(
        data=valid_competition_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = CompetitionExpert(gateway=gateway)

    emitted_events = []
    def track_events(evt: Any) -> None:
        emitted_events.append(evt)

    dispatcher.register("CompetitionAssessmentStarted", track_events)
    dispatcher.register("CompetitionAssessmentCompleted", track_events)
    dispatcher.register("CompetitionAssessmentFailed", track_events)

    try:
        assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})

        assert assessment is not None
        assert assessment.domain == "competition"
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
        assert emitted_events[0].event_name == "CompetitionAssessmentStarted"
        assert emitted_events[0].payload["startup_id"] == str(mock_profile.startup_id)
        assert emitted_events[1].event_name == "CompetitionAssessmentCompleted"
        assert emitted_events[1].payload["startup_id"] == str(mock_profile.startup_id)

    finally:
        dispatcher.unregister("CompetitionAssessmentStarted", track_events)
        dispatcher.unregister("CompetitionAssessmentCompleted", track_events)
        dispatcher.unregister("CompetitionAssessmentFailed", track_events)


def test_competition_expert_empty_profile() -> None:
    expert = CompetitionExpert(gateway=MockAIGateway())
    
    with pytest.raises(ValueError, match="Startup Intelligence Profile is missing"):
        expert.evaluate(None, [], [], [], {})

    class DummyProfile:
        startup_id = uuid4()
    
    with pytest.raises(ValueError, match="Claims context must be provided"):
        expert.evaluate(DummyProfile(), None, [], [], {})


def test_competition_expert_missing_competitors(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_competition_assessment: AgentAssessment
) -> None:
    # Insufficient competitor mapping generates a question and missing evidence
    valid_competition_assessment.questions.append(
        Question(
            id="QST-COMP-002",
            question="Who are the main incumbents in this geography?",
            purpose="Verify local competition dynamics.",
            priority="High",
            expected_evidence="Local market positioning map",
            blocking=True,
            generated_by="competition"
        )
    )
    valid_competition_assessment.missing_evidence.append(
        MissingEvidence(
            description="Geographical competitor map",
            importance="High",
            expected_document="Market Map Analysis"
        )
    )
    completion_result = AICompletionResult(
        data=valid_competition_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = CompetitionExpert(gateway=gateway)

    assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    assert assessment is not None
    assert any(q.blocking for q in assessment.questions)
    assert any(m.importance == "High" for m in assessment.missing_evidence)


def test_competition_expert_unsupported_moat(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_competition_assessment: AgentAssessment
) -> None:
    # Flagging unsupported moat/defensibility claims as risks
    valid_competition_assessment.risks.append(
        Risk(
            id="RISK-COMP-002",
            description="Claimed data moat lacks historical registry evidence or validation.",
            supporting_observations=["OBS-COMP-001"],
            supporting_claims=["claim-comp-2"],
            supporting_evidence=["evidence-comp-2"],
            severity="High",
            likelihood="High",
            impact="High",
            mitigation="Provide data source statistics."
        )
    )
    completion_result = AICompletionResult(
        data=valid_competition_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = CompetitionExpert(gateway=gateway)

    assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    assert assessment is not None
    assert any("lacks historical registry evidence" in r.description for r in assessment.risks)


def test_competition_expert_unsupported_differentiation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_competition_assessment: AgentAssessment
) -> None:
    # Flagging unsupported differentiation claims as risks
    valid_competition_assessment.risks.append(
        Risk(
            id="RISK-COMP-003",
            description="Claimed speed differentiation is unsupported by prototype performance data.",
            supporting_observations=["OBS-COMP-001"],
            supporting_claims=["claim-comp-2"],
            supporting_evidence=["evidence-comp-2"],
            severity="High",
            likelihood="Medium",
            impact="High",
            mitigation="Provide benchmark performance trials."
        )
    )
    completion_result = AICompletionResult(
        data=valid_competition_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = CompetitionExpert(gateway=gateway)

    assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    assert assessment is not None
    assert any("speed differentiation is unsupported" in r.description for r in assessment.risks)


def test_competition_expert_gateway_failure(mock_profile: Any, mock_claims: list[Any]) -> None:
    gateway = MockAIGateway(should_fail=True)
    expert = CompetitionExpert(gateway=gateway)

    emitted_events = []
    def track_events(evt: Any) -> None:
        emitted_events.append(evt)

    dispatcher.register("CompetitionAssessmentStarted", track_events)
    dispatcher.register("CompetitionAssessmentFailed", track_events)

    try:
        with pytest.raises(AIProviderError):
            expert.evaluate(mock_profile, mock_claims, [], [], {})

        assert len(emitted_events) == 2
        assert emitted_events[0].event_name == "CompetitionAssessmentStarted"
        assert emitted_events[1].event_name == "CompetitionAssessmentFailed"

    finally:
        dispatcher.unregister("CompetitionAssessmentStarted", track_events)
        dispatcher.unregister("CompetitionAssessmentFailed", track_events)


def test_competition_expert_malformed_response(mock_profile: Any, mock_claims: list[Any]) -> None:
    from pydantic import BaseModel
    class DummyModel(BaseModel):
        test: str
        
    completion_result = AICompletionResult(
        data=DummyModel(test="malformed"),
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=10.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = CompetitionExpert(gateway=gateway)

    with pytest.raises(ValueError, match="AI Gateway response data is not a valid AgentAssessment"):
        expert.evaluate(mock_profile, mock_claims, [], [], {})


def test_competition_expert_confidence_validation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_competition_assessment: AgentAssessment
) -> None:
    # Set invalid overall confidence score
    valid_competition_assessment.confidence.overall_domain_confidence = 1.5
    
    completion_result = AICompletionResult(
        data=valid_competition_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = CompetitionExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert any("Confidence score" in err for err in exc_info.value.errors)


def test_competition_expert_traceability_validation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_competition_assessment: AgentAssessment
) -> None:
    # Set an unlinked claim id to breach traceability rules
    valid_competition_assessment.observations[0].claim_ids = ["unlinked-claim-id"]
    
    completion_result = AICompletionResult(
        data=valid_competition_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = CompetitionExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert any("Broken Reference" in err for err in exc_info.value.errors)


def test_competition_expert_ontology_violation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_competition_assessment: AgentAssessment
) -> None:
    # Prohibited ratings verdict term in reasoning
    valid_competition_assessment.reasoning = "We recommend incubation approval based on competition results."
    
    completion_result = AICompletionResult(
        data=valid_competition_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = CompetitionExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert any("Ontology breach" in err for err in exc_info.value.errors)


def test_competition_expert_registry_discovery() -> None:
    registry = AgentRegistry()
    count = discover_and_register_experts(registry)
    
    assert count >= 6
    assert registry.exists("CompetitionExpert")
    assert registry.exists("TRLExpert")
    assert registry.exists("FinancialExpert")
    assert registry.exists("MarketExpert")
    assert registry.exists("FounderExpert")
    assert registry.exists("ProductExpert")
    
    assert registry.get("CompetitionExpert") is CompetitionExpert
