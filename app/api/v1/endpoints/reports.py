from fastapi import APIRouter, Depends, Query, Request, status

from app.dependencies.auth import get_current_active_user
from app.schemas.common import ApiResponse
from app.schemas.report import ReportCreate, ReportRead, ReportVoteRequest
from app.services.abuse_prevention_service import AbusePreventionService
from app.services.report_service import ReportService

router = APIRouter()


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[ReportRead])
def create_report(payload: ReportCreate, request: Request, current_user=Depends(get_current_active_user)) -> ApiResponse[ReportRead]:
    ip_address = request.client.host if request.client else None
    AbusePreventionService.check_report_submission(str(current_user.id), ip_address)
    row = ReportService.create_report(payload, current_user.id, ip_address=ip_address)
    return ApiResponse(data=ReportRead.model_validate(row, from_attributes=True))


@router.get("/", response_model=ApiResponse[list[ReportRead]])
def list_reports(
    status_filter: str | None = Query(default=None, alias="status"),
    mine_only: bool = Query(default=False),
    current_user=Depends(get_current_active_user),
) -> ApiResponse[list[ReportRead]]:
    user_id = current_user.id if mine_only else None
    rows = ReportService.list_reports(status=status_filter, user_id=user_id)
    return ApiResponse(data=[ReportRead.model_validate(r, from_attributes=True) for r in rows])


@router.get("/{report_id}", response_model=ApiResponse[ReportRead])
def get_report(report_id: int, _: object = Depends(get_current_active_user)) -> ApiResponse[ReportRead]:
    row = ReportService.get_report(report_id)
    return ApiResponse(data=ReportRead.model_validate(row, from_attributes=True))


@router.post("/{report_id}/vote", response_model=ApiResponse[dict])
def vote(report_id: int, payload: ReportVoteRequest, current_user=Depends(get_current_active_user)) -> ApiResponse[dict]:
    data = ReportService.vote(report_id, current_user.id, payload.vote_value)
    return ApiResponse(data=data)
