from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.alert import Alert
from app.schemas.alert import AlertCreate, AlertResponse

router = APIRouter(prefix="/alerts", tags=["Disaster Alerts"])


@router.get("", response_model=List[AlertResponse])
def get_alerts(severity: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    """
    Retrieve incoming disaster alerts (e.g. SACHET-NDMA, IMD, CWC).
    Supports optional filtering by severity.
    """
    query = db.query(Alert)
    if severity:
        query = query.filter(Alert.severity == severity.upper())
    return query.order_by(Alert.timestamp.desc()).limit(limit).all()


@router.post("", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create_alert(alert_in: AlertCreate, db: Session = Depends(get_db)):
    """Ingest a new disaster alert into the system."""
    alert = Alert(**alert_in.model_dump())
    db.add(alert)
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/{alert_id}", response_model=AlertResponse)
def get_alert_by_id(alert_id: int, db: Session = Depends(get_db)):
    """Retrieve an alert by its ID."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Alert {alert_id} not found")
    return alert
