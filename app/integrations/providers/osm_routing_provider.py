from math import sqrt
from urllib.parse import quote

from app.core.config import settings
from app.db.session import SessionLocal
from app.integrations.http_client import ResilientHttpClient
from app.integrations.interfaces import RoutingProvider
from app.models.checkpoint import Checkpoint


class OSMRoutingProvider(RoutingProvider):
    def __init__(self, http_client: ResilientHttpClient):
        self.http_client = http_client

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
        profile = self._map_profile(transport_mode)
        url = (
            f"{settings.routing_base_url}/route/v1/{profile}/"
            f"{origin_lng},{origin_lat};{destination_lng},{destination_lat}"
        )
        params = {"overview": "false", "alternatives": "true", "steps": "false", "annotations": "false"}

        payload = self.http_client.request_json(
            provider="osm-routing",
            method="GET",
            url=url,
            params=params,
            min_interval_ms=settings.routing_min_interval_ms,
        )

        routes = payload.get("routes", [])
        options = []
        for idx, route in enumerate(routes[:3], start=1):
            options.append({"rank": idx, "distance_m": int(route.get("distance", 0)), "duration_s": int(route.get("duration", 0))})

        best = options[0] if options else {"distance_m": 0, "duration_s": 0}

        checkpoint_penalty = self._checkpoint_penalty(origin_lat, origin_lng, destination_lat, destination_lng) if avoid_checkpoints else 0
        area_penalty = 120 * len(avoid_area_ids) if avoid_area_ids else 0

        factors = {
            "provider_constraints": {
                "avoid_checkpoints_applied": bool(avoid_checkpoints),
                "avoid_areas_applied": bool(avoid_area_ids),
                "notes": "OSRM public endpoint does not support hard polygon/checkpoint exclusion; heuristic penalties are applied.",
            },
            "requested_avoid_checkpoints": avoid_checkpoints,
            "requested_avoid_area_ids": avoid_area_ids,
            "checkpoint_penalty_s": checkpoint_penalty,
            "area_penalty_s": area_penalty,
        }

        return {
            "provider": "osm-osrm",
            "estimated_distance_m": best["distance_m"],
            "estimated_duration_s": best["duration_s"],
            "options": options,
            "factors": factors,
            "raw": payload,
        }

    def geocode(self, query: str, limit: int) -> list[dict]:
        encoded_query = quote(query)
        url = f"{settings.geocoding_base_url}/search"
        params = {"q": encoded_query, "format": "jsonv2", "limit": limit, "addressdetails": 1}

        payload = self.http_client.request_json(
            provider="osm-geocoding",
            method="GET",
            url=url,
            params=params,
            min_interval_ms=settings.routing_min_interval_ms,
            headers={"Accept": "application/json"},
        )

        results = []
        for item in payload:
            results.append(
                {
                    "display_name": item.get("display_name"),
                    "lat": float(item.get("lat")),
                    "lng": float(item.get("lon")),
                    "type": item.get("type"),
                }
            )
        return results

    @staticmethod
    def _map_profile(mode: str) -> str:
        normalized = mode.upper()
        if normalized == "WALK":
            return "foot"
        return "driving"

    @staticmethod
    def _distance(a_lat: float, a_lng: float, b_lat: float, b_lng: float) -> float:
        return sqrt((a_lat - b_lat) ** 2 + (a_lng - b_lng) ** 2)

    def _checkpoint_penalty(self, origin_lat: float, origin_lng: float, destination_lat: float, destination_lng: float) -> int:
        with SessionLocal() as db:
            checkpoints = db.query(Checkpoint).filter(Checkpoint.is_active.is_(True)).limit(150).all()
        if not checkpoints:
            return 0

        mid_lat = (origin_lat + destination_lat) / 2
        mid_lng = (origin_lng + destination_lng) / 2
        close_count = 0
        for cp in checkpoints:
            if self._distance(mid_lat, mid_lng, cp.latitude, cp.longitude) < 0.05:
                close_count += 1
        return close_count * 90
