from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.team import Team
from app.schemas.team import TeamCreate, TeamUpdate, TeamResponse

router = APIRouter(prefix="/teams", tags=["Rescue Teams"])


@router.get("", response_model=List[TeamResponse])
def get_all_teams(status_filter: Optional[str] = None, db: Session = Depends(get_db)):
    """Retrieve all emergency rescue and volunteer response teams."""
    query = db.query(Team)
    if status_filter:
        query = query.filter(Team.status == status_filter.upper())
    return query.all()


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(team_in: TeamCreate, db: Session = Depends(get_db)):
    """Register or deploy a new response team."""
    team = Team(**team_in.model_dump())
    db.add(team)
    db.commit()
    db.refresh(team)
    return team


@router.get("/{team_id}", response_model=TeamResponse)
def get_team_by_id(team_id: int, db: Session = Depends(get_db)):
    """Get single team details."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Team {team_id} not found")
    return team


@router.patch("/{team_id}", response_model=TeamResponse)
def update_team(team_id: int, update_in: TeamUpdate, db: Session = Depends(get_db)):
    """Update team status (e.g. AVAILABLE -> EN_ROUTE -> ON_SITE), task or GPS location."""
    team = db.query(Team).filter(Team.id == team_id).first()
    if not team:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Team {team_id} not found")
    
    for field, value in update_in.model_dump(exclude_unset=True).items():
        setattr(team, field, value)
        
    db.commit()
    db.refresh(team)
    return team
