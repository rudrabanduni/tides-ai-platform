import json
import re
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
handoff_dir = REPO_ROOT / "reports" / "hand_off"
md_path = handoff_dir / "STETHAIM_FINAL_REVIEW_PACKAGE_v2.1.md"
json_path = handoff_dir / "STETHAIM_FINAL_REVIEW_PACKAGE_v2.1.json"
db_path = REPO_ROOT / "tides_ai.db"

md_content = md_path.read_text(encoding="utf-8")
js_obj = json.loads(json_path.read_text(encoding="utf-8"))

# 1. Product architecture check
md_lower = md_content.lower()
js_lower = json.dumps(js_obj, ensure_ascii=False).lower()

forbidden_arch = ["ppg", "photoplethysmography", "temperature", "thermistor", "ambient noise mic", "optical ppg"]
for fa in forbidden_arch:
    assert fa not in md_lower, f"Found {fa} in MD"
    assert fa not in js_lower, f"Found {fa} in JSON"
arch_pass = "PASS"

# 2. Unsupported wording audit
prohibited = [
    "patent ownership remains with individual founders",
    "zero external funding raised",
    "clean cap table",
    "clean institutional debt",
    "zero funding raised"
]
for p in prohibited:
    assert p not in md_lower, f"Found {p} in MD"
    assert p not in js_lower, f"Found {p} in JSON"
wording_pass = "PASS"

# 3. N/A applicability audit
na_crit = [c for c in js_obj["canonical_criteria_matrix"] if c["final_status"] == "NOT_APPLICABLE"]
assert len(na_crit) == 6
for c in na_crit:
    assert "canonical rubric applicability rule" in c["assessment_narrative"].lower(), f"N/A rule missing for {c['criterion_id']}"
na_pass = "PASS"

# 4. Clinical threshold wording
for line in md_content.splitlines():
    if "85%" in line:
        assert "internal program milestone" in line.lower() or "incubation program" in line.lower(), f"85% line not qualified: {line}"
thresh_pass = "PASS"

# 5. Confidence wording
assert "assessment confidence reflects the quality" in md_lower
assert "assessment confidence reflects the quality" in js_lower
conf_pass = "PASS"

# 6. Markdown/JSON consistency
md_crit = set(re.findall(r'\|\s*\*\*([A-Z]{2}-\d{2})\*\*\s*\|', md_content))
js_crit = {c["criterion_id"] for c in js_obj["canonical_criteria_matrix"]}
assert len(md_crit) == 87
assert len(js_crit) == 87
assert md_crit == js_crit

md_risks = set(re.findall(r'\|\s*\*\*(RISK-[A-Z0-9\-]+)\*\*\s*\|', md_content))
js_risks = {r["risk_id"] for r in js_obj["master_risk_register"]}
assert len(md_risks) == 12
assert len(js_risks) == 12
assert md_risks == js_risks

md_qs = set(re.findall(r'\|\s*\*\*(Q-\d{2})\*\*\s*\|', md_content))
js_qs = {q["question_id"] for q in js_obj["actionable_diligence_inquiries"]}
assert len(md_qs) == 18
assert len(js_qs) == 18
assert md_qs == js_qs
consistency_pass = "PASS"

# 7. Contamination check
forbidden_contam = ["cleanpower", "battery", "electrochemical", "mineral pricing", "cell scale-up"]
for fc in forbidden_contam:
    assert fc not in md_lower, f"Found {fc} in MD"
    assert fc not in js_lower, f"Found {fc} in JSON"
contam_pass = "PASS"

# 8. Database unchanged
h = hashlib.sha256(open(db_path, "rb").read()).hexdigest().upper()
expected_h = "D9659F4E8C1058C5D5F4511E1BB22D3ABE6CB12101C16CE397416051A38176C7"
assert h == expected_h, f"DB changed! {h}"
db_pass = "PASS"

print("All automated checks PASSED!")

# Build compact line-by-line JSON for display
lines = ['{']
lines.append('  "handoff_metadata": ' + json.dumps(js_obj["handoff_metadata"], ensure_ascii=False) + ',')
lines.append('  "governance_and_scoring_summary": ' + json.dumps(js_obj["governance_and_scoring_summary"], ensure_ascii=False) + ',')
lines.append('  "canonical_criteria_matrix": [')
for i, c in enumerate(js_obj["canonical_criteria_matrix"]):
    sep = ',' if i < len(js_obj["canonical_criteria_matrix"]) - 1 else ''
    lines.append('    ' + json.dumps(c, ensure_ascii=False) + sep)
lines.append('  ],')
lines.append('  "master_risk_register": [')
for i, r in enumerate(js_obj["master_risk_register"]):
    sep = ',' if i < len(js_obj["master_risk_register"]) - 1 else ''
    lines.append('    ' + json.dumps(r, ensure_ascii=False) + sep)
lines.append('  ],')
lines.append('  "actionable_diligence_inquiries": [')
for i, q in enumerate(js_obj["actionable_diligence_inquiries"]):
    sep = ',' if i < len(js_obj["actionable_diligence_inquiries"]) - 1 else ''
    lines.append('    ' + json.dumps(q, ensure_ascii=False) + sep)
lines.append('  ],')
lines.append('  "cost_and_usage_telemetry": ' + json.dumps(js_obj["cost_and_usage_telemetry"], ensure_ascii=False) + ',')
lines.append('  "consistency_and_validation_dossier": ' + json.dumps(js_obj["consistency_and_validation_dossier"], ensure_ascii=False))
lines.append('}')
formatted_json = '\n'.join(lines)

compact_path = handoff_dir / "STETHAIM_FINAL_REVIEW_PACKAGE_v2.1_compact.json"
compact_path.write_text(formatted_json, encoding="utf-8")
print(f"Compact JSON saved: {compact_path} ({len(formatted_json)} chars, {len(lines)} lines)")
