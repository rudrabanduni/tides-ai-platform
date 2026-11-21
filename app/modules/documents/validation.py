"""validation.py - Upload safety checks for startup application documents.

Applied to every uploaded file before it is registered:
  * filename sanitisation (no path components, no NTFS alternate-data-stream ':' syntax,
    no reserved device names, bounded length, safe character set)
  * extension allow-list
  * content-signature check (the bytes must match the declared extension)
  * executable / script payload rejection
  * corrupt / encrypted PDF and malformed Office container detection
  * macro-enabled Office container rejection
"""

from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path

from app.core.exceptions import ValidationError

ALLOWED_DOCUMENT_EXTENSIONS = frozenset({
    ".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".csv", ".txt", ".md", ".log",
})

_OLE_SIGNATURE = b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1"
_ZIP_SIGNATURE = b"PK\x03\x04"
_DANGEROUS_SIGNATURES: tuple[tuple[bytes, str], ...] = (
    (b"MZ", "Windows executable"),
    (b"\x7fELF", "ELF executable"),
    (b"\xcf\xfa\xed\xfe", "Mach-O executable"),
    (b"\xfe\xed\xfa\xcf", "Mach-O executable"),
    (b"#!", "script"),
)
_WINDOWS_RESERVED = {"con", "prn", "aux", "nul", *(f"com{i}" for i in range(1, 10)), *(f"lpt{i}" for i in range(1, 10))}
_OOXML_PART = {".docx": "word/", ".pptx": "ppt/", ".xlsx": "xl/"}
_TEXT_EXTENSIONS = {".csv", ".txt", ".md", ".log"}
MAX_FILENAME_LENGTH = 120


def sanitize_filename(raw: str | None) -> str:
    """Returns a display-safe original filename or raises ValidationError."""
    name = (raw or "").replace("\\", "/").split("/")[-1].strip()
    # Neutralise NTFS alternate-data-stream syntax ("evil:stream.pdf" -> "evil_stream.pdf")
    name = name.replace(":", "_")
    name = re.sub(r"[\x00-\x1f\x7f]", "", name)
    name = re.sub(r"[^A-Za-z0-9._ ()\-]", "_", name)
    name = re.sub(r"\s+", " ", name).strip(" .")
    if not name or name in {".", ".."}:
        raise ValidationError("Uploaded file must include a valid filename")
    stem, ext = Path(name).stem, Path(name).suffix.lower()
    if stem.lower() in _WINDOWS_RESERVED:
        stem = f"file_{stem}"
    if len(stem) + len(ext) > MAX_FILENAME_LENGTH:
        stem = stem[: MAX_FILENAME_LENGTH - len(ext)]
    return f"{stem}{ext}"


def validate_document_bytes(filename: str, head: bytes, full_path: Path) -> None:
    """Validates file content against its declared extension. Raises ValidationError."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_DOCUMENT_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file type '{ext or 'none'}'. Allowed: PDF, DOCX, DOC, PPTX, PPT, XLSX, XLS, CSV, TXT, MD."
        )
    for sig, label in _DANGEROUS_SIGNATURES:
        if head.startswith(sig):
            raise ValidationError(f"Rejected '{filename}': file content is a {label}, not a document.")

    if ext == ".pdf":
        if not head.lstrip()[:5].startswith(b"%PDF-"):
            raise ValidationError(f"Rejected '{filename}': content is not a valid PDF (missing %PDF header).")
        _validate_pdf(filename, full_path)
    elif ext in _OOXML_PART:
        if not head.startswith(_ZIP_SIGNATURE):
            raise ValidationError(f"Rejected '{filename}': content is not a valid {ext[1:].upper()} file.")
        _validate_ooxml(filename, full_path, _OOXML_PART[ext])
    elif ext in {".doc", ".ppt", ".xls"}:
        if not head.startswith(_OLE_SIGNATURE):
            raise ValidationError(f"Rejected '{filename}': content is not a valid legacy Office file.")
    elif ext in _TEXT_EXTENSIONS:
        if b"\x00" in head:
            raise ValidationError(f"Rejected '{filename}': binary content in a text file.")
        try:
            head.decode("utf-8")
        except UnicodeDecodeError:
            try:
                head.decode("latin-1")
            except UnicodeDecodeError as exc:  # pragma: no cover - latin-1 decodes everything
                raise ValidationError(f"Rejected '{filename}': unreadable text encoding.") from exc


def _validate_pdf(filename: str, full_path: Path) -> None:
    try:
        import pypdf
    except ImportError:  # pragma: no cover - pypdf is a declared dependency
        return
    try:
        reader = pypdf.PdfReader(str(full_path), strict=False)
        if reader.is_encrypted:
            raise ValidationError(f"Rejected '{filename}': password-protected PDFs cannot be evaluated.")
        page_count = len(reader.pages)
    except ValidationError:
        raise
    except Exception as exc:
        raise ValidationError(f"Rejected '{filename}': the PDF is corrupt or unreadable.") from exc
    if page_count < 1:
        raise ValidationError(f"Rejected '{filename}': the PDF has no pages.")


def _validate_ooxml(filename: str, full_path: Path, required_prefix: str) -> None:
    try:
        with zipfile.ZipFile(full_path) as zf:
            names = zf.namelist()
            bad = zf.testzip()
    except zipfile.BadZipFile as exc:
        raise ValidationError(f"Rejected '{filename}': the document container is corrupt.") from exc
    if bad is not None:
        raise ValidationError(f"Rejected '{filename}': the document container is corrupt.")
    if "[Content_Types].xml" not in names or not any(n.startswith(required_prefix) for n in names):
        raise ValidationError(f"Rejected '{filename}': not a valid Office Open XML document.")
    if any(n.lower().endswith("vbaproject.bin") for n in names):
        raise ValidationError(f"Rejected '{filename}': macro-enabled documents are not accepted.")
    if any(".." in n or n.startswith("/") for n in names):
        raise ValidationError(f"Rejected '{filename}': unsafe paths inside the document container.")


__all__ = ["ALLOWED_DOCUMENT_EXTENSIONS", "sanitize_filename", "validate_document_bytes", "io"]
