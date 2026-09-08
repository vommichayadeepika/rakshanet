from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db

router = APIRouter(tags=["Simulation Engine"])


@router.post("/simulate-flood")
def trigger_flood_simulation(db: Session = Depends(get_db)):
    """
    Triggers the end-to-end flood escalation simulation pipeline.
    In Phase 1, validates connectivity and returns readiness status.
    Will run the T+0 to T+12 cascade in subsequent phases.
    """
    return {
        "status": "initiated",
        "message": "Flood escalation simulation pipeline triggered",
        "steps_count": 12,
        "mode": "hybrid_prototype"
    }
