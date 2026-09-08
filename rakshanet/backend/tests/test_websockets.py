import json
import pytest
from app.websocket.manager import ws_manager


def test_websocket_connect_and_ping(client):
    """Verify that a client can connect to /ws and exchange ping/pong messages."""
    with client.websocket_connect("/ws") as websocket:
        # Receive initial greeting
        data = websocket.receive_json()
        assert data["event"] == "CONNECTED"
        assert "active_clients" in data

        # Send ping
        websocket.send_json({"action": "ping"})
        response = websocket.receive_json()
        assert response["event"] == "PONG"
        assert "timestamp" in response


def test_websocket_broadcast_on_sos_submission(client):
    """Verify that submitting an SOS report broadcasts NEW_SOS event to connected websockets."""
    with client.websocket_connect("/ws") as websocket:
        # Consume greeting
        greeting = websocket.receive_json()
        assert greeting["event"] == "CONNECTED"

        # Post a new citizen SOS distress report
        sos_payload = {
            "message": "Water entered house, urgent insulin needed for grandmother",
            "latitude": 16.501,
            "longitude": 80.621
        }
        res = client.post("/sos", json=sos_payload)
        assert res.status_code == 201

        # Receive broadcast over websocket
        msg = websocket.receive_json()
        assert msg["event"] == "NEW_SOS"
        assert "data" in msg
        assert msg["data"]["message"] == sos_payload["message"]
        assert msg["data"]["structured_extraction"]["need_type"] == "medical"
        assert msg["data"]["urgency"] == "critical"


def test_websocket_broadcast_on_zone_recalculation(client):
    """Verify that triggering risk recalculation broadcasts ZONE_INTELLIGENCE_UPDATED."""
    client.post("/demo/seed")
    with client.websocket_connect("/ws") as websocket:
        greeting = websocket.receive_json()
        assert greeting["event"] == "CONNECTED"

        # Trigger AI risk recalculation
        res = client.post("/zone-intelligence/recalculate")
        assert res.status_code == 200

        # Receive broadcast over websocket
        msg = websocket.receive_json()
        assert msg["event"] == "ZONE_INTELLIGENCE_UPDATED"
        assert isinstance(msg["data"], list)
        assert len(msg["data"]) > 0
        assert "risk_score" in msg["data"][0]



def test_simulate_live_event_endpoint(client):
    """Verify the demo live incident simulation endpoint triggers live websocket broadcasts."""
    with client.websocket_connect("/ws") as websocket:
        greeting = websocket.receive_json()
        assert greeting["event"] == "CONNECTED"

        # 1. Test live SOS event simulation
        res = client.post("/demo/simulate-live-event?event_type=sos")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "broadcasted"
        assert data["event"] == "NEW_SOS"

        # Check websocket received the live SOS broadcast
        msg1 = websocket.receive_json()
        assert msg1["event"] == "NEW_SOS"

        # Check websocket received the followed risk update broadcast
        msg2 = websocket.receive_json()
        assert msg2["event"] == "ZONE_INTELLIGENCE_UPDATED"


def test_simulate_live_drone_event(client):
    """Verify live drone blockage simulation broadcasts NEW_DRONE_READING and risk updates."""
    with client.websocket_connect("/ws") as websocket:
        greeting = websocket.receive_json()
        assert greeting["event"] == "CONNECTED"

        # Trigger drone event
        res = client.post("/demo/simulate-live-event?event_type=drone")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "broadcasted"
        assert data["event"] == "NEW_DRONE_READING"

        # Websocket receives drone reading broadcast
        msg1 = websocket.receive_json()
        assert msg1["event"] == "NEW_DRONE_READING"
        assert msg1["data"]["road_status"] == "blocked"

        # Websocket receives updated zone risk
        msg2 = websocket.receive_json()
        assert msg2["event"] == "ZONE_INTELLIGENCE_UPDATED"
