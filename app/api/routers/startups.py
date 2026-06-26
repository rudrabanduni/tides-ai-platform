from fastapi import APIRouter, Depends, Request, status, Path
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel, Field
from typing import Optional

from app.db.session import get_db
from app.modules.startups.models import StartupApplication
from app.api.responses import make_response
from app.api.exceptions import StartupNotFoundError
from app.api.pagination import PaginationParams, paginate_list

router = APIRouter(tags=["Startups"])

class StartupCreateInput(BaseModel):
    startup_name: str = Field(..., max_length=255, description="Name of the startup")
    sector: Optional[str] = Field(None, max_length=128, description="Industry sector")
    stage: Optional[str] = Field(None, max_length=128, description="Development stage")
    problem_statement: Optional[str] = Field(None, description="Problem statement")
    solution_summary: Optional[str] = Field(None, description="Solution summary")
    business_model: Optional[str] = Field(None, description="Business model details")
    target_market: Optional[str] = Field(None, description="Target market analysis")
    traction_summary: Optional[str] = Field(None, description="Traction summary")
    funding_status: Optional[str] = Field(None, description="Funding status/needs")

class StartupResponseData(BaseModel):
    id: UUID
    startup_name: str
    sector: Optional[str]
    stage: Optional[str]
    current_status: str
    problem_statement: Optional[str]
    solution_summary: Optional[str]
    business_model: Optional[str]
    target_market: Optional[str]
    traction_summary: Optional[str]
    funding_status: Optional[str]
    created_at: str

@router.post("/startups", status_code=status.HTTP_201_CREATED)
def create_startup(request: Request, payload: StartupCreateInput, db: Session = Depends(get_db)):
    startup = StartupApplication(
        startup_name=payload.startup_name,
        sector=payload.sector,
        stage=payload.stage,
        problem_statement=payload.problem_statement,
        solution_summary=payload.solution_summary,
        business_model=payload.business_model,
        target_market=payload.target_market,
        traction_summary=payload.traction_summary,
        funding_status=payload.funding_status
    )
    db.add(startup)
    db.commit()
    db.refresh(startup)
    
    # Format response dict
    data = {
        "id": str(startup.id),
        "startup_name": startup.startup_name,
        "sector": startup.sector,
        "stage": startup.stage,
        "current_status": startup.current_status.value if hasattr(startup.current_status, "value") else str(startup.current_status),
        "problem_statement": startup.problem_statement,
        "solution_summary": startup.solution_summary,
        "business_model": startup.business_model,
        "target_market": startup.target_market,
        "traction_summary": startup.traction_summary,
        "funding_status": startup.funding_status,
        "created_at": startup.created_at.isoformat() + "Z" if hasattr(startup, "created_at") and startup.created_at else None
    }
    
    return make_response(request, data=data, message="Startup application registered successfully")

@router.get("/startups")
def list_startups(request: Request, pagination: PaginationParams = Depends(), db: Session = Depends(get_db)):
    query = db.query(StartupApplication)
    
    # Fetch all matching entries
    startups = query.all()
    
    # Map to JSON-friendly structures
    formatted = []
    for startup in startups:
        formatted.append({
            "id": str(startup.id),
            "startup_name": startup.startup_name,
            "sector": startup.sector,
            "stage": startup.stage,
            "current_status": startup.current_status.value if hasattr(startup.current_status, "value") else str(startup.current_status),
            "problem_statement": startup.problem_statement,
            "solution_summary": startup.solution_summary,
            "business_model": startup.business_model,
            "target_market": startup.target_market,
            "traction_summary": startup.traction_summary,
            "funding_status": startup.funding_status,
            "created_at": startup.created_at.isoformat() + "Z" if hasattr(startup, "created_at") and startup.created_at else None
        })
        
    res_data = paginate_list(formatted, pagination, default_sort_key="startup_name")
    return make_response(request, data=res_data, message="Startups retrieved successfully")

@router.get("/startups/{startup_id}")
def get_startup(request: Request, startup_id: UUID = Path(...), db: Session = Depends(get_db)):
    startup = db.query(StartupApplication).filter(StartupApplication.id == startup_id).first()
    if not startup:
        raise StartupNotFoundError(str(startup_id))
        
    data = {
        "id": str(startup.id),
        "startup_name": startup.startup_name,
        "sector": startup.sector,
        "stage": startup.stage,
        "current_status": startup.current_status.value if hasattr(startup.current_status, "value") else str(startup.current_status),
        "problem_statement": startup.problem_statement,
        "solution_summary": startup.solution_summary,
        "business_model": startup.business_model,
        "target_market": startup.target_market,
        "traction_summary": startup.traction_summary,
        "funding_status": startup.funding_status,
        "created_at": startup.created_at.isoformat() + "Z" if hasattr(startup, "created_at") and startup.created_at else None
    }
    return make_response(request, data=data, message="Startup details retrieved successfully")

from app.modules.auth.dependencies import AdminUser

@router.delete("/startups/{startup_id}")
def delete_startup(
    request: Request,
    current_user: AdminUser,
    startup_id: UUID = Path(...),
    db: Session = Depends(get_db)
):
    startup = db.query(StartupApplication).filter(StartupApplication.id == startup_id).first()
    if not startup:
        raise StartupNotFoundError(str(startup_id))
        
    db.delete(startup)
    db.commit()
    return make_response(request, data={"id": str(startup_id)}, message="Startup application deleted successfully")

