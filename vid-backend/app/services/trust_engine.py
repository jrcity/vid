"""
app/services/trust_engine.py

VID Trust Scoring Engine.

Takes raw CAMARA signals for one or more SIM cards,
applies weighted scoring + multi-SIM consistency bonus,
and produces a 0–100 trust score with full signal breakdown.

Scoring weights (must sum to 1.0):
  SIM Swap              35%  — strongest fraud signal
  Number Verification   20%  — is the number real?
  KYC Match             20%  — profile consistency
  Location Verification 15%  — regional stability
  Device Status         10%  — device continuity

Multi-SIM bonus: +1 to +5 points if all declared SIMs
are in the same country and have consistent profiles.
"""
import phonenumbers
from app.services.camara_service import AllSignals
from app.models.schemas import SignalResult, TrustScoreResponse
from app.core.country_config import get_country


# ── Weights ───────────────────────────────────────────────────────────────────

WEIGHTS = {
    "sim_swap":            0.35,
    "number_verification": 0.20,
    "kyc_match":           0.20,
    "location_verify":     0.15,
    "device_status":       0.10,
}


# ── Phone resolver ────────────────────────────────────────────────────────────

def resolve_country_from_phone(phone: str) -> tuple[str, dict | None]:
    """
    Detect country ISO code from an E.164 phone number.
    Returns (iso_code, country_config_dict).

    Handles cross-continental numbers e.g.:
      +2348031234567  → NG (Nigeria)
      +254712345678   → KE (Kenya)
      +27831234567    → ZA (South Africa)
    """
    try:
        parsed = phonenumbers.parse(phone)
        if not phonenumbers.is_valid_number(parsed):
            return "UNKNOWN", None
        iso = phonenumbers.region_code_for_number(parsed)
        config = get_country(iso)
        return iso, config
    except phonenumbers.phonenumberutil.NumberParseException:
        return "UNKNOWN", None


def mask_phone(phone: str) -> str:
    """
    Mask a phone number for display on the certificate.
    +2348031234567 → +234 8XX XXX 4567
    Only shows country code + first digit + last 4 digits.
    """
    try:
        parsed = phonenumbers.parse(phone)
        national = str(parsed.national_number)
        country_code = str(parsed.country_code)
        if len(national) >= 6:
            masked = national[0] + "X" * (len(national) - 5) + national[-4:]
        else:
            masked = "X" * len(national)
        return f"+{country_code} {masked}"
    except Exception:
        return "+" + "X" * (len(phone) - 1)


# ── Signal conversion ─────────────────────────────────────────────────────────

def signals_to_results(signals: AllSignals) -> list[SignalResult]:
    """
    Convert raw CAMARA signal dataclasses into scored SignalResult objects.
    Each result has a passed bool, weight, and display strings.
    """
    results = []

    # ── SIM Swap ──────────────────────────────────────────────────────────────
    ss = signals.sim_swap
    if not ss.swapped_recently and ss.days_since_swap > 0:
        months = ss.days_since_swap // 30
        display = f"No swap · {months}+ months"
        detail = f"SIM has been stable for over {months} months — strong identity signal."
    elif ss.swapped_recently:
        display = f"Swapped {ss.days_since_swap} days ago"
        detail = "Recent SIM swap detected — this reduces identity confidence."
    else:
        display = "No swap history"
        detail = "No recent SIM swap detected."

    results.append(SignalResult(
        api_name="SIM Swap",
        signal_key="sim_swap",
        passed=not ss.swapped_recently,
        weight=WEIGHTS["sim_swap"],
        display_value=display,
        detail=detail,
    ))

    # ── Number Verification ───────────────────────────────────────────────────
    nv = signals.number_verification
    results.append(SignalResult(
        api_name="Number Verification",
        signal_key="number_verification",
        passed=nv.active,
        weight=WEIGHTS["number_verification"],
        display_value="Active · confirmed" if nv.active else "Inactive / unregistered",
        detail=(
            "Phone number is active and registered on the network."
            if nv.active
            else "Phone number could not be verified as active on any network."
        ),
    ))

    # ── KYC Match ─────────────────────────────────────────────────────────────
    km = signals.kyc_match
    if km.name_match and not km.partial:
        display = "Full match confirmed"
        detail = "Subscriber profile matches declared identity across all checked fields."
        passed = True
    elif km.partial:
        display = "Partial match"
        detail = "Some profile fields matched — minor discrepancy detected."
        passed = True  # partial is a warn, not a fail
    else:
        display = "No match"
        detail = "Subscriber profile could not be matched to the declared identity."
        passed = False

    results.append(SignalResult(
        api_name="KYC Match",
        signal_key="kyc_match",
        passed=passed,
        weight=WEIGHTS["kyc_match"],
        display_value=display,
        detail=detail,
    ))

    # ── Location Verification ─────────────────────────────────────────────────
    lv = signals.location_verification
    results.append(SignalResult(
        api_name="Location Verification",
        signal_key="location_verify",
        passed=lv.in_declared_region,
        weight=WEIGHTS["location_verify"],
        display_value="In declared region" if lv.in_declared_region else "Outside declared region",
        detail=(
            "Device location is consistent with the declared country."
            if lv.in_declared_region
            else "Device appears to be outside the declared country — may be roaming or travelling."
        ),
    ))

    # ── Device Status ─────────────────────────────────────────────────────────
    ds = signals.device_status
    if ds.reachable and not ds.new_device:
        display = "Active · stable device"
        detail = "Device is reachable and appears to be a long-term device — no change detected."
        passed = True
    elif ds.reachable and ds.new_device:
        display = "Active · new device"
        detail = "Device is reachable but a recent device change was detected. Minor flag — not a disqualifier."
        passed = True  # warn, not fail
    else:
        display = "Unreachable"
        detail = "Device could not be reached on the network at this time."
        passed = False

    results.append(SignalResult(
        api_name="Device Status",
        signal_key="device_status",
        passed=ds.reachable,
        weight=WEIGHTS["device_status"],
        display_value=display,
        detail=detail,
    ))

    return results


