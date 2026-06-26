import re
from datetime import datetime
from typing import Any
from app.modules.evaluation.schemas import AgentAssessment
from app.modules.evaluation.validation.validation_results import ValidationResult


def validate_schema_integrity(assessment: AgentAssessment, result: ValidationResult) -> None:
    """Verifies that the assessment is a valid AgentAssessment Pydantic model instance."""
    if not isinstance(assessment, AgentAssessment):
        result.is_valid = False
        result.errors.append("Schema integrity failed: assessment is not a valid AgentAssessment instance")
        result.ontology_violations.append("Object is not an instance of AgentAssessment")


def validate_required_fields(assessment: AgentAssessment, result: ValidationResult) -> None:
    """Checks that all top-level required fields are populated in the assessment."""
    required = ["domain", "summary", "observations", "risks", "questions", "confidence", "reasoning", "missing_evidence"]
    for field in required:
        val = getattr(assessment, field, None)
        if val is None:
            result.is_valid = False
            result.errors.append(f"Required field '{field}' is missing or None")
            result.ontology_violations.append(f"Missing required top-level field '{field}'")

    # Explicit metadata fields validation
    metadata_fields = ["prompt_name", "prompt_version", "prompt_hash", "agent_version", "generated_at"]
    for field in metadata_fields:
        val = getattr(assessment, field, None)
        if val is None or val == "":
            result.is_valid = False
            result.errors.append(f"Required metadata field '{field}' is missing or empty")
            result.ontology_violations.append(f"Missing metadata field '{field}'")


def validate_duplicate_objects(assessment: AgentAssessment, result: ValidationResult) -> None:
    """Checks for duplicate IDs and duplicate content across observations, risks, and questions."""
    all_ids = set()

    # 1. Observations
    obs_texts = set()
    for obs in assessment.observations:
        if not obs.observation_id:
            result.is_valid = False
            result.errors.append("Observation has empty or missing observation_id")
        elif obs.observation_id in all_ids:
            result.is_valid = False
            result.duplicate_objects.append(f"Duplicate Observation ID found: {obs.observation_id}")
            result.errors.append(f"Duplicate ID '{obs.observation_id}'")
        else:
            all_ids.add(obs.observation_id)

        clean_obs = obs.observation.strip().lower()
        if clean_obs in obs_texts:
            result.warnings.append(f"Duplicate Observation content detected: '{obs.observation[:30]}...'")
        else:
            obs_texts.add(clean_obs)

    # 2. Risks
    risk_texts = set()
    for risk in assessment.risks:
        if not risk.id:
            result.is_valid = False
            result.errors.append("Risk has empty or missing ID")
        elif risk.id in all_ids:
            result.is_valid = False
            result.duplicate_objects.append(f"Duplicate Risk ID found: {risk.id}")
            result.errors.append(f"Duplicate ID '{risk.id}'")
        else:
            all_ids.add(risk.id)

        clean_risk = risk.description.strip().lower()
        if clean_risk in risk_texts:
            result.warnings.append(f"Duplicate Risk content detected: '{risk.description[:30]}...'")
        else:
            risk_texts.add(clean_risk)

    # 3. Questions
    qst_texts = set()
    for qst in assessment.questions:
        if not qst.id:
            result.is_valid = False
            result.errors.append("Question has empty or missing ID")
        elif qst.id in all_ids:
            result.is_valid = False
            result.duplicate_objects.append(f"Duplicate Question ID found: {qst.id}")
            result.errors.append(f"Duplicate ID '{qst.id}'")
        else:
            all_ids.add(qst.id)

        clean_qst = qst.question.strip().lower()
        if clean_qst in qst_texts:
            result.warnings.append(f"Duplicate Question content detected: '{qst.question[:30]}...'")
        else:
            qst_texts.add(clean_qst)


def validate_timestamps_and_versions(assessment: AgentAssessment, result: ValidationResult) -> None:
    """Verifies that versions and timestamps are in a valid format."""
    # Check agent version format
    if assessment.agent_version:
        ver_str = str(assessment.agent_version)
        if not re.match(r"^\d+(\.\d+){0,2}$", ver_str):
            result.warnings.append(f"Agent version format '{ver_str}' is not standard SemVer")

    # Check prompt version format
    if assessment.prompt_version:
        ver_str = str(assessment.prompt_version)
        if not re.match(r"^\d+(\.\d+){0,2}$", ver_str):
            result.warnings.append(f"Prompt version format '{ver_str}' is not standard SemVer")

    # Check generated_at timestamp
    if assessment.generated_at:
        # If it's a datetime object, it's valid. If it's serializing to string, check ISO-8601 format
        if isinstance(assessment.generated_at, str):
            iso_pattern = r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$"
            if not re.match(iso_pattern, assessment.generated_at):
                result.warnings.append(f"Timestamp '{assessment.generated_at}' is not in ISO-8601 format")


