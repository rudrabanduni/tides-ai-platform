from fastapi import APIRouter, Depends, Request, Query, Path
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.api.responses import make_response
from app.api.dependencies import get_committee_service, CommitteeService
from app.api.pagination import PaginationParams, paginate_list

router = APIRouter(tags=["Committee"])

@router.get("/committee")
def get_all_decisions(
    request: Request,
    recommendation: Optional[str] = Query(None, description="Filter by Recommendation enum"),
    priority: Optional[str] = Query(None, description="Filter by Investment Priority enum"),
    pagination: PaginationParams = Depends(),
    committee_service: CommitteeService = Depends(get_committee_service)
):
    decisions = committee_service.get_decisions()
    
    # Apply filters
    if recommendation:
        decisions = [d for d in decisions if d.recommendation.value.lower() == recommendation.lower()]
    if priority:
        decisions = [d for d in decisions if d.investment_priority.value.lower() == priority.lower()]
        
    formatted = [d.model_dump() if hasattr(d, "model_dump") else d.__dict__ for d in decisions]
    res_data = paginate_list(formatted, pagination, default_sort_key="portfolio_rank")
    return make_response(request, data=res_data, message="Committee decisions retrieved successfully")

@router.get("/committee/incubate")
def get_incubate_decisions(
    request: Request,
    pagination: PaginationParams = Depends(),
    committee_service: CommitteeService = Depends(get_committee_service)
):
    decisions = committee_service.get_incubate()
    formatted = [d.model_dump() if hasattr(d, "model_dump") else d.__dict__ for d in decisions]
    res_data = paginate_list(formatted, pagination, default_sort_key="portfolio_rank")
    return make_response(request, data=res_data, message="Committee incubation decisions retrieved successfully")

@router.get("/committee/pending-dd")
def get_pending_dd_decisions(
    request: Request,
    pagination: PaginationParams = Depends(),
    committee_service: CommitteeService = Depends(get_committee_service)
):
    decisions = committee_service.get_pending_dd()
    formatted = [d.model_dump() if hasattr(d, "model_dump") else d.__dict__ for d in decisions]
    res_data = paginate_list(formatted, pagination, default_sort_key="portfolio_rank")
    return make_response(request, data=res_data, message="Committee pending due diligence decisions retrieved successfully")

@router.get("/committee/deferred")
def get_deferred_decisions(
    request: Request,
    pagination: PaginationParams = Depends(),
    committee_service: CommitteeService = Depends(get_committee_service)
):
    decisions = committee_service.get_deferred()
    formatted = [d.model_dump() if hasattr(d, "model_dump") else d.__dict__ for d in decisions]
    res_data = paginate_list(formatted, pagination, default_sort_key="portfolio_rank")
    return make_response(request, data=res_data, message="Committee deferred decisions retrieved successfully")

@router.get("/committee/{startup_id}")
def get_startup_decision(
    request: Request,
    startup_id: UUID = Path(...),
    committee_service: CommitteeService = Depends(get_committee_service)
):
    decision = committee_service.get_decision(startup_id)
    formatted = decision.model_dump() if hasattr(decision, "model_dump") else decision.__dict__
    return make_response(request, data=formatted, message="Startup committee decision retrieved successfully")
