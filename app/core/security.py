import hashlib
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import UnauthorizedException

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def _create_token(subject: str, expires_delta: timedelta, token_type: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "type": token_type,
        "jti": str(uuid4()),
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(subject: str) -> str:
    expires = timedelta(minutes=settings.access_token_expire_minutes)
    return _create_token(subject=subject, expires_delta=expires, token_type="access")


def create_refresh_token(subject: str) -> str:
    expires = timedelta(days=settings.refresh_token_expire_days)
    return _create_token(subject=subject, expires_delta=expires, token_type="refresh")


def decode_token(token: str, expected_type: str | None = None) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:
        raise UnauthorizedException(message="Invalid token") from exc

    if expected_type and payload.get("type") != expected_type:
        raise UnauthorizedException(message="Invalid token type")

    if not payload.get("sub"):
        raise UnauthorizedException(message="Token subject is missing")
    return payload


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
