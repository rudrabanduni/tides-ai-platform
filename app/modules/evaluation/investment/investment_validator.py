from typing import List
from app.modules.evaluation.graph.graph_models import ObservationGraph, NodeType
from app.modules.evaluation.investment.investment_models import InvestmentRecommendation


class InvestmentValidator:
    """Validator for InvestmentAssessment nodes, scores, recommendations, and traceability."""

    @staticmethod
    def validate(graph: ObservationGraph) -> List[str]:
        errors = []
        node = graph.investment_assessment
        if not node:
            return errors

        # 1. Validate score ranges (between 0.0 and 100.0)
        score_fields = {
            "investment_score": node.investment_score,
            "readiness_score": node.readiness_score,
            "risk_score": node.risk_score,
            "technology_score": node.technology_score,
            "market_score": node.market_score,
            "founder_score": node.founder_score,
            "financial_score": node.financial_score,
            "competition_score": node.competition_score
        }
        for field, score in score_fields.items():
            if not (0.0 <= score <= 100.0):
                errors.append(f"Invalid Score: {field} {score} must be between 0.0 and 100.0.")

        # 2. Validate confidence range (between 0.0 and 1.0)
        if not (0.0 <= node.confidence <= 1.0):
            errors.append(f"Invalid Confidence: confidence {node.confidence} must be between 0.0 and 1.0.")

        # 3. Validate recommendation consistency
        expected_rec = None
        score = node.investment_score
        if score < 40.0:
            expected_rec = InvestmentRecommendation.DO_NOT_INVEST
        elif score < 55.0:
            expected_rec = InvestmentRecommendation.REVIEW
        elif score < 70.0:
            expected_rec = InvestmentRecommendation.WATCHLIST
        elif score < 85.0:
            expected_rec = InvestmentRecommendation.INVEST
        else:
            expected_rec = InvestmentRecommendation.STRONG_INVEST

        if node.recommendation != expected_rec:
            errors.append(
                f"Inconsistent Recommendation: score {score} corresponds to "
                f"{expected_rec.value}, but assessment has {node.recommendation.value}."
            )

        # 4. Verify recommendation traceability exists
        trace = node.traceability
        if "RECOMMENDATION" not in trace:
            errors.append("Missing Traceability: Traceability map does not contain 'RECOMMENDATION' key.")
        else:
            rec_trace = trace["RECOMMENDATION"]
            if abs(rec_trace.get("investment_score", -1.0) - score) > 1e-5:
                errors.append("Traceability Mismatch: investment_score in traceability does not match actual score.")

        # 5. Check referential integrity: no orphan findings / broken references
        all_obs_ids = set(graph.observations.keys())
        all_risk_ids = set(graph.risks.keys())

        # Check Strengths (Every strength must be supported by observations)
        for idx, strength in enumerate(node.strengths):
            # Check if there is a corresponding strength trace in the traceability mapping
            # We matched strengths using "STRENGTH-{obs_id}" in engine
            found_obs_trace = False
            for k, val in trace.items():
                if k.startswith("STRENGTH-") and val and "observation" in val:
                    obs_payload = val["observation"]
                    # Match by observation string (description) or ID
                    if obs_payload and getattr(obs_payload, "observation", "") == strength:
                        obs_id = getattr(obs_payload, "observation_id", "")
                        if obs_id not in all_obs_ids:
                            errors.append(f"Broken Reference: Strength trace '{k}' references non-existent observation '{obs_id}'.")
                        found_obs_trace = True
                        break
                    elif obs_payload and isinstance(obs_payload, dict) and obs_payload.get("observation") == strength:
                        obs_id = obs_payload.get("observation_id", "")
                        if obs_id not in all_obs_ids:
                            errors.append(f"Broken Reference: Strength trace '{k}' references non-existent observation '{obs_id}'.")
                        found_obs_trace = True
                        break

            if not found_obs_trace:
                # Direct check on trace IDs
                # Let's verify that the trace contains STRENGTH keys and their values exist in observations
                strength_traces = {k: v for k, v in trace.items() if k.startswith("STRENGTH-")}
                if not strength_traces:
                    errors.append(f"No Supporting Observations: Strength '{strength}' has no traceability mapping.")

        # Check Major Risks (Every risk must be supported by evidence)
        for risk_desc in node.major_risks:
            found_risk_trace = False
            for k, val in trace.items():
                if k.startswith("RISK-") and val and "risk" in val:
                    risk_payload = val["risk"]
                    # Match by risk description
                    if risk_payload and getattr(risk_payload, "description", "") == risk_desc:
                        risk_id = getattr(risk_payload, "risk_id", "")
                        if risk_id not in all_risk_ids:
                            errors.append(f"Broken Reference: Risk trace '{k}' references non-existent risk '{risk_id}'.")
                        
                        # Verify the risk has evidence support
                        # RiskNode --REFERENCES--> Observation/Evidence
                        has_evidence = False
                        out_edges = graph.out_edges.get(risk_id, [])
                        evidence_ids = [e.target_id for e in out_edges if e.target_type == NodeType.EVIDENCE]
                        if evidence_ids:
                            has_evidence = True
                        else:
                            # Indirect via observations -> claims -> evidence
                            ref_obs = [e.target_id for e in out_edges if e.target_type == NodeType.OBSERVATION]
                            for oid in ref_obs:
                                obs_out = graph.out_edges.get(oid, [])
                                if any(e.target_type == NodeType.EVIDENCE for e in obs_out):
                                    has_evidence = True
                                    break
                                # via claims
                                claim_ids = [e.target_id for e in obs_out if e.target_type == NodeType.CLAIM]
                                for cid in claim_ids:
                                    claim_out = graph.out_edges.get(cid, [])
                                    if any(e.target_type == NodeType.EVIDENCE for e in claim_out):
                                        has_evidence = True
                                        break
                        if not has_evidence:
                            errors.append(f"Broken Evidence Lineage: Risk '{risk_id}' supporting major risk '{risk_desc}' does not trace to any evidence.")
                        found_risk_trace = True
                        break
                    elif risk_payload and isinstance(risk_payload, dict) and risk_payload.get("description") == risk_desc:
                        risk_id = risk_payload.get("risk_id", "")
                        if risk_id not in all_risk_ids:
                            errors.append(f"Broken Reference: Risk trace '{k}' references non-existent risk '{risk_id}'.")
                        
                        # Verify the risk has evidence support
                        has_evidence = False
                        out_edges = graph.out_edges.get(risk_id, [])
                        evidence_ids = [e.target_id for e in out_edges if e.target_type == NodeType.EVIDENCE]
                        if evidence_ids:
                            has_evidence = True
                        else:
                            ref_obs = [e.target_id for e in out_edges if e.target_type == NodeType.OBSERVATION]
                            for oid in ref_obs:
                                obs_out = graph.out_edges.get(oid, [])
                                if any(e.target_type == NodeType.EVIDENCE for e in obs_out):
                                    has_evidence = True
                                    break
                                claim_ids = [e.target_id for e in obs_out if e.target_type == NodeType.CLAIM]
                                for cid in claim_ids:
                                    claim_out = graph.out_edges.get(cid, [])
                                    if any(e.target_type == NodeType.EVIDENCE for e in claim_out):
                                        has_evidence = True
                                        break
                        if not has_evidence:
                            errors.append(f"Broken Evidence Lineage: Risk '{risk_id}' supporting major risk '{risk_desc}' does not trace to any evidence.")
                        found_risk_trace = True
                        break

            if not found_risk_trace:
                risk_traces = {k: v for k, v in trace.items() if k.startswith("RISK-")}
                if not risk_traces:
                    errors.append(f"No Supporting Evidence: Risk '{risk_desc}' has no traceability mapping.")

        # Check for any broken references in traceability mapping
        for key, val in trace.items():
            if key.startswith("STRENGTH-") and val and "observation" in val:
                obs_payload = val["observation"]
                obs_id = getattr(obs_payload, "observation_id", None) or (obs_payload.get("observation_id") if isinstance(obs_payload, dict) else None)
                if obs_id and obs_id not in all_obs_ids:
                    errors.append(f"Broken Reference: Traceability key '{key}' references non-existent observation '{obs_id}'.")
            elif key.startswith("RISK-") and val and "risk" in val:
                risk_payload = val["risk"]
                risk_id = getattr(risk_payload, "risk_id", None) or (risk_payload.get("risk_id") if isinstance(risk_payload, dict) else None)
                if risk_id and risk_id not in all_risk_ids:
                    errors.append(f"Broken Reference: Traceability key '{key}' references non-existent risk '{risk_id}'.")

        return errors
