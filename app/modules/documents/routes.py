from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.orm import Session

from app.core.enums import DocumentType
from app.db.session import get_db
from app.modules.auth.dependencies import EvaluatorUser, ReadOnlyUser
from app.modules.documents.models import Document, DocumentSource
from app.modules.documents.schemas import (
    DocumentParsedTextUpdate,
    DocumentRead,
    DocumentSourceCreate,
    DocumentSourceRead,
)
from app.modules.documents.service import DocumentService

router = APIRouter(tags=["Documents"])


@router.post("/startups/{startup_id}/documents", response_model=DocumentRead, status_code=status.HTTP_201_CREATED)
def upload_document(
    startup_id: UUID,
    current_user: EvaluatorUser,
    db: Annotated[Session, Depends(get_db)],
    document_type: DocumentType = Form(...),
    file: UploadFile = File(...),
):
    return DocumentService(db).upload(
        startup_id,
        file=file,
        document_type=document_type,
        actor_id=current_user.id,
    )


@router.get("/startups/{startup_id}/documents", response_model=list[DocumentRead])
def list_documents(
    startup_id: UUID,
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
) -> Sequence[Document]:
    return DocumentService(db).list_for_startup(startup_id)


@router.get("/documents/{document_id}", response_model=DocumentRead)
def get_document(document_id: UUID, current_user: ReadOnlyUser, db: Annotated[Session, Depends(get_db)]):
    return DocumentService(db).get_document(document_id)


@router.patch("/documents/{document_id}/parsed-text", response_model=DocumentRead)
def update_document_parsed_text(
    document_id: UUID,
    payload: DocumentParsedTextUpdate,
    current_user: EvaluatorUser,
    db: Annotated[Session, Depends(get_db)],
):
    return DocumentService(db).update_parsed_text(document_id, payload, actor_id=current_user.id)


@router.post(
    "/startups/{startup_id}/document-sources",
    response_model=DocumentSourceRead,
    status_code=status.HTTP_201_CREATED,
)
def create_document_source(
    startup_id: UUID,
    payload: DocumentSourceCreate,
    current_user: EvaluatorUser,
    db: Annotated[Session, Depends(get_db)],
):
    return DocumentService(db).create_source(startup_id, payload, actor_id=current_user.id)


@router.get("/startups/{startup_id}/document-sources", response_model=list[DocumentSourceRead])
def list_document_sources(
    startup_id: UUID,
    current_user: ReadOnlyUser,
    db: Annotated[Session, Depends(get_db)],
) -> Sequence[DocumentSource]:
    return DocumentService(db).list_sources_for_startup(startup_id)
