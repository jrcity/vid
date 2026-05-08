"""
app/services/store.py — SQLite-backed Persistence (Sprint 3)

Ensures that VID certificates are persisted across server restarts 
and enforces uniqueness constraints to prevent duplicate identities.
"""
import sqlite3
import hashlib
import os
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from app.core.config import get_settings

settings = get_settings()
DB_PATH = settings.certificate_store_path

# Ensure data directory exists
os.makedirs(os.path.dirname(os.path.abspath(DB_PATH)), exist_ok=True)

# ── Hashing helper ────────────────────────────────────────────────────────────

def _hash_phone(phone: str) -> str:
    """SHA-256 hash of phone number — never store the raw number."""
    return hashlib.sha256(phone.strip().encode()).hexdigest()

# ── Initialization ───────────────────────────────────────────────────────────

def initialize_store():
    """Initialise SQLite database and create tables if missing."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Main certificates table
        cursor.execute("""
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
                revoked INTEGER NOT NULL DEFAULT 0,
                revoked_at TEXT,
                last_refreshed TEXT,
                explanation TEXT
            )
        """)
        
        # Phone index table (one-to-many: a VID can have multiple phones)
        # phone_hash is the PRIMARY KEY to enforce unique identity per number
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS certificate_phones (
                phone_hash TEXT PRIMARY KEY,
                vid_id TEXT NOT NULL,
                FOREIGN KEY(vid_id) REFERENCES certificates(vid_id) ON DELETE CASCADE
            )
        """)
        conn.commit()
    print(f"[STORE] SQLite initialised at {DB_PATH}")

# ── Save ──────────────────────────────────────────────────────────────────────

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
    explanation: str | None = None,
    phone_numbers: list[str] | None = None,
    consent_given: bool = True
) -> None:
    """Save certificate record and link phone numbers."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        
        # Insert or replace main record
        cursor.execute("""
            INSERT OR REPLACE INTO certificates (
                vid_id, certificate_hash, iso_code, vid_label, region,
                nationality, trust_grade, score, issued_at, expires_at,
                consent_given, revoked, explanation
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            vid_id, certificate_hash, iso_code, vid_label, region,
            nationality, trust_grade, score, issued_at.isoformat(), 
            expires_at.isoformat(), 1 if consent_given else 0, 0, explanation
        ))
        
        # Insert phone links
        if phone_numbers:
            for phone in phone_numbers:
                h = _hash_phone(phone)
                try:
                    cursor.execute(
                        "INSERT OR IGNORE INTO certificate_phones (phone_hash, vid_id) VALUES (?, ?)",
                        (h, vid_id)
                    )
                except sqlite3.IntegrityError:
                    pass # Already linked
        
        conn.commit()

# ── Lookup ────────────────────────────────────────────────────────────────────

def get_certificate(vid_id: str) -> Optional[dict]:
    """Retrieve full certificate details by VID ID."""
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM certificates WHERE vid_id = ?", (vid_id,))
        row = cursor.fetchone()
        
        if row:
            res = dict(row)
            # Fetch associated phones
            cursor.execute("SELECT phone_hash FROM certificate_phones WHERE vid_id = ?", (vid_id,))
            res["phone_hashes"] = [r[0] for r in cursor.fetchall()]
            res["primary_phone"] = res["phone_hashes"][0] if res["phone_hashes"] else None
            return res
    return None

def get_by_phone(phone: str) -> Optional[dict]:
    """Look up an existing certificate by a phone number."""
    h = _hash_phone(phone)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT vid_id FROM certificate_phones WHERE phone_hash = ?", (h,))
        row = cursor.fetchone()
        if row:
            return get_certificate(row[0])
    return None

def get_vid_id_by_phone(phone: str) -> Optional[str]:
    """Get the VID-ID linked to a phone number."""
    h = _hash_phone(phone)
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT vid_id FROM certificate_phones WHERE phone_hash = ?", (h,))
        row = cursor.fetchone()
        return row[0] if row else None

def get_all_active() -> dict[str, dict]:
    """Return all non-revoked, non-expired certificates for monitoring."""
    now = datetime.now(timezone.utc).isoformat()
    active = {}
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM certificates 
            WHERE revoked = 0 AND expires_at > ?
        """, (now,))
        for row in cursor.fetchall():
            active[row["vid_id"]] = dict(row)
    return active

# ── Update ────────────────────────────────────────────────────────────────────

def update_score(vid_id: str, new_score: int, new_grade: str) -> bool:
    """Update trust score during re-enrollment."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE certificates 
            SET score = ?, trust_grade = ?, last_refreshed = ?
            WHERE vid_id = ?
        """, (new_score, new_grade, datetime.now(timezone.utc).isoformat(), vid_id))
        return cursor.rowcount > 0

# ── Revocation ────────────────────────────────────────────────────────────────

def revoke_certificate(vid_id: str) -> bool:
    """Permanently revoke a certificate."""
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE certificates 
            SET revoked = 1, revoked_at = ?
            WHERE vid_id = ?
        """, (datetime.now(timezone.utc).isoformat(), vid_id))
        return cursor.rowcount > 0

def is_valid(vid_id: str) -> bool:
    """Check if a certificate is currently valid (not revoked, not expired)."""
    record = get_certificate(vid_id)
    if not record or record.get("revoked"):
        return False
    expires = datetime.fromisoformat(record["expires_at"])
    return datetime.now(timezone.utc) < expires
