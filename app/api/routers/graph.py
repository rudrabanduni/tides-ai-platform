from fastapi import APIRouter, Depends, Request, Path
from uuid import UUID
import json

from app.api.responses import make_response
from app.api.dependencies import get_evaluation_service, EvaluationService
from app.modules.evaluation.graph.graph_serializer import to_json as graph_to_json

router = APIRouter(tags=["Graph"])

@router.get("/graph/{startup_id}")
def get_graph(
    request: Request,
    startup_id: UUID = Path(...),
    eval_service: EvaluationService = Depends(get_evaluation_service)
):
    graph = eval_service.get_graph(str(startup_id))
    graph_dict = json.loads(graph_to_json(graph))
    return make_response(request, data=graph_dict, message="Observation graph retrieved successfully")

@router.get("/graph/{startup_id}/trace")
def get_graph_trace(
    request: Request,
    startup_id: UUID = Path(...),
    eval_service: EvaluationService = Depends(get_evaluation_service)
):
    graph = eval_service.get_graph(str(startup_id))
    # Return provenance cache containing O(1) audit logs for all evaluation nodes
    trace_data = getattr(graph, "provenance_cache", {})
    # If provenance cache is unpopulated or empty, rebuild it
    if not trace_data:
        from app.modules.evaluation.graph.graph_builder import ObservationGraphBuilder
        ObservationGraphBuilder._populate_provenance_cache(graph)
        trace_data = getattr(graph, "provenance_cache", {})
        
    return make_response(request, data=trace_data, message="Graph lineage trace retrieved successfully")

@router.get("/graph/{startup_id}/observations")
def get_graph_observations(
    request: Request,
    startup_id: UUID = Path(...),
    eval_service: EvaluationService = Depends(get_evaluation_service)
):
    graph = eval_service.get_graph(str(startup_id))
    obs_list = [obs.model_dump() if hasattr(obs, "model_dump") else obs.__dict__ for obs in graph.observations.values()]
    return make_response(request, data=obs_list, message="Observations retrieved successfully")

@router.get("/graph/{startup_id}/risks")
def get_graph_risks(
    request: Request,
    startup_id: UUID = Path(...),
    eval_service: EvaluationService = Depends(get_evaluation_service)
):
    graph = eval_service.get_graph(str(startup_id))
    risks_list = [risk.model_dump() if hasattr(risk, "model_dump") else risk.__dict__ for risk in graph.risks.values()]
    return make_response(request, data=risks_list, message="Risks retrieved successfully")

@router.get("/graph/{startup_id}/questions")
def get_graph_questions(
    request: Request,
    startup_id: UUID = Path(...),
    eval_service: EvaluationService = Depends(get_evaluation_service)
):
    graph = eval_service.get_graph(str(startup_id))
    questions_list = [q.model_dump() if hasattr(q, "model_dump") else q.__dict__ for q in graph.questions.values()]
    return make_response(request, data=questions_list, message="Questions retrieved successfully")
