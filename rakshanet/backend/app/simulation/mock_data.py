from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from app.models.zone import Zone
from app.models.alert import Alert
from app.models.drone import DroneReading
from app.models.sos import SOSReport
from app.models.team import Team
from app.models.user import User
from app.models.environmental import EnvironmentalReading
from app.models.relief import (
    ReliefCamp,
    ReliefRequest,
    ResourceInventory,
    ReliefTeam,
    RecoveryItem,
    ZoneDamageAssessment,
    ReliefFund,
    ReliefDonation,
)



def utc_now():
    return datetime.now(timezone.utc)


# =====================================================================
# DEMONSTRATION GEOGRAPHY: KRISHNA DELTA RIVERINE BASIN (SIMULATION)
# Coordinates centered around 16.48°N - 16.53°N, 80.59°E - 80.68°E
# =====================================================================

MOCK_ZONES = [
    {
        "name": "Zone 1 - Krishna Barrage North",
        "latitude": 16.5091,
        "longitude": 80.6034,
        "population": 14200,
        "risk_score": 88.5,
        "risk_level": "RED",
        "priority_rank": 1,
        "recommended_action": "EVACUATE IMMEDIATELY",
        "active_sos_count": 6
    },
    {
        "name": "Zone 2 - Bhavanipuram Lowlands",
        "latitude": 16.5230,
        "longitude": 80.5980,
        "population": 22500,
        "risk_score": 84.0,
        "risk_level": "RED",
        "priority_rank": 2,
        "recommended_action": "DEPLOY RESCUE TEAM",
        "active_sos_count": 5
    },
    {
        "name": "Zone 3 - Krishnalanka Floodway",
        "latitude": 16.4980,
        "longitude": 80.6280,
        "population": 31000,
        "risk_score": 93.5,
        "risk_level": "RED",
        "priority_rank": 3,
        "recommended_action": "EVACUATE IMMEDIATELY",
        "active_sos_count": 8
    },
    {
        "name": "Zone 4 - Autonagar Sector 7",
        "latitude": 16.4950,
        "longitude": 80.6650,
        "population": 18400,
        "risk_score": 68.0,
        "risk_level": "ORANGE",
        "priority_rank": 4,
        "recommended_action": "PRE-POSITION RELIEF SUPPLIES",
        "active_sos_count": 4
    },
    {
        "name": "Zone 5 - Ramavarappadu Junction",
        "latitude": 16.5280,
        "longitude": 80.6720,
        "population": 16800,
        "risk_score": 48.0,
        "risk_level": "YELLOW",
        "priority_rank": 5,
        "recommended_action": "MONITOR CLOSELY",
        "active_sos_count": 2
    },
    {
        "name": "Zone 6 - Gunadala Hillside Corridor",
        "latitude": 16.5160,
        "longitude": 80.6550,
        "population": 19500,
        "risk_score": 35.0,
        "risk_level": "YELLOW",
        "priority_rank": 6,
        "recommended_action": "NO IMMEDIATE ACTION",
        "active_sos_count": 1
    },
    {
        "name": "Zone 7 - Tadepalli Relief Haven",
        "latitude": 16.4800,
        "longitude": 80.6020,
        "population": 11000,
        "risk_score": 12.0,
        "risk_level": "GREEN",
        "priority_rank": 7,
        "recommended_action": "SAFE RELIEF SHELTER",
        "active_sos_count": 0
    }
]


# =====================================================================
# SACHET-STYLE INCOMING DISASTER ALERTS
# Sources: SACHET-NDMA, IMD, CWC
# =====================================================================

MOCK_ALERTS = [
    {
        "source": "SACHET-NDMA",
        "alert_type": "Flash Flood Inundation Warning",
        "severity": "SEVERE",
        "message": (
            "FLASH FLOOD CRITICAL: Krishna River inflow surged past 450,000 cusecs at Barrage. "
            "Severe inundation occurring in Krishnalanka and Bhavanipuram low-lying habitations. "
            "Immediate high-ground evacuation ordered by District Disaster Management Authority."
        ),
        "latitude": 16.5050,
        "longitude": 80.6150,
        "radius": 12.0,
        "minutes_ago": 15
    },
    {
        "source": "IMD",
        "alert_type": "Extremely Heavy Rainfall (Red Alert)",
        "severity": "WARNING",
        "message": (
            "IMD RED WARNING: Deep depression anchored over Krishna Delta catchment. "
            "Precipitation rates of 75-95 mm/hr recorded with cumulative 24h rainfall exceeding 260 mm. "
            "Urban stormwater drainage overwhelmed across municipal sectors."
        ),
        "latitude": 16.5100,
        "longitude": 80.6300,
        "radius": 25.0,
        "minutes_ago": 45
    },
    {
        "source": "CWC",
        "alert_type": "River Water Level Breach Warning",
        "severity": "SEVERE",
        "message": (
            "CENTRAL WATER COMMISSION (CWC): River gauge station at Barrage reports water level at 19.25 meters, "
            "exceeding Danger Level (17.50m) by +1.75m. Discharge velocity 4.1 m/s, continuous rapid rise of 0.65 m/hr."
        ),
        "latitude": 16.5090,
        "longitude": 80.6030,
        "radius": 10.0,
        "minutes_ago": 30
    },
    {
        "source": "SACHET-NDMA",
        "alert_type": "Road Inundation & Culvert Choke Advisory",
        "severity": "ALERT",
        "message": (
            "SACHET ADVISORY: Autonagar stormwater canals experiencing severe backflow. "
            "Key arterial underpasses submerged under 1.4m water. Vehicular transit prohibited on Bund Road."
        ),
        "latitude": 16.4950,
        "longitude": 80.6650,
        "radius": 8.0,
        "minutes_ago": 75
    },
    {
        "source": "IMD",
        "alert_type": "Precipitation Watch Bulletin",
        "severity": "WATCH",
        "message": (
            "IMD BULLETIN: Light to moderate intermittent precipitation continuing over Gunadala and outer eastern corridor. "
            "Soil saturation near 95% capacity."
        ),
        "latitude": 16.5160,
        "longitude": 80.6550,
        "radius": 15.0,
        "minutes_ago": 120
    }
]


# =====================================================================
# DRONE SURVEY ROAD BLOCKAGE READINGS
# High-resolution observations along key transport arteries
# =====================================================================

