from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.simulation.mock_data import seed_mock_data, clear_mock_data, get_mock_data_status

router = APIRouter(prefix="/demo", tags=["Demo Data & Simulation Controls"])


@router.post("/seed")
def seed_demo_data(
    overwrite: bool = Query(True, description="Clear existing data before seeding new scenario"),
    db: Session = Depends(get_db)
):
    """
    Populates the database with realistic prototype disaster data and broadcasts
    refresh event across WebSockets.
    """
    result = seed_mock_data(db, overwrite=overwrite)
    from app.websocket import ws_manager
    ws_manager.broadcast_sync({
        "event": "DEMO_DATA_REFRESHED",
        "action": "seed",
        "message": "Scenario demo data seeded successfully"
    })
    return result


@router.post("/reset")
def reset_demo_data(db: Session = Depends(get_db)):
    """
    Wipes simulated disaster data back to an empty baseline and broadcasts reset.
    """
    deleted = clear_mock_data(db)
    from app.websocket import ws_manager
    ws_manager.broadcast_sync({
        "event": "DEMO_DATA_REFRESHED",
        "action": "reset",
        "message": "Scenario data reset"
    })
    return {
        "status": "cleared",
        "message": "Demo data successfully wiped",
        "deleted_records": deleted
    }


@router.get("/status")
def demo_data_status(db: Session = Depends(get_db)):
    """
    Returns counts and metrics of all currently seeded simulation entities.
    """
    return get_mock_data_status(db)


