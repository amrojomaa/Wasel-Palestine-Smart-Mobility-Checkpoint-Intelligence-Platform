from fastapi import APIRouter, Depends, Request

from app.dependencies.auth import get_current_active_user, require_roles
from app.schemas.common import ApiResponse
from app.schemas.report import ModerationActionRequest, ReportRead
from app.services.moderation_service import ModerationService

router = APIRouter()


@router.get("/reports/queue", response_model=ApiResponse[list[ReportRead]])
def moderation_queue(
    _: None = Depends(require_roles("moderator", "admin")),
    __=Depends(get_current_active_user),
) -> ApiResponse[list[ReportRead]]:
    rows = ModerationService.queue()
    return ApiResponse(data=[ReportRead.model_validate(r, from_attributes=True) for r in rows])


@router.post("/reports/{report_id}/actions", response_model=ApiResponse[dict])
def moderation_action(
    report_id: int,
    payload: ModerationActionRequest,
    request: Request,
    current_user=Depends(get_current_active_user),
    _: None = Depends(require_roles("moderator", "admin")),
) -> ApiResponse[dict]:
    row = ModerationService.act(
        report_id=report_id,
        action=payload.action,
        reason=payload.reason,
        duplicate_of_report_id=payload.duplicate_of_report_id,
        moderator_user_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return ApiResponse(data={"id": row.id, "report_id": row.report_id, "action": row.action, "to_status": row.to_status, "created_at": row.created_at})


@router.post("/reports/{report_id}/promote-to-incident", response_model=ApiResponse[dict])
def promote_to_incident(
    report_id: int,
    current_user=Depends(get_current_active_user),
    _: None = Depends(require_roles("moderator", "admin")),
) -> ApiResponse[dict]:
    result = ModerationService.promote_to_incident(report_id, current_user.id)
    return ApiResponse(data=result)
