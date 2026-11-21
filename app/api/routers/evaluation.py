from fastapi import APIRouter, Depends, Request, BackgroundTasks, status, Path, UploadFile, File, Form
from sqlalchemy.orm import Session
from uuid import UUID
from pydantic import BaseModel
import json

from app.db.session import get_db
from app.api.responses import make_response
from app.api.dependencies import get_evaluation_service, EvaluationService
from app.modules.auth.dependencies import EvaluatorUser, ReadOnlyUser
from app.modules.evaluation.graph.graph_serializer import to_json as graph_to_json
from app.modules.ai.orchestrator.pipeline import coordinate_evaluation_pipeline

router = APIRouter(tags=["Evaluation"])

class EvaluateInput(BaseModel):
    startup_id: UUID

@router.post("/evaluate", status_code=status.HTTP_202_ACCEPTED)
def evaluate_startup_post(
    request: Request,
    payload: EvaluateInput,
    background_tasks: BackgroundTasks,
    current_user: EvaluatorUser,
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
    current_user: EvaluatorUser,
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
    current_user: ReadOnlyUser,
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
        "graph_hash": graph.graph_hash,
        "evaluation_mode": getattr(graph, "evaluation_mode", None),
    }
    
    # Full graph deserialized to dict to return in 'data'
    graph_dict = json.loads(graph_to_json(graph))

    sup_review = getattr(graph, "supervisory_review", None) or getattr(graph, "final_review", None)
    if not sup_review and graph.report:
        sup_review = getattr(graph.report, "final_review", None)
    if sup_review:
        sup_dict = sup_review.model_dump() if hasattr(sup_review, "model_dump") else (sup_review if isinstance(sup_review, dict) else getattr(sup_review, "__dict__", {}))
        graph_dict["supervisory_review"] = sup_dict
        graph_dict["final_review"] = sup_dict

    dom_reports = getattr(graph, "domain_reports", None) or (getattr(graph.report, "domain_reports", None) if graph.report else None)
    if dom_reports and isinstance(dom_reports, dict):
        graph_dict["domain_reports"] = {
            k: (v.model_dump() if hasattr(v, "model_dump") else (v if isinstance(v, dict) else getattr(v, "__dict__", {})))
            for k, v in dom_reports.items()
        }
    
    return make_response(
        request,
        data=graph_dict,
        message="Evaluation graph retrieved successfully",
        metadata=metadata
    )


@router.post("/evaluate-startup", status_code=status.HTTP_201_CREATED)
async def evaluate_startup_end_to_end(
    request: Request,
    current_user: EvaluatorUser,
    startup_name: str = Form(...),
    sector: str = Form("SaaS"),
    stage: str = Form("Pre-Seed"),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    result = await coordinate_evaluation_pipeline(
        db=db,
        startup_name=startup_name,
        sector=sector,
        stage=stage,
        files=files,
        actor_id=current_user.id,
    )
    return make_response(
        request,
        data=result,
        message="Startup evaluated successfully end-to-end"
    )
