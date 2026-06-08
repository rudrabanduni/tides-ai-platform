from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.audit.models import AuditLog
from app.modules.audit.repository import AuditLogRepository


class AuditService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = AuditLogRepository(db)

    def log(
        self,
        *,
        actor_id: UUID | None,
        entity_type: str,
        entity_id: UUID | str,
        action: str,
        reason: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> AuditLog:
        audit_log = AuditLog(
            actor_id=actor_id,
            entity_type=entity_type,
            entity_id=str(entity_id),
            action=action,
            reason=reason,
            details=details,
        )
        return self.repository.add(audit_log)