MOCK_DRONE_READINGS = [
    {
        "latitude": 16.5045,
        "longitude": 80.6120,
        "obstacle_type": "flooded_road",
        "water_depth": 1.6,
        "road_status": "blocked",
        "confidence": 0.97,
        "minutes_ago": 10
    },
    {
        "latitude": 16.5180,
        "longitude": 80.6010,
        "obstacle_type": "submerged_underpass",
        "water_depth": 1.85,
        "road_status": "blocked",
        "confidence": 0.99,
        "minutes_ago": 18
    },
    {
        "latitude": 16.4960,
        "longitude": 80.6350,
        "obstacle_type": "river_bund_breach",
        "water_depth": 1.35,
        "road_status": "blocked",
        "confidence": 0.94,
        "minutes_ago": 25
    },
    {
        "latitude": 16.4990,
        "longitude": 80.6510,
        "obstacle_type": "collapsed_culvert",
        "water_depth": 0.90,
        "road_status": "blocked",
        "confidence": 0.92,
        "minutes_ago": 35
    },
    {
        "latitude": 16.5020,
        "longitude": 80.6480,
        "obstacle_type": "waterlogged_artery",
        "water_depth": 0.45,
        "road_status": "restricted",
        "confidence": 0.88,
        "minutes_ago": 40
    },
    {
        "latitude": 16.5210,
        "longitude": 80.6680,
        "obstacle_type": "clear_flyover",
        "water_depth": 0.05,
        "road_status": "passable",
        "confidence": 0.99,
        "minutes_ago": 15
    },
    {
        "latitude": 16.4850,
        "longitude": 80.6080,
        "obstacle_type": "high_elevation_bypass",
        "water_depth": 0.0,
        "road_status": "passable",
        "confidence": 0.99,
        "minutes_ago": 8
    }
]


# =====================================================================
# CITIZEN SOS DISTRESS REPORTS (MULTILINGUAL: ENGLISH, TELUGU, HINDI)
# Geographically clustered within the high-risk zones
# =====================================================================

MOCK_SOS_REPORTS = [
    # English reports
    {
        "message": "Water entered our ground floor. My diabetic mother is bedridden and urgently needs insulin and rescue.",
        "language": "en",
        "need_type": "medical",
        "urgency": "critical",
        "latitude": 16.5085,
        "longitude": 80.6040,
        "priority_score": 96.0,
        "status": "SUBMITTED",
        "minutes_ago": 12
    },
    {
        "message": "6 people trapped on residential terrace near Krishnalanka sluice gate. Flood water rising past first floor level rapidly!",
        "language": "en",
        "need_type": "rescue",
        "urgency": "critical",
        "latitude": 16.4985,
        "longitude": 80.6275,
        "priority_score": 98.0,
        "status": "ASSIGNED",
        "minutes_ago": 22
    },
    {
        "message": "We have 2 infants and no drinking water since morning. Submerged road preventing us from leaving house.",
        "language": "en",
        "need_type": "water",
        "urgency": "high",
        "latitude": 16.5225,
        "longitude": 80.5990,
        "priority_score": 78.0,
        "status": "SUBMITTED",
        "minutes_ago": 48
    },
    {
        "message": "Power cut for 14 hours and water is knee-deep inside house. Requesting dry rations and shelter.",
        "language": "en",
        "need_type": "food",
        "urgency": "medium",
        "latitude": 16.4945,
        "longitude": 80.6630,
        "priority_score": 58.0,
        "status": "SUBMITTED",
        "minutes_ago": 90
    },

    # Telugu reports
    {
        "message": "మా ఇంట్లోకి నీళ్లు వచ్చాయి. మా అమ్మకు వెంటనే మందులు కావాలి, దయచేసి కాపాడండి.",
        "language": "te",
        "need_type": "medical",
        "urgency": "critical",
        "latitude": 16.5072,
        "longitude": 80.6050,
        "priority_score": 95.0,
        "status": "SUBMITTED",
        "minutes_ago": 14
    },
    {
        "message": "కృష్ణలంకలో వరద నీరు మొదటి అంతస్తు వరకు వచ్చింది. మేము పైకప్పుపై 7 మందిమి చిక్కుకున్నాము, వెంటనే బోటు పంపండి.",
        "language": "te",
        "need_type": "rescue",
        "urgency": "critical",
        "latitude": 16.4975,
        "longitude": 80.6290,
        "priority_score": 97.0,
        "status": "ASSIGNED",
        "minutes_ago": 28
    },
    {
        "message": "భవానిపురంలో మురుగు కాలువ పొంగి రోడ్డు మొత్తం మునిగిపోయింది. చిన్న పిల్లలకి పాలు మరియు ఆహారం అత్యవసరం.",
        "language": "te",
        "need_type": "food",
        "urgency": "high",
        "latitude": 16.5240,
        "longitude": 80.5970,
        "priority_score": 82.0,
        "status": "SUBMITTED",
        "minutes_ago": 52
    },
    {
        "message": "మేము ఆటోనగర్ వర్క్‌షాప్‌లో 5 మంది కార్మికులం చిక్కుకున్నాము. వర్షం నీరు నడుము లోతు వరకు వచ్చింది.",
        "language": "te",
        "need_type": "rescue",
        "urgency": "high",
        "latitude": 16.4955,
        "longitude": 80.6660,
        "priority_score": 79.0,
        "status": "SUBMITTED",
        "minutes_ago": 65
    },

    # Hindi reports
    {
        "message": "हमारे घर में पानी आ गया है और मेरी माँ को तुरंत दिल की दवा चाहिए। रास्ता पूरी तरह बंद है।",
        "language": "hi",
        "need_type": "medical",
        "urgency": "critical",
        "latitude": 16.5065,
        "longitude": 80.6060,
        "priority_score": 94.0,
        "status": "SUBMITTED",
        "minutes_ago": 16
    },
    {
        "message": "बाढ़ का पानी छत तक पहुँचने वाला है, परिवार के 5 सदस्य फंसे हैं। कृपया तुरंत रेस्क्यू बोट भेजें!",
        "language": "hi",
        "need_type": "rescue",
        "urgency": "critical",
        "latitude": 16.4995,
        "longitude": 80.6260,
        "priority_score": 98.0,
        "status": "EN_ROUTE",
        "minutes_ago": 32
    },
    {
        "message": "हमारे इलाके में बिजली गुल है और पीने का स्वच्छ पानी समाप्त हो गया है। नवजात शिशु के लिए मदद चाहिए।",
        "language": "hi",
        "need_type": "water",
        "urgency": "high",
        "latitude": 16.5215,
        "longitude": 80.6005,
        "priority_score": 80.0,
        "status": "SUBMITTED",
        "minutes_ago": 58
    },
    {
        "message": "ऑटोनगर मेन रोड पर पानी 3 फीट भर गया है और हमारी वैन डूब रही है, हमें सुरक्षित स्थान पर ले जाएं।",
        "language": "hi",
        "need_type": "evacuation",
        "urgency": "high",
        "latitude": 16.4960,
        "longitude": 80.6640,
        "priority_score": 81.0,
        "status": "SUBMITTED",
        "minutes_ago": 70
    },

    # Tamil reports
    {
        "message": "எங்கள் வீட்டின் தரைத்தளத்தில் தண்ணீர் புகுந்துவிட்டது, மாடியில் 4 பேர் மாட்டிக்கொண்டோம், உடனடியாக படகு தேவை.",
        "language": "ta",
        "need_type": "rescue",
        "urgency": "critical",
        "latitude": 16.4988,
        "longitude": 80.6278,
        "priority_score": 97.0,
        "status": "SUBMITTED",
        "minutes_ago": 25
    },
    {
        "message": "முதியவருக்கு ஆஸ்துமா பிரச்சனை, அவசர மருந்து மற்றும் குடிநீர் தேவை.",
        "language": "ta",
        "need_type": "medical",
        "urgency": "high",
        "latitude": 16.5080,
        "longitude": 80.6055,
        "priority_score": 88.0,
        "status": "SUBMITTED",
        "minutes_ago": 40
    },

    # Kannada reports
    {
        "message": "ನಮ್ಮ ಮನೆಯೊಳಗೆ ಪ್ರವಾಹದ ನೀರು ನುಗ್ಗಿದೆ, ಮೇಲ್ಛಾವಣಿಯಲ್ಲಿ 5 ಜನರು ಸಿಲುಕಿಕೊಂಡಿದ್ದೇವೆ. ದಯವಿಟ್ಟು ತಕ್ಷಣ ಕಾಪಾಡಿ!",
        "language": "kn",
        "need_type": "rescue",
        "urgency": "critical",
        "latitude": 16.4970,
        "longitude": 80.6285,
        "priority_score": 96.0,
        "status": "SUBMITTED",
        "minutes_ago": 30
    },
    {
        "message": "ಆಸ್ಪತ್ರೆಗೆ ಹೋಗಲು ದಾರಿಯಿಲ್ಲ, ಗರ್ಭಿಣಿ ಮಹಿಳೆಗೆ ತಕ್ಷಣ ವೈದ್ಯಕೀಯ ನೆರವು ಬೇಕು.",
        "language": "kn",
        "need_type": "medical",
        "urgency": "critical",
        "latitude": 16.5235,
        "longitude": 80.5985,
        "priority_score": 94.0,
        "status": "SUBMITTED",
        "minutes_ago": 35
    },

    # Malayalam reports
    {
        "message": "വീട്ടിൽ വെള്ളം കയറി, ടെറസ്സിൽ 4 പേർ കുടുങ്ങിക്കിടക്കുന്നു. പെട്ടെന്ന് രക്ഷിക്കൂ!",
        "language": "ml",
        "need_type": "rescue",
        "urgency": "critical",
        "latitude": 16.4990,
        "longitude": 80.6265,
        "priority_score": 96.0,
        "status": "SUBMITTED",
        "minutes_ago": 20
    },
    {
        "message": "കുട്ടികൾക്ക് കുടിവെള്ളവും ഭക്ഷണവും ലഭ്യമല്ല, വൈദ്യുതി മുടങ്ങിയിട്ട് 12 മണിക്കൂറായി.",
        "language": "ml",
        "need_type": "water",
        "urgency": "high",
        "latitude": 16.5220,
        "longitude": 80.6010,
        "priority_score": 82.0,
        "status": "SUBMITTED",
        "minutes_ago": 60
    },

    # Transliterated / Romanized Indian Languages
    {
        "message": "Maa intloki neellu vachayi, amma ki BP and diabetes mandulu urgent ga kavali please help us!",
        "language": "te",
        "need_type": "medical",
        "urgency": "critical",
        "latitude": 16.5078,
        "longitude": 80.6045,
        "priority_score": 95.0,
        "status": "SUBMITTED",
        "minutes_ago": 18
    },
    {
        "message": "Ghar mein paani 4 feet ghus gaya hai, 5 log chhat par phase hain, jaldi rescue boat bhejo!",
        "language": "hi",
        "need_type": "rescue",
        "urgency": "critical",
        "latitude": 16.4982,
        "longitude": 80.6270,
        "priority_score": 97.0,
        "status": "SUBMITTED",
        "minutes_ago": 24
    }
]


