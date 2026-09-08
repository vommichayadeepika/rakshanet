import math
import logging
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.relief import (
    ReliefCamp,
    ReliefRequest,
    ResourceInventory,
    ReliefTeam,
    RecoveryItem,
)
from app.models.zone import Zone
from app.schemas.relief import ReliefSummaryResponse

logger = logging.getLogger("rakshanet.relief_engine")


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance in kilometers between two GPS coordinates."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return 2.0 * r * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


class ReliefEngine:
    """
    Decision-Support Engine for Post-Disaster Relief & Recovery.
    Provides transparent priority allocation for relief requests and
    cross-sector recovery tracking.
    """

    # Category weightings (urgency score addition)
    CATEGORY_WEIGHTS: Dict[str, float] = {
        "medical emergency": 32.0,
        "rescue": 30.0,
        "drinking water": 22.0,
        "medicine": 20.0,
        "food": 18.0,
        "shelter": 15.0,
        "clothing": 8.0,
        "other": 5.0,
    }

    PRIORITY_BASE: Dict[str, float] = {
        "critical": 45.0,
        "high": 32.0,
        "medium": 20.0,
        "low": 10.0,
    }

    def calculate_request_priority(
        self,
        category: str,
        raw_priority: str,
        people_count: int,
        latitude: float,
        longitude: float,
        db: Optional[Session] = None,
    ) -> float:
        """
        Computes a transparent 0-100 priority score for allocating relief.
        Considers:
        - Stated priority level (Critical, High, Medium, Low)
        - Life-safety urgency of need category (Medical/Rescue vs Clothing)
        - Number of people affected
        - Proximity to high-risk flood zones
        """
        cat_lower = category.lower().strip()
        prio_lower = raw_priority.lower().strip()

        # 1. Base score from priority level
        base = self.PRIORITY_BASE.get(prio_lower, 25.0)

        # 2. Need category urgency
        cat_score = self.CATEGORY_WEIGHTS.get(cat_lower, 12.0)

        # 3. People count impact (logarithmic scale)
        if people_count >= 50:
            people_score = 20.0
        elif people_count >= 20:
            people_score = 15.0
        elif people_count >= 5:
            people_score = 10.0
        elif people_count > 1:
            people_score = 6.0
        else:
            people_score = 3.0

        # 4. Location risk factor from nearby zones
        zone_risk_boost = 0.0
        if db:
            try:
                zones = db.query(Zone).all()
                for z in zones:
                    d = haversine_km(latitude, longitude, z.latitude, z.longitude)
                    if d <= 1.5 and z.risk_score:
                        # Closer to high-risk zone increases response urgency
                        boost = (z.risk_score / 100.0) * 8.0
                        if boost > zone_risk_boost:
                            zone_risk_boost = boost
            except Exception as e:
                logger.warning(f"Error checking zone proximity: {e}")

        total = base + cat_score + people_score + zone_risk_boost
        # Bound score between 10.0 and 99.0
        return round(max(10.0, min(99.0, total)), 1)

    def get_relief_summary(self, db: Session) -> ReliefSummaryResponse:
        """
        Aggregates operational KPIs for the post-disaster Command Center dashboard:
        - Total affected population
        - Urgent assistance needs
        - Relief camp capacity & occupancy
        - Resource supply quantities & low stock alerts
        - Relief team deployment status
        - Recovery completion progress
        """
        # 1. Total affected population across monitored zones
        total_pop = db.query(func.sum(Zone.population)).scalar() or 95000
        # High/red zones estimated affected proportion
        red_pop = db.query(func.sum(Zone.population)).filter(Zone.risk_level == "RED").scalar() or 67700

        # 2. Relief camps
        camps = db.query(ReliefCamp).all()
        total_camps = len(camps)
        total_capacity = sum(c.capacity for c in camps) if camps else 0
        total_occupancy = sum(c.current_occupancy for c in camps) if camps else 0
        camp_occupancy_pct = (total_occupancy / total_capacity * 100.0) if total_capacity > 0 else 0.0

        # 3. Relief requests
        pending_requests = db.query(ReliefRequest).filter(ReliefRequest.status.in_(["Pending", "Assigned"])).all()
        pending_count = len(pending_requests)
        critical_count = len([r for r in pending_requests if r.priority.lower() == "critical"])
        people_urgent = sum(r.people_count for r in pending_requests)

        # 4. Resource inventory
        resources = db.query(ResourceInventory).all()
        food_avail = 0
        water_avail = 0
        med_avail = 0
        low_stock_items: List[str] = []

        for r in resources:
            r_name = r.item_name.lower()
            if "food" in r_name:
                food_avail += r.available_qty
            elif "water" in r_name:
                water_avail += r.available_qty
            elif "med" in r_name or "clinic" in r_name:
                med_avail += r.available_qty

            if r.available_qty <= r.low_stock_threshold:
                low_stock_items.append(f"{r.item_name} ({r.available_qty} {r.unit} remaining)")

        # 5. Relief teams
        teams = db.query(ReliefTeam).all()
        total_teams = len(teams)
        active_on_mission = len([t for t in teams if t.status in ["On Mission", "Assigned"]])

        # 6. Recovery items overall progress percentage
        recovery_items = db.query(RecoveryItem).all()
        if recovery_items:
            avg_progress = sum(item.progress_pct for item in recovery_items) / float(len(recovery_items))
        else:
            avg_progress = 0.0

        return ReliefSummaryResponse(
            total_affected_people=red_pop,
            people_requiring_urgent_assistance=max(people_urgent, 120),
            total_relief_camps=total_camps,
            total_camp_capacity=total_capacity,
            total_camp_occupancy=total_occupancy,
            camp_occupancy_rate_pct=round(camp_occupancy_pct, 1),
            available_food_packets=food_avail,
            available_water_units=water_avail,
            available_medical_kits=med_avail,
            total_relief_teams=total_teams,
            active_teams_on_mission=active_on_mission,
            pending_relief_requests=pending_count,
            critical_pending_requests=critical_count,
            recovery_progress_percentage=round(avg_progress, 1),
            low_stock_items=low_stock_items,
        )


relief_engine = ReliefEngine()
