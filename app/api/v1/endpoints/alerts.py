from fastapi import APIRouter, Depends, Query, status

from app.dependencies.auth import get_current_active_user
from app.schemas.alert import AlertDeliveryRead, AlertSubscriptionCreate, AlertSubscriptionRead
from app.schemas.common import ApiResponse
from app.services.alert_service import AlertService

router = APIRouter()


@router.get("/subscriptions", response_model=ApiResponse[list[AlertSubscriptionRead]])
def list_subscriptions(current_user=Depends(get_current_active_user)) -> ApiResponse[list[AlertSubscriptionRead]]:
    rows = AlertService.list_subscriptions(current_user.id)
    return ApiResponse(data=[AlertSubscriptionRead.model_validate(r, from_attributes=True) for r in rows])


@router.post("/subscriptions", status_code=status.HTTP_201_CREATED, response_model=ApiResponse[AlertSubscriptionRead])
def create_subscription(payload: AlertSubscriptionCreate, current_user=Depends(get_current_active_user)) -> ApiResponse[AlertSubscriptionRead]:
    row = AlertService.create_subscription(current_user.id, payload)
    return ApiResponse(data=AlertSubscriptionRead.model_validate(row, from_attributes=True))


@router.delete("/subscriptions/{subscription_id}", response_model=ApiResponse[dict])
def delete_subscription(subscription_id: int, current_user=Depends(get_current_active_user)) -> ApiResponse[dict]:
    AlertService.delete_subscription(current_user.id, subscription_id)
    return ApiResponse(data={"deleted": True})


@router.get("/", response_model=ApiResponse[list[AlertDeliveryRead]])
def list_alerts(
    unread_only: bool = Query(default=False),
    subscription_id: int | None = Query(default=None),
    current_user=Depends(get_current_active_user),
) -> ApiResponse[list[AlertDeliveryRead]]:
    rows = AlertService.list_alerts(current_user.id, unread_only=unread_only, subscription_id=subscription_id)
    return ApiResponse(data=rows)


@router.post("/{alert_id}/mark-read", response_model=ApiResponse[dict])
def mark_read(alert_id: int, current_user=Depends(get_current_active_user)) -> ApiResponse[dict]:
    result = AlertService.mark_read(alert_id, current_user.id)
    return ApiResponse(data=result)