# =====================================================================
# RESCUE & VOLUNTEER TEAMS
# Professional responders and citizen volunteer units
# =====================================================================

MOCK_TEAMS = [
    {
        "name": "NDRF Quick Response Team 01",
        "task": "Flood Evacuation & Inflatable Boat Rescue",
        "status": "EN_ROUTE",
        "latitude": 16.5020,
        "longitude": 80.6220,
        "member_count": 8
    },
    {
        "name": "SDRF Aquatic Rescue Unit 03",
        "task": "Terrace Extraction & Sluice Gate Evacuation",
        "status": "ON_SITE",
        "latitude": 16.4980,
        "longitude": 80.6280,
        "member_count": 6
    },
    {
        "name": "Red Cross Emergency Medical Squad Alpha",
        "task": "Critical Insulin & Trauma First Aid Dispatch",
        "status": "ASSIGNED",
        "latitude": 16.5075,
        "longitude": 80.6080,
        "member_count": 4
    },
    {
        "name": "Civil Defence Volunteer Unit 07",
        "task": "Dry Food Rations & Bottled Water Delivery",
        "status": "AVAILABLE",
        "latitude": 16.4810,
        "longitude": 80.6030,
        "member_count": 5
    }
]


# =====================================================================
# USERS (CITIZENS & VOLUNTEERS)
# =====================================================================

MOCK_USERS = [
    {
        "name": "Venkat Rao",
        "phone": "+91 98480 12345",
        "email": "venkat.rao@example.com",
        "role": "citizen",
        "latitude": 16.5085,
        "longitude": 80.6040,
        "availability": True,
        "skills": None
    },
    {
        "name": "Ananya Sharma",
        "phone": "+91 98110 54321",
        "email": "ananya.sharma@example.com",
        "role": "volunteer",
        "latitude": 16.4820,
        "longitude": 80.6050,
        "availability": True,
        "skills": "first_aid,swimming,medical"
    },
    {
        "name": "Rajesh Kumar",
        "phone": "+91 98765 43210",
        "email": "rajesh.kumar@example.com",
        "role": "volunteer",
        "latitude": 16.4835,
        "longitude": 80.6015,
        "availability": True,
        "skills": "boat_handling,evacuation"
    },
    {
        "name": "Inspector K. Srinivas (NDRF)",
        "phone": "+91 94400 99887",
        "email": "ndrf.srinivas@gov.in",
        "role": "responder",
        "latitude": 16.5020,
        "longitude": 80.6220,
        "availability": False,
        "skills": "command,aquatic_rescue"
    }
]


# =====================================================================
# PHASE 8 DEMONSTRATION DATA: POST-DISASTER RELIEF, RECOVERY & DAMAGE
# =====================================================================

