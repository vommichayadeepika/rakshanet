from typing import List, Optional, Dict
from pydantic import BaseModel, ConfigDict, Field


class TrajectorySchema(BaseModel):
    trend: str = Field(default="stable", description="Overall trajectory: improving, stable, worsening")
    h3: str = Field(alias="3h", default="STABLE")
    h6: str = Field(alias="6h", default="STABLE")
    h24: str = Field(alias="24h", default="STABLE")

    model_config = ConfigDict(populate_by_name=True)


class ScoreBreakdown(BaseModel):
    hazard_score: float = Field(description="Environmental flood hazard rating (0-100)")
    rainfall_component: float = Field(description="Rainfall intensity & saturation impact")
    river_component: float = Field(description="River surge & water depth index")
    alert_component: float = Field(description="Correlated SACHET/IMD warning level")
    sos_urgency_component: float = Field(description="Citizen distress & medical urgency factor")
    isolation_component: float = Field(description="Drone-reported road cutoffs and isolation risk")
    population_component: float = Field(description="Vulnerable population exposure")
    data_freshness_factor: float = Field(description="Sensor and drone reading freshness weight (0.0-1.0)")


class ZoneIntelligenceResponse(BaseModel):
    zone_id: int
    zone_name: str
    latitude: Optional[float] = Field(default=None, description="Centroid latitude")
    longitude: Optional[float] = Field(default=None, description="Centroid longitude")
    risk_score: float
    risk_level: str  # GREEN, YELLOW, ORANGE, RED
    trajectory: TrajectorySchema
    overall_trajectory: str = "stable"  # improving, stable, worsening
    response_priority_score: float = 0.0
    response_priority_rank: int = 1
    recommended_action: str
    active_sos_count: int = 0
    affected_population: int = 0

    
    # Backward compatibility aliases for Phase 1 endpoints
    impact_score: Optional[float] = None
    response_priority: Optional[float] = None
    priority_rank: Optional[int] = None
    active_sos: Optional[int] = None
    population: Optional[int] = None

    score_breakdown: ScoreBreakdown
    reasoning: List[str]
    disclaimer: str = (
        "AI-assisted decision-support recommendation for simulation and triage. "
        "Field operations require incident commander verification."
    )

    model_config = ConfigDict(populate_by_name=True)
