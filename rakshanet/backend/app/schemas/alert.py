from datetime import datetime
from pydantic import BaseModel, ConfigDict


class AlertBase(BaseModel):
    source: str = "SACHET-NDMA"
    alert_type: str
    severity: str = "WATCH"  # WATCH, ALERT, WARNING, SEVERE
    message: str
    latitude: float
    longitude: float
    radius: float = 10.0


class AlertCreate(AlertBase):
    pass


class AlertResponse(AlertBase):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
