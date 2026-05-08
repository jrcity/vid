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
        "welcome":   "Welcome to VID\nVirtual Identity\n\n1. English\n2. Hausa\n3. Twi\n4. Swahili\n5. Zulu\n6. Sesotho",
        "get_given": "Enter your First Name\n(e.g. Jane)\n\n0. Back",
        "get_family": "Enter your Last Name\n(e.g. Doe)\n\n0. Back",
        "get_address": "Enter your Address\n(City/Area)\n\n0. Back",
        "get_phone": "Verify current phone?\n{phone}\n\n1. Yes\n2. Enter other\n0. Back",
        "enter_other": "Enter phone number\nwith +country code\ne.g. +234...",
        "consent":   "VID will check your\nSIM card signals.\nNo personal data stored.\n\n1. I agree\n2. Cancel",
        "checking":  "Checking your identity...\nPlease wait.",
        "result_hi": "VID Score: {score}/100\nGrade: HIGH\nYour VID code:\n{vid_id}\n\nSave this code.\nDial again to check.",
        "result_md": "VID Score: {score}/100\nGrade: MODERATE\nYour VID code:\n{vid_id}\n\nSave this code.",
        "result_lo": "VID Score: {score}/100\nGrade: LOW\nMore SIM history\nneeded. Try again\nin 3 months.",
        "invalid":   "Invalid input.\nPlease try again.",
        "cancelled": "Cancelled.\nDial again anytime.",
        "error":     "Service error.\nPlease try again\nlater.",
    },
    "ha": {
        "welcome":   "Barka da zuwa VID\nShaidar Asali\n\n1. English\n2. Hausa\n3. Twi\n4. Swahili\n5. Zulu\n6. Sesotho",
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
        "welcome":   "Akwaaba ba VID\nVirtual Identity\n\n1. English\n2. Hausa\n3. Twi\n4. Swahili\n5. Zulu\n6. Sesotho",
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
        "welcome":   "Karibu VID\nVirtual Identity\n\n1. English\n2. Hausa\n3. Twi\n4. Swahili\n5. Zulu\n6. Sesotho",
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
        "welcome":   "Siyakwamukela VID\nVirtual Identity\n\n1. English\n2. Hausa\n3. Twi\n4. Swahili\n5. Zulu\n6. Sesotho",
        "get_phone": "Faka inombolo yakho\nyocingo\ne.g. +27821234567\n\n0. Buyela",
        "consent":   "VID izoqala ukuhlola\ni-SIM kadi yakho.\nAyikho idatha egciniwe.\n\n1. Ngiyavuma\n2. Khansela",
        "result_hi": "Akara VID: {score}/100\nIzinga: ELIPHEZULU\nI-VID yakho:\n{vid_id}\n\nGcina le nombolo.",
        "result_md": "Akara VID: {score}/100\nIzinga: ELIPHAKATHI\nI-VID yakho:\n{vid_id}",
        "result_lo": "Akara VID: {score}/100\nIzinga: ELIPHANSI\nUmlando we-SIM\noyidingayo.",
        "invalid":   "Inombolo engeyona.\nSebenzisa +27...",
        "cancelled": "Kukhanseliwe.\nZame futhi.",
        "error":     "Iphutha lensizakalo.\nZame futhi kamuva.",
    },
    "st": {
        "welcome":   "Rea u amohela ho VID\nVirtual Identity\n\n1. English\n2. Hausa\n3. Twi\n4. Swahili\n5. Zulu\n6. Sesotho",
        "get_given": "Kenya Lebitso la\nhau la pele\n\n0. Khutla",
        "get_family": "Kenya Fane ea hau\n\n0. Khutla",
        "get_address": "Kenya Aterese ea hau\n(City/Area)\n\n0. Khutla",
        "get_phone": "Netefatsa nomoro?\n{phone}\n\n1. Ee\n2. Kenya e 'ngoe\n0. Khutla",
        "enter_other": "Kenya nomoro ea\nmohala (+...)",
        "consent":   "VID e tla hlahloba\nSIM ea hau.\nHa ho datha e bolokoang.\n\n1. Kea lumela\n2. Khansela",
        "result_hi": "VID Score: {score}/100\nGrade: PHAHAMENG\nID ea hau ea VID:\n{vid_id}",
        "result_md": "VID Score: {score}/100\nGrade: MAHARENG\nID ea hau ea VID:\n{vid_id}",
        "result_lo": "VID Score: {score}/100\nGrade: TLASE\nNalane ea SIM e\nngata ea hlokahala.",
        "invalid":   "Phoso. Ka kopo\nlika hape.",
        "cancelled": "E hlakotsoe.\nLika hape nako efe.",
        "error":     "Phoso ea tšebeletso.\nLika hape hamorao.",
    },
}