MOCK_RELIEF_CAMPS = [
    {
        "name": "Tadepalli High School Relief Camp",
        "location_name": "Tadepalli Ridge High-Ground (Zone 7)",
        "latitude": 16.4800,
        "longitude": 80.6020,
        "capacity": 1500,
        "current_occupancy": 650,
        "available_beds": 850,
        "food_availability": "Adequate",
        "water_availability": "Adequate",
        "medical_support": "Available",
        "contact_person": "Shri M. Venkat Rao (Tahsildar)",
        "contact_phone": "+91 94401 22331",
        "status": "Available"
    },
    {
        "name": "Kanakadurga Temple Complex Haven",
        "location_name": "Indrakeeladri Hill Elevated Footing",
        "latitude": 16.5170,
        "longitude": 80.6120,
        "capacity": 2000,
        "current_occupancy": 1600,
        "available_beds": 400,
        "food_availability": "Adequate",
        "water_availability": "Surplus",
        "medical_support": "Full Clinic",
        "contact_person": "Dr. K. Sujatha (Chief Medical Officer)",
        "contact_phone": "+91 94401 33442",
        "status": "Near Capacity"
    },
    {
        "name": "Autonagar Industrial Hall Relief Camp",
        "location_name": "Autonagar Sector 7 Elevated Platform",
        "latitude": 16.4870,
        "longitude": 80.6720,
        "capacity": 1200,
        "current_occupancy": 1150,
        "available_beds": 50,
        "food_availability": "Low",
        "water_availability": "Adequate",
        "medical_support": "First Aid Only",
        "contact_person": "Sri B. Satyanarayana",
        "contact_phone": "+91 94401 44553",
        "status": "Near Capacity"
    },
    {
        "name": "Bhavanipuram Community Center Camp",
        "location_name": "Bhavanipuram Lowlands High Platform",
        "latitude": 16.5230,
        "longitude": 80.5980,
        "capacity": 800,
        "current_occupancy": 800,
        "available_beds": 0,
        "food_availability": "Critical",
        "water_availability": "Low",
        "medical_support": "First Aid Only",
        "contact_person": "Smt. P. Lakshmi Devi",
        "contact_phone": "+91 94401 55664",
        "status": "Full"
    },
    {
        "name": "Benz Circle Elevated College Campus Camp",
        "location_name": "PB Siddhartha College Complex",
        "latitude": 16.5020,
        "longitude": 80.6500,
        "capacity": 1000,
        "current_occupancy": 350,
        "available_beds": 650,
        "food_availability": "Surplus",
        "water_availability": "Surplus",
        "medical_support": "Available",
        "contact_person": "Sri V. Mohan Reddy",
        "contact_phone": "+91 94401 66775",
        "status": "Available"
    }
]

MOCK_RESOURCES = [
    {
        "item_name": "Cooked Food Packets",
        "category": "Food",
        "unit": "packets",
        "available_qty": 8500,
        "required_qty": 15000,
        "distributed_qty": 4200,
        "low_stock_threshold": 2000
    },
    {
        "item_name": "Drinking Water Cans (20L)",
        "category": "Water",
        "unit": "cans",
        "available_qty": 4200,
        "required_qty": 8000,
        "distributed_qty": 2800,
        "low_stock_threshold": 1000
    },
    {
        "item_name": "Emergency Medical First-Aid Kits",
        "category": "Medical",
        "unit": "kits",
        "available_qty": 340,
        "required_qty": 600,
        "distributed_qty": 210,
        "low_stock_threshold": 100
    },
    {
        "item_name": "Thermal Blankets & Bedrolls",
        "category": "Shelter/Warmth",
        "unit": "pieces",
        "available_qty": 5200,
        "required_qty": 8000,
        "distributed_qty": 3600,
        "low_stock_threshold": 1500
    },
    {
        "item_name": "Waterproof Tarpaulin Sheets",
        "category": "Shelter/Warmth",
        "unit": "sheets",
        "available_qty": 850,
        "required_qty": 1800,
        "distributed_qty": 620,
        "low_stock_threshold": 300
    },
    {
        "item_name": "Infant Formula & Milk Packs",
        "category": "Food",
        "unit": "packs",
        "available_qty": 450,
        "required_qty": 1200,
        "distributed_qty": 580,
        "low_stock_threshold": 500  # Low stock warning!
    },
    {
        "item_name": "Chlorine Water Purification Strips",
        "category": "Water",
        "unit": "strips",
        "available_qty": 12000,
        "required_qty": 20000,
        "distributed_qty": 8000,
        "low_stock_threshold": 3000
    }
]

MOCK_RELIEF_TEAMS = [
    {
        "team_code": "RELIEF-NDRF-01",
        "name": "NDRF 10th Battalion Aquatic Taskforce",
        "team_type": "Rescue",
        "location_name": "Krishnalanka Riverfront",
        "latitude": 16.4980,
        "longitude": 80.6280,
        "members": 8,
        "leader_name": "Inspector Rajesh Kumar",
        "contact_phone": "+91 94402 11223",
        "assigned_task": "Inflatable boat rescue for stranded residents along floodway bund",
        "status": "On Mission"
    },
    {
        "team_code": "RELIEF-SDRF-02",
        "name": "Andhra SDRF Marine Rapid Response Team 3",
        "team_type": "Search & Rescue",
        "location_name": "Bhavanipuram Lowlands",
        "latitude": 16.5230,
        "longitude": 80.5980,
        "members": 6,
        "leader_name": "Sub-Inspector K. Srinivas",
        "contact_phone": "+91 94402 22334",
        "assigned_task": "Search & evacuation operations in inundated underpass colonies",
        "status": "On Mission"
    },
    {
        "team_code": "RELIEF-MED-03",
        "name": "Red Cross Mobile Trauma & Triage Unit",
        "team_type": "Medical",
        "location_name": "Kanakadurga High-Ground Camp",
        "latitude": 16.5170,
        "longitude": 80.6120,
        "members": 5,
        "leader_name": "Dr. Ananya Sharma",
        "contact_phone": "+91 94402 33445",
        "assigned_task": "Triage and essential diabetes / trauma care for evacuated citizens",
        "status": "Assigned"
    },
    {
        "team_code": "RELIEF-CIV-04",
        "name": "Vijayawada Food Logistics & Supply Brigade",
        "team_type": "Food Distribution",
        "location_name": "Tadepalli Supply Depot",
        "latitude": 16.4800,
        "longitude": 80.6020,
        "members": 10,
        "leader_name": "Captain D. Prasad",
        "contact_phone": "+91 94402 44556",
        "assigned_task": "Loading convoy and delivering hot cooked meals & bottled water",
        "status": "On Mission"
    },
    {
        "team_code": "RELIEF-INFRA-05",
        "name": "AP Transco Power Grid Restoration Squad",
        "team_type": "Infrastructure",
        "location_name": "Autonagar Sector 7",
        "latitude": 16.4950,
        "longitude": 80.6650,
        "members": 7,
        "leader_name": "Eng. T. Ramana Murthy",
        "contact_phone": "+91 94402 55667",
        "assigned_task": "Isolating flooded transformers and clearing overhead lines",
        "status": "Assigned"
    },
    {
        "team_code": "RELIEF-VOL-06",
        "name": "Civil Defense Volunteer Auxiliary Force",
        "team_type": "Community Assistance",
        "location_name": "Benz Circle Transit Hub",
        "latitude": 16.5020,
        "longitude": 80.6500,
        "members": 12,
        "leader_name": "Coordinator S. Haritha",
        "contact_phone": "+91 94402 66778",
        "assigned_task": "Assisting elderly citizens and registering field relief requests",
        "status": "Available"
    },
    {
        "team_code": "RELIEF-COMM-07",
        "name": "Vijayawada Youth Civic Response Volunteers",
        "team_type": "Community Assistance",
        "location_name": "Benz Circle Safe Zone Platform",
        "latitude": 16.5020,
        "longitude": 80.6500,
        "members": 8,
        "leader_name": "Suresh Varma (Volunteer Lead)",
        "contact_phone": "+91 98480 77889",
        "assigned_task": "Standby for local food/water distribution and senior assistance",
        "status": "Available"
    },
    {
        "team_code": "RELIEF-COMM-08",
        "name": "Tadepalli Motorboat Community Taskforce",
        "team_type": "Community Assistance",
        "location_name": "Tadepalli High-Ground",
        "latitude": 16.4820,
        "longitude": 80.6050,
        "members": 6,
        "leader_name": "Ramesh Babu (Volunteer Captain)",
        "contact_phone": "+91 98480 88990",
        "assigned_task": "Local flood evacuation and emergency medicine transport",
        "status": "Available"
    }
]

