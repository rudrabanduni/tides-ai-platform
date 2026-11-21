"""evidence_locator.py - Grounds extracted claims in the source document text.

An extracted value only counts as documentary evidence when a supporting passage can actually
be found in the parsed document. Otherwise the claim keeps its value but carries no snippet,
so the domain specialists and report treat it as applicant-reported / not documented.
"""

from __future__ import annotations

import json
import re
from typing import Any

_PAGE_MARK = re.compile(r"^\[Page (\d+)\]\s*$")
_STOPWORDS = {
    "the", "and", "for", "with", "from", "that", "this", "into", "our", "are", "per", "has", "have",
    "will", "its", "their", "over", "under", "not", "all", "any", "each", "more", "than",
}


def _flatten(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        try:
            return json.dumps(value, ensure_ascii=False)
        except TypeError:
            return str(value)
    return str(value)


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.lower()).strip()


def _tokens(text: str) -> list[str]:
    toks = re.findall(r"[a-z0-9][a-z0-9.%₹$,-]*", text.lower())
    out = []
    for t in toks:
        t = t.strip(".,-")
        if len(t) < 3 or t in _STOPWORDS:
            continue
        if t in {"null", "none", "true", "false", "name", "role", "value"}:
            continue
        out.append(t)
    return list(dict.fromkeys(out))


def split_pages(document_text: str) -> list[tuple[int | None, list[str]]]:
    pages: list[tuple[int | None, list[str]]] = []
    current_page: int | None = None
    current: list[str] = []
    for line in (document_text or "").splitlines():
        m = _PAGE_MARK.match(line.strip())
        if m:
            if current:
                pages.append((current_page, current))
            current_page, current = int(m.group(1)), []
            continue
        if line.strip():
            current.append(line.strip())
    if current:
        pages.append((current_page, current))
    return pages


def locate_passage(document_text: str, value: Any, *, max_len: int = 300) -> tuple[str | None, int | None]:
    """Returns (passage, page_number) where the value is supported in the document, else (None, None).

    Match rules (deterministic):
      1. the normalised value (<= 120 chars) occurs verbatim in a line, or
      2. at least 60% of the value's distinctive tokens (and >= 2 tokens) occur in one line,
         and every numeric token of the value occurs in that line.
    """
    if not document_text:
        return None, None
    if isinstance(value, (dict, list)):
        # Structured values: locate their individual string leaves and cite the first passages found.
        leaves: list[str] = []

        def _walk(v: Any) -> None:
            if isinstance(v, dict):
                for x in v.values():
                    _walk(x)
            elif isinstance(v, list):
                for x in v:
                    _walk(x)
            elif v is not None and len(str(v).strip()) >= 3:
                leaves.append(str(v).strip())

        _walk(value)
        found: list[str] = []
        first_page: int | None = None
        for leaf in leaves[:8]:
            passage, page = locate_passage(document_text, leaf, max_len=max_len)
            if passage and passage not in found:
                found.append(passage)
                first_page = first_page or page
            if len(found) >= 3:
                break
        if not found:
            return None, None
        return " / ".join(found)[:max_len], first_page
    raw = _flatten(value)
    if not raw.strip():
        return None, None
    needle = _norm(raw)[:120]
    toks = _tokens(raw)[:24]
    numeric = [t for t in toks if any(ch.isdigit() for ch in t)]
    best: tuple[float, str, int | None] | None = None
    for page_no, lines in split_pages(document_text):
        for line in lines:
            hay = _norm(line)
            if needle and len(needle) >= 4 and needle in hay:
                return line[:max_len], page_no
            if len(toks) < 2:
                continue
            hits = sum(1 for t in toks if t in hay)
            ratio = hits / len(toks)
            if hits >= 2 and ratio >= 0.6 and all(n in hay for n in numeric):
                if best is None or ratio > best[0]:
                    best = (ratio, line[:max_len], page_no)
    if best:
        return best[1], best[2]
    return None, None
