import pytest
from app.ai.sos_nlp import sos_nlp, MultilingualSOSNLP


def test_language_detection():
    """Verify script and transliteration detection across all 6 target languages."""
    # English
    lang, name, trans = sos_nlp.detect_language("We need a rescue boat immediately, water is rising.")
    assert lang == "en"
    assert not trans

    # Telugu (Native)
    lang, name, trans = sos_nlp.detect_language("మా ఇంట్లోకి నీళ్లు వచ్చాయి, మా అమ్మకు మందులు కావాలి.")
    assert lang == "te"
    assert not trans

    # Hindi (Native)
    lang, name, trans = sos_nlp.detect_language("हमारे घर में पानी भर गया है और मेरी माँ को दवा चाहिए।")
    assert lang == "hi"
    assert not trans

    # Tamil (Native)
    lang, name, trans = sos_nlp.detect_language("எங்கள் வீட்டின் தரைத்தளத்தில் தண்ணீர் புகுந்துவிட்டது, படகு தேவை.")
    assert lang == "ta"
    assert not trans

    # Kannada (Native)
    lang, name, trans = sos_nlp.detect_language("ನಮ್ಮ ಮನೆಯೊಳಗೆ ಪ್ರವಾಹದ ನೀರು ನುಗ್ಗಿದೆ, ದಯವಿಟ್ಟು ಕಾಪಾಡಿ.")
    assert lang == "kn"
    assert not trans

    # Malayalam (Native)
    lang, name, trans = sos_nlp.detect_language("വീട്ടിൽ വെള്ളം കയറി, പെട്ടെന്ന് രക്ഷിക്കൂ!")
    assert lang == "ml"
    assert not trans

    # Telugu Transliterated in Roman Script
    lang, name, trans = sos_nlp.detect_language("Maa intloki neellu vachayi, ammaku mandulu kavali.")
    assert lang == "te"
    assert trans

    # Hindi Transliterated in Roman Script (Hinglish)
    lang, name, trans = sos_nlp.detect_language("Ghar mein paani ghus gaya hai, bachao jaldi!")
    assert lang == "hi"
    assert trans


def test_need_type_extraction():
    """Verify classification of emergency needs across languages."""
    # Medical
    res = sos_nlp.process_sos("Grandmother is bedridden with heart condition and needs insulin doctor immediately.")
    assert res.need_type == "medical"
    assert "heart" in res.extracted_keywords or "insulin" in res.extracted_keywords

    # Rescue
    res = sos_nlp.process_sos("Water reached terrace, 6 people trapped on roof!")
    assert res.need_type == "rescue"

    # Drinking water
    res = sos_nlp.process_sos("మాకు తాగడానికి మంచి నీళ్లు లేవు, దాహంతో అల్లాడుతున్నాం.")
    assert res.need_type == "water"

    # Food
    res = sos_nlp.process_sos("छोटे बच्चों के लिए दूध और खाना खत्म हो गया है।")
    assert res.need_type == "food"

    # Evacuation
    res = sos_nlp.process_sos("Road is completely blocked, please evacuate our family.")
    assert res.need_type == "evacuation"


def test_people_count_extraction():
    """Verify parsing of explicit numbers and quantity words."""
    # English explicit digits
    assert sos_nlp.extract_people_count("There are 8 people stuck on the second floor.") == 8

    # Hindi digits
    assert sos_nlp.extract_people_count("छत पर 5 लोग फंसे हैं।") == 5

    # Telugu digits
    assert sos_nlp.extract_people_count("మేము 7 మందిమి పైకప్పుపై ఉన్నాము.") == 7

    # Word terms
    assert sos_nlp.extract_people_count("My family is trapped here.") == 4
    assert sos_nlp.extract_people_count("Single person here.") == 1


def test_danger_factors_and_critical_urgency():
    """Verify life-threatening danger triggers elevate urgency and priority score."""
    # Critical life danger
    res = sos_nlp.process_sos(
        "Flood water rising fast, pregnant woman in labor trapped on roof with 2 infants. Send boat urgently!"
    )
    assert res.is_life_threatening
    assert res.urgency == "critical"
    assert res.priority_score >= 90.0
    assert "trapped_above_water" in res.danger_factors
    assert "vulnerable_infant_or_pregnant" in res.danger_factors

    # Non-critical request
    res_mild = sos_nlp.process_sos("Requesting dry food packet when convenient, safe on second floor.")
    assert not res_mild.is_life_threatening
    assert res_mild.urgency in ["medium", "low"]
    assert res_mild.priority_score < 70.0


def test_location_mentions_extraction():
    """Verify extraction of building levels and landmarks."""
    res = sos_nlp.process_sos(
        "Water entered ground floor, moving to terrace near Krishnalanka sluice gate and hospital."
    )
    locations_lower = [loc.lower() for loc in res.location_mentions]
    assert any("ground floor" in loc or "terrace" in loc for loc in locations_lower)
    assert any("krishnalanka" in loc or "hospital" in loc or "sluice gate" in loc for loc in locations_lower)


def test_sos_analyze_api_endpoint(client):
    """Verify POST /sos/analyze endpoint processes multilingual messages on the fly."""
    # Test Tamil message via API
    ta_payload = {
        "message": "எங்கள் வீட்டின் தரைத்தளத்தில் தண்ணீர் புகுந்துவிட்டது, 4 பேர் மாட்டிக்கொண்டோம், உடனடியாக படகு தேவை."
    }
    resp = client.post("/sos/analyze", json=ta_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["detected_language"] == "ta"
    assert data["language_name"] == "Tamil"
    assert data["need_type"] == "rescue"
    assert data["urgency"] == "critical"
    assert data["people_count"] == 4
    assert data["priority_score"] >= 90.0

    # Test Transliterated Telugu via API
    te_trans_payload = {
        "message": "Maa intloki neellu vachayi, amma ki BP and diabetes mandulu urgent ga kavali please help!"
    }
    resp_te = client.post("/sos/analyze", json=te_trans_payload)
    assert resp_te.status_code == 200
    data_te = resp_te.json()
    assert data_te["detected_language"] == "te"
    assert data_te["is_transliterated"] is True
    assert data_te["need_type"] == "medical"
    assert data_te["urgency"] == "critical"


def test_sos_submission_enriches_with_nlp(client):
    """Verify that POST /sos persists the report with NLP-derived need, urgency, and score."""
    payload = {
        "message": "नहर का बांध टूट गया है, 6 लोग छत पर फंसे हैं, तुरंत रेस्क्यू बोट चाहिए!",
        "latitude": 16.5010,
        "longitude": 80.6250
    }
    create_resp = client.post("/sos", json=payload)
    assert create_resp.status_code == 201
    data = create_resp.json()
    assert data["language"] == "hi"
    assert data["need_type"] == "rescue"
    assert data["urgency"] == "critical"
    assert data["priority_score"] >= 90.0
    assert "structured_extraction" in data
    assert data["structured_extraction"]["detected_language"] == "hi"
    assert data["structured_extraction"]["people_count"] == 6

    # Verify retrieval preserves structured intelligence
    sos_id = data["id"]
    get_resp = client.get(f"/sos/{sos_id}")
    assert get_resp.status_code == 200
    get_data = get_resp.json()
    assert get_data["id"] == sos_id
    assert get_data["structured_extraction"]["people_count"] == 6
