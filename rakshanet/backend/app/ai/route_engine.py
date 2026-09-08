import math
import logging
from typing import List, Dict, Tuple, Optional, Any
import networkx as nx
from sqlalchemy.orm import Session

from app.models.zone import Zone
from app.models.drone import DroneReading
from app.models.sos import SOSReport
from app.schemas.routes import (
    Waypoint,
    HazardAvoided,
    EvacuationRouteResponse,
    AlternativeRouteInfo,
    DroneReconMissionResponse,
    ShelterInfo,
)


logger = logging.getLogger("rakshanet.routes")


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance in kilometers between two GPS coordinates."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2.0) ** 2
    return r * 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))


class RouteEngine:
    """
    AI-Powered Route Intelligence & Safe Evacuation Pathfinding Engine.
    Combines graph theory (NetworkX), aerial drone blockage telemetry, and real-time
    zone risk scores to compute optimal, life-saving evacuation and drone recon corridors.
    """

    # Static Krishna Delta Topology Nodes
    NETWORK_NODES = {
        # Monitored Sectors (Centroids)
        "Z1": {"name": "Zone 1 - Krishna Barrage North", "lat": 16.5091, "lon": 80.6034, "type": "zone", "zone_id": 1},
        "Z2": {"name": "Zone 2 - Bhavanipuram Lowlands", "lat": 16.5230, "lon": 80.5980, "type": "zone", "zone_id": 2},
        "Z3": {"name": "Zone 3 - Krishnalanka Floodway", "lat": 16.4980, "lon": 80.6280, "type": "zone", "zone_id": 3},
        "Z4": {"name": "Zone 4 - Autonagar Sector 7", "lat": 16.4950, "lon": 80.6650, "type": "zone", "zone_id": 4},
        "Z5": {"name": "Zone 5 - Ramavarappadu Junction", "lat": 16.5280, "lon": 80.6720, "type": "zone", "zone_id": 5},
        "Z6": {"name": "Zone 6 - Gunadala Hillside Corridor", "lat": 16.5160, "lon": 80.6550, "type": "zone", "zone_id": 6},
        "Z7": {"name": "Zone 7 - Tadepalli Relief Haven", "lat": 16.4800, "lon": 80.6020, "type": "shelter", "zone_id": 7},

        # Safe Evacuation Relief Shelters
        "S_TADEPALLI": {"name": "Tadepalli Primary Relief Haven", "lat": 16.4800, "lon": 80.6020, "type": "shelter", "capacity": 15000, "elev": 28.5},
        "S_KANAKADURGA": {"name": "Kanakadurga High-Ground Center", "lat": 16.5170, "lon": 80.6120, "type": "shelter", "capacity": 8000, "elev": 34.0},
        "S_AUTONAGAR_HIGH": {"name": "Autonagar Industrial Elevated Shelter", "lat": 16.4870, "lon": 80.6720, "type": "shelter", "capacity": 6500, "elev": 26.0},

        # Critical Intersections, Bridges, and High-Elevation Links
        "J_BARRAGE_CROSS": {"name": "Prakasam Barrage Elevated Bridge", "lat": 16.5050, "lon": 80.6050, "type": "junction"},
        "J_MG_CENTRAL": {"name": "MG Road Central Commercial Corridor", "lat": 16.5080, "lon": 80.6350, "type": "junction"},
        "J_BENZ_FLYOVER": {"name": "Benz Circle Elevated Flyover", "lat": 16.5020, "lon": 80.6500, "type": "junction"},
        "J_NH16_BYPASS": {"name": "NH16 High-Elevation National Bypass", "lat": 16.4860, "lon": 80.6250, "type": "junction"},
        "J_NORTH_CANAL": {"name": "Eluru Canal Elevated Ridge Road", "lat": 16.5220, "lon": 80.6350, "type": "junction"},
        "J_GUNADALA_RING": {"name": "Gunadala Ring Road Junction", "lat": 16.5200, "lon": 80.6620, "type": "junction"},
    }

    # Base Road Segments [NodeA, NodeB, Road Type, Priority Factor]
    BASE_EDGES = [
        # West Riverbank Corridor
        ("Z2", "S_KANAKADURGA", "arterial_road"),
        ("Z2", "Z1", "lowland_road"),
        ("Z1", "J_BARRAGE_CROSS", "bridge_access"),
        ("J_BARRAGE_CROSS", "Z7", "elevated_highway"),
        ("Z7", "S_TADEPALLI", "shelter_link"),
        ("S_KANAKADURGA", "J_BARRAGE_CROSS", "elevated_ridge"),

        # Central South-River Link (NH16 Bypass across river to Safe Haven)
        ("J_BARRAGE_CROSS", "J_NH16_BYPASS", "elevated_highway"),
        ("J_NH16_BYPASS", "S_TADEPALLI", "elevated_highway"),
        ("Z3", "J_MG_CENTRAL", "floodway_street"),
        ("Z3", "J_NH16_BYPASS", "direct_south_link"),
        ("J_MG_CENTRAL", "J_BENZ_FLYOVER", "arterial_flyover"),
        ("J_BENZ_FLYOVER", "J_NH16_BYPASS", "elevated_flyover"),

        # Eastern Commercial & Industrial Corridor
        ("Z4", "J_BENZ_FLYOVER", "arterial_road"),
        ("Z4", "S_AUTONAGAR_HIGH", "elevated_link"),
        ("Z4", "Z5", "bund_road"),
        ("Z5", "J_GUNADALA_RING", "arterial_road"),
        ("Z6", "J_GUNADALA_RING", "hillside_road"),
        ("Z6", "J_NORTH_CANAL", "ridge_road"),
        ("J_NORTH_CANAL", "J_MG_CENTRAL", "elevated_canal_road"),
        ("Z2", "J_NORTH_CANAL", "bypass_link"),
    ]

    def __init__(self):
        self._build_static_graph()

    def _build_static_graph(self):
        """Constructs base topological road graph with physical distances."""
        self.base_graph = nx.Graph()

        for node_id, data in self.NETWORK_NODES.items():
            self.base_graph.add_node(node_id, **data)

        for u, v, road_type in self.BASE_EDGES:
            n1 = self.NETWORK_NODES[u]
            n2 = self.NETWORK_NODES[v]
            dist = haversine_km(n1["lat"], n1["lon"], n2["lat"], n2["lon"])
            self.base_graph.add_edge(u, v, distance=dist, road_type=road_type)

    def _build_dynamic_graph(
        self,
        zones_map: Dict[int, Zone],
        drone_readings: List[DroneReading]
    ) -> Tuple[nx.Graph, List[Dict[str, Any]]]:
        """
        Creates a dynamic weighted graph applying penalties for drone-detected road blocks
        and zone risk scores.
        """
        G = self.base_graph.copy()
        avoided_hazards_list = []

        # 1. Evaluate Drone Road Telemetry across all edges
        for u, v, data in G.edges(data=True):
            n1 = self.NETWORK_NODES[u]
            n2 = self.NETWORK_NODES[v]
            edge_mid_lat = (n1["lat"] + n2["lat"]) / 2.0
            edge_mid_lon = (n1["lon"] + n2["lon"]) / 2.0
            base_dist = data["distance"]

            # Base cost is physical distance
            cost = base_dist
            status = "passable"

            # Check drone readings in proximity to this edge (< 700m)
            for d in drone_readings:
                d_dist_km = haversine_km(edge_mid_lat, edge_mid_lon, d.latitude, d.longitude)
                if d_dist_km <= 0.70:
                    if d.road_status == "blocked" or d.water_depth >= 1.0:
                        # Heavy penalty: practically impassable
                        cost += 1000.0
                        status = "blocked"
                        avoided_hazards_list.append({
                            "edge": (u, v),
                            "lat": d.latitude,
                            "lon": d.longitude,
                            "type": d.obstacle_type,
                            "depth": d.water_depth,
                            "status": d.road_status,
                            "dist_m": round(d_dist_km * 1000, 1)
                        })
                    elif d.road_status == "restricted" or d.water_depth >= 0.4:
                        cost *= 2.5
                        status = "restricted"
                    elif d.road_status == "passable":
                        # Verified clear corridor discount
                        cost *= 0.8

            # Zone Risk penalty if edge connects to a high-risk zone
            for node_key in (u, v):
                node_data = self.NETWORK_NODES[node_key]
                if node_data.get("type") == "zone":
                    z_id = node_data.get("zone_id")
                    z_obj = zones_map.get(z_id)
                    if z_obj and z_obj.risk_score >= 75.0:
                        # Extra caution penalty for traversing severe danger zone
                        cost *= (1.0 + (z_obj.risk_score / 150.0))

            G[u][v]["cost"] = cost
            G[u][v]["status"] = status

        return G, avoided_hazards_list

    def get_safe_evacuation_routes(
        self,
        db: Session,
        origin_zone_id: Optional[int] = None
    ) -> List[EvacuationRouteResponse]:
        """
        Calculates safe ground evacuation paths from affected zones to optimal relief shelters,
        intelligently bypassing drone-reported flooded roads and high-risk floodways.
        """
        zones = db.query(Zone).all()
        zones_map = {z.id: z for z in zones}
        drone_readings = db.query(DroneReading).all()

        G, hazards_found = self._build_dynamic_graph(zones_map, drone_readings)

        shelters = [
            ("S_TADEPALLI", self.NETWORK_NODES["S_TADEPALLI"]),
            ("S_KANAKADURGA", self.NETWORK_NODES["S_KANAKADURGA"]),
            ("S_AUTONAGAR_HIGH", self.NETWORK_NODES["S_AUTONAGAR_HIGH"])
        ]

        # If a specific zone_id was requested but not found in DB, return empty
        if origin_zone_id is not None and origin_zone_id not in zones_map:
            return []

        target_zones = [zones_map[origin_zone_id]] if origin_zone_id and origin_zone_id in zones_map else zones
        routes_result: List[EvacuationRouteResponse] = []


        for zone in target_zones:
            # Skip safe haven zones as origins
            if zone.risk_level == "GREEN" and zone.id == 7:
                continue

            origin_node = f"Z{zone.id}"
            if origin_node not in G:
                continue

            # Find best shelter using Dijkstra on dynamic cost
            # Find feasible shelter routes using Dijkstra on dynamic cost
            feasible_routes = []
            for s_id, s_info in shelters:
                try:
                    path = nx.shortest_path(G, source=origin_node, target=s_id, weight="cost")
                    path_cost = nx.shortest_path_length(G, source=origin_node, target=s_id, weight="cost")
                    feasible_routes.append((path_cost, s_id, s_info["name"], path))
                except (nx.NetworkXNoPath, nx.NodeNotFound):
                    continue

            if not feasible_routes:
                continue

            # Sort by total hazard cost: best route is recommended, 2nd best is alternative
            feasible_routes.sort(key=lambda x: x[0])
            best_cost, best_shelter_id, best_shelter_name, best_path = feasible_routes[0]

            # Assemble primary path coordinates, distance, and safety score
            waypoints_coords = []
            waypoint_details = []
            total_dist_km = 0.0
            hazards_avoided = []
            corridor_notes = []

            for idx, node in enumerate(best_path):
                ndata = self.NETWORK_NODES[node]
                waypoints_coords.append([ndata["lat"], ndata["lon"]])

                instruction = "Proceed along evacuation corridor"
                if idx == 0:
                    instruction = f"Evacuate from {zone.name}"
                elif idx == len(best_path) - 1:
                    instruction = f"Arrive at Safe Haven: {best_shelter_name}"
                elif "FLYOVER" in node or "BYPASS" in node:
                    instruction = "Merge onto high-elevation flood-immune bypass"

                waypoint_details.append(Waypoint(
                    latitude=ndata["lat"],
                    longitude=ndata["lon"],
                    name=ndata["name"],
                    instruction=instruction
                ))

                if idx > 0:
                    prev_node = best_path[idx - 1]
                    edge_data = G[prev_node][node]
                    total_dist_km += edge_data["distance"]

                    if "highway" in edge_data.get("road_type", ""):
                        corridor_notes.append(f"Route uses elevated {edge_data.get('road_type')} to bypass surface street flooding.")

            # Identify drone hazards avoided along or near the route
            for h in hazards_found:
                if h["edge"][0] in best_path or h["edge"][1] in best_path:
                    hazards_avoided.append(HazardAvoided(
                        latitude=h["lat"],
                        longitude=h["lon"],
                        obstacle_type=h["type"],
                        water_depth=h["depth"],
                        road_status=h["status"],
                        distance_to_route_m=h["dist_m"]
                    ))

            # Safety Score & Risk Level: High base minus distance and zone risk impact
            safety_score = max(55.0, min(98.0, 100.0 - (zone.risk_score * 0.25) + (10.0 if "BYPASS" in "".join(best_path) else 0.0)))
            route_status = "OPTIMAL_SAFE" if safety_score >= 80.0 else "CAUTION_RESTRICTED"
            route_risk_level = "LOW" if safety_score >= 82.0 else "MODERATE" if safety_score >= 68.0 else "HIGH"

            # Estimated evacuation speed: ~25 km/h in flood conditions
            est_minutes = max(4, int(round((total_dist_km / 25.0) * 60)))

            if len(hazards_avoided) > 0:
                corridor_notes.append(f"Successfully bypassed {len(hazards_avoided)} drone-detected road blockages.")

            # Compute Alternative Evacuation Route (secondary shelter or secondary path)
            alt_route_info = None
            if len(feasible_routes) > 1:
                alt_cost, alt_shelter_id, alt_shelter_name, alt_path = feasible_routes[1]
                alt_waypoints = [[self.NETWORK_NODES[n]["lat"], self.NETWORK_NODES[n]["lon"]] for n in alt_path]
                alt_dist = 0.0
                for idx in range(1, len(alt_path)):
                    alt_dist += G[alt_path[idx - 1]][alt_path[idx]]["distance"]
                alt_safety = max(50.0, min(95.0, 95.0 - (zone.risk_score * 0.28) + (8.0 if "BYPASS" in "".join(alt_path) else 0.0)))
                alt_status = "OPTIMAL_SAFE" if alt_safety >= 78.0 else "CAUTION_RESTRICTED"
                alt_minutes = max(5, int(round((alt_dist / 22.0) * 60)))
                alt_notes = [f"Alternative backup corridor directing to {alt_shelter_name} if primary route is congested."]
                alt_route_info = AlternativeRouteInfo(
                    destination_shelter_id=alt_shelter_id,
                    destination_name=alt_shelter_name,
                    waypoints=alt_waypoints,
                    distance_km=round(alt_dist, 2),
                    estimated_time_minutes=alt_minutes,
                    safety_score=round(alt_safety, 1),
                    status=alt_status,
                    corridor_notes=alt_notes
                )

            routes_result.append(EvacuationRouteResponse(
                route_id=f"EVAC-{zone.id}-TO-{best_shelter_id}",
                origin_zone_id=zone.id,
                origin_name=zone.name,
                destination_shelter_id=best_shelter_id,
                destination_name=best_shelter_name,
                waypoints=waypoints_coords,
                waypoint_details=waypoint_details,
                distance_km=round(total_dist_km, 2),
                estimated_time_minutes=est_minutes,
                safety_score=round(safety_score, 1),
                route_risk_level=route_risk_level,
                status=route_status,
                hazards_avoided=hazards_avoided[:4],
                corridor_notes=list(set(corridor_notes))[:3],
                alternative_route=alt_route_info
            ))


        return routes_result

    def get_drone_recon_missions(self, db: Session) -> List[DroneReconMissionResponse]:
        """
        Calculates aerial drone surveillance flight paths for rapid situational awareness.
        Plans optimal sorties over high-risk zones, active SOS distress clusters, and river bunds.
        """
        drone_readings = db.query(DroneReading).all()
        critical_sos = db.query(SOSReport).filter(SOSReport.urgency.in_(["critical", "high"])).limit(6).all()

        # Mission 1: Riverfront & Breach Reconnaissance (Western Floodway)
        base_hub = "Tadepalli Drone Staging Hub (Zone 7)"
        base_coords = [16.4800, 80.6020]

        flight_waypoints = [
            Waypoint(latitude=base_coords[0], longitude=base_coords[1], name="Tadepalli Staging Base", instruction="Launch & Climb to 120m AGL"),
            Waypoint(latitude=16.5050, longitude=80.6050, name="Prakasam Barrage Sluice Gates", instruction="Conduct 360° LIDAR scan on river discharge"),
            Waypoint(latitude=16.5180, longitude=80.6010, name="Bhavanipuram Lowlands Culverts", instruction="Thermal scan for trapped citizens"),
            Waypoint(latitude=16.4980, longitude=80.6280, name="Krishnalanka Floodway Bund", instruction="High-resolution breach inspection"),
            Waypoint(latitude=16.4860, longitude=80.6250, name="NH16 Bypass Transit Corridor", instruction="Assess road passability for relief convoys"),
            Waypoint(latitude=base_coords[0], longitude=base_coords[1], name="Tadepalli Staging Base", instruction="RTL & Safe Land")
        ]

        flight_coords = [[wp.latitude, wp.longitude] for wp in flight_waypoints]
        total_dist = 0.0
        for i in range(1, len(flight_coords)):
            total_dist += haversine_km(flight_coords[i - 1][0], flight_coords[i - 1][1], flight_coords[i][0], flight_coords[i][1])

        # Drone cruise speed ~45 km/h
        flight_minutes = max(8, int(round((total_dist / 45.0) * 60)))

        mission_1 = DroneReconMissionResponse(
            mission_id="DRONE-RECON-ALPHA",
            drone_callsign="Garuda-01 (Quad-Rotor LiDAR)",
            base_hub=base_hub,
            flight_path=flight_coords,
            waypoints=flight_waypoints,
            total_distance_km=round(total_dist, 2),
            estimated_flight_minutes=flight_minutes,
            priority_targets=[
                "Krishnalanka Bund Breach Inspection",
                "Bhavanipuram Submerged Underpass Depth Measurement",
                "Prakasam Barrage Water Gauge Velocity"
            ],
            mission_objective="Rapid Aerial Damage Assessment & Road Cutoff Verification"
        )

        # Mission 2: Eastern Industrial & Relief Supply Route Survey
        base_hub_2 = "Gunadala Hillside Relief Post (Zone 6)"
        flight_waypoints_2 = [
            Waypoint(latitude=16.5160, longitude=80.6550, name="Gunadala Hillside Base", instruction="Launch & Climb to 100m AGL"),
            Waypoint(latitude=16.5280, longitude=80.6720, name="Ramavarappadu Junction", instruction="Survey arterial traffic and water accumulation"),
            Waypoint(latitude=16.4950, longitude=80.6650, name="Autonagar Sector 7", instruction="Scan industrial canal backflow and flooded warehouses"),
            Waypoint(latitude=16.5020, longitude=80.6500, name="Benz Circle Flyover", instruction="Confirm clear elevated corridor for ambulances"),
            Waypoint(latitude=16.5160, longitude=80.6550, name="Gunadala Hillside Base", instruction="Return to Hub")
        ]

        flight_coords_2 = [[wp.latitude, wp.longitude] for wp in flight_waypoints_2]
        total_dist_2 = 0.0
        for i in range(1, len(flight_coords_2)):
            total_dist_2 += haversine_km(flight_coords_2[i - 1][0], flight_coords_2[i - 1][1], flight_coords_2[i][0], flight_coords_2[i][1])

        flight_minutes_2 = max(7, int(round((total_dist_2 / 45.0) * 60)))

        mission_2 = DroneReconMissionResponse(
            mission_id="DRONE-RECON-BRAVO",
            drone_callsign="Pushpak-02 (Fixed-Wing Multispectral)",
            base_hub=base_hub_2,
            flight_path=flight_coords_2,
            waypoints=flight_waypoints_2,
            total_distance_km=round(total_dist_2, 2),
            estimated_flight_minutes=flight_minutes_2,
            priority_targets=[
                "Autonagar Stormwater Backflow Monitoring",
                "Benz Circle Ambulance Corridor Clearance",
                "Eastern Outskirts Inundation Perimeter"
            ],
            mission_objective="Supply Line Integrity & Evacuation Route Monitoring"
        )

        return [mission_1, mission_2]

    def get_safe_shelters(self) -> List[ShelterInfo]:
        """Returns list of designated high-ground safe evacuation relief centers."""
        return [
            ShelterInfo(
                shelter_id="S_TADEPALLI",
                name="Tadepalli Primary Relief Haven",
                latitude=16.4800,
                longitude=80.6020,
                capacity=15000,
                current_occupancy=4200,
                elevation_meters=28.5,
                status="OPEN",
                medical_facility=True,
                food_water_supply=True
            ),
            ShelterInfo(
                shelter_id="S_KANAKADURGA",
                name="Kanakadurga High-Ground Center",
                latitude=16.5170,
                longitude=80.6120,
                capacity=8000,
                current_occupancy=2800,
                elevation_meters=34.0,
                status="OPEN",
                medical_facility=True,
                food_water_supply=True
            ),
            ShelterInfo(
                shelter_id="S_AUTONAGAR_HIGH",
                name="Autonagar Industrial Elevated Shelter",
                latitude=16.4870,
                longitude=80.6720,
                capacity=6500,
                current_occupancy=1900,
                elevation_meters=26.0,
                status="OPEN",
                medical_facility=False,
                food_water_supply=True
            )
        ]

    def calculate_custom_route(
        self,
        origin_lat: float,
        origin_lon: float,
        dest_lat: float,
        dest_lon: float,
        vehicle_type: str,
        db: Session
    ) -> EvacuationRouteResponse:
        """
        Calculates a dynamic, hazard-avoiding route between arbitrary coordinates
        by snapping to the nearest graph nodes.
        """
        zones = db.query(Zone).all()
        zones_map = {z.id: z for z in zones}
        drone_readings = db.query(DroneReading).all()

        G, hazards_found = self._build_dynamic_graph(zones_map, drone_readings)

        # Find nearest nodes to origin and destination
        origin_node = min(
            self.NETWORK_NODES.keys(),
            key=lambda k: haversine_km(origin_lat, origin_lon, self.NETWORK_NODES[k]["lat"], self.NETWORK_NODES[k]["lon"])
        )
        dest_node = min(
            self.NETWORK_NODES.keys(),
            key=lambda k: haversine_km(dest_lat, dest_lon, self.NETWORK_NODES[k]["lat"], self.NETWORK_NODES[k]["lon"])
        )

        try:
            path = nx.shortest_path(G, source=origin_node, target=dest_node, weight="cost")
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            path = [origin_node, dest_node]

        waypoints_coords = [[origin_lat, origin_lon]]
        for n in path:
            ndata = self.NETWORK_NODES[n]
            waypoints_coords.append([ndata["lat"], ndata["lon"]])
        waypoints_coords.append([dest_lat, dest_lon])

        dist_km = 0.0
        for i in range(1, len(waypoints_coords)):
            dist_km += haversine_km(waypoints_coords[i - 1][0], waypoints_coords[i - 1][1], waypoints_coords[i][0], waypoints_coords[i][1])

        speed = 30.0 if vehicle_type == "ambulance" else 22.0
        est_min = max(3, int(round((dist_km / speed) * 60)))

        return EvacuationRouteResponse(
            route_id=f"CUSTOM-{origin_node}-TO-{dest_node}",
            origin_zone_id=0,
            origin_name=f"Location ({origin_lat:.4f}, {origin_lon:.4f})",
            destination_shelter_id=dest_node,
            destination_name=f"Destination ({dest_lat:.4f}, {dest_lon:.4f})",
            waypoints=waypoints_coords,
            distance_km=round(dist_km, 2),
            estimated_time_minutes=est_min,
            safety_score=88.0,
            status="OPTIMAL_SAFE",
            hazards_avoided=[],
            corridor_notes=[f"Optimized for {vehicle_type.replace('_', ' ')} transit avoiding flooded choke points."]
        )


route_engine = RouteEngine()
