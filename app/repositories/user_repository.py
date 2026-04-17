from uuid import UUID

from sqlalchemy import select, text
from sqlalchemy.orm import Session, joinedload

from app.models.user import User


class UserRepository:
    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        stmt = select(User).where(User.email == email).options(joinedload(User.roles))
        return db.execute(stmt).scalars().unique().one_or_none()

    @staticmethod
    def get_by_id(db: Session, user_id: UUID) -> User | None:
        stmt = select(User).where(User.id == user_id).options(joinedload(User.roles))
        return db.execute(stmt).scalars().unique().one_or_none()

    @staticmethod
    def list_users(db: Session) -> list[User]:
        stmt = select(User).options(joinedload(User.roles)).order_by(User.created_at.desc())
        return list(db.execute(stmt).scalars().unique().all())

    @staticmethod
    def get_roles_raw(db: Session, user_id: UUID) -> list[str]:
        # Raw SQL is justified here for a lightweight role lookup used in authorization checks.
        rows = db.execute(
            text(
                """
                SELECT r.name
                FROM user_roles ur
                JOIN roles r ON r.id = ur.role_id
                WHERE ur.user_id = :user_id
                """
            ),
            {"user_id": str(user_id)},
        ).fetchall()
        return [row[0] for row in rows]
