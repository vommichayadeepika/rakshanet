def test_dashboard_endpoint_serves_html(client):
    """Verify that /dashboard returns 200 OK and valid HTML containing React root and Leaflet."""
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    content = response.text
    assert 'id="root"' in content
    assert "RakshaNet" in content
    assert "leaflet" in content.lower()


def test_static_assets_served(client):
    """Verify that frontend static assets (CSS, JS) are properly served under /static."""
    css_res = client.get("/static/css/dashboard.css")
    assert css_res.status_code == 200
    assert "leaflet-container" in css_res.text

    js_res = client.get("/static/js/app.js")
    assert js_res.status_code == 200
    assert "RakshaNetApp" in js_res.text


def test_root_includes_dashboard_link(client):
    """Verify that root / includes discovery link to /dashboard while maintaining status online."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["dashboard"] == "/dashboard"


def test_zone_intelligence_returns_coordinates_for_map(client):
    """Verify that /zone-intelligence returns latitude and longitude required by Leaflet map."""
    client.post("/demo/seed")
    res = client.get("/zone-intelligence")
    assert res.status_code == 200
    data = res.json()
    assert len(data) == 7
    for zone in data:
        assert "latitude" in zone and isinstance(zone["latitude"], (int, float))
        assert "longitude" in zone and isinstance(zone["longitude"], (int, float))
        assert 16.40 <= zone["latitude"] <= 16.60
        assert 80.50 <= zone["longitude"] <= 80.75

