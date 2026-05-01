"""
app/services/store.py

Certificate verification store.

The production path is intentionally privacy-preserving: store only the public
VID identifier, certificate hash, country metadata, score, dates, and revocation
state. Do not store holder names, raw phone numbers, location data, or raw
CAMARA API responses.
"""
from datetime import datetime, timezone
from pathlib import Path
import sqlite3
from typing import Optional

from app.core.config import get_settings

settings = get_settings()


def _db_path() -> Path:
    path = Path(settings.certificate_store_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def initialize_store() -> None:
    """Initialize the certificate store database schema."""
    with sqlite3.connect(_db_path()) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS certificates (
                vid_id TEXT PRIMARY KEY,
                certificate_hash TEXT NOT NULL,
                iso_code TEXT NOT NULL,
                vid_label TEXT NOT NULL,
                region TEXT NOT NULL,
                nationality TEXT NOT NULL,
                trust_grade TEXT NOT NULL,
                score INTEGER NOT NULL,
                issued_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                consent_given INTEGER NOT NULL DEFAULT 1,
                revoked INTEGER NOT NULL DEFAULT 0
            )
            """
        )


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
    consent_given: bool = True,
) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO certificates (
                vid_id,
                certificate_hash,
                iso_code,
                vid_label,
                region,
                nationality,
                trust_grade,
                score,
                issued_at,
                expires_at,
                consent_given,
                revoked
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
            ON CONFLICT(vid_id) DO UPDATE SET
                certificate_hash = excluded.certificate_hash,
                iso_code = excluded.iso_code,
                vid_label = excluded.vid_label,
                region = excluded.region,
                nationality = excluded.nationality,
                trust_grade = excluded.trust_grade,
                score = excluded.score,
                issued_at = excluded.issued_at,
                expires_at = excluded.expires_at,
                consent_given = excluded.consent_given,
                revoked = excluded.revoked
            """,
            (
                vid_id,
                certificate_hash,
                iso_code,
                vid_label,
                region,
                nationality,
                trust_grade,
                score,
                issued_at.isoformat(),
                expires_at.isoformat(),
                1 if consent_given else 0,
            ),
        )


def get_certificate(vid_id: str) -> Optional[dict]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM certificates WHERE vid_id = ?",
            (vid_id,),
        ).fetchone()
    if not row:
        return None
    record = dict(row)
    record["revoked"] = bool(record["revoked"])
    record["consent_given"] = bool(record["consent_given"])
    return record


def revoke_certificate(vid_id: str) -> bool:
    """Mark a certificate as revoked, for example after a later SIM swap event."""
    with _connect() as conn:
        cursor = conn.execute(
            "UPDATE certificates SET revoked = 1 WHERE vid_id = ?",
            (vid_id,),
        )
        return cursor.rowcount > 0


def is_valid(vid_id: str) -> bool:
    record = get_certificate(vid_id)
    if not record or record.get("revoked"):
        return False
    expires = datetime.fromisoformat(record["expires_at"])
    return datetime.now(timezone.utc) < expires
