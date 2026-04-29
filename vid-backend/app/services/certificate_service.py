"""
app/services/certificate_service.py

VID Certificate generator.

Generates:
  - A unique VID ID  (e.g. VID-NG-2026-8F4A2C91)
  - A QR code PNG encoded as a base64 data URL
  - A SHA-256 certificate hash (only thing stored in DB)
  - Issue and expiry dates (1-year validity)
"""
import hashlib
import secrets
import base64
import io
from datetime import datetime, timezone, timedelta
import qrcode
from qrcode.image.pure import PyPNGImage

from app.models.schemas import (
    VIDCertificate,
    TrustScoreResponse,
    CountryInfo,
)
from app.services.trust_engine import mask_phone


# ── VID ID generator ──────────────────────────────────────────────────────────

def generate_vid_id(iso_code: str) -> str:
    """
    Generate a unique, human-readable VID identifier.
    Format: VID-{ISO}-{YEAR}-{8 HEX CHARS}
    Example: VID-NG-2026-8F4A2C91
    """
    year = datetime.now(timezone.utc).year
    unique_part = secrets.token_hex(4).upper()
    return f"VID-{iso_code.upper()}-{year}-{unique_part}"


# ── Certificate hash ──────────────────────────────────────────────────────────

def compute_certificate_hash(
    vid_id: str,
    masked_phones: list[str],
    iso_code: str,
    score: int,
    issued_at: datetime,
) -> str:
    """
    SHA-256 hash of non-personal certificate fields.
    This is the ONLY thing stored in our database —
    no names, no raw phone numbers, no location data.
    """
    data = f"{vid_id}|{'|'.join(masked_phones)}|{iso_code}|{score}|{issued_at.isoformat()}"
    return hashlib.sha256(data.encode()).hexdigest()


# ── QR code generator ─────────────────────────────────────────────────────────

def generate_qr_code(vid_id: str, base_verify_url: str = "https://vid.africa/verify") -> str:
    """
    Generate a QR code PNG as a base64 data URL.
    The QR code encodes the verification URL: https://vid.africa/verify/{vid_id}
    Third parties scan this to verify identity without receiving personal data.
    """
    verify_url = f"{base_verify_url}/{vid_id}"

    qr = qrcode.QRCode(
        version=None,      # auto-size
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=6,
        border=2,
    )
    qr.add_data(verify_url)
    qr.make(fit=True)

    # Generate PNG in memory
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)

    # Encode as base64 data URL for direct use in <img src="...">
    b64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/png;base64,{b64}"


# ── Main certificate builder ──────────────────────────────────────────────────

def build_certificate(
    phone_numbers: list[str],
    full_name: str,
    country_iso: str,
    country_config: dict,
    trust_score: TrustScoreResponse,
) -> VIDCertificate:
    """
    Assemble the full VID certificate from all components.
    """
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=365)

    vid_id = generate_vid_id(country_iso)
    masked_phones = [mask_phone(p) for p in phone_numbers]

    country_info = CountryInfo(
        iso=country_iso,
        name=country_config["name"],
        vid_label=country_config["vid_label"],
        region=country_config["region"],
        mnos=country_config.get("mnos", []),
        prefix=country_config.get("prefix", ""),
    )

    cert_hash = compute_certificate_hash(
        vid_id=vid_id,
        masked_phones=masked_phones,
        iso_code=country_iso,
        score=trust_score.score,
        issued_at=now,
    )

    qr_data_url = generate_qr_code(vid_id)

    return VIDCertificate(
        vid_id=vid_id,
        holder_name=full_name,
        masked_phones=masked_phones,
        country=country_info,
        trust_score=trust_score,
        issued_at=now,
        expires_at=expires,
        qr_data_url=qr_data_url,
        certificate_hash=cert_hash,
    )
