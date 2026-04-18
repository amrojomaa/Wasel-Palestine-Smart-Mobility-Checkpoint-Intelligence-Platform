from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import get_current_active_user
from app.schemas.common import ApiResponse
from app.schemas.routing import GeocodeResponseItem, RouteEstimateRequest, RouteEstimateResponse
from app.services.route_history_service import RouteHistoryService
from app.services.routing_service import RoutingService

router = APIRouter()


@router.post("/estimate", response_model=ApiResponse[RouteEstimateResponse])
def estimate_route(
    payload: RouteEstimateRequest,
    current_user=Depends(get_current_active_user),
) -> ApiResponse[RouteEstimateResponse]:
    result = RoutingService.estimate_route(payload, user_id=current_user.id)
    return ApiResponse(data=RouteEstimateResponse.model_validate(result))


@router.get("/geocode", response_model=ApiResponse[dict])
def geocode(
    q: str = Query(min_length=2, max_length=180),
    limit: int = Query(default=5, ge=1, le=10),
    _=Depends(get_current_active_user),
) -> ApiResponse[dict]:
    result = RoutingService.geocode(query=q, limit=limit)
    response = {
        "results": [GeocodeResponseItem.model_validate(item).model_dump() for item in result["results"]],
        "cached": result["cached"],
    }
    return ApiResponse(data=response)


@router.get("/requests", response_model=ApiResponse[list[dict]])
def route_history(current_user=Depends(get_current_active_user)) -> ApiResponse[list[dict]]:
    rows = RouteHistoryService.list_for_user(current_user.id)
    data = [
        {
            "id": r.id,
            "transport_mode": r.transport_mode,
            "request_status": r.request_status,
            "estimated_distance_m": r.estimated_distance_m,
            "estimated_duration_s": r.estimated_duration_s,
            "requested_at": r.requested_at,
        }
        for r in rows
    ]
    return ApiResponse(data=data)
