import pytest
from uuid import uuid4
from typing import Any
from datetime import datetime

from app.modules.intelligence.events import dispatcher
from app.modules.intelligence.models import StartupIntelligenceProfile
from app.services.ai.schemas import AICompletionResult, AICompletionMetadata
from app.services.ai.exceptions import AIProviderError

from app.modules.evaluation.ip_expert import IPExpert
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
        DummyClaim("claim-ip-1", "patents", "Patent US-12345 granted", 0.95),
        DummyClaim("claim-ip-2", "ownership_declarations", "Company assigns IP from founders", 0.9),
    ]


@pytest.fixture
def mock_evidence() -> list[Any]:
    class DummyEvidence:
        def __init__(self, id: str, claim_id: str, document_id: str):
            self.id = id
            self.claim_id = claim_id
            self.document_id = document_id
            self.evidence_snippet = "US-12345 patent search log assigned"
            self.section_name = "IP Moat"
            self.page_number = 6

    return [
        DummyEvidence("evidence-ip-1", "claim-ip-1", "doc-ip-1"),
        DummyEvidence("evidence-ip-2", "claim-ip-2", "doc-ip-1"),
    ]


@pytest.fixture
def valid_ip_assessment() -> AgentAssessment:
    return AgentAssessment(
        domain="ip",
        summary="Granted patents exist and company assignment is documented.",
        observations=[
            Observation(
                observation_id="OBS-IP-001",
                observation="Patent US-12345 has been assigned to the company.",
                claim_ids=["claim-ip-2"],
                evidence_ids=["evidence-ip-2"],
                reasoning="Evidence confirms founder-to-company assignment agreement.",
                confidence=0.9
            )
        ],
        risks=[
            Risk(
                id="RISK-IP-001",
                description="Potential freedom-to-operate exposure in European markets.",
                supporting_observations=["OBS-IP-001"],
                supporting_claims=["claim-ip-2"],
                supporting_evidence=["evidence-ip-2"],
                severity="Medium",
                likelihood="Medium",
                impact="Medium",
                mitigation="Perform local FTO patent search."
            )
        ],
        questions=[
            Question(
                id="QST-IP-001",
                question="Is there third-party dependency in key claims?",
                purpose="To verify licensing requirements.",
                priority="Medium",
                expected_evidence="FTO search report",
                blocking=False,
                generated_by="ip"
            )
        ],
        confidence=ConfidenceHierarchy(
            finding_confidence=0.9,
            evidence_confidence=0.8,
            reasoning_confidence=0.9,
            overall_domain_confidence=0.87
        ),
        reasoning="Overall IP position is protected by assignment logs.",
        missing_evidence=[
            MissingEvidence(
                description="European FTO search report",
                importance="Medium",
                expected_document="FTO Analysis"
            )
        ],
        prompt_name="IP Analysis Prompt",
        prompt_version="1.0.0",
        prompt_hash="dummy-hash",
        agent_version="1.0.0",
        generated_at=datetime.utcnow()
    )


def test_ip_expert_success(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_ip_assessment: AgentAssessment
) -> None:
    completion_result = AICompletionResult(
        data=valid_ip_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = IPExpert(gateway=gateway)

    emitted_events = []
    def track_events(evt: Any) -> None:
        emitted_events.append(evt)

    dispatcher.register("IPAssessmentStarted", track_events)
    dispatcher.register("IPAssessmentCompleted", track_events)
    dispatcher.register("IPAssessmentFailed", track_events)

    try:
        assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})

        assert assessment is not None
        assert assessment.domain == "ip"
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
        assert emitted_events[0].event_name == "IPAssessmentStarted"
        assert emitted_events[0].payload["startup_id"] == str(mock_profile.startup_id)
        assert emitted_events[1].event_name == "IPAssessmentCompleted"
        assert emitted_events[1].payload["startup_id"] == str(mock_profile.startup_id)

    finally:
        dispatcher.unregister("IPAssessmentStarted", track_events)
        dispatcher.unregister("IPAssessmentCompleted", track_events)
        dispatcher.unregister("IPAssessmentFailed", track_events)


def test_ip_expert_empty_profile() -> None:
    expert = IPExpert(gateway=MockAIGateway())
    
    with pytest.raises(ValueError, match="Startup Intelligence Profile is missing"):
        expert.evaluate(None, [], [], [], {})

    class DummyProfile:
        startup_id = uuid4()
    
    with pytest.raises(ValueError, match="Claims context must be provided"):
        expert.evaluate(DummyProfile(), None, [], [], {})


