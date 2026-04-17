from sqlalchemy import select

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.incident import IncidentCategory
from app.models.user import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository


class UserService:
    @staticmethod
    def list_users() -> list[User]:
        with SessionLocal() as db:
            return UserRepository.list_users(db)


def seed_initial_data() -> None:
    with SessionLocal() as db:
        RoleRepository.create_defaults(db)

        # Seed baseline incident categories once.
        defaults = [
            ("CLOSURE", "Road Closure"),
            ("DELAY", "Delay"),
            ("ACCIDENT", "Accident"),
            ("WEATHER_HAZARD", "Weather Hazard"),
        ]
        for key, label in defaults:
            exists = db.execute(select(IncidentCategory).where(IncidentCategory.key == key)).scalar_one_or_none()
            if not exists:
                db.add(IncidentCategory(key=key, label=label))
        db.commit()

        if not settings.seed_admin_email or not settings.seed_admin_password:
            return

        existing = UserRepository.get_by_email(db, settings.seed_admin_email.lower())
        if existing:
            return

        roles = RoleRepository.get_by_names(db, ["admin", "moderator", "citizen"])
        admin = User(
            email=settings.seed_admin_email.lower(),
            password_hash=hash_password(settings.seed_admin_password),
            full_name=settings.seed_admin_full_name,
            is_active=True,
            is_verified=True,
        )
        admin.roles = roles
        db.add(admin)
        db.commit()
