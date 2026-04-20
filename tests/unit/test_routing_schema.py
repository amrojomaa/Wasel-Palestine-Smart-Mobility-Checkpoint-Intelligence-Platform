import pytest

from app.schemas.routing import RouteEstimateRequest


def test_route_schema_rejects_identical_points():
    with pytest.raises(ValueError):
        RouteEstimateRequest(
            origin={"lat": 31.9, "lng": 35.2},
            destination={"lat": 31.9, "lng": 35.2},
        )
