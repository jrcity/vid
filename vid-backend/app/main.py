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
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
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

# ── CORS — allow React frontend to call this API ───────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

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
