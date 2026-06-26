from datetime import datetime
import uuid
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    request_id: str
    timestamp: str

def make_response(
    request: Any,
    data: Optional[Any] = None,
    message: str = "Operation successful",
    metadata: Optional[Dict[str, Any]] = None,
    success: bool = True
) -> Dict[str, Any]:
    req_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return {
        "success": success,
        "message": message,
        "data": data,
        "metadata": metadata or {},
        "request_id": req_id,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
