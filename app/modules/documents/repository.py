from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.documents.models import Document, DocumentSource
from app.repositories.base import BaseRepository


class DocumentRepository(BaseRepository[Document]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Document)

    def list_for_startup(self, startup_id: UUID) -> Sequence[Document]:
        statement = select(Document).where(Document.startup_id == startup_id).order_by(Document.created_at.desc())
        return self.db.scalars(statement).all()


class DocumentSourceRepository(BaseRepository[DocumentSource]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, DocumentSource)

    def list_for_startup(self, startup_id: UUID) -> Sequence[DocumentSource]:
        statement = (
            select(DocumentSource)
            .where(DocumentSource.startup_id == startup_id)
            .order_by(DocumentSource.created_at.desc())
        )
        return self.db.scalars(statement).all()
