from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.orm import Session

from app.core.enums import RoleName
from app.core.exceptions import ConflictError, NotFoundError
from app.core.security import hash_password, verify_password
from app.modules.audit.service import AuditService
from app.modules.users.models import Role, User
from app.modules.users.repository import RoleRepository, UserRepository
from app.modules.users.schemas import UserCreate, UserUpdate


DEFAULT_ROLE_DESCRIPTIONS: dict[RoleName, str] = {
    RoleName.ADMIN: "Full platform administration access.",
    RoleName.EVALUATOR: "Can evaluate startups and manage scoring workflows.",
    RoleName.COMMITTEE_MEMBER: "Can review committee materials, notes, and overrides.",
    RoleName.VIEWER: "Read-only access to platform records.",
}


class UserService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.roles = RoleRepository(db)
        self.users = UserRepository(db)
        self.audit = AuditService(db)

    def ensure_default_roles(self) -> None:
        for role_name, description in DEFAULT_ROLE_DESCRIPTIONS.items():
            if not self.roles.get_by_name(role_name.value):
                self.roles.add(Role(name=role_name.value, description=description))

    def authenticate(self, email: str, password: str) -> User | None:
        user = self.users.get_by_email(email)
        if not user or not user.is_active:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    def bootstrap_admin(self, *, name: str, email: str, password: str) -> User:
        if self.users.count() > 0:
            raise ConflictError("Bootstrap is only available before the first user exists")
        self.ensure_default_roles()
        admin_role = self.roles.get_by_name(RoleName.ADMIN.value)
        if not admin_role:
            raise NotFoundError("Admin role was not initialized")
        user = User(
            name=name,
            email=email.lower(),
            password_hash=hash_password(password),
            role_id=admin_role.id,
            is_active=True,
        )
        self.users.add(user)
        self.audit.log(
            actor_id=None,
            entity_type="user",
            entity_id=user.id,
            action="bootstrap_admin_created",
        )
        self.db.commit()
        loaded = self.users.get(user.id)
        if not loaded:
            raise NotFoundError("Created admin user could not be loaded")
        return loaded

    def create_user(self, payload: UserCreate, *, actor_id: UUID | None) -> User:
        self.ensure_default_roles()
        if self.users.get_by_email(payload.email):
            raise ConflictError("A user with this email already exists")
        role = self.roles.get_by_name(payload.role.value)
        if not role:
            raise NotFoundError("Role not found")
        user = User(
            name=payload.name,
            email=str(payload.email).lower(),
            password_hash=hash_password(payload.password),
            role_id=role.id,
            is_active=payload.is_active,
        )
        self.users.add(user)
        self.audit.log(
            actor_id=actor_id,
            entity_type="user",
            entity_id=user.id,
            action="user_created",
            details={"role": payload.role.value},
        )
        self.db.commit()
        loaded = self.users.get(user.id)
        if not loaded:
            raise NotFoundError("Created user could not be loaded")
        return loaded

    def get_user(self, user_id: UUID) -> User:
        user = self.users.get(user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    def list_users(self, *, skip: int = 0, limit: int = 100) -> Sequence[User]:
        return self.users.list(skip=skip, limit=limit)

    def update_user(self, user_id: UUID, payload: UserUpdate, *, actor_id: UUID | None) -> User:
        user = self.get_user(user_id)
        data = payload.model_dump(exclude_unset=True)
        if "role" in data and data["role"] is not None:
            role = self.roles.get_by_name(data.pop("role").value)
            if not role:
                raise NotFoundError("Role not found")
            user.role_id = role.id
        for field, value in data.items():
            setattr(user, field, value)
        self.audit.log(
            actor_id=actor_id,
            entity_type="user",
            entity_id=user.id,
            action="user_updated",
            details=data,
        )
        self.db.commit()
        loaded = self.users.get(user.id)
        if not loaded:
            raise NotFoundError("Updated user could not be loaded")
        return loaded
