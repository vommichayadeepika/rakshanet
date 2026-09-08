from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.drone import DroneReading
from app.schemas.drone import DroneReadingCreate, DroneReadingResponse

router = APIRouter(prefix="/drone-readings", tags=["Drone Intelligence"])


@router.get("", response_model=List[DroneReadingResponse])
def get_drone_readings(
    road_status: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Retrieve aerial drone road survey readings.
    Filter by road_status ('passable', 'restricted', 'blocked').
    """
    query = db.query(DroneReading)
    if road_status:
        query = query.filter(DroneReading.road_status == road_status.lower())
    return query.order_by(DroneReading.timestamp.desc()).limit(limit).all()


@router.post("", response_model=DroneReadingResponse, status_code=status.HTTP_201_CREATED)
def submit_drone_reading(reading_in: DroneReadingCreate, db: Session = Depends(get_db)):
    """Ingest a new drone observation reading."""
    reading = DroneReading(**reading_in.model_dump())
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading
