import pytest
from typing import Any
from datetime import datetime
from app.modules.evaluation.schemas import (
    AgentAssessment,
    Observation,
    Risk,
    Question,
    ConfidenceHierarchy,
    MissingEvidence
)
from app.modules.evaluation.validation.assessment_validator import AssessmentValidator
from app.modules.evaluation.validation.validation_exceptions import AssessmentValidationError


class DummyClaim:
    def __init__(self, id: str):
        self.id = id
        class DummyField:
            field_key = "founder_experience"
        self.field = DummyField()
        self.value_string = "Validated founder claim"
        self.confidence_score = 0.9
        self.validation_status = "VALIDATED"


class DummyEvidence:
    def __init__(self, id: str, claim_id: str, document_id: str | None = "doc-123"):
        self.id = id
        self.claim_id = claim_id
        self.document_id = document_id
        self.evidence_snippet = "Supporting quote"
        self.section_name = "Introduction"
        self.page_number = 1


@pytest.fixture
def valid_assessment_data() -> dict[str, Any]:
    return {
        "domain": "founder",
        "summary": "Team has high domain experience.",
        "observations": [
            {
                "observation_id": "OBS-001",
                "observation": "Team has high domain experience.",
                "claim_ids": ["claim-1"],
                "evidence_ids": ["ev-1"],
                "reasoning": "Substantial research and engineering tenure.",
                "confidence": 0.95
            }
        ],
        "risks": [
            {
                "id": "RISK-001",
                "description": "Lack of commercial co-founder.",
                "severity": "Medium",
                "likelihood": "High",
                "impact": "Medium",
                "mitigation": "Recruit a business developer.",
                "supporting_observations": ["OBS-001"],
                "supporting_claims": ["claim-1"],
                "supporting_evidence": ["ev-1"]
            }
        ],
        "questions": [
            {
                "id": "QST-001",
                "question": "What is the team's commitment level?",
                "purpose": "Verify runway retention.",
                "priority": "Low",
                "expected_evidence": "Employment contracts",
                "blocking": False,
                "generated_by": "founder"
            }
        ],
        "confidence": {
            "finding_confidence": 0.9,
            "evidence_confidence": 0.8,
            "reasoning_confidence": 0.85,
            "overall_domain_confidence": 0.85
        },
        "reasoning": "The technical core is extremely robust.",
        "missing_evidence": [
            {
                "description": "Founder CV details",
                "importance": "Medium",
                "expected_document": "Founder CV"
            }
        ],
        "prompt_name": "Founder Analysis Prompt",
        "prompt_version": "1.0.0",
        "prompt_hash": "dummy-hash",
        "agent_version": "1.0.0",
        "generated_at": datetime.utcnow()
    }


def test_validator_success(valid_assessment_data: dict[str, Any]) -> None:
    assessment = AgentAssessment(**valid_assessment_data)
    claims = [DummyClaim("claim-1")]
    evidence = [DummyEvidence("ev-1", "claim-1")]

    res = AssessmentValidator.validate(assessment, context_claims=claims, context_evidence=evidence)
    assert res == assessment

    result = AssessmentValidator.validate_assessment(assessment, context_claims=claims, context_evidence=evidence)
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validator_malformed_assessment() -> None:
    result = AssessmentValidator.validate_assessment("not an assessment")  # type: ignore
    assert result.is_valid is False
    assert any("Schema integrity failed" in err for err in result.errors)


def test_validator_missing_required_fields(valid_assessment_data: dict[str, Any]) -> None:
    data = valid_assessment_data.copy()
    data.pop("confidence")
    
    with pytest.raises(Exception):
        AgentAssessment(**data)


def test_validator_duplicate_ids(valid_assessment_data: dict[str, Any]) -> None:
    data = valid_assessment_data.copy()
    data["observations"][0]["observation_id"] = "DUP-001"
    data["risks"][0]["id"] = "DUP-001"

    assessment = AgentAssessment(**data)
    result = AssessmentValidator.validate_assessment(assessment)
    assert result.is_valid is False
    assert any("Duplicate ID 'DUP-001'" in err for err in result.errors)
    assert "Duplicate Risk ID found: DUP-001" in result.duplicate_objects


def test_validator_duplicate_content(valid_assessment_data: dict[str, Any]) -> None:
    data = valid_assessment_data.copy()
    data["observations"].append({
        "observation_id": "OBS-002",
        "observation": "Team has high domain experience. ",
        "claim_ids": ["claim-1"],
        "evidence_ids": ["ev-1"],
        "reasoning": "Similar reasoning",
        "confidence": 0.8
    })

    assessment = AgentAssessment(**data)
    result = AssessmentValidator.validate_assessment(assessment)
    assert result.is_valid is True
    assert any("Duplicate Observation content detected" in warn for warn in result.warnings)


