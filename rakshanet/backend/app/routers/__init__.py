from app.routers.health import router as health_router
from app.routers.zones import router as zones_router
from app.routers.alerts import router as alerts_router
from app.routers.drone import router as drone_router
from app.routers.sos import router as sos_router
from app.routers.teams import router as teams_router
from app.routers.intelligence import router as intelligence_router
from app.routers.simulation import router as simulation_router
from app.routers.reports import router as reports_router
from app.routers.demo import router as demo_router
from app.routers.environmental import router as environmental_router
from app.routers.routes import router as routes_router  # Phase 7
from app.routers.relief import router as relief_router  # Phase 8

__all__ = [
    "health_router",
    "zones_router",
    "alerts_router",
    "drone_router",
    "sos_router",
    "teams_router",
    "intelligence_router",
    "simulation_router",
    "reports_router",
    "demo_router",
    "environmental_router",
    "routes_router",  # Phase 7
    "relief_router",  # Phase 8
]


