import math
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Tuple, Optional
from sqlalchemy.orm import Session

from app.models.zone import Zone
from app.models.alert import Alert
from app.models.drone import DroneReading
from app.models.sos import SOSReport
from app.models.environmental import EnvironmentalReading
from app.schemas.intelligence import ZoneIntelligenceResponse, TrajectorySchema, ScoreBreakdown


def utc_now():
    return datetime.now(timezone.utc)


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two geographic coordinates in kilometers."""
    R = 6371.0  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2.0) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2.0) ** 2)
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return R * c


class AIRiskEngine:
    """
    RakshaNet AI Risk & Response-Priority Engine.
    
    Combines multi-source disaster indicators:
    - Hydrological telemetry (rainfall intensity, river surge, water depth)
    - SACHET-NDMA, IMD, CWC disaster alert vectors
    - Aerial drone road survey observations
    - Multilingual citizen SOS emergency reports
    
    Produces transparent risk scoring (0-100), response priority rankings,
    multi-horizon predictive trajectories, and explainable action recommendations.
    """

    SEVERITY_WEIGHTS = {
        "SEVERE": 95.0,
        "WARNING": 75.0,
        "ALERT": 50.0,
        "WATCH": 25.0
    }

    NEED_WEIGHTS = {
        "medical": 1.4,
        "rescue": 1.35,
        "water": 1.1,
        "food": 1.05,
        "evacuation": 1.25,
        "shelter": 1.0,
        "other": 1.0
    }

    URGENCY_SCORES = {
        "critical": 30.0,
        "high": 15.0,
        "medium": 7.0,
        "low": 3.0
    }

    def compute_data_freshness_factor(self, timestamp: Optional[datetime]) -> float:
        """
        Calculates time-decay factor (0.5 to 1.0) based on how recently data was ingested.
        Fresh data (<30m) = 1.0, decaying gradually over 6 hours.
        """
        if not timestamp:
            return 0.85
        now = utc_now()
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        diff_minutes = max(0.0, (now - timestamp).total_seconds() / 60.0)
        if diff_minutes <= 30.0:
            return 1.0
        elif diff_minutes <= 180.0:
            return max(0.75, 1.0 - ((diff_minutes - 30.0) / 150.0) * 0.25)
        else:
            return max(0.5, 0.75 - ((diff_minutes - 180.0) / 360.0) * 0.25)

    def calculate_environmental_hazard(
        self,
        env_reading: Optional[EnvironmentalReading]
    ) -> Tuple[float, float, float, float]:
        """
        Calculates environmental hazard score (0-100) split into:
        (hazard_score, rainfall_component, river_component, rate_of_rise)
        """
        if not env_reading:
            return 10.0, 10.0, 10.0, 0.0

        # 1. Rainfall intensity & cumulative saturation
        rain_intensity_score = min(100.0, (env_reading.rainfall_intensity / 100.0) * 100.0)
        cumulative_score = min(100.0, (env_reading.cumulative_rainfall / 250.0) * 100.0)
        rainfall_component = round(0.6 * rain_intensity_score + 0.4 * cumulative_score, 1)

        # 2. River surge and local water depth
        river_excess = max(0.0, env_reading.river_level - env_reading.danger_level)
        river_surge_score = min(100.0, (river_excess / 2.5) * 60.0 + (35.0 if river_excess > 0 else 0.0))
        depth_score = min(100.0, (env_reading.water_depth / 2.0) * 100.0)
        rate_bonus = min(25.0, max(0.0, env_reading.water_level_change_rate * 25.0))
        river_component = round(min(100.0, 0.45 * river_surge_score + 0.40 * depth_score + rate_bonus), 1)

        # Composite hazard (0-100)
        composite = round(0.48 * river_component + 0.52 * rainfall_component, 1)
        return composite, rainfall_component, river_component, env_reading.water_level_change_rate

    def correlate_alerts(self, zone: Zone, alerts: List[Alert]) -> float:
        """
        Correlates active disaster alerts within proximity of the zone.
        Uses distance attenuation within alert radius.
        """
        if not alerts:
            return 0.0

        max_alert_score = 0.0
        for alert in alerts:
            dist = haversine_distance_km(zone.latitude, zone.longitude, alert.latitude, alert.longitude)
            if dist <= alert.radius:
                base_val = self.SEVERITY_WEIGHTS.get(alert.severity, 30.0)
                proximity_factor = max(0.4, 1.0 - (dist / alert.radius) * 0.6)
                alert_val = base_val * proximity_factor
                if alert_val > max_alert_score:
                    max_alert_score = alert_val

        return round(min(100.0, max_alert_score), 1)

    def is_assigned_to_zone(self, lat: float, lon: float, zone: Zone, all_zones: List[Zone], max_dist_km: float = 6.0) -> bool:
        """
        Voronoi-style nearest-zone spatial association.
        Prevents observations across physical barriers (e.g. river boundary) from leaking into safe zones.
        """
        if not all_zones:
            return True
        closest_dist = float("inf")
        closest_id = None
        for z in all_zones:
            d = haversine_distance_km(lat, lon, z.latitude, z.longitude)
            if d < closest_dist:
                closest_dist = d
                closest_id = z.id
        return closest_id == zone.id and closest_dist <= max_dist_km

    def correlate_drone_blockages(self, zone: Zone, drone_readings: List[DroneReading], all_zones: List[Zone]) -> Tuple[int, int, float]:
        """
        Finds drone road blockage reports partitioned to this zone.
        Returns: (blocked_count, restricted_count, isolation_score)
        """
        blocked_count = 0
        restricted_count = 0

        for dr in drone_readings:
            if self.is_assigned_to_zone(dr.latitude, dr.longitude, zone, all_zones):
                if dr.road_status == "blocked":
                    blocked_count += 1
                elif dr.road_status == "restricted":
                    restricted_count += 1

        isolation_score = round(min(100.0, (blocked_count * 35.0) + (restricted_count * 15.0)), 1)
        return blocked_count, restricted_count, isolation_score

    def correlate_sos_distress(self, zone: Zone, sos_reports: List[SOSReport], all_zones: List[Zone]) -> Tuple[int, int, int, float, bool]:
        """
        Gathers active citizen SOS distress signals partitioned to this zone.
        Returns: (total_sos, critical_sos, medical_sos, distress_component, has_trapped)
        """
        total_sos = 0
        critical_sos = 0
        medical_sos = 0
        has_trapped = False
        raw_distress = 0.0

        active_statuses = ["SUBMITTED", "ASSIGNED", "EN_ROUTE", "ON_SITE"]

        for sos in sos_reports:
            if sos.status not in active_statuses:
                continue
            if self.is_assigned_to_zone(sos.latitude, sos.longitude, zone, all_zones):
                total_sos += 1
                if sos.urgency == "critical":
                    critical_sos += 1
                if sos.need_type == "medical":
                    medical_sos += 1
                if sos.need_type == "rescue" or "trapped" in sos.message.lower() or "చిక్కు" in sos.message:
                    has_trapped = True

                weight = self.NEED_WEIGHTS.get(sos.need_type, 1.0)
                urgency_pts = self.URGENCY_SCORES.get(sos.urgency, 8.0)
                raw_distress += (urgency_pts * weight)

        distress_component = round(min(100.0, raw_distress * 1.25), 1)
        return total_sos, critical_sos, medical_sos, distress_component, has_trapped

    def determine_trajectory(
        self,
        risk_score: float,
        rate_of_rise: float,
        rainfall_intensity: float,
        alert_score: float
    ) -> Tuple[str, TrajectorySchema]:
        """
        Calculates short-term overall trajectory and 3h/6h/24h predictive horizons.
        """
        if rate_of_rise > 0.15 or rainfall_intensity > 40.0 or alert_score >= 75.0:
            overall = "worsening"
        elif rate_of_rise < -0.02 and rainfall_intensity < 15.0 and risk_score < 30.0:
            overall = "improving"
        else:
            overall = "stable"

        if risk_score >= 80.0 or rate_of_rise >= 0.50:
            forecast = TrajectorySchema(trend=overall, h3="WORSENING", h6="SEVERE", h24="CRITICAL")
        elif risk_score >= 60.0 or rate_of_rise >= 0.20:
            forecast = TrajectorySchema(trend=overall, h3="WORSENING", h6="HIGH", h24="SEVERE")
        elif risk_score >= 35.0:
            forecast = TrajectorySchema(trend=overall, h3="STABLE", h6="MODERATE", h24="WATCH")
        else:
            forecast = TrajectorySchema(trend=overall, h3="IMPROVING", h6="STABLE", h24="SAFE")

        return overall, forecast

    def determine_recommended_action(
        self,
        risk_score: float,
        critical_sos: int,
        medical_sos: int,
        has_trapped: bool,
        blocked_roads: int,
        water_depth: float
    ) -> str:
        """
        Safety-critical explainable decision tree for operational recommendations.
        """
        if risk_score >= 80.0 and (critical_sos >= 1 or water_depth >= 1.4 or blocked_roads >= 1):
            return "EVACUATE IMMEDIATELY"
        elif critical_sos >= 1 and medical_sos >= 1:
            return "SEND MEDICAL ASSISTANCE"
        elif has_trapped or critical_sos >= 1 or risk_score >= 75.0:
            return "DISPATCH RESCUE TEAM"
        elif risk_score >= 55.0 or blocked_roads >= 1:
            return "PRE-POSITION RELIEF SUPPLIES"
        elif risk_score >= 30.0:
            return "MONITOR CLOSELY"
        else:
            return "NO IMMEDIATE ACTION"

    def generate_reasoning(
        self,
        risk_score: float,
        rainfall_intensity: float,
        cumulative_rainfall: float,
        river_level: float,
        danger_level: float,
        rate_of_rise: float,
        water_depth: float,
        active_sos: int,
        critical_sos: int,
        medical_sos: int,
        blocked_roads: int,
        alerts_detected: bool
    ) -> List[str]:
        """
        Generates clear, human-readable bullet points explaining the decision drivers.
        """
        reasons = []
        
        if river_level > danger_level:
            excess = round(river_level - danger_level, 2)
            reasons.append(f"River gauge at {river_level}m exceeds danger threshold ({danger_level}m) by +{excess}m")
        if rate_of_rise > 0.2:
            reasons.append(f"Rapid water surge velocity (+{rate_of_rise} m/hr) indicates ongoing inundation expansion")
        if rainfall_intensity >= 60.0:
            reasons.append(f"Intense radar rainfall rate ({rainfall_intensity} mm/hr) exceeding stormwater drainage limit")
        elif cumulative_rainfall >= 150.0:
            reasons.append(f"Catchment soil saturation reached ({cumulative_rainfall} mm 24h cumulative rainfall)")
        if water_depth >= 1.0:
            reasons.append(f"Ground inundation depth estimated at {water_depth}m inside populated sector")

        if critical_sos > 0:
            reasons.append(f"{critical_sos} critical life-safety SOS distress signals active in this sector")
        if medical_sos > 0:
            reasons.append(f"{medical_sos} urgent medical/insulin/trauma rescue cases identified")
        elif active_sos > 0:
            reasons.append(f"{active_sos} verified citizen distress signals logged in zone")

        if blocked_roads > 0:
            reasons.append(f"Drone surveillance confirmed {blocked_roads} key arterial access roads blocked by floodwaters")

        if alerts_detected:
            reasons.append("Official SACHET-NDMA / IMD severe warning alert active in immediate proximity")

        if not reasons:
            reasons.append("Environmental sensors within normal baseline parameters. Safe elevation and clear drainage.")

        return reasons

    def analyze_zone(
        self,
        zone: Zone,
        alerts: List[Alert],
        drone_readings: List[DroneReading],
        sos_reports: List[SOSReport],
        env_reading: Optional[EnvironmentalReading],
        all_zones: List[Zone] = None
    ) -> ZoneIntelligenceResponse:
        """
        Runs comprehensive analysis for a single zone with GIS partitioning across all zones.
        """
        if all_zones is None:
            all_zones = [zone]

        # 1. Environmental Hazard
        hazard_score, rain_comp, river_comp, rate_rise = self.calculate_environmental_hazard(env_reading)
        alert_comp = self.correlate_alerts(zone, alerts)
        
        # Combined Risk Score (0-100)
        # If no live sensor telemetry is available, fall back to initial zone baseline if present
        if env_reading is None and alert_comp == 0.0 and zone.risk_score > 0.0:
            risk_score = zone.risk_score
            hazard_score = zone.risk_score
        else:
            raw_risk = (hazard_score * 0.65) + (alert_comp * 0.35)
            risk_score = round(min(100.0, max(0.0, raw_risk)), 1)

        # Risk Level
        if risk_score >= 75.0:
            risk_level = "RED"
        elif risk_score >= 55.0:
            risk_level = "ORANGE"
        elif risk_score >= 30.0:
            risk_level = "YELLOW"
        else:
            risk_level = "GREEN"

        # 2. Drone Blockage & Isolation (Nearest-Zone GIS partitioned)
        blocked_roads, restricted_roads, isolation_comp = self.correlate_drone_blockages(zone, drone_readings, all_zones)

        # 3. Citizen SOS Distress (Nearest-Zone GIS partitioned)
        total_sos, crit_sos, med_sos, sos_comp, has_trapped = self.correlate_sos_distress(zone, sos_reports, all_zones)
        effective_sos = max(total_sos, zone.active_sos_count if zone.active_sos_count and not sos_reports else 0)

        # 4. Population Vulnerability Component
        pop_comp = round(min(100.0, (zone.population / 30000.0) * 100.0), 1)

        # 5. Data Freshness
        latest_ts = env_reading.timestamp if env_reading else None
        freshness = round(self.compute_data_freshness_factor(latest_ts), 2)

        # 6. Response Priority Score (0-100)
        priority_raw = (
            (risk_score * 0.35) +
            (sos_comp * 0.35) +
            (isolation_comp * 0.15) +
            (pop_comp * 0.15)
        ) * freshness
        priority_score = round(min(100.0, max(0.0, priority_raw)), 1)

        # 7. Trajectory Forecasting
        rain_val = env_reading.rainfall_intensity if env_reading else 0.0
        trajectory_str, trajectory_forecast = self.determine_trajectory(
            risk_score, rate_rise, rain_val, alert_comp
        )

        # 8. Operational Recommended Action
        water_depth_val = env_reading.water_depth if env_reading else 0.0
        action = self.determine_recommended_action(
            risk_score=risk_score,
            critical_sos=crit_sos,
            medical_sos=med_sos,
            has_trapped=has_trapped,
            blocked_roads=blocked_roads,
            water_depth=water_depth_val
        )

        # 9. Reasoning Breakdown
        reasons = self.generate_reasoning(
            risk_score=risk_score,
            rainfall_intensity=rain_val,
            cumulative_rainfall=env_reading.cumulative_rainfall if env_reading else 0.0,
            river_level=env_reading.river_level if env_reading else 0.0,
            danger_level=env_reading.danger_level if env_reading else 17.5,
            rate_of_rise=rate_rise,
            water_depth=water_depth_val,
            active_sos=effective_sos,
            critical_sos=crit_sos,
            medical_sos=med_sos,
            blocked_roads=blocked_roads,
            alerts_detected=(alert_comp >= 30.0)
        )

        score_breakdown = ScoreBreakdown(
            hazard_score=hazard_score,
            rainfall_component=rain_comp,
            river_component=river_comp,
            alert_component=alert_comp,
            sos_urgency_component=sos_comp,
            isolation_component=isolation_comp,
            population_component=pop_comp,
            data_freshness_factor=freshness
        )

        return ZoneIntelligenceResponse(
            zone_id=zone.id,
            zone_name=zone.name,
            latitude=zone.latitude,
            longitude=zone.longitude,
            risk_score=risk_score,
            risk_level=risk_level,
            trajectory=trajectory_forecast,
            overall_trajectory=trajectory_str,
            response_priority_score=priority_score,
            response_priority_rank=1,
            recommended_action=action,
            active_sos_count=effective_sos,
            affected_population=zone.population,

            impact_score=priority_score,
            response_priority=priority_score,
            priority_rank=1,
            active_sos=effective_sos,
            population=zone.population,
            score_breakdown=score_breakdown,
            reasoning=reasons
        )

    def analyze_all_zones(self, db: Session, sync_to_db: bool = True) -> List[ZoneIntelligenceResponse]:
        """
        Executes end-to-end risk and priority scoring across all zones in the database.
        Ranks all zones by response priority descending and optionally updates the Zone records.
        """
        zones = db.query(Zone).all()
        alerts = db.query(Alert).all()
        drone_readings = db.query(DroneReading).all()
        sos_reports = db.query(SOSReport).all()
        
        env_readings = db.query(EnvironmentalReading).order_by(EnvironmentalReading.timestamp.desc()).all()
        env_map: Dict[int, EnvironmentalReading] = {}
        for er in env_readings:
            if er.zone_id not in env_map:
                env_map[er.zone_id] = er

        results: List[ZoneIntelligenceResponse] = []
        for zone in zones:
            env_record = env_map.get(zone.id)
            zone_intel = self.analyze_zone(
                zone=zone,
                alerts=alerts,
                drone_readings=drone_readings,
                sos_reports=sos_reports,
                env_reading=env_record,
                all_zones=zones
            )
            results.append(zone_intel)

        # Sort zones by response priority score descending
        results.sort(key=lambda x: (x.response_priority_score, x.risk_score), reverse=True)

        # Assign global rank 1..N
        for rank, item in enumerate(results, start=1):
            item.response_priority_rank = rank
            item.priority_rank = rank

        # Sync scores to DB Zone records if requested
        if sync_to_db and results:
            for item in results:
                z_row = db.query(Zone).filter(Zone.id == item.zone_id).first()
                if z_row:
                    z_row.risk_score = item.risk_score
                    z_row.risk_level = item.risk_level
                    z_row.priority_rank = item.response_priority_rank
                    z_row.recommended_action = item.recommended_action
                    z_row.active_sos_count = item.active_sos_count
            db.commit()

        return results


risk_engine = AIRiskEngine()