def test_validator_broken_references_observation(valid_assessment_data: dict[str, Any]) -> None:
    assessment = AgentAssessment(**valid_assessment_data)
    claims = [DummyClaim("different-claim-id")]
    evidence = [DummyEvidence("ev-1", "claim-1")]

    result = AssessmentValidator.validate_assessment(assessment, context_claims=claims, context_evidence=evidence)
    assert result.is_valid is False
    assert any("references non-existent Claim 'claim-1'" in err for err in result.errors)


def test_validator_broken_references_risk(valid_assessment_data: dict[str, Any]) -> None:
    data = valid_assessment_data.copy()
    data["risks"][0]["supporting_observations"] = ["OBS-NONEXISTENT"]

    assessment = AgentAssessment(**data)
    result = AssessmentValidator.validate_assessment(assessment)
    assert result.is_valid is False
    assert any("references non-existent Observation 'OBS-NONEXISTENT'" in err for err in result.errors)


def test_validator_claim_missing_evidence(valid_assessment_data: dict[str, Any]) -> None:
    assessment = AgentAssessment(**valid_assessment_data)
    claims = [DummyClaim("claim-1")]
    result = AssessmentValidator.validate_assessment(assessment, context_claims=claims, context_evidence=[])
    assert result.is_valid is False
    assert any("Claim 'claim-1' must reference at least one Evidence ID" in err for err in result.errors)


def test_validator_evidence_missing_document(valid_assessment_data: dict[str, Any]) -> None:
    assessment = AgentAssessment(**valid_assessment_data)
    claims = [DummyClaim("claim-1")]
    evidence = [DummyEvidence("ev-1", "claim-1", document_id=None)]
    
    result = AssessmentValidator.validate_assessment(assessment, context_claims=claims, context_evidence=evidence)
    assert result.is_valid is False
    assert any("Evidence 'ev-1' must reference a Document ID" in err for err in result.errors)


def test_validator_invalid_confidence_hierarchy(valid_assessment_data: dict[str, Any]) -> None:
    data = valid_assessment_data.copy()
    ch_data = data.pop("confidence")
    ch_data["finding_confidence"] = 1.5  # Out of bounds
    
    bad_ch = ConfidenceHierarchy.model_construct(**ch_data)
    
    observations = [Observation.model_construct(**o) for o in data.pop("observations")]
    risks = [Risk.model_construct(**r) for r in data.pop("risks")]
    questions = [Question.model_construct(**q) for q in data.pop("questions")]
    missing_ev = [MissingEvidence.model_construct(**m) for m in data.pop("missing_evidence")]

    assessment = AgentAssessment.model_construct(
        observations=observations,
        risks=risks,
        questions=questions,
        missing_evidence=missing_ev,
        confidence=bad_ch,
        **data
    )
    result = AssessmentValidator.validate_assessment(assessment)
    assert result.is_valid is False
    assert any("finding_confidence' must be between 0.0 and 1.0" in err for err in result.errors)


def test_validator_invalid_observation_confidence(valid_assessment_data: dict[str, Any]) -> None:
    data = valid_assessment_data.copy()
    obs_data = data.pop("observations")[0].copy()
    obs_data["confidence"] = -0.1  # Out of bounds
    
    bad_obs = Observation.model_construct(**obs_data)
    
    ch = ConfidenceHierarchy.model_construct(**data.pop("confidence"))
    risks = [Risk.model_construct(**r) for r in data.pop("risks")]
    questions = [Question.model_construct(**q) for q in data.pop("questions")]
    missing_ev = [MissingEvidence.model_construct(**m) for m in data.pop("missing_evidence")]

    assessment = AgentAssessment.model_construct(
        observations=[bad_obs],
        risks=risks,
        questions=questions,
        missing_evidence=missing_ev,
        confidence=ch,
        **data
    )
    result = AssessmentValidator.validate_assessment(assessment)
    assert result.is_valid is False
    assert any("confidence must be between 0.0 and 1.0" in err for err in result.errors)


def test_validator_missing_metadata(valid_assessment_data: dict[str, Any]) -> None:
    data = valid_assessment_data.copy()
    data.pop("prompt_name")  # Remove one of the required metadata fields

    observations = [Observation.model_construct(**o) for o in data.pop("observations")]
    risks = [Risk.model_construct(**r) for r in data.pop("risks")]
    questions = [Question.model_construct(**q) for q in data.pop("questions")]
    missing_ev = [MissingEvidence.model_construct(**m) for m in data.pop("missing_evidence")]
    ch = ConfidenceHierarchy.model_construct(**data.pop("confidence"))

    assessment = AgentAssessment.model_construct(
        observations=observations,
        risks=risks,
        questions=questions,
        missing_evidence=missing_ev,
        confidence=ch,
        **data
    )
    result = AssessmentValidator.validate_assessment(assessment)
    assert result.is_valid is False
    assert any("Required metadata field 'prompt_name' is missing or empty" in err for err in result.errors)


