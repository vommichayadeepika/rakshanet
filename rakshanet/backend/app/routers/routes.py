"""
Phase 7 – Drone Route Intelligence & Safe Evacuation Pathfinding API Router.
Exposes endpoints for evacuation route planning, drone recon missions, shelter
info, and arbitrary point-to-point route calculation.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.ai.route_engine import route_engine
from app.schemas.routes import (
    EvacuationRouteResponse,
    DroneReconMissionResponse,
    ShelterInfo,
    CustomRouteRequest,
)

router = APIRouter(
    prefix="/routes",
    tags=["Route Intelligence (Phase 7)"],
)


@router.get(
    "/evacuation",
    response_model=List[EvacuationRouteResponse],
    summary="Get safe ground evacuation routes from affected zones to relief shelters",
)
def get_evacuation_routes(
    zone_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Computes optimal, drone-hazard-aware ground evacuation paths for all monitored
    sectors (or a specific zone if `zone_id` is supplied).

    The engine dynamically weights road segments using:
    - Drone-reported blocked / flooded roads (+1000 penalty → impassable)
    - Restricted / partially flooded roads (×2.5 cost multiplier)
    - Zone risk scores (RED zones incur additional danger factor)
    - Verified clear drone corridors (×0.8 discount)

    Returns ranked safe routes with turn-by-turn waypoints, distance,
    estimated travel time, safety score, and a list of hazards bypassed.
    """
    try:
        routes = route_engine.get_safe_evacuation_routes(db, origin_zone_id=zone_id)
        return routes
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Route engine error: {exc}")


@router.get(
    "/drone-recon",
    response_model=List[DroneReconMissionResponse],
    summary="Get planned drone aerial reconnaissance missions",
)
def get_drone_recon_missions(db: Session = Depends(get_db)):
    """
    Returns pre-planned multi-waypoint drone reconnaissance sorties.

    **Mission ALPHA (Garuda-01)** — Western floodway: Prakasam Barrage, 
    Bhavanipuram culverts, Krishnalanka bund breach, NH16 bypass assessment.

    **Mission BRAVO (Pushpak-02)** — Eastern corridor: Ramavarappadu junction,
    Autonagar industrial canal backflow, Benz Circle ambulance corridor clearance.

    Each mission includes flight path polyline, waypoint instructions, flight
    distance, estimated duration, and priority target list.
    """
    try:
        missions = route_engine.get_drone_recon_missions(db)
        return missions
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Drone mission engine error: {exc}")


@router.get(
    "/safe-shelters",
    response_model=List[ShelterInfo],
    summary="Get list of designated high-ground evacuation relief centres",
)
def get_safe_shelters():
    """
    Returns static info for all three designated relief shelters:
    - Tadepalli Primary Relief Haven (capacity 15,000, elevation 28.5 m)
    - Kanakadurga High-Ground Center (capacity 8,000, elevation 34.0 m)
    - Autonagar Industrial Elevated Shelter (capacity 6,500, elevation 26.0 m)
    """
    return route_engine.get_safe_shelters()


@router.post(
    "/calculate",
    response_model=EvacuationRouteResponse,
    summary="Calculate a custom point-to-point hazard-avoiding route",
)
def calculate_custom_route(
    request: CustomRouteRequest,
    db: Session = Depends(get_db),
):
    """
    Calculates a drone-blockage-aware route between arbitrary GPS coordinates.
    The engine snaps to the nearest graph nodes and runs Dijkstra with live
    hazard costs.

    Supported `vehicle_type` values: `rescue_truck`, `ambulance`, `boat`
    (affects the assumed speed used for ETA calculation).
    """
    try:
        route = route_engine.calculate_custom_route(
            origin_lat=request.origin_lat,
            origin_lon=request.origin_lon,
            dest_lat=request.destination_lat,
            dest_lon=request.destination_lon,
            vehicle_type=request.vehicle_type or "rescue_truck",
            db=db,
        )
        return route
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Custom route calculation error: {exc}")


@router.post(
    "/recalculate",
    response_model=List[EvacuationRouteResponse],
    summary="Recalculate all evacuation routes and broadcast over WebSockets",
)
def recalculate_evacuation_routes(db: Session = Depends(get_db)):
    """
    Triggers dynamic re-routing across all monitored zones incorporating latest
    drone telemetry and zone flood risk assessments, broadcasting updates to all
    connected dashboards.
    """
    try:
        routes = route_engine.get_safe_evacuation_routes(db)
        from app.websocket import ws_manager
        routes_data = [r.model_dump() for r in routes]
        ws_manager.broadcast_sync({
            "event": "ROUTES_UPDATED",
            "data": routes_data,
            "message": f"Successfully recomputed {len(routes)} safe evacuation corridors with live hazard avoidance."
        })
        return routes
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Route recalculation error: {exc}")

