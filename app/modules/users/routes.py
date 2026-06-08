from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.modules.auth.dependencies import AdminUser
from app.modules.users.models import User
from app.modules.users.schemas import UserCreate, UserRead, UserUpdate
from app.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreate, current_user: AdminUser, db: Annotated[Session, Depends(get_db)]):
    return UserService(db).create_user(payload, actor_id=current_user.id)


@router.get("", response_model=list[UserRead])
def list_users(
    current_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> Sequence[User]:
    return UserService(db).list_users(skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserRead)
def get_user(user_id: UUID, current_user: AdminUser, db: Annotated[Session, Depends(get_db)]):
    return UserService(db).get_user(user_id)


@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    user_id: UUID,
    payload: UserUpdate,
    current_user: AdminUser,
    db: Annotated[Session, Depends(get_db)],
):
    return UserService(db).update_user(user_id, payload, actor_id=current_user.id)
