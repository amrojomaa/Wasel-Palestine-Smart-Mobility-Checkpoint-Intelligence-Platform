from fastapi import APIRouter

from app.core.config import settings
from app.schemas.common import ApiResponse

router = APIRouter()


@router.get("/health", response_model=ApiResponse[dict])
def health_check() -> ApiResponse[dict]:
    has_weather_key = bool(settings.weather_api_key and settings.weather_api_key.get_secret_value().strip())
    return ApiResponse(
        data={
            "status": "ok",
            "dependencies": {
                "weather_api_configured": has_weather_key,
            },
        }
    )
