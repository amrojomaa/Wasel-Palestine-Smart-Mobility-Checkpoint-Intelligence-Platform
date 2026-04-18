from app.dependencies.auth import get_current_active_user


def test_route_estimation_endpoint(test_client, monkeypatch, fake_current_user):
    from app.main import app
    from app.services.routing_service import RoutingService

    monkeypatch.setattr(
        RoutingService,
        "estimate_route",
        lambda payload: {
            "provider": "osm-osrm",
            "estimated_distance_m": 10000,
            "estimated_duration_s": 1200,
            "options": [{"rank": 1, "distance_m": 10000, "duration_s": 1200}],
            "factors": {"notes": "test"},
            "cached": False,
        },
    )

    app.dependency_overrides[get_current_active_user] = lambda: fake_current_user
    try:
        response = test_client.post(
            "/api/v1/routes/estimate",
            json={
                "origin": {"lat": 31.9, "lng": 35.2},
                "destination": {"lat": 31.8, "lng": 35.3},
                "transport_mode": "CAR",
                "avoid_checkpoints": True,
                "avoid_area_ids": [12],
            },
            headers={"Authorization": "Bearer x"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["estimated_duration_s"] == 1200
    finally:
        app.dependency_overrides.clear()


def test_weather_current_endpoint(test_client, monkeypatch, fake_current_user):
    from app.main import app
    from app.services.weather_service import WeatherService

    monkeypatch.setattr(
        WeatherService,
        "get_current",
        lambda lat, lng: {
            "provider": "openweather",
            "temperature_c": 19.3,
            "feels_like_c": 18.5,
            "humidity_percent": 70,
            "condition": "Clouds",
            "condition_description": "scattered clouds",
            "wind_speed_mps": 3.1,
            "cached": False,
        },
    )

    app.dependency_overrides[get_current_active_user] = lambda: fake_current_user
    try:
        response = test_client.get(
            "/api/v1/weather/current?lat=31.9&lng=35.2",
            headers={"Authorization": "Bearer x"},
        )
        assert response.status_code == 200
        assert response.json()["data"]["provider"] == "openweather"
    finally:
        app.dependency_overrides.clear()
