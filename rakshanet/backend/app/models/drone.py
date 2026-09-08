from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class DroneReading(Base):
    __tablename__ = "drone_readings"

    id = Column(Integer, primary_key=True, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    obstacle_type = Column(String(50), default="flooded_road")  # flooded_road, landslide, bridge_submerged, clear
    water_depth = Column(Float, default=0.0)                    # in meters
    road_status = Column(String(30), default="passable")         # passable, restricted, blocked
    confidence = Column(Float, default=0.9)                     # 0.0 to 1.0
    timestamp = Column(DateTime, default=utc_now)
