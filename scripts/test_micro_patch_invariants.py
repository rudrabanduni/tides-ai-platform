import json
import re
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
handoff_dir = REPO_ROOT / "reports" / "hand_off"
md_path = handoff_dir / "STETHAIM_FINAL_REVIEW_PACKAGE_v2.1.md"
json_path = handoff_dir / "STETHAIM_FINAL_REVIEW_PACKAGE_v2.1.json"
db_path = REPO_ROOT / "tides_ai.db"

md_text = md_path.read_text(encoding="utf-8")
js_obj = json.loads(json_path.read_text(encoding="utf-8"))
js_text = json.dumps(js_obj, ensure_ascii=False)

# 1. FT-08 Mapping
ft_08_obj = [c for c in js_obj["canonical_criteria_matrix"] if c["criterion_id"] == "FT-08"][0]
assert "patent" not in ft_08_obj["assessment_narrative"].lower()
assert "skill gaps" in ft_08_obj["assessment_narrative"].lower()
ft_08_md = [l for l in md_text.splitlines() if "**FT-08**" in l][0]
assert "patent" not in ft_08_md.lower()
assert "skill gaps" in ft_08_md.lower()
print("1. FT-08 criterion mapping: PASS")

# 2. Commercial zero-claim audit
bad_commercial = ["pre-revenue (₹0)", "currently ₹0 revenue", "0 commercial users", "zero commercial users"]
for bc in bad_commercial:
    assert bc not in md_text.lower(), f"Found '{bc}' in MD"
    assert bc not in js_text.lower(), f"Found '{bc}' in JSON"
assert "no commercial revenue was evidenced" in md_text.lower()
assert "no commercial users or paying customers were evidenced" in md_text.lower()
print("2. Commercial zero-claim audit: PASS")

# 3. Bootstrapping language audit
assert "the venture is entirely bootstrapped" not in md_text.lower()
assert "entirely bootstrapped" not in js_text.lower()
assert "the submitted materials do not evidence an external funding amount; financial planning and operating-cost disclosures remain incomplete" in md_text.lower()
print("3. Bootstrapping language audit: PASS")

# 4. Founder-history absolute claim audit
assert "zero prior corporate exits" not in md_text.lower()
assert "zero prior corporate exits" not in js_text.lower()
assert "no prior corporate exits were disclosed or evidenced" in md_text.lower()
print("4. Founder-history absolute claim audit: PASS")

# 5. II-07 provenance consistency
ii_07_obj = [c for c in js_obj["canonical_criteria_matrix"] if c["criterion_id"] == "II-07"][0]
assert ii_07_obj["evidence_status"] == "SELF_REPORTED_ONLY"
assert ii_07_obj["source_provenance"] == "APPLICANT_REPORTED"
ii_07_md = [l for l in md_text.splitlines() if "**II-07**" in l][0]
assert "`SELF_REPORTED_ONLY`" in ii_07_md
assert "`APPLICANT_REPORTED`" in ii_07_md
print("5. II-07 provenance consistency: PASS")

# 6. KIMS MOU wording
assert "this does not establish ethics committee approval or completed clinical validation" in md_text.lower()
print("6. KIMS MOU wording: PASS")

# 7. Unsupported absolute-claim audit
bad_absolutes = [
    "clean institutional debt sheet",
    "clean cap table documentation",
    "patent ownership remains with individual founders",
    "zero external funding raised"
]
for ba in bad_absolutes:
    assert ba not in md_text.lower(), f"Found '{ba}' in MD"
    assert ba not in js_text.lower(), f"Found '{ba}' in JSON"
print("7. Unsupported absolute-claim audit: PASS")

# 8. Canonical 87-criterion integrity
assert len(js_obj["canonical_criteria_matrix"]) == 87
assert len([c for c in js_obj["canonical_criteria_matrix"] if c["final_status"] == "ASSESSED"]) == 81
assert len([c for c in js_obj["canonical_criteria_matrix"] if c["final_status"] == "NOT_APPLICABLE"]) == 6
assert len([c for c in js_obj["canonical_criteria_matrix"] if c["final_status"] == "NOT_ASSESSED"]) == 0
assert len(js_obj["master_risk_register"]) == 12
assert len(js_obj["actionable_diligence_inquiries"]) == 18
print("8. Canonical 87-criterion integrity: PASS")

# 9. Database unchanged
db_hash = hashlib.sha256(open(db_path, "rb").read()).hexdigest().upper()
expected_db_hash = "D9659F4E8C1058C5D5F4511E1BB22D3ABE6CB12101C16CE397416051A38176C7"
assert db_hash == expected_db_hash, f"DB changed! {db_hash}"
print("9. Database unchanged: PASS")

print("\nALL INVARIANTS PASSED!")
