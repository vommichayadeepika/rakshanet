def test_health_check(client):
    """Verify health endpoint and database status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "healthy"
    assert "version" in data


def test_root_endpoint(client):
    """Verify root discovery endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"


def test_zones_crud(client):
    """Verify zone creation, listing, retrieval, and update."""
    payload = {
        "name": "Zone A - Krishna Riverfront",
        "latitude": 16.5062,
        "longitude": 80.6480,
        "population": 12500,
        "risk_score": 85.0,
        "risk_level": "RED",
        "priority_rank": 1,
        "recommended_action": "EVACUATE IMMEDIATELY",
        "active_sos_count": 4
    }
    create_resp = client.post("/zones", json=payload)
    assert create_resp.status_code == 201
    zone_data = create_resp.json()
    zone_id = zone_data["id"]
    assert zone_data["name"] == payload["name"]
    assert zone_data["risk_level"] == "RED"

    # Duplicate name should return 400
    dup_resp = client.post("/zones", json=payload)
    assert dup_resp.status_code == 400

    # List zones
    list_resp = client.get("/zones")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) == 1

    # Get single zone
    get_resp = client.get(f"/zones/{zone_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == zone_id

    # Update zone
    update_resp = client.patch(f"/zones/{zone_id}", json={"active_sos_count": 7, "risk_score": 92.0})
    assert update_resp.status_code == 200
    assert update_resp.json()["active_sos_count"] == 7
    assert update_resp.json()["risk_score"] == 92.0


def test_alerts_api(client):
    """Verify disaster alert ingestion and listing."""
    payload = {
        "source": "SACHET-NDMA",
        "alert_type": "Severe Flash Flood Warning",
        "severity": "SEVERE",
        "message": "Heavy downpour expected in Krishna catchment basin. Inundation likely in low-lying wards.",
        "latitude": 16.5100,
        "longitude": 80.6400,
        "radius": 15.0
    }
    create_resp = client.post("/alerts", json=payload)
    assert create_resp.status_code == 201

    # List alerts
    list_resp = client.get("/alerts")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1

    # Filter alerts by severity
    filter_resp = client.get("/alerts?severity=SEVERE")
    assert filter_resp.status_code == 200
    assert len(filter_resp.json()) >= 1


def test_drone_readings_api(client):
    """Verify drone road obstruction reading ingestion."""
    payload = {
        "latitude": 16.5020,
        "longitude": 80.6350,
        "obstacle_type": "flooded_road",
        "water_depth": 1.4,
        "road_status": "blocked",
        "confidence": 0.95
    }
    create_resp = client.post("/drone-readings", json=payload)
    assert create_resp.status_code == 201
    assert create_resp.json()["road_status"] == "blocked"

    # List readings
    list_resp = client.get("/drone-readings?road_status=blocked")
    assert list_resp.status_code == 200
    assert len(list_resp.json()) >= 1


def test_sos_reports_multilingual_and_urgency(client):
    """Verify SOS report creation in English, Telugu, and Hindi."""
    # English Medical SOS
    en_payload = {
        "message": "Water has entered our ground floor and grandmother needs insulin medicine immediately.",
        "latitude": 16.5055,
        "longitude": 80.6410
    }
    en_resp = client.post("/sos", json=en_payload)
    assert en_resp.status_code == 201
    en_data = en_resp.json()
    assert en_data["need_type"] == "medical"
    assert en_data["urgency"] == "critical"
    assert en_data["priority_score"] >= 90.0

    # Telugu SOS
    te_payload = {
        "message": "మా ఇంట్లోకి నీళ్లు వచ్చాయి, మా అమ్మకు మందులు కావాలి.",
        "latitude": 16.5070,
        "longitude": 80.6420
    }
    te_resp = client.post("/sos", json=te_payload)
    assert te_resp.status_code == 201
    te_data = te_resp.json()
    assert te_data["language"] == "te"

    # Hindi SOS
    hi_payload = {
        "message": "हमारे घर में पानी आ गया है और हमें तुरंत मदद चाहिए, हम छत पर फंसे हैं।",
        "latitude": 16.5080,
        "longitude": 80.6430
    }
    hi_resp = client.post("/sos", json=hi_payload)
    assert hi_resp.status_code == 201
    hi_data = hi_resp.json()
    assert hi_data["language"] == "hi"

    # Update SOS status
    sos_id = en_data["id"]
    patch_resp = client.patch(f"/sos/{sos_id}", json={"status": "EN_ROUTE"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "EN_ROUTE"


def test_rescue_teams_api(client):
    """Verify rescue team registration and dispatch."""
    payload = {
        "name": "NDRF Rescue Team 04",
        "task": "Inflatable Boat Evacuation",
        "status": "AVAILABLE",
        "latitude": 16.5150,
        "longitude": 80.6300,
        "member_count": 6
    }
    create_resp = client.post("/teams", json=payload)
    assert create_resp.status_code == 201
    team_id = create_resp.json()["id"]

    # Dispatch team
    patch_resp = client.patch(f"/teams/{team_id}", json={"status": "EN_ROUTE", "task": "Evacuating Zone A"})
    assert patch_resp.status_code == 200
    assert patch_resp.json()["status"] == "EN_ROUTE"


def test_zone_intelligence_endpoint(client):
    """Verify the core GET /zone-intelligence endpoint schema and trajectory outputs."""
    client.post("/zones", json={
        "name": "Zone B - Autonagar Lowlands",
        "latitude": 16.4950,
        "longitude": 80.6600,
        "population": 18000,
        "risk_score": 88.0,
        "risk_level": "RED",
        "priority_rank": 1,
        "recommended_action": "EVACUATE IMMEDIATELY",
        "active_sos_count": 5
    })

    resp = client.get("/zone-intelligence")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    zone_int = data[0]
    assert zone_int["zone_name"] == "Zone B - Autonagar Lowlands"
    assert zone_int["risk_score"] == 88.0
    assert "trajectory" in zone_int
    assert "3h" in zone_int["trajectory"]
    assert "6h" in zone_int["trajectory"]
    assert "24h" in zone_int["trajectory"]
    assert isinstance(zone_int["reasoning"], list)
    assert len(zone_int["reasoning"]) > 0


def test_simulate_flood_endpoint(client):
    """Verify simulate flood endpoint responds cleanly."""
    resp = client.post("/simulate-flood")
    assert resp.status_code == 200
    assert resp.json()["status"] == "initiated"


def test_situation_report_export(client):
    """Verify CSV and JSON situation report generation."""
    csv_resp = client.get("/reports/export?format=csv")
    assert csv_resp.status_code == 200
    assert "text/csv" in csv_resp.headers["content-type"]
    assert "RAKSHANET DISASTER SITUATION REPORT" in csv_resp.text

    json_resp = client.get("/reports/export?format=json")
    assert json_resp.status_code == 200
    json_data = json_resp.json()
    assert "summary" in json_data
    assert "zones" in json_data
