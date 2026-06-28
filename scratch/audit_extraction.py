"""
Extraction Pipeline Audit Script
=================================
1. Parse PETREVOLT PDF with real_pipeline.extract_facts_from_text
2. Print COMPLETE StartupProfileExtraction JSON (as the MockProvider would build it) 
   BEFORE any mapping occurs
3. Print the mapped StartupProfile JSON
4. Compare every field and produce a PASS/FAIL audit table

Run from project root:
    python scratch/audit_extraction.py
"""
import sys
import os
import json
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# ── 1. Parse the PDF into raw text ──────────────────────────────────────────
PDF_PATH = (
    r"uploads/07487879-4890-4239-830d-c1c8cd8f6171/"
    r"4679f012-ad0e-430b-94d7-793f1b524ece_PETREVOLT ENERGY SOLUTIONS- Pitch Deck.pdf"
)

combined_text = ""

# Try PyMuPDF (fitz) first
try:
    import fitz  # pymupdf
    doc = fitz.open(PDF_PATH)
    pages_text = [doc[i].get_text() for i in range(len(doc))]
    combined_text = "\n\n".join(p.strip() for p in pages_text if p.strip())
    print(f"[OK] PDF parsed via PyMuPDF: {len(combined_text)} chars")
except Exception:
    pass

# Try pypdf
if not combined_text:
    try:
        from pypdf import PdfReader
        reader = PdfReader(PDF_PATH)
        pages_text = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages_text.append(t.strip())
        combined_text = "\n\n".join(pages_text)
        print(f"[OK] PDF parsed via pypdf: {len(combined_text)} chars")
    except Exception:
        pass

# Fallback: use meta.json parsed_text stored by the app
if not combined_text:
    META_PATH = PDF_PATH + ".meta.json"
    try:
        with open(META_PATH, "r", encoding="utf-8") as fh:
            meta = json.load(fh)
        combined_text = meta.get("parsed_text", "") or ""
        print(f"[OK] Using meta.json parsed_text: {len(combined_text)} chars")
    except Exception as e2:
        print(f"[FAIL] All PDF parsing methods failed: {e2}")
        sys.exit(1)

if not combined_text:
    print("[FAIL] combined_text is empty after all fallbacks")
    sys.exit(1)

# ── 2. Run the MOCK provider's StartupProfileExtraction logic ────────────────
from app.services.ai.real_pipeline import extract_facts_from_text

print("\n" + "="*70)
print("STEP 1  extract_facts_from_text -> DocumentExtraction")
print("="*70)

doc_ext = extract_facts_from_text(f"Extract from text:\n{combined_text}")

# Simulate what MockProvider does to build StartupProfileExtraction
founders_raw = doc_ext.founder.founder_names.value or ""
founders_list = [n.strip() for n in founders_raw.split(",") if n.strip()]

startup_profile_extraction = {
    "company_name": doc_ext.founder.founder_names.value or "Startup",
    "founders": founders_list,
    "problem_statement": doc_ext.product.problem_solved.value or "Not specified",
    "solution": doc_ext.product.description.value or "Not specified",
    "market": doc_ext.market.target_market.value or "Not specified",
    "business_model": doc_ext.product.business_model.value or "Not specified",
    "competition": doc_ext.market.competitors.value or "Not specified",
    "traction": doc_ext.product.customers.value or "Not specified",
    "team": doc_ext.founder.leadership_experience.value or "Not specified",
    "technology": doc_ext.technology.description.value or "Not specified",
    "financial_information": doc_ext.financial.financial_metrics.value or "Not specified",
}

print("\n📋 COMPLETE StartupProfileExtraction JSON (BEFORE MAPPING):")
print(json.dumps(startup_profile_extraction, indent=2))

# ── 3. Show what gets mapped into pipeline fields ────────────────────────────
print("\n" + "="*70)
print("STEP 2  Mapping into pipeline fields (doc_ext → DocumentExtraction)")
print("="*70)

startup_profile_mapped = {
    "founder.founder_names.value":              doc_ext.founder.founder_names.value,
    "founder.leadership_experience.value":      doc_ext.founder.leadership_experience.value,
    "founder.domain_expertise.value":           doc_ext.founder.domain_expertise.value,
    "founder.commitment_level.value":           doc_ext.founder.commitment_level.value,
    "product.description.value":               doc_ext.product.description.value,
    "product.problem_solved.value":            doc_ext.product.problem_solved.value,
    "product.solution_value_prop.value":       doc_ext.product.solution_value_prop.value,
    "product.customers.value":                 doc_ext.product.customers.value,
    "product.business_model.value":            doc_ext.product.business_model.value,
    "market.target_market.value":              doc_ext.market.target_market.value,
    "market.market_size.value":                doc_ext.market.market_size.value,
    "market.competitors.value":                doc_ext.market.competitors.value,
    "market.competition_analysis.value":       doc_ext.market.competition_analysis.value,
    "financial.revenue_model.value":           doc_ext.financial.revenue_model.value,
    "financial.funding_received.value":        doc_ext.financial.funding_received.value,
    "financial.current_revenue.value":         doc_ext.financial.current_revenue.value,
    "financial.financial_metrics.value":       doc_ext.financial.financial_metrics.value,
    "technology.description.value":            doc_ext.technology.description.value,
    "technology.trl_level.value":              doc_ext.technology.trl_level.value,
    "technology.ip_status.value":              doc_ext.technology.ip_status.value,
}

print("\n📋 COMPLETE Mapped StartupProfile JSON (DocumentExtraction fields):")
print(json.dumps(startup_profile_mapped, indent=2, default=str))

# ── 4. Field-by-field audit ──────────────────────────────────────────────────

