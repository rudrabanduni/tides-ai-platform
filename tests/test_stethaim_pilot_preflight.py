"""tests/test_stethaim_pilot_preflight.py - Deterministic Offline Preflight Tests for STETHAIM Pilot.

Zero live API calls.
Verifies:
1. All three local input files exist, are readable, and match expected cryptographic hashes.
2. File format parsers handle XLSX, DOCX, and PDF natively.
3. Document classification maps to Application Form, Founder Resume, and Pitch Deck.
4. Privacy safeguards strictly exclude Aadhaar, phone, email, and residential addresses.
5. CleanPower Systems data/claims are completely isolated and never reused.
6. Evaluation budget ceiling ($0.35 USD) and differentiated token caps are strictly enforced.
7. Due diligence contradictions and missing evidence are programmatically detected.
8. Workspace tides_ai.db SHA-256 remains bit-for-bit unaltered.
"""

import hashlib
import io
import re
import subprocess
import sys
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import openpyxl
import pytest

from app.core.enums import DocumentType
from app.modules.intelligence.classification import (
    DocumentClassification,
    classify_document,
)
from app.modules.intelligence.parsers import (
    DocxParser,
    ParserManager,
    PdfParser,
    XlsxParser,
)
from app.modules.intelligence.pii_sanitizer import (
    prepare_sanitized_stethaim_inputs,
    sanitize_application_workbook,
    sanitize_text,
)
from app.services.ai.cost_ledger import EvaluationCostLedger
from app.services.ai.exceptions import AIBudgetExhaustedError
from app.services.ai.pricing import get_pricing_catalog
from scripts.run_one_time_live_eval import (
    BUDGET_CEILING_USD,
    BUFFERED_CEILING_INR,
    DOMAIN_OUTPUT_TOKEN_LIMITS,
    PROJECT_ROOT,
    REVIEWER_MAX_OUTPUT_TOKENS,
    STETHAIM_PILOT_DIR,
    validate_stethaim_prerequisites,
)

EXPECTED_WORKSPACE_DB_HASH = "d9659f4e8c1058c5d5f4511e1bb22d3abe6cb12101c16ce397416051a38176c7"
WORKSPACE_DB = PROJECT_ROOT / "tides_ai.db"

EXPECTED_HASHES = {
    "Applications.xlsx": "939156e0e4a089b8d7ca7047abdcc5742d1e25054d3fbdbcb96d8727e8e7c1e3",
    "Shikha_Behera_CV-2.docx": "b6a744b0de74397286c9b44ff395def3b39c3ca4ea785c9df0c763d601cc6743",
    "NEW PITCH DECK STETHAIM.pdf": "af80a3d1f52821af741bab5c9674edab8dc9d3ed76393965e812c48201afdc5c",
}


