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


def _canon(text: str) -> str:
    """Canonical form used on BOTH the value and the document text.

    Handles PDF-extraction artefacts seen in real decks: run-together tokens ("35,700SAM"),
    letter-spaced headings ("S A M D"), "%" vs "percent", thousands separators and stray symbols.
    """
    t = (text or "").lower().replace("%", " percent ").replace("&", " and ")
    t = re.sub(r"\b(?:[a-z] ){2,}[a-z]\b", lambda m: m.group(0).replace(" ", ""), t)  # S A M D -> samd
    t = re.sub(r"(?<=\d)(?=[a-z])|(?<=[a-z])(?=\d)", " ", t)  # 35700sam -> 35700 sam
    t = re.sub(r"(?<=\d),(?=\d{3}\b)", "", t)  # 21,420 -> 21420
    t = re.sub(r"[^a-z0-9.]+", " ", t)
    t = re.sub(r"(?<!\d)\.|\.(?!\d)", " ", t)  # keep decimal points only
    return re.sub(r"\s+", " ", t).strip()


def _canon_tokens(text: str) -> list[str]:
    out = []
    for tok in _canon(text).split():
        if tok.isdigit() or any(ch.isdigit() for ch in tok):
            out.append(tok)
        elif len(tok) >= 3 and tok not in _STOPWORDS and tok not in {"null", "none", "true", "false", "name", "role", "value"}:
            out.append(tok)
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

    Match rules (deterministic), applied to windows of 1-3 consecutive lines on one page after the
    same canonicalisation of value and document (see `_canon`):
      1. the canonical value (<= 120 chars) occurs verbatim, or
      2. at least 60% of the value's distinctive tokens (and >= 2 tokens) occur in the window,
         and EVERY numeric token of the value occurs in the window.
    The tightest qualifying window is cited.
    """
    if not document_text:
        return None, None
    if isinstance(value, (dict, list)):
        # Structured values: locate each item by its IDENTIFYING field only (a founder's name, a
        # patent title, an SDG name, a competitor's name), never by model-written explanation text,
        # so an inferred item (e.g. an SDG the deck never mentions) cannot borrow a nearby passage.
        leaves: list[str] = []

        def _identity(d: dict) -> str | None:
            for x in d.values():
                if isinstance(x, str) and len(x.strip()) >= 3:
                    return x.strip()
            return None

        def _walk(v: Any) -> None:
            if isinstance(v, dict):
                ident = _identity(v)
                if ident:
                    leaves.append(ident)
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
    needle = _canon(raw)[:120]
    toks = _canon_tokens(raw)[:24]
    numeric = [t for t in toks if any(ch.isdigit() for ch in t)]
    best: tuple[float, str, int | None] | None = None
    for page_no, lines in split_pages(document_text):
        canon_lines = [_canon(line) for line in lines]
        for i in range(len(lines)):
            # Windows of 1-3 consecutive lines: PDF extraction often splits one statement across lines.
            for span in (1, 2, 3):
                if i + span > len(lines):
                    break
                hay = " ".join(canon_lines[i:i + span])
                passage = "\n".join(lines[i:i + span])
                hay_tokens = set(hay.split())
                if needle and len(needle) >= 4 and needle in hay:
                    return passage[:max_len], page_no
                if len(toks) < 2:
                    continue
                # Words may sit inside run-together PDF text ("LaunchedJUN"); numbers must match exactly.
                hits = sum(1 for t in toks if (t in hay_tokens if any(ch.isdigit() for ch in t) else t in hay))
                ratio = hits / len(toks)
                # Every number in the value must appear: figures are the facts most worth citing exactly.
                if hits >= 2 and ratio >= 0.6 and all(n in hay_tokens for n in numeric):
                    score = ratio - 0.01 * (span - 1)  # prefer the tightest passage
                    if best is None or score > best[0]:
                        best = (score, passage[:max_len], page_no)
    if best:
        return best[1], best[2]
    return None, None
