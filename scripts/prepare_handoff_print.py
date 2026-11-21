import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
handoff_dir = REPO_ROOT / "reports" / "hand_off"

md_path = handoff_dir / "STETHAIM_FINAL_REVIEW_PACKAGE.md"
json_path = handoff_dir / "STETHAIM_FINAL_REVIEW_PACKAGE.json"

md_content = md_path.read_text(encoding="utf-8")
js_obj = json.loads(json_path.read_text(encoding="utf-8"))

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

print("Formatted compact JSON size:", len(formatted_json), "chars, lines:", len(lines))
# Verify valid json
reparsed = json.loads(formatted_json)
assert len(reparsed["canonical_criteria_matrix"]) == 87
assert len(reparsed["master_risk_register"]) == 12
assert len(reparsed["actionable_diligence_inquiries"]) == 18
print("Reparsed successfully!")
