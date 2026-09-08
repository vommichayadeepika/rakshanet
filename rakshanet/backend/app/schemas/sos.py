from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


class SOSExtractionResponse(BaseModel):
    detected_language: str
    language_name: str
    is_transliterated: bool
    need_type: str
    urgency: str
    priority_score: float
    people_count: Optional[int] = 1
    is_life_threatening: bool = False
    danger_factors: List[str] = []
    location_mentions: List[str] = []
    extracted_keywords: List[str] = []


class SOSAnalyzeRequest(BaseModel):
    message: str = Field(description="Raw citizen distress report in English, Hindi, Telugu, Tamil, Kannada, Malayalam, or Transliterated script")


class SOSBase(BaseModel):
    message: str
    latitude: float
    longitude: float
    language: Optional[str] = "en"
    need_type: Optional[str] = "other"  # medical, rescue, food, water, shelter, evacuation, other
    urgency: Optional[str] = "medium"   # low, medium, high, critical
    priority_score: Optional[float] = Field(default=50.0, ge=0.0, le=100.0)
    status: Optional[str] = "SUBMITTED" # SUBMITTED, ASSIGNED, EN_ROUTE, ON_SITE, COMPLETED
    user_id: Optional[int] = None
    assigned_team_id: Optional[int] = None


class SOSCreate(BaseModel):
    message: str
    latitude: float
    longitude: float
    user_id: Optional[int] = None
    language: Optional[str] = None
    need_type: Optional[str] = None
    urgency: Optional[str] = None


class SOSUpdate(BaseModel):
    status: Optional[str] = None
    assigned_team_id: Optional[int] = None
    priority_score: Optional[float] = None
    urgency: Optional[str] = None
    need_type: Optional[str] = None


class SOSResponse(SOSBase):
    id: int
    timestamp: datetime
    structured_extraction: Optional[SOSExtractionResponse] = None

    model_config = ConfigDict(from_attributes=True)
