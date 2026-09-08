from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    task = Column(String(150), default="General Rescue")
    status = Column(String(30), default="AVAILABLE")  # AVAILABLE, ASSIGNED, EN_ROUTE, ON_SITE, RETURNING
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    member_count = Column(Integer, default=4)
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    assigned_sos = relationship("SOSReport", back_populates="team")
