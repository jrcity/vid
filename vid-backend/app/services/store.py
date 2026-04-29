"""
app/services/store.py

Certificate store — in-memory for hackathon, swap for PostgreSQL in production.

What is stored per certificate:
  - vid_id           (public identifier)
  - certificate_hash (SHA-256 of non-personal fields)
  - iso_code         (country)
  - vid_label        (e.g. "Virtual NIN")
  - region
  - trust_grade      (e.g. "High confidence")
  - score            (0–100)
  - issued_at
  - expires_at

What is NOT stored:
  - Full name
  - Raw phone numbers
  - Location coordinates
  - Any raw CAMARA API response data
"""
from datetime import datetime, timezone
from typing import Optional


# In-memory store: vid_id → record dict
_store: dict[str, dict] = {}


def save_certificate(
    vid_id: str,
    certificate_hash: str,
    iso_code: str,
    vid_label: str,
    region: str,
    nationality: str,
    trust_grade: str,
    score: int,
    issued_at: datetime,
    expires_at: datetime,
) -> None:
    _store[vid_id] = {
        "vid_id": vid_id,
        "certificate_hash": certificate_hash,
        "iso_code": iso_code,
        "vid_label": vid_label,
        "region": region,
        "nationality": nationality,
        "trust_grade": trust_grade,
        "score": score,
        "issued_at": issued_at.isoformat(),
        "expires_at": expires_at.isoformat(),
        "revoked": False,
    }


def get_certificate(vid_id: str) -> Optional[dict]:
    return _store.get(vid_id)


def revoke_certificate(vid_id: str) -> bool:
    """Mark a certificate as revoked (e.g. SIM swap detected post-issuance)."""
    if vid_id in _store:
        _store[vid_id]["revoked"] = True
        return True
    return False


def is_valid(vid_id: str) -> bool:
    record = _store.get(vid_id)
    if not record:
        return False
    if record.get("revoked"):
        return False
    expires = datetime.fromisoformat(record["expires_at"])
    return datetime.now(timezone.utc) < expires
