"""
app/services/ussd_service.py

VID USSD Gateway — Rural Access Layer.

Enables feature phone users (no smartphone required) to:
  - Enroll in VID by dialling a USSD shortcode
  - Check their VID trust score
  - Generate a shareable VID reference code

USSD Provider: Africa's Talking (africastalking.com)
  - Free sandbox available immediately at account.africastalking.com
  - Nigerian shortcode: *384*<appcode># (sandbox: *384*57911#)
  - USSD sessions are stateful — each step is tracked by session_id

HOW USSD WORKS:
  User dials *384*57911# on any phone (Nokia 3310 to iPhone)
  → Telecom sends POST request to our callback URL
  → We respond with text menu (max 182 chars per screen)
  → User presses a number to navigate
  → Session ends when we send "END" prefix

SESSION FLOW:
  Step 0: Welcome → ask for language
  Step 1: Ask for phone number
  Step 2: Ask for consent
  Step 3: Run CAMARA APIs → show trust score
  Step 4: Show VID reference code → END

INTEGRATION:
  1. Register at account.africastalking.com
  2. Create a USSD service → get your serviceCode
  3. Set callback URL to: https://vid-backend-jca8.onrender.com/api/v1/ussd
  4. Set AFRICASTALKING_USERNAME and AFRICASTALKING_API_KEY in .env

NIGERIA SHORTCODE:
  Request shortcode from NCC (Nigerian Communications Commission)
  For hackathon demo: use Africa's Talking sandbox shortcode *384*57911#
"""
import re
from app.services.trust_engine import (
    resolve_country_from_phone,
    score_to_grade,
)

# ── Session store (in-memory — replace with Redis for production) ─────────────
# session_id → { step, phone, language, consent }
_sessions: dict[str, dict] = {}

