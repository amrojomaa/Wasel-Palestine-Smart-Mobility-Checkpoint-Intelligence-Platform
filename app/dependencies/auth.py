from typing import Callable

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.exceptions import ForbiddenException, UnauthorizedException
from app.core.security import decode_token
from app.db.session import SessionLocal
from app.repositories.user_repository import UserRepository

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_active_user(credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme)):
    if credentials is None:
        raise UnauthorizedException(message="Missing bearer token")

    token = credentials.credentials
    payload = decode_token(token, expected_type="access")
    user_id = payload["sub"]

    with SessionLocal() as db:
        user = UserRepository.get_by_id(db, user_id)
        if not user:
            raise UnauthorizedException(message="User not found")
        if not user.is_active:
            raise UnauthorizedException(message="User is inactive")

        role_names = UserRepository.get_roles_raw(db, user.id)
        setattr(user, "role_names", role_names)
        return user


def require_roles(*required_roles: str) -> Callable:
    def checker(current_user=Depends(get_current_active_user)):
        user_roles = set(getattr(current_user, "role_names", []))
        if not user_roles.intersection(set(required_roles)):
            raise ForbiddenException(message="Insufficient permissions")
        return None

    return checker
