import hashlib
import json

from app.core.config import settings
from app.integrations.factory import get_weather_provider
from app.services.cache_service import CacheService


class WeatherService:
    @staticmethod
    def get_current(lat: float, lng: float) -> dict:
        payload = {"lat": round(lat, 4), "lng": round(lng, 4)}
        cache_key = WeatherService._cache_key(payload)
        cached = CacheService.get(cache_key)
        if cached:
            return {**cached, "cached": True}

        provider = get_weather_provider()
        result = provider.current_weather(lat=lat, lng=lng)
        normalized = {
            "provider": result["provider"],
            "temperature_c": result.get("temperature_c"),
            "feels_like_c": result.get("feels_like_c"),
            "humidity_percent": result.get("humidity_percent"),
            "condition": result.get("condition"),
            "condition_description": result.get("condition_description"),
            "wind_speed_mps": result.get("wind_speed_mps"),
            "cached": False,
        }
        CacheService.set(cache_key, normalized, settings.cache_ttl_weather_seconds)
        return normalized

    @staticmethod
    def _cache_key(payload: dict) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return "weather:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()
