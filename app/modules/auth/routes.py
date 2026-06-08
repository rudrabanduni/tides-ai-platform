from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.db.session import get_db
from app.modules.auth.dependencies import AnyAuthenticatedUser
from app.modules.auth.schemas import BootstrapAdminRequest, LoginRequest, TokenResponse
from app.modules.users.schemas import UserRead
from app.modules.users.service import UserService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/bootstrap-admin", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def bootstrap_admin(payload: BootstrapAdminRequest, db: Annotated[Session, Depends(get_db)]):
    return UserService(db).bootstrap_admin(
        name=payload.name,
        email=str(payload.email),
        password=payload.password,
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    user = UserService(db).authenticate(str(payload.email), payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    return TokenResponse(access_token=create_access_token(str(user.id)), user=user)


@router.get("/me", response_model=UserRead)
def me(current_user: AnyAuthenticatedUser):
    return current_user
