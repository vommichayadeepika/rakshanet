from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(50), default="SACHET-NDMA")  # SACHET-NDMA, CWC, IMD, SENSOR
    alert_type = Column(String(100), nullable=False)    # Heavy rainfall warning, Flood warning, etc.
    severity = Column(String(30), default="WATCH")      # WATCH, ALERT, WARNING, SEVERE
    message = Column(Text, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius = Column(Float, default=10.0)                # impact radius in km
    timestamp = Column(DateTime, default=utc_now)
