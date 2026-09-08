import uuid
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
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
from app.schemas.relief import (
    ReliefCampCreate, ReliefCampUpdate, ReliefCampResponse,
    ReliefRequestCreate, ReliefRequestUpdate, ReliefRequestResponse,
    ResourceInventoryCreate, ResourceInventoryUpdate, ResourceInventoryResponse,
    ReliefTeamCreate, ReliefTeamUpdate, ReliefTeamResponse,
    RecoveryItemCreate, RecoveryItemUpdate, RecoveryItemResponse,
    ReliefSummaryResponse,
    DamageAssessmentCreate, DamageAssessmentUpdate, DamageAssessmentResponse,
    ReliefFundResponse, ReliefDonationCreate, ReliefDonationResponse,
)
from app.ai.relief_engine import relief_engine
from app.websocket import ws_manager


router = APIRouter(prefix="/relief", tags=["Post-Disaster Relief & Recovery (Phase 8)"])


# -----------------------------------------------------------------------
# 1. SUMMARY DASHBOARD KPI
# -----------------------------------------------------------------------

@router.get("/summary", response_model=ReliefSummaryResponse, summary="Get post-disaster relief & recovery KPI summary")
def get_relief_summary(db: Session = Depends(get_db)):
    """Returns aggregated metrics on affected population, camp capacity, resources, teams, requests, and recovery progress."""
    try:
        return relief_engine.get_relief_summary(db)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error computing relief summary: {e}")


# -----------------------------------------------------------------------
# 2. RELIEF CAMPS
# -----------------------------------------------------------------------

@router.get("/camps", response_model=List[ReliefCampResponse], summary="Get all designated relief camps")
def get_relief_camps(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: Available, Near Capacity, Full"),
    db: Session = Depends(get_db),
):
    query = db.query(ReliefCamp)
    if status_filter:
        query = query.filter(ReliefCamp.status == status_filter)
    return query.order_by(ReliefCamp.capacity.desc()).all()


@router.post("/camps", response_model=ReliefCampResponse, status_code=status.HTTP_201_CREATED, summary="Register a new relief camp")
def create_relief_camp(camp_in: ReliefCampCreate, db: Session = Depends(get_db)):
    camp = ReliefCamp(**camp_in.model_dump())
    db.add(camp)
    db.commit()
    db.refresh(camp)

    ws_manager.broadcast_sync({
        "event": "RELIEF_CAMP_UPDATED",
        "action": "create",
        "data": ReliefCampResponse.model_validate(camp).model_dump(mode="json"),
        "message": f"New relief camp opened: {camp.name}"
    })
    return camp


@router.put("/camps/{camp_id}", response_model=ReliefCampResponse, summary="Update camp occupancy, resources, or status")
def update_relief_camp(camp_id: int, camp_in: ReliefCampUpdate, db: Session = Depends(get_db)):
    camp = db.query(ReliefCamp).filter(ReliefCamp.id == camp_id).first()
    if not camp:
        raise HTTPException(status_code=404, detail="Relief camp not found")

    update_data = camp_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(camp, field, value)

    # Auto-adjust status based on occupancy if not manually overridden
    if "current_occupancy" in update_data and "status" not in update_data:
        occ_ratio = camp.current_occupancy / float(camp.capacity) if camp.capacity > 0 else 1.0
        if occ_ratio >= 0.95:
            camp.status = "Full"
        elif occ_ratio >= 0.75:
            camp.status = "Near Capacity"
        else:
            camp.status = "Available"
        camp.available_beds = max(0, camp.capacity - camp.current_occupancy)

    camp.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(camp)

    ws_manager.broadcast_sync({
        "event": "RELIEF_CAMP_UPDATED",
        "action": "update",
        "data": ReliefCampResponse.model_validate(camp).model_dump(mode="json"),
        "message": f"Camp {camp.name} updated: occupancy {camp.current_occupancy}/{camp.capacity}"
    })
    return camp


