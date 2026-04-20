from datetime import datetime

from pydantic import BaseModel, Field


class CheckpointCreate(BaseModel):
    code: str = Field(min_length=2, max_length=40)
    name: str = Field(min_length=2, max_length=160)
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    governorate: str | None = Field(default=None, max_length=80)


class CheckpointUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=160)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    governorate: str | None = Field(default=None, max_length=80)
    is_active: bool | None = None


class CheckpointRead(BaseModel):
    id: int
    code: str
    name: str
    latitude: float
    longitude: float
    governorate: str | None
    is_active: bool


class CheckpointStatusCreate(BaseModel):
    status: str = Field(min_length=2, max_length=30)
    reason: str | None = Field(default=None, max_length=1000)


class CheckpointStatusRead(BaseModel):
    id: int
    checkpoint_id: int
    status: str
    reason: str | None
    source_type: str
    effective_from: datetime
    effective_to: datetime | None
