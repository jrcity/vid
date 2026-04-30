"""
app/services/camara_service.py

Nokia Network-as-Code CAMARA API integration.

Architecture:
  - When NOKIA_NAC_TOKEN is set and valid → makes real API calls via NaC SDK
  - When token is missing or USE_MOCK=True → returns mock responses for development

All CAMARA APIs return yes/no boolean signals. No raw subscriber data
is ever received or stored by VID. This is the privacy-by-design core.

Nokia NaC SDK docs: https://network.developer.nokia.com/api-documentation/25_11
CAMARA API specs:   https://github.com/camaraproject
"""
import asyncio
import logging
import random
from dataclasses import dataclass
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


# ── Raw signal data from CAMARA APIs ─────────────────────────────────────────

@dataclass
class SimSwapSignal:
    swapped_recently: bool      # True = swapped in last 90 days (bad signal)
    days_since_swap: int        # 0 = never checked / unknown; >0 = days since last swap


@dataclass
class NumberVerificationSignal:
    active: bool                # Is this number live on the network?
    registered: bool            # Is it properly registered to a subscriber?


@dataclass
class KYCMatchSignal:
    name_match: bool            # Does subscriber profile name match across SIMs?
    partial: bool               # Partial match (e.g. first name only)


@dataclass
class LocationVerificationSignal:
    in_declared_region: bool    # Is device in the country it claims to be in?


@dataclass
class DeviceStatusSignal:
    reachable: bool             # Is device reachable on network right now?
    new_device: bool            # Was device recently changed (flag, not fail)?


@dataclass
class AllSignals:
    sim_swap: SimSwapSignal
    number_verification: NumberVerificationSignal
    kyc_match: KYCMatchSignal
    location_verification: LocationVerificationSignal
    device_status: DeviceStatusSignal


# ── Nokia NaC SDK client ──────────────────────────────────────────────────────

def _get_nac_client():
    """
    Returns an authenticated Nokia NaC client.
    
    Nokia NaC SDK usage:
        import network_as_code as nac
        client = nac.NetworkAsCodeClient(token=NOKIA_NAC_TOKEN)
        device = client.devices.get(phone_number="+2348031234567")
        sim_swap = device.get_sim_swap_date()
    
    Full SDK reference: https://network.developer.nokia.com/developer-docs/docs/python-sdk
    """
    try:
        import network_as_code as nac
        return nac.NetworkAsCodeClient(token=settings.nokia_nac_token)
    except Exception as e:
        raise RuntimeError(f"Nokia NaC SDK init failed: {e}")


# ── Real CAMARA API calls ─────────────────────────────────────────────────────

async def call_sim_swap(phone: str) -> SimSwapSignal:
    """
    CAMARA SIM Swap API via Nokia NaC.
    Question asked: "Has this SIM been swapped in the last 90 days?"
    """
    try:
        client = _get_nac_client()
        device = client.devices.get(
            phone_number=phone,
            # Nokia NaC requires network access token per device
            # The SDK handles OAuth2 CIBA flow automatically
        )
        # get_sim_swap_date() returns the last swap datetime or None
        swap_date = device.get_sim_swap_date()
        if swap_date is None:
            return SimSwapSignal(swapped_recently=False, days_since_swap=9999)
        from datetime import datetime, timezone
        days = (datetime.now(timezone.utc) - swap_date).days
        return SimSwapSignal(swapped_recently=days < 90, days_since_swap=days)
    except Exception:
        # On API failure, treat as unknown — do not penalise user for network errors
        logger.warning("SIM Swap API error for %s", phone, exc_info=True)
        return SimSwapSignal(swapped_recently=False, days_since_swap=0)


async def call_number_verification(phone: str) -> NumberVerificationSignal:
    """
    CAMARA Number Verification API via Nokia NaC.
    Question asked: "Is this number real and active?"
    """
    try:
        client = _get_nac_client()
        device = client.devices.get(phone_number=phone)
        # verify_number() returns True if number is registered and active
        result = device.verify_number(phone_number=phone)
        return NumberVerificationSignal(active=result, registered=result)
    except Exception:
        logger.warning("Number Verification API error for %s", phone, exc_info=True)
        return NumberVerificationSignal(active=False, registered=False)


async def call_kyc_match(phone: str, name: str) -> KYCMatchSignal:
    """
    CAMARA KYC Match API via Nokia NaC.
    Question asked: "Does the subscriber profile match the declared name?"

    Nokia NaC KYC Match checks name/DOB against MNO records.
    Returns a match score — VID treats ≥80% as full match, 50–79% as partial.
    """
    try:
        client = _get_nac_client()
        device = client.devices.get(phone_number=phone)
        # kyc_match() — pass the fields you want to verify
        match_result = device.kyc_match(
            given_name=name.split()[0] if name.split() else name,
            family_name=name.split()[-1] if len(name.split()) > 1 else "",
        )
        # match_result is a dict with per-field boolean matches
        name_fields = [
            match_result.get("given_name_match", False),
            match_result.get("family_name_match", False),
        ]
        full_match = all(name_fields)
        partial = any(name_fields) and not full_match
        return KYCMatchSignal(name_match=full_match or partial, partial=partial)
    except Exception:
        logger.warning("KYC Match API error for %s", phone, exc_info=True)
        return KYCMatchSignal(name_match=False, partial=False)


