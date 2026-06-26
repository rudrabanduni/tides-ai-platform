from fastapi import APIRouter, Depends, Request, UploadFile, File, Form, status, Path
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.db.session import get_db
from app.modules.documents.models import Document
from app.modules.documents.service import DocumentService
from app.modules.intelligence.service import IntelligenceService
from app.core.enums import DocumentType
from app.api.responses import make_response
from app.api.exceptions import DocumentNotFoundError, StartupNotFoundError
from app.modules.startups.models import StartupApplication

router = APIRouter(tags=["Documents"])

def map_to_document_type(doc_type_str: str) -> DocumentType:
    try:
        val = doc_type_str.upper().replace(" ", "_")
        for dt in DocumentType:
            if dt.value.upper() == val or dt.name == val:
                return dt
    except Exception:
        pass
    return DocumentType.OTHER

@router.post("/documents/upload", status_code=status.HTTP_201_CREATED)
def upload_document(
    request: Request,
    startup_id: UUID = Form(..., description="The startup application ID"),
    document_type: str = Form(default="Pitch Deck", description="Type of document"),
    file: UploadFile = File(..., description="File payload"),
    db: Session = Depends(get_db)
):
    # Verify startup exists
    startup = db.query(StartupApplication).filter(StartupApplication.id == startup_id).first()
    if not startup:
        raise StartupNotFoundError(str(startup_id))
        
    doc_type = map_to_document_type(document_type)
    
    # Save the file using standard DocumentService upload
    doc_service = DocumentService(db)
    document = doc_service.upload(
        startup_id=startup_id,
        file=file,
        document_type=doc_type,
        actor_id=None
    )
    
    # Run parsing pipeline to populate claims/evidence
    try:
        intel_service = IntelligenceService(db)
        intel_service.process_document(document.id)
    except Exception as e:
        # Log error but do not fail the upload itself
        import logging
        logger = logging.getLogger("tides_api")
        logger.warning(f"Failed to auto-parse document {document.id}: {e}")
        
    data = {
        "id": str(document.id),
        "startup_id": str(document.startup_id),
        "filename": document.original_filename,
        "document_type": document.document_type.value if hasattr(document.document_type, "value") else str(document.document_type),
        "file_size": document.file_size,
        "content_type": document.content_type,
        "processing_status": document.processing_status.value if hasattr(document.processing_status, "value") else str(document.processing_status),
        "uploaded_at": document.created_at.isoformat() + "Z" if hasattr(document, "created_at") and document.created_at else None
    }
    
    return make_response(request, data=data, message="Document uploaded and processing started successfully")

@router.get("/documents/{document_id}")
def get_document(request: Request, document_id: UUID = Path(...), db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise DocumentNotFoundError(str(document_id))
        
    data = {
        "id": str(document.id),
        "startup_id": str(document.startup_id),
        "filename": document.original_filename,
        "document_type": document.document_type.value if hasattr(document.document_type, "value") else str(document.document_type),
        "file_size": document.file_size,
        "content_type": document.content_type,
        "processing_status": document.processing_status.value if hasattr(document.processing_status, "value") else str(document.processing_status),
        "parsed_text": document.parsed_text,
        "uploaded_at": document.created_at.isoformat() + "Z" if hasattr(document, "created_at") and document.created_at else None
    }
    return make_response(request, data=data, message="Document retrieved successfully")

@router.delete("/documents/{document_id}")
def delete_document(request: Request, document_id: UUID = Path(...), db: Session = Depends(get_db)):
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise DocumentNotFoundError(str(document_id))
        
    db.delete(document)
    db.commit()
    return make_response(request, data={"id": str(document_id)}, message="Document deleted successfully")
