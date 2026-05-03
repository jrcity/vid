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
    partial: bool = False       # Is the location verification result 'PARTIAL'?


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
    precise_location_verified: bool = False  # Track if user provided location
    biometric_passed: bool = False           # New: track face verification from frontend


# ── Nokia NaC Geofencing Centroids ───────────────────────────────────────────

# Full African Centroid Lookup (Lat, Lng, Default Country Radius in metres)
# Radius reflects country size to avoid false negatives at borders.
# Move to module scope to avoid re-initializing on every call.
CENTROIDS = {
    "DZ": (28.0339, 1.6596, 800000),
    "AO": (-11.2027, 17.8739, 600000),
    "BJ": (9.3077, 2.3158, 200000),
    "BW": (-22.3285, 24.6849, 400000),
    "BF": (12.2383, -1.5616, 300000),
    "BI": (-3.3731, 29.9189, 100000),
    "CV": (15.1204, -23.6053, 100000),
    "CM": (7.3697, 12.3547, 400000),
    "CF": (6.6111, 20.9394, 400000),
    "TD": (15.4542, 18.7322, 600000),
    "KM": (-11.6455, 43.3333, 50000),
    "CG": (-0.2280, 15.8277, 300000),
    "CD": (-4.0383, 21.7587, 800000),
    "DJ": (11.8251, 42.5903, 100000),
    "EG": (26.8206, 30.8025, 600000),
    "GQ": (1.6508, 10.2817, 100000),
    "ER": (15.1794, 39.7823, 200000),
    "SZ": (-26.5225, 31.4659, 100000),
    "ET": (9.1450, 40.4897, 600000),
    "GA": (-0.8037, 11.6094, 200000),
    "GM": (13.4432, -15.3101, 100000),
    "GH": (7.9465, -1.0232, 300000),
    "GN": (9.9456, -9.6966, 300000),
    "GW": (11.8037, -15.1804, 100000),
    "CI": (7.5400, -5.5471, 300000),
    "KE": (-0.0236, 37.9062, 400000),
    "LS": (-29.6100, 28.2336, 100000),
    "LR": (6.4281, -9.4295, 200000),
    "LY": (26.3351, 17.2283, 700000),
    "MG": (-18.7669, 46.8691, 500000),
    "MW": (-13.2543, 34.3015, 300000),
    "ML": (17.5707, -3.9962, 600000),
    "MR": (21.0079, -10.9408, 600000),
    "MU": (-20.3484, 57.5522, 50000),
    "MA": (31.7917, -7.0926, 400000),
    "MZ": (-18.6657, 35.5296, 500000),
    "NA": (-22.9576, 18.4904, 500000),
    "NE": (17.6078, 8.0817, 600000),
    "NG": (9.0820, 8.6753, 500000),
    "RW": (-1.9403, 29.8739, 100000),
    "ST": (0.1864, 6.6131, 50000),
    "SN": (14.4974, -14.4524, 300000),
    "SC": (-4.6796, 55.4920, 50000),
    "SL": (8.4606, -11.7799, 200000),
    "SO": (5.1521, 46.1996, 500000),
    "ZA": (-30.5595, 22.9375, 700000),
    "SS": (6.8770, 31.3070, 400000),
    "SD": (12.8628, 30.2176, 700000),
    "TZ": (-6.3690, 34.8888, 500000),
    "TG": (8.6195, 0.8248, 100000),
    "TN": (33.8869, 9.5375, 200000),
    "UG": (1.3733, 32.2903, 300000),
    "ZM": (-13.1339, 27.8493, 400000),
    "ZW": (-19.0154, 29.1549, 300000),
}


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
    settings = get_settings()
    try:
        import network_as_code as nac
        return nac.NetworkAsCodeClient(token=settings.nokia_nac_token)
    except Exception as e:
        raise RuntimeError(f"Nokia NaC SDK init failed: {e}")


def phone_to_simulator_id(phone: str) -> str:
    """
    Maps a phone number to a simulator identifier if USE_SIMULATOR is True.
    Simulator ID format: device-XXXXXX@testcsp.net (where XXXXXX is last 6 digits)
    """
    settings = get_settings()
    if not settings.use_simulator:
        return phone

    # Standard Nokia test numbers pass through
    if phone in ["+99999991000", "99999991000"]:
        return phone

    # Map real numbers to simulator IDs
    digits = "".join(filter(str.isdigit, phone))
    last6 = digits[-6:] if len(digits) >= 6 else digits.zfill(6)
    return f"device-{last6}@testcsp.net"


# ── Real CAMARA API calls ─────────────────────────────────────────────────────

