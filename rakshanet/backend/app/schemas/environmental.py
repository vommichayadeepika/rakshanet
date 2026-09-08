from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class EnvironmentalReadingBase(BaseModel):
    zone_id: int
    rainfall_intensity: float = Field(default=0.0, description="Rainfall intensity in mm/hr")
    cumulative_rainfall: float = Field(default=0.0, description="24h cumulative rainfall in mm")
    river_level: float = Field(default=0.0, description="Current river/canal water level in meters")
    danger_level: float = Field(default=17.5, description="Danger threshold in meters")
    water_level_change_rate: float = Field(default=0.0, description="Rate of change in meters/hr")
    water_depth: float = Field(default=0.0, description="Surface inundation water depth in meters")


class EnvironmentalReadingCreate(EnvironmentalReadingBase):
    pass


class EnvironmentalReadingResponse(EnvironmentalReadingBase):
    id: int
    timestamp: datetime
    zone_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
