from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    @staticmethod
    def add(db: Session, token: RefreshToken) -> RefreshToken:
        db.add(token)
        db.commit()
        db.refresh(token)
        return token

    @staticmethod
    def get_by_hash(db: Session, token_hash: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def revoke(db: Session, token: RefreshToken) -> None:
        token.revoked_at = datetime.now(timezone.utc)
        db.add(token)
        db.commit()