MOCK_RELIEF_REQUESTS = [
    {
        "request_code": "REQ-KD-101",
        "location_name": "Krishnalanka Old Bund Road, Ward 14",
        "latitude": 16.4975,
        "longitude": 80.6275,
        "zone_id": 3,
        "category": "Rescue",
        "priority": "Critical",
        "priority_score": 94.0,
        "people_count": 14,
        "status": "Assigned",
        "assigned_team_name": "NDRF 10th Battalion Aquatic Taskforce",
        "notes": "Elderly persons and infants trapped on first floor; water reached 5ft height"
    },
    {
        "request_code": "REQ-KD-102",
        "location_name": "Bhavanipuram Gollapudi Market Link",
        "latitude": 16.5220,
        "longitude": 80.5970,
        "zone_id": 2,
        "category": "Medical Emergency",
        "priority": "Critical",
        "priority_score": 91.5,
        "people_count": 3,
        "status": "Assigned",
        "assigned_team_name": "Red Cross Mobile Trauma & Triage Unit",
        "notes": "Diabetic patient in urgent need of insulin and hydration salts"
    },
    {
        "request_code": "REQ-KD-103",
        "location_name": "Autonagar Industrial Slum Quarters",
        "latitude": 16.4940,
        "longitude": 80.6640,
        "zone_id": 4,
        "category": "Drinking Water",
        "priority": "High",
        "priority_score": 82.0,
        "people_count": 65,
        "status": "Pending",
        "assigned_team_name": None,
        "notes": "Main drinking water pipe burst; 65 families have zero clean water"
    },
    {
        "request_code": "REQ-KD-104",
        "location_name": "Krishna Barrage North Sluice Colony",
        "latitude": 16.5085,
        "longitude": 80.6040,
        "zone_id": 1,
        "category": "Food",
        "priority": "High",
        "priority_score": 79.5,
        "people_count": 40,
        "status": "In Progress",
        "assigned_team_name": "Vijayawada Food Logistics & Supply Brigade",
        "notes": "Fishermen colony cut off from markets; cooked food packets requested"
    },
    {
        "request_code": "REQ-KD-105",
        "location_name": "Gunadala Hillside Low-Lying Foothills",
        "latitude": 16.5155,
        "longitude": 80.6540,
        "zone_id": 6,
        "category": "Medicine",
        "priority": "Medium",
        "priority_score": 58.0,
        "people_count": 8,
        "status": "Pending",
        "assigned_team_name": None,
        "notes": "Fever medication, water purification tablets, and antiseptic ointments needed"
    },
    {
        "request_code": "REQ-KD-106",
        "location_name": "Ramavarappadu Ring Road Community Shed",
        "latitude": 16.5275,
        "longitude": 80.6710,
        "zone_id": 5,
        "category": "Shelter",
        "priority": "High",
        "priority_score": 73.0,
        "people_count": 25,
        "status": "Pending",
        "assigned_team_name": None,
        "notes": "Temporary community shed damaged by storm; tarpaulins and blankets requested"
    },
    {
        "request_code": "REQ-KD-107",
        "location_name": "Tadepalli Railway Lowlands Camp Perimeter",
        "latitude": 16.4810,
        "longitude": 80.6030,
        "zone_id": 7,
        "category": "Clothing",
        "priority": "Medium",
        "priority_score": 45.0,
        "people_count": 18,
        "status": "Completed",
        "assigned_team_name": "Civil Defense Volunteer Auxiliary Force",
        "notes": "Dry clothes, baby blankets, and sanitary hygiene kits delivered"
    },
    {
        "request_code": "REQ-KD-108",
        "location_name": "Bhavanipuram School Camp Outreach",
        "latitude": 16.5240,
        "longitude": 80.5990,
        "zone_id": 2,
        "category": "Other",
        "priority": "Low",
        "priority_score": 35.0,
        "people_count": 12,
        "status": "Pending",
        "assigned_team_name": None,
        "notes": "Mosquito repellent coils and solar flashlights requested for night illumination"
    }
]

MOCK_RECOVERY_ITEMS = [
    {
        "item_code": "REC-RD-01",
        "name": "NH16 Krishna Barrage Northern Link Road",
        "category": "Roads",
        "location_name": "Barrage North Approach (Zone 1)",
        "latitude": 16.5091,
        "longitude": 80.6034,
        "damage_level": "Severe",
        "recovery_status": "Repairing",
        "progress_pct": 45,
        "assigned_team": "APSRDC Infrastructure Team 2",
        "estimated_completion": "36 hours",
        "notes": "Debris clearing complete; laying asphalt binder course on submerged stretch"
    },
    {
        "item_code": "REC-BR-02",
        "name": "Prakasam Barrage Sluice Spillway Access Bridge",
        "category": "Bridges",
        "location_name": "Krishna Barrage Center",
        "latitude": 16.5050,
        "longitude": 80.6050,
        "damage_level": "Moderate",
        "recovery_status": "Assessment",
        "progress_pct": 20,
        "assigned_team": "Irrigation Dept Structural Squad",
        "estimated_completion": "48 hours",
        "notes": "Sonar inspection of bridge piers; minor scouring detected"
    },
    {
        "item_code": "REC-PWR-03",
        "name": "Krishnalanka 33kV Electrical Substation",
        "category": "Electricity",
        "location_name": "Krishnalanka Sector 3 (Zone 3)",
        "latitude": 16.4980,
        "longitude": 80.6280,
        "damage_level": "Severe",
        "recovery_status": "Repairing",
        "progress_pct": 35,
        "assigned_team": "AP Transco Power Grid Restoration Squad",
        "estimated_completion": "2 days",
        "notes": "Pumping floodwaters from control room; drying out transformer windings"
    },
    {
        "item_code": "REC-WTR-04",
        "name": "Vijayawada Head Water Works Filtration Plant",
        "category": "Water supply",
        "location_name": "Bhavanipuram Riverbank (Zone 2)",
        "latitude": 16.5200,
        "longitude": 80.6000,
        "damage_level": "Severe",
        "recovery_status": "Repairing",
        "progress_pct": 55,
        "assigned_team": "VMC Water Works Rapid Response",
        "estimated_completion": "24 hours",
        "notes": "Chlorination booster replaced; flushing contaminated intake conduits"
    },
    {
        "item_code": "REC-HSP-05",
        "name": "Government General Hospital Trauma Wing",
        "category": "Hospitals",
        "location_name": "Old GGH Complex Vijayawada",
        "latitude": 16.5100,
        "longitude": 80.6300,
        "damage_level": "Minor",
        "recovery_status": "Restored",
        "progress_pct": 100,
        "assigned_team": "Medical Infrastructure Taskforce",
        "estimated_completion": "Completed",
        "notes": "Backup diesel generators running; emergency emergency wing 100% functional"
    },
    {
        "item_code": "REC-SCH-06",
        "name": "Zilla Parishad High School Bhavanipuram",
        "category": "Schools",
        "location_name": "Bhavanipuram Center",
        "latitude": 16.5230,
        "longitude": 80.5980,
        "damage_level": "Moderate",
        "recovery_status": "Assessment",
        "progress_pct": 15,
        "assigned_team": "Samagra Shiksha Civil Wing",
        "estimated_completion": "5 days",
        "notes": "Structural integrity verified; silt removal and sanitization pending"
    },
    {
        "item_code": "REC-TEL-07",
        "name": "BSNL Cellular Tower & Fiber Conduit KD-04",
        "category": "Communication infrastructure",
        "location_name": "Benz Circle Junction",
        "latitude": 16.5020,
        "longitude": 80.6500,
        "damage_level": "Minor",
        "recovery_status": "Restored",
        "progress_pct": 95,
        "assigned_team": "BSNL Disaster Restoration Cell",
        "estimated_completion": "6 hours",
        "notes": "Microwave backup link operational; fiber cable spliced"
    },
    {
        "item_code": "REC-HOU-08",
        "name": "Krishnalanka Bund Flood Housing Colony",
        "category": "Housing",
        "location_name": "Krishnalanka Bund Perimeter",
        "latitude": 16.4960,
        "longitude": 80.6260,
        "damage_level": "Severe",
        "recovery_status": "Not Started",
        "progress_pct": 5,
        "assigned_team": "AP Housing Board Survey Team",
        "estimated_completion": "2 weeks",
        "notes": "Preliminary drone damage scan complete; structural re-entry unsafe until water recedes"
    }
]

