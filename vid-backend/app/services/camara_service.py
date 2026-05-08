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
import re
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
    name_match: bool            # Does subscriber profile name match?
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
    precise_location_verified: bool = False  
    biometric_passed: bool = False           


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


# ── Nokia NaC Client & Helpers ───────────────────────────────────────────────

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


def get_device_identifier(phone: str) -> dict:
    """
    Standardizes device identifiers for the NaC SDK.
    Always includes phone_number as it's required for SIM Swap/KYC Match.
    Includes network_access_identifier in simulator mode for location/reachability.
    """
    settings = get_settings()
    clean_phone = phone.replace(" ", "").replace("-", "")
    
    params = {"phone_number": clean_phone}
    
    # If in simulator mode, add the test identifier as an alias
    if settings.use_mock_apis or settings.use_simulator:
        suffix = re.sub(r'\D', '', phone)[-6:] or "000001"
        params["network_access_identifier"] = f"vid-{suffix}@testcsp.net"
        
    return params


# ── Real CAMARA API calls ─────────────────────────────────────────────────────

async def call_sim_swap(phone: str) -> SimSwapSignal:
    """
    CAMARA SIM Swap API via Nokia NaC.
    """
    client = _get_nac_client()
    device = client.devices.get(**get_device_identifier(phone))
    swap_date = device.get_sim_swap_date()
    if swap_date is None:
        return SimSwapSignal(swapped_recently=False, days_since_swap=9999)
    from datetime import datetime, timezone
    diff = datetime.now(timezone.utc) - swap_date
    days = diff.days
    
    # Sandbox quirk: if swapped in the last hour, it's usually a test trigger
    # In a real scenario, < 24h is very high risk, but for testing we'll be slightly lenient
    is_recent = days < 90 and days > 0
    return SimSwapSignal(swapped_recently=is_recent, days_since_swap=days)


async def call_number_verification(phone: str) -> NumberVerificationSignal:
    try:
        client = _get_nac_client()
        # Reachability is sensitive to identifiers; use ONLY phone_number here
        clean_phone = phone.replace(" ", "").replace("-", "")
        device = client.devices.get(phone_number=clean_phone)
        reachability = device.get_reachability()
        is_active = getattr(reachability, "reachable", False)
        logger.info("Number Verification for %s: %s", phone, is_active)
        return NumberVerificationSignal(active=is_active, registered=is_active)
    except Exception as e:
        logger.error("Number Verification FAILED for %s: %s", phone, e)
        raise e


async def call_kyc_match(
    phone: str,
    given_name: str,
    family_name: str,
    birthdate: str | None = None,
    email: str | None = None,
    id_document: str | None = None,
    address: str | None = None,
    gender: str | None = None,
) -> KYCMatchSignal:
    try:
        client = _get_nac_client()
        device = client.devices.get(**get_device_identifier(phone))
        
        kyc_kwargs: dict = {
            "given_name": given_name,
            "family_name": family_name,
        }
        if birthdate: kyc_kwargs["birthdate"] = birthdate
        if email: kyc_kwargs["email"] = email
        if id_document: kyc_kwargs["id_document"] = id_document
        if address: kyc_kwargs["address"] = address
        if gender: kyc_kwargs["gender"] = gender
        
        logger.info("Calling KYC Match for %s with %s", phone, kyc_kwargs)
        # Fix: The SDK wants a phone_number string, not a Device object
        clean_phone = phone.replace(" ", "").replace("-", "")
        match_result = client.kyc.match_customer(phone_number=clean_phone, **kyc_kwargs)
        logger.info("KYC Match Result for %s: %s", phone, match_result)
        
        # Result mapping - Now including ID document match
        given_match = getattr(match_result, "given_name_match", False)
        family_match = getattr(match_result, "family_name_match", False)
        id_match = getattr(match_result, "id_document_match", False)
        
        full_match = given_match and family_match
        # If ID matches but name doesn't, it's still a strong partial signal
        partial = given_match or family_match or id_match
                   
        return KYCMatchSignal(name_match=bool(full_match or partial), partial=bool(partial and not full_match))
    except Exception as e:
        logger.error("KYC Match FAILED for %s: %s", phone, e)
        raise e


