from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class TeamBase(BaseModel):
    name: str
    task: str = "General Rescue"
    status: str = "AVAILABLE"  # AVAILABLE, ASSIGNED, EN_ROUTE, ON_SITE, RETURNING
    latitude: float
    longitude: float
    member_count: int = 4


class TeamCreate(TeamBase):
    pass


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    task: Optional[str] = None
    status: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    member_count: Optional[int] = None


class TeamResponse(TeamBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