MOCK_DAMAGE_ASSESSMENTS = [
    {
        "zone_id": 1,
        "zone_name": "Zone 1 - Krishna Barrage North",
        "damage_severity": "CRITICAL",
        "assessment_status": "VERIFIED",
        "buildings_damage": "78 riverfront tenements inundated, 12 collapsed",
        "roads_bridges_damage": "Barrage north ramp submerged under 1.2m water; road access blocked",
        "infrastructure_damage": "Water pumping intake submersed; power feeder line severed",
        "affected_people": 14200,
        "injured_count": 52,
        "missing_count": 4,
        "rescued_count": 230,
        "displaced_count": 3800,
        "food_packets_needed": 6000,
        "water_liters_needed": 12000,
        "medical_kits_needed": 180,
        "shelter_tents_needed": 400,
        "blankets_needed": 3000,
        "urgent_requirements": "Immediate boat evacuation, clean drinking water cans, and pediatric trauma care",
        "priority_level": "CRITICAL",
        "priority_score": 92.0
    },
    {
        "zone_id": 2,
        "zone_name": "Zone 2 - Bhavanipuram Lowlands",
        "damage_severity": "CRITICAL",
        "assessment_status": "ASSESSED",
        "buildings_damage": "60% low-lying residential colonies waterlogged up to roof levels",
        "roads_bridges_damage": "Gollapudi underpasses impassable; silt deposits on internal corridors",
        "infrastructure_damage": "Sewage pump station backflow; 11kV electrical transformer submerged",
        "affected_people": 22500,
        "injured_count": 64,
        "missing_count": 5,
        "rescued_count": 310,
        "displaced_count": 5400,
        "food_packets_needed": 8500,
        "water_liters_needed": 16000,
        "medical_kits_needed": 240,
        "shelter_tents_needed": 600,
        "blankets_needed": 4500,
        "urgent_requirements": "High-clearance rescue trucks, insulin kits, water purification tablets",
        "priority_level": "CRITICAL",
        "priority_score": 94.5
    },
    {
        "zone_id": 3,
        "zone_name": "Zone 3 - Krishnalanka Floodway",
        "damage_severity": "CRITICAL",
        "assessment_status": "VERIFIED",
        "buildings_damage": "River bund breached at 2 points; 110 kutcha houses destroyed",
        "roads_bridges_damage": "Old Bund road washed away in 3 sections; 1.8m floodwaters in colonies",
        "infrastructure_damage": "Complete electrical blackout; municipal water conduit fractured",
        "affected_people": 31000,
        "injured_count": 95,
        "missing_count": 8,
        "rescued_count": 480,
        "displaced_count": 8200,
        "food_packets_needed": 12000,
        "water_liters_needed": 24000,
        "medical_kits_needed": 350,
        "shelter_tents_needed": 900,
        "blankets_needed": 7000,
        "urgent_requirements": "Heavy-duty aquatic rescue craft, anti-venom, baby formula, and temporary camp tents",
        "priority_level": "CRITICAL",
        "priority_score": 98.0
    },
    {
        "zone_id": 4,
        "zone_name": "Zone 4 - Autonagar Sector 7",
        "damage_severity": "HIGH",
        "assessment_status": "ASSESSED",
        "buildings_damage": "Industrial workshops and labor colonies inundated up to 1.1m",
        "roads_bridges_damage": "Canal link road blocked with stranded container vehicles",
        "infrastructure_damage": "Stormwater drains backflowing industrial sludge",
        "affected_people": 18400,
        "injured_count": 28,
        "missing_count": 1,
        "rescued_count": 145,
        "displaced_count": 2600,
        "food_packets_needed": 4500,
        "water_liters_needed": 9000,
        "medical_kits_needed": 90,
        "shelter_tents_needed": 200,
        "blankets_needed": 2000,
        "urgent_requirements": "Safe drinking water cans, skin infection ointments, and barrier tarpaulins",
        "priority_level": "HIGH",
        "priority_score": 76.5
    },
    {
        "zone_id": 5,
        "zone_name": "Zone 5 - Ramavarappadu Junction",
        "damage_severity": "MEDIUM",
        "assessment_status": "ASSESSED",
        "buildings_damage": "Ground floor commercial shophouses waterlogged up to 0.4m",
        "roads_bridges_damage": "Highway flyover clear; ground service roads congested with traffic",
        "infrastructure_damage": "Telecom cell towers running on battery backups; partial power outages",
        "affected_people": 16800,
        "injured_count": 12,
        "missing_count": 0,
        "rescued_count": 65,
        "displaced_count": 1100,
        "food_packets_needed": 2200,
        "water_liters_needed": 4500,
        "medical_kits_needed": 45,
        "shelter_tents_needed": 100,
        "blankets_needed": 900,
        "urgent_requirements": "Traffic clearance cranes, dry food packets, and basic hygiene kits",
        "priority_level": "MEDIUM",
        "priority_score": 54.0
    },
    {
        "zone_id": 6,
        "zone_name": "Zone 6 - Gunadala Hillside Corridor",
        "damage_severity": "LOW",
        "assessment_status": "VERIFIED",
        "buildings_damage": "Minor stormwater accumulation in low-lying gullies; no structural collapses",
        "roads_bridges_damage": "Hillside arterial corridors clear and fully passable",
        "infrastructure_damage": "Electricity and communications fully stable; functioning as secondary relief post",
        "affected_people": 19500,
        "injured_count": 6,
        "missing_count": 0,
        "rescued_count": 25,
        "displaced_count": 450,
        "food_packets_needed": 1200,
        "water_liters_needed": 2500,
        "medical_kits_needed": 30,
        "shelter_tents_needed": 50,
        "blankets_needed": 400,
        "urgent_requirements": "Support volunteer coordination and transit food supply",
        "priority_level": "LOW",
        "priority_score": 32.0
    },
    {
        "zone_id": 7,
        "zone_name": "Zone 7 - Tadepalli Relief Haven",
        "damage_severity": "LOW",
        "assessment_status": "VERIFIED",
        "buildings_damage": "Zero flood damage; elevated ridge sanctuary operating at full efficiency",
        "roads_bridges_damage": "All evacuation corridors into Tadepalli clear and safeguarded",
        "infrastructure_damage": "100% operational emergency command hub and relief warehouses",
        "affected_people": 15000,
        "injured_count": 2,
        "missing_count": 0,
        "rescued_count": 0,
        "displaced_count": 0,
        "food_packets_needed": 0,
        "water_liters_needed": 0,
        "medical_kits_needed": 0,
        "shelter_tents_needed": 0,
        "blankets_needed": 0,
        "urgent_requirements": "Hub receiving evacuees and coordinating outbound aid convoys",
        "priority_level": "LOW",
        "priority_score": 15.0
    }
]


