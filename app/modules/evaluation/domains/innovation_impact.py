"""innovation_impact.py - Domain 5: Innovation, IP & Impact Specialist Expert Agent.

Owns LaunchIndex Slides 13–14 and Canonical Criteria II-01 through II-11.
Reuses capabilities from IPExpert.
Evaluates non-patent proprietary moats (data flywheel, switching costs, network effects), patent records, and UN SDG impact.
Enforces IP non-discrimination (absence of patents does NOT automatically imply lack of innovation).
"""

from typing import Any, Optional, List
from app.modules.evaluation.domains.base import CanonicalDomainExpert
from app.modules.evaluation.domain_schemas import VerificationStatus


class InnovationImpactExpert(CanonicalDomainExpert):
    """Domain 5: Innovation, IP & Impact Specialist."""

    def get_domain_key(self) -> str:
        return "innovation_impact"

    def get_fallback_prompt_key(self) -> str:
        return "ip"

    def refine_verification_status(
        self,
        criterion_id: str,
        value: Optional[str],
        default_status: VerificationStatus,
        all_claims: List[Any]
    ) -> VerificationStatus:
        """Enforces IP non-discrimination:

        Startups with no patents filed are evaluated on trade secrets, proprietary algorithms,
        or workflow moats rather than receiving an automatic failure.
        """
        if criterion_id == "II-07":  # Patent records / IP status
            if self._is_missing_placeholder(value):
                # Missing patent disclosure must never be elevated to VERIFIED_DOCUMENTED
                return (
                    VerificationStatus.MISSING_INFORMATION
                    if default_status in (VerificationStatus.VERIFIED_DOCUMENTED, VerificationStatus.MISSING_INFORMATION)
                    else default_status
                )
            lowered = str(value).strip().lower()
            if any(tok in lowered for tok in ("no ip", "no patent", "pre-patent", "trade secret", "none filed", "nil")):
                # Explicitly documented pre-patent or trade secret status must not fail as contradicted
                return (
                    VerificationStatus.VERIFIED_DOCUMENTED
                    if default_status == VerificationStatus.VERIFIED_DOCUMENTED
                    else VerificationStatus.SELF_REPORTED_ONLY
                )

        return default_status