LANG_MAP = {"1": "en", "2": "ha", "3": "tw", "4": "sw", "5": "zu", "6": "st"}


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
    
    # AFRICA'S TALKING TEXT FORMAT:
    # "" -> welcome
    # "1" -> get_given
    # "1*Jane" -> get_family
    # "1*Jane*Doe" -> get_address
    # "1*Jane*Doe*Lagos" -> get_phone
    # "1*Jane*Doe*Lagos*1" -> consent
    # "1*Jane*Doe*Lagos*1*1" -> enrollment
    # OR if "2" for other phone:
    # "1*Jane*Doe*Lagos*2*+234..." -> consent
    # "1*Jane*Doe*Lagos*2*+234...*1" -> enrollment

    step = len(inputs)

    # Get or create session
    if session_id not in _sessions:
        _sessions[session_id] = {
            "caller_phone": phone_number,
            "step": 0,
        }
    session = _sessions[session_id]

    # Stateless language derivation: always use inputs[0] if available
    if len(inputs) > 0:
        session["language"] = LANG_MAP.get(inputs[0], "en")
    else:
        session["language"] = "en"

    # ── Step 0: Language Selection ────────────────────────────────────────────
    if step == 0:
        return f"CON {_t(session, 'welcome')}"

    # ── Step 1: Process Language -> Get Given Name ────────────────────────────
    if step == 1:
        # Language already derived above
        return f"CON {_t(session, 'get_given')}"

    # ── Step 2: Process Given Name -> Get Family Name ─────────────────────────
    if step == 2:
        name = inputs[1]
        if name == "0": return f"CON {_t(session, 'welcome')}"
        session["given_name"] = name
        return f"CON {_t(session, 'get_family')}"

    # ── Step 3: Process Family Name -> Get Address ────────────────────────────
    if step == 3:
        name = inputs[2]
        if name == "0": return f"CON {_t(session, 'get_given')}"
        session["family_name"] = name
        return f"CON {_t(session, 'get_address')}"

    # ── Step 4: Process Address -> Get Phone Choice ───────────────────────────
    if step == 4:
        addr = inputs[3]
        if addr == "0": return f"CON {_t(session, 'get_family')}"
        session["address"] = addr
        return f"CON {_t(session, 'get_phone', phone=phone_number)}"

    # ── Step 5: Process Phone Choice ──────────────────────────────────────────
    if step == 5:
        choice = inputs[4]
        if choice == "0": return f"CON {_t(session, 'get_address')}"
        if choice == "1":
            session["phone"] = phone_number
            return f"CON {_t(session, 'consent')}"
        if choice == "2":
            return f"CON {_t(session, 'enter_other')}"
        return f"CON {_t(session, 'get_phone', phone=phone_number)}"

    # ── Step 6: Process Phone Input OR Consent ────────────────────────────────
    if step == 6:
        prev_choice = inputs[4]
        
        if prev_choice == "2":
            # User just entered a custom phone number
            entered_phone = inputs[5]
            if not _validate_phone(entered_phone):
                return f"CON {_t(session, 'invalid')}\n\n0. Try again"
            session["phone"] = entered_phone
            return f"CON {_t(session, 'consent')}"
        else:
            # User was at consent step (choice 1)
            consent_choice = inputs[5]
            if consent_choice == "2":
                del _sessions[session_id]
                return f"END {_t(session, 'cancelled')}"
            if consent_choice == "1":
                # PROCEED TO ENROLLMENT (Skip to the logic below)
                pass
            else:
                return f"CON {_t(session, 'consent')}"

    # ── Step 7: Handle Enrollment (if from custom phone) ──────────────────────
    if step == 7:
        consent_choice = inputs[6]
        if consent_choice == "2":
            del _sessions[session_id]
            return f"END {_t(session, 'cancelled')}"
        if consent_choice != "1":
            return f"CON {_t(session, 'consent')}"
        # PROCEED TO ENROLLMENT

    # ── ENROLLMENT LOGIC ──────────────────────────────────────────────────────
    phone = session.get("phone")
    if not phone:
        return f"END {_t(session, 'error')}"

    try:
        from app.services.camara_service import fetch_all_signals
        from app.services.trust_engine import (
            signals_to_results,
            compute_score,
            score_to_grade,
        )
        from app.services.certificate_service import (
            build_certificate,
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
                given_name=session.get("given_name", "USSD"),
                family_name=session.get("family_name", "User"),
                country_iso=iso,
                address=session.get("address", ""),
            )
            results = signals_to_results(signals)
            score = compute_score(results)
            grade = score_to_grade(score)

            # Generate certificate
            cert = build_certificate(
                phone_numbers=[phone],
                full_name=f"{session.get('given_name')} {session.get('family_name')}",
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
                explanation="Enrolled via USSD Gateway (Rural Access)",
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
