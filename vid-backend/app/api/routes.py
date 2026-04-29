"""
app/api/routes.py

All VID API endpoints.

Endpoints:
  GET  /health                  — health check
  GET  /countries               — list all supported countries for frontend dropdown
  POST /resolve-phone           — detect country from phone number
  POST /enroll                  — main enroll flow (CAMARA calls + certificate)
  GET  /verify/{vid_id}         — third-party QR verification
"""
from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone

from app.models.schemas import (
    EnrollRequest,
    EnrollResponse,
    VerifyResponse,
    ResolvePhoneResponse,
    HealthResponse,
)
from app.services.camara_service import fetch_all_signals
from app.services.trust_engine import (
    build_trust_score,
    resolve_country_from_phone,
)
from app.services.certificate_service import build_certificate
from app.services import store
from app.core.config import get_settings
from app.core.country_config import get_all_countries, get_country

router = APIRouter()
settings = get_settings()


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Check API is live and confirm Nokia NaC connection status."""
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        environment=settings.app_env,
        nokia_nac_connected=not settings.use_mock_apis,
        mock_mode=settings.use_mock_apis,
    )


# ── Countries ─────────────────────────────────────────────────────────────────

@router.get("/countries", tags=["Reference"])
async def list_countries():
    """
    Return all 54+ supported African countries for the frontend dropdown.
    Used by the enrollment form to show auto-detected or manually selected country.
    """
    return {"countries": get_all_countries()}


# ── Phone resolver ────────────────────────────────────────────────────────────

@router.post("/resolve-phone", response_model=ResolvePhoneResponse, tags=["Reference"])
async def resolve_phone(body: dict):
    """
    Detect country from a phone number.
    Called by the frontend on every phone input change for real-time country auto-detection.

    Input:  { "phone": "+2348031234567" }
    Output: country info object
    """
    phone = body.get("phone", "").strip()
    if not phone:
        raise HTTPException(status_code=400, detail="phone is required")

    iso, config = resolve_country_from_phone(phone)

    if iso == "UNKNOWN" or not config:
        return ResolvePhoneResponse(
            phone=phone,
            iso_code="UNKNOWN",
            country_name="Unknown",
            vid_label="Virtual Network ID",
            region="Africa",
            prefix="",
            valid=False,
            error="Could not detect country from this phone number",
        )

    return ResolvePhoneResponse(
        phone=phone,
        iso_code=iso,
        country_name=config["name"],
        vid_label=config["vid_label"],
        region=config["region"],
        prefix=config.get("prefix", ""),
        valid=True,
    )


# ── Enroll ────────────────────────────────────────────────────────────────────

@router.post("/enroll", response_model=EnrollResponse, tags=["VID"])
async def enroll(request: EnrollRequest):
    """
    Main VID enrollment endpoint.

    Flow:
      1. Validate consent (required)
      2. Resolve country from primary phone number
      3. Call all 5 CAMARA APIs for each declared SIM
      4. Score signals through trust engine
      5. Generate VID certificate + QR code
      6. Save certificate hash to store
      7. Return full certificate to frontend

    Privacy guarantee:
      - CAMARA APIs return yes/no only — no raw subscriber data received
      - Only certificate hash, score, and country stored
      - Full name and phone numbers are NOT stored
    """
    if not request.consent:
        raise HTTPException(status_code=400, detail="User consent is required")

    phone_numbers = [p.number for p in request.phone_numbers]
    primary_phone = phone_numbers[0]

    # Resolve country from primary phone
    iso, country_config = resolve_country_from_phone(primary_phone)
    if iso == "UNKNOWN" or not country_config:
        raise HTTPException(
            status_code=422,
            detail=f"Could not resolve country from phone number {primary_phone}. "
                   "Ensure the number is in E.164 format (e.g. +2348031234567).",
        )

    # Fetch CAMARA signals for all declared SIMs
    all_signals = []
    for phone in phone_numbers:
        try:
            signals = await fetch_all_signals(
                phone=phone,
                name=request.full_name,
                country_iso=iso,
            )
            all_signals.append(signals)
        except Exception as e:
            # If one SIM fails, log and continue with others
            print(f"[Enroll] Signal fetch failed for {phone}: {e}")
            continue

    if not all_signals:
        raise HTTPException(
            status_code=503,
            detail="Could not fetch network signals. Please try again.",
        )

    # Build trust score
    trust_score = build_trust_score(
        all_signals_per_sim=all_signals,
        phone_numbers=phone_numbers,
        name=request.full_name,
        country_name=country_config["name"],
    )

    # Build certificate
    certificate = build_certificate(
        phone_numbers=phone_numbers,
        full_name=request.full_name,
        country_iso=iso,
        country_config=country_config,
        trust_score=trust_score,
    )

    # Save to store (hash only — no personal data)
    store.save_certificate(
        vid_id=certificate.vid_id,
        certificate_hash=certificate.certificate_hash,
        iso_code=iso,
        vid_label=country_config["vid_label"],
        region=country_config["region"],
        nationality=country_config["name"],
        trust_grade=trust_score.grade,
        score=trust_score.score,
        issued_at=certificate.issued_at,
        expires_at=certificate.expires_at,
    )

    return EnrollResponse(success=True, certificate=certificate)


# ── Verify ────────────────────────────────────────────────────────────────────

@router.get("/verify/{vid_id}", response_model=VerifyResponse, tags=["VID"])
async def verify(vid_id: str):
    """
    Third-party QR code verification endpoint.

    Called when a bank, clinic, school, or NGO scans the VID QR code.
    Returns ONLY:
      - valid: bool
      - nationality (country name)
      - vid_label (e.g. "Virtual NIN")
      - region
      - trust_grade
      - score
      - dates

    Does NOT return:
      - Holder name
      - Phone numbers
      - Any personal data
    """
    record = store.get_certificate(vid_id)

    if not record:
        raise HTTPException(status_code=404, detail="VID certificate not found")

    if record.get("revoked"):
        return VerifyResponse(
            valid=False,
            vid_id=vid_id,
            nationality=record["nationality"],
            vid_label=record["vid_label"],
            region=record["region"],
            trust_grade="Revoked",
            score=0,
            issued_at=record["issued_at"],
            expires_at=record["expires_at"],
        )

    is_valid = store.is_valid(vid_id)

    return VerifyResponse(
        valid=is_valid,
        vid_id=vid_id,
        nationality=record["nationality"],
        vid_label=record["vid_label"],
        region=record["region"],
        trust_grade=record["trust_grade"],
        score=record["score"],
        issued_at=record["issued_at"],
        expires_at=record["expires_at"],
    )
