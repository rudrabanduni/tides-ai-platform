from fastapi import APIRouter, Depends, Request, Query, Path
from sqlalchemy.orm import Session
from typing import Optional, List

from app.api.responses import make_response
from app.api.dependencies import get_portfolio_service, PortfolioService
from app.api.pagination import PaginationParams, paginate_list

router = APIRouter(tags=["Portfolio"])

@router.get("/portfolio")
def get_portfolio(
    request: Request,
    category: Optional[str] = Query(None, description="Filter by sector/category"),
    recommendation: Optional[str] = Query(None, description="Filter by investment recommendation status"),
    min_score: Optional[float] = Query(None, description="Minimum investment score"),
    max_score: Optional[float] = Query(None, description="Maximum investment score"),
    min_confidence: Optional[float] = Query(None, description="Minimum score confidence"),
    pagination: PaginationParams = Depends(),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    portfolio = portfolio_service.get_portfolio()
    if not portfolio:
        return make_response(
            request,
            data={"items": [], "pagination": {"total_count": 0, "page": 1, "page_size": pagination.page_size, "total_pages": 0, "has_next": False, "has_prev": False}},
            message="No portfolio rankings available yet"
        )
        
    entries = portfolio.entries
    
    # Apply filters
    if category:
        entries = [e for e in entries if e.category.lower() == category.lower()]
    if recommendation:
        entries = [e for e in entries if e.recommendation.lower() == recommendation.lower()]
    if min_score is not None:
        entries = [e for e in entries if e.investment_score >= min_score]
    if max_score is not None:
        entries = [e for e in entries if e.investment_score <= max_score]
    if min_confidence is not None:
        entries = [e for e in entries if e.confidence >= min_confidence]
        
    formatted = [e.model_dump() if hasattr(e, "model_dump") else e.__dict__ for e in entries]
    res_data = paginate_list(formatted, pagination, default_sort_key="rank")
    return make_response(request, data=res_data, message="Portfolio retrieved successfully")

@router.get("/portfolio/top")
def get_top_startups(
    request: Request,
    limit: int = Query(default=10, ge=1, le=100, description="Number of top startups to fetch"),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    top_entries = portfolio_service.get_top_startups(limit)
    formatted = [e.model_dump() if hasattr(e, "model_dump") else e.__dict__ for e in top_entries]
    return make_response(request, data=formatted, message="Top startups retrieved successfully")

@router.get("/portfolio/statistics")
def get_portfolio_statistics(
    request: Request,
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    stats = portfolio_service.get_statistics()
    if not stats:
        return make_response(request, data=None, message="No portfolio statistics available yet")
    formatted = stats.model_dump() if hasattr(stats, "model_dump") else stats
    return make_response(request, data=formatted, message="Portfolio statistics retrieved successfully")

@router.get("/portfolio/category/{category}")
def get_by_category(
    request: Request,
    category: str = Path(..., description="The sector category name"),
    pagination: PaginationParams = Depends(),
    portfolio_service: PortfolioService = Depends(get_portfolio_service)
):
    entries = portfolio_service.get_by_category(category)
    formatted = [e.model_dump() if hasattr(e, "model_dump") else e.__dict__ for e in entries]
    res_data = paginate_list(formatted, pagination, default_sort_key="rank")
    return make_response(request, data=res_data, message=f"Portfolio entries for category '{category}' retrieved successfully")
