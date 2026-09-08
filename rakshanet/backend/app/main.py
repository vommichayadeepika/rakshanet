from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import Base, engine
import app.models  # ensure all models are registered with SQLAlchemy metadata
from app.routers import (
    health_router,
    zones_router,
    alerts_router,
    drone_router,
    sos_router,
    teams_router,
    intelligence_router,
    simulation_router,
    reports_router,
    demo_router,
    environmental_router,
    routes_router,  # Phase 7
    relief_router,  # Phase 8
)



# Initialize Database Schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "RakshaNet AI Decision & Coordination Platform for Disaster Response. "
        "Transforms SACHET-style alerts, environmental indicators, drone readings, "
        "and multilingual citizen SOS into prioritized action."
    ),
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits local frontend development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Modular Routers
app.include_router(health_router)
app.include_router(zones_router)
app.include_router(alerts_router)
app.include_router(drone_router)
app.include_router(sos_router)
app.include_router(teams_router)
app.include_router(intelligence_router)
app.include_router(simulation_router)
app.include_router(reports_router)
app.include_router(demo_router)

app.include_router(environmental_router)
app.include_router(routes_router)  # Phase 7 – Route Intelligence
app.include_router(relief_router)  # Phase 8 – Post-Disaster Relief & Damage Assessment


# Mount WebSocket Real-Time Router
from app.websocket import ws_router
app.include_router(ws_router)


# Mount Frontend Static Assets & Command Center Dashboard
import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    app.mount("/static", StaticFiles(directory=frontend_dir), name="static")

    @app.get("/dashboard", tags=["Operations Dashboard"])
    def get_dashboard():
        """Serves the RakshaNet React 18 + Leaflet Command Center Dashboard."""
        index_path = os.path.join(frontend_dir, "index.html")
        return FileResponse(index_path)


@app.get("/")
def root():
    return {
        "platform": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "dashboard": "/dashboard",
        "status": "online",
        "description": "Decision + Coordination layer for disaster management"
    }

