from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    role = Column(String(30), default="citizen")  # citizen, volunteer, responder, coordinator, admin
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    availability = Column(Boolean, default=True)
    skills = Column(String(255), nullable=True)  # comma-separated e.g. "first_aid,swimming"
    created_at = Column(DateTime, default=utc_now)

    # Relationships
    sos_reports = relationship("SOSReport", back_populates="user")
