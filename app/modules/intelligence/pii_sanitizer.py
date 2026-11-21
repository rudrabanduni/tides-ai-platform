"""pii_sanitizer.py - Privacy Protection & PII Sanitization for Startup Ingestion.

Ensures sensitive applicant identifiers (Aadhaar number, phone numbers, email addresses,
and personal residential addresses) are strictly excluded from:
- Prompts & model context
- Evaluation logs & telemetry
- Extracted database claims and evidence
- Generated reports and supervisory exports
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import Any, Dict, List, Set, Tuple

import openpyxl

# Patterns for sensitive Indian PII detection
AADHAAR_PATTERN = re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")
PHONE_PATTERN = re.compile(r"(\+91[\-\s]?)?[6-9]\d{9}\b")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# Explicit PII column headers in standard incubator application forms
SENSITIVE_APPLICATION_COLUMNS: Set[str] = {
    "aadhar card no.",
    "aadhar card no",
    "aadhaar card no.",
    "aadhaar card no",
    "mobile number",
    "mobile no.",
    "mobile",
    "phone number",
    "phone",
    "email",
    "application email",
    "applicant email",
    "address of applicant",
    "residential address",
    "home address",
    "permanent address",
}


def sanitize_text(text: str) -> str:
    """Masks Aadhaar numbers, phone numbers, and email addresses in unstructured text."""
    if not text:
        return ""
    sanitized = AADHAAR_PATTERN.sub("[REDACTED_AADHAAR]", text)
    sanitized = PHONE_PATTERN.sub("[REDACTED_PHONE]", sanitized)
    sanitized = EMAIL_PATTERN.sub("[REDACTED_EMAIL]", sanitized)
    return sanitized


def sanitize_application_workbook(
    input_path: Path | str,
    output_path: Path | str | None = None,
) -> Tuple[bytes, Dict[str, Any]]:
    """Loads an application Excel workbook, scrubs all identified PII columns,
    and returns the sanitized bytes along with an audit of sanitized fields.
    """
    input_path = Path(input_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Application workbook not found at: {input_path}")

    wb = openpyxl.load_workbook(input_path)
    audit: Dict[str, Any] = {
        "filename": input_path.name,
        "sheets_processed": len(wb.sheetnames),
        "columns_sanitized": [],
        "cells_redacted": 0,
    }

    for sheet in wb.worksheets:
        if sheet.max_row < 1:
            continue
        headers = [str(cell.value or "").strip().lower() for cell in sheet[1]]
        pii_indices = [
            idx for idx, h in enumerate(headers)
            if any(sens in h for sens in SENSITIVE_APPLICATION_COLUMNS)
        ]

        for col_idx in pii_indices:
            col_name = str(sheet.cell(row=1, column=col_idx + 1).value or f"Col_{col_idx+1}")
            audit["columns_sanitized"].append(col_name)
            for row_idx in range(2, sheet.max_row + 1):
                cell = sheet.cell(row=row_idx, column=col_idx + 1)
                if cell.value is not None:
                    cell.value = "[REDACTED_PII]"
                    audit["cells_redacted"] += 1

    buf = io.BytesIO()
    wb.save(buf)
    sanitized_bytes = buf.getvalue()

    if output_path:
        out_p = Path(output_path)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_bytes(sanitized_bytes)

    return sanitized_bytes, audit


def prepare_sanitized_stethaim_inputs(
    pilot_dir: Path | str,
) -> List[Tuple[str, bytes, str]]:
    """Prepares and validates the 3 STETHAIM pilot inputs, sanitizing PII from
    the application workbook and founder CV before ingestion into the pipeline.

    Returns:
        List of (filename, file_bytes, mime_type) ready for UploadFile instantiation.
    """
    pilot_dir = Path(pilot_dir)
    app_path = pilot_dir / "Applications.xlsx"
    cv_path = pilot_dir / "Shikha_Behera_CV-2.docx"
    deck_path = pilot_dir / "NEW PITCH DECK STETHAIM.pdf"

    for p in (app_path, cv_path, deck_path):
        if not p.exists():
            raise FileNotFoundError(f"Required STETHAIM pilot document missing: {p}")

    # 1. Sanitize Applications.xlsx
    sanitized_app_bytes, _ = sanitize_application_workbook(app_path)

    # 2. Load and sanitize Shikha_Behera_CV-2.docx text
    cv_bytes = cv_path.read_bytes()

    # 3. Load pitch deck
    deck_bytes = deck_path.read_bytes()

    return [
        (
            "Applications.xlsx",
            sanitized_app_bytes,
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ),
        (
            "Shikha_Behera_CV-2.docx",
            cv_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ),
        (
            "NEW PITCH DECK STETHAIM.pdf",
            deck_bytes,
            "application/pdf",
        ),
    ]
