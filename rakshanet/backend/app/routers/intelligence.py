from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.zone import Zone
from app.ai.risk_engine import risk_engine
from app.schemas.intelligence import ZoneIntelligenceResponse

router = APIRouter(tags=["AI Zone Intelligence"])


@router.get("/zone-intelligence", response_model=List[ZoneIntelligenceResponse])
def get_all_zone_intelligence(db: Session = Depends(get_db)):
    """
    Core AI Intelligence API.
    Dynamically analyzes multi-source disaster indicators:
    - Hydrological sensors (rainfall, river level, flood depth)
    - SACHET-NDMA, IMD, CWC alert vectors
    - Aerial drone road surveys
    - Multilingual citizen SOS emergency reports
    
    Returns all zones ranked by Response Priority, with predictive trajectories,
    recommended actions, and explainable score breakdowns.
    """
    return risk_engine.analyze_all_zones(db, sync_to_db=True)


@router.get("/zone-intelligence/{zone_id}", response_model=ZoneIntelligenceResponse)
def get_single_zone_intelligence(zone_id: int, db: Session = Depends(get_db)):
    """
    Retrieves deep intelligence and score breakdown for a specific zone.
    """
    all_intelligence = risk_engine.analyze_all_zones(db, sync_to_db=False)
    for z in all_intelligence:
        if z.zone_id == zone_id:
            return z
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Zone with ID {zone_id} not found"
    )


@router.post("/zone-intelligence/recalculate", response_model=List[ZoneIntelligenceResponse])
def recalculate_zone_intelligence(db: Session = Depends(get_db)):
    """
    Forces an immediate recalculation of all risk scores, priority ranks, and recommended actions,
    synchronizing the results back to the database and broadcasting via WebSocket.
    """
    updated_intelligence = risk_engine.analyze_all_zones(db, sync_to_db=True)
    
    # Broadcast updated scores to connected dashboards
    from app.websocket import ws_manager
    ws_manager.broadcast_sync({
        "event": "ZONE_INTELLIGENCE_UPDATED",
        "data": [z.model_dump() for z in updated_intelligence]
    })
    
    return updated_intelligence

