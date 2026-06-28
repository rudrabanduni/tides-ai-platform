from typing import Any
from app.modules.evaluation.graph.graph_models import (
    ObservationGraph, ObservationNode, EvidenceNode, ClaimNode,
    AssessmentNode, RiskNode, QuestionNode, Edge, NodeType, DocumentNode
)
from app.modules.ai.agents.models import AgentAssessment

def integrate_assessment_to_graph(graph: ObservationGraph, assessment: AgentAssessment):
    """Maps structured AgentAssessment outputs directly into the ObservationGraph.
    
    This preserves the existing report building architecture without changing code.
    """
    asm_id = f"ASM-{assessment.domain.upper()}"
    
    # 1. Assessment Node
    asm_node = AssessmentNode(
        node_id=asm_id,
        node_type=NodeType.ASSESSMENT,
        assessment_id=asm_id,
        domain=assessment.domain,
        expert_name=f"{assessment.domain.capitalize()}Expert",
        agent_version="1.0.0",
        prompt_version=assessment.execution_metadata.prompt_version,
        confidence=assessment.confidence,
        generated_at=assessment.execution_metadata.timestamp
    )
    graph.assessments[asm_id] = asm_node
    graph.assessments_by_domain.setdefault(assessment.domain, []).append(asm_id)

    # 2. Observations
    for obs in assessment.observations:
        obs_id = obs.observation_id
        obs_node = ObservationNode(
            node_id=obs_id,
            node_type=NodeType.OBSERVATION,
            observation_id=obs_id,
            domain=assessment.domain,
            observation=obs.observation,
            confidence=obs.confidence,
            consensus_status="independent"
        )
        graph.observations[obs_id] = obs_node
        graph.observations_by_domain.setdefault(assessment.domain, []).append(obs_id)

        # Edge: Assessment --GENERATED--> Observation
        edge = Edge(
            source_id=asm_id,
            source_type=NodeType.ASSESSMENT,
            target_id=obs_id,
            target_type=NodeType.OBSERVATION,
            relationship="GENERATED"
        )
        graph.edges.append(edge)
        graph.out_edges.setdefault(asm_id, []).append(edge)
        graph.in_edges.setdefault(obs_id, []).append(edge)

        # Edges: Observation --SUPPORTED_BY--> Claims
        for cid in obs.claim_ids:
            edge_claim = Edge(
                source_id=obs_id,
                source_type=NodeType.OBSERVATION,
                target_id=cid,
                target_type=NodeType.CLAIM,
                relationship="SUPPORTED_BY"
            )
            graph.edges.append(edge_claim)
            graph.out_edges.setdefault(obs_id, []).append(edge_claim)
            graph.in_edges.setdefault(cid, []).append(edge_claim)

        # Edges: Observation --SUPPORTED_BY--> Evidence
        for eid in obs.evidence_ids:
            edge_ev = Edge(
                source_id=obs_id,
                source_type=NodeType.OBSERVATION,
                target_id=eid,
                target_type=NodeType.EVIDENCE,
                relationship="SUPPORTED_BY"
            )
            graph.edges.append(edge_ev)
            graph.out_edges.setdefault(obs_id, []).append(edge_ev)
            graph.in_edges.setdefault(eid, []).append(edge_ev)

    # 3. Evidence
    for ev in assessment.supporting_evidence:
        ev_id = ev.evidence_id
        ev_node = EvidenceNode(
            node_id=ev_id,
            node_type=NodeType.EVIDENCE,
            evidence_id=ev_id,
            excerpt=ev.evidence_snippet,
            location=ev.source_document,
            confidence=1.0
        )
        graph.evidence[ev_id] = ev_node
        
        # Ensure fallback DocumentNode
        doc_id = "doc-default"
        if doc_id not in graph.documents:
            graph.documents[doc_id] = DocumentNode(
                node_id=doc_id,
                node_type=NodeType.DOCUMENT,
                document_id=doc_id,
                document_name="Source Document",
                document_type="PDF",
                uploaded_at=assessment.execution_metadata.timestamp
            )
            
        # Edge: Evidence --DERIVED_FROM--> Document
        edge_doc = Edge(
            source_id=ev_id,
            source_type=NodeType.EVIDENCE,
            target_id=doc_id,
            target_type=NodeType.DOCUMENT,
            relationship="DERIVED_FROM"
        )
        graph.edges.append(edge_doc)
        graph.out_edges.setdefault(ev_id, []).append(edge_doc)
        graph.in_edges.setdefault(doc_id, []).append(edge_doc)
        
        # Link: Claim --SUPPORTED_BY--> Evidence
        cid = ev.source_claim_id
        if cid:
            if cid not in graph.claims:
                graph.claims[cid] = ClaimNode(
                    node_id=cid,
                    node_type=NodeType.CLAIM,
                    claim_id=cid,
                    claim_text=f"Claim on {assessment.domain}"
                )
            edge_claim_ev = Edge(
                source_id=cid,
                source_type=NodeType.CLAIM,
                target_id=ev_id,
                target_type=NodeType.EVIDENCE,
                relationship="SUPPORTED_BY"
            )
            graph.edges.append(edge_claim_ev)
            graph.out_edges.setdefault(cid, []).append(edge_claim_ev)
            graph.in_edges.setdefault(ev_id, []).append(edge_claim_ev)

    # 4. Risks
    for idx, risk_str in enumerate(assessment.risks):
        risk_id = f"RISK-{assessment.domain.upper()}-{idx}"
        risk_node = RiskNode(
            node_id=risk_id,
            node_type=NodeType.RISK,
            risk_id=risk_id,
            category=assessment.domain,
            description=risk_str,
            confidence=assessment.confidence,
            reasoning="Inferred from expert evaluation"
        )
        graph.risks[risk_id] = risk_node
        graph.risks_by_category.setdefault(assessment.domain, []).append(risk_id)

        # Edge: Assessment --GENERATED--> Risk
        edge = Edge(
            source_id=asm_id,
            source_type=NodeType.ASSESSMENT,
            target_id=risk_id,
            target_type=NodeType.RISK,
            relationship="GENERATED"
        )
        graph.edges.append(edge)
        graph.out_edges.setdefault(asm_id, []).append(edge)
        graph.in_edges.setdefault(risk_id, []).append(edge)

        # Edge: Risk --REFERENCES--> Observations
        for obs in assessment.observations:
            edge_ref = Edge(
                source_id=risk_id,
                source_type=NodeType.RISK,
                target_id=obs.observation_id,
                target_type=NodeType.OBSERVATION,
                relationship="REFERENCES"
            )
            graph.edges.append(edge_ref)
            graph.out_edges.setdefault(risk_id, []).append(edge_ref)
            graph.in_edges.setdefault(obs.observation_id, []).append(edge_ref)

    # 5. Open Questions
    for idx, q_str in enumerate(assessment.open_questions):
        q_id = f"QST-{assessment.domain.upper()}-{idx}"
        q_node = QuestionNode(
            node_id=q_id,
            node_type=NodeType.QUESTION,
            question_id=q_id,
            question=q_str,
            purpose=f"Clarify {assessment.domain} detail"
        )
        graph.questions[q_id] = q_node

        # Edge: Question --REFERENCES--> Observation
        if assessment.observations:
            target_obs = assessment.observations[0].observation_id
            edge_ref_q = Edge(
                source_id=q_id,
                source_type=NodeType.QUESTION,
                target_id=target_obs,
                target_type=NodeType.OBSERVATION,
                relationship="REFERENCES"
            )
            graph.edges.append(edge_ref_q)
            graph.out_edges.setdefault(q_id, []).append(edge_ref_q)
            graph.in_edges.setdefault(target_obs, []).append(edge_ref_q)

    # 6. Update statistics
    graph.graph_stats.observation_count = len(graph.observations)
    graph.graph_stats.evidence_count = len(graph.evidence)
    graph.graph_stats.claim_count = len(graph.claims)
    graph.graph_stats.assessment_count = len(graph.assessments)
    graph.graph_stats.risk_count = len(graph.risks)
    graph.graph_stats.question_count = len(graph.questions)
    graph.graph_stats.edge_count = len(graph.edges)