async def call_sim_swap(phone: str) -> SimSwapSignal:
    """
    CAMARA SIM Swap API via Nokia NaC.
    Question asked: "Has this SIM been swapped in the last 90 days?"
    """
    try:
        client = _get_nac_client()
        device_id = phone_to_simulator_id(phone)
        device = client.devices.get(phone_number=device_id)
        # get_sim_swap_date() returns the last swap datetime or None
        swap_date = device.get_sim_swap_date()
        logger.info("SIM Swap API response for %s: %s", device_id, swap_date)
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
        device_id = phone_to_simulator_id(phone)
        device = client.devices.get(phone_number=device_id)
        # verify_number() returns True if number is registered and active
        result = device.verify_number(phone_number=device_id)
        logger.info("Number Verification API response for %s: %s", device_id, result)
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
        device_id = phone_to_simulator_id(phone)
        # kyc.match_customer() — pass the fields you want to verify
        match_result = client.kyc.match_customer(
            phone_number=device_id,
            given_name=name.split()[0] if name.split() else name,
            family_name=name.split()[-1] if len(name.split()) > 1 else "",
        )
        logger.info("KYC Match API response for %s: %s", device_id, match_result)
        # match_result is a CustomerMatchResult object
        # Using exact keys from SDK: given_name_match, family_name_match
        full_match = getattr(match_result, "given_name_match", False) and \
                     getattr(match_result, "family_name_match", False)
        partial = (getattr(match_result, "given_name_match", False) or \
                   getattr(match_result, "family_name_match", False)) and not full_match
        return KYCMatchSignal(name_match=full_match or partial, partial=partial)
    except Exception:
        logger.warning("KYC Match API error for %s", phone, exc_info=True)
        return KYCMatchSignal(name_match=False, partial=False)


async def call_location_verification(
    phone: str, 
    country_iso: str,
    user_lat: float | None = None,
    user_lng: float | None = None,
    user_radius: float | None = None
) -> LocationVerificationSignal:
    """
    CAMARA Location Verification API via Nokia NaC.
    Question asked: "Is this device currently in the declared area?"

    If user_lat/user_lng are provided, we verify precise location.
    Otherwise, we fallback to country-level geofencing.
    """
    try:
        client = _get_nac_client()
        device = client.devices.get(phone_number=phone)


        if user_lat is not None and user_lng is not None:
            # Precise verification requested by user
            lat, lng = user_lat, user_lng
            radius = user_radius if user_radius else 10000  # Default 10km for precise

            # Nokia API radius limit is typically 200km (200,000m) for high precision.
            # For user-specified, precise checks we cap the radius to 200km to match
            # most CAMARA implementations and avoid overly broad geofences.
            safe_radius = min(radius, 200000)
        else:
            # Fallback to country centroid
            lat, lng, radius = CENTROIDS.get(country_iso, (0, 20, 200000))

            # For coarse, country-level checks we allow larger radii so that
            # country-level geofences (including border areas) are not unintentionally
            # shrunk to 200km. We still apply a generous upper bound to avoid
            # obviously invalid values from configuration.
            # Constant used to cap fallback checks at 1000km
            COUNTRY_LEVEL_MAX_RADIUS = 1000000
            safe_radius = min(radius, COUNTRY_LEVEL_MAX_RADIUS)

        result = device.verify_location(
            latitude=lat,
            longitude=lng,
            radius=safe_radius,
            max_age=3600
        )
        logger.info("Location Verification API response for %s: %s", device_id, result)
        
        # Handle both bool (legacy/bare) and object (SDK) result shapes
        if isinstance(result, bool):
            status = result
        else:
            status = getattr(result, "verification_result", False)
            
        # Handle PARTIAL case
        is_in = (status is True or status == "PARTIAL")
        is_partial = (status == "PARTIAL")
        
        return LocationVerificationSignal(in_declared_region=is_in, partial=is_partial)
    except Exception:
        logger.warning("Location Verification API error for %s", phone, exc_info=True)
        return LocationVerificationSignal(in_declared_region=False, partial=False)


async def call_device_status(phone: str) -> DeviceStatusSignal:
    """
    CAMARA Device Status API via Nokia NaC.
    Question asked: "Is this device active and reachable on the network?"
    """
    try:
        client = _get_nac_client()
        device_id = phone_to_simulator_id(phone)
        device = client.devices.get(phone_number=device_id)
        # get_reachability() returns a ReachabilityStatus object
        reachability = device.get_reachability()
        logger.info("Device Status (Reachability) API response for %s: %s", device_id, reachability)
        
        # Valid status: CONNECTED_DATA, CONNECTED_SMS, NOT_CONNECTED
        status = str(getattr(reachability, "status", "")).upper()
        reachable = status in ["CONNECTED_DATA", "CONNECTED_SMS"]
        
        # get_roaming() returns a RoamingStatus object
        roaming = device.get_roaming()
        is_roaming = getattr(roaming, "roaming", False)
        return DeviceStatusSignal(reachable=reachable, new_device=is_roaming)
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
        biometric_passed=False, # Default mock value
    )


# ── Main entry point ──────────────────────────────────────────────────────────

async def fetch_all_signals(
    phone: str, 
    name: str, 
    country_iso: str,
    user_lat: float | None = None,
    user_lng: float | None = None,
    user_radius: float | None = None,
    biometric_passed: bool = False
) -> AllSignals:
    """
    Fetch all 5 CAMARA signals for a single phone number.
    Routes to real Nokia NaC APIs or mock based on settings.
    """
    settings = get_settings()
    if settings.use_mock_apis:
        logger.info("Using mock CAMARA signals for %s", phone)
        signals = _mock_signals(phone)
        signals.precise_location_verified = user_lat is not None
        signals.biometric_passed = biometric_passed
        return signals

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
        call_location_verification(phone, country_iso, user_lat, user_lng, user_radius),
        call_device_status(phone),
    )

    return AllSignals(
        sim_swap=sim_swap,
        number_verification=number_verification,
        kyc_match=kyc_match,
        location_verification=location,
        device_status=device_status,
        precise_location_verified=user_lat is not None,
        biometric_passed=biometric_passed
    )
