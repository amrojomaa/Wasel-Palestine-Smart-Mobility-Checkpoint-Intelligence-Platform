import hashlib
import json

from app.core.config import settings
from app.integrations.factory import get_routing_provider
from app.schemas.routing import RouteEstimateRequest
from app.services.cache_service import CacheService
from app.services.route_history_service import RouteHistoryService


class RoutingService:
    @staticmethod
    def estimate_route(payload: RouteEstimateRequest, user_id=None) -> dict:
        cache_key = RoutingService._cache_key("route", payload.model_dump())
        cached = CacheService.get(cache_key)
        if cached:
            return {**cached, "cached": True}

        provider = get_routing_provider()
        result = provider.estimate_route(
            origin_lat=payload.origin.lat,
            origin_lng=payload.origin.lng,
            destination_lat=payload.destination.lat,
            destination_lng=payload.destination.lng,
            transport_mode=payload.transport_mode,
            avoid_checkpoints=payload.avoid_checkpoints,
            avoid_area_ids=payload.avoid_area_ids,
        )

        normalized = {
            "provider": result["provider"],
            "estimated_distance_m": result["estimated_distance_m"],
            "estimated_duration_s": result["estimated_duration_s"],
            "options": result["options"],
            "factors": result["factors"],
            "cached": False,
        }

        # Partial constraint handling: apply heuristic duration penalties where direct provider enforcement is unavailable.
        penalties = 0
        if payload.avoid_checkpoints:
            penalties += int(result.get("factors", {}).get("checkpoint_penalty_s", 0))
        if payload.avoid_area_ids:
            penalties += int(result.get("factors", {}).get("area_penalty_s", 0))

        if penalties > 0:
            normalized["estimated_duration_s"] = max(0, normalized["estimated_duration_s"] + penalties)
            normalized["factors"]["heuristic_penalty_s"] = penalties

        CacheService.set(cache_key, normalized, settings.cache_ttl_route_seconds)
        if user_id:
            RouteHistoryService.store(user_id=user_id, payload=payload, result=normalized)
        return normalized

    @staticmethod
    def geocode(query: str, limit: int) -> dict:
        payload = {"q": query.strip().lower(), "limit": limit}
        cache_key = RoutingService._cache_key("geocode", payload)
        cached = CacheService.get(cache_key)
        if cached is not None:
            return {"results": cached, "cached": True}

        provider = get_routing_provider()
        results = provider.geocode(query=query, limit=limit)
        CacheService.set(cache_key, results, settings.cache_ttl_geocode_seconds)
        return {"results": results, "cached": False}

    @staticmethod
    def _cache_key(prefix: str, payload: dict) -> str:
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
        return f"{prefix}:{digest}"
