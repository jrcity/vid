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
import asyncio
import logging

from fastapi import APIRouter, HTTPException, Request

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
    mask_phone,
)
from app.services.certificate_service import build_certificate
from app.services import store
from app.core.config import get_settings
from app.core.country_config import get_all_countries
from app.core.rate_limit import limiter

router = APIRouter()
settings = get_settings()
logger = logging.getLogger(__name__)


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
@limiter.limit(settings.rate_limit_enroll)
async def enroll(request: Request, enroll_request: EnrollRequest):
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
    if not enroll_request.consent:
        raise HTTPException(status_code=400, detail="User consent is required")

    primary_entry = next(
        (phone for phone in enroll_request.phone_numbers if phone.is_primary),
        enroll_request.phone_numbers[0],
    )
    ordered_entries = [primary_entry] + [
        phone for phone in enroll_request.phone_numbers
        if phone.number != primary_entry.number
    ]
    phone_numbers = [p.number for p in ordered_entries]
    primary_phone = phone_numbers[0]

    # Resolve country from primary phone
    iso, country_config = resolve_country_from_phone(primary_phone)
    if iso == "UNKNOWN" or not country_config:
        raise HTTPException(
            status_code=422,
            detail=f"Could not resolve country from phone number {primary_phone}. "
                   "Ensure the number is in E.164 format (e.g. +2348031234567).",
        )

    # Fetch signals for all numbers (parallel)
    signal_results = await asyncio.gather(
        *[
            fetch_all_signals(
                phone=p,
                name=enroll_request.full_name,
                country_iso=iso,
                user_lat=enroll_request.location.latitude if enroll_request.location else None,
                user_lng=enroll_request.location.longitude if enroll_request.location else None,
                user_radius=enroll_request.location.radius if enroll_request.location else None,
                biometric_passed=enroll_request.biometric_passed,
            )
            for p in phone_numbers
        ],
        return_exceptions=True,
    )

    all_signals = []
    scored_phone_numbers = []
    for phone, signals in zip(phone_numbers, signal_results):
        if isinstance(signals, Exception):
            logger.warning(
                "Signal fetch failed for %s",
                mask_phone(phone),
                exc_info=(type(signals), signals, signals.__traceback__),
            )
            continue
        all_signals.append(signals)
        scored_phone_numbers.append(phone)

    if not all_signals:
        raise HTTPException(
            status_code=502,
            detail="Could not fetch any network signals. Please ensure your SIM cards are active and try again.",
        )

    # Ensure the primary SIM was successfully verified
    if primary_phone not in scored_phone_numbers:
        raise HTTPException(
            status_code=502,
            detail=(
                f"Verification failed for primary SIM ({mask_phone(primary_phone)}). "
                "The primary SIM is required for VID enrollment."
            ),
        )

    # Ensure primary phone was successfully scored
    if primary_phone not in scored_phone_numbers:
        raise HTTPException(
            status_code=503,
            detail=(
                "Primary SIM did not return network signals. "
                "Please retry with the same primary number or choose another primary SIM."
            ),
        )

    # Build trust score
    trust_score = build_trust_score(
        all_signals_per_sim=all_signals,
        phone_numbers=scored_phone_numbers,
        name=enroll_request.full_name,
        country_name=country_config["name"],
    )

    # Reuse existing VID for the same phone if present in the store.
    existing_vid_id = None
    for phone in phone_numbers:
        existing_vid = store.get_vid_id_by_phone(phone)
        if existing_vid:
            existing_vid_id = existing_vid
            break

    is_returning = existing_vid_id is not None

    # Build certificate
    certificate = build_certificate(
        phone_numbers=scored_phone_numbers,
        full_name=enroll_request.full_name,
        country_iso=iso,
        country_config=country_config,
        trust_score=trust_score,
        base_verify_url=settings.verify_base_url,
        vid_id=existing_vid_id,
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
        consent_given=enroll_request.consent,
        phone_numbers=scored_phone_numbers,
    )

    return EnrollResponse(
        success=True,
        is_returning=is_returning,
        certificate=certificate,
    )
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
            iso_code=record["iso_code"],
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
        iso_code=record["iso_code"],
        nationality=record["nationality"],
        vid_label=record["vid_label"],
        region=record["region"],
        trust_grade=record["trust_grade"],
        score=record["score"],
        issued_at=record["issued_at"],
        expires_at=record["expires_at"],
    )
