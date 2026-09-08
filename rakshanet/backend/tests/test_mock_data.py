def test_seed_demo_data_endpoint(client):
    """Verify that POST /demo/seed populates all correlated mock disaster data."""
    seed_resp = client.post("/demo/seed")
    assert seed_resp.status_code == 200
    data = seed_resp.json()
    assert data["status"] == "success"
    counts = data["counts"]
    assert counts["zones"] == 7
    assert counts["alerts"] == 5
    assert counts["drone_readings"] == 7
    assert counts["environmental_readings"] == 7
    assert counts["sos_reports"] == 20
    assert counts["teams"] == 4
    assert counts["users"] == 4


def test_demo_status_endpoint(client):
    """Verify that GET /demo/status returns accurate counts of active simulated entities."""
    client.post("/demo/seed")

    status_resp = client.get("/demo/status")
    assert status_resp.status_code == 200
    status_data = status_resp.json()
    assert status_data["status"] == "active"
    assert status_data["counts"]["zones"] == 7
    assert status_data["critical_sos_count"] >= 5
    assert status_data["blocked_roads_count"] >= 4
    assert status_data["red_zones_count"] >= 3


def test_environmental_readings_api(client):
    """Verify environmental telemetry endpoint and per-zone filtering."""
    client.post("/demo/seed")

    resp = client.get("/environmental-readings")
    assert resp.status_code == 200
    readings = resp.json()
    assert len(readings) == 7

    r1 = readings[0]
    assert "rainfall_intensity" in r1
    assert "cumulative_rainfall" in r1
    assert "river_level" in r1
    assert "danger_level" in r1
    assert "water_level_change_rate" in r1
    assert "water_depth" in r1

    zone_id = r1["zone_id"]
    filtered_resp = client.get(f"/environmental-readings?zone_id={zone_id}")
    assert filtered_resp.status_code == 200
    assert len(filtered_resp.json()) == 1
    assert filtered_resp.json()[0]["zone_id"] == zone_id


def test_multilingual_sos_diversity(client):
    """Verify that seeded SOS reports include English, Telugu, Hindi, Tamil, Kannada, and Malayalam."""
    client.post("/demo/seed")

    resp = client.get("/sos")
    assert resp.status_code == 200
    sos_list = resp.json()
    assert len(sos_list) == 20

    languages = {s["language"] for s in sos_list}
    assert "en" in languages
    assert "te" in languages
    assert "hi" in languages
    assert "ta" in languages
    assert "kn" in languages
    assert "ml" in languages

    need_types = {s["need_type"] for s in sos_list}
    assert "medical" in need_types
    assert "rescue" in need_types
    assert "water" in need_types or "food" in need_types

    urgencies = {s["urgency"] for s in sos_list}
    assert "critical" in urgencies
    assert "high" in urgencies


def test_drone_readings_seeded(client):
    """Verify that seeded drone readings capture road obstacles and passable routes."""
    client.post("/demo/seed")

    blocked_resp = client.get("/drone-readings?road_status=blocked")
    assert blocked_resp.status_code == 200
    blocked = blocked_resp.json()
    assert len(blocked) >= 4
    for b in blocked:
        assert b["water_depth"] > 0.8
        assert b["confidence"] >= 0.9

    passable_resp = client.get("/drone-readings?road_status=passable")
    assert passable_resp.status_code == 200
    passable = passable_resp.json()
    assert len(passable) >= 2


def test_alerts_seeded(client):
    """Verify that incoming disaster alerts from SACHET, IMD, and CWC are available."""
    client.post("/demo/seed")

    resp = client.get("/alerts")
    assert resp.status_code == 200
    alerts = resp.json()
    assert len(alerts) == 5

    sources = {a["source"] for a in alerts}
    assert "SACHET-NDMA" in sources
    assert "IMD" in sources
    assert "CWC" in sources


def test_demo_reset_endpoint(client):
    """Verify that POST /demo/reset cleans the database to 0 records."""
    client.post("/demo/seed")
    assert len(client.get("/zones").json()) == 7

    reset_resp = client.post("/demo/reset")
    assert reset_resp.status_code == 200
    assert reset_resp.json()["status"] == "cleared"

    status_resp = client.get("/demo/status")
    counts = status_resp.json()["counts"]
    for table, count in counts.items():
        assert count == 0, f"Table {table} was expected to be empty but had {count}"