@router.post("/simulate-live-event")
def simulate_live_event(
    event_type: str = Query("sos", description="Type of live incident to simulate: 'sos', 'drone', or 'risk'"),
    db: Session = Depends(get_db)
):
    """
    Live WebSocket Demo Verification Endpoint.
    Injects a real-time event into the active database and broadcasts it over WebSockets
    to all connected Command Center dashboards:
    - 'sos': Simulates a critical multilingual citizen distress report with NLP intelligence
    - 'drone': Simulates an aerial drone detecting a blocked arterial road with deep water
    - 'risk': Simulates an escalation in river surge and forces an AI risk recalculation
    """
    import random
    from datetime import datetime, timezone
    from app.websocket import ws_manager
    from app.ai.risk_engine import risk_engine

    if event_type == "drone":
        from app.models.drone import DroneReading
        # Drone survey near Krishnalanka Floodway / Barrage
        lat = 16.502 + random.uniform(-0.01, 0.01)
        lon = 80.622 + random.uniform(-0.01, 0.01)
        depth = round(random.uniform(1.6, 2.4), 1)
        drone = DroneReading(
            latitude=lat,
            longitude=lon,
            obstacle_type="flooded_road",
            water_depth=depth,
            road_status="blocked",
            confidence=0.96,
            timestamp=datetime.now(timezone.utc)
        )
        db.add(drone)
        db.commit()
        db.refresh(drone)

        # Recalculate risk
        intel = risk_engine.analyze_all_zones(db, sync_to_db=True)
        intel_data = [z.model_dump() for z in intel]

        # Broadcast drone reading & updated risk
        drone_data = {
            "id": drone.id,
            "latitude": drone.latitude,
            "longitude": drone.longitude,
            "obstacle_type": drone.obstacle_type,
            "water_depth": drone.water_depth,
            "road_status": drone.road_status,
            "confidence": drone.confidence,
            "timestamp": drone.timestamp.isoformat()
        }
        ws_manager.broadcast_sync({
            "event": "NEW_DRONE_READING",
            "data": drone_data,
            "message": f"Drone detected road blockage with {depth}m water depth"
        })
        ws_manager.broadcast_sync({
            "event": "ZONE_INTELLIGENCE_UPDATED",
            "data": intel_data
        })

        # Phase 7: Automatically update evacuation routes with newly reported hazard
        from app.ai.route_engine import route_engine
        updated_routes = route_engine.get_safe_evacuation_routes(db)
        routes_payload = [r.model_dump() for r in updated_routes]
        ws_manager.broadcast_sync({
            "event": "ROUTES_UPDATED",
            "data": routes_payload,
            "message": f"Evacuation paths dynamically recalculated: {len(updated_routes)} routes active."
        })

        return {
            "status": "broadcasted",
            "event": "NEW_DRONE_READING",
            "data": drone_data,
            "zones_updated": len(intel_data),
            "routes_updated": len(routes_payload)
        }

    elif event_type == "risk":
        # Force recalculation and broadcast
        intel = risk_engine.analyze_all_zones(db, sync_to_db=True)
        intel_data = [z.model_dump() for z in intel]
        ws_manager.broadcast_sync({
            "event": "ZONE_INTELLIGENCE_UPDATED",
            "data": intel_data,
            "message": "AI Risk Engine dynamic re-scoring broadcasted"
        })
        from app.ai.route_engine import route_engine
        updated_routes = route_engine.get_safe_evacuation_routes(db)
        routes_payload = [r.model_dump() for r in updated_routes]
        ws_manager.broadcast_sync({
            "event": "ROUTES_UPDATED",
            "data": routes_payload,
            "message": "Evacuation routes synchronized with updated sector risk."
        })
        return {
            "status": "broadcasted",
            "event": "ZONE_INTELLIGENCE_UPDATED",
            "data": intel_data,
            "routes_updated": len(routes_payload)
        }

    elif event_type == "route":
        from app.ai.route_engine import route_engine
        routes = route_engine.get_safe_evacuation_routes(db)
        routes_payload = [r.model_dump() for r in routes]
        ws_manager.broadcast_sync({
            "event": "ROUTES_UPDATED",
            "data": routes_payload,
            "message": f"Live evacuation routes recalculated for {len(routes)} sectors."
        })
        return {
            "status": "broadcasted",
            "event": "ROUTES_UPDATED",
            "routes_count": len(routes_payload)
        }

    elif event_type == "relief":
        # Phase 8: Simulate live incoming relief request
        from app.models.relief import ReliefRequest
        from app.schemas.relief import ReliefRequestResponse
        import random
        req_id = f"REQ-LIVE-{random.randint(100, 999)}"
        new_req = ReliefRequest(
            request_code=req_id,
            location_name="Bhavanipuram Flood Relief Point 4",
            latitude=16.5210 + random.uniform(-0.005, 0.005),
            longitude=80.5980 + random.uniform(-0.005, 0.005),
            zone_id=2,
            category="Drinking Water",
            priority="Critical",
            priority_score=93.5,
            people_count=48,
            status="Pending",
            notes="Drinking water reserve exhausted; 48 evacuees require immediate supply"
        )
        db.add(new_req)
        db.commit()
        db.refresh(new_req)
        req_data = ReliefRequestResponse.model_validate(new_req).model_dump(mode="json")
        ws_manager.broadcast_sync({
            "event": "NEW_RELIEF_REQUEST",
            "data": req_data,
            "message": f"Urgent relief request {req_id} logged for 48 people in Bhavanipuram"
        })
        return {
            "status": "broadcasted",
            "event": "NEW_RELIEF_REQUEST",
            "data": req_data
        }

    else:

        # Default: Simulate realistic multilingual SOS distress report
        from app.models.sos import SOSReport
        from app.ai.sos_nlp import sos_nlp
        from app.routers.sos import build_sos_response

        simulation_messages = [
            ("మా కాలనీలో వరద నీరు 4 అడుగులు చేరింది, గర్భిణీ స్త్రీ ఉంది, వెంటనే రక్షించండి", "te", 16.4990, 80.6270),
            ("पानी बहुत तेज़ी से बढ़ रहा है, छत पर 5 लोग फंसे हैं, तुरंत नाव भेजो", "hi", 16.5110, 80.6040),
            ("Illu munigipothondi, ma babu ki high fever undi, emergency boat kavali", "te", 16.5240, 80.5970),
            ("வெள்ளம் வீட்டுக்குள் வந்துவிட்டது, 4 பேர் மாடியில் உள்ளோம், உதவி வேண்டும்", "ta", 16.4960, 80.6640),
            ("Severe water logging in Bhavanipuram, 3 elders trapped with no food or drinking water", "en", 16.5210, 80.5990)
        ]
        msg_text, default_lang, lat, lon = random.choice(simulation_messages)
        # Jitter coordinates slightly
        lat += random.uniform(-0.003, 0.003)
        lon += random.uniform(-0.003, 0.003)

        nlp_res = sos_nlp.process_sos(msg_text)
        sos = SOSReport(
            message=msg_text,
            language=nlp_res.detected_language or default_lang,
            need_type=nlp_res.need_type or "rescue",
            urgency=nlp_res.urgency or "critical",
            latitude=lat,
            longitude=lon,
            priority_score=nlp_res.priority_score or 90.0,
            status="SUBMITTED",
            timestamp=datetime.now(timezone.utc)
        )
        db.add(sos)
        db.commit()
        db.refresh(sos)

        sos_resp = build_sos_response(sos)
        sos_dict = sos_resp.model_dump()

        # Recalculate zone intelligence with the new emergency
        intel = risk_engine.analyze_all_zones(db, sync_to_db=True)
        intel_data = [z.model_dump() for z in intel]

        # Broadcast live events
        ws_manager.broadcast_sync({
            "event": "NEW_SOS",
            "data": sos_dict,
            "message": f"New live distress signal: {nlp_res.language_name} ({sos.urgency.upper()})"
        })
        ws_manager.broadcast_sync({
            "event": "ZONE_INTELLIGENCE_UPDATED",
            "data": intel_data
        })

        return {
            "status": "broadcasted",
            "event": "NEW_SOS",
            "data": sos_dict,
            "zones_updated": len(intel_data)
        }