# -----------------------------------------------------------------------
# 3. RELIEF REQUESTS
# -----------------------------------------------------------------------

@router.get("/requests", response_model=List[ReliefRequestResponse], summary="List citizen / field team relief requests")
def get_relief_requests(
    category: Optional[str] = None,
    priority: Optional[str] = None,
    req_status: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    query = db.query(ReliefRequest)
    if category:
        query = query.filter(ReliefRequest.category.ilike(f"%{category}%"))
    if priority:
        query = query.filter(ReliefRequest.priority.ilike(priority))
    if req_status:
        query = query.filter(ReliefRequest.status.ilike(req_status))
    return query.order_by(ReliefRequest.priority_score.desc(), ReliefRequest.created_at.desc()).all()


@router.post("/requests", response_model=ReliefRequestResponse, status_code=status.HTTP_201_CREATED, summary="Submit a new relief request")
def submit_relief_request(req_in: ReliefRequestCreate, db: Session = Depends(get_db)):
    req_data = req_in.model_dump()
    if not req_data.get("request_code"):
        # Auto-generate human-readable request code
        count = db.query(ReliefRequest).count() + 101
        req_data["request_code"] = f"REQ-KD-{count}"

    # Calculate transparent priority score
    prio_score = relief_engine.calculate_request_priority(
        category=req_data["category"],
        raw_priority=req_data.get("priority", "High"),
        people_count=req_data.get("people_count", 1),
        latitude=req_data["latitude"],
        longitude=req_data["longitude"],
        db=db,
    )
    req_data["priority_score"] = prio_score
    req_data["status"] = "Pending"

    req_obj = ReliefRequest(**req_data)
    db.add(req_obj)
    db.commit()
    db.refresh(req_obj)

    ws_manager.broadcast_sync({
        "event": "NEW_RELIEF_REQUEST",
        "data": ReliefRequestResponse.model_validate(req_obj).model_dump(mode="json"),
        "message": f"New [{req_obj.priority.upper()}] relief request for {req_obj.category} at {req_obj.location_name}"
    })
    return req_obj


@router.put("/requests/{request_id}", response_model=ReliefRequestResponse, summary="Update request status or assign relief team")
def update_relief_request(request_id: int, req_in: ReliefRequestUpdate, db: Session = Depends(get_db)):
    req_obj = db.query(ReliefRequest).filter(ReliefRequest.id == request_id).first()
    if not req_obj:
        raise HTTPException(status_code=404, detail="Relief request not found")

    update_data = req_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(req_obj, field, value)

    req_obj.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(req_obj)

    ws_manager.broadcast_sync({
        "event": "RELIEF_REQUEST_UPDATED",
        "data": ReliefRequestResponse.model_validate(req_obj).model_dump(mode="json"),
        "message": f"Request {req_obj.request_code} status updated to {req_obj.status}"
    })
    return req_obj


@router.post("/requests/{request_id}/accept", response_model=ReliefRequestResponse, summary="Accept a help request for a community or official team")
def accept_relief_request(
    request_id: int,
    team_id: Optional[int] = None,
    team_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    req_obj = db.query(ReliefRequest).filter(ReliefRequest.id == request_id).first()
    if not req_obj:
        raise HTTPException(status_code=404, detail="Relief request not found")

    assigned_name = team_name or "Community Volunteer Team"
    if team_id:
        team_obj = db.query(ReliefTeam).filter(ReliefTeam.id == team_id).first()
        if team_obj:
            assigned_name = team_obj.name
            team_obj.status = "On Mission"
            team_obj.assigned_task = f"Assisting request {req_obj.request_code} at {req_obj.location_name}"
            team_obj.updated_at = datetime.now(timezone.utc)
            ws_manager.broadcast_sync({
                "event": "RELIEF_TEAM_UPDATED",
                "data": ReliefTeamResponse.model_validate(team_obj).model_dump(mode="json"),
                "message": f"Team {team_obj.name} accepted mission for request {req_obj.request_code}"
            })

    req_obj.status = "Assigned"
    req_obj.assigned_team_id = team_id
    req_obj.assigned_team_name = assigned_name
    req_obj.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(req_obj)

    ws_manager.broadcast_sync({
        "event": "RELIEF_REQUEST_UPDATED",
        "data": ReliefRequestResponse.model_validate(req_obj).model_dump(mode="json"),
        "message": f"Help Request {req_obj.request_code} ACCEPTED by {assigned_name}"
    })
    return req_obj


@router.post("/requests/{request_id}/complete", response_model=ReliefRequestResponse, summary="Mark help request as completed/resolved")
def complete_relief_request(request_id: int, db: Session = Depends(get_db)):
    req_obj = db.query(ReliefRequest).filter(ReliefRequest.id == request_id).first()
    if not req_obj:
        raise HTTPException(status_code=404, detail="Relief request not found")

    req_obj.status = "Completed"
    req_obj.updated_at = datetime.now(timezone.utc)

    # Free assigned team if any
    if req_obj.assigned_team_id:
        team_obj = db.query(ReliefTeam).filter(ReliefTeam.id == req_obj.assigned_team_id).first()
        if team_obj:
            team_obj.status = "Available"
            team_obj.assigned_task = "Standby at Operations Base"
            team_obj.updated_at = datetime.now(timezone.utc)
            ws_manager.broadcast_sync({
                "event": "RELIEF_TEAM_UPDATED",
                "data": ReliefTeamResponse.model_validate(team_obj).model_dump(mode="json"),
                "message": f"Team {team_obj.name} is now Available"
            })

    db.commit()
    db.refresh(req_obj)

    ws_manager.broadcast_sync({
        "event": "RELIEF_REQUEST_UPDATED",
        "data": ReliefRequestResponse.model_validate(req_obj).model_dump(mode="json"),
        "message": f"Help Request {req_obj.request_code} marked COMPLETED (Help Delivered)"
    })
    return req_obj


@router.post("/requests/{request_id}/escalate", response_model=ReliefRequestResponse, summary="Escalate help request to official NDRF/SDRF rescue force")
def escalate_relief_request(request_id: int, db: Session = Depends(get_db)):
    req_obj = db.query(ReliefRequest).filter(ReliefRequest.id == request_id).first()
    if not req_obj:
        raise HTTPException(status_code=404, detail="Relief request not found")

    req_obj.priority = "Critical"
    req_obj.priority_score = 98.0
    req_obj.notes = f"{req_obj.notes or ''} [ESCALATED TO OFFICIAL NDRF/SDRF RESCUE TASKFORCE]"
    
    # Try to assign NDRF team if available
    ndrf_team = db.query(ReliefTeam).filter(ReliefTeam.name.ilike("%NDRF%")).first()
    if ndrf_team:
        req_obj.assigned_team_id = ndrf_team.id
        req_obj.assigned_team_name = ndrf_team.name
        req_obj.status = "Assigned"
        ndrf_team.status = "On Mission"
        ndrf_team.assigned_task = f"HIGH-PRIORITY ESCALATION: Rescue at {req_obj.location_name}"

    req_obj.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(req_obj)

    ws_manager.broadcast_sync({
        "event": "SOS_ESCALATED",
        "data": ReliefRequestResponse.model_validate(req_obj).model_dump(mode="json"),
        "message": f"🚨 EMERGENCY ESCALATION: Request {req_obj.request_code} escalated to NDRF Aquatic Taskforce!"
    })
    return req_obj


# -----------------------------------------------------------------------
# 4. RESOURCE INVENTORY
# -----------------------------------------------------------------------

@router.get("/resources", response_model=List[ResourceInventoryResponse], summary="Get inventory of emergency relief supplies")
def get_resource_inventory(db: Session = Depends(get_db)):
    resources = db.query(ResourceInventory).all()
    results = []
    for r in resources:
        res_dict = {
            "id": r.id,
            "item_name": r.item_name,
            "category": r.category,
            "unit": r.unit,
            "available_qty": r.available_qty,
            "required_qty": r.required_qty,
            "distributed_qty": r.distributed_qty,
            "low_stock_threshold": r.low_stock_threshold,
            "remaining_qty": max(0, r.available_qty - r.distributed_qty),
            "low_stock_warning": (r.available_qty <= r.low_stock_threshold),
            "updated_at": r.updated_at,
        }
        results.append(ResourceInventoryResponse(**res_dict))
    return results


@router.put("/resources/{resource_id}", response_model=ResourceInventoryResponse, summary="Update resource stock levels")
def update_resource_inventory(resource_id: int, res_in: ResourceInventoryUpdate, db: Session = Depends(get_db)):
    res_obj = db.query(ResourceInventory).filter(ResourceInventory.id == resource_id).first()
    if not res_obj:
        raise HTTPException(status_code=404, detail="Resource item not found")

    update_data = res_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(res_obj, field, value)

    res_obj.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(res_obj)

    res_dict = {
        "id": res_obj.id,
        "item_name": res_obj.item_name,
        "category": res_obj.category,
        "unit": res_obj.unit,
        "available_qty": res_obj.available_qty,
        "required_qty": res_obj.required_qty,
        "distributed_qty": res_obj.distributed_qty,
        "low_stock_threshold": res_obj.low_stock_threshold,
        "remaining_qty": max(0, res_obj.available_qty - res_obj.distributed_qty),
        "low_stock_warning": (res_obj.available_qty <= res_obj.low_stock_threshold),
        "updated_at": res_obj.updated_at,
    }
    response_model = ResourceInventoryResponse(**res_dict)

    ws_manager.broadcast_sync({
        "event": "RESOURCE_UPDATED",
        "data": response_model.model_dump(mode="json"),
        "message": f"Resource {res_obj.item_name} inventory updated ({res_obj.available_qty} {res_obj.unit})"
    })
    return response_model


# -----------------------------------------------------------------------
# 5. RELIEF TEAMS
# -----------------------------------------------------------------------

@router.get("/teams", response_model=List[ReliefTeamResponse], summary="List deployed relief and rescue teams")
def get_relief_teams(
    status_filter: Optional[str] = Query(None, alias="status"),
    team_type: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(ReliefTeam)
    if status_filter:
        query = query.filter(ReliefTeam.status.ilike(status_filter))
    if team_type:
        query = query.filter(ReliefTeam.team_type.ilike(f"%{team_type}%"))
    return query.order_by(ReliefTeam.id.asc()).all()


@router.put("/teams/{team_id}", response_model=ReliefTeamResponse, summary="Update team status, location, or assigned task")
def update_relief_team(team_id: int, team_in: ReliefTeamUpdate, db: Session = Depends(get_db)):
    team_obj = db.query(ReliefTeam).filter(ReliefTeam.id == team_id).first()
    if not team_obj:
        raise HTTPException(status_code=404, detail="Relief team not found")

    update_data = team_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team_obj, field, value)

    team_obj.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(team_obj)

    ws_manager.broadcast_sync({
        "event": "RELIEF_TEAM_UPDATED",
        "data": ReliefTeamResponse.model_validate(team_obj).model_dump(mode="json"),
        "message": f"Team {team_obj.name} status updated: {team_obj.status}"
    })
    return team_obj


# -----------------------------------------------------------------------
# 6. RECOVERY TRACKING
# -----------------------------------------------------------------------

@router.get("/recovery", response_model=List[RecoveryItemResponse], summary="Track infrastructure recovery across roads, power, water, hospitals")
def get_recovery_items(
    category: Optional[str] = None,
    rec_status: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    query = db.query(RecoveryItem)
    if category:
        query = query.filter(RecoveryItem.category.ilike(f"%{category}%"))
    if rec_status:
        query = query.filter(RecoveryItem.recovery_status.ilike(f"%{rec_status}%"))
    return query.order_by(RecoveryItem.progress_pct.asc()).all()


@router.put("/recovery/{item_id}", response_model=RecoveryItemResponse, summary="Update recovery restoration progress and status")
def update_recovery_item(item_id: int, item_in: RecoveryItemUpdate, db: Session = Depends(get_db)):
    item_obj = db.query(RecoveryItem).filter(RecoveryItem.id == item_id).first()
    if not item_obj:
        raise HTTPException(status_code=404, detail="Recovery item not found")

    update_data = item_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(item_obj, field, value)

    # Automatically set Restored status when 100%
    if item_obj.progress_pct >= 100:
        item_obj.recovery_status = "Restored"

    item_obj.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(item_obj)

    ws_manager.broadcast_sync({
        "event": "RECOVERY_UPDATED",
        "data": RecoveryItemResponse.model_validate(item_obj).model_dump(mode="json"),
        "message": f"Recovery updated: {item_obj.name} at {item_obj.progress_pct}% ({item_obj.recovery_status})"
    })
    return item_obj


# -----------------------------------------------------------------------
# 7. POST-DISASTER DAMAGE & NEEDS ASSESSMENT (PHASE 8 CORE)
# -----------------------------------------------------------------------

@router.get("/damage-assessments", response_model=List[DamageAssessmentResponse], summary="List damage and needs assessments for all zones")
def get_damage_assessments(
    severity: Optional[str] = Query(None, description="Filter by damage severity: LOW, MEDIUM, HIGH, CRITICAL"),
    assessment_status: Optional[str] = Query(None, description="Filter by status: PENDING, ASSESSED, VERIFIED"),
    priority_level: Optional[str] = Query(None, description="Filter by priority: CRITICAL, HIGH, MEDIUM, LOW"),
    db: Session = Depends(get_db),
):
    query = db.query(ZoneDamageAssessment)
    if severity:
        query = query.filter(ZoneDamageAssessment.damage_severity.ilike(severity))
    if assessment_status:
        query = query.filter(ZoneDamageAssessment.assessment_status.ilike(assessment_status))
    if priority_level:
        query = query.filter(ZoneDamageAssessment.priority_level.ilike(priority_level))
    return query.order_by(ZoneDamageAssessment.priority_score.desc(), ZoneDamageAssessment.zone_id.asc()).all()


@router.get("/damage-assessments/{zone_id}", response_model=DamageAssessmentResponse, summary="Get damage and needs assessment for a specific zone")
def get_zone_damage_assessment(zone_id: int, db: Session = Depends(get_db)):
    assessment = db.query(ZoneDamageAssessment).filter(ZoneDamageAssessment.zone_id == zone_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail=f"Damage assessment for Zone {zone_id} not found")
    return assessment


@router.put("/damage-assessments/{zone_id}", response_model=DamageAssessmentResponse, summary="Update zone damage severity, impact, or relief requirements")
def update_zone_damage_assessment(zone_id: int, assessment_in: DamageAssessmentUpdate, db: Session = Depends(get_db)):
    assessment = db.query(ZoneDamageAssessment).filter(ZoneDamageAssessment.zone_id == zone_id).first()
    if not assessment:
        raise HTTPException(status_code=404, detail=f"Damage assessment for Zone {zone_id} not found")

    update_data = assessment_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(assessment, field, value)

    # Reclassify priority score and priority level based on damage severity, affected people, and injuries
    sev_weights = {"CRITICAL": 40.0, "HIGH": 28.0, "MEDIUM": 16.0, "LOW": 8.0}
    sev_score = sev_weights.get(assessment.damage_severity.upper(), 25.0)
    people_factor = min(35.0, (assessment.affected_people / 1000.0) * 1.5)
    injury_factor = min(25.0, (assessment.injured_count * 0.4) + (assessment.missing_count * 1.5))
    
    calc_score = round(min(99.0, max(15.0, sev_score + people_factor + injury_factor)), 1)
    if "priority_score" not in update_data:
        assessment.priority_score = calc_score
    
    if "priority_level" not in update_data:
        if assessment.priority_score >= 80.0:
            assessment.priority_level = "CRITICAL"
        elif assessment.priority_score >= 65.0:
            assessment.priority_level = "HIGH"
        elif assessment.priority_score >= 45.0:
            assessment.priority_level = "MEDIUM"
        else:
            assessment.priority_level = "LOW"

    assessment.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(assessment)

    ws_manager.broadcast_sync({
        "event": "DAMAGE_ASSESSMENT_UPDATED",
        "data": DamageAssessmentResponse.model_validate(assessment).model_dump(mode="json"),
        "message": f"Damage assessment for {assessment.zone_name} updated: Severity {assessment.damage_severity}, Priority {assessment.priority_level}"
    })
    return assessment


# -----------------------------------------------------------------------
# 8. RELIEF FUNDRAISING & DONATIONS (PHASE 8 CORE)
# -----------------------------------------------------------------------

@router.get("/funds", response_model=ReliefFundResponse, summary="Get post-disaster relief fundraising campaign status and allocations")
def get_relief_fund(db: Session = Depends(get_db)):
    fund = db.query(ReliefFund).first()
    if not fund:
        # Auto-initialize default fund campaign if not exists
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
        db.refresh(fund)

    remaining = max(0.0, fund.target_amount - fund.raised_amount)
    pct = round((fund.raised_amount / fund.target_amount * 100.0), 1) if fund.target_amount > 0 else 100.0

    return ReliefFundResponse(
        id=fund.id,
        campaign_name=fund.campaign_name,
        target_amount=fund.target_amount,
        raised_amount=fund.raised_amount,
        remaining_amount=remaining,
        donor_count=fund.donor_count,
        funding_progress_pct=pct,
        food_relief_allocation=fund.food_relief_allocation,
        medical_aid_allocation=fund.medical_aid_allocation,
        shelters_allocation=fund.shelters_allocation,
        infrastructure_allocation=fund.infrastructure_allocation,
        emergency_cash_allocation=fund.emergency_cash_allocation,
        updated_at=fund.updated_at,
    )


@router.get("/donations", response_model=List[ReliefDonationResponse], summary="List recent relief donations")
def get_relief_donations(
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
):
    donations = db.query(ReliefDonation).order_by(ReliefDonation.id.desc()).limit(limit).all()
    return donations


@router.post("/donations", response_model=ReliefDonationResponse, status_code=status.HTTP_201_CREATED, summary="Submit a simulated relief donation")
def submit_relief_donation(donation_in: ReliefDonationCreate, db: Session = Depends(get_db)):
    tx_ref = f"TXN-KD-{uuid.uuid4().hex[:8].upper()}"
    donation = ReliefDonation(
        donor_name=donation_in.donor_name or "Anonymous Supporter",
        amount=donation_in.amount,
        category=donation_in.category or "All Areas (General Relief)",
        transaction_ref=tx_ref,
        payment_method="UPI / Direct Transfer (Demo)",
        message=donation_in.message,
    )
    db.add(donation)

    # Update overall fundraising total
    fund = db.query(ReliefFund).first()
    if fund:
        fund.raised_amount += donation_in.amount
        fund.donor_count += 1
        fund.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(donation)

    donation_response = ReliefDonationResponse.model_validate(donation)

    ws_manager.broadcast_sync({
        "event": "NEW_DONATION",
        "data": donation_response.model_dump(mode="json"),
        "message": f"New contribution: ₹{donation.amount:,.0f} from {donation.donor_name} for {donation.category}"
    })

    return donation_response

