import io
import csv
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.zone import Zone
from app.models.sos import SOSReport
from app.models.drone import DroneReading
from app.models.team import Team

router = APIRouter(prefix="/reports", tags=["Situation Reports"])


@router.get("/export")
def export_situation_report(format: str = "csv", db: Session = Depends(get_db)):
    """
    Exports a comprehensive Disaster Situation Report (SITREP) in CSV or JSON format.
    Summarizes affected zones, priorities, SOS counts, drone road status, and deployed teams.
    """
    zones = db.query(Zone).order_by(Zone.priority_rank.asc()).all()
    sos_reports = db.query(SOSReport).all()
    drone_readings = db.query(DroneReading).all()
    teams = db.query(Team).all()

    unresolved_sos = [s for s in sos_reports if s.status != "COMPLETED"]
    blocked_roads = [d for d in drone_readings if d.road_status == "blocked"]

    now_utc = datetime.now(timezone.utc)

    if format.lower() == "json":
        return {
            "title": "RakshaNet Incident Command - Situation Report (SITREP)",
            "timestamp": now_utc.isoformat(),
            "summary": {
                "total_zones": len(zones),
                "red_zones": len([z for z in zones if z.risk_level == "RED"]),
                "unresolved_sos": len(unresolved_sos),
                "blocked_roads": len(blocked_roads),
                "active_teams": len([t for t in teams if t.status in ["ASSIGNED", "EN_ROUTE", "ON_SITE"]])
            },
            "zones": [
                {
                    "name": z.name,
                    "risk_score": z.risk_score,
                    "risk_level": z.risk_level,
                    "priority_rank": z.priority_rank,
                    "recommended_action": z.recommended_action,
                    "active_sos": z.active_sos_count
                } for z in zones
            ],
            "unresolved_sos": [
                {
                    "id": s.id,
                    "need_type": s.need_type,
                    "urgency": s.urgency,
                    "priority_score": s.priority_score,
                    "status": s.status,
                    "message": s.message
                } for s in unresolved_sos
            ]
        }

    # Default: CSV format
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["RAKSHANET DISASTER SITUATION REPORT", now_utc.isoformat()])
    writer.writerow([])
    writer.writerow(["--- ZONE INTELLIGENCE SUMMARY ---"])
    writer.writerow(["Zone ID", "Zone Name", "Risk Score", "Risk Level", "Priority Rank", "Action", "Active SOS", "Population"])
    for z in zones:
        writer.writerow([z.id, z.name, z.risk_score, z.risk_level, z.priority_rank, z.recommended_action, z.active_sos_count, z.population])

    writer.writerow([])
    writer.writerow(["--- ACTIVE SOS DISTRESS LOG ---"])
    writer.writerow(["SOS ID", "Need Type", "Urgency", "Priority Score", "Status", "Message", "Language"])
    for s in unresolved_sos:
        writer.writerow([s.id, s.need_type, s.urgency, s.priority_score, s.status, s.message, s.language])

    writer.writerow([])
    writer.writerow(["--- DRONE ROAD OBSTACLES ---"])
    writer.writerow(["Drone ID", "Latitude", "Longitude", "Obstacle Type", "Water Depth (m)", "Status", "Confidence"])
    for d in drone_readings:
        writer.writerow([d.id, d.latitude, d.longitude, d.obstacle_type, d.water_depth, d.road_status, d.confidence])

    writer.writerow([])
    writer.writerow(["--- RESCUE TEAM OPERATIONS ---"])
    writer.writerow(["Team ID", "Name", "Task", "Status", "Members"])
    for t in teams:
        writer.writerow([t.id, t.name, t.task, t.status, t.member_count])

    output.seek(0)
    filename = f"RakshaNet_SitRep_{now_utc.strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
