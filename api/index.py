import sys
import os
import traceback

current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)

candidates = [
    os.path.join(root_dir, "backend"),
    os.path.join(current_dir, "backend"),
    root_dir,
    current_dir
]

for p in candidates:
    if os.path.exists(p) and p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
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
    version="1.0.0"
)

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