def is_atomic(value, field_name):
    """Return (status, root_cause)."""
    if value is None:
        return "FAIL", "Value is None — field was never populated"

    val_str = str(value).strip()

    if not val_str or val_str.lower() in ("not specified", "n/a", "none", "null", "unknown"):
        return "FAIL", "Value is empty/placeholder — extraction produced no meaningful content"

    # Check for multi-paragraph / OCR dump
    word_count = len(val_str.split())
    newline_count = val_str.count("\n")

    if word_count > 80:
        return "FAIL", f"Value is too long ({word_count} words) — likely an OCR dump or paragraph block"

    if newline_count > 3:
        return "FAIL", f"Value contains {newline_count} newlines — likely concatenated slide text"

    # Check for obvious OCR artifacts
    if re.search(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', val_str):
        return "FAIL", "Value contains email address -- OCR dump"

    if re.search(r'\+\d[\d\s\-()]{7,}', val_str):
        return "FAIL", "Value contains phone number -- OCR dump"

    if re.search(r'(page\s+\d+|slide\s+\d+)', val_str, re.I):
        return "FAIL", "Value contains slide/page reference — OCR dump"

    # Heuristic: if three or more unrelated sentences joined together
    sentence_count = len(re.findall(r'[.!?]+', val_str))
    if sentence_count >= 4 and word_count > 50:
        return "FAIL", f"Value is {sentence_count} sentences / {word_count} words — likely concatenated observations"

    return "PASS", "Value appears atomic"


AUDIT_FIELDS = [
    ("company_name",        startup_profile_extraction["company_name"],             "StartupProfileExtraction.company_name"),
    ("founders",            str(startup_profile_extraction["founders"]),            "StartupProfileExtraction.founders (list)"),
    ("founder_roles",       None,                                                   "NOT in schema — field missing"),
    ("problem_statement",   startup_profile_extraction["problem_statement"],        "StartupProfileExtraction.problem_statement"),
    ("solution",            startup_profile_extraction["solution"],                 "StartupProfileExtraction.solution"),
    ("technology",          startup_profile_extraction["technology"],               "StartupProfileExtraction.technology"),
    ("patents",             None,                                                   "NOT in schema — field missing"),
    ("business_model",      startup_profile_extraction["business_model"],           "StartupProfileExtraction.business_model"),
    ("revenue_model",       doc_ext.financial.revenue_model.value,                 "DocumentExtraction.financial.revenue_model"),
    ("target_customers",    doc_ext.product.customers.value,                       "DocumentExtraction.product.customers"),
    ("competition",         startup_profile_extraction["competition"],              "StartupProfileExtraction.competition"),
    ("traction",            startup_profile_extraction["traction"],                "StartupProfileExtraction.traction"),
    ("funding_ask",         None,                                                   "NOT in schema — field missing"),
    ("funding_raised",      str(doc_ext.financial.funding_received.value),         "DocumentExtraction.financial.funding_received"),
    ("current_revenue",     str(doc_ext.financial.current_revenue.value),          "DocumentExtraction.financial.current_revenue"),
    ("burn_rate",           None,                                                   "NOT in schema — field missing"),
    ("runway",              None,                                                   "NOT in schema — field missing"),
    ("market_size",         doc_ext.market.market_size.value,                      "DocumentExtraction.market.market_size"),
]

print("\n" + "="*70)
print("STEP 3  FIELD-BY-FIELD AUDIT")
print("="*70)

# Print header
header = f"{'Field':<22} {'Status':<7} {'Source':<45} {'Root Cause / Value (first 120 chars)'}"
print("\n" + header)
print("-" * 160)

audit_results = []
for field_name, value, source in AUDIT_FIELDS:
    if value is None:
        status = "FAIL"
        root_cause = "Field does not exist in current schema"
        display_val = "—"
    else:
        status, root_cause = is_atomic(value, field_name)
        display_val = str(value)[:120].replace("\n", "↵")

    audit_results.append((field_name, status, source, root_cause, display_val))
    status_icon = "[PASS]" if status == "PASS" else "[FAIL]"
    print(f"{status_icon} {field_name:<20} {status:<7} {source:<45} {root_cause}")

# Full value dump for FAIL fields
print("\n" + "="*70)
print("FAILED FIELD VALUES — FULL CONTENT")
print("="*70)
for field_name, status, source, root_cause, display_val in audit_results:
    if status == "FAIL":  # noqa
        # Get full value
        full_val = None
        for fn, v, _ in AUDIT_FIELDS:
            if fn == field_name:
                full_val = v
                break
        print(f"\n[FAIL] {field_name}  ({source})")
        print(f"   Root Cause: {root_cause}")
        print(f"   Full Value:\n   {str(full_val)[:800]}")
        print()

# Summary
total = len(audit_results)
passes = sum(1 for _, s, *_ in audit_results if s == "PASS")
fails  = sum(1 for _, s, *_ in audit_results if s == "FAIL")

print("="*70)
print(f"AUDIT SUMMARY: {passes}/{total} PASS  |  {fails}/{total} FAIL")
print("="*70)

# Save results to JSON for reference
output = {
    "startup_profile_extraction_json": startup_profile_extraction,
    "document_extraction_mapped": startup_profile_mapped,
    "audit": [
        {
            "field": fn,
            "status": st,
            "source": src,
            "root_cause": rc,
            "value_preview": dv,
        }
        for fn, st, src, rc, dv in audit_results
    ],
    "summary": {"pass": passes, "fail": fails, "total": total},
}

output_path = os.path.join("scratch", "audit_results.json")
with open(output_path, "w", encoding="utf-8") as fh:
    json.dump(output, fh, indent=2, default=str)
print(f"\n📄 Full results saved to: {output_path}")