def test_validator_warnings_version_and_timestamp(valid_assessment_data: dict[str, Any]) -> None:
    data = valid_assessment_data.copy()
    data["prompt_version"] = "not-semver"
    data["generated_at"] = "not-iso-8601"

    observations = [Observation.model_construct(**o) for o in data.pop("observations")]
    risks = [Risk.model_construct(**r) for r in data.pop("risks")]
    questions = [Question.model_construct(**q) for q in data.pop("questions")]
    missing_ev = [MissingEvidence.model_construct(**m) for m in data.pop("missing_evidence")]
    ch = ConfidenceHierarchy.model_construct(**data.pop("confidence"))

    assessment = AgentAssessment.model_construct(
        observations=observations,
        risks=risks,
        questions=questions,
        missing_evidence=missing_ev,
        confidence=ch,
        **data
    )
    result = AssessmentValidator.validate_assessment(assessment)
    assert result.is_valid is True
    assert any("not standard SemVer" in warn for warn in result.warnings)
    assert any("not in ISO-8601 format" in warn for warn in result.warnings)


def test_validator_ontology_compliance_forbidden_keys(valid_assessment_data: dict[str, Any]) -> None:
    data = valid_assessment_data.copy()
    # Scoring term inside reasoning triggers validation error now
    data["reasoning"] = "This startup gets a high score rating."

    assessment = AgentAssessment(**data)
    result = AssessmentValidator.validate_assessment(assessment)
    assert result.is_valid is False
    assert any("score" in err for err in result.errors)


def test_validator_large_assessment() -> None:
    obs_list = []
    claims = []
    evidence = []
    risks = []

    for i in range(100):
        claim_id = f"claim-{i}"
        ev_id = f"ev-{i}"
        obs_id = f"OBS-{i}"
        
        claims.append(DummyClaim(claim_id))
        evidence.append(DummyEvidence(ev_id, claim_id))
        
        obs_list.append(Observation(
            observation_id=obs_id,
            observation=f"Observation description {i}",
            claim_ids=[claim_id],
            evidence_ids=[ev_id],
            reasoning=f"Reasoning text {i}",
            confidence=0.9
        ))

        risks.append(Risk(
            id=f"RISK-{i}",
            description=f"Risk factor description {i}",
            severity="Low",
            likelihood="Low",
            impact="Low",
            mitigation=f"Mitigation plan {i}",
            supporting_observations=[obs_id],
            supporting_claims=[claim_id],
            supporting_evidence=[ev_id]
        ))

    assessment = AgentAssessment(
        domain="founder",
        summary="A very large scale valid assessment.",
        observations=obs_list,
        risks=risks,
        questions=[],
        confidence=ConfidenceHierarchy(
            finding_confidence=0.8,
            evidence_confidence=0.8,
            reasoning_confidence=0.8,
            overall_domain_confidence=0.8
        ),
        reasoning="A very large scale valid assessment.",
        missing_evidence=[],
        prompt_name="Founder Analysis Prompt",
        prompt_version="1.0.0",
        prompt_hash="dummy-hash",
        agent_version="1.0.0",
        generated_at=datetime.utcnow()
    )

    result = AssessmentValidator.validate_assessment(assessment, context_claims=claims, context_evidence=evidence)
    assert result.is_valid is True
    assert len(result.errors) == 0


def test_validator_exception_raising(valid_assessment_data: dict[str, Any]) -> None:
    data = valid_assessment_data.copy()
    ch_data = data.pop("confidence")
    ch_data["finding_confidence"] = 5.0  # Invalid
    
    bad_ch = ConfidenceHierarchy.model_construct(**ch_data)
    
    observations = [Observation.model_construct(**o) for o in data.pop("observations")]
    risks = [Risk.model_construct(**r) for r in data.pop("risks")]
    questions = [Question.model_construct(**q) for q in data.pop("questions")]
    missing_ev = [MissingEvidence.model_construct(**m) for m in data.pop("missing_evidence")]

    assessment = AgentAssessment.model_construct(
        observations=observations,
        risks=risks,
        questions=questions,
        missing_evidence=missing_ev,
        confidence=bad_ch,
        **data
    )
    with pytest.raises(AssessmentValidationError) as exc_info:
        AssessmentValidator.validate(assessment)

    assert "Assessment validation failed" in str(exc_info.value)
    assert len(exc_info.value.errors) > 0