def validate_confidence_rules(assessment: AgentAssessment, result: ValidationResult) -> None:
    """Ensures that all confidence values lie strictly between 0.0 and 1.0 (inclusive)."""
    ch = getattr(assessment, "confidence", None)
    if ch:
        confidences = {
            "finding_confidence": ch.finding_confidence,
            "evidence_confidence": ch.evidence_confidence,
            "reasoning_confidence": ch.reasoning_confidence,
            "overall_domain_confidence": ch.overall_domain_confidence,
        }
        for name, val in confidences.items():
            if not (0.0 <= val <= 1.0):
                result.is_valid = False
                result.errors.append(f"Confidence score '{name}' must be between 0.0 and 1.0")
                result.confidence_issues.append(f"Confidence hierarchy '{name}' out of bounds: {val}")

    # Check individual observation confidence scores
    for obs in assessment.observations:
        if not (0.0 <= obs.confidence <= 1.0):
            result.is_valid = False
            result.errors.append(f"Observation '{obs.observation_id}' confidence must be between 0.0 and 1.0")
            result.confidence_issues.append(f"Observation '{obs.observation_id}' confidence out of bounds: {obs.confidence}")

    # Check individual risk confidence scores if present
    for risk in assessment.risks:
        conf = getattr(risk, "confidence", None)
        if conf is not None:
            if not (0.0 <= conf <= 1.0):
                result.is_valid = False
                result.errors.append(f"Risk '{risk.id}' confidence must be between 0.0 and 1.0")
                result.confidence_issues.append(f"Risk '{risk.id}' confidence out of bounds: {conf}")


def validate_traceability_rules(
    assessment: AgentAssessment, 
    result: ValidationResult,
    context_claims: list[Any] | None = None,
    context_evidence: list[Any] | None = None
) -> None:
    """Enforces bi-directional reference matching from observations to claims, evidence, and documents."""
    claims_dict = {}
    evidence_dict = {}

    if context_claims:
        claims_dict = {str(c.id): c for c in context_claims}
    if context_evidence:
        evidence_dict = {str(ev.id): ev for ev in context_evidence}

    obs_ids = {obs.observation_id for obs in assessment.observations}

    # 1. Observation Traceability
    for obs in assessment.observations:
        if not obs.claim_ids:
            result.is_valid = False
            result.errors.append(f"Traceability breach: Observation '{obs.observation_id}' must reference at least one Claim ID")
            result.missing_evidence.append(f"Observation '{obs.observation_id}' has no supporting claims")
            continue

        if not obs.evidence_ids:
            result.is_valid = False
            result.errors.append(f"Traceability breach: Observation '{obs.observation_id}' must reference at least one Evidence ID")
            result.missing_evidence.append(f"Observation '{obs.observation_id}' has no supporting evidence")
            continue

        for claim_id in obs.claim_ids:
            claim_id_str = str(claim_id)
            if context_claims and claim_id_str not in claims_dict:
                result.is_valid = False
                result.errors.append(f"Broken Reference: Observation '{obs.observation_id}' references non-existent Claim '{claim_id_str}'")
                result.broken_references.append(f"Observation '{obs.observation_id}' -> Claim '{claim_id_str}'")
                continue

            # Check that Claim references Evidence
            claim_obj = claims_dict.get(claim_id_str)
            if claim_obj:
                # Build list of evidence associated with this claim
                linked_evs = [ev for ev in context_evidence or [] if str(ev.claim_id) == claim_id_str]
                if not linked_evs:
                    result.is_valid = False
                    result.errors.append(f"Traceability breach: Claim '{claim_id_str}' must reference at least one Evidence ID")
                    result.missing_evidence.append(f"Claim '{claim_id_str}' has no evidence linked")
                    continue

                for ev in linked_evs:
                    # Check that Evidence references Document
                    doc_id = getattr(ev, "source_document_id", getattr(ev, "document_id", None))
                    if not doc_id:
                        result.is_valid = False
                        result.errors.append(f"Traceability breach: Evidence '{ev.id}' must reference a Document ID")
                        result.missing_evidence.append(f"Evidence '{ev.id}' has no document reference")

        for ev_id in obs.evidence_ids:
            ev_id_str = str(ev_id)
            if context_evidence and ev_id_str not in evidence_dict:
                result.is_valid = False
                result.errors.append(f"Broken Reference: Observation '{obs.observation_id}' references non-existent Evidence '{ev_id_str}'")
                result.broken_references.append(f"Observation '{obs.observation_id}' -> Evidence '{ev_id_str}'")

    # 2. Risk Rules
    for risk in assessment.risks:
        # Check Observation references
        if not risk.supporting_observations:
            result.is_valid = False
            result.errors.append(f"Referential breach: Risk '{risk.id}' must reference at least one Observation ID")
            result.broken_references.append(f"Risk '{risk.id}' has no supporting observations")
        else:
            for obs_id in risk.supporting_observations:
                if obs_id not in obs_ids:
                    result.is_valid = False
                    result.errors.append(f"Broken Reference: Risk '{risk.id}' references non-existent Observation '{obs_id}'")
                    result.broken_references.append(f"Risk '{risk.id}' -> Observation '{obs_id}'")

        # Check Claim references
        if not risk.supporting_claims:
            result.is_valid = False
            result.errors.append(f"Referential breach: Risk '{risk.id}' must reference at least one Claim ID")
            result.broken_references.append(f"Risk '{risk.id}' has no supporting claims")
        else:
            for claim_id in risk.supporting_claims:
                claim_id_str = str(claim_id)
                if context_claims and claim_id_str not in claims_dict:
                    result.is_valid = False
                    result.errors.append(f"Broken Reference: Risk '{risk.id}' references non-existent Claim '{claim_id_str}'")
                    result.broken_references.append(f"Risk '{risk.id}' -> Claim '{claim_id_str}'")

        # Check Evidence references
        if not risk.supporting_evidence:
            result.is_valid = False
            result.errors.append(f"Referential breach: Risk '{risk.id}' must reference at least one Evidence ID")
            result.broken_references.append(f"Risk '{risk.id}' has no supporting evidence")
        else:
            for ev_id in risk.supporting_evidence:
                ev_id_str = str(ev_id)
                if context_evidence and ev_id_str not in evidence_dict:
                    result.is_valid = False
                    result.errors.append(f"Broken Reference: Risk '{risk.id}' references non-existent Evidence '{ev_id_str}'")
                    result.broken_references.append(f"Risk '{risk.id}' -> Evidence '{ev_id_str}'")


