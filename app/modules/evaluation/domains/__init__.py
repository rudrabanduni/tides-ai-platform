"""app.modules.evaluation.domains - Six Canonical Domain Specialist Evaluators for TIDES-AI."""

from app.modules.evaluation.domains.registry import (
    CANONICAL_DOMAINS,
    CRITERIA_DIRECTORY,
    get_domain_for_criterion,
    get_criteria_for_domain,
    get_criterion_metadata,
)
from app.modules.evaluation.domains.base import CanonicalDomainExpert
from app.modules.evaluation.domains.problem_solution import ProblemSolutionExpert
from app.modules.evaluation.domains.market_opportunity import MarketOpportunityExpert
from app.modules.evaluation.domains.founder_team import FounderTeamExpert
from app.modules.evaluation.domains.commercialisation import CommercialisationExpert
from app.modules.evaluation.domains.innovation_impact import InnovationImpactExpert
from app.modules.evaluation.domains.financials_support import FinancialsSupportExpert

__all__ = [
    "CANONICAL_DOMAINS",
    "CRITERIA_DIRECTORY",
    "get_domain_for_criterion",
    "get_criteria_for_domain",
    "get_criterion_metadata",
    "CanonicalDomainExpert",
    "ProblemSolutionExpert",
    "MarketOpportunityExpert",
    "FounderTeamExpert",
    "CommercialisationExpert",
    "InnovationImpactExpert",
    "FinancialsSupportExpert",
]
