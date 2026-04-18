from fastapi import APIRouter, Depends, Query

from app.dependencies.auth import get_current_active_user
from app.schemas.common import ApiResponse
from app.schemas.weather import WeatherCurrentResponse
from app.services.weather_service import WeatherService

router = APIRouter()


@router.get("/current", response_model=ApiResponse[WeatherCurrentResponse])
def current_weather(
    lat: float = Query(ge=-90, le=90),
    lng: float = Query(ge=-180, le=180),
    _=Depends(get_current_active_user),
) -> ApiResponse[WeatherCurrentResponse]:
    result = WeatherService.get_current(lat=lat, lng=lng)
    return ApiResponse(data=WeatherCurrentResponse.model_validate(result))
