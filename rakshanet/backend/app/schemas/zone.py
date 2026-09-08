from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ZoneBase(BaseModel):
    name: str
    latitude: float
    longitude: float
    population: int = 0
    risk_score: float = Field(default=0.0, ge=0.0, le=100.0)
    risk_level: str = "GREEN"  # GREEN, YELLOW, ORANGE, RED
    priority_rank: int = 0
    recommended_action: str = "MONITOR CLOSELY"
    active_sos_count: int = 0


class ZoneCreate(ZoneBase):
    pass


class ZoneUpdate(BaseModel):
    name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    population: Optional[int] = None
    risk_score: Optional[float] = Field(default=None, ge=0.0, le=100.0)
    risk_level: Optional[str] = None
    priority_rank: Optional[int] = None
    recommended_action: Optional[str] = None
    active_sos_count: Optional[int] = None


class ZoneResponse(ZoneBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
