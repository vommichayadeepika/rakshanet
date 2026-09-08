import pytest
from app.ai.risk_engine import risk_engine, haversine_distance_km
from app.models.zone import Zone
from app.models.environmental import EnvironmentalReading
from app.models.sos import SOSReport
from app.models.drone import DroneReading
from app.models.alert import Alert


def test_haversine_distance():
    """Verify distance calculation between coordinates."""
    # Krishna Barrage to Bhavanipuram ~ 1.6 km
    d = haversine_distance_km(16.5091, 80.6034, 16.5230, 80.5980)
    assert 1.2 <= d <= 2.2


def test_risk_engine_environmental_hazard():
    """Verify hazard score scales with rainfall and river levels."""
    # Extreme surge
    extreme_env = EnvironmentalReading(
        zone_id=1,
        rainfall_intensity=95.0,
        cumulative_rainfall=260.0,
        river_level=19.5,
        danger_level=17.5,
        water_level_change_rate=0.75,
        water_depth=1.8
    )
    hazard, rain_c, river_c, rate = risk_engine.calculate_environmental_hazard(extreme_env)
    assert hazard >= 80.0
    assert rain_c >= 80.0
    assert river_c >= 80.0
    assert rate == 0.75

    # Calm baseline
    calm_env = EnvironmentalReading(
        zone_id=2,
        rainfall_intensity=5.0,
        cumulative_rainfall=10.0,
        river_level=12.0,
        danger_level=17.5,
        water_level_change_rate=0.0,
        water_depth=0.0
    )
    calm_hazard, calm_rain, calm_river, _ = risk_engine.calculate_environmental_hazard(calm_env)
    assert calm_hazard <= 20.0


def test_risk_engine_recommended_actions():
    """Verify explainable rule-based action triggers."""
    # Severe conditions -> Evacuate
    action_evac = risk_engine.determine_recommended_action(
        risk_score=92.0,
        critical_sos=3,
        medical_sos=1,
        has_trapped=True,
        blocked_roads=2,
        water_depth=1.8
    )
    assert action_evac == "EVACUATE IMMEDIATELY"

    # Medical distress priority
    action_med = risk_engine.determine_recommended_action(
        risk_score=60.0,
        critical_sos=1,
        medical_sos=1,
        has_trapped=False,
        blocked_roads=0,
        water_depth=0.5
    )
    assert action_med == "SEND MEDICAL ASSISTANCE"

    # Trapped / rescue priority
    action_rescue = risk_engine.determine_recommended_action(
        risk_score=76.0,
        critical_sos=0,
        medical_sos=0,
        has_trapped=True,
        blocked_roads=0,
        water_depth=0.8
    )
    assert action_rescue == "DISPATCH RESCUE TEAM"

    # Moderate conditions -> Relief pre-position
    action_relief = risk_engine.determine_recommended_action(
        risk_score=58.0,
        critical_sos=0,
        medical_sos=0,
        has_trapped=False,
        blocked_roads=0,
        water_depth=0.4
    )
    assert action_relief == "PRE-POSITION RELIEF SUPPLIES"

    # Low risk -> Safe/No action
    action_safe = risk_engine.determine_recommended_action(
        risk_score=15.0,
        critical_sos=0,
        medical_sos=0,
        has_trapped=False,
        blocked_roads=0,
        water_depth=0.0
    )
    assert action_safe == "NO IMMEDIATE ACTION"


def test_zone_intelligence_api_with_seeded_data(client):
    """Verify /zone-intelligence API returns ranked zones with full score breakdown and reasoning."""
    # Seed full mock scenario
    client.post("/demo/seed")

    resp = client.get("/zone-intelligence")
    assert resp.status_code == 200
    zones = resp.json()
    assert len(zones) == 7

    # Verify ranking is strictly sequential 1..7
    ranks = [z["response_priority_rank"] for z in zones]
    assert ranks == [1, 2, 3, 4, 5, 6, 7]

    # Priority 1 must have high priority score and RED risk level
    top_zone = zones[0]
    assert top_zone["response_priority_score"] >= 70.0
    assert top_zone["risk_level"] in ["RED", "ORANGE"]
    assert top_zone["recommended_action"] in ["EVACUATE IMMEDIATELY", "DISPATCH RESCUE TEAM"]
    assert top_zone["overall_trajectory"] in ["worsening", "stable", "improving"]
    assert top_zone["trajectory"]["trend"] in ["worsening", "stable", "improving"]
    assert "3h" in top_zone["trajectory"]
    assert "6h" in top_zone["trajectory"]
    assert "24h" in top_zone["trajectory"]

    # Verify score breakdown fields
    sb = top_zone["score_breakdown"]
    assert "hazard_score" in sb
    assert "rainfall_component" in sb
    assert "river_component" in sb
    assert "alert_component" in sb
    assert "sos_urgency_component" in sb
    assert "isolation_component" in sb
    assert "population_component" in sb
    assert "data_freshness_factor" in sb
    assert 0.0 <= sb["data_freshness_factor"] <= 1.0

    # Verify explainable reasoning
    assert isinstance(top_zone["reasoning"], list)
    assert len(top_zone["reasoning"]) > 0

    # Verify human confirmation disclaimer
    assert "incident commander" in top_zone["disclaimer"].lower() or "human" in top_zone["disclaimer"].lower()


def test_single_zone_intelligence_endpoint(client):
    """Verify retrieving detailed intelligence for a single zone by ID."""
    client.post("/demo/seed")
    zones = client.get("/zones").json()
    first_zone_id = zones[0]["id"]

    resp = client.get(f"/zone-intelligence/{first_zone_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["zone_id"] == first_zone_id
    assert "risk_score" in data
    assert "score_breakdown" in data

    # 404 on non-existent zone
    resp_404 = client.get("/zone-intelligence/99999")
    assert resp_404.status_code == 404


def test_recalculate_zone_intelligence_syncs_db(client):
    """Verify POST /zone-intelligence/recalculate persists calculated scores to Zone table."""
    client.post("/demo/seed")

    recalc_resp = client.post("/zone-intelligence/recalculate")
    assert recalc_resp.status_code == 200
    intel_data = recalc_resp.json()

    # Verify Zone table reflects the calculated scores
    zones_db = client.get("/zones").json()
    assert len(zones_db) == 7
    intel_map = {item["zone_id"]: item for item in intel_data}

    for z in zones_db:
        intel = intel_map[z["id"]]
        assert z["risk_score"] == intel["risk_score"]
        assert z["priority_rank"] == intel["response_priority_rank"]
        assert z["recommended_action"] == intel["recommended_action"]
