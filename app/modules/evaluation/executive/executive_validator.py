from typing import List
from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType


class ExecutiveValidator:
    """Performs validation checks on ExecutiveAssessments, ExecutiveFindings, and Traceability maps."""

    @staticmethod
    def validate(graph: ObservationGraph) -> List[str]:
        errors = []
        exec_node = graph.executive_assessment
        if not exec_node:
            # If no executive assessment exists, validation is trivial (or we flag it if required, but here we return empty)
            return errors

        # 1. Check confidence value bounds
        if not (0.0 <= exec_node.confidence <= 1.0):
            errors.append(f"Invalid Confidence: ExecutiveAssessment confidence {exec_node.confidence} must be between 0.0 and 1.0.")

        # Gather all nodes to check existence
        all_obs_ids = set(graph.observations.keys())

        # Collect all findings
        all_findings = exec_node.key_observations + exec_node.major_risks
        finding_ids = set()
        finding_descriptions = set()

        for finding in all_findings:
            fid = finding.finding_id
            
            # Rule 4: No duplicate executive findings
            if fid in finding_ids:
                errors.append(f"Duplicate Finding ID: '{fid}' is defined multiple times in findings.")
            finding_ids.add(fid)

            desc = finding.description.strip().lower()
            if desc in finding_descriptions:
                errors.append(f"Duplicate Finding Content: Finding '{fid}' has duplicate description text: '{finding.description}'.")
            finding_descriptions.add(desc)

            # Rule 3: Every confidence value must be between 0 and 1
            if not (0.0 <= finding.confidence <= 1.0):
                errors.append(f"Invalid Confidence: Finding '{fid}' has confidence {finding.confidence} which is outside [0, 1].")

            # Rule 1: Every executive finding must trace to at least one Observation
            if not finding.supporting_observations and finding.finding_type == "OBSERVATION":
                errors.append(f"No Supporting Observations: Finding '{fid}' of type OBSERVATION has no supporting observation references.")

            # Rule 5: No orphan references
            for obs_id in finding.supporting_observations:
                if obs_id not in all_obs_ids:
                    errors.append(f"Orphan Reference: Finding '{fid}' references non-existent observation '{obs_id}'.")
                else:
                    # Rule 2: Every observation must trace to evidence
                    # We verify if this observation has at least one evidence linked (or claim linked to evidence)
                    has_evidence = False
                    
                    # Direct evidence
                    out_edges = graph.out_edges.get(obs_id, [])
                    evidence_ids = [e.target_id for e in out_edges if e.target_type == NodeType.EVIDENCE]
                    if evidence_ids:
                        has_evidence = True
                    else:
                        # Indirect via claim -> evidence
                        claim_ids = [e.target_id for e in out_edges if e.target_type == NodeType.CLAIM]
                        for cid in claim_ids:
                            claim_out_edges = graph.out_edges.get(cid, [])
                            if any(e.target_type == NodeType.EVIDENCE for e in claim_out_edges):
                                has_evidence = True
                                break
                    
                    if not has_evidence:
                        errors.append(f"Broken Evidence Lineage: Observation '{obs_id}' supporting finding '{fid}' does not trace to any evidence.")

            # Rule 6: No broken traceability
            if fid not in exec_node.traceability or not exec_node.traceability[fid]:
                errors.append(f"Broken Traceability: Finding '{fid}' is missing its traceability pedigree trace mapping.")

        # Validate unresolved conflicts exist in conflicts
        for cid in exec_node.unresolved_conflicts:
            if cid not in graph.conflicts:
                errors.append(f"Orphan Reference: Unresolved conflict reference '{cid}' does not exist in graph conflicts.")

        return errors
