from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.modules.users.models import Role, User
from app.repositories.base import BaseRepository


class RoleRepository(BaseRepository[Role]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Role)

    def get_by_name(self, name: str) -> Role | None:
        return self.db.scalar(select(Role).where(Role.name == name))


class UserRepository(BaseRepository[User]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, User)

    def get(self, entity_id: UUID) -> User | None:
        return self.db.scalar(select(User).options(joinedload(User.role)).where(User.id == entity_id))

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).options(joinedload(User.role)).where(User.email == email.lower()))

    def list(self, *, skip: int = 0, limit: int = 100) -> Sequence[User]:
        statement = select(User).options(joinedload(User.role)).offset(skip).limit(limit)
        return self.db.scalars(statement).all()

    def count(self) -> int:
        return len(self.db.scalars(select(User.id)).all())
