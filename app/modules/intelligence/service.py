import os
from uuid import UUID

from sqlalchemy.orm import Session


from app.modules.intelligence.models import StartupIntelligenceProfile, StartupProcessingStatus
from app.modules.intelligence.repository import (
    FieldConflictRepository,
    FieldSourceRepository,
    FieldVersionRepository,
    KnowledgeFieldRegistryRepository,
    StartupClaimRepository,
    StartupEvidenceRepository,
    StartupIntelligenceProfileRepository,
    StartupIntelligenceProfileVersionRepository,
    StartupProcessingStatusRepository,
)


class IntelligenceService:
    """Foundational service orchestrating TIE database access and event dispatching."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.field_registry = KnowledgeFieldRegistryRepository(db)
        self.profiles = StartupIntelligenceProfileRepository(db)
        self.claims = StartupClaimRepository(db)
        self.evidence = StartupEvidenceRepository(db)
        self.versions = FieldVersionRepository(db)
        self.conflicts = FieldConflictRepository(db)
        self.sources = FieldSourceRepository(db)
        self.status = StartupProcessingStatusRepository(db)
        self.profile_versions = StartupIntelligenceProfileVersionRepository(db)

    def get_profile(self, startup_id: UUID) -> StartupIntelligenceProfile | None:
        """Fetch the unified Startup Intelligence Profile if it exists."""
        return self.profiles.get_by_startup(startup_id)

    def get_processing_status(self, startup_id: UUID, pipeline_name: str) -> StartupProcessingStatus | None:
        """Fetch current processing logs for a startup's AI pipeline execution."""
        return self.status.get_by_startup_pipeline(startup_id, pipeline_name)

    def get_document_metadata(self, file_path: str) -> dict[str, Any] | None:
        """Helper to read sidecar document metadata if it exists."""
        meta_path = file_path + ".meta.json"
        if os.path.exists(meta_path):
            import json
            try:
                with open(meta_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def process_document(self, document_id: UUID, actor_id: UUID | None = None) -> dict[str, Any]:
        """Runs the document intelligence processing pipeline on a registered document.

        Updates stages: REGISTERED, CLASSIFIED, PARSING, PARSED, FAILED.
        Publishes: DocumentRegistered, DocumentClassified, DocumentParsed, DocumentFailed.
        """
        import hashlib
        import json
        import time
        from app.core.enums import DocumentProcessingStatus, DocumentType
        from app.modules.documents.repository import DocumentRepository
        from app.modules.intelligence.classification import classify_document, DocumentClassification
        from app.modules.intelligence.events import dispatcher, Event
        from app.modules.intelligence.models import PipelineStatus
        from app.modules.intelligence.parsers import ParserManager

        doc_repo = DocumentRepository(self.db)
        document = doc_repo.get(document_id)
        if not document:
            raise ValueError(f"Document with ID {document_id} not found")

        # Map DocumentClassification to existing DocumentType
        classification_mapping = {
            DocumentClassification.PITCH_DECK: DocumentType.PITCH_DECK,
            DocumentClassification.BUSINESS_PLAN: DocumentType.BUSINESS_PLAN,
            DocumentClassification.FINANCIAL_STATEMENT: DocumentType.COMPANY_DOCUMENT,
            DocumentClassification.PATENT: DocumentType.COMPANY_DOCUMENT,
            DocumentClassification.RESEARCH_PAPER: DocumentType.OTHER,
            DocumentClassification.EXCEL_INTAKE: DocumentType.APPLICATION_FORM,
            DocumentClassification.TEXT: DocumentType.OTHER,
            DocumentClassification.PDF: DocumentType.OTHER,
            DocumentClassification.DOCX: DocumentType.OTHER,
            DocumentClassification.PPTX: DocumentType.PITCH_DECK,
            DocumentClassification.WEBSITE_EXPORT: DocumentType.OTHER,
            DocumentClassification.UNKNOWN: DocumentType.OTHER,
        }

        # Retrieve or create status record
        status_record = self.status.get_by_startup_pipeline(document.startup_id, "document_intelligence")
        if not status_record:
            status_record = self.status.create_status(
                startup_id=document.startup_id,
                pipeline_name="document_intelligence",
                stage="REGISTERED"
            )
        else:
            self.status.update_progress(status_record.id, "REGISTERED", 0, PipelineStatus.RUNNING)
            self.db.refresh(status_record)

        start_time = time.time()
        checksum = ""
        classification = DocumentClassification.UNKNOWN

        try:
            # 1. REGISTERED Stage
            self.status.update_progress(status_record.id, "REGISTERED", 20, PipelineStatus.RUNNING)
            
            # Calculate checksum
            if os.path.exists(document.file_path):
                hash_md5 = hashlib.md5()
                with open(document.file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_md5.update(chunk)
                checksum = hash_md5.hexdigest()
            else:
                raise FileNotFoundError(f"Source file not found at path: {document.file_path}")

            dispatcher.publish(Event(
                event_name="DocumentRegistered",
                payload={
                    "document_id": str(document.id),
                    "startup_id": str(document.startup_id),
                    "filename": document.original_filename,
                    "checksum": checksum,
                }
            ))

            # 2. CLASSIFIED Stage
            self.status.update_progress(status_record.id, "CLASSIFIED", 40, PipelineStatus.RUNNING)
            classification = classify_document(document.original_filename, document.content_type)
            
            # Map and update db DocumentType
            db_doc_type = classification_mapping.get(classification, DocumentType.OTHER)
            document.document_type = db_doc_type
            self.db.add(document)
            self.db.flush()

            dispatcher.publish(Event(
                event_name="DocumentClassified",
                payload={
                    "document_id": str(document.id),
                    "startup_id": str(document.startup_id),
                    "filename": document.original_filename,
                    "classification": classification.value,
                    "checksum": checksum,
                }
            ))

            # 3. PARSING Stage
            self.status.update_progress(status_record.id, "PARSING", 60, PipelineStatus.RUNNING)
            parsed_result = ParserManager.parse_file(document.file_path, document.content_type)

            # 4. PARSED (Complete) Stage
            document.parsed_text = parsed_result["normalized_text"]
            document.processing_status = DocumentProcessingStatus.PARSED
            self.db.add(document)
            self.db.flush()

            # Save sidecar metadata
            meta_path = document.file_path + ".meta.json"
            meta_data = {
                "document_id": str(document.id),
                "startup_id": str(document.startup_id),
                "filename": document.original_filename,
                "mime_type": document.content_type,
                "checksum": checksum,
                "classification": classification.value,
                "classification_confidence": 1.0,
                "title": parsed_result["metadata"].get("title", ""),
                "author": parsed_result["metadata"].get("author", ""),
                "creation_date": parsed_result["metadata"].get("creation_date", ""),
                "modification_date": parsed_result["metadata"].get("modification_date", ""),
                "page_count": parsed_result["page_count"],
                "word_count": parsed_result["word_count"],
                "language": parsed_result["language"],
                "images_count": parsed_result.get("images_count", 0),
                "tables": parsed_result.get("tables", []),
            }
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(meta_data, f, ensure_ascii=False, indent=2)

            duration_ms = int((time.time() - start_time) * 1000)
            self.status.update_progress(status_record.id, "PARSED", 100, PipelineStatus.COMPLETED)
            self.status.mark_completed(status_record.id, duration_ms)
            self.db.commit()

            dispatcher.publish(Event(
                event_name="DocumentParsed",
                payload={
                    "document_id": str(document.id),
                    "startup_id": str(document.startup_id),
                    "filename": document.original_filename,
                    "checksum": checksum,
                    "classification": classification.value,
                }
            ))

            return meta_data

        except Exception as e:
            # 5. FAILED Stage
            document.processing_status = DocumentProcessingStatus.FAILED
            self.db.add(document)
            self.db.commit()

            err_msg = str(e)
            self.status.update_progress(status_record.id, "FAILED", 100, PipelineStatus.FAILED)
            self.status.mark_failed(status_record.id, err_msg)
            self.db.commit()

            dispatcher.publish(Event(
                event_name="DocumentFailed",
                payload={
                    "document_id": str(document.id),
                    "startup_id": str(document.startup_id),
                    "filename": document.original_filename,
                    "error": err_msg,
                }
            ))
            raise e

