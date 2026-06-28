from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class EvidenceSnippet(BaseModel):
    id: str
    source_document_id: Optional[str] = None
    snippet: str
    metadata: Dict[str, Any] = {}

class EvidenceMemory:
    def __init__(self):
        self.evidence_pool: Dict[str, EvidenceSnippet] = {}

    def add_evidence(self, id: str, snippet: str, source_doc: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
        self.evidence_pool[id] = EvidenceSnippet(
            id=id,
            source_document_id=source_doc,
            snippet=snippet,
            metadata=metadata or {}
        )

    def retrieve_by_keywords(self, keywords: List[str]) -> List[EvidenceSnippet]:
        results = []
        for ev in self.evidence_pool.values():
            text = ev.snippet.lower()
            if any(kw.lower() in text for kw in keywords):
                results.append(ev)
        return results

    def get_all(self) -> List[EvidenceSnippet]:
        return list(self.evidence_pool.values())
