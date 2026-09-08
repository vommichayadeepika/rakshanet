import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.websocket.manager import ws_manager
from app.database import SessionLocal
from app.ai.risk_engine import risk_engine

logger = logging.getLogger("rakshanet.websocket")
ws_router = APIRouter(tags=["WebSockets"])


@ws_router.websocket("/ws")
@ws_router.websocket("/ws/live")
async def live_websocket_endpoint(websocket: WebSocket):
    """
    Real-time bidirectional WebSocket connection for RakshaNet Command Center.
    Pushes instantaneous alerts:
    - NEW_SOS: Incoming citizen distress signals enriched with NLP
    - ZONE_INTELLIGENCE_UPDATED: Recalculated flood risk scores & action priorities
    - DRONE_READING: Aerial road blockage telemetry
    - DEMO_DATA_REFRESHED: Reset/seeding events
    """
    await ws_manager.connect(websocket)
    try:
        # Greet newly connected client
        await ws_manager.send_personal_message({
            "event": "CONNECTED",
            "message": "Connected to RakshaNet Live Incident Grid",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "active_clients": ws_manager.count
        }, websocket)

        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                action = msg.get("action")

                if action == "ping":
                    await ws_manager.send_personal_message({
                        "event": "PONG",
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }, websocket)

                elif action == "recalculate":
                    # Trigger instant risk calculation and broadcast to all connected dashboards
                    db = SessionLocal()
                    try:
                        intel = risk_engine.analyze_all_zones(db, sync_to_db=True)
                        intel_data = [z.model_dump() for z in intel]
                        await ws_manager.broadcast({
                            "event": "ZONE_INTELLIGENCE_UPDATED",
                            "data": intel_data,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })

                        # Phase 7: Automatically broadcast updated evacuation routes
                        from app.ai.route_engine import route_engine
                        routes = route_engine.get_safe_evacuation_routes(db)
                        routes_data = [r.model_dump() for r in routes]
                        await ws_manager.broadcast({
                            "event": "ROUTES_UPDATED",
                            "data": routes_data,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                    finally:
                        db.close()

                elif action == "recalculate_routes":
                    # Phase 7: Dedicated live route recalculation action
                    db = SessionLocal()
                    try:
                        from app.ai.route_engine import route_engine
                        routes = route_engine.get_safe_evacuation_routes(db)
                        routes_data = [r.model_dump() for r in routes]
                        await ws_manager.broadcast({
                            "event": "ROUTES_UPDATED",
                            "data": routes_data,
                            "timestamp": datetime.now(timezone.utc).isoformat()
                        })
                    finally:
                        db.close()


                elif action == "get_status":
                    await ws_manager.send_personal_message({
                        "event": "STATUS",
                        "active_clients": ws_manager.count,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }, websocket)

            except json.JSONDecodeError:
                await ws_manager.send_personal_message({
                    "event": "ERROR",
                    "message": "Malformed JSON payload"
                }, websocket)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket session error: {e}")
        ws_manager.disconnect(websocket)
