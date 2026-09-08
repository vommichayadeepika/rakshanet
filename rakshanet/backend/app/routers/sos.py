from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.sos import SOSReport
from app.ai.sos_nlp import sos_nlp
from app.schemas.sos import (
    SOSCreate,
    SOSUpdate,
    SOSResponse,
    SOSExtractionResponse,
    SOSAnalyzeRequest,
)

router = APIRouter(prefix="/sos", tags=["Citizen SOS"])


def build_sos_response(sos: SOSReport) -> SOSResponse:
    """Helper to construct SOSResponse with rich structured NLP metadata."""
    nlp_res = sos_nlp.process_sos(sos.message)
    extraction = SOSExtractionResponse(
        detected_language=sos.language or nlp_res.detected_language,
        language_name=nlp_res.language_name,
        is_transliterated=nlp_res.is_transliterated,
        need_type=sos.need_type or nlp_res.need_type,
        urgency=sos.urgency or nlp_res.urgency,
        priority_score=sos.priority_score or nlp_res.priority_score,
        people_count=nlp_res.people_count,
        is_life_threatening=nlp_res.is_life_threatening,
        danger_factors=nlp_res.danger_factors,
        location_mentions=nlp_res.location_mentions,
        extracted_keywords=nlp_res.extracted_keywords
    )
    resp = SOSResponse.model_validate(sos)
    resp.structured_extraction = extraction
    return resp


@router.post("/analyze", response_model=SOSExtractionResponse)
def analyze_sos_message(req: SOSAnalyzeRequest):
    """
    NLP Analysis Sandbox Endpoint.
    Analyzes raw distress text in English, Hindi, Telugu, Tamil, Kannada, Malayalam,
    or Transliterated / Romanized Indian languages without writing to the database.
    Extracts need type, urgency, danger factors, people count, location cues, and priority score.
    """
    res = sos_nlp.process_sos(req.message)
    return SOSExtractionResponse(
        detected_language=res.detected_language,
        language_name=res.language_name,
        is_transliterated=res.is_transliterated,
        need_type=res.need_type,
        urgency=res.urgency,
        priority_score=res.priority_score,
        people_count=res.people_count,
        is_life_threatening=res.is_life_threatening,
        danger_factors=res.danger_factors,
        location_mentions=res.location_mentions,
        extracted_keywords=res.extracted_keywords
    )


@router.get("", response_model=List[SOSResponse])
def get_all_sos(
    status_filter: Optional[str] = None,
    urgency_filter: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Retrieve citizen SOS emergency reports.
    Supports filtering by status ('SUBMITTED', 'ASSIGNED', 'EN_ROUTE', 'ON_SITE', 'COMPLETED')
    and urgency ('low', 'medium', 'high', 'critical').
    """
    query = db.query(SOSReport)
    if status_filter:
        query = query.filter(SOSReport.status == status_filter.upper())
    if urgency_filter:
        query = query.filter(SOSReport.urgency == urgency_filter.lower())
    reports = query.order_by(SOSReport.priority_score.desc(), SOSReport.timestamp.desc()).limit(limit).all()
    return [build_sos_response(s) for s in reports]


@router.post("", response_model=SOSResponse, status_code=status.HTTP_201_CREATED)
def submit_sos(sos_in: SOSCreate, db: Session = Depends(get_db)):
    """
    Submit a citizen SOS distress report.
    Executes the Multilingual SOS NLP pipeline to automatically extract language,
    emergency need category, life danger triggers, urgency, and calibrated priority score.
    """
    nlp_res = sos_nlp.process_sos(sos_in.message)

    # Use explicit input overrides if specified, otherwise populate with NLP extraction
    lang = sos_in.language or nlp_res.detected_language
    need = sos_in.need_type or nlp_res.need_type
    urgency = sos_in.urgency or nlp_res.urgency
    priority_score = nlp_res.priority_score

    sos = SOSReport(
        user_id=sos_in.user_id,
        message=sos_in.message,
        language=lang,
        need_type=need,
        urgency=urgency,
        latitude=sos_in.latitude,
        longitude=sos_in.longitude,
        priority_score=priority_score,
        status="SUBMITTED"
    )
    db.add(sos)
    db.commit()
    db.refresh(sos)

    # Sync into relief_requests for Community Assistance workflow
    try:
        from app.models.relief import ReliefRequest
        loc_str = f"Sector Near ({sos.latitude:.3f}, {sos.longitude:.3f})"
        if nlp_res.location_mentions and len(nlp_res.location_mentions) > 0:
            loc_str = f"{nlp_res.location_mentions[0]} Sector"
            
        rel_req = ReliefRequest(
            request_code=f"REQ-SOS-{sos.id}",
            location_name=loc_str,
            latitude=sos.latitude,
            longitude=sos.longitude,
            category=need.capitalize() if need else "Emergency Aid",
            priority=urgency.capitalize() if urgency else "High",
            priority_score=priority_score,
            people_count=nlp_res.people_count,
            notes=sos.message,
            status="Pending"
        )
        db.add(rel_req)
        db.commit()
    except Exception as e:
        print("[RakshaNet] Notice: Relief request sync skipped:", e)
    
    # Broadcast live SOS update to all connected WebSocket clients
    sos_response = build_sos_response(sos)
    from app.websocket import ws_manager
    ws_manager.broadcast_sync({
        "event": "NEW_SOS",
        "data": sos_response.model_dump(),
        "timestamp": sos.timestamp.isoformat()
    })
    
    return sos_response



@router.get("/{sos_id}", response_model=SOSResponse)
def get_sos_by_id(sos_id: int, db: Session = Depends(get_db)):
    """Retrieve detailed SOS report by ID with structured NLP intelligence."""
    sos = db.query(SOSReport).filter(SOSReport.id == sos_id).first()
    if not sos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"SOS report {sos_id} not found")
    return build_sos_response(sos)


@router.patch("/{sos_id}", response_model=SOSResponse)
def update_sos(sos_id: int, update_in: SOSUpdate, db: Session = Depends(get_db)):
    """Update SOS assignment status, priority score, or assigned team."""
    sos = db.query(SOSReport).filter(SOSReport.id == sos_id).first()
    if not sos:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"SOS report {sos_id} not found")
    
    for field, value in update_in.model_dump(exclude_unset=True).items():
        setattr(sos, field, value)
    
    db.commit()
    db.refresh(sos)
    return build_sos_response(sos)