# ── Language strings ──────────────────────────────────────────────────────────
STRINGS = {
    "en": {
        "welcome":   "Welcome to VID\nVirtual Identity\n\n1. English\n2. Hausa\n3. Twi\n4. Swahili\n5. Zulu",
        "get_phone": "Enter your phone number\n(with country code)\ne.g. +2348031234567\n\n0. Back",
        "consent":   "VID will check your\nSIM card signals.\nNo personal data stored.\n\n1. I agree\n2. Cancel",
        "checking":  "Checking your identity...\nPlease wait.",
        "result_hi": "VID Score: {score}/100\nGrade: HIGH\nYour VID code:\n{vid_id}\n\nSave this code.\nDial again to check.",
        "result_md": "VID Score: {score}/100\nGrade: MODERATE\nYour VID code:\n{vid_id}\n\nSave this code.",
        "result_lo": "VID Score: {score}/100\nGrade: LOW\nMore SIM history\nneeded. Try again\nin 3 months.",
        "invalid":   "Invalid number.\nEnter with +country\ncode e.g. +234...",
        "cancelled": "Cancelled.\nDial again anytime.",
        "error":     "Service error.\nPlease try again\nlater.",
    },
    "ha": {
        "welcome":   "Barka da zuwa VID\nShaidar Asali\n\n1. Turanci (English)\n2. Hausa\n3. Twi (Ghana)\n4. Swahili (Tanzania)\n5. Zulu (South Africa)",
        "get_phone": "Shigar da lambar\nwaya taka\ne.g. +2348031234567\n\n0. Koma",
        "consent":   "VID zai duba\nkatin SIM dinka.\nBa a ajiye bayanan.\n\n1. Na yarda\n2. Soke",
        "result_hi": "Maki VID: {score}/100\nDaraja: BABBA\nKodin VID dinka:\n{vid_id}\n\nKiyaye wannan lamba.",
        "result_md": "Maki VID: {score}/100\nDaraja: MATSAKAICI\nKodin VID:\n{vid_id}",
        "result_lo": "Maki VID: {score}/100\nDaraja: KASA\nKuna bukatar tarihin\nSIM mai tsawo.",
        "invalid":   "Lambar wayar ba\nta dace ba. Shigar\nda +234...",
        "cancelled": "An soke. Kira\nkowane lokaci.",
        "error":     "Kuskure. Da fatan\na sake gwadawa.",
    },
    "tw": {
        "welcome":   "Akwaaba ba VID\nVirtual Identity\n\n1. English (UK)\n2. Hausa\n3. Twi (Ghana)\n4. Swahili (Tanzania)\n5. Zulu (South Africa)",
        "get_phone": "Fa w'ekyere nọmba\n(wɔ amanaman nọmba)\ne.g. +233241234567\n\n0. San kɔ",
        "consent":   "VID bɛhwɛ wo\nSIM card nsenia.\nYɛnhyɛ wo ho data.\n\n1. Megye tom\n2. Gyae",
        "result_hi": "VID Score: {score}/100\nGrade: KƐSE\nWo VID code:\n{vid_id}\n\nKura nọmba yi.",
        "result_md": "VID Score: {score}/100\nGrade: MFIMFINI\nWo VID code:\n{vid_id}",
        "result_lo": "VID Score: {score}/100\nGrade: KETIWA\nWo ho nsɛm\nnia yɛ hia.",
        "invalid":   "Nọmba no nyɛ pa.\nFa amanaman nọmba\ne.g. +233...",
        "cancelled": "Yɛagyae.\nFrɛ biom.",
        "error":     "Mfomso bi aba.\nSan bɔ mmɔden biom.",
    },
    "sw": {
        "welcome":   "Karibu VID\nVirtual Identity\n\n1. English (UK)\n2. Hausa\n3. Twi (Ghana)\n4. Swahili (Tanzania)\n5. Zulu (South Africa)",
        "get_phone": "Ingiza namba yako\nya simu\ne.g. +254712345678\n\n0. Rudi",
        "consent":   "VID itakagua hali\nya SIM kadi.\nHakuna data iliyohifadhiwa.\n\n1. Nakubali\n2. Ghairi",
        "result_hi": "VID Score: {score}/100\nGrade: JUU\nNamba yako ya VID:\n{vid_id}\n\nHifadhi namba hii.",
        "result_md": "VID Score: {score}/100\nGrade: KATI\nNamba yako ya VID:\n{vid_id}",
        "result_lo": "VID Score: {score}/100\nGrade: CHINI\nHistoria zaidi ya\nSIM inahitajika.",
        "invalid":   "Namba si sahihi.\nTumia +254...",
        "cancelled": "Imeghairiwa.\nPiga simu tena.",
        "error":     "Hitilafu ya huduma.\nJaribu tena.",
    },
    "zu": {
        "welcome":   "Siyakwamukela VID\nVirtual Identity\n\n1. English (UK)\n2. Hausa\n3. Twi (Ghana)\n4. Swahili (Tanzania)\n5. Zulu (South Africa)",
        "get_phone": "Faka inombolo yakho\nyocingo\ne.g. +27821234567\n\n0. Buyela",
        "consent":   "VID izoqala ukuhlola\ni-SIM kadi yakho.\nAyikho idatha egciniwe.\n\n1. Ngiyavuma\n2. Khansela",
        "result_hi": "Akara VID: {score}/100\nIzinga: ELIPHEZULU\nI-VID yakho:\n{vid_id}\n\nGcina le nombolo.",
        "result_md": "Akara VID: {score}/100\nIzinga: ELIPHAKATHI\nI-VID yakho:\n{vid_id}",
        "result_lo": "Akara VID: {score}/100\nIzinga: ELIPHANSI\nUmlando we-SIM\noyidingayo.",
        "invalid":   "Inombolo engeyona.\nSebenzisa +27...",
        "cancelled": "Kukhanseliwe.\nZame futhi.",
        "error":     "Iphutha lensizakalo.\nZame futhi kamuva.",
    },
}

LANG_MAP = {"1": "en", "2": "ha", "3": "tw", "4": "sw", "5": "zu"}


def _t(session: dict, key: str, **kwargs) -> str:
    """Get translated string for current session language."""
    lang = session.get("language", "en")
    strings = STRINGS.get(lang, STRINGS["en"])
    text = strings.get(key, STRINGS["en"].get(key, ""))
    return text.format(**kwargs) if kwargs else text


def _validate_phone(phone: str) -> bool:
    """Validate E.164 phone format."""
    return bool(re.match(r"^\+\d{7,15}$", phone.strip()))


# ── Main USSD handler ─────────────────────────────────────────────────────────

