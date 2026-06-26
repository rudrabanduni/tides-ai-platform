import time
from datetime import datetime
from uuid import UUID
from typing import Any
from sqlalchemy.orm import Session

from app.core.enums import DocumentProcessingStatus, DocumentType
from app.modules.documents.repository import DocumentRepository
from app.modules.intelligence.ai.chunking import SemanticChunker, Chunk
from app.modules.intelligence.ai.prompt_registry import prompt_registry
from app.modules.intelligence.ai.schemas import DocumentExtraction, ExtractedField, RiskInfo, FounderInfo
from app.modules.intelligence.events import dispatcher, Event
from app.modules.intelligence.models import PipelineStatus
from app.modules.intelligence.repository import StartupProcessingStatusRepository
from app.services.ai.gateway import AIGateway, create_ai_gateway
from app.services.ai.schemas import AICompletionRequest


def merge_extracted_field(a: Any, b: Any) -> Any:
    """Merge two ExtractedField objects based on confidence score."""
    if a.value is None:
        return b
    if b.value is None:
        return a

    # Both have values, return the one with higher confidence score
    if b.confidence_score > a.confidence_score:
        return b
    return a


def merge_risk_info(a: RiskInfo, b: RiskInfo) -> RiskInfo:
    """Combine major risk lists, de-duplicating by lowercase value."""
    merged_risks = list(a.major_risks)
    existing_values = {r.value.lower() for r in merged_risks if r.value}
    for risk in b.major_risks:
        if risk.value and risk.value.lower() not in existing_values:
            merged_risks.append(risk)
            existing_values.add(risk.value.lower())
    return RiskInfo(major_risks=merged_risks)


def merge_extractions(extractions: list[DocumentExtraction]) -> DocumentExtraction:
    """Merge extractions from multiple chunks, selecting the highest confidence fields."""
    if not extractions:
        return DocumentExtraction()
    if len(extractions) == 1:
        return extractions[0]

    merged = DocumentExtraction()

    # Merge Founder
    for ext in extractions:
        merged.founder.founder_names = merge_extracted_field(merged.founder.founder_names, ext.founder.founder_names)
        merged.founder.leadership_experience = merge_extracted_field(merged.founder.leadership_experience, ext.founder.leadership_experience)
        merged.founder.domain_expertise = merge_extracted_field(merged.founder.domain_expertise, ext.founder.domain_expertise)
        merged.founder.commitment_level = merge_extracted_field(merged.founder.commitment_level, ext.founder.commitment_level)

    # Merge Product
    for ext in extractions:
        merged.product.description = merge_extracted_field(merged.product.description, ext.product.description)
        merged.product.problem_solved = merge_extracted_field(merged.product.problem_solved, ext.product.problem_solved)
        merged.product.solution_value_prop = merge_extracted_field(merged.product.solution_value_prop, ext.product.solution_value_prop)
        merged.product.customers = merge_extracted_field(merged.product.customers, ext.product.customers)
        merged.product.business_model = merge_extracted_field(merged.product.business_model, ext.product.business_model)

    # Merge Market
    for ext in extractions:
        merged.market.target_market = merge_extracted_field(merged.market.target_market, ext.market.target_market)
        merged.market.market_size = merge_extracted_field(merged.market.market_size, ext.market.market_size)
        merged.market.competitors = merge_extracted_field(merged.market.competitors, ext.market.competitors)
        merged.market.competition_analysis = merge_extracted_field(merged.market.competition_analysis, ext.market.competition_analysis)

    # Merge Financial
    for ext in extractions:
        merged.financial.revenue_model = merge_extracted_field(merged.financial.revenue_model, ext.financial.revenue_model)
        merged.financial.funding_received = merge_extracted_field(merged.financial.funding_received, ext.financial.funding_received)
        merged.financial.current_revenue = merge_extracted_field(merged.financial.current_revenue, ext.financial.current_revenue)
        merged.financial.financial_metrics = merge_extracted_field(merged.financial.financial_metrics, ext.financial.financial_metrics)

    # Merge Technology
    for ext in extractions:
        merged.technology.description = merge_extracted_field(merged.technology.description, ext.technology.description)
        merged.technology.trl_level = merge_extracted_field(merged.technology.trl_level, ext.technology.trl_level)
        merged.technology.ip_status = merge_extracted_field(merged.technology.ip_status, ext.technology.ip_status)

    # Merge Risk
    for ext in extractions:
        merged.risk = merge_risk_info(merged.risk, ext.risk)

    # Merge Metadata
    first_ext = extractions[0]
    merged.metadata.document_id = first_ext.metadata.document_id
    merged.metadata.startup_id = first_ext.metadata.startup_id
    merged.metadata.extraction_timestamp = first_ext.metadata.extraction_timestamp or datetime.utcnow().isoformat()

    return merged


