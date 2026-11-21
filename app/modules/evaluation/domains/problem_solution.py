"""problem_solution.py - Domain 1: Problem & Solution Specialist Expert Agent.

Owns LaunchIndex Slides 3–5 and Canonical Criteria PS-01 through PS-13.
Reuses capabilities from ProductExpert and TRLExpert.
Implements conditional prototype evaluation (TRL 1-4 ventures are not failed for absent prototypes).
"""

from typing import Any, Optional, List
from app.modules.evaluation.domains.base import CanonicalDomainExpert
from app.modules.evaluation.domain_schemas import VerificationStatus


class ProblemSolutionExpert(CanonicalDomainExpert):
    """Domain 1: Problem & Solution Specialist."""

    def get_domain_key(self) -> str:
        return "problem_solution"

    def get_fallback_prompt_key(self) -> str:
        return "product"

    def refine_verification_status(
        self,
        criterion_id: str,
        value: Optional[str],
        default_status: VerificationStatus,
        all_claims: List[Any]
    ) -> VerificationStatus:
        """Enforces conditional prototype logic:

        Early-stage startups (TRL <= 4) must not fail evaluation solely due to absent working prototype.
        """
        if criterion_id == "PS-10":  # Demo / Prototype Link
            trl_claim = next((c for c in all_claims if getattr(getattr(c, "field", None), "field_key", "").lower().startswith("ps_09_current_trl")), None)
            trl_val = float(trl_claim.value_number) if trl_claim and trl_claim.value_number is not None else 3.0

            if not value or value.lower() in ("none", "null", "none disclosed (conditional field)", "missing from application"):
                if trl_val <= 4:
                    return VerificationStatus.NOT_APPLICABLE
                else:
                    return VerificationStatus.UNSUPPORTED_ASSUMPTION

        return default_status
