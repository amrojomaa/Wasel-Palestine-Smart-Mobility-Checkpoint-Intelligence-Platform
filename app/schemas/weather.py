from pydantic import BaseModel, Field


class WeatherCurrentRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)


class WeatherCurrentResponse(BaseModel):
    provider: str
    temperature_c: float | None
    feels_like_c: float | None
    humidity_percent: float | None
    condition: str | None
    condition_description: str | None
    wind_speed_mps: float | None
    cached: bool
