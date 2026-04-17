from fastapi import APIRouter, Depends, status

from app.dependencies.auth import get_current_active_user
from app.schemas.auth import LoginRequest, RefreshRequest, TokenResponse, UserRegisterRequest
from app.schemas.common import ApiResponse
from app.schemas.user import UserRead
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/register", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[UserRead])
def register(payload: UserRegisterRequest) -> ApiResponse[UserRead]:
    user = AuthService.register(payload)
    return ApiResponse(data=UserRead.model_validate(user, from_attributes=True))


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(payload: LoginRequest) -> ApiResponse[TokenResponse]:
    tokens = AuthService.login(payload)
    return ApiResponse(data=tokens)


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
def refresh(payload: RefreshRequest) -> ApiResponse[TokenResponse]:
    tokens = AuthService.refresh(payload.refresh_token)
    return ApiResponse(data=tokens)


@router.post("/logout", response_model=ApiResponse[dict])
def logout(payload: RefreshRequest, current_user=Depends(get_current_active_user)) -> ApiResponse[dict]:
    AuthService.logout(payload.refresh_token, expected_user_id=current_user.id)
    return ApiResponse(data={"revoked": True})


@router.get("/me", response_model=ApiResponse[UserRead])
def me(current_user=Depends(get_current_active_user)) -> ApiResponse[UserRead]:
    return ApiResponse(data=UserRead.model_validate(current_user, from_attributes=True))
