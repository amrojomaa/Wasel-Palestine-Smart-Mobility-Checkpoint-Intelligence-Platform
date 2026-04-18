from app.core.config import settings
from app.core.exceptions import ServiceConfigurationException
from app.integrations.http_client import ResilientHttpClient
from app.integrations.interfaces import WeatherProvider


class OpenWeatherProvider(WeatherProvider):
    def __init__(self, http_client: ResilientHttpClient):
        self.http_client = http_client

    def current_weather(self, lat: float, lng: float) -> dict:
        if not settings.weather_api_key:
            raise ServiceConfigurationException(message="WEATHER_API_KEY is not configured")

        params = {
            "lat": lat,
            "lon": lng,
            "appid": settings.weather_api_key.get_secret_value(),
            "units": "metric",
        }
        url = f"{settings.weather_base_url}/weather"
        payload = self.http_client.request_json(
            provider="openweather",
            method="GET",
            url=url,
            params=params,
            min_interval_ms=settings.weather_min_interval_ms,
        )

        weather_items = payload.get("weather", [])
        first_weather = weather_items[0] if weather_items else {}
        main = payload.get("main", {})
        wind = payload.get("wind", {})

        return {
            "provider": "openweather",
            "temperature_c": main.get("temp"),
            "feels_like_c": main.get("feels_like"),
            "humidity_percent": main.get("humidity"),
            "condition": first_weather.get("main"),
            "condition_description": first_weather.get("description"),
            "wind_speed_mps": wind.get("speed"),
            "raw": payload,
        }
