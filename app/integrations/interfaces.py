from abc import ABC, abstractmethod


class RoutingProvider(ABC):
    @abstractmethod
    def estimate_route(
        self,
        origin_lat: float,
        origin_lng: float,
        destination_lat: float,
        destination_lng: float,
        transport_mode: str,
        avoid_checkpoints: bool,
        avoid_area_ids: list[int],
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def geocode(self, query: str, limit: int) -> list[dict]:
        raise NotImplementedError


class WeatherProvider(ABC):
    @abstractmethod
    def current_weather(self, lat: float, lng: float) -> dict:
        raise NotImplementedError
