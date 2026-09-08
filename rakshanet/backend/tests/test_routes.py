"""
Phase 7 Tests – Drone Route Intelligence & Safe Evacuation Pathfinding.
Tests cover:
  - GET /routes/evacuation  (all zones and single-zone filter)
  - GET /routes/drone-recon
  - GET /routes/safe-shelters
  - POST /routes/calculate
  - Hazard avoidance and schema validity
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


# -----------------------------------------------------------------------
# Helper
# -----------------------------------------------------------------------

def seed_demo():
    """Ensure the DB has demo data before route tests."""
    resp = client.post("/demo/seed")
    assert resp.status_code == 200, f"Demo seed failed: {resp.text}"


# -----------------------------------------------------------------------
# GET /routes/safe-shelters
# -----------------------------------------------------------------------

class TestSafeShelters:
    def test_returns_list(self):
        resp = client.get("/routes/safe-shelters")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    def test_shelter_schema(self):
        resp = client.get("/routes/safe-shelters")
        shelters = resp.json()
        required = {
            "shelter_id", "name", "latitude", "longitude",
            "capacity", "current_occupancy", "elevation_meters",
            "status", "medical_facility", "food_water_supply"
        }
        for shelter in shelters:
            for field in required:
                assert field in shelter, f"Missing field '{field}' in shelter: {shelter}"

    def test_three_shelters_present(self):
        resp = client.get("/routes/safe-shelters")
        shelters = resp.json()
        assert len(shelters) == 3

    def test_shelter_coordinates_valid(self):
        resp = client.get("/routes/safe-shelters")
        for s in resp.json():
            assert isinstance(s["latitude"], float)
            assert isinstance(s["longitude"], float)
            # All shelters should be near Vijayawada area
            assert 16.0 <= s["latitude"] <= 17.5
            assert 80.0 <= s["longitude"] <= 81.5

    def test_tadepalli_is_highest_capacity(self):
        resp = client.get("/routes/safe-shelters")
        shelters = resp.json()
        capacities = {s["shelter_id"]: s["capacity"] for s in shelters}
        assert capacities.get("S_TADEPALLI", 0) >= 10000

    def test_shelter_status_open(self):
        resp = client.get("/routes/safe-shelters")
        for s in resp.json():
            assert s["status"] in ("OPEN", "FULL", "CLOSED")


# -----------------------------------------------------------------------
# GET /routes/drone-recon
# -----------------------------------------------------------------------

class TestDroneRecon:
    def setup_method(self):
        seed_demo()

    def test_returns_list(self):
        resp = client.get("/routes/drone-recon")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_two_missions_returned(self):
        resp = client.get("/routes/drone-recon")
        assert len(resp.json()) == 2

    def test_mission_schema(self):
        resp = client.get("/routes/drone-recon")
        required = {
            "mission_id", "drone_callsign", "base_hub",
            "flight_path", "waypoints", "total_distance_km",
            "estimated_flight_minutes", "priority_targets", "mission_objective"
        }
        for mission in resp.json():
            for field in required:
                assert field in mission, f"Missing field '{field}' in mission: {mission}"

    def test_mission_ids(self):
        resp = client.get("/routes/drone-recon")
        ids = {m["mission_id"] for m in resp.json()}
        assert "DRONE-RECON-ALPHA" in ids
        assert "DRONE-RECON-BRAVO" in ids

    def test_flight_path_is_polyline(self):
        resp = client.get("/routes/drone-recon")
        for mission in resp.json():
            fp = mission["flight_path"]
            assert isinstance(fp, list)
            assert len(fp) >= 2
            for coord in fp:
                assert isinstance(coord, list)
                assert len(coord) == 2
                lat, lon = coord
                assert isinstance(lat, float)
                assert isinstance(lon, float)

    def test_waypoints_have_instructions(self):
        resp = client.get("/routes/drone-recon")
        for mission in resp.json():
            for wp in mission["waypoints"]:
                assert "latitude" in wp
                assert "longitude" in wp
                assert "instruction" in wp

    def test_flight_duration_positive(self):
        resp = client.get("/routes/drone-recon")
        for mission in resp.json():
            assert mission["estimated_flight_minutes"] > 0
            assert mission["total_distance_km"] > 0


# -----------------------------------------------------------------------
# GET /routes/evacuation
# -----------------------------------------------------------------------

class TestEvacuationRoutes:
    def setup_method(self):
        seed_demo()

    def test_returns_list(self):
        resp = client.get("/routes/evacuation")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_routes_returned_for_seeded_zones(self):
        resp = client.get("/routes/evacuation")
        # With 7 zones seeded (zone 7 is skipped as safe haven), expect ≥1 route
        assert len(resp.json()) >= 1

    def test_evacuation_route_schema(self):
        resp = client.get("/routes/evacuation")
        required = {
            "route_id", "origin_zone_id", "origin_name",
            "destination_shelter_id", "destination_name",
            "waypoints", "distance_km", "estimated_time_minutes",
            "safety_score", "status", "hazards_avoided", "corridor_notes"
        }
        for route in resp.json():
            for field in required:
                assert field in route, f"Missing field '{field}' in route: {route}"

    def test_waypoints_are_valid_coordinates(self):
        resp = client.get("/routes/evacuation")
        for route in resp.json():
            assert isinstance(route["waypoints"], list)
            assert len(route["waypoints"]) >= 2
            for coord in route["waypoints"]:
                assert isinstance(coord, list)
                assert len(coord) == 2
                lat, lon = coord
                assert 14.0 <= lat <= 20.0, f"Unexpected latitude: {lat}"
                assert 78.0 <= lon <= 85.0, f"Unexpected longitude: {lon}"

    def test_safety_score_range(self):
        resp = client.get("/routes/evacuation")
        for route in resp.json():
            score = route["safety_score"]
            assert 0.0 <= score <= 100.0, f"Safety score out of range: {score}"

    def test_status_values(self):
        valid = {"OPTIMAL_SAFE", "CAUTION_RESTRICTED", "IMPASSABLE"}
        resp = client.get("/routes/evacuation")
        for route in resp.json():
            assert route["status"] in valid, f"Unexpected status: {route['status']}"

    def test_distance_and_time_positive(self):
        resp = client.get("/routes/evacuation")
        for route in resp.json():
            assert route["distance_km"] > 0
            assert route["estimated_time_minutes"] > 0

    def test_single_zone_filter(self):
        resp = client.get("/routes/evacuation?zone_id=1")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        # If a route is found it must be from zone 1
        for route in data:
            assert route["origin_zone_id"] == 1

    def test_filter_nonexistent_zone_returns_empty(self):
        resp = client.get("/routes/evacuation?zone_id=999")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_destination_is_known_shelter(self):
        valid_shelters = {"S_TADEPALLI", "S_KANAKADURGA", "S_AUTONAGAR_HIGH"}
        resp = client.get("/routes/evacuation")
        for route in resp.json():
            assert route["destination_shelter_id"] in valid_shelters

    def test_route_ids_are_unique(self):
        resp = client.get("/routes/evacuation")
        ids = [r["route_id"] for r in resp.json()]
        assert len(ids) == len(set(ids)), "Duplicate route IDs detected"


# -----------------------------------------------------------------------
# POST /routes/calculate  (Custom route)
# -----------------------------------------------------------------------

class TestCustomRoute:
    def setup_method(self):
        seed_demo()

    def test_basic_custom_route(self):
        payload = {
            "origin_lat": 16.5091,
            "origin_lon": 80.6034,
            "destination_lat": 16.4800,
            "destination_lon": 80.6020,
            "vehicle_type": "rescue_truck"
        }
        resp = client.post("/routes/calculate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert "route_id" in data
        assert "waypoints" in data
        assert len(data["waypoints"]) >= 2

    def test_ambulance_route(self):
        payload = {
            "origin_lat": 16.4950,
            "origin_lon": 80.6650,
            "destination_lat": 16.5170,
            "destination_lon": 80.6120,
            "vehicle_type": "ambulance"
        }
        resp = client.post("/routes/calculate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["estimated_time_minutes"] > 0
        assert data["distance_km"] > 0

    def test_custom_route_schema_complete(self):
        payload = {
            "origin_lat": 16.5230,
            "origin_lon": 80.5980,
            "destination_lat": 16.4870,
            "destination_lon": 80.6720,
        }
        resp = client.post("/routes/calculate", json=payload)
        assert resp.status_code == 200
        required = {
            "route_id", "origin_zone_id", "origin_name",
            "destination_shelter_id", "destination_name",
            "waypoints", "distance_km", "estimated_time_minutes",
            "safety_score", "status"
        }
        for field in required:
            assert field in resp.json(), f"Missing field: {field}"

    def test_missing_required_fields_returns_422(self):
        # Omit destination coordinates
        payload = {"origin_lat": 16.5, "origin_lon": 80.6}
        resp = client.post("/routes/calculate", json=payload)
        assert resp.status_code == 422

    def test_default_vehicle_type(self):
        payload = {
            "origin_lat": 16.5091,
            "origin_lon": 80.6034,
            "destination_lat": 16.4800,
            "destination_lon": 80.6020,
        }
        resp = client.post("/routes/calculate", json=payload)
        assert resp.status_code == 200


# -----------------------------------------------------------------------
# Phase 7 Feature Enhancements: Alternative Routes, Risk Levels & Live WS
# -----------------------------------------------------------------------

class TestPhase7Enhancements:
    def setup_method(self):
        seed_demo()

    def test_alternative_route_present_and_valid(self):
        resp = client.get("/routes/evacuation")
        assert resp.status_code == 200
        routes = resp.json()
        assert len(routes) >= 1

        # Check alternative route on at least one sector
        has_alt = False
        for route in routes:
            assert "route_risk_level" in route
            assert route["route_risk_level"] in ("LOW", "MODERATE", "HIGH")

            if route.get("alternative_route") is not None:
                has_alt = True
                alt = route["alternative_route"]
                assert "destination_shelter_id" in alt
                assert "destination_name" in alt
                assert "waypoints" in alt
                assert "distance_km" in alt
                assert "estimated_time_minutes" in alt
                assert "safety_score" in alt
                assert alt["distance_km"] > 0
                assert alt["estimated_time_minutes"] > 0
                assert 0.0 <= alt["safety_score"] <= 100.0

        assert has_alt, "Expected at least one route to have a viable alternative shelter path"

    def test_recalculate_routes_endpoint(self):
        resp = client.post("/routes/recalculate")
        assert resp.status_code == 200
        routes = resp.json()
        assert isinstance(routes, list)
        assert len(routes) >= 1
        for r in routes:
            assert "route_id" in r
            assert "safety_score" in r
            assert "route_risk_level" in r

    def test_simulate_live_event_route_recalculation(self):
        resp = client.post("/demo/simulate-live-event?event_type=route")
        assert resp.status_code == 200
        data = resp.json()
        assert data["event"] == "ROUTES_UPDATED"
        assert data["routes_count"] >= 1

