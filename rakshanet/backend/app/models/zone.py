from sqlalchemy import Column, Integer, String, Float
from app.database import Base


class Zone(Base):
    __tablename__ = "zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    population = Column(Integer, default=0)
    risk_score = Column(Float, default=0.0)  # 0 to 100
    risk_level = Column(String(20), default="GREEN")  # GREEN, YELLOW, ORANGE, RED
    priority_rank = Column(Integer, default=0)
    recommended_action = Column(String(100), default="MONITOR CLOSELY")
    active_sos_count = Column(Integer, default=0)
