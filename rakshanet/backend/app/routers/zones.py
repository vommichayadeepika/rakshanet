from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.zone import Zone
from app.schemas.zone import ZoneCreate, ZoneUpdate, ZoneResponse

router = APIRouter(prefix="/zones", tags=["Zones"])


@router.get("", response_model=List[ZoneResponse])
def get_all_zones(db: Session = Depends(get_db)):
    """Retrieve all monitored disaster zones sorted by priority rank."""
    return db.query(Zone).order_by(Zone.priority_rank.asc(), Zone.risk_score.desc()).all()


@router.post("", response_model=ZoneResponse, status_code=status.HTTP_201_CREATED)
def create_zone(zone_in: ZoneCreate, db: Session = Depends(get_db)):
    """Create a new zone."""
    existing = db.query(Zone).filter(Zone.name == zone_in.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Zone with name '{zone_in.name}' already exists"
        )
    zone = Zone(**zone_in.model_dump())
    db.add(zone)
    db.commit()
    db.refresh(zone)
    return zone


@router.get("/{zone_id}", response_model=ZoneResponse)
def get_zone_by_id(zone_id: int, db: Session = Depends(get_db)):
    """Retrieve detailed zone by its ID."""
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone with ID {zone_id} not found"
        )
    return zone


@router.patch("/{zone_id}", response_model=ZoneResponse)
def update_zone(zone_id: int, update_data: ZoneUpdate, db: Session = Depends(get_db)):
    """Update zone metrics (risk score, priority rank, active SOS count, etc.)."""
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Zone with ID {zone_id} not found"
        )
    for field, value in update_data.model_dump(exclude_unset=True).items():
        setattr(zone, field, value)
    db.commit()
    db.refresh(zone)
    return zone
