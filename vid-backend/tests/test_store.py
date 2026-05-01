import pytest
from datetime import datetime, timedelta, timezone
from app.services import store

@pytest.fixture(autouse=True)
def setup_db():
    """Ensure database is initialized before each test."""
    store.init_db()

def make_sample_cert(vid_id: str, expires_at: datetime):
    return {
        "vid_id": vid_id,
        "certificate_hash": "hash_123",
        "iso_code": "NG",
        "vid_label": "Virtual NIN",
        "region": "West Africa",
        "nationality": "Nigeria",
        "trust_grade": "High confidence",
        "score": 95,
        "issued_at": datetime.now(timezone.utc),
        "expires_at": expires_at,
        "consent_given": True,
    }

def test_store_round_trip():
    """Save and retrieve a certificate."""
    vid_id = "VID-NG-2026-STORETEST"
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    data = make_sample_cert(vid_id, expires_at)
    
    store.save_certificate(**data)
    
    loaded = store.get_certificate(vid_id)
    assert loaded is not None
    assert loaded["vid_id"] == vid_id
    assert loaded["score"] == 95
    assert loaded["revoked"] is False
    assert isinstance(loaded["revoked"], bool)

def test_store_on_conflict_updates():
    """Test ON CONFLICT path updates the existing row."""
    vid_id = "VID-NG-2026-CONFLICT"
    expires_at = datetime.now(timezone.utc) + timedelta(days=1)
    
    # First save
    data1 = make_sample_cert(vid_id, expires_at)
    data1["score"] = 50
    store.save_certificate(**data1)
    
    # Second save with same vid_id
    data2 = make_sample_cert(vid_id, expires_at + timedelta(days=10))
    data2["score"] = 99
    store.save_certificate(**data2)
    
    loaded = store.get_certificate(vid_id)
    assert loaded["score"] == 99

def test_revoke_and_validity():
    """Test revocation flag and is_valid logic."""
    vid_id = "VID-NG-2026-REVOKE"
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    data = make_sample_cert(vid_id, expires_at)
    store.save_certificate(**data)
    
    assert store.is_valid(vid_id) is True
    
    # Revoke
    store.revoke_certificate(vid_id)
    assert store.is_valid(vid_id) is False
    
    loaded = store.get_certificate(vid_id)
    assert loaded["revoked"] is True

def test_is_valid_false_for_unknown():
    assert store.is_valid("unknown-vid") is False

def test_is_valid_false_for_expired():
    vid_id = "VID-NG-2026-EXPIRED"
    expires_at = datetime.now(timezone.utc) - timedelta(days=1)
    data = make_sample_cert(vid_id, expires_at)
    store.save_certificate(**data)
    
    assert store.is_valid(vid_id) is False
