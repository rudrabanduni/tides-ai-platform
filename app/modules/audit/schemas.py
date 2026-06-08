from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    actor_id: UUID | None
    entity_type: str
    entity_id: str
    action: str
    reason: str | None
    details: dict | None
    created_at: datetime
