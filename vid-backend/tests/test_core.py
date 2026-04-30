"""
tests/test_core.py

Run with: pytest tests/ -v
"""
import os

os.environ['NOKIA_NAC_TOKEN'] = ''
os.environ['APP_ENV'] = 'test'

from datetime import datetime, timezone
from fastapi.testclient import TestClient
from app.main import app
from app.services.trust_engine import (
    resolve_country_from_phone,
    mask_phone,
    compute_multi_sim_bonus,
    compute_score,
    score_to_grade,
    signals_to_results,
    build_trust_score,
)
from app.services.camara_service import (
    AllSignals,
    SimSwapSignal,
    NumberVerificationSignal,
    KYCMatchSignal,
    LocationVerificationSignal,
    DeviceStatusSignal,
)
from app.services.certificate_service import generate_vid_id, generate_qr_code

client = TestClient(app)


# ── Country resolution ────────────────────────────────────────────────────────

def test_resolves_nigeria():
    iso, config = resolve_country_from_phone("+2348031234567")
    assert iso == "NG"
    assert config["vid_label"] == "Virtual NIN"

def test_resolves_kenya():
    iso, config = resolve_country_from_phone("+254712345678")
    assert iso == "KE"
    assert config["vid_label"] == "Virtual Huduma Namba"

def test_resolves_south_africa():
    iso, config = resolve_country_from_phone("+27831234567")
    assert iso == "ZA"

def test_resolves_ghana():
    iso, config = resolve_country_from_phone("+233244123456")
    assert iso == "GH"

def test_resolves_ethiopia():
    iso, config = resolve_country_from_phone("+251911234567")
    assert iso == "ET"

def test_invalid_number():
    iso, config = resolve_country_from_phone("not-a-number")
    assert iso == "UNKNOWN"
    assert config is None


# ── Phone masking ─────────────────────────────────────────────────────────────

def test_mask_nigeria():
    masked = mask_phone("+2348031234567")
    assert masked.startswith("+234")
    assert "4567" in masked   # last 4 digits shown

def test_mask_kenya():
    masked = mask_phone("+254712345678")
    assert masked.startswith("+254")


# ── Multi-SIM bonus ───────────────────────────────────────────────────────────

def test_single_sim_no_bonus():
    bonus = compute_multi_sim_bonus(["+2348031234567"])
    assert bonus == 0

def test_two_sims_same_country_bonus():
    bonus = compute_multi_sim_bonus(["+2348031234567", "+2341234567890"])
    assert bonus == 4  # 2 sims × 2 = 4

def test_three_sims_same_country_bonus():
    bonus = compute_multi_sim_bonus([
        "+2348031234567", "+2341234567890", "+2349031234567"
    ])
    assert bonus == 5  # capped at 5

def test_cross_country_no_bonus():
    bonus = compute_multi_sim_bonus(["+2348031234567", "+254712345678"])
    assert bonus == 0  # diaspora — no penalty, no bonus


# ── Score computation ─────────────────────────────────────────────────────────

def _perfect_signals():
    return AllSignals(
        sim_swap=SimSwapSignal(swapped_recently=False, days_since_swap=730),
        number_verification=NumberVerificationSignal(active=True, registered=True),
        kyc_match=KYCMatchSignal(name_match=True, partial=False),
        location_verification=LocationVerificationSignal(in_declared_region=True),
        device_status=DeviceStatusSignal(reachable=True, new_device=False),
    )

def _poor_signals():
    return AllSignals(
        sim_swap=SimSwapSignal(swapped_recently=True, days_since_swap=5),
        number_verification=NumberVerificationSignal(active=False, registered=False),
        kyc_match=KYCMatchSignal(name_match=False, partial=False),
        location_verification=LocationVerificationSignal(in_declared_region=False),
        device_status=DeviceStatusSignal(reachable=False, new_device=True),
    )

def test_perfect_score():
    results = signals_to_results(_perfect_signals())
    score = compute_score(results, multi_sim_bonus=0)
    assert score == 100

def test_poor_score():
    results = signals_to_results(_poor_signals())
    score = compute_score(results, multi_sim_bonus=0)
    assert score == 0

def test_bonus_caps_at_100():
    results = signals_to_results(_perfect_signals())
    score = compute_score(results, multi_sim_bonus=5)
    assert score == 100  # should not exceed 100

def test_grade_high():
    assert score_to_grade(95) == "High confidence"
    assert score_to_grade(80) == "High confidence"

def test_grade_moderate():
    assert score_to_grade(55) == "Moderate confidence"
    assert score_to_grade(79) == "Moderate confidence"

def test_grade_low():
    assert score_to_grade(54) == "Low confidence"
    assert score_to_grade(0) == "Low confidence"


# ── Full trust score build ────────────────────────────────────────────────────

def test_build_trust_score_nigeria():
    result = build_trust_score(
        all_signals_per_sim=[_perfect_signals()],
        phone_numbers=["+2348031234567"],
        name="Aminu Bello",
        country_name="Nigeria",
    )
    assert result.score == 100
    assert result.grade == "High confidence"
    assert "Nigeria" in result.explanation
    assert len(result.signals) == 5


# ── Certificate generation ────────────────────────────────────────────────────

def test_vid_id_format():
    vid_id = generate_vid_id("NG")
    prefix = f"VID-NG-{datetime.now(timezone.utc).year}-"
    assert vid_id.startswith(prefix)
    assert len(vid_id) == len(prefix) + 8

def test_qr_generates():
    qr = generate_qr_code("VID-NG-2026-TESTTEST")
    assert qr.startswith("data:image/png;base64,")
    assert len(qr) > 100


# ── API endpoints ─────────────────────────────────────────────────────────────

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "mock_mode" in body


def test_resolve_phone_endpoint():
    response = client.post("/api/v1/resolve-phone", json={"phone": "+2348031234567"})
    assert response.status_code == 200
    body = response.json()
    assert body["valid"] is True
    assert body["iso_code"] == "NG"


def test_enroll_and_verify_flow():
    enroll_response = client.post(
        "/api/v1/enroll",
        json={
            "phone_numbers": [
                {"number": "+2348031234567", "is_primary": True},
            ],
            "full_name": "Aminu Bello",
            "consent": True,
        },
    )
    assert enroll_response.status_code == 200
    certificate = enroll_response.json()["certificate"]
    assert certificate["vid_id"].startswith("VID-NG-")
    assert certificate["holder_name"] == "Aminu Bello"
    assert certificate["qr_data_url"].startswith("data:image/png;base64,")

    verify_response = client.get(f"/api/v1/verify/{certificate['vid_id']}")
    assert verify_response.status_code == 200
    verification = verify_response.json()
    assert verification["valid"] is True
    assert verification["vid_id"] == certificate["vid_id"]
    assert "holder_name" not in verification


def test_enroll_respects_declared_primary_phone():
    response = client.post(
        "/api/v1/enroll",
        json={
            "phone_numbers": [
                {"number": "+254712345678", "is_primary": False},
                {"number": "+2348031234567", "is_primary": True},
            ],
            "full_name": "Aminu Bello",
            "consent": True,
        },
    )
    assert response.status_code == 200
    certificate = response.json()["certificate"]
    assert certificate["country"]["iso"] == "NG"
    assert certificate["masked_phones"][0].startswith("+234")
