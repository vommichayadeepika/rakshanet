from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class EnvironmentalReading(Base):
    __tablename__ = "environmental_readings"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, ForeignKey("zones.id", ondelete="CASCADE"), nullable=False)
    rainfall_intensity = Column(Float, default=0.0)         # mm/hr
    cumulative_rainfall = Column(Float, default=0.0)        # mm (past 24h)
    river_level = Column(Float, default=0.0)                # current water level in meters
    danger_level = Column(Float, default=17.5)              # danger mark threshold in meters
    water_level_change_rate = Column(Float, default=0.0)    # rate of change in meters/hr (+ rising, - falling)
    water_depth = Column(Float, default=0.0)                # average inundation depth in zone (meters)
    timestamp = Column(DateTime, default=utc_now)

    # Relationship
    zone = relationship("Zone", backref="environmental_readings")
