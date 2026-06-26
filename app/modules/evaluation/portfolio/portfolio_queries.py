from typing import List, Optional, Union, Any
from app.modules.evaluation.graph.graph_models import ObservationGraph
from app.modules.evaluation.portfolio.portfolio_models import Portfolio, PortfolioEntry, PortfolioStatistics


def _ensure_portfolio(portfolio_or_graphs: Union[Portfolio, List[ObservationGraph]]) -> Portfolio:
    """Ensures we have a Portfolio object. If a list of graphs is passed, compiles it first."""
    if isinstance(portfolio_or_graphs, Portfolio):
        return portfolio_or_graphs
    from app.modules.evaluation.portfolio.portfolio_engine import PortfolioEngine
    return PortfolioEngine.generate(portfolio_or_graphs)


def get_top_n(portfolio_or_graphs: Union[Portfolio, List[ObservationGraph]], n: int) -> List[PortfolioEntry]:
    """Retrieves the top N startups in the portfolio ranking."""
    port = _ensure_portfolio(portfolio_or_graphs)
    return port.entries[:n]


def get_by_rank(portfolio_or_graphs: Union[Portfolio, List[ObservationGraph]], rank: int) -> Optional[PortfolioEntry]:
    """Retrieves the startup entry occupying the specified rank (1-indexed)."""
    port = _ensure_portfolio(portfolio_or_graphs)
    for entry in port.entries:
        if entry.rank == rank:
            return entry
    return None


def get_by_startup(portfolio_or_graphs: Union[Portfolio, List[ObservationGraph]], startup_id: str) -> Optional[PortfolioEntry]:
    """Retrieves the portfolio entry for the specified startup ID."""
    port = _ensure_portfolio(portfolio_or_graphs)
    for entry in port.entries:
        if entry.startup_id == startup_id:
            return entry
    return None


def filter_by_category(portfolio_or_graphs: Union[Portfolio, List[ObservationGraph]], category: str) -> List[PortfolioEntry]:
    """Filters portfolio entries matching the specified category/sector."""
    port = _ensure_portfolio(portfolio_or_graphs)
    # Case-insensitive comparison
    cat_lower = category.lower()
    return [e for e in port.entries if e.category.lower() == cat_lower]


def filter_by_confidence(portfolio_or_graphs: Union[Portfolio, List[ObservationGraph]], min_confidence: float) -> List[PortfolioEntry]:
    """Filters portfolio entries with confidence score >= min_confidence."""
    port = _ensure_portfolio(portfolio_or_graphs)
    return [e for e in port.entries if e.confidence >= min_confidence]


def filter_by_recommendation(portfolio_or_graphs: Union[Portfolio, List[ObservationGraph]], recommendation: str) -> List[PortfolioEntry]:
    """Filters portfolio entries with the specified recommendation."""
    port = _ensure_portfolio(portfolio_or_graphs)
    rec_lower = recommendation.lower()
    return [e for e in port.entries if e.recommendation.lower() == rec_lower]


def statistics(portfolio_or_graphs: Union[Portfolio, List[ObservationGraph]]) -> PortfolioStatistics:
    """Retrieves the portfolio statistics summary."""
    port = _ensure_portfolio(portfolio_or_graphs)
    return port.statistics
