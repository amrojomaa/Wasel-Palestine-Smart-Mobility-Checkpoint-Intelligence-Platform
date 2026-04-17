from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.db.session import SessionLocal
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest, TokenResponse, UserRegisterRequest


class AuthService:
    @staticmethod
    def register(payload: UserRegisterRequest) -> User:
        with SessionLocal() as db:
            existing = UserRepository.get_by_email(db, payload.email.lower())
            if existing:
                raise ConflictException(message="Email is already registered")

            citizen_role = RoleRepository.get_by_name(db, "citizen")
            if not citizen_role:
                RoleRepository.create_defaults(db)
                citizen_role = RoleRepository.get_by_name(db, "citizen")

            user = User(
                email=payload.email.lower(),
                password_hash=hash_password(payload.password),
                full_name=payload.full_name,
                is_active=True,
                is_verified=False,
            )
            user.roles.append(citizen_role)
            db.add(user)
            db.commit()
            db.refresh(user)
            # Re-fetch with eager-loaded roles to avoid detached lazy-load issues in response serialization.
            return UserRepository.get_by_id(db, user.id)

    @staticmethod
    def login(payload: LoginRequest) -> TokenResponse:
        with SessionLocal() as db:
            user = UserRepository.get_by_email(db, payload.email.lower())
            if not user or not verify_password(payload.password, user.password_hash):
                raise UnauthorizedException(message="Invalid credentials")
            if not user.is_active:
                raise UnauthorizedException(message="Account is disabled")
            return AuthService._issue_tokens(db, user)

    @staticmethod
    def refresh(refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token, expected_type="refresh")
        user_id = payload["sub"]

        with SessionLocal() as db:
            token_hash = hash_token(refresh_token)
            token_record = RefreshTokenRepository.get_by_hash(db, token_hash)
            if not token_record:
                raise UnauthorizedException(message="Refresh token not found")
            if token_record.revoked_at:
                raise UnauthorizedException(message="Refresh token already revoked")
            if token_record.expires_at <= datetime.now(timezone.utc):
                raise UnauthorizedException(message="Refresh token expired")

            user = UserRepository.get_by_id(db, user_id)
            if not user or not user.is_active:
                raise UnauthorizedException(message="User is not active")

            RefreshTokenRepository.revoke(db, token_record)
            return AuthService._issue_tokens(db, user)

    @staticmethod
    def logout(refresh_token: str, expected_user_id) -> None:
        decode_token(refresh_token, expected_type="refresh")
        with SessionLocal() as db:
            token_record = RefreshTokenRepository.get_by_hash(db, hash_token(refresh_token))
            if not token_record:
                raise UnauthorizedException(message="Refresh token not found")
            if str(token_record.user_id) != str(expected_user_id):
                raise UnauthorizedException(message="Token does not belong to this user")
            if not token_record.revoked_at:
                RefreshTokenRepository.revoke(db, token_record)

    @staticmethod
    def _issue_tokens(db, user: User) -> TokenResponse:
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        now = datetime.now(timezone.utc)
        refresh_expires_at = now + timedelta(days=settings.refresh_token_expire_days)

        token_record = RefreshToken(
            user_id=user.id,
            token_hash=hash_token(refresh_token),
            issued_at=now,
            expires_at=refresh_expires_at,
        )
        RefreshTokenRepository.add(db, token_record)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        )
