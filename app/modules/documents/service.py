from collections.abc import Sequence
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import DocumentProcessingStatus, DocumentType
from app.core.exceptions import NotFoundError, ValidationError
from app.modules.audit.service import AuditService
from app.modules.documents.models import Document, DocumentSource
from app.modules.documents.repository import DocumentRepository, DocumentSourceRepository
from app.modules.documents.schemas import DocumentParsedTextUpdate, DocumentSourceCreate
from app.modules.startups.service import StartupService


class DocumentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.documents = DocumentRepository(db)
        self.sources = DocumentSourceRepository(db)
        self.startups = StartupService(db)
        self.audit = AuditService(db)

    def upload(
        self,
        startup_id: UUID,
        *,
        file: UploadFile,
        document_type: DocumentType,
        actor_id: UUID | None,
    ) -> Document:
        self.startups.get(startup_id)
        settings = get_settings()
        original_filename = Path(file.filename or "upload.bin").name
        stored_filename = f"{uuid4()}_{original_filename}"
        startup_dir = Path(settings.upload_dir) / str(startup_id)
        startup_dir.mkdir(parents=True, exist_ok=True)
        file_path = startup_dir / stored_filename

        max_bytes = settings.max_upload_size_mb * 1024 * 1024
        size = 0
        with file_path.open("wb") as target:
            while chunk := file.file.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    target.close()
                    file_path.unlink(missing_ok=True)
                    raise ValidationError(f"File exceeds {settings.max_upload_size_mb} MB limit")
                target.write(chunk)

        document = Document(
            startup_id=startup_id,
            document_type=document_type,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=str(file_path),
            content_type=file.content_type,
            file_size=size,
            processing_status=DocumentProcessingStatus.UPLOADED,
            uploaded_by=actor_id,
        )
        self.documents.add(document)
        self.audit.log(
            actor_id=actor_id,
            entity_type="document",
            entity_id=document.id,
            action="document_uploaded",
            details={"startup_id": str(startup_id), "document_type": document_type.value},
        )
        self.db.commit()
        self.db.refresh(document)
        return document

    def get_document(self, document_id: UUID) -> Document:
        document = self.documents.get(document_id)
        if not document:
            raise NotFoundError("Document not found")
        return document

    def list_for_startup(self, startup_id: UUID) -> Sequence[Document]:
        self.startups.get(startup_id)
        return self.documents.list_for_startup(startup_id)

    def update_parsed_text(
        self,
        document_id: UUID,
        payload: DocumentParsedTextUpdate,
        *,
        actor_id: UUID | None,
    ) -> Document:
        document = self.get_document(document_id)
        document.parsed_text = payload.parsed_text
        document.processing_status = payload.processing_status
        self.audit.log(
            actor_id=actor_id,
            entity_type="document",
            entity_id=document.id,
            action="document_parsed_text_updated",
        )
        self.db.commit()
        self.db.refresh(document)
        return document

    def create_source(
        self,
        startup_id: UUID,
        payload: DocumentSourceCreate,
        *,
        actor_id: UUID | None,
    ) -> DocumentSource:
        self.startups.get(startup_id)
        if payload.document_id:
            document = self.get_document(payload.document_id)
            if document.startup_id != startup_id:
                raise ValidationError("Document source must reference a document from the same startup")
        source = DocumentSource(startup_id=startup_id, **payload.model_dump())
        self.sources.add(source)
        self.audit.log(
            actor_id=actor_id,
            entity_type="document_source",
            entity_id=source.id,
            action="document_source_created",
            details={"startup_id": str(startup_id), "source_type": source.source_type.value},
        )
        self.db.commit()
        self.db.refresh(source)
        return source

    def get_source(self, source_id: UUID) -> DocumentSource:
        source = self.sources.get(source_id)
        if not source:
            raise NotFoundError("Document source not found")
        return source

    def list_sources_for_startup(self, startup_id: UUID) -> Sequence[DocumentSource]:
        self.startups.get(startup_id)
        return self.sources.list_for_startup(startup_id)
