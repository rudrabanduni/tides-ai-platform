import os
import re
from enum import Enum


class DocumentClassification(str, Enum):
    PITCH_DECK = "Pitch Deck"
    BUSINESS_PLAN = "Business Plan"
    FINANCIAL_STATEMENT = "Financial Statement"
    PATENT = "Patent"
    RESEARCH_PAPER = "Research Paper"
    EXCEL_INTAKE = "Excel Intake"
    TEXT = "Text"
    PDF = "PDF"
    DOCX = "DOCX"
    PPTX = "PPTX"
    WEBSITE_EXPORT = "Website Export"
    UNKNOWN = "Unknown"


def classify_document(filename: str, content_type: str | None = None) -> DocumentClassification:
    """Automatically classify a document based on extension, mime type, and filename heuristics.

    Prioritizes specific keyword heuristics, falling back to extension and MIME-type based defaults.
    """
    ext = os.path.splitext(filename)[1].lower()
    name_lower = filename.lower()

    # 1. Filename keyword heuristics (highest priority)
    if any(kw in name_lower for kw in ["pitch", "deck", "slide", "presentation", "demo", "intro"]):
        return DocumentClassification.PITCH_DECK
    if any(kw in name_lower for kw in ["plan", "business_plan", "bizplan", "proposal"]):
        return DocumentClassification.BUSINESS_PLAN
    if any(kw in name_lower for kw in ["financial", "statement", "sheet", "report", "balance", "revenue", "tax", "budget", "pnl", "cash"]):
        return DocumentClassification.FINANCIAL_STATEMENT
    if any(kw in name_lower for kw in ["patent", "invention", "claims"]):
        return DocumentClassification.PATENT
    if any(kw in name_lower for kw in ["paper", "research", "journal", "thesis", "publication"]):
        return DocumentClassification.RESEARCH_PAPER
    if any(kw in name_lower for kw in ["intake", "application", "form"]):
        return DocumentClassification.EXCEL_INTAKE

    # 2. Mime type and extension fallbacks
    if ext in [".xlsx", ".xls", ".csv"] or (content_type and content_type in [
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.ms-excel",
        "text/csv"
    ]):
        return DocumentClassification.EXCEL_INTAKE

    if ext in [".pptx", ".ppt"] or (content_type and content_type in [
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        "application/vnd.ms-powerpoint"
    ]):
        return DocumentClassification.PITCH_DECK

    if ext == ".pdf" or (content_type == "application/pdf"):
        return DocumentClassification.PDF

    if ext in [".docx", ".doc"] or (content_type and content_type in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword"
    ]):
        return DocumentClassification.DOCX

    if ext in [".txt", ".md", ".log"] or (content_type == "text/plain"):
        return DocumentClassification.TEXT

    if ext in [".html", ".htm"] or (content_type == "text/html"):
        return DocumentClassification.WEBSITE_EXPORT

    return DocumentClassification.UNKNOWN
