from app.core.config import settings
from app.integrations.http_client import ResilientHttpClient
from app.integrations.interfaces import RoutingProvider, WeatherProvider
from app.integrations.providers.openweather_provider import OpenWeatherProvider
from app.integrations.providers.osm_routing_provider import OSMRoutingProvider

_http_client = ResilientHttpClient()


def get_routing_provider() -> RoutingProvider:
    provider_name = settings.routing_provider.lower()
    if provider_name == "osm":
        return OSMRoutingProvider(_http_client)
    raise ValueError(f"Unsupported routing provider: {provider_name}")


def get_weather_provider() -> WeatherProvider:
    provider_name = settings.weather_provider.lower()
    if provider_name == "openweather":
        return OpenWeatherProvider(_http_client)
    raise ValueError(f"Unsupported weather provider: {provider_name}")
