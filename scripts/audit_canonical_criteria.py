import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from app.modules.evaluation.domains.registry import CRITERIA_DIRECTORY

def audit():
    graph_path = REPO_ROOT / "uploads" / "graphs" / "a246f3a5-b797-43fc-9dc3-3e603e3b37b9.json"
    with open(graph_path, "r", encoding="utf-8") as f:
        g = json.load(f)

    domain_reports = g.get("domain_reports", {})
    claims = g.get("claims", {})

    print(f"Total Registry Criteria: {len(CRITERIA_DIRECTORY)}")
    
    counts = {
        "ASSESSED": 0,
        "NOT_ASSESSED": 0,
        "NOT_APPLICABLE": 0,
        "INTAKE_DOCUMENTED": 0
    }
    
    scored_counts = {
        "scored": 0,
        "unscored_or_zero": 0
    }

    results = []

    for cid, info in CRITERIA_DIRECTORY.items():
        domain = info["domain"]
        cname = info["name"]
        slide = info.get("slide", 1)
        is_required = info.get("is_required", True)
        is_conditional = info.get("is_conditional", False)

        if domain == "intake_completeness":
            # Check claims
            claim_match = None
            for c in claims.values():
                ctext = c.get("claim_text", "")
                if cid.lower().replace("-", "_") in ctext.lower():
                    claim_match = ctext
                    break
            status = "ASSESSED" if claim_match else "NOT_ASSESSED"
            res = {
                "criterion_id": cid,
                "criterion_name": cname,
                "domain": domain,
                "has_assessment": claim_match is not None,
                "has_evidence": True if claim_match else False,
                "score": None,
                "score_max": None,
                "verification_status": "DOCUMENT_EVIDENCED" if claim_match else "MISSING_INFORMATION",
                "final_status": "ASSESSED" if claim_match else "NOT_ASSESSED",
                "reason": "Evaluated during intake cover metadata extraction." if claim_match else "Missing intake metadata.",
                "extracted_value": claim_match
            }
            results.append(res)
            counts[res["final_status"]] += 1
            continue

        d_rep = domain_reports.get(domain, {})
        ce = d_rep.get("criteria_evaluations", {})
        eval_item = ce.get(cid)

        if eval_item is not None:
            has_assessment = True
            ev_ids = eval_item.get("evidence_ids", [])
            has_evidence = len(ev_ids) > 0
            raw_score = eval_item.get("score")
            v_status = eval_item.get("verification_status", "UNKNOWN")
            extracted = eval_item.get("extracted_startup_response")
            narrative = eval_item.get("assessment_narrative")
            
            # Determine canonical status
            if v_status == "NOT_APPLICABLE" or (is_conditional and not extracted):
                final_status = "NOT_APPLICABLE"
            elif has_assessment:
                final_status = "ASSESSED"
            else:
                final_status = "NOT_ASSESSED"

            res = {
                "criterion_id": cid,
                "criterion_name": cname,
                "domain": domain,
                "has_assessment": True,
                "has_evidence": has_evidence,
                "score": raw_score,
                "score_max": 10.0,
                "verification_status": v_status,
                "final_status": final_status,
                "reason": f"Evaluated under {domain} domain." if final_status == "ASSESSED" else "Conditional criterion not applicable to current stage.",
                "extracted_value": extracted,
                "narrative": narrative
            }
        else:
            final_status = "NOT_ASSESSED"
            res = {
                "criterion_id": cid,
                "criterion_name": cname,
                "domain": domain,
                "has_assessment": False,
                "has_evidence": False,
                "score": None,
                "score_max": 10.0,
                "verification_status": "MISSING_INFORMATION",
                "final_status": "NOT_ASSESSED",
                "reason": f"No assessment generated in domain_reports['{domain}'].",
                "extracted_value": None,
                "narrative": None
            }

        results.append(res)
        counts[final_status] += 1
        if res["score"] is not None:
            scored_counts["scored"] += 1
        else:
            scored_counts["unscored_or_zero"] += 1

    print("\nCriterion Audit Counts:")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    print("Scored counts:", scored_counts)
    
    # Check criteria with score 0
    zero_scored = [r for r in results if r["score"] == 0 or r["score"] == 0.0]
    print(f"\nCriteria with score == 0: {len(zero_scored)}")
    for z in zero_scored:
        print(f"  {z['criterion_id']}: {z['criterion_name']} | status={z['verification_status']} | extracted={str(z['extracted_value'])[:40]} | narr={str(z['narrative'])[:50]}")

if __name__ == "__main__":
    audit()