# =====================================================================
# GENERATION / SEED / RESET ENGINE
# =====================================================================

def clear_mock_data(db: Session) -> dict:
    """Removes existing simulated records cleanly from SQLite."""
    deleted_counts = {
        "relief_donations": db.query(ReliefDonation).delete(),
        "relief_funds": db.query(ReliefFund).delete(),
        "damage_assessments": db.query(ZoneDamageAssessment).delete(),
        "recovery_items": db.query(RecoveryItem).delete(),
        "relief_teams": db.query(ReliefTeam).delete(),
        "resource_inventory": db.query(ResourceInventory).delete(),
        "relief_requests": db.query(ReliefRequest).delete(),
        "relief_camps": db.query(ReliefCamp).delete(),
        "environmental_readings": db.query(EnvironmentalReading).delete(),
        "sos_reports": db.query(SOSReport).delete(),
        "drone_readings": db.query(DroneReading).delete(),
        "alerts": db.query(Alert).delete(),
        "teams": db.query(Team).delete(),
        "zones": db.query(Zone).delete(),
        "users": db.query(User).delete()
    }
    db.commit()
    return deleted_counts



def seed_mock_data(db: Session, overwrite: bool = True) -> dict:
    """
    Seeds comprehensive, geographically correlated mock data into the database.
    Creates Zones, Users, Teams, Alerts, Drone Readings, Environmental telemetry, and SOS reports.
    """
    now = utc_now()
    if overwrite:
        clear_mock_data(db)

    # 1. Seed Zones
    zone_entities = []
    for zd in MOCK_ZONES:
        zone = Zone(**zd)
        db.add(zone)
        zone_entities.append(zone)
    db.commit()
    for z in zone_entities:
        db.refresh(z)
    zone_map = {z.name: z for z in zone_entities}

    # 2. Seed Users
    user_entities = []
    for ud in MOCK_USERS:
        user = User(**ud)
        db.add(user)
        user_entities.append(user)
    db.commit()
    for u in user_entities:
        db.refresh(u)

    # 3. Seed Teams
    team_entities = []
    for td in MOCK_TEAMS:
        team = Team(**td)
        db.add(team)
        team_entities.append(team)
    db.commit()
    for t in team_entities:
        db.refresh(t)

    # 4. Seed Alerts
    alert_entities = []
    for ad in MOCK_ALERTS:
        mins = ad.pop("minutes_ago", 0)
        alert = Alert(
            source=ad["source"],
            alert_type=ad["alert_type"],
            severity=ad["severity"],
            message=ad["message"],
            latitude=ad["latitude"],
            longitude=ad["longitude"],
            radius=ad["radius"],
            timestamp=now - timedelta(minutes=mins)
        )
        db.add(alert)
        alert_entities.append(alert)
    db.commit()

    # 5. Seed Drone Readings
    drone_entities = []
    for dd in MOCK_DRONE_READINGS:
        mins = dd.pop("minutes_ago", 0)
        drone = DroneReading(
            latitude=dd["latitude"],
            longitude=dd["longitude"],
            obstacle_type=dd["obstacle_type"],
            water_depth=dd["water_depth"],
            road_status=dd["road_status"],
            confidence=dd["confidence"],
            timestamp=now - timedelta(minutes=mins)
        )
        db.add(drone)
        drone_entities.append(drone)
    db.commit()

    # 6. Seed Environmental Telemetry (Per Zone)
    env_readings = [
        # Zone 1 - Krishna Barrage North (Severe surge)
        {"zone": "Zone 1 - Krishna Barrage North", "rainfall_intensity": 78.5, "cumulative_rainfall": 242.0, "river_level": 18.90, "danger_level": 17.50, "water_level_change_rate": 0.65, "water_depth": 1.60},
        # Zone 2 - Bhavanipuram Lowlands (Urban waterlogging)
        {"zone": "Zone 2 - Bhavanipuram Lowlands", "rainfall_intensity": 64.0, "cumulative_rainfall": 195.0, "river_level": 17.85, "danger_level": 17.50, "water_level_change_rate": 0.40, "water_depth": 1.20},
        # Zone 3 - Krishnalanka Floodway (Overflow corridor)
        {"zone": "Zone 3 - Krishnalanka Floodway", "rainfall_intensity": 85.0, "cumulative_rainfall": 268.0, "river_level": 19.25, "danger_level": 17.50, "water_level_change_rate": 0.80, "water_depth": 1.90},
        # Zone 4 - Autonagar Sector 7 (Drainage blockage)
        {"zone": "Zone 4 - Autonagar Sector 7", "rainfall_intensity": 45.0, "cumulative_rainfall": 130.0, "river_level": 16.80, "danger_level": 17.50, "water_level_change_rate": 0.25, "water_depth": 0.70},
        # Zone 5 - Ramavarappadu Junction (Intermediate watch)
        {"zone": "Zone 5 - Ramavarappadu Junction", "rainfall_intensity": 32.0, "cumulative_rainfall": 95.0, "river_level": 15.20, "danger_level": 17.50, "water_level_change_rate": 0.10, "water_depth": 0.30},
        # Zone 6 - Gunadala Hillside Corridor (Slope runoff)
        {"zone": "Zone 6 - Gunadala Hillside Corridor", "rainfall_intensity": 28.0, "cumulative_rainfall": 75.0, "river_level": 14.10, "danger_level": 17.50, "water_level_change_rate": 0.05, "water_depth": 0.10},
        # Zone 7 - Tadepalli Relief Haven (Safe high-ground)
        {"zone": "Zone 7 - Tadepalli Relief Haven", "rainfall_intensity": 14.0, "cumulative_rainfall": 42.0, "river_level": 12.50, "danger_level": 17.50, "water_level_change_rate": -0.05, "water_depth": 0.0}
    ]
    env_entities = []
    for env in env_readings:
        z_obj = zone_map.get(env["zone"])
        if z_obj:
            er = EnvironmentalReading(
                zone_id=z_obj.id,
                rainfall_intensity=env["rainfall_intensity"],
                cumulative_rainfall=env["cumulative_rainfall"],
                river_level=env["river_level"],
                danger_level=env["danger_level"],
                water_level_change_rate=env["water_level_change_rate"],
                water_depth=env["water_depth"],
                timestamp=now
            )
            db.add(er)
            env_entities.append(er)
    db.commit()

    # 7. Seed Multilingual Citizen SOS Reports
    sos_entities = []
    assigned_team = team_entities[0] if team_entities else None
    for idx, sd in enumerate(MOCK_SOS_REPORTS):
        mins = sd.pop("minutes_ago", 0)
        team_id = assigned_team.id if sd["status"] in ["ASSIGNED", "EN_ROUTE"] and assigned_team else None
        sos = SOSReport(
            user_id=user_entities[0].id if user_entities else None,
            message=sd["message"],
            language=sd["language"],
            need_type=sd["need_type"],
            urgency=sd["urgency"],
            latitude=sd["latitude"],
            longitude=sd["longitude"],
            priority_score=sd["priority_score"],
            status=sd["status"],
            assigned_team_id=team_id,
            timestamp=now - timedelta(minutes=mins)
        )
        db.add(sos)
        sos_entities.append(sos)
    db.commit()

    # 8. Phase 8 – Seed Relief Camps
    camp_entities = []
    for cd in MOCK_RELIEF_CAMPS:
        camp = ReliefCamp(**cd)
        db.add(camp)
        camp_entities.append(camp)
    db.commit()

    # 9. Phase 8 – Seed Resource Inventory
    res_entities = []
    for rd in MOCK_RESOURCES:
        resource = ResourceInventory(**rd)
        db.add(resource)
        res_entities.append(resource)
    db.commit()

    # 10. Phase 8 – Seed Relief Teams
    relief_team_entities = []
    for rtd in MOCK_RELIEF_TEAMS:
        rt = ReliefTeam(**rtd)
        db.add(rt)
        relief_team_entities.append(rt)
    db.commit()

    # 11. Phase 8 – Seed Relief Requests
    req_entities = []
    for rqd in MOCK_RELIEF_REQUESTS:
        req = ReliefRequest(**rqd)
        db.add(req)
        req_entities.append(req)
    db.commit()

    # 12. Phase 8 – Seed Recovery Items
    recovery_entities = []
    for rcd in MOCK_RECOVERY_ITEMS:
        item = RecoveryItem(**rcd)
        db.add(item)
        recovery_entities.append(item)
    db.commit()

    # 13. Phase 8 – Seed Zone Damage Assessments
    damage_entities = []
    for da in MOCK_DAMAGE_ASSESSMENTS:
        assessment = ZoneDamageAssessment(**da)
        db.add(assessment)
        damage_entities.append(assessment)
    db.commit()

    # 14. Phase 8 – Seed Relief Fund & Initial Donations
    fund = ReliefFund(
        campaign_name="Krishna Delta Flood Relief & Rehabilitation Fund",
        target_amount=50000000.0,
        raised_amount=24500000.0,
        donor_count=1420,
        food_relief_allocation=7500000.0,
        medical_aid_allocation=5000000.0,
        shelters_allocation=6000000.0,
        infrastructure_allocation=4500000.0,
        emergency_cash_allocation=1500000.0,
    )
    db.add(fund)
    db.commit()

    donations = [
        ReliefDonation(
            donor_name="AP Chamber of Commerce & Industry",
            amount=5000000.0,
            category="Infrastructure Rehabilitation",
            transaction_ref="TXN-KD-CORP01",
            payment_method="Corporate CSR Grant",
            message="Support for repairing flooded schools and community dispensaries."
        ),
        ReliefDonation(
            donor_name="Krishna River Delta Relief Consortium",
            amount=2500000.0,
            category="Emergency Medical Aid",
            transaction_ref="TXN-KD-CORP02",
            payment_method="Bank Transfer (Demo)",
            message="Provision for life-saving insulin, pediatric medicines, and mobile medical vans."
        ),
        ReliefDonation(
            donor_name="Anonymous Citizen Donor",
            amount=50000.0,
            category="Food & Rations",
            transaction_ref="TXN-KD-UPI01",
            payment_method="UPI (Demo)",
            message="For hot meals distribution in Krishnalanka and Bhavanipuram."
        ),
        ReliefDonation(
            donor_name="Vijayawada Alumni Association",
            amount=150000.0,
            category="Safe Shelters & Tents",
            transaction_ref="TXN-KD-UPI02",
            payment_method="UPI (Demo)",
            message="Emergency waterproof tarpaulins and clean drinking water tankers."
        ),
    ]
    for d in donations:
        db.add(d)
    db.commit()

    return {
        "status": "success",
        "message": "Fictional Krishna River Delta disaster scenario mock data seeded successfully",
        "counts": {
            "zones": len(zone_entities),
            "alerts": len(alert_entities),
            "drone_readings": len(drone_entities),
            "environmental_readings": len(env_entities),
            "sos_reports": len(sos_entities),
            "teams": len(team_entities),
            "users": len(user_entities),
            "relief_camps": len(camp_entities),
            "resources": len(res_entities),
            "relief_teams": len(relief_team_entities),
            "relief_requests": len(req_entities),
            "recovery_items": len(recovery_entities),
            "damage_assessments": len(damage_entities),
            "relief_donations": len(donations),
        }
    }