async def call_location_verification(phone: str, country_iso: str) -> LocationVerificationSignal:
    """
    CAMARA Location Verification API via Nokia NaC.
    Question asked: "Is this device currently in the declared country?"

    Uses country-level geofencing — we do not request precise GPS coordinates.
    """
    try:
        client = _get_nac_client()
        device = client.devices.get(phone_number=phone)
        # verify_location() — pass a bounding area (country-level polygon or lat/lng + radius)
        # For country-level, we pass a generous radius centred on the country's centroid
        # Country centroids are defined in a lookup (abbreviated here)
        CENTROIDS = {
            "NG": (9.082, 8.6753, 800000),    # lat, lng, radius_metres
            "KE": (-0.0236, 37.9062, 600000),
            "GH": (7.9465, -1.0232, 400000),
            "ZA": (-30.5595, 22.9375, 900000),
            "ET": (9.145, 40.4897, 900000),
            # Add all countries from country_config.py
        }
        lat, lng, radius = CENTROIDS.get(country_iso, (0, 20, 5000000))
        result = device.verify_location(
            latitude=lat,
            longitude=lng,
            radius=radius,
            max_age=3600  # Accept location data up to 1 hour old
        )
        return LocationVerificationSignal(in_declared_region=result)
    except Exception:
        logger.warning("Location Verification API error for %s", phone, exc_info=True)
        return LocationVerificationSignal(in_declared_region=False)


async def call_device_status(phone: str) -> DeviceStatusSignal:
    """
    CAMARA Device Status API via Nokia NaC.
    Question asked: "Is this device active and reachable on the network?"
    """
    try:
        client = _get_nac_client()
        device = client.devices.get(phone_number=phone)
        # get_connectivity() returns CONNECTED_DATA, CONNECTED_SMS, or NOT_CONNECTED
        connectivity = device.get_connectivity()
        reachable = connectivity in ["CONNECTED_DATA", "CONNECTED_SMS"]
        # get_roaming() — roaming on a new device MAY indicate SIM in new handset
        roaming = device.get_roaming()
        return DeviceStatusSignal(reachable=reachable, new_device=bool(roaming))
    except Exception:
        logger.warning("Device Status API error for %s", phone, exc_info=True)
        return DeviceStatusSignal(reachable=False, new_device=False)


# ── Mock API responses (for development without NaC credentials) ──────────────

def _mock_signals(phone: str, seed_offset: int = 0) -> AllSignals:
    """
    Deterministic mock responses based on phone number hash.
    Allows consistent testing: same phone always gets same mock result.
    Simulates a realistic distribution of signal outcomes.
    """
    seed = sum(ord(c) for c in phone) + seed_offset
    rng = random.Random(seed)

    # Simulate: 80% of users have stable SIMs
    swapped = rng.random() < 0.2
    days_since = rng.randint(0, 30) if swapped else rng.randint(180, 1800)

    # Simulate: 95% of submitted numbers are valid
    active = rng.random() < 0.95

    # Simulate: 85% full KYC match, 10% partial, 5% no match
    kyc_roll = rng.random()
    kyc_match = kyc_roll < 0.85
    kyc_partial = 0.85 <= kyc_roll < 0.95

    # Simulate: 88% in declared region
    in_region = rng.random() < 0.88

    # Simulate: 92% reachable, 20% of reachable are on new device
    reachable = rng.random() < 0.92
    new_device = reachable and rng.random() < 0.2

    return AllSignals(
        sim_swap=SimSwapSignal(swapped_recently=swapped, days_since_swap=days_since),
        number_verification=NumberVerificationSignal(active=active, registered=active),
        kyc_match=KYCMatchSignal(name_match=kyc_match, partial=kyc_partial),
        location_verification=LocationVerificationSignal(in_declared_region=in_region),
        device_status=DeviceStatusSignal(reachable=reachable, new_device=new_device),
    )


# ── Main entry point ──────────────────────────────────────────────────────────

async def fetch_all_signals(phone: str, name: str, country_iso: str) -> AllSignals:
    """
    Fetch all 5 CAMARA signals for a single phone number.
    Routes to real Nokia NaC APIs or mock based on settings.
    """
    if settings.use_mock_apis:
        logger.info("Using mock CAMARA signals for %s", phone)
        return _mock_signals(phone)

    (
        sim_swap,
        number_verification,
        kyc_match,
        location,
        device_status,
    ) = await asyncio.gather(
        call_sim_swap(phone),
        call_number_verification(phone),
        call_kyc_match(phone, name),
        call_location_verification(phone, country_iso),
        call_device_status(phone),
    )

    return AllSignals(
        sim_swap=sim_swap,
        number_verification=number_verification,
        kyc_match=kyc_match,
        location_verification=location,
        device_status=device_status,
    )
