from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.role import Role


class RoleRepository:
    @staticmethod
    def get_by_name(db: Session, name: str) -> Role | None:
        return db.execute(select(Role).where(Role.name == name)).scalar_one_or_none()

    @staticmethod
    def get_by_names(db: Session, names: list[str]) -> list[Role]:
        stmt = select(Role).where(Role.name.in_(names))
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def create_defaults(db: Session) -> None:
        for role_name in ("citizen", "moderator", "admin"):
            if not RoleRepository.get_by_name(db, role_name):
                db.add(Role(name=role_name, description=f"Default role: {role_name}"))
        db.commit()
