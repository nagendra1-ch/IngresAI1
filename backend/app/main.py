import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import logging
import threading
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ingres_ai")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base, init_db, SessionLocal
import app.models

def _prewarm_caches():
    """Background worker to pre-populate database in-memory caches on startup."""
    try:
        logger.info("Pre-warming in-memory datasets and caches...")
        db = SessionLocal()
        from app.routes.districts import get_districts, get_districts_map
        user_stub = type('UserStub', (), {'id': 1})()
        get_districts(db=db, current_user=user_stub)
        get_districts_map(db=db, current_user=user_stub)
        db.close()
        logger.info("Cache pre-warming completed successfully. API is primed for instant response.")
    except Exception as e:
        logger.warning(f"Cache pre-warming notice: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    is_serverless = os.environ.get("VERCEL") == "1" or os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None
    if not is_serverless:
        # Safe background init for long-running servers
        threading.Thread(target=init_db, daemon=True).start()
        threading.Thread(target=_prewarm_caches, daemon=True).start()
    yield

# Import routers directly from route modules
from app.routes.auth import router as auth_router
from app.routes.weather import router as weather_router
from app.routes.districts import router as districts_router
from app.routes.compare import router as compare_router
from app.routes.dashboard import router as dashboard_router
from app.routes.ai import router as ai_router
from app.routes.admin import router as admin_router
from app.routes.prediction import router as prediction_router

app = FastAPI(
    title="INGRES AI API",
    description="API server for INGRES AI - India's Ground Water Resource Estimation System Virtual Assistant",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS Origins list
origins = [org.strip() for org in settings.CORS_ORIGINS.split(",") if org.strip()]
if not origins or "*" in origins:
    allow_origins = ["*"]
else:
    allow_origins = origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(weather_router)
app.include_router(districts_router)
app.include_router(compare_router)
app.include_router(dashboard_router)
app.include_router(ai_router)
app.include_router(admin_router)
app.include_router(prediction_router)


@app.get("/")
@app.get("/api")
@app.get("/api/")
def read_root():
    return {
        "name": "INGRES AI API",
        "description": "AI-driven Virtual Assistant for India's Ground Water Resource Estimation System",
        "status": "Online",
        "database": "Connected & Optimized",
        "documentation_url": "/docs"
    }

@app.get("/health")
@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ingres-ai",
        "version": "1.0.0"
    }

# Unified single-container SPA static asset mounting for Docker / Render / Railway
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import HTTPException

dist_candidates = [
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "frontend", "dist"),
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "static"),
    os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dist"),
]
frontend_dist = next((p for p in dist_candidates if os.path.exists(p) and os.path.isdir(p)), None)

if frontend_dist:
    assets_dir = os.path.join(frontend_dist, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="spa_assets")

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            raise HTTPException(status_code=404, detail="API route not found")
        target = os.path.join(frontend_dist, full_path)
        if os.path.isfile(target):
            return FileResponse(target)
        index_html = os.path.join(frontend_dist, "index.html")
        if os.path.isfile(index_html):
            return FileResponse(index_html)
        return {"status": "Frontend build not found"}