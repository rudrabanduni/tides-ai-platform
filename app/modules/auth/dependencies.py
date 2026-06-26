from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.enums import RoleName
from app.core.security import decode_access_token
from app.db.session import get_db
from app.modules.users.models import User
from app.modules.users.service import UserService

settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.api_v1_prefix}/auth/login", auto_error=False)


def _get_dev_user(db: Session) -> User:
    """Return the first active user in the database as the DEV_MODE actor."""
    users = UserService(db).list_users(limit=1)
    if users:
        return users[0]
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="DEV_MODE is enabled but no users have been bootstrapped. Run POST /auth/bootstrap-admin first.",
    )


from app.security.auth import get_current_user



def require_roles(*allowed_roles: RoleName) -> Callable:
    allowed = {role.value for role in allowed_roles}

    def dependency(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        # DEV_MODE: skip role enforcement
        if settings.dev_mode:
            return current_user
        if current_user.role.name not in allowed:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return dependency


AnyAuthenticatedUser = Annotated[User, Depends(get_current_user)]
AdminUser = Annotated[User, Depends(require_roles(RoleName.ADMIN))]
EvaluatorUser = Annotated[User, Depends(require_roles(RoleName.ADMIN, RoleName.EVALUATOR))]
ReviewerUser = Annotated[
    User,
    Depends(require_roles(RoleName.ADMIN, RoleName.EVALUATOR, RoleName.COMMITTEE_MEMBER)),
]
ReadOnlyUser = Annotated[
    User,
    Depends(require_roles(RoleName.ADMIN, RoleName.EVALUATOR, RoleName.COMMITTEE_MEMBER, RoleName.VIEWER)),
]
