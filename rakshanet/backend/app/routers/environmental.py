from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.environmental import EnvironmentalReading
from app.models.zone import Zone
from app.schemas.environmental import EnvironmentalReadingResponse

router = APIRouter(prefix="/environmental-readings", tags=["Environmental Telemetry"])


@router.get("", response_model=List[EnvironmentalReadingResponse])
def get_environmental_readings(
    zone_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Retrieve real-time environmental telemetry:
    - Rainfall intensity (mm/hr)
    - Cumulative rainfall (mm)
    - River water levels vs Danger mark
    - Rate of water level change (+/- m/hr)
    - Surface flood water depth
    """
    query = db.query(EnvironmentalReading)
    if zone_id:
        query = query.filter(EnvironmentalReading.zone_id == zone_id)
    
    readings = query.order_by(EnvironmentalReading.timestamp.desc()).all()
    results = []
    for r in readings:
        resp = EnvironmentalReadingResponse.model_validate(r)
        if r.zone:
            resp.zone_name = r.zone.name
        results.append(resp)
    return results