# ── Multi-SIM consistency ─────────────────────────────────────────────────────

def compute_multi_sim_bonus(phone_numbers: list[str]) -> int:
    """
    Award 0–5 bonus points for multi-SIM cross-network corroboration.

    Logic:
      - 1 SIM:  no bonus
      - 2 SIMs, same country: +4
      - 3 SIMs, same country: +5
      - SIMs across different countries: +0 (diaspora user — not a flag, just no bonus)
    """
    if len(phone_numbers) <= 1:
        return 0

    countries = []
    for phone in phone_numbers:
        iso, _ = resolve_country_from_phone(phone)
        if iso != "UNKNOWN":
            countries.append(iso)

    if not countries:
        return 0

    all_same_country = len(set(countries)) == 1
    if not all_same_country:
        return 0  # cross-country — diaspora, no bonus but no penalty

    return min(5, len(phone_numbers) * 2)


# ── Score computation ─────────────────────────────────────────────────────────

def compute_score(signal_results: list[SignalResult], multi_sim_bonus: int = 0) -> int:
    """
    Weighted average of signal results → 0–100 score.
    Each passed signal contributes its full weight × 100.
    Bonus capped to keep total ≤ 100.
    """
    base = sum(
        r.weight * (100 if r.passed else 0)
        for r in signal_results
    )
    return min(100, int(base) + multi_sim_bonus)


def score_to_grade(score: int) -> str:
    if score >= 80:
        return "High confidence"
    elif score >= 55:
        return "Moderate confidence"
    else:
        return "Low confidence"


# ── AI explanation generator ──────────────────────────────────────────────────

def generate_explanation(
    score: int,
    grade: str,
    signal_results: list[SignalResult],
    country_name: str,
    num_sims: int,
    bonus: int,
) -> str:
    """
    Generate a plain-language explanation of the trust result.
    Designed to be readable by clinic staff, bank officers, and NGO workers
    — not just technical users.
    """
    passed = [r for r in signal_results if r.passed]
    failed = [r for r in signal_results if not r.passed]

    lines = []

    # Opening sentence
    if score >= 80:
        lines.append(f"This identity has a high confidence rating of {score}/100 in {country_name}.")
    elif score >= 55:
        lines.append(f"This identity has a moderate confidence rating of {score}/100 in {country_name}.")
    else:
        lines.append(f"This identity has a low confidence rating of {score}/100 in {country_name}.")

    # Passed signals summary
    if passed:
        passed_names = ", ".join(r.api_name for r in passed)
        lines.append(f"Confirmed signals: {passed_names}.")

    # Failed signals
    if failed:
        failed_names = ", ".join(r.api_name for r in failed)
        lines.append(f"Flags detected: {failed_names}.")

    # Multi-SIM note
    if num_sims > 1 and bonus > 0:
        lines.append(
            f"Identity corroborated across {num_sims} SIM cards "
            f"in {country_name} (+{bonus} points)."
        )
    elif num_sims > 1 and bonus == 0:
        lines.append(
            f"Multiple SIMs declared across different countries "
            f"(likely diaspora user — no bonus applied, no penalty)."
        )

    # Recommendation
    if score >= 80:
        lines.append("This VID certificate can be accepted with high confidence.")
    elif score >= 55:
        lines.append(
            "This VID certificate is acceptable for most uses — "
            "consider requesting supporting documents for high-value transactions."
        )
    else:
        lines.append(
            "This VID certificate should be treated with caution. "
            "Additional verification is recommended before accepting."
        )

    return " ".join(lines)


# ── Main entry point ──────────────────────────────────────────────────────────

def build_trust_score(
    all_signals_per_sim: list[AllSignals],
    phone_numbers: list[str],
    name: str,
    country_name: str,
) -> TrustScoreResponse:
    """
    Build the full trust score from signals for all enrolled SIMs.
    Uses the primary SIM (index 0) signals for the main score,
    then applies multi-SIM bonus.
    """
    # Use primary SIM for base scoring
    primary_signals = all_signals_per_sim[0]
    signal_results = signals_to_results(primary_signals)

    # Multi-SIM bonus
    bonus = compute_multi_sim_bonus(phone_numbers)

    # Score
    score = compute_score(signal_results, bonus)
    grade = score_to_grade(score)

    # Explanation
    explanation = generate_explanation(
        score=score,
        grade=grade,
        signal_results=signal_results,
        country_name=country_name,
        num_sims=len(phone_numbers),
        bonus=bonus,
    )

    return TrustScoreResponse(
        score=score,
        grade=grade,
        signals=signal_results,
        explanation=explanation,
        multi_sim_bonus=bonus,
    )