class AIExtractor:
    """Coordinates semantic chunking, prompt resolution, gateway calls, and schema validation."""

    def __init__(self, db: Session, gateway: AIGateway | None = None) -> None:
        self.db = db
        self.gateway = gateway or create_ai_gateway()
        self.status = StartupProcessingStatusRepository(db)

    def extract_document(self, document_id: UUID) -> DocumentExtraction:
        doc_repo = DocumentRepository(self.db)
        document = doc_repo.get(document_id)
        if not document:
            raise ValueError(f"Document with ID {document_id} not found")

        # Map document_type to PromptRegistry keys
        doc_type_key = "Generic Document"
        if document.document_type == DocumentType.PITCH_DECK:
            doc_type_key = "Pitch Deck"
        elif document.document_type == DocumentType.BUSINESS_PLAN:
            doc_type_key = "Business Plan"
        elif document.document_type == DocumentType.APPLICATION_FORM:
            doc_type_key = "Excel Intake"
        elif document.document_type == DocumentType.COMPANY_DOCUMENT:
            doc_type_key = "Generic Document"

        # Initialize or retrieve status
        status_record = self.status.get_by_startup_pipeline(document.startup_id, "ai_extraction")
        if not status_record:
            status_record = self.status.create_status(
                startup_id=document.startup_id,
                pipeline_name="ai_extraction",
                stage="CHUNKING"
            )
        else:
            self.status.update_progress(status_record.id, "CHUNKING", 0, PipelineStatus.RUNNING)
            self.db.refresh(status_record)

        start_time = time.time()

        try:
            # 1. CHUNKING Stage
            self.status.update_progress(status_record.id, "CHUNKING", 10, PipelineStatus.RUNNING)
            if not document.parsed_text or not document.parsed_text.strip():
                raise ValueError("Parsed document text is empty; extraction aborted")

            chunks = SemanticChunker.chunk_document(str(document.id), document.parsed_text)
            if not chunks:
                raise ValueError("No semantic chunks produced from document text")

            dispatcher.publish(Event(
                event_name="ExtractionStarted",
                payload={
                    "document_id": str(document.id),
                    "startup_id": str(document.startup_id),
                    "total_chunks": len(chunks),
                }
            ))

            # 2. AI_EXTRACTION Stage
            extractions = []
            for i, chunk in enumerate(chunks):
                progress = 20 + int(60 * (i / len(chunks)))
                self.status.update_progress(status_record.id, "AI_EXTRACTION", progress, PipelineStatus.RUNNING)

                system_prompt, user_prompt = prompt_registry.get_prompts(doc_type_key, chunk.text)
                request = AICompletionRequest(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                    prompt_version="1.0"
                )

                # Execute Gateway completion call
                res = self.gateway.complete_json(request, response_model=DocumentExtraction)
                
                # Fill in metadata for this chunk
                res.data.metadata.document_id = str(document.id)
                res.data.metadata.startup_id = str(document.startup_id)
                res.data.metadata.extraction_timestamp = datetime.utcnow().isoformat()
                
                extractions.append(res.data)

                dispatcher.publish(Event(
                    event_name="ChunkProcessed",
                    payload={
                        "document_id": str(document.id),
                        "chunk_id": chunk.chunk_id,
                        "index": i + 1,
                        "total": len(chunks),
                    }
                ))

            # Merge extractions from all chunks
            merged_extraction = merge_extractions(extractions)

            # 3. VALIDATING Stage
            self.status.update_progress(status_record.id, "VALIDATING", 90, PipelineStatus.RUNNING)
            
            # Pydantic validation has run, verify custom business validation rules
            # TRL levels and confidence fields validation
            if merged_extraction.technology.trl_level.value is not None:
                trl = merged_extraction.technology.trl_level.value
                if not (1 <= trl <= 9):
                    raise ValueError(f"Extracted invalid TRL level: {trl}")

            # 4. READY_FOR_CLAIMS Stage
            duration_ms = int((time.time() - start_time) * 1000)
            self.status.update_progress(status_record.id, "READY_FOR_CLAIMS", 100, PipelineStatus.COMPLETED)
            self.status.mark_completed(status_record.id, duration_ms)
            self.db.commit()

            dispatcher.publish(Event(
                event_name="ExtractionCompleted",
                payload={
                    "document_id": str(document.id),
                    "startup_id": str(document.startup_id),
                }
            ))

            return merged_extraction

        except Exception as e:
            # 5. FAILED Stage
            self.status.update_progress(status_record.id, "FAILED", 100, PipelineStatus.FAILED)
            self.status.mark_failed(status_record.id, str(e))
            self.db.commit()

            dispatcher.publish(Event(
                event_name="ExtractionFailed",
                payload={
                    "document_id": str(document.id),
                    "error": str(e),
                }
            ))
            raise e
