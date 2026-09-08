import pytest
from fastapi.testclient import TestClient
from app.simulation.mock_data import seed_mock_data


def test_relief_summary_empty(client: TestClient):
    """Test /relief/summary when database has no records."""
    response = client.get("/relief/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_affected_people" in data
    assert "total_camp_capacity" in data
    assert "total_relief_teams" in data
    assert "recovery_progress_percentage" in data
    assert data["total_camp_capacity"] == 0


def test_relief_summary_with_seeded_data(client: TestClient):
    """Test /relief/summary with full mock data seeded."""
    seed_res = client.post("/demo/seed")
    assert seed_res.status_code == 200

    response = client.get("/relief/summary")
    assert response.status_code == 200
    data = response.json()
    assert data["total_affected_people"] > 0
    assert data["total_camp_capacity"] >= 5000
    assert data["total_camp_occupancy"] > 0
    assert data["camp_occupancy_rate_pct"] > 0
    assert data["total_relief_teams"] >= 5
    assert data["recovery_progress_percentage"] > 0


def test_relief_camps_crud_and_status(client: TestClient):
    """Test GET, POST, PUT for relief camps with automatic status and capacity calculation."""
    camp_payload = {
        "name": "Test Vijayawada Stadium Camp",
        "location_name": "Indira Gandhi Stadium",
        "latitude": 16.5050,
        "longitude": 80.6400,
        "capacity": 5000,
        "current_occupancy": 1000,
        "available_beds": 4000,
        "food_availability": "Adequate",
        "water_availability": "Adequate",
        "medical_support": "Available",
        "contact_person": "Officer Sharma",
        "contact_phone": "+91 9988776655",
    }
    create_res = client.post("/relief/camps", json=camp_payload)
    assert create_res.status_code == 201
    created_camp = create_res.json()
    camp_id = created_camp["id"]
    assert created_camp["status"] == "Available"
    assert created_camp["available_beds"] == 4000

    get_res = client.get("/relief/camps")
    assert get_res.status_code == 200
    camps = get_res.json()
    assert len(camps) >= 1

    update_res = client.put(f"/relief/camps/{camp_id}", json={"current_occupancy": 4000})
    assert update_res.status_code == 200
    updated_camp = update_res.json()
    assert updated_camp["status"] == "Near Capacity"
    assert updated_camp["available_beds"] == 1000

    update_res2 = client.put(f"/relief/camps/{camp_id}", json={"current_occupancy": 4900})
    assert update_res2.status_code == 200
    updated_camp2 = update_res2.json()
    assert updated_camp2["status"] == "Full"
    assert updated_camp2["available_beds"] == 100


def test_relief_requests_priority_scoring(client: TestClient):
    """Test submitting relief requests and verifying automated priority scoring."""
    client.post("/demo/seed")

    req_payload = {
        "category": "Medical Emergency",
        "priority": "Critical",
        "people_count": 50,
        "location_name": "Krishnalanka Lowlands",
        "latitude": 16.4980,
        "longitude": 80.6280,
        "notes": "Patients stranded with diabetic shock and floodwater rising."
    }
    create_res = client.post("/relief/requests", json=req_payload)
    assert create_res.status_code == 201
    data = create_res.json()
    assert data["status"] == "Pending"
    assert data["priority_score"] >= 80.0
    assert "REQ-KD-" in data["request_code"]

    req_id = data["id"]

    update_res = client.put(f"/relief/requests/{req_id}", json={"status": "Assigned", "assigned_team_name": "Medical Unit 01"})
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "Assigned"
    assert update_res.json()["assigned_team_name"] == "Medical Unit 01"

    list_res = client.get("/relief/requests?status=Assigned")
    assert list_res.status_code == 200
    assert any(r["id"] == req_id for r in list_res.json())


def test_resource_inventory_and_low_stock(client: TestClient):
    """Test resource inventory retrieval, updates, and low-stock warnings."""
    client.post("/demo/seed")

    res = client.get("/relief/resources")
    assert res.status_code == 200
    resources = res.json()
    assert len(resources) >= 7

    first_item = resources[0]
    res_id = first_item["id"]
    assert "remaining_qty" in first_item
    assert "low_stock_warning" in first_item

    threshold = first_item["low_stock_threshold"]
    update_res = client.put(f"/relief/resources/{res_id}", json={"available_qty": threshold - 10})
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["available_qty"] == threshold - 10
    assert updated["low_stock_warning"] is True


def test_relief_teams_lifecycle(client: TestClient):
    """Test relief team listing and status updating."""
    client.post("/demo/seed")

    teams_res = client.get("/relief/teams")
    assert teams_res.status_code == 200
    teams = teams_res.json()
    assert len(teams) >= 6

    team = teams[0]
    team_id = team["id"]

    update_res = client.put(f"/relief/teams/{team_id}", json={"status": "Available", "assigned_task": "Base maintenance"})
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "Available"
    assert update_res.json()["assigned_task"] == "Base maintenance"


def test_recovery_tracking(client: TestClient):
    """Test infrastructure recovery tracking and 100% restored trigger."""
    client.post("/demo/seed")

    items_res = client.get("/relief/recovery")
    assert items_res.status_code == 200
    items = items_res.json()
    assert len(items) >= 8

    item = items[0]
    item_id = item["id"]

    update_res = client.put(f"/relief/recovery/{item_id}", json={"progress_pct": 100})
    assert update_res.status_code == 200
    assert update_res.json()["progress_pct"] == 100
    assert update_res.json()["recovery_status"] == "Restored"


def test_damage_assessments_endpoints(client: TestClient):
    """Test damage assessments listing, single zone retrieval, and update with score reclassification."""
    client.post("/demo/seed")

    list_res = client.get("/relief/damage-assessments")
    assert list_res.status_code == 200
    assessments = list_res.json()
    assert len(assessments) == 7

    crit_res = client.get("/relief/damage-assessments?severity=CRITICAL")
    assert crit_res.status_code == 200
    for a in crit_res.json():
        assert a["damage_severity"] == "CRITICAL"

    zone1_res = client.get("/relief/damage-assessments/1")
    assert zone1_res.status_code == 200
    zone1 = zone1_res.json()
    assert zone1["zone_id"] == 1
    assert "affected_people" in zone1
    assert "food_packets_needed" in zone1

    update_res = client.put("/relief/damage-assessments/1", json={
        "damage_severity": "CRITICAL",
        "affected_people": 25000,
        "injured_count": 80,
        "missing_count": 15
    })
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["damage_severity"] == "CRITICAL"
    assert updated["priority_score"] >= 80.0
    assert updated["priority_level"] == "CRITICAL"


def test_relief_fundraising_and_donations(client: TestClient):
    """Test fundraising campaign retrieval and simulated donation submission."""
    client.post("/demo/seed")

    # 1. Get campaign fund status
    fund_res = client.get("/relief/funds")
    assert fund_res.status_code == 200
    fund_data = fund_res.json()
    assert "target_amount" in fund_data
    assert "raised_amount" in fund_data
    assert "remaining_amount" in fund_data
    assert fund_data["target_amount"] == 50000000.0
    assert fund_data["raised_amount"] >= 24500000.0
    initial_raised = fund_data["raised_amount"]
    initial_donors = fund_data["donor_count"]

    # 2. Get donation list
    donations_res = client.get("/relief/donations")
    assert donations_res.status_code == 200
    donations = donations_res.json()
    assert len(donations) >= 4

    # 3. Post a simulated donation
    donate_payload = {
        "donor_name": "Tech Mahindra CSR",
        "amount": 250000.0,
        "category": "Medical Aid & Supplies",
        "message": "Direct contribution for flood-affected families in Vijayawada."
    }
    post_res = client.post("/relief/donations", json=donate_payload)
    assert post_res.status_code == 201
    donation_data = post_res.json()
    assert donation_data["amount"] == 250000.0
    assert "TXN-KD-" in donation_data["transaction_ref"]

    # 4. Verify fundraising campaign total increased
    updated_fund_res = client.get("/relief/funds")
    assert updated_fund_res.status_code == 200
    updated_fund = updated_fund_res.json()
    assert updated_fund["raised_amount"] == initial_raised + 250000.0
    assert updated_fund["donor_count"] == initial_donors + 1


def test_simulate_live_relief_event(client: TestClient):
    """Test simulating a live relief event broadcast via demo endpoint."""
    client.post("/demo/seed")

    res = client.post("/demo/simulate-live-event?event_type=relief")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "broadcasted"
    assert data["event"] == "NEW_RELIEF_REQUEST"
    assert "request_code" in data["data"]
