from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class MemoryMessage(BaseModel):
    role: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ConversationMemory:
    def __init__(self):
        self.history: List[MemoryMessage] = []

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        self.history.append(MemoryMessage(role=role, content=content, metadata=metadata or {}))

    def get_history(self) -> List[MemoryMessage]:
        return self.history

    def clear(self):
        self.history = []
