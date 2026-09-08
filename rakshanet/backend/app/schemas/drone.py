from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class DroneReadingBase(BaseModel):
    latitude: float
    longitude: float
    obstacle_type: str = "flooded_road"
    water_depth: float = Field(default=0.0, ge=0.0)
    road_status: str = "passable"  # passable, restricted, blocked
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)


class DroneReadingCreate(DroneReadingBase):
    pass


class DroneReadingResponse(DroneReadingBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
