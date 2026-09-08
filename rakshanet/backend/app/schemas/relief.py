from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# -----------------------------------------------------------------------
# RELIEF CAMP SCHEMAS
# -----------------------------------------------------------------------

class ReliefCampBase(BaseModel):
    name: str
    location_name: str
    latitude: float
    longitude: float
    capacity: int = 1000
    current_occupancy: int = 0
    available_beds: int = 1000
    food_availability: str = "Adequate"       # Surplus, Adequate, Low, Critical
    water_availability: str = "Adequate"      # Surplus, Adequate, Low, Critical
    medical_support: str = "Available"        # Full Clinic, Available, First Aid Only, None
    contact_person: Optional[str] = "Camp Coordinator"
    contact_phone: Optional[str] = "+91 94400 11223"
    status: str = "Available"                 # Available, Near Capacity, Full


class ReliefCampCreate(ReliefCampBase):
    pass


class ReliefCampUpdate(BaseModel):
    current_occupancy: Optional[int] = None
    available_beds: Optional[int] = None
    food_availability: Optional[str] = None
    water_availability: Optional[str] = None
    medical_support: Optional[str] = None
    status: Optional[str] = None


class ReliefCampResponse(ReliefCampBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------
# RELIEF REQUEST SCHEMAS
# -----------------------------------------------------------------------

class ReliefRequestBase(BaseModel):
    location_name: str
    latitude: float
    longitude: float
    zone_id: Optional[int] = None
    category: str = Field(description="Food, Drinking Water, Medicine, Shelter, Rescue, Medical Emergency, Clothing, Other")
    priority: str = Field(default="High", description="Critical, High, Medium, Low")
    people_count: int = 1
    notes: Optional[str] = None


class ReliefRequestCreate(ReliefRequestBase):
    request_code: Optional[str] = None


class ReliefRequestUpdate(BaseModel):
    status: Optional[str] = Field(None, description="Pending, Assigned, In Progress, Completed")
    assigned_team_id: Optional[int] = None
    assigned_team_name: Optional[str] = None
    priority: Optional[str] = None
    notes: Optional[str] = None


class ReliefRequestResponse(ReliefRequestBase):
    id: int
    request_code: str
    priority_score: float
    status: str
    assigned_team_id: Optional[int] = None
    assigned_team_name: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------
# RESOURCE INVENTORY SCHEMAS
# -----------------------------------------------------------------------

class ResourceInventoryBase(BaseModel):
    item_name: str
    category: str = "General"
    unit: str = "units"
    available_qty: int = 0
    required_qty: int = 0
    distributed_qty: int = 0
    low_stock_threshold: int = 100


class ResourceInventoryCreate(ResourceInventoryBase):
    pass


class ResourceInventoryUpdate(BaseModel):
    available_qty: Optional[int] = None
    required_qty: Optional[int] = None
    distributed_qty: Optional[int] = None
    low_stock_threshold: Optional[int] = None


class ResourceInventoryResponse(ResourceInventoryBase):
    id: int
    remaining_qty: int = 0
    low_stock_warning: bool = False
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------
# RELIEF TEAM SCHEMAS
# -----------------------------------------------------------------------

class ReliefTeamBase(BaseModel):
    team_code: str
    name: str
    team_type: str = Field(description="Rescue, Medical, Food Distribution, Infrastructure, Search & Rescue")
    location_name: str
    latitude: float
    longitude: float
    members: int = 6
    leader_name: Optional[str] = "Team Lead"
    contact_phone: Optional[str] = "+91 94400 33445"
    assigned_task: Optional[str] = "Standby at Operations Base"
    status: str = Field(default="Available", description="Available, Assigned, On Mission, Completed")


class ReliefTeamCreate(ReliefTeamBase):
    pass


class ReliefTeamUpdate(BaseModel):
    status: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    assigned_task: Optional[str] = None


class ReliefTeamResponse(ReliefTeamBase):
    id: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------
# RECOVERY ITEM SCHEMAS
# -----------------------------------------------------------------------

class RecoveryItemBase(BaseModel):
    item_code: str
    name: str
    category: str = Field(description="Roads, Bridges, Electricity, Water supply, Hospitals, Schools, Communication infrastructure, Housing")
    location_name: str
    latitude: float
    longitude: float
    damage_level: str = "Moderate"        # Severe, Moderate, Minor
    recovery_status: str = "Assessment"   # Not Started, Assessment, Repairing, Restored
    progress_pct: int = 0                 # 0-100
    assigned_team: Optional[str] = "Unassigned"
    estimated_completion: Optional[str] = "3 days"
    notes: Optional[str] = None


class RecoveryItemCreate(RecoveryItemBase):
    pass


class RecoveryItemUpdate(BaseModel):
    recovery_status: Optional[str] = None
    progress_pct: Optional[int] = None
    assigned_team: Optional[str] = None
    estimated_completion: Optional[str] = None
    notes: Optional[str] = None


class RecoveryItemResponse(RecoveryItemBase):
    id: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------
# POST-DISASTER DASHBOARD SUMMARY SCHEMA
# -----------------------------------------------------------------------

class ReliefSummaryResponse(BaseModel):
    total_affected_people: int
    people_requiring_urgent_assistance: int
    total_relief_camps: int
    total_camp_capacity: int
    total_camp_occupancy: int
    camp_occupancy_rate_pct: float
    available_food_packets: int
    available_water_units: int
    available_medical_kits: int
    total_relief_teams: int
    active_teams_on_mission: int
    pending_relief_requests: int
    critical_pending_requests: int
    recovery_progress_percentage: float
    low_stock_items: List[str] = []


# -----------------------------------------------------------------------
# DAMAGE & NEEDS ASSESSMENT SCHEMAS (PHASE 8)
# -----------------------------------------------------------------------

class DamageAssessmentBase(BaseModel):
    zone_id: int
    zone_name: str
    damage_severity: str = Field(default="HIGH", description="LOW, MEDIUM, HIGH, CRITICAL")
    assessment_status: str = Field(default="ASSESSED", description="PENDING, ASSESSED, VERIFIED")
    buildings_damage: str = "Moderate structural flooding, roofs damaged"
    roads_bridges_damage: str = "Arterial routes partially inundated"
    infrastructure_damage: str = "Power substation submerged, water mains burst"
    affected_people: int = 5000
    injured_count: int = 45
    missing_count: int = 3
    rescued_count: int = 210
    displaced_count: int = 1800
    food_packets_needed: int = 3500
    water_liters_needed: int = 7000
    medical_kits_needed: int = 120
    shelter_tents_needed: int = 250
    blankets_needed: int = 1500
    urgent_requirements: str = "Emergency pediatric medical supplies and clean drinking water"
    priority_level: str = Field(default="HIGH", description="CRITICAL, HIGH, MEDIUM, LOW")
    priority_score: float = 85.0


class DamageAssessmentCreate(DamageAssessmentBase):
    pass


class DamageAssessmentUpdate(BaseModel):
    damage_severity: Optional[str] = None
    assessment_status: Optional[str] = None
    buildings_damage: Optional[str] = None
    roads_bridges_damage: Optional[str] = None
    infrastructure_damage: Optional[str] = None
    affected_people: Optional[int] = None
    injured_count: Optional[int] = None
    missing_count: Optional[int] = None
    rescued_count: Optional[int] = None
    displaced_count: Optional[int] = None
    food_packets_needed: Optional[int] = None
    water_liters_needed: Optional[int] = None
    medical_kits_needed: Optional[int] = None
    shelter_tents_needed: Optional[int] = None
    blankets_needed: Optional[int] = None
    urgent_requirements: Optional[str] = None
    priority_level: Optional[str] = None
    priority_score: Optional[float] = None


class DamageAssessmentResponse(DamageAssessmentBase):
    id: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# -----------------------------------------------------------------------
# RELIEF FUNDRAISING & DONATIONS SCHEMAS (PHASE 8)
# -----------------------------------------------------------------------

class ReliefFundResponse(BaseModel):
    id: int
    campaign_name: str
    target_amount: float
    raised_amount: float
    remaining_amount: float
    donor_count: int
    funding_progress_pct: float
    food_relief_allocation: float
    medical_aid_allocation: float
    shelters_allocation: float
    infrastructure_allocation: float
    emergency_cash_allocation: float
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReliefDonationCreate(BaseModel):
    donor_name: str = "Anonymous Supporter"
    amount: float = Field(gt=0, description="Donation amount in INR")
    category: str = "All Areas (General Relief)"
    message: Optional[str] = None


class ReliefDonationResponse(BaseModel):
    id: int
    donor_name: str
    amount: float
    category: str
    transaction_ref: str
    payment_method: str
    message: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