async def handle_ussd(
    session_id: str,
    phone_number: str,    # caller's number from Africa's Talking
    text: str,            # accumulated input e.g. "1*+2348031234567*1"
    service_code: str,
) -> str:
    """
    Main USSD request handler.

    Africa's Talking sends:
      sessionId:    unique session identifier
      phoneNumber:  caller's MSISDN
      text:         all inputs so far, separated by *
                    empty string on first request
      serviceCode:  e.g. *384*57911#

    Returns:
      "CON <text>"  → continue session (show menu, wait for input)
      "END <text>"  → end session (final message, no more input)
    """
    # Parse input history into steps
    inputs = [i.strip() for i in text.split("*")] if text else []
    step = len(inputs)

    # Get or create session
    if session_id not in _sessions:
        _sessions[session_id] = {
            "caller_phone": phone_number,
            "language": "en",
            "step": 0,
        }
    session = _sessions[session_id]

    # ── Step 0: Welcome + language selection ──────────────────────────────────
    if step == 0:
        return f"CON {_t(session, 'welcome')}"

    # ── Step 1: Language selected ──────────────────────────────────────────────
    if step == 1:
        lang_choice = inputs[0]
        session["language"] = LANG_MAP.get(lang_choice, "en")
        return f"CON {_t(session, 'get_phone')}"

    # ── Step 2: Phone number entered ───────────────────────────────────────────
    if step == 2:
        entered_phone = inputs[1]

        # Handle back
        if entered_phone == "0":
            return f"CON {_t(session, 'welcome')}"

        # Validate phone
        if not _validate_phone(entered_phone):
            # Prefill Nigeria code if user forgot
            if entered_phone.startswith("0") and len(entered_phone) == 11:
                entered_phone = "+234" + entered_phone[1:]
            elif not entered_phone.startswith("+"):
                entered_phone = "+" + entered_phone

            if not _validate_phone(entered_phone):
                return f"CON {_t(session, 'invalid')}\n\n0. Try again"

        # Resolve country
        iso, config = resolve_country_from_phone(entered_phone)
        if iso == "UNKNOWN" or not config:
            return f"CON {_t(session, 'invalid')}\n\n0. Try again"

        session["phone"] = entered_phone
        session["country"] = config["name"]
        session["vid_label"] = config["vid_label"]
        return f"CON {_t(session, 'consent')}"

    # ── Step 3: Consent ────────────────────────────────────────────────────────
    if step == 3:
        consent_choice = inputs[2]

        if consent_choice == "2":
            del _sessions[session_id]
            return f"END {_t(session, 'cancelled')}"

        if consent_choice != "1":
            return f"CON {_t(session, 'consent')}"

        session["consent"] = True
        phone = session.get("phone")

        if not phone:
            return f"END {_t(session, 'error')}"

        # ── Run CAMARA APIs + trust score ────────────────────────────────────
        try:
            from app.services.camara_service import fetch_all_signals
            from app.services.trust_engine import (
                signals_to_results,
                compute_score,
                compute_multi_sim_bonus,
            )
            from app.services.certificate_service import (
                build_certificate,
                generate_vid_id,
            )
            from app.services import store as cert_store
            from app.core.country_config import get_country

            iso, country_config = resolve_country_from_phone(phone)

            # Check if already enrolled
            existing = cert_store.get_by_phone(phone)
            if existing:
                vid_id = existing["vid_id"]
                score = existing["score"]
                grade = existing["trust_grade"]
            else:
                # New enrollment via USSD
                signals = await fetch_all_signals(
                    phone=phone,
                    given_name="USSD",
                    family_name="User",
                    country_iso=iso,
                )
                results = signals_to_results(signals)
                score = compute_score(results)
                grade = score_to_grade(score)

                # Generate certificate
                cert = build_certificate(
                    phone_numbers=[phone],
                    full_name="USSD User",
                    country_iso=iso,
                    country_config=country_config,
                    trust_score=type("T", (), {
                        "score": score, "grade": grade,
                        "signals": results, "explanation": "",
                        "multi_sim_bonus": 0
                    })(),
                )
                vid_id = cert.vid_id

                cert_store.save_certificate(
                    vid_id=vid_id,
                    certificate_hash=cert.certificate_hash,
                    iso_code=iso,
                    vid_label=country_config["vid_label"],
                    region=country_config["region"],
                    nationality=country_config["name"],
                    trust_grade=grade,
                    score=score,
                    issued_at=cert.issued_at,
                    expires_at=cert.expires_at,
                    phone_numbers=[phone],
                )

            # Return result based on grade
            if score >= 80:
                msg = _t(session, "result_hi", score=score, vid_id=vid_id)
            elif score >= 55:
                msg = _t(session, "result_md", score=score, vid_id=vid_id)
            else:
                msg = _t(session, "result_lo", score=score, vid_id=vid_id)

            del _sessions[session_id]
            return f"END {msg}"

        except Exception as e:
            print(f"[USSD] Error during enrollment: {e}")
            return f"END {_t(session, 'error')}"

    # ── Fallback ───────────────────────────────────────────────────────────────
    return f"END {_t(session, 'error')}"
