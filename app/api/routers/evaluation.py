from fastapi import APIRouter, Depends, Request, BackgroundTasks, status, Path
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
import json

from app.db.session import get_db
from app.api.responses import make_response
from app.api.dependencies import get_evaluation_service, EvaluationService
from app.modules.evaluation.graph.graph_serializer import to_json as graph_to_json

router = APIRouter(tags=["Evaluation"])

class EvaluateInput(BaseModel):
    startup_id: UUID

@router.post("/evaluate", status_code=status.HTTP_202_ACCEPTED)
def evaluate_startup_post(
    request: Request,
    payload: EvaluateInput,
    background_tasks: BackgroundTasks,
    eval_service: EvaluationService = Depends(get_evaluation_service)
):
    eval_service.evaluate_startup(payload.startup_id, background_tasks)
    return make_response(
        request,
        data={"startup_id": str(payload.startup_id), "status": "queued"},
        message="Startup evaluation queued successfully in the background"
    )

@router.post("/evaluate/{startup_id}", status_code=status.HTTP_202_ACCEPTED)
def evaluate_startup_path(
    request: Request,
    background_tasks: BackgroundTasks,
    startup_id: UUID = Path(...),
    eval_service: EvaluationService = Depends(get_evaluation_service)
):
    eval_service.evaluate_startup(startup_id, background_tasks)
    return make_response(
        request,
        data={"startup_id": str(startup_id), "status": "queued"},
        message="Startup evaluation queued successfully in the background"
    )

@router.get("/evaluation/{startup_id}")
def get_evaluation_result(
    request: Request,
    startup_id: UUID = Path(...),
    eval_service: EvaluationService = Depends(get_evaluation_service)
):
    graph = eval_service.get_graph(str(startup_id))
    
    # Extract high-level summary metadata
    inv_asm = graph.investment_assessment
    exec_asm = graph.executive_assessment
    
    metadata = {
        "startup_id": str(startup_id),
        "investment_score": inv_asm.investment_score if inv_asm else None,
        "recommendation": inv_asm.recommendation.value if inv_asm else None,
        "confidence": inv_asm.confidence if inv_asm else None,
        "active_risks_count": len(graph.risks),
        "unresolved_conflicts_count": graph.graph_stats.unresolved_conflicts,
        "graph_hash": graph.graph_hash
    }
    
    # Full graph deserialized to dict to return in 'data'
    graph_dict = json.loads(graph_to_json(graph))
    
    return make_response(
        request,
        data=graph_dict,
        message="Evaluation graph retrieved successfully",
        metadata=metadata
    )