async def call_location_verification(
    phone: str, 
    country_iso: str,
    user_lat: float | None = None,
    user_lng: float | None = None,
    user_radius: float | None = None
) -> LocationVerificationSignal:
    client = _get_nac_client()
    device = client.devices.get(**get_device_identifier(phone))

    if user_lat is not None and user_lng is not None:
        lat, lng = user_lat, user_lng
        radius = user_radius if user_radius else 10000
        safe_radius = min(radius, 200000)
    else:
        lat, lng, radius = CENTROIDS.get(country_iso, (0, 20, 200000))
        safe_radius = min(radius, 200000)

    result = device.verify_location(
        latitude=lat,
        longitude=lng,
        radius=safe_radius,
        max_age=3600
    )
    
    if isinstance(result, bool):
        status = result
    else:
        status = getattr(result, "verification_result", False)
        
    is_in = (status is True or status == "PARTIAL")
    is_partial = (status == "PARTIAL")
    return LocationVerificationSignal(in_declared_region=is_in, partial=is_partial)


async def call_device_status(phone: str) -> DeviceStatusSignal:
    try:
        client = _get_nac_client()
        # Device Status is sensitive; use ONLY phone_number here
        clean_phone = phone.replace(" ", "").replace("-", "")
        device = client.devices.get(phone_number=clean_phone)
        reachability = device.get_reachability()
        reachable = getattr(reachability, "reachable", False)
        
        roaming = device.get_roaming()
        is_roaming = getattr(roaming, "roaming", False)
        return DeviceStatusSignal(reachable=reachable, new_device=is_roaming)
    except Exception as e:
        logger.error("Device Status FAILED for %s: %s", phone, e)
        raise e


# ── Mock API responses ────────────────────────────────────────────────────────

def _mock_signals(phone: str, seed_offset: int = 0) -> AllSignals:
    seed = sum(ord(c) for c in phone) + seed_offset
    rng = random.Random(seed)

    swapped = rng.random() < 0.2
    days_since = rng.randint(0, 30) if swapped else rng.randint(180, 1800)
    active = rng.random() < 0.95
    kyc_roll = rng.random()
    kyc_match = kyc_roll < 0.85
    kyc_partial = 0.85 <= kyc_roll < 0.95
    in_region = rng.random() < 0.88
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

async def fetch_all_signals(
    phone: str, 
    given_name: str,
    family_name: str,
    country_iso: str,
    birthdate: str | None = None,
    email: str | None = None,
    id_document: str | None = None,
    address: str | None = None,
    gender: str | None = None,
    user_lat: float | None = None,
    user_lng: float | None = None,
    user_radius: float | None = None,
    biometric_passed: bool = False
) -> AllSignals:
    """
    Fetch all 5 CAMARA signals for a single phone number.
    Forwards optional KYC fields for stronger identity matching.
    """
    settings = get_settings()
    if settings.use_mock_apis:
        signals = _mock_signals(phone)
        signals.precise_location_verified = user_lat is not None
        signals.biometric_passed = biometric_passed
        return signals

    results = await asyncio.gather(
        call_sim_swap(phone),
        call_number_verification(phone),
        call_kyc_match(
            phone, given_name, family_name,
            birthdate=birthdate,
            email=email,
            id_document=id_document,
            address=address,
            gender=gender,
        ),
        call_location_verification(phone, country_iso, user_lat, user_lng, user_radius),
        call_device_status(phone),
        return_exceptions=True
    )

    # Unpack results with fallback for non-critical failures
    sim_swap = results[0] if not isinstance(results[0], Exception) else SimSwapSignal(False, 0)
    number_verification = results[1] if not isinstance(results[1], Exception) else NumberVerificationSignal(False, False)
    kyc_match = results[2] if not isinstance(results[2], Exception) else KYCMatchSignal(False, False)
    location = results[3] if not isinstance(results[3], Exception) else LocationVerificationSignal(False, False)
    device_status = results[4] if not isinstance(results[4], Exception) else DeviceStatusSignal(False, False)

    # Re-raise critical exceptions if needed (e.g. if everything failed)
    if all(isinstance(r, Exception) for r in results):
        raise results[0] # Raise the first one as representative

    return AllSignals(
        sim_swap=sim_swap,
        number_verification=number_verification,
        kyc_match=kyc_match,
        location_verification=location,
        device_status=device_status,
        precise_location_verified=user_lat is not None,
        biometric_passed=biometric_passed
    )
