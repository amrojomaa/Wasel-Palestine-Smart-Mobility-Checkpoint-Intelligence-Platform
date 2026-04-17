from fastapi import APIRouter, Depends

from app.dependencies.auth import get_current_active_user, require_roles
from app.schemas.common import ApiResponse
from app.schemas.user import UserRead
from app.services.user_service import UserService

router = APIRouter()


@router.get("/", response_model=ApiResponse[list[UserRead]])
def list_users(
    _: None = Depends(require_roles("admin")),
    current_user=Depends(get_current_active_user),
) -> ApiResponse[list[UserRead]]:
    users = UserService.list_users()
    return ApiResponse(data=[UserRead.model_validate(u) for u in users])