def validate_ontology_compliance(assessment: AgentAssessment, result: ValidationResult) -> None:
    """Verifies that no numeric scores, verdicts, or funding recommendations exist inside any text fields."""
    forbidden_keys = {
        "score", "domain_score", "overall_score", "investment_score", "funding_score", 
        "verdict", "recommendation_type", "approval", "rejection"
    }
    
    # Check text fields for scores or verdicts
    text_check = (
        str(assessment.reasoning) + " " + 
        str(assessment.summary) + " " +
        " ".join(obs.observation for obs in assessment.observations) + " " +
        " ".join(risk.description for risk in assessment.risks)
    ).lower()

    patterns = [
        r"\bscore\b", r"\bviability rating\b", r"\bfunding recommendation\b", 
        r"\bincubation verdict\b", r"\bapproval\b", r"\brejection\b", r"\brecommendation\b",
        r"\bverdict\b", r"\bincubation decision\b", r"\bfunding decision\b",
        r"\brating\b", r"\brank\b", r"\breject\b", r"\bincubate\b", r"\bdo not incubate\b",
        r"\binvest\b", r"\bdo not invest\b"
    ]
    for pattern in patterns:
        if re.search(pattern, text_check):
            result.is_valid = False
            result.ontology_violations.append(f"Ontology compliance error: Forbidden term '{pattern}' found in text.")
            result.errors.append(f"Ontology breach: contains '{pattern}'")


def validate_risk_expert_schema(assessment: AgentAssessment, result: ValidationResult) -> None:
    """If the domain is 'risk', enforces that every risk contains all required RiskExpert fields."""
    if assessment.domain == "risk":
        allowed_categories = {"technical", "execution", "market", "competition", "financial", "regulatory", "ip"}
        for risk in assessment.risks:
            # Check mandatory presence
            if not getattr(risk, "risk_id", None):
                result.is_valid = False
                result.errors.append(f"Risk '{risk.id}' is missing mandatory 'risk_id'")
            
            category = getattr(risk, "category", None)
            if not category:
                result.is_valid = False
                result.errors.append(f"Risk '{risk.id}' is missing mandatory 'category'")
            elif category not in allowed_categories:
                result.is_valid = False
                result.errors.append(f"Risk '{risk.id}' category '{category}' is invalid. Must be one of {allowed_categories}")
            
            if getattr(risk, "confidence", None) is None:
                result.is_valid = False
                result.errors.append(f"Risk '{risk.id}' is missing mandatory 'confidence'")
            
            if not getattr(risk, "reasoning", None):
                result.is_valid = False
                result.errors.append(f"Risk '{risk.id}' is missing mandatory 'reasoning'")
            
            if not risk.supporting_observations:
                result.is_valid = False
                result.errors.append(f"Risk '{risk.id}' is missing mandatory 'supporting_observations'")
            
            if not risk.supporting_claims:
                result.is_valid = False
                result.errors.append(f"Risk '{risk.id}' is missing mandatory 'supporting_claims'")
                
            if not risk.supporting_evidence:
                result.is_valid = False
                result.errors.append(f"Risk '{risk.id}' is missing mandatory 'supporting_evidence'")
