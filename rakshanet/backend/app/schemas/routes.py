from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class Waypoint(BaseModel):
    latitude: float
    longitude: float
    name: Optional[str] = None
    instruction: Optional[str] = None


class HazardAvoided(BaseModel):
    latitude: float
    longitude: float
    obstacle_type: str
    water_depth: float
    road_status: str
    distance_to_route_m: float


class AlternativeRouteInfo(BaseModel):
    destination_shelter_id: str
    destination_name: str
    waypoints: List[List[float]] = Field(default_factory=list, description="Array of [lat, lon] coordinates for alternative polyline")
    distance_km: float
    estimated_time_minutes: int
    safety_score: float
    status: str
    corridor_notes: List[str] = []


class EvacuationRouteResponse(BaseModel):
    route_id: str
    origin_zone_id: int
    origin_name: str
    destination_shelter_id: str
    destination_name: str
    waypoints: List[List[float]] = Field(description="Array of [lat, lon] coordinates for polyline")
    waypoint_details: List[Waypoint] = []
    distance_km: float
    estimated_time_minutes: int
    safety_score: float = Field(description="Safety index 0-100 where 100 is completely safe")
    route_risk_level: str = Field(default="LOW", description="Route Risk Level: LOW, MODERATE, or HIGH")
    status: str = Field(description="OPTIMAL_SAFE, CAUTION_RESTRICTED, or IMPASSABLE")
    hazards_avoided: List[HazardAvoided] = []
    corridor_notes: List[str] = []
    alternative_route: Optional[AlternativeRouteInfo] = None



class DroneReconMissionResponse(BaseModel):
    mission_id: str
    drone_callsign: str
    base_hub: str
    flight_path: List[List[float]] = Field(description="Array of [lat, lon] coordinates for flight polyline")
    waypoints: List[Waypoint] = []
    total_distance_km: float
    estimated_flight_minutes: int
    priority_targets: List[str] = []
    mission_objective: str


class CustomRouteRequest(BaseModel):
    origin_lat: float
    origin_lon: float
    destination_lat: float
    destination_lon: float
    vehicle_type: Optional[str] = "rescue_truck"


class ShelterInfo(BaseModel):
    shelter_id: str
    name: str
    latitude: float
    longitude: float
    capacity: int
    current_occupancy: int
    elevation_meters: float
    status: str
    medical_facility: bool
    food_water_supply: bool