def test_ip_expert_missing_patent_evidence(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_ip_assessment: AgentAssessment
) -> None:
    # Missing patent evidence triggers questions and missing evidence records
    valid_ip_assessment.questions.append(
        Question(
            id="QST-IP-002",
            question="Where is the patent registry search log?",
            purpose="To verify patent filing status.",
            priority="High",
            expected_evidence="Patent registry filing receipt",
            blocking=True,
            generated_by="ip"
        )
    )
    valid_ip_assessment.missing_evidence.append(
        MissingEvidence(
            description="Patent filing receipts",
            importance="High",
            expected_document="Patent Registry Document"
        )
    )
    completion_result = AICompletionResult(
        data=valid_ip_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = IPExpert(gateway=gateway)

    assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    assert assessment is not None
    assert any(q.blocking for q in assessment.questions)
    assert any(m.importance == "High" for m in assessment.missing_evidence)


def test_ip_expert_ownership_ambiguity(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_ip_assessment: AgentAssessment
) -> None:
    # Ownership ambiguity triggers a risk and a question
    valid_ip_assessment.risks.append(
        Risk(
            id="RISK-IP-002",
            description="Ambiguity in founder IP assignment log.",
            supporting_observations=["OBS-IP-001"],
            supporting_claims=["claim-ip-2"],
            supporting_evidence=["evidence-ip-2"],
            severity="High",
            likelihood="High",
            impact="High",
            mitigation="Execute assignment agreements immediately."
        )
    )
    completion_result = AICompletionResult(
        data=valid_ip_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = IPExpert(gateway=gateway)

    assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    assert assessment is not None
    assert any("assignment log" in r.description for r in assessment.risks)


def test_ip_expert_unsupported_patent_claim(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_ip_assessment: AgentAssessment
) -> None:
    # Unsupported patent claims are flagged as risks
    valid_ip_assessment.risks.append(
        Risk(
            id="RISK-IP-003",
            description="Claimed patent US-99999 has no supporting evidence in document logs.",
            supporting_observations=["OBS-IP-001"],
            supporting_claims=["claim-ip-2"],
            supporting_evidence=["evidence-ip-2"],
            severity="High",
            likelihood="High",
            impact="High",
            mitigation="Provide patent filing documentation."
        )
    )
    completion_result = AICompletionResult(
        data=valid_ip_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = IPExpert(gateway=gateway)

    assessment = expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    assert assessment is not None
    assert any("has no supporting evidence in document logs" in r.description for r in assessment.risks)


def test_ip_expert_gateway_failure(mock_profile: Any, mock_claims: list[Any]) -> None:
    gateway = MockAIGateway(should_fail=True)
    expert = IPExpert(gateway=gateway)

    emitted_events = []
    def track_events(evt: Any) -> None:
        emitted_events.append(evt)

    dispatcher.register("IPAssessmentStarted", track_events)
    dispatcher.register("IPAssessmentFailed", track_events)

    try:
        with pytest.raises(AIProviderError):
            expert.evaluate(mock_profile, mock_claims, [], [], {})

        assert len(emitted_events) == 2
        assert emitted_events[0].event_name == "IPAssessmentStarted"
        assert emitted_events[1].event_name == "IPAssessmentFailed"

    finally:
        dispatcher.unregister("IPAssessmentStarted", track_events)
        dispatcher.unregister("IPAssessmentFailed", track_events)


def test_ip_expert_malformed_response(mock_profile: Any, mock_claims: list[Any]) -> None:
    from pydantic import BaseModel
    class DummyModel(BaseModel):
        test: str
        
    completion_result = AICompletionResult(
        data=DummyModel(test="malformed"),
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=10.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = IPExpert(gateway=gateway)

    with pytest.raises(ValueError, match="AI Gateway response data is not a valid AgentAssessment"):
        expert.evaluate(mock_profile, mock_claims, [], [], {})


def test_ip_expert_confidence_validation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_ip_assessment: AgentAssessment
) -> None:
    # Set invalid overall confidence score
    valid_ip_assessment.confidence.overall_domain_confidence = 1.5
    
    completion_result = AICompletionResult(
        data=valid_ip_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = IPExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert any("Confidence score" in err for err in exc_info.value.errors)


def test_ip_expert_traceability_validation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_ip_assessment: AgentAssessment
) -> None:
    # Set an unlinked claim id to breach traceability rules
    valid_ip_assessment.observations[0].claim_ids = ["unlinked-claim-id"]
    
    completion_result = AICompletionResult(
        data=valid_ip_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = IPExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert any("Broken Reference" in err for err in exc_info.value.errors)


def test_ip_expert_ontology_violation(
    mock_profile: Any,
    mock_claims: list[Any],
    mock_evidence: list[Any],
    valid_ip_assessment: AgentAssessment
) -> None:
    # Prohibited funding verdict term in reasoning
    valid_ip_assessment.reasoning = "We recommend incubation approval based on patent moat strength."
    
    completion_result = AICompletionResult(
        data=valid_ip_assessment,
        metadata=AICompletionMetadata(model="gpt-4", provider="mock", latency_ms=150.0)
    )
    gateway = MockAIGateway(mock_result=completion_result)
    expert = IPExpert(gateway=gateway)

    with pytest.raises(AssessmentValidationError) as exc_info:
        expert.evaluate(mock_profile, mock_claims, mock_evidence, [], {})
    
    assert any("Ontology breach" in err for err in exc_info.value.errors)


def test_ip_expert_registry_discovery() -> None:
    registry = AgentRegistry()
    count = discover_and_register_experts(registry)
    
    assert count >= 7
    assert registry.exists("IPExpert")
    assert registry.exists("CompetitionExpert")
    assert registry.exists("TRLExpert")
    assert registry.exists("FinancialExpert")
    assert registry.exists("MarketExpert")
    assert registry.exists("FounderExpert")
    assert registry.exists("ProductExpert")
    
    assert registry.get("IPExpert") is IPExpert
