"""
app/main.py

FastAPI application entry point.

To run locally:
    uvicorn app.main:app --reload --port 8000

API docs available at:
    http://localhost:8000/docs       (Swagger UI)
    http://localhost:8000/redoc      (ReDoc)
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
import logging
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.routes import router
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.services.store import initialize_store
from app.services.agentic_monitor import (
    start_monitoring,
    stop_monitoring,
    get_audit_log,
)
from app.services.trust_engine import get_model

settings = get_settings()
logging.basicConfig(
    level=logging.INFO if settings.app_env != "production" else logging.WARNING,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan — runs startup logic before first request,
    shutdown logic after last request.
    """
    # ── Startup ───────────────────────────────────────────────────────────────
    print("[VID] Starting up...")
    
    # 1. Initialise Persistence Layer (SQLite)
    initialize_store()
    
    # 2. Pre-train/Load Trust Engine model
    get_model()
    
    # 3. Launch Background Monitoring Agent
    start_monitoring()
    
    print("[VID] System ready and monitoring active.")

    yield  # App runs here

    # ── Shutdown ──────────────────────────────────────────────────────────────
    stop_monitoring()
    print("[VID] Shutdown complete.")


app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "VID (Virtual ID) — Pan-African Network Identity API. "
        "CAMARA APIs + Random Forest trust scoring + Agentic SIM monitoring."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS — allow React frontend to call this API ───────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(SlowAPIMiddleware)

# ── Register routes ────────────────────────────────────────────────────────────
app.include_router(router, prefix="/api/v1")


# ── Audit endpoint ──────────────────────────────────────────────────────────
@app.get("/api/v1/audit/{vid_id}", tags=["Agentic"])
async def get_certificate_audit(vid_id: str):
    """
    Return the monitoring audit trail for a specific VID certificate.
    Shows every check, swap detection, and revocation event.
    Used by the frontend to show 'Certificate history' on the verify screen.
    """
    events = get_audit_log(vid_id)
    return {
        "vid_id": vid_id,
        "event_count": len(events),
        "events": events,
    }


@app.get("/", tags=["System"])
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health",
        "mock_mode": settings.use_mock_apis,
        "agentic_monitor": "active",
    }
