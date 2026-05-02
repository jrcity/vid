"""
app/main.py

FastAPI application entry point.

To run locally:
    uvicorn app.main:app --reload --port 8000

API docs available at:
    http://localhost:8000/docs       (Swagger UI)
    http://localhost:8000/redoc      (ReDoc)
"""
from fastapi import FastAPI
import logging
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.api.routes import router
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.services.store import init_db
from contextlib import asynccontextmanager

settings = get_settings()
logging.basicConfig(
    level=logging.INFO if settings.app_env != "production" else logging.WARNING,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema on startup
    init_db()
    yield

app = FastAPI(
    lifespan=lifespan,
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "VID (Virtual ID) — Pan-African Network Identity API. "
        "Uses Nokia Network-as-Code CAMARA APIs to derive a trust score "
        "from mobile network signals. No raw personal data stored."
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


@app.get("/", tags=["System"])
async def root():
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health",
        "mock_mode": settings.use_mock_apis,
    }
