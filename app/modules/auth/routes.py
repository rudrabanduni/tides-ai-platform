from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import AnyAuthenticatedUser
from app.modules.auth.schemas import BootstrapAdminRequest, LoginRequest, TokenResponse, RefreshRequest
from app.modules.users.schemas import UserRead
from app.modules.users.service import UserService
from app.security.jwt import jwt_service
from app.security.audit import security_audit_service

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/bootstrap-admin", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def bootstrap_admin(payload: BootstrapAdminRequest, db: Annotated[Session, Depends(get_db)]):
    return UserService(db).bootstrap_admin(
        name=payload.name,
        email=str(payload.email),
        password=payload.password,
    )


@router.post("/login", response_model=TokenResponse)
def login(request: Request, payload: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    ip = request.client.host if request.client else "unknown"
    user = UserService(db).authenticate(str(payload.email), payload.password)
    if not user:
        security_audit_service.login_failure(str(payload.email), ip, "Invalid credentials")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    
    access_token = jwt_service.create_access_token(str(user.id), user.role.name)
    refresh_token = jwt_service.create_refresh_token(str(user.id), user.role.name)
    
    security_audit_service.login_success(str(user.id), ip)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserRead.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh(request: Request, payload: RefreshRequest, db: Annotated[Session, Depends(get_db)]):
    ip = request.client.host if request.client else "unknown"
    claims = jwt_service.decode_token(payload.refresh_token)
    if not claims:
        security_audit_service.token_invalid(ip, "Invalid or expired refresh token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    try:
        user_id = UUID(claims.subject)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token subject")
        
    user = UserService(db).get_user(user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User is inactive or not found")
        
    # Revoke the old refresh token
    jwt_service.revoke_token(claims.jti)
    
    # Generate new pair
    access_token = jwt_service.create_access_token(str(user.id), user.role.name)
    new_refresh_token = jwt_service.create_refresh_token(str(user.id), user.role.name)
    
    security_audit_service.token_refresh(str(user.id), ip)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        user=UserRead.model_validate(user),
    )


@router.post("/logout")
def logout(request: Request, db: Annotated[Session, Depends(get_db)]):
    ip = request.client.host if request.client else "unknown"
    
    # Try to extract the Bearer token
    auth_header = request.headers.get("Authorization")
    jti = None
    user_id = "anonymous"
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header[7:]
        claims = jwt_service.decode_token(token)
        if claims:
            jti = claims.jti
            user_id = claims.subject
            jwt_service.revoke_token(jti)
            
    security_audit_service.logout(user_id, ip)
    return {"success": True, "message": "Logged out successfully"}


@router.get("/me", response_model=UserRead)
def me(current_user: AnyAuthenticatedUser):
    return current_user
