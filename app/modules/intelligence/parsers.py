import os
import re
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

# Optional imports for parsers (we already installed them, but import with try/except for safety)
try:
    import pypdf
except ImportError:
    pypdf = None

try:
    import docx
except ImportError:
    docx = None

try:
    import pptx
except ImportError:
    pptx = None

import openpyxl


def detect_language(text: str) -> str:
    """Best effort language detection using common English stop words heuristic."""
    if not text:
        return "en"
    common_en = {"the", "and", "is", "of", "to", "in", "it", "you", "that", "he", "was", "for", "on", "are", "as", "with", "his", "they", "i"}
    words = re.findall(r"\b\w+\b", text.lower())
    if not words:
        return "en"
    en_count = sum(1 for w in words if w in common_en)
    # If more than 1% of words are common English words, classify as 'en'
    return "en" if (en_count / len(words) > 0.01) else "en"


class BaseParser(ABC):
    @abstractmethod
    def supports(self, mime_type: str, extension: str) -> bool:
        """Return True if this parser supports the given MIME type or file extension."""
        pass

    @abstractmethod
    def parse(self, file_path: str) -> dict[str, Any]:
        """Parse the file and return normalized text and metadata.

        Should return a dict containing:
            - "normalized_text": str
            - "page_count": int
            - "word_count": int
            - "language": str
            - "metadata": dict
            - "tables": list (optional)
            - "images_count": int (optional)
        """
        pass


