from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey
from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class ReliefCamp(Base):
    __tablename__ = "relief_camps"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    location_name = Column(String(150), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    capacity = Column(Integer, default=1000)
    current_occupancy = Column(Integer, default=0)
    available_beds = Column(Integer, default=1000)
    food_availability = Column(String(50), default="Adequate")       # Surplus, Adequate, Low, Critical
    water_availability = Column(String(50), default="Adequate")      # Surplus, Adequate, Low, Critical
    medical_support = Column(String(50), default="Available")        # Full Clinic, Available, First Aid Only, None
    contact_person = Column(String(100), default="Camp Coordinator")
    contact_phone = Column(String(50), default="+91 94400 11223")
    status = Column(String(50), default="Available")                 # Available, Near Capacity, Full
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class ReliefRequest(Base):
    __tablename__ = "relief_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_code = Column(String(50), unique=True, index=True, nullable=False)
    location_name = Column(String(150), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    zone_id = Column(Integer, nullable=True)
    category = Column(String(50), nullable=False)                    # Food, Drinking Water, Medicine, Shelter, Rescue, Medical Emergency, Clothing, Other
    priority = Column(String(30), default="High")                    # Critical, High, Medium, Low
    priority_score = Column(Float, default=70.0)                     # 0-100 transparent decision score
    people_count = Column(Integer, default=1)
    status = Column(String(30), default="Pending")                   # Pending, Assigned, In Progress, Completed
    assigned_team_id = Column(Integer, nullable=True)
    assigned_team_name = Column(String(120), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utc_now)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class ResourceInventory(Base):
    __tablename__ = "resource_inventory"

    id = Column(Integer, primary_key=True, index=True)
    item_name = Column(String(120), unique=True, nullable=False)
    category = Column(String(50), default="General")                 # Food, Water, Medical, Shelter/Warmth, Sanitation
    unit = Column(String(30), default="units")                       # packets, cans, kits, pieces
    available_qty = Column(Integer, default=0)
    required_qty = Column(Integer, default=0)
    distributed_qty = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=100)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class ReliefTeam(Base):
    __tablename__ = "relief_teams"

    id = Column(Integer, primary_key=True, index=True)
    team_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(120), nullable=False)
    team_type = Column(String(50), nullable=False)                   # Rescue, Medical, Food Distribution, Infrastructure, Search & Rescue
    location_name = Column(String(150), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    members = Column(Integer, default=6)
    leader_name = Column(String(100), default="Team Lead")
    contact_phone = Column(String(50), default="+91 94400 33445")
    assigned_task = Column(String(200), default="Standby at Operations Base")
    status = Column(String(30), default="Available")                 # Available, Assigned, On Mission, Completed
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class RecoveryItem(Base):
    __tablename__ = "recovery_items"

    id = Column(Integer, primary_key=True, index=True)
    item_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(150), nullable=False)
    category = Column(String(50), nullable=False)                    # Roads, Bridges, Electricity, Water supply, Hospitals, Schools, Communication infrastructure, Housing
    location_name = Column(String(150), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    damage_level = Column(String(30), default="Moderate")            # Severe, Moderate, Minor
    recovery_status = Column(String(30), default="Assessment")       # Not Started, Assessment, Repairing, Restored
    progress_pct = Column(Integer, default=0)                        # 0-100
    assigned_team = Column(String(120), default="Unassigned")
    estimated_completion = Column(String(50), default="3 days")
    notes = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class ZoneDamageAssessment(Base):
    __tablename__ = "damage_assessments"

    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, nullable=False, unique=True, index=True)
    zone_name = Column(String(100), nullable=False)
    damage_severity = Column(String(30), default="HIGH")       # LOW, MEDIUM, HIGH, CRITICAL
    assessment_status = Column(String(30), default="ASSESSED") # PENDING, ASSESSED, VERIFIED
    buildings_damage = Column(String(250), default="Moderate structural flooding, roofs damaged")
    roads_bridges_damage = Column(String(250), default="Arterial routes partially inundated")
    infrastructure_damage = Column(String(250), default="Power substation submerged, water mains burst")
    
    # Human Impact
    affected_people = Column(Integer, default=5000)
    injured_count = Column(Integer, default=45)
    missing_count = Column(Integer, default=3)
    rescued_count = Column(Integer, default=210)
    displaced_count = Column(Integer, default=1800)

    # Relief Needs
    food_packets_needed = Column(Integer, default=3500)
    water_liters_needed = Column(Integer, default=7000)
    medical_kits_needed = Column(Integer, default=120)
    shelter_tents_needed = Column(Integer, default=250)
    blankets_needed = Column(Integer, default=1500)
    urgent_requirements = Column(Text, default="Emergency pediatric medical supplies and clean drinking water")

    # Priority Classification
    priority_level = Column(String(30), default="HIGH")        # CRITICAL, HIGH, MEDIUM, LOW
    priority_score = Column(Float, default=85.0)

    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class ReliefFund(Base):
    __tablename__ = "relief_funds"

    id = Column(Integer, primary_key=True, index=True)
    campaign_name = Column(String(150), default="Krishna Delta Flood Relief & Rehabilitation Fund")
    target_amount = Column(Float, default=50000000.0)    # 5 Crore INR target
    raised_amount = Column(Float, default=24500000.0)    # 2.45 Crore INR raised
    donor_count = Column(Integer, default=1420)
    food_relief_allocation = Column(Float, default=7500000.0)
    medical_aid_allocation = Column(Float, default=5000000.0)
    shelters_allocation = Column(Float, default=6000000.0)
    infrastructure_allocation = Column(Float, default=4500000.0)
    emergency_cash_allocation = Column(Float, default=1500000.0)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now)


class ReliefDonation(Base):
    __tablename__ = "relief_donations"

    id = Column(Integer, primary_key=True, index=True)
    donor_name = Column(String(120), nullable=False)
    amount = Column(Float, nullable=False)
    category = Column(String(80), default="All Areas (General Relief)")
    transaction_ref = Column(String(80), unique=True, index=True, nullable=False)
    payment_method = Column(String(50), default="UPI / Direct Transfer (Demo)")
    message = Column(String(250), nullable=True)
    created_at = Column(DateTime, default=utc_now)

