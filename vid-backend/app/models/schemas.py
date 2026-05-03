"""
app/models/schemas.py
All Pydantic request/response models for the VID API.
"""
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime
import re


# ── Enroll ─────────────────────────────────────────────────────────────────────

class PhoneEntry(BaseModel):
    number: str          # E.164 format e.g. +2348031234567
    is_primary: bool = False

    @field_validator("number")
    @classmethod
    def validate_phone(cls, v):
        v = v.strip()
        if not v.startswith("+"):
            raise ValueError("Phone number must be in E.164 format starting with +")
        if not re.match(r"^\+\d{7,15}$", v):
            raise ValueError("Invalid phone number format")
        return v


class LocationInput(BaseModel):
    latitude: float
    longitude: float
    radius: float = 10000.0  # Default 10km radius


class EnrollRequest(BaseModel):
    phone_numbers: list[PhoneEntry]   # 1–3 SIM numbers
    full_name: str                    # User's name (not verified by VID — entered by user)
    consent: bool                     # MUST be True — consent to network queries
    location: Optional[LocationInput] = None
    biometric_passed: bool = False    # New: face verification result from frontend

    @field_validator("phone_numbers")
    @classmethod
    def validate_phone_list(cls, v):
        if not v:
            raise ValueError("At least one phone number is required")
        if len(v) > 3:
            raise ValueError("Maximum 3 SIM numbers allowed")
        numbers = [entry.number for entry in v]
        if len(set(numbers)) != len(numbers):
            raise ValueError("Phone numbers must be unique")
        primary_count = sum(1 for entry in v if entry.is_primary)
        if primary_count > 1:
            raise ValueError("Only one phone number can be marked as primary")
        return v

    @field_validator("full_name")
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        return v


# ── Signal results ─────────────────────────────────────────────────────────────

class SignalResult(BaseModel):
    api_name: str         # e.g. "SIM Swap"
    signal_key: str       # e.g. "sim_swap"
    passed: bool          # True = good identity signal
    partial: bool = False  # True if result is 'PARTIAL'
    weight: float         # contribution to score (0.0–1.0)
    display_value: str    # e.g. "No swap · 24 months"
    detail: str           # plain language detail


# ── Trust score ────────────────────────────────────────────────────────────────

class TrustScoreResponse(BaseModel):
    score: int                         # 0–100
    grade: str                         # "High confidence" | "Moderate confidence" | "Low confidence"
    signals: list[SignalResult]
    explanation: str                   # AI plain-language explanation
    multi_sim_bonus: int               # 0–5 bonus points for cross-SIM consistency


# ── Country info ───────────────────────────────────────────────────────────────

class CountryInfo(BaseModel):
    iso: str
    name: str
    vid_label: str                     # e.g. "Virtual NIN"
    region: str                        # e.g. "West Africa"
    mnos: list[str]
    prefix: str


# ── VID Certificate ────────────────────────────────────────────────────────────

class VIDCertificate(BaseModel):
    vid_id: str                        # e.g. VID-NG-2026-8F4A2C91
    holder_name: str
    masked_phones: list[str]           # e.g. ["+234 8XX XXX XX67"]
    country: CountryInfo
    trust_score: TrustScoreResponse
    issued_at: datetime
    expires_at: datetime
    qr_data_url: str                   # base64 PNG data URL for the QR code
    certificate_hash: str              # SHA-256 hash stored in DB (not personal data)


# ── Enroll response ────────────────────────────────────────────────────────────

class EnrollResponse(BaseModel):
    success: bool
    certificate: Optional[VIDCertificate] = None
    error: Optional[str] = None


# ── Verify (third-party QR scan) ──────────────────────────────────────────────

class VerifyResponse(BaseModel):
    valid: bool
    vid_id: str
    nationality: str                   # country name only
    vid_label: str                     # e.g. "Virtual NIN"
    region: str
    trust_grade: str                   # "High confidence" etc.
    score: int
    issued_at: str
    expires_at: str
    # NOTE: No personal data (no name, no phone) returned to third parties


# ── Country resolver ───────────────────────────────────────────────────────────

class ResolvePhoneResponse(BaseModel):
    phone: str
    iso_code: str
    country_name: str
    vid_label: str
    region: str
    prefix: str
    valid: bool
    error: Optional[str] = None


# ── Health check ──────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    environment: str
    nokia_nac_connected: bool
    mock_mode: bool
