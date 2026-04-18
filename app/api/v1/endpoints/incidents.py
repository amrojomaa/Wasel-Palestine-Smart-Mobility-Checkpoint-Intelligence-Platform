from typing import Literal

from fastapi import APIRouter, Depends, Query, Request, status

from app.dependencies.auth import get_current_active_user, require_roles
from app.schemas.common import ApiResponse
from app.schemas.incident import (
    IncidentCreate,
    IncidentRead,
    IncidentUpdate,
    IncidentVerificationRead,
    IncidentVerifyRequest,
)
from app.services.incident_service import IncidentService

router = APIRouter()


@router.get("/", response_model=ApiResponse[list[IncidentRead]])
def list_incidents(
    status_filter: str | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    sort_by: Literal["created_at", "reported_at", "severity", "status"] = Query(default="created_at"),
    order: Literal["asc", "desc"] = Query(default="desc"),
    _: object = Depends(get_current_active_user),
) -> ApiResponse[list[IncidentRead]]:
    rows = IncidentService.list_incidents(
        status=status_filter,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        order=order,
    )
    return ApiResponse(data=[IncidentRead.model_validate(r, from_attributes=True) for r in rows])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[IncidentRead])
def create_incident(
    payload: IncidentCreate,
    request: Request,
    current_user=Depends(get_current_active_user),
    _: None = Depends(require_roles("moderator", "admin")),
) -> ApiResponse[IncidentRead]:
    row = IncidentService.create_incident(
        payload,
        current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return ApiResponse(data=IncidentRead.model_validate(row, from_attributes=True))


@router.get("/{incident_id}", response_model=ApiResponse[IncidentRead])
def get_incident(incident_id: int, _: object = Depends(get_current_active_user)) -> ApiResponse[IncidentRead]:
    row = IncidentService.get_incident(incident_id)
    return ApiResponse(data=IncidentRead.model_validate(row, from_attributes=True))


@router.patch("/{incident_id}", response_model=ApiResponse[IncidentRead])
def update_incident(
    incident_id: int,
    payload: IncidentUpdate,
    _: None = Depends(require_roles("moderator", "admin")),
) -> ApiResponse[IncidentRead]:
    row = IncidentService.update_incident(incident_id, payload)
    return ApiResponse(data=IncidentRead.model_validate(row, from_attributes=True))


@router.post("/{incident_id}/verify", response_model=ApiResponse[IncidentVerificationRead])
def verify_incident(
    incident_id: int,
    payload: IncidentVerifyRequest,
    request: Request,
    current_user=Depends(get_current_active_user),
    _: None = Depends(require_roles("moderator", "admin")),
) -> ApiResponse[IncidentVerificationRead]:
    row = IncidentService.verify_incident(
        incident_id,
        payload.action,
        payload.reason,
        current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return ApiResponse(data=IncidentVerificationRead.model_validate(row, from_attributes=True))


@router.get("/{incident_id}/verification-events", response_model=ApiResponse[list[IncidentVerificationRead]])
def verification_events(incident_id: int, _: object = Depends(get_current_active_user)) -> ApiResponse[list[IncidentVerificationRead]]:
    rows = IncidentService.list_verification_events(incident_id)
    return ApiResponse(data=[IncidentVerificationRead.model_validate(r, from_attributes=True) for r in rows])
