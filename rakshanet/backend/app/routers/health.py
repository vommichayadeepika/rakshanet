from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db
from app.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint returning system status, database connectivity, and version.
    """
    db_status = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "degraded",
        "platform": "RakshaNet - AI Disaster Response Coordination",
        "version": settings.VERSION,
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
