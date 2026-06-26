import os
import pytest
from uuid import uuid4
from sqlalchemy.orm import Session
from pydantic import ValidationError

from app.db.base import Base
from app.modules.documents.models import Document
from app.core.enums import DocumentProcessingStatus, DocumentType
from app.modules.startups.models import StartupApplication
from app.modules.intelligence.ai.chunking import SemanticChunker
from app.modules.intelligence.ai.prompt_registry import prompt_registry
from app.modules.intelligence.ai.schemas import DocumentExtraction, ExtractedString, ExtractedInt, ExtractedFloat
from app.modules.intelligence.ai.extractor import AIExtractor, merge_extractions
from app.modules.intelligence.events import dispatcher, Event
from app.modules.intelligence.models import PipelineStatus
from app.services.ai.mock import MockAIGateway
from app.services.ai.exceptions import AIResponseParseError
from app.services.ai.schemas import AICompletionRequest


@pytest.fixture()
def db_session() -> Session:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    Base.metadata.create_all(engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_chunking() -> None:
    # 1. Text chunking by paragraphs
    text = "Paragraph 1 is here.\n\nParagraph 2 is right next.\n\nParagraph 3 is also present."
    chunks = SemanticChunker.chunk_document("doc-1", text, max_tokens=10)
    assert len(chunks) == 3
    assert chunks[0].text == "Paragraph 1 is here."
    assert chunks[0].page_start == 1
    assert chunks[0].page_end == 1
    assert chunks[0].word_count == 4

    # 2. Slide chunking
    slide_text = "Slide 1 Content--- Slide ---Slide 2 Content--- Slide ---Slide 3 Content"
    slide_chunks = SemanticChunker.chunk_document("doc-2", slide_text, max_tokens=5)
    assert len(slide_chunks) == 3
    assert slide_chunks[0].text == "Slide 1 Content"
    assert slide_chunks[0].page_start == 1
    assert slide_chunks[0].page_end == 1


def test_prompt_registry() -> None:
    # Verify templates lookup
    sys_deck, user_deck = prompt_registry.get_prompts("Pitch Deck", "Slide text")
    assert "PITCH DECK" in sys_deck
    assert "Slide text" in user_deck

    sys_financial, user_financial = prompt_registry.get_prompts("Financial Statement", "Revenue text")
    assert "FINANCIAL STATEMENT" in sys_financial

    sys_patent, _ = prompt_registry.get_prompts("Patent", "Patent text")
    assert "PATENT" in sys_patent

    # Fallback to default
    sys_default, _ = prompt_registry.get_prompts("Unknown Type", "Some text")
    assert "TIDES IIT Roorkee" in sys_default


def test_extractor_success(db_session: Session) -> None:
    # Setup startup
    startup = StartupApplication(startup_name="TIE AI Startup", stage="Prototype", current_status="Submitted")
    db_session.add(startup)
    db_session.flush()

    # Setup document record
    doc = Document(
        startup_id=startup.id,
        document_type=DocumentType.PITCH_DECK,
        original_filename="deck.pdf",
        stored_filename="deck.pdf",
        file_path="mock/path/deck.pdf",
        file_size=1000,
        parsed_text="Founder Name: John Doe. Pitch Deck problem statement solution. Technology details TRL 5.",
        processing_status=DocumentProcessingStatus.PARSED
    )
    db_session.add(doc)
    db_session.flush()

    # Pre-configure mock AI response matching Pydantic schema
    fixed_extraction = DocumentExtraction()
    fixed_extraction.founder.founder_names = ExtractedString(
        value="John Doe", confidence_score=0.9, confidence_reason="Explicitly stated",
        why_extracted="Key personnel identified", supporting_evidence="John Doe", document_section="Introduction"
    )
    fixed_extraction.technology.trl_level = ExtractedInt(
        value=5, confidence_score=0.85, confidence_reason="Clearly stated",
        why_extracted="TRL assessment", supporting_evidence="TRL 5", document_section="Technology"
    )

    mock_gateway = MockAIGateway(fixed_response=fixed_extraction)
    extractor = AIExtractor(db_session, mock_gateway)

    # Event tracking
    events = []
    def tracker(event: Event) -> None:
        events.append(event)

    dispatcher.register("ExtractionStarted", tracker)
    dispatcher.register("ChunkProcessed", tracker)
    dispatcher.register("ExtractionCompleted", tracker)

    res = extractor.extract_document(doc.id)

    # Asserts
    assert res.founder.founder_names.value == "John Doe"
    assert res.technology.trl_level.value == 5
    assert res.metadata.document_id == str(doc.id)
    assert res.metadata.startup_id == str(doc.startup_id)

    # Check status
    status_record = extractor.status.get_by_startup_pipeline(startup.id, "ai_extraction")
    assert status_record is not None
    assert status_record.status == PipelineStatus.COMPLETED
    assert status_record.current_stage == "READY_FOR_CLAIMS"

    # Check events
    event_names = [e.event_name for e in events]
    assert "ExtractionStarted" in event_names
    assert "ChunkProcessed" in event_names
    assert "ExtractionCompleted" in event_names


def test_extractor_unsupported_trl(db_session: Session) -> None:
    startup = StartupApplication(startup_name="TIE TRL Startup", stage="Prototype", current_status="Submitted")
    db_session.add(startup)
    db_session.flush()

    doc = Document(
        startup_id=startup.id,
        document_type=DocumentType.OTHER,
        original_filename="patent.pdf",
        stored_filename="patent.pdf",
        file_path="mock/path/patent.pdf",
        file_size=1000,
        parsed_text="TRL 10 invalid level.",
        processing_status=DocumentProcessingStatus.PARSED
    )
    db_session.add(doc)
    db_session.flush()

    # Mock invalid TRL level (TRL 10 is outside 1-9)
    fixed_extraction = DocumentExtraction()
    fixed_extraction.technology.trl_level = ExtractedInt(value=10, confidence_score=0.9)

    mock_gateway = MockAIGateway(fixed_response=fixed_extraction)
    extractor = AIExtractor(db_session, mock_gateway)

    # Expect validation failure during validates stage
    with pytest.raises(AIResponseParseError):
        extractor.extract_document(doc.id)

    status_record = extractor.status.get_by_startup_pipeline(startup.id, "ai_extraction")
    assert status_record.status == PipelineStatus.FAILED
    assert status_record.current_stage == "FAILED"


def test_extractor_empty_document(db_session: Session) -> None:
    startup = StartupApplication(startup_name="TIE Empty Startup", stage="Prototype", current_status="Submitted")
    db_session.add(startup)
    db_session.flush()

    doc = Document(
        startup_id=startup.id,
        document_type=DocumentType.OTHER,
        original_filename="empty.pdf",
        stored_filename="empty.pdf",
        file_path="mock/path/empty.pdf",
        file_size=0,
        parsed_text="",  # Empty text
        processing_status=DocumentProcessingStatus.PARSED
    )
    db_session.add(doc)
    db_session.flush()

    extractor = AIExtractor(db_session, MockAIGateway())

    # Expect ValueError for empty content
    with pytest.raises(ValueError, match="Parsed document text is empty"):
        extractor.extract_document(doc.id)


def test_extractor_large_document_merge(db_session: Session) -> None:
    startup = StartupApplication(startup_name="TIE Merge Startup", stage="Prototype", current_status="Submitted")
    db_session.add(startup)
    db_session.flush()

    # Set up text that will split into two chunks (divided by \n\n and exceeding max_tokens = 1500)
    doc = Document(
        startup_id=startup.id,
        document_type=DocumentType.PITCH_DECK,
        original_filename="large.pdf",
        stored_filename="large.pdf",
        file_path="mock/path/large.pdf",
        file_size=2000,
        parsed_text="Founder is John.\n\n" + "word " * 1200 + "\n\nFounder is Jack.",
        processing_status=DocumentProcessingStatus.PARSED
    )
    db_session.add(doc)
    db_session.flush()

    # We will mock a response factory that returns different extractions for each chunk
    chunk_index = 0
    def response_factory(request: AICompletionRequest) -> dict:
        nonlocal chunk_index
        extraction = DocumentExtraction()
        if chunk_index == 0:
            extraction.founder.founder_names = ExtractedString(value="John", confidence_score=0.7)
            extraction.founder.leadership_experience = ExtractedString(value="5 Years", confidence_score=0.9)
        else:
            # Chunk 2 has different founder name and higher confidence, and lower confidence leadership
            extraction.founder.founder_names = ExtractedString(value="Jack", confidence_score=0.9)
            extraction.founder.leadership_experience = ExtractedString(value="10 Years", confidence_score=0.5)
        chunk_index += 1
        return extraction.model_dump()

    mock_gateway = MockAIGateway(response_factory=response_factory)
    extractor = AIExtractor(db_session, mock_gateway)

    res = extractor.extract_document(doc.id)

    # Asserts that merging picked the highest confidence fields correctly:
    # Jack (0.9) preferred over John (0.7)
    assert res.founder.founder_names.value == "Jack"
    # 5 Years (0.9) preferred over 10 Years (0.5)
    assert res.founder.leadership_experience.value == "5 Years"

