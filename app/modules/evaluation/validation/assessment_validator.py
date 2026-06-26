from typing import Any
from app.modules.evaluation.schemas import AgentAssessment
from app.modules.evaluation.validation.validation_results import ValidationResult
from app.modules.evaluation.validation.validation_exceptions import AssessmentValidationError
from app.modules.evaluation.validation.validation_rules import (
    validate_schema_integrity,
    validate_required_fields,
    validate_duplicate_objects,
    validate_timestamps_and_versions,
    validate_confidence_rules,
    validate_traceability_rules,
    validate_ontology_compliance,
    validate_risk_expert_schema
)


class AssessmentValidator:
    """Read-only validation engine that verifies every Expert assessment before it enters the Committee pipeline."""

    @staticmethod
    def validate_assessment(
        assessment: AgentAssessment,
        context_claims: list[Any] | None = None,
        context_evidence: list[Any] | None = None
    ) -> ValidationResult:
        """Runs the complete suite of structural, semantic, and traceability rules, returning a ValidationResult."""
        result = ValidationResult(is_valid=True)
        
        # 1. Base schema check
        validate_schema_integrity(assessment, result)
        if not result.is_valid:
            return result

        # 2. Run all rules
        validate_required_fields(assessment, result)
        validate_duplicate_objects(assessment, result)
        validate_timestamps_and_versions(assessment, result)
        validate_confidence_rules(assessment, result)
        validate_traceability_rules(assessment, result, context_claims, context_evidence)
        validate_ontology_compliance(assessment, result)
        validate_risk_expert_schema(assessment, result)

        return result

    @staticmethod
    def validate(
        assessment: AgentAssessment,
        context_claims: list[Any] | None = None,
        context_evidence: list[Any] | None = None
    ) -> AgentAssessment:
        """Validates the draft assessment. Raises AssessmentValidationError if any blocking errors are found."""
        result = AssessmentValidator.validate_assessment(assessment, context_claims, context_evidence)
        if not result.is_valid:
            raise AssessmentValidationError(
                message=f"Assessment validation failed with {len(result.errors)} errors.",
                errors=result.errors
            )
        return assessment
