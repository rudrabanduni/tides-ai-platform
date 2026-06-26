from typing import List
from app.modules.evaluation.graph.graph_models import ObservationGraph
from app.modules.evaluation.portfolio.portfolio_models import Portfolio
from app.modules.evaluation.portfolio.portfolio_builder import PortfolioBuilder


class PortfolioEngine:
    """Entry point for Portfolio Intelligence. Delegates building and ranking to PortfolioBuilder."""

    @staticmethod
    def generate(graphs: List[ObservationGraph]) -> Portfolio:
        """Deterministically ranks startups and compiles portfolio statistics from their graphs."""
        return PortfolioBuilder.build(graphs)
