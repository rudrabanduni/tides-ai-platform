import re
from pydantic import BaseModel, Field


class Chunk(BaseModel):
    chunk_id: str = Field(..., description="Unique identifier for the chunk.")
    document_id: str = Field(..., description="The parent document identifier.")
    page_start: int = Field(..., description="First page or slide index of the chunk.")
    page_end: int = Field(..., description="Last page or slide index of the chunk.")
    text: str = Field(..., description="The text content of this chunk.")
    estimated_tokens: int = Field(..., description="Estimated token count.")
    section_title: str | None = Field(default=None, description="Inferred section header.")
    word_count: int = Field(..., description="Word count of this chunk.")


class SemanticChunker:
    """Chunks documents into semantic fragments respecting token boundaries."""

    @staticmethod
    def chunk_document(document_id: str, text: str, max_tokens: int = 1500) -> list[Chunk]:
        if not text or not text.strip():
            return []

        def estimate_tokens(txt: str) -> int:
            return int(len(txt.split()) * 1.3)

        def extract_section_title(txt: str) -> str | None:
            lines = [line.strip() for line in txt.split("\n") if line.strip()]
            for line in lines[:3]:
                # If a line contains typical header keywords, return it
                if len(line) < 60 and any(h in line.lower() for h in [
                    "introduction", "problem", "solution", "product", "market",
                    "competition", "financial", "revenue", "team", "founder",
                    "technology", "trl", "risk", "summary", "milestone", "traction"
                ]):
                    return line
            return None

        # Check for slide delimiters
        if "--- Slide ---" in text:
            elements = text.split("--- Slide ---")
            is_slide = True
        else:
            # Paragraphs/page boundaries
            elements = [el.strip() for el in text.split("\n\n") if el.strip()]
            is_slide = False

        chunks = []
        current_elements = []
        current_tokens = 0
        page_start = 1
        current_page = 1

        for el in elements:
            el_text = el.strip()
            if not el_text:
                continue

            el_tokens = estimate_tokens(el_text)

            # Flush current buffer if adding next element exceeds limit
            if current_tokens + el_tokens > max_tokens and current_elements:
                chunk_text = "\n\n".join(current_elements)
                chunks.append(Chunk(
                    chunk_id=f"{document_id}_chunk_{len(chunks)}",
                    document_id=document_id,
                    page_start=page_start,
                    page_end=current_page - 1 if is_slide else page_start,
                    text=chunk_text,
                    estimated_tokens=estimate_tokens(chunk_text),
                    section_title=extract_section_title(chunk_text),
                    word_count=len(chunk_text.split())
                ))
                current_elements = []
                current_tokens = 0
                page_start = current_page

            current_elements.append(el_text)
            current_tokens += el_tokens
            if is_slide:
                current_page += 1

            # Flush immediately if buffer is full
            if current_tokens >= max_tokens:
                chunk_text = "\n\n".join(current_elements)
                chunks.append(Chunk(
                    chunk_id=f"{document_id}_chunk_{len(chunks)}",
                    document_id=document_id,
                    page_start=page_start,
                    page_end=current_page - 1 if is_slide else page_start,
                    text=chunk_text,
                    estimated_tokens=estimate_tokens(chunk_text),
                    section_title=extract_section_title(chunk_text),
                    word_count=len(chunk_text.split())
                ))
                current_elements = []
                current_tokens = 0
                page_start = current_page

        # Flush final elements
        if current_elements:
            chunk_text = "\n\n".join(current_elements)
            chunks.append(Chunk(
                chunk_id=f"{document_id}_chunk_{len(chunks)}",
                document_id=document_id,
                page_start=page_start,
                page_end=current_page - 1 if is_slide else page_start,
                text=chunk_text,
                estimated_tokens=estimate_tokens(chunk_text),
                section_title=extract_section_title(chunk_text),
                word_count=len(chunk_text.split())
            ))

        return chunks