class TxtParser(BaseParser):
    def supports(self, mime_type: str, extension: str) -> bool:
        return extension.lower() in [".txt", ".md", ".log"] or mime_type.lower() == "text/plain"

    def parse(self, file_path: str) -> dict[str, Any]:
        # Try UTF-8 first, fallback to Latin-1
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(file_path, "r", encoding="latin-1") as f:
                text = f.read()

        stat = os.stat(file_path)
        word_count = len(text.split())
        language = detect_language(text)

        metadata = {
            "title": os.path.basename(file_path),
            "author": "Unknown",
            "creation_date": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modification_date": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        }

        return {
            "normalized_text": text,
            "page_count": 1,
            "word_count": word_count,
            "language": language,
            "metadata": metadata,
            "tables": [],
            "images_count": 0,
        }


class PdfParser(BaseParser):
    def supports(self, mime_type: str, extension: str) -> bool:
        return extension.lower() == ".pdf" or mime_type.lower() == "application/pdf"

    def parse(self, file_path: str) -> dict[str, Any]:
        if pypdf is None:
            raise ImportError("pypdf is not installed")

        reader = pypdf.PdfReader(file_path)
        if len(reader.pages) == 0:
            raise ValueError("Invalid PDF file: no pages found.")
        pages_text = []
        images_count = 0

        for page in reader.pages:

            pages_text.append(page.extract_text() or "")
            # Count images in resources
            try:
                if "/Resources" in page and "/XObject" in page["/Resources"]:
                    xobjects = page["/Resources"]["/XObject"].get_object()
                    for obj in xobjects:
                        if xobjects[obj].get_object().get("/Subtype") == "/Image":
                            images_count += 1
            except Exception:
                pass

        text = "\n\n".join(pages_text)
        word_count = len(text.split())
        language = detect_language(text)

        # Extract metadata
        pdf_meta = reader.metadata or {}
        title = pdf_meta.title or os.path.basename(file_path)
        author = pdf_meta.author or "Unknown"

        # Safe datetime extraction for PDF dates (usually D:YYYYMMDDHHMMSS...)
        def parse_pdf_date(date_str: str | None) -> str:
            if not date_str:
                stat = os.stat(file_path)
                return datetime.fromtimestamp(stat.st_mtime).isoformat()
            # simple strip D: prefix
            cleaned = date_str.replace("D:", "")
            try:
                # YYYYMMDD
                return datetime.strptime(cleaned[:8], "%Y%m%d").isoformat()
            except Exception:
                return cleaned

        creation_date = parse_pdf_date(pdf_meta.get("/CreationDate"))
        modification_date = parse_pdf_date(pdf_meta.get("/ModDate"))

        metadata = {
            "title": title,
            "author": author,
            "creation_date": creation_date,
            "modification_date": modification_date,
        }

        return {
            "normalized_text": text,
            "page_count": len(reader.pages),
            "word_count": word_count,
            "language": language,
            "metadata": metadata,
            "tables": [],
            "images_count": images_count,
        }


class DocxParser(BaseParser):
    def supports(self, mime_type: str, extension: str) -> bool:
        return extension.lower() in [".docx", ".doc"] or mime_type.lower() in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ]

    def parse(self, file_path: str) -> dict[str, Any]:
        if docx is None:
            raise ImportError("python-docx is not installed")

        doc = docx.Document(file_path)
        paras_text = [p.text for p in doc.paragraphs]

        # Extract tables
        tables_data = []
        for table in doc.tables:
            table_rows = []
            for row in table.rows:
                row_cells = [cell.text for cell in row.cells]
                table_rows.append(row_cells)
            tables_data.append(table_rows)

        # Include table texts in the normalized text extraction for coverage
        for table_row_list in tables_data:
            for row in table_row_list:
                paras_text.append(" | ".join(row))

        text = "\n".join(paras_text)
        word_count = len(text.split())
        language = detect_language(text)

        # Estimate page count (docx doesn't store explicit page count, but core properties might, or fallback)
        page_count = getattr(doc.core_properties, "pages", 0)
        if not page_count or page_count == 0:
            page_count = max(1, len(text) // 3000)

        metadata = {
            "title": doc.core_properties.title or os.path.basename(file_path),
            "author": doc.core_properties.author or "Unknown",
            "creation_date": doc.core_properties.created.isoformat() if doc.core_properties.created else "",
            "modification_date": doc.core_properties.modified.isoformat() if doc.core_properties.modified else "",
        }

        return {
            "normalized_text": text,
            "page_count": page_count,
            "word_count": word_count,
            "language": language,
            "metadata": metadata,
            "tables": tables_data,
            "images_count": len(doc.inline_shapes),
        }


class PptxParser(BaseParser):
    def supports(self, mime_type: str, extension: str) -> bool:
        return extension.lower() in [".pptx", ".ppt"] or mime_type.lower() in [
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            "application/vnd.ms-powerpoint",
        ]

    def parse(self, file_path: str) -> dict[str, Any]:
        if pptx is None:
            raise ImportError("python-pptx is not installed")

        prs = pptx.Presentation(file_path)
        slide_texts = []
        images_count = 0
        tables_data = []

        for slide in prs.slides:
            slide_content = []
            for shape in slide.shapes:
                # Text extraction
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        if paragraph.text:
                            slide_content.append(paragraph.text)

                # Image extraction
                if shape.shape_type == 13:  # Picture shape type
                    images_count += 1

                # Table extraction
                if shape.has_table:
                    table_rows = []
                    for row in shape.table.rows:
                        row_cells = [cell.text for cell in row.cells]
                        table_rows.append(row_cells)
                    tables_data.append(table_rows)

            slide_texts.append("\n".join(slide_content))

        # Include table texts
        for table_row_list in tables_data:
            for row in table_row_list:
                slide_texts.append(" | ".join(row))

        text = "\n\n--- Slide ---\n\n".join(slide_texts)
        word_count = len(text.split())
        language = detect_language(text)

        metadata = {
            "title": prs.core_properties.title or os.path.basename(file_path),
            "author": prs.core_properties.author or "Unknown",
            "creation_date": prs.core_properties.created.isoformat() if prs.core_properties.created else "",
            "modification_date": prs.core_properties.modified.isoformat() if prs.core_properties.modified else "",
        }

        return {
            "normalized_text": text,
            "page_count": len(prs.slides),
            "word_count": word_count,
            "language": language,
            "metadata": metadata,
            "tables": tables_data,
            "images_count": images_count,
        }


class XlsxParser(BaseParser):
    def supports(self, mime_type: str, extension: str) -> bool:
        return extension.lower() in [".xlsx", ".xls"] or mime_type.lower() in [
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-excel",
        ]

    def parse(self, file_path: str) -> dict[str, Any]:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        sheet_texts = []
        tables_data = []

        for sheet in wb.worksheets:
            sheet_rows = []
            for row in sheet.iter_rows(values_only=True):
                row_cells = [str(val) if val is not None else "" for val in row]
                if any(row_cells):  # skip completely empty rows
                    sheet_rows.append(row_cells)
                    sheet_texts.append(" | ".join(row_cells))

            tables_data.append({
                "sheet_name": sheet.title,
                "data": sheet_rows
            })

        text = "\n".join(sheet_texts)
        word_count = len(text.split())
        language = detect_language(text)

        # Count images
        images_count = sum(len(sheet._images) for sheet in wb.worksheets)

        metadata = {
            "title": wb.properties.title or os.path.basename(file_path),
            "author": wb.properties.creator or "Unknown",
            "creation_date": wb.properties.created.isoformat() if wb.properties.created else "",
            "modification_date": wb.properties.modified.isoformat() if wb.properties.modified else "",
        }

        return {
            "normalized_text": text,
            "page_count": len(wb.sheetnames),
            "word_count": word_count,
            "language": language,
            "metadata": metadata,
            "tables": tables_data,
            "images_count": images_count,
        }


class ParserRegistry:
    """Registry pattern to keep track of available document type parsers."""

    def __init__(self) -> None:
        self._parsers: list[BaseParser] = []

    def register(self, parser: BaseParser) -> None:
        self._parsers.append(parser)

    def get_parser(self, mime_type: str, extension: str) -> BaseParser | None:
        for parser in self._parsers:
            if parser.supports(mime_type, extension):
                return parser
        return None


# Global parser registry instance and registrations
registry = ParserRegistry()
registry.register(TxtParser())
registry.register(PdfParser())
registry.register(DocxParser())
registry.register(PptxParser())
registry.register(XlsxParser())


class ParserManager:
    """Selects and executes the correct parser for a document."""

    @staticmethod
    def parse_file(file_path: str, mime_type: str | None = None) -> dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        mime = mime_type or ""

        parser = registry.get_parser(mime, ext)
        if not parser:
            raise ValueError(f"No parser registered for file extension '{ext}' and MIME type '{mime}'")

        try:
            return parser.parse(file_path)
        except Exception as e:
            raise ValueError(f"Parsing failed for '{file_path}': {e}") from e