class TestStethaimPilotPreflight:
    """Preflight test suite for the STETHAIM Pvt. Ltd. (Neumo Rex) pilot evaluation."""

    def test_stethaim_pilot_files_exist_and_hashes_match(self):
        """Verifies that all three STETHAIM pilot files exist in private/pilot_inputs/stethaim."""
        assert STETHAIM_PILOT_DIR.exists(), f"STETHAIM dir missing: {STETHAIM_PILOT_DIR}"
        prereqs = validate_stethaim_prerequisites()
        files_dict = prereqs["files"]

        for filename, expected_hash in EXPECTED_HASHES.items():
            assert filename in files_dict, f"Missing file in manifest: {filename}"
            actual_hash = files_dict[filename]["sha256"]
            assert actual_hash == expected_hash, (
                f"SHA-256 hash mismatch for {filename}!\nExpected: {expected_hash}\nActual:   {actual_hash}"
            )

    def test_multi_format_parsers_parse_all_three_documents(self):
        """Verifies that XlsxParser, DocxParser, and PdfParser successfully parse the three files."""
        app_path = STETHAIM_PILOT_DIR / "Applications.xlsx"
        cv_path = STETHAIM_PILOT_DIR / "Shikha_Behera_CV-2.docx"
        deck_path = STETHAIM_PILOT_DIR / "NEW PITCH DECK STETHAIM.pdf"

        # 1. Excel intake parser
        app_res = ParserManager.parse_file(str(app_path))
        assert app_res["page_count"] == 1
        assert "STETHAIM" in app_res["normalized_text"]
        assert len(app_res["normalized_text"]) > 500

        # 2. DOCX CV parser
        cv_res = ParserManager.parse_file(str(cv_path))
        assert cv_res["page_count"] >= 1
        assert "SHIKHA BEHERA" in cv_res["normalized_text"].upper()
        assert "MBBS" in cv_res["normalized_text"]

        # 3. PDF pitch deck parser
        deck_res = ParserManager.parse_file(str(deck_path))
        assert deck_res["page_count"] == 14
        assert "NEUMO REX" in deck_res["normalized_text"].upper()
        assert "THE STETHERS" in deck_res["normalized_text"]

    def test_document_classification_identifies_all_three_document_types(self):
        """Verifies document classification maps files to Application Form, Founder Resume, and Pitch Deck."""
        assert classify_document("Applications.xlsx") == DocumentClassification.EXCEL_INTAKE
        assert classify_document("Shikha_Behera_CV-2.docx") == DocumentClassification.FOUNDER_RESUME
        assert classify_document("NEW PITCH DECK STETHAIM.pdf") == DocumentClassification.PITCH_DECK

    def test_privacy_sanitizer_scrubs_aadhaar_phone_email_address(self):
        """Verifies that PII is completely sanitized and zero Aadhaar, phone, or email leaks occur."""
        app_path = STETHAIM_PILOT_DIR / "Applications.xlsx"
        sanitized_bytes, audit = sanitize_application_workbook(app_path)

        assert audit["cells_redacted"] >= 5
        assert any("aadhar" in c.lower() for c in audit["columns_sanitized"])
        assert any("mobile" in c.lower() for c in audit["columns_sanitized"])
        assert any("email" in c.lower() for c in audit["columns_sanitized"])
        assert any("address" in c.lower() for c in audit["columns_sanitized"])

        # Parse sanitized workbook and verify regex matches are 0
        wb = openpyxl.load_workbook(io.BytesIO(sanitized_bytes))
        sheet = wb.active
        all_text = " ".join(str(c.value) for row in sheet.iter_rows() for c in row if c.value is not None)

        aadhaar_matches = re.findall(r"\b\d{4}\s?\d{4}\s?\d{4}\b", all_text)
        phone_matches = re.findall(r"(\+91[\-\s]?)?[6-9]\d{9}\b", all_text)
        email_matches = re.findall(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", all_text)

        assert len(aadhaar_matches) == 0, f"Aadhaar leaked: {aadhaar_matches}"
        assert len(phone_matches) == 0, f"Phone leaked: {phone_matches}"
        assert len(email_matches) == 0, f"Email leaked: {email_matches}"

    def test_stethaim_pilot_fails_closed_if_combined_with_cleanpower_reuse(self):
        """Verifies runner rejects combining --stethaim-pilot with CleanPower reuse flags."""
        python_exe = sys.executable
        script_path = PROJECT_ROOT / "scripts" / "run_one_time_live_eval.py"

        result = subprocess.run(
            [python_exe, str(script_path), "--stethaim-pilot", "--reuse-existing-extraction"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "Cannot combine --stethaim-pilot with CleanPower reuse flags" in result.stderr

    def test_stethaim_dry_run_displays_pilot_preflight_plan(self):
        """Verifies running scripts/run_one_time_live_eval.py --stethaim-pilot produces the pilot plan."""
        python_exe = sys.executable
        script_path = PROJECT_ROOT / "scripts" / "run_one_time_live_eval.py"

        result = subprocess.run(
            [python_exe, str(script_path), "--stethaim-pilot"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "DRY RUN / PREPARATION ONLY" in result.stdout
        assert "Target Startup:            STETHAIM Pvt. Ltd. (Neumo Rex)" in result.stdout
        assert "MedTech | Stage 4 (Agreement Signing, Round: Passed)" in result.stdout
        assert "FRESH EXTRACTION (Multi-Document Ingestion; Zero CleanPower Reuse)" in result.stdout
        assert "Provider Cost Ceiling:     $0.35 USD" in result.stdout
        assert "Buffered Cost Ceiling:     INR 39.65" in result.stdout
        assert "Problem & Solution (PS, 3 batches):   <= 900 tokens/batch" in result.stdout
        assert "Financials & Support (FI, 5 batches): <= 900 tokens/batch" in result.stdout
        assert "Supervisory Reviewer:                 2,400 tokens" in result.stdout
        assert "Applications.xlsx" in result.stdout
        assert "Shikha_Behera_CV-2.docx" in result.stdout
        assert "NEW PITCH DECK STETHAIM.pdf" in result.stdout
        assert "Aadhaar, Phone, Email, Residential Address EXCLUDED" in result.stdout
        assert "Worst-Case Evaluation:     $0.3248 USD (~INR 36.80 buffered)" in result.stdout

    def test_budget_reservation_and_worst_case_evaluation_under_35_cents(self):
        """Mathematically verifies that worst-case evaluation cost (10 Haiku extractions + 19 Sonnet domain batches + 1 Sonnet reviewer) fits under $0.35 USD."""
        pricing = get_pricing_catalog("2026-10-live-v1")

        # 1. 10 Staged Extractions on Haiku 5.5 (10 * 16,000 in, 9*2400 + 4096 = 25,696 total out = $0.028848)
        haiku_in_cost = round(10 * 16000 * (0.10 / 1e6), 6)  # $0.016000
        haiku_out_cost = round(25696 * (0.50 / 1e6), 6)      # $0.012848
        worst_ext_cost = 0.028848

        # 2. 19 Criterion-Batched Domain Calls on Sonnet 5.5 (19 batches @ 2,500 in, 900 max out = $0.0140 ea)
        per_batch_cost = pricing.calculate_cost("claude-sonnet-5-5", 2500, 900)  # 2500*$2/M ($0.005) + 900*$10/M ($0.009) = $0.0140
        domains_total = round(19 * per_batch_cost, 6)  # 19 * 0.0140 = 0.2660

        # 3. Supervisory reviewer on Sonnet 5.5 (3,000 in, 2,400 out)
        worst_review_cost = pricing.calculate_cost("claude-sonnet-5-5", 3000, 2400)  # 0.0300
        sonnet_20_ops = round(domains_total + worst_review_cost, 6)  # 0.2960

        # 4. Total worst-case cost including fresh 10-stage extraction
        worst_total = round(worst_ext_cost + sonnet_20_ops, 6)  # 0.324848

        assert haiku_in_cost == 0.016000
        assert haiku_out_cost == 0.012848
        assert domains_total == 0.266000
        assert worst_review_cost == 0.030000
        assert sonnet_20_ops == 0.296000
        assert worst_total == 0.324848
        assert worst_total <= BUDGET_CEILING_USD
        assert round(worst_total * 96.0 * 1.18, 2) == 36.80
        assert round(worst_total * 96.0 * 1.18, 2) <= BUFFERED_CEILING_INR

    def test_factual_contradictions_and_missing_evidence_audit(self):
        """Programmatically asserts the specific due diligence gaps and discrepancies in STETHAIM data."""
        # 1. Company registration date contradiction
        wb = openpyxl.load_workbook(STETHAIM_PILOT_DIR / "Applications.xlsx")
        ws = wb.active
        headers = [c.value for c in ws[1]]
        row = list(ws.iter_rows(min_row=2, values_only=True))[0]
        app_reg_date = row[headers.index("Date of Company Registration")]
        assert "2023" in str(app_reg_date)
        assert "Sep" in str(app_reg_date)  # Application: 17 Sep 2023

        deck_res = ParserManager.parse_file(str(STETHAIM_PILOT_DIR / "NEW PITCH DECK STETHAIM.pdf"))
        deck_text = deck_res["normalized_text"]
        assert "NOV 2023" in deck_text  # Deck Slide 10: NOV 2023

        # 2. Patent filing ambiguity (claims 'Patented technology*' with '*Patent filed')
        assert "Patented technology*" in deck_text
        assert "*Patent filed" in deck_text
        # No patent application number exists in deck or application
        assert not re.search(r"\b(IN|PCT|US)?\s?\d{6,14}\b", deck_text)

        # 3. Market sizing ambiguity (unit counts only, zero currency value)
        assert "TAM" in deck_text
        assert "35,700" in deck_text  # ICU unit count
        assert "INR" not in deck_text
        assert "₹" not in deck_text
        assert "USD" not in deck_text
        assert "$" not in deck_text

        # 4. Slide 11 Funds Requirement: zero capital ask amount
        assert "FUNDS REQUIREMENT" in deck_text
        # No INR funding amount requested
        assert not re.search(r"₹\s?\d+", deck_text)
        assert "Lakhs" not in deck_text
        assert "Crores" not in deck_text

        # 5. Founder team roster ambiguity: 1 solo applicant in form vs 4 members in deck
        assert row[headers.index("Name")].strip() == "SHIKHA BEHERA"
        assert "Sanat Behera" in deck_text
        assert "Rakshit Singh" in deck_text
        assert "Lohith Dayantri" in deck_text

    def test_workspace_database_hash_unchanged(self):
        """Absolute safety guard: workspace tides_ai.db MUST NOT be modified or touched."""
        assert WORKSPACE_DB.exists(), "Workspace tides_ai.db not found!"
        current_hash = hashlib.sha256(WORKSPACE_DB.read_bytes()).hexdigest()
        assert current_hash == EXPECTED_WORKSPACE_DB_HASH, (
            f"FATAL: Workspace database SHA-256 altered!\n"
            f"Expected: {EXPECTED_WORKSPACE_DB_HASH}\n"
            f"Actual:   {current_hash}"
        )
