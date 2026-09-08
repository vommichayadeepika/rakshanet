from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class UserBase(BaseModel):
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    role: str = "citizen"
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    availability: bool = True
    skills: Optional[str] = None


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    availability: Optional[bool] = None
    skills: Optional[str] = None


class UserResponse(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