def get_mock_data_status(db: Session) -> dict:
    """Returns current counts and summary of simulated entities in the database."""
    return {
        "status": "active",
        "counts": {
            "zones": db.query(Zone).count(),
            "alerts": db.query(Alert).count(),
            "drone_readings": db.query(DroneReading).count(),
            "environmental_readings": db.query(EnvironmentalReading).count(),
            "sos_reports": db.query(SOSReport).count(),
            "teams": db.query(Team).count(),
            "users": db.query(User).count(),
            "relief_camps": db.query(ReliefCamp).count(),
            "resources": db.query(ResourceInventory).count(),
            "relief_teams": db.query(ReliefTeam).count(),
            "relief_requests": db.query(ReliefRequest).count(),
            "recovery_items": db.query(RecoveryItem).count(),
            "damage_assessments": db.query(ZoneDamageAssessment).count(),
        },
        "critical_sos_count": db.query(SOSReport).filter(SOSReport.urgency == "critical").count(),
        "blocked_roads_count": db.query(DroneReading).filter(DroneReading.road_status == "blocked").count(),
        "red_zones_count": db.query(Zone).filter(Zone.risk_level == "RED").count(),
        "pending_relief_requests": db.query(ReliefRequest).filter(ReliefRequest.status == "Pending").count(),
        "critical_damage_zones": db.query(ZoneDamageAssessment).filter(ZoneDamageAssessment.damage_severity == "CRITICAL").count(),
    }

