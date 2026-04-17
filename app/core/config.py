from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "Wasel Palestine API"
    app_env: str = "development"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 14

    database_url: str
    auto_create_tables: bool = True

    log_level: str = "INFO"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])

    seed_admin_email: str | None = None
    seed_admin_password: str | None = None
    seed_admin_full_name: str = "Platform Admin"

    # External integration resilience
    external_request_timeout_seconds: float = 8.0
    external_max_retries: int = 3
    external_backoff_base_seconds: float = 0.5
    external_backoff_max_seconds: float = 4.0
    external_user_agent: str = "WaselPalestine/1.0 (academic-project)"

    # Routing/geolocation provider (OSM-based)
    routing_provider: str = "osm"
    routing_base_url: str = "https://router.project-osrm.org"
    geocoding_base_url: str = "https://nominatim.openstreetmap.org"
    routing_min_interval_ms: int = 1200

    # Weather provider
    weather_provider: str = "openweather"
    weather_base_url: str = "https://api.openweathermap.org/data/2.5"
    weather_api_key: SecretStr | None = None
    weather_min_interval_ms: int = 300

    # Cache TTLs
    cache_ttl_route_seconds: int = 120
    cache_ttl_geocode_seconds: int = 600
    cache_ttl_weather_seconds: int = 300


settings = Settings()
