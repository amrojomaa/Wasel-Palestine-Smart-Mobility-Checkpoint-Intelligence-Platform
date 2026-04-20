from typing import Literal

from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import get_current_active_user, require_roles
from app.schemas.checkpoint import (
    CheckpointCreate,
    CheckpointRead,
    CheckpointStatusCreate,
    CheckpointStatusRead,
    CheckpointUpdate,
)
from app.schemas.common import ApiResponse
from app.services.checkpoint_service import CheckpointService

router = APIRouter()


@router.get("/", response_model=ApiResponse[list[CheckpointRead]])
def list_checkpoints(
    active_only: bool = Query(default=False),
    governorate: str | None = Query(default=None, max_length=80),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=500, ge=1, le=1000),
    order: Literal["asc", "desc"] = Query(default="desc"),
    _: object = Depends(get_current_active_user),
) -> ApiResponse[list[CheckpointRead]]:
    rows = CheckpointService.list_checkpoints(
        active_only=active_only,
        governorate=governorate,
        page=page,
        page_size=page_size,
        order=order,
    )
    return ApiResponse(data=[CheckpointRead.model_validate(r, from_attributes=True) for r in rows])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[CheckpointRead])
def create_checkpoint(
    payload: CheckpointCreate,
    _: None = Depends(require_roles("moderator", "admin")),
) -> ApiResponse[CheckpointRead]:
    row = CheckpointService.create_checkpoint(payload)
    return ApiResponse(data=CheckpointRead.model_validate(row, from_attributes=True))


@router.get("/{checkpoint_id}", response_model=ApiResponse[CheckpointRead])
def get_checkpoint(checkpoint_id: int, _: object = Depends(get_current_active_user)) -> ApiResponse[CheckpointRead]:
    row = CheckpointService.get_checkpoint(checkpoint_id)
    return ApiResponse(data=CheckpointRead.model_validate(row, from_attributes=True))


@router.patch("/{checkpoint_id}", response_model=ApiResponse[CheckpointRead])
def update_checkpoint(
    checkpoint_id: int,
    payload: CheckpointUpdate,
    _: None = Depends(require_roles("moderator", "admin")),
) -> ApiResponse[CheckpointRead]:
    row = CheckpointService.update_checkpoint(checkpoint_id, payload)
    return ApiResponse(data=CheckpointRead.model_validate(row, from_attributes=True))


@router.get("/{checkpoint_id}/status-history", response_model=ApiResponse[list[CheckpointStatusRead]])
def list_status_history(checkpoint_id: int, _: object = Depends(get_current_active_user)) -> ApiResponse[list[CheckpointStatusRead]]:
    rows = CheckpointService.list_status_history(checkpoint_id)
    return ApiResponse(data=[CheckpointStatusRead.model_validate(r, from_attributes=True) for r in rows])


@router.post("/{checkpoint_id}/status-history", response_model=ApiResponse[CheckpointStatusRead])
def add_status(
    checkpoint_id: int,
    payload: CheckpointStatusCreate,
    current_user=Depends(get_current_active_user),
    _: None = Depends(require_roles("moderator", "admin")),
) -> ApiResponse[CheckpointStatusRead]:
    row = CheckpointService.add_status(checkpoint_id, payload, str(current_user.id))
    return ApiResponse(data=CheckpointStatusRead.model_validate(row, from_attributes=True))
