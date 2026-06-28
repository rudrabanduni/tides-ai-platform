"""
Validate that the new LLM-backed extraction produces atomic fields.

Run from project root:
    set PYTHONIOENCODING=utf-8
    .venv\Scripts\python.exe scratch/validate_extraction.py
"""
import sys
import os
import json

# Force UTF-8 output
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

PDF_PATH = (
    "uploads/07487879-4890-4239-830d-c1c8cd8f6171/"
    "4679f012-ad0e-430b-94d7-793f1b524ece_PETREVOLT ENERGY SOLUTIONS- Pitch Deck.pdf"
)

# ── Parse PDF ─────────────────────────────────────────────────────────────────
combined_text = ""

try:
    from pypdf import PdfReader
    reader = PdfReader(PDF_PATH)
    pages = []
    for page in reader.pages:
        t = page.extract_text()
        if t:
            pages.append(t.strip())
    combined_text = "\n\n".join(pages)
    print(f"[OK] PDF parsed via pypdf: {len(combined_text)} chars, {len(pages)} pages")
except Exception as e:
    print(f"[FAIL] pypdf failed: {e}")
    sys.exit(1)

if not combined_text.strip():
    print("[FAIL] No text extracted from PDF")
    sys.exit(1)

# ── Call the real LLM gateway ─────────────────────────────────────────────────
from app.services.ai.gateway import create_ai_gateway
from app.services.ai.schemas import AICompletionRequest
from app.modules.ai.orchestrator.startup_profile_extraction import StartupProfileExtraction

print("\n[INFO] Creating AI gateway...")
llm = create_ai_gateway()
print(f"[INFO] Gateway type: {type(llm).__name__}")

req = AICompletionRequest(
    system_prompt=(
        "You are an expert venture capital analyst performing due diligence on a startup pitch deck. "
        "Your task is to extract specific, atomic facts from the document provided. "
        "Rules:\n"
        "1. Every field must be a single atomic value: one name, one sentence, one number, or one short phrase.\n"
        "2. Never include raw paragraphs, OCR text dumps, slide headers, bullet lists, roadmap text, "
        "email addresses, phone numbers, or multiple unrelated concepts in a single field.\n"
        "3. If a piece of information is not present in the document, return null for that field.\n"
        "4. Do not guess or hallucinate. Only extract what is explicitly stated."
    ),
    user_prompt=(
        f"Pitch deck text from 'PETREVOLT ENERGY SOLUTIONS' (CleanTech, seed stage):\n\n"
        f"{combined_text}\n\n"
        "Extract the startup profile fields as specified. Return only what is explicitly stated."
    ),
)

print("[INFO] Calling LLM with StartupProfileExtraction schema...")
result = llm.complete_json(req, StartupProfileExtraction)
extracted: StartupProfileExtraction = result.data

print("\n" + "="*70)
print("StartupProfileExtraction JSON (BEFORE MAPPING) — from LLM:")
print("="*70)
print(extracted.model_dump_json(indent=2))
print("="*70)

# ── Field-by-field quality check ──────────────────────────────────────────────
import re

def check_atomic(field_name: str, value) -> tuple[str, str]:
    if value is None:
        return "NULL", "null — not present in deck (acceptable)"

    if isinstance(value, list):
        # Lists are OK if every item is short
        for item in value:
            if len(str(item).split()) > 15:
                return "FAIL", f"List item too long: {str(item)[:100]}"
        return "PASS", f"List with {len(value)} item(s)"

    val = str(value).strip()
    if not val:
        return "FAIL", "Empty string"

    word_count = len(val.split())
    newline_count = val.count("\n")

    if word_count > 60:
        return "FAIL", f"{word_count} words — too long (OCR dump)"
    if newline_count > 2:
        return "FAIL", f"{newline_count} newlines — multi-paragraph dump"
    if re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", val):
        return "FAIL", "Contains email address — OCR dump"
    if re.search(r"\+\d[\d\s\-()]{7,}", val):
        return "FAIL", "Contains phone number — OCR dump"

    return "PASS", f"{word_count} words"


print("\nField-by-Field Atomicity Check:")
print("-" * 100)

fields = [
    "company_name", "founders", "founder_roles", "problem_statement", "solution",
    "technology", "patents", "market", "market_size", "business_model",
    "revenue_model", "competition", "traction", "team", "financial_information",
    "funding_ask", "funding_raised", "current_revenue", "burn_rate", "runway",
]

passes = 0
fails = 0
nulls = 0

for field in fields:
    value = getattr(extracted, field, None)
    status, reason = check_atomic(field, value)
    if status == "PASS":
        passes += 1
        indicator = "[PASS]"
    elif status == "NULL":
        nulls += 1
        indicator = "[NULL]"
    else:
        fails += 1
        indicator = "[FAIL]"

    val_preview = str(value)[:80].replace("\n", " | ") if value is not None else "null"
    print(f"{indicator} {field:<25} {reason:<40} Value: {val_preview}")

print("-" * 100)
print(f"RESULT: {passes} PASS | {nulls} NULL (acceptable) | {fails} FAIL")
if fails == 0:
    print("[SUCCESS] All extracted fields are atomic. LLM extraction is working correctly.")
else:
    print("[ISSUES FOUND] Some fields still contain non-atomic content.")
print()
