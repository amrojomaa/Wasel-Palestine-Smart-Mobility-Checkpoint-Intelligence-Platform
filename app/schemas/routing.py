from pydantic import BaseModel, Field, model_validator


class GeoPoint(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class RouteEstimateRequest(BaseModel):
    origin: GeoPoint
    destination: GeoPoint
    transport_mode: str = Field(default="CAR")
    avoid_checkpoints: bool = False
    avoid_area_ids: list[int] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_points_differ(self):
        if abs(self.origin.lat - self.destination.lat) < 1e-9 and abs(self.origin.lng - self.destination.lng) < 1e-9:
            raise ValueError("origin and destination cannot be identical")
        return self


class GeocodeResponseItem(BaseModel):
    display_name: str | None
    lat: float
    lng: float
    type: str | None


class RouteOption(BaseModel):
    rank: int
    distance_m: int
    duration_s: int


class RouteEstimateResponse(BaseModel):
    provider: str
    estimated_distance_m: int
    estimated_duration_s: int
    options: list[RouteOption]
    factors: dict
    cached: bool
