from typing import Any, List, Optional
from app.modules.evaluation.graph.graph_models import ObservationGraph, ObservationNode, NodeType
from app.modules.evaluation.conflict_resolution.conflict_models import ResolutionNode


def get_resolution(graph: ObservationGraph, resolution_id: str) -> Optional[ResolutionNode]:
    """Retrieves a ResolutionNode by ID from the graph in O(1) time."""
    return graph.resolutions.get(resolution_id)


def get_conflict_resolutions(graph: ObservationGraph, conflict_id: str) -> List[ResolutionNode]:
    """Retrieves all resolutions for a given conflict or correlation ID in O(1) time."""
    res_ids = graph.resolutions_by_conflict.get(conflict_id, [])
    return [graph.resolutions[rid] for rid in res_ids if rid in graph.resolutions]


def get_observation_resolutions(graph: ObservationGraph, observation_id: str) -> List[ResolutionNode]:
    """Retrieves all resolutions where the given observation is preferred/resolved in O(1) time."""
    res_ids = graph.resolutions_by_observation.get(observation_id, [])
    return [graph.resolutions[rid] for rid in res_ids if rid in graph.resolutions]


def get_preferred_observation(graph: ObservationGraph, conflict_id: str) -> Optional[ObservationNode]:
    """Retrieves the preferred observation node (if any) associated with the resolution of a conflict."""
    res_ids = graph.resolutions_by_conflict.get(conflict_id, [])
    for rid in res_ids:
        res = graph.resolutions.get(rid)
        if res and res.preferred_observation_id:
            return graph.observations.get(res.preferred_observation_id)
    return None


def trace_resolution(graph: ObservationGraph, resolution_id: str, visited: Optional[set] = None) -> dict[str, Any]:
    """Traces a resolution node down to its conflict, observations, claims, evidence, documents, and assessments."""
    if visited is None:
        visited = set()
    
    if resolution_id in visited:
        return {}
        
    if resolution_id in graph.provenance_cache:
        return graph.provenance_cache[resolution_id]
        
    visited.add(resolution_id)
    res_node = graph.resolutions.get(resolution_id)
    if not res_node:
        return {}
        
    conflict_id = res_node.conflict_id
    conflict_node = graph.conflicts.get(conflict_id) or graph.correlations.get(conflict_id)
    
    obs_ids = []
    if conflict_node:
        if getattr(conflict_node, "node_type", None) == NodeType.CONFLICT:
            conflict_edges = graph.out_edges.get(conflict_id, [])
            claim_ids = [e.target_id for e in conflict_edges 
                         if e.target_type == NodeType.CLAIM and e.relationship == "CONFLICTS_WITH"]
            for cid in claim_ids:
                for edge in graph.in_edges.get(cid, []):
                    if edge.source_type == NodeType.OBSERVATION and edge.relationship == "SUPPORTED_BY":
                        obs_ids.append(edge.source_id)
        elif getattr(conflict_node, "node_type", None) == NodeType.CORRELATION:
            corr_edges = graph.out_edges.get(conflict_id, [])
            obs_ids = [e.target_id for e in corr_edges 
                      if e.target_type == NodeType.OBSERVATION and e.relationship == "RELATED_TO"]
                      
    obs_ids = list(dict.fromkeys(obs_ids))
    
    obs_traces = []
    from app.modules.evaluation.graph.graph_queries import trace_observation
    for oid in obs_ids:
        obs_tr = trace_observation(graph, oid, visited)
        if obs_tr:
            asm_nodes = []
            for edge in graph.in_edges.get(oid, []):
                if edge.source_type == NodeType.ASSESSMENT and edge.relationship == "GENERATED":
                    asm = graph.assessments.get(edge.source_id)
                    if asm:
                        asm_nodes.append(asm)
            obs_tr["assessments"] = asm_nodes
            obs_traces.append(obs_tr)
            
    res = {
        "resolution": res_node,
        "conflict": conflict_node,
        "observations": obs_traces
    }
    graph.provenance_cache[resolution_id] = res
    return res
