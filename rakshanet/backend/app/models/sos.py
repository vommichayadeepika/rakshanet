from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class SOSReport(Base):
    __tablename__ = "sos_reports"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    message = Column(Text, nullable=False)
    language = Column(String(10), default="en")          # en, te, hi, unknown
    need_type = Column(String(30), default="other")       # medical, rescue, food, water, shelter, evacuation, other
    urgency = Column(String(20), default="medium")        # low, medium, high, critical
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    priority_score = Column(Float, default=50.0)         # 0.0 to 100.0
    status = Column(String(30), default="SUBMITTED")     # SUBMITTED, ASSIGNED, EN_ROUTE, ON_SITE, COMPLETED
    assigned_team_id = Column(Integer, ForeignKey("teams.id", ondelete="SET NULL"), nullable=True)
    timestamp = Column(DateTime, default=utc_now)

    # Relationships
    user = relationship("User", back_populates="sos_reports")
    team = relationship("Team", back_populates="assigned_sos")
