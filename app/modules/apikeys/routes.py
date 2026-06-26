from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import AdminUser
from app.security.api_keys import api_key_store
from app.security.schemas import APIKeyCreate, APIKeyResponse, APIKeyRead
from app.security.audit import security_audit_service

router = APIRouter(prefix="/apikeys", tags=["API Keys"])


@router.post("", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
def create_api_key(
    payload: APIKeyCreate,
    current_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    key_resp = api_key_store.create(payload)
    security_audit_service.api_key_created(str(current_user.id), key_resp.name)
    return key_resp


@router.get("", response_model=list[APIKeyRead])
def list_api_keys(
    current_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    return api_key_store.list_all()


@router.delete("/{key_id}")
def delete_api_key(
    key_id: str,
    current_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    success = api_key_store.delete(key_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API Key not found",
        )
    security_audit_service.api_key_revoked(str(current_user.id), key_id)
    return {"success": True, "message": "API Key deleted successfully"}
