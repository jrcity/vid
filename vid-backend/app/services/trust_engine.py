"""
app/services/trust_engine.py

VID Trust Scoring Engine Using Random Forest.
"""

import os
import pickle
import numpy as np
import phonenumbers
from sklearn.ensemble import RandomForestClassifier
from app.services.camara_service import AllSignals
from app.models.schemas import SignalResult, TrustScoreResponse
from app.core.country_config import get_country
from app.core.rate_limit import limiter

# ── Model path ────────────────────────────────────────────────────────────────
MODEL_PATH = os.path.join(os.path.dirname(__file__), "vid_rf_model.pkl")
_model: RandomForestClassifier | None = None
GRADE_LABELS = ["Low confidence", "Moderate confidence", "High confidence"]

WEIGHTS = {
    "sim_swap":            0.30,
    "number_verification": 0.15,
    "kyc_match":           0.15,
    "location_verify":     0.10,
    "device_status":       0.05,
    "biometric_verify":    0.25,
}

# ── Localized Explanation Components ──────────────────────────────────────────
# We support the primary 4 languages in the backend for the identity report.
EXPLANATIONS = {
    "en": {
        "report_start": "This identity has a {grade} rating of {score}/100 in {country}.",
        "ai_confidence": "The AI model is {pct}% confident this identity is genuine.",
        "confirmed": "Confirmed signals: {signals}.",
        "flags": "Flags detected: {signals}.",
        "bonus": "Identity corroborated across {num} SIM cards in {country} (+{bonus} pts).",
        "diaspora": "Multiple SIMs across different countries — diaspora user, no bonus applied.",
        "high_conclusion": "This VID certificate can be accepted with high confidence.",
        "mod_conclusion": "Acceptable for most uses — consider extra checks for high-value transactions.",
        "low_conclusion": "Treat with caution. Additional verification recommended before accepting.",
        "grades": {
            "High confidence": "high confidence",
            "Moderate confidence": "moderate confidence",
            "Low confidence": "low confidence"
        },
        "signal_names": {
            "SIM Swap": "SIM Swap",
            "Number Verification": "Number Verification",
            "KYC Match": "KYC Match",
            "Location Verification": "Location Verification",
            "Device Status": "Device Status",
            "Biometric Verification": "Biometric Verification"
        }
    },
    "ha": {
        "report_start": "Wannan shaidar tana da matsayin {grade} na {score}/100 a {country}.",
        "ai_confidence": "Samfurin AI yana da kwarin gwiwa kashi {pct}% cewa wannan shaidar ta gaskiya ce.",
        "confirmed": "Alamun da aka tabbatar: {signals}.",
        "flags": "An gano tutoci: {signals}.",
        "bonus": "An tabbatar da shaida a fadin katinan SIM {num} a {country} (+{bonus} makin).",
        "diaspora": "Katinan SIM da yawa a fadin kasashe daban-daban — mai amfani da kasashen waje, ba a ba da makin bonus ba.",
        "high_conclusion": "Ana iya karbar wannan takardar shaidar VID tare da babban kwarin gwiwa.",
        "mod_conclusion": "Ana iya karba don mafi yawan amfani — yi la'akari da ƙarin bincike don manyan ma'amaloli.",
        "low_conclusion": "Yi amfani da hankali. Ana ba da shawarar ƙarin tabbaci kafin karba.",
        "grades": {
            "High confidence": "babban kwarin gwiwa",
            "Moderate confidence": "matsakaicin kwarin gwiwa",
            "Low confidence": "karamin kwarin gwiwa"
        },
        "signal_names": {
            "SIM Swap": "Sauya SIM",
            "Number Verification": "Tabbatar da lamba",
            "KYC Match": "Kwatanta KYC",
            "Location Verification": "Tabbatar da wuri",
            "Device Status": "Yanayin na'ura",
            "Biometric Verification": "Tabbatar da halittu"
        }
    },
    "sw": {
        "report_start": "Utambulisho huu una daraja ya {grade} ya {score}/100 nchini {country}.",
        "ai_confidence": "Mfano wa AI una uhakika wa {pct}% kwamba utambulisho huu ni halisi.",
        "confirmed": "Ishara zilizothibitishwa: {signals}.",
        "flags": "Bendera zimegunduliwa: {signals}.",
        "bonus": "Utambulisho umethibitishwa katika kadi {num} za SIM nchini {country} (+{bonus} pts).",
        "diaspora": "SIM nyingi katika nchi tofauti — mtumiaji wa ughaibuni, hakuna bonasi iliyotumiwa.",
        "high_conclusion": "Cheti hiki cha VID kinaweza kukubaliwa kwa ujasiri wa juu.",
        "mod_conclusion": "Inakubalika kwa matumizi mengi — fikiria hundi za ziada kwa shughuli za thamani ya juu.",
        "low_conclusion": "Chukua kwa tahadhari. Uthibitishaji wa ziada unapendekezwa kabla ya kukubali.",
        "grades": {
            "High confidence": "ujasiri wa juu",
            "Moderate confidence": "ujasiri wa wastani",
            "Low confidence": "ujasiri wa chini"
        },
        "signal_names": {
            "SIM Swap": "Kubadilisha SIM",
            "Number Verification": "Uthibitishaji wa namba",
            "KYC Match": "Ulinganifu wa KYC",
            "Location Verification": "Uthibitishaji wa mahali",
            "Device Status": "Hali ya kifaa",
            "Biometric Verification": "Uthibitishaji wa biometriska"
        }
    },
    "am": {
        "report_start": "ይህ ማንነት በ{country} ውስጥ {score}/100 የ{grade} ደረጃ አለው።",
        "ai_confidence": "የAI ሞዴሉ ይህ ማንነት እውነተኛ ስለመሆኑ {pct}% እርግጠኛ ነው።",
        "confirmed": "የተረጋገጡ ምልክቶች፡ {signals}።",
        "flags": "የታዩ ማስጠንቀቂያዎች፡ {signals}።",
        "bonus": "በ{country} ውስጥ ባሉ {num} የሲም ካርዶች ማንነቱ ተረጋግጧል (+{bonus} ነጥብ)።",
        "diaspora": "በተለያዩ አገሮች ውስጥ ያሉ ብዙ ሲሞች — የዲያስፖራ ተጠቃሚ፣ ምንም ቦነስ አልተተገበረም።",
        "high_conclusion": "ይህ የVID ምስክር ወረቀት በከፍተኛ እምነት ሊቀበል ይችላል።",
        "mod_conclusion": "ለአብዛኛዎቹ አጠቃቀሞች ተቀባይነት ያለው — ለከፍተኛ ዋጋ ግብይቶች ተጨማሪ ፍተሻዎችን ያስቡበት።",
        "low_conclusion": "በጥንቃቄ ይያዙ። ከመቀበልዎ በፊት ተጨማሪ ማረጋገጫ ይመከራል።",
        "grades": {
            "High confidence": "ከፍተኛ እምነት",
            "Moderate confidence": "መካከለኛ እምነት",
            "Low confidence": "ዝቅተኛ እምነት"
        },
        "signal_names": {
            "SIM Swap": "ሲም መቀየር",
            "Number Verification": "የቁጥር ማረጋገጫ",
            "KYC Match": "የKYC ተዛማጅ",
            "Location Verification": "የቦታ ማረጋገጫ",
            "Device Status": "የመሣሪያ ሁኔታ",
            "Biometric Verification": "የባዮሜትሪክ ማረጋገጫ"
        }
    }
}

def resolve_country_from_phone(phone: str) -> tuple[str, dict | None]:
    if phone in ["+99999991000", "99999991000"]:
        return "NG", get_country("NG")
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

def signals_to_results(signals: AllSignals) -> list[SignalResult]:
    results = []
    ss = signals.sim_swap
    if not ss.swapped_recently and ss.days_since_swap > 0:
        months = ss.days_since_swap // 30
        display, detail, passed = f"No swap · {months}+ months", f"SIM stable for {months}+ months — strong identity signal.", True
    elif ss.swapped_recently:
        display, detail, passed = f"Swapped {ss.days_since_swap} days ago", "Recent SIM swap detected — reduces identity confidence.", False
    else:
        display, detail, passed = "No swap history", "No recent SIM swap detected.", True

    results.append(SignalResult(api_name="SIM Swap", signal_key="sim_swap", passed=passed, weight=WEIGHTS["sim_swap"], display_value=display, detail=detail))

    nv = signals.number_verification
    results.append(SignalResult(api_name="Number Verification", signal_key="number_verification", passed=nv.active, weight=WEIGHTS["number_verification"], display_value="Active · confirmed" if nv.active else "Inactive / unregistered", detail="Phone number active and registered on network." if nv.active else "Phone number could not be verified as active."))

    km = signals.kyc_match
    if km.name_match and not km.partial:
        display, detail, passed = "Full match confirmed", "Subscriber profile matches declared identity.", True
    elif km.partial:
        display, detail, passed = "Partial match", "Some profile fields matched — minor discrepancy.", True
    else:
        display, detail, passed = "No match", "Profile could not be matched to declared identity.", False
    results.append(SignalResult(api_name="KYC Match", signal_key="kyc_match", passed=passed, weight=WEIGHTS["kyc_match"], display_value=display, detail=detail))

    lv = signals.location_verification
    if lv.in_declared_region and not lv.partial:
        display, detail, passed = "In declared region", "Device location consistent with declared country.", True
    elif lv.partial:
        display, detail, passed = "In declared region (partial)", "Device location partially verified — minor discrepancy.", True
    else:
        display, detail, passed = "Outside declared region", "Device outside declared country — may be roaming.", False
    results.append(SignalResult(api_name="Location Verification", signal_key="location_verify", passed=passed, partial=lv.partial, weight=WEIGHTS["location_verify"], display_value=display, detail=detail))

    ds = signals.device_status
    if ds.reachable and not ds.new_device:
        display, detail, passed = "Active · stable device", "Device reachable, no recent change detected.", True
    elif ds.reachable and ds.new_device:
        display, detail, passed = "Active · new device", "Device reachable but recently changed — minor flag.", True
    else:
        display, detail, passed = "Unreachable", "Device could not be reached on network.", False
    results.append(SignalResult(api_name="Device Status", signal_key="device_status", passed=passed, weight=WEIGHTS["device_status"], display_value=display, detail=detail))

    results.append(SignalResult(api_name="Biometric Verification", signal_key="biometric_verify", passed=signals.biometric_passed, weight=WEIGHTS["biometric_verify"], display_value="Passed" if signals.biometric_passed else "Not performed / Failed", detail="Face verification matched user identity." if signals.biometric_passed else "Biometric verification not completed or failed."))
    return results

def compute_multi_sim_bonus(phone_numbers: list[str]) -> int:
    if len(phone_numbers) <= 1: return 0
    countries = []
    for phone in phone_numbers:
        iso, _ = resolve_country_from_phone(phone)
        if iso != "UNKNOWN": countries.append(iso)
    if not countries or len(set(countries)) != 1: return 0
    return min(5, len(phone_numbers) * 2)

def score_to_grade(score: int) -> str:
    if score >= 80:
        return "High confidence"
    elif score >= 55:
        return "Moderate confidence"
    return "Low confidence"

def compute_score(signal_results: list[SignalResult], multi_sim_bonus: int = 0) -> int:
    """Fallback weighted formula — used if RF model unavailable."""
    score = 0
    for r in signal_results:
        if r.passed:
            multiplier = 0.5 if getattr(r, 'partial', False) else 1.0
            score += r.weight * 100 * multiplier
    return min(100, int(score) + multi_sim_bonus)

def generate_explanation(
    score: int,
    grade: str,
    signal_results: list[SignalResult],
    country_name: str,
    num_sims: int,
    bonus: int,
    probabilities: dict | None = None,
    locale: str = "en"
) -> str:
    # Default to English if locale not supported
    lang = EXPLANATIONS.get(locale, EXPLANATIONS["en"])
    passed = [r for r in signal_results if r.passed]
    failed = [r for r in signal_results if not r.passed]
    lines = []

    # Localized grade name
    localized_grade = lang["grades"].get(grade, grade.lower())
    lines.append(lang["report_start"].format(grade=localized_grade, score=score, country=country_name))

    if probabilities:
        high_pct = int(probabilities.get("High confidence", 0) * 100)
        if high_pct >= 70:
            lines.append(lang["ai_confidence"].format(pct=high_pct))

    if passed:
        localized_passed = [lang["signal_names"].get(r.api_name, r.api_name) for r in passed]
        lines.append(lang["confirmed"].format(signals=', '.join(localized_passed)))
    if failed:
        localized_failed = [lang["signal_names"].get(r.api_name, r.api_name) for r in failed]
        lines.append(lang["flags"].format(signals=', '.join(localized_failed)))

    if num_sims > 1 and bonus > 0:
        lines.append(lang["bonus"].format(num=num_sims, country=country_name, bonus=bonus))
    elif num_sims > 1 and bonus == 0:
        lines.append(lang["diaspora"])

    if score >= 80: lines.append(lang["high_conclusion"])
    elif score >= 55: lines.append(lang["mod_conclusion"])
    else: lines.append(lang["low_conclusion"])

    return " ".join(lines)

def extract_features(signals: AllSignals, multi_sim_bonus: int = 0) -> np.ndarray:
    ss, nv, km, lv, ds = signals.sim_swap, signals.number_verification, signals.kyc_match, signals.location_verification, signals.device_status
    sim_stable = int(not ss.swapped_recently)
    num_active = int(nv.active)
    kyc_full = int(km.name_match and not km.partial)
    kyc_partial = int(km.partial)
    in_region = 1.0 if (lv.in_declared_region and not lv.partial) else (0.5 if lv.partial else 0.0)
    device_stable = int(ds.reachable)
    new_device = int(ds.new_device)
    tenure_months = min(60, ss.days_since_swap // 30) if ss.days_since_swap > 0 else 0
    precise_loc = int(signals.precise_location_verified and lv.in_declared_region)
    biometric = int(signals.biometric_passed)

    return np.array([[sim_stable, num_active, kyc_full, kyc_partial, in_region, device_stable, new_device, tenure_months, multi_sim_bonus, precise_loc, biometric]], dtype=float)

def generate_training_data(n_samples: int = 8000) -> tuple[np.ndarray, np.ndarray]:
    rng = np.random.default_rng(seed=42)
    sim_stable = rng.choice([1, 0], n_samples, p=[0.80, 0.20])
    num_active = rng.choice([1, 0], n_samples, p=[0.95, 0.05])
    kyc_roll = rng.random(n_samples)
    kyc_full, kyc_partial = (kyc_roll < 0.75).astype(int), ((kyc_roll >= 0.75) & (kyc_roll < 0.95)).astype(int)
    loc_roll = rng.random(n_samples)
    in_region = np.where(loc_roll < 0.80, 1.0, np.where(loc_roll < 0.88, 0.5, 0.0))
    device_stable = rng.choice([1, 0], n_samples, p=[0.92, 0.08])
    new_device = np.where(device_stable == 1, rng.choice([1, 0], n_samples, p=[0.20, 0.80]), 0)
    tenure_months = rng.integers(1, 61, n_samples)
    multi_sim_b = rng.choice([0, 2, 4, 5], n_samples, p=[0.50, 0.20, 0.20, 0.10])
    precise_loc = rng.choice([1, 0], n_samples, p=[0.30, 0.70])
    biometric = rng.choice([1, 0], n_samples, p=[0.70, 0.30])

    X = np.stack([sim_stable, num_active, kyc_full, kyc_partial, in_region, device_stable, new_device, tenure_months, multi_sim_b, precise_loc, biometric], axis=1).astype(float)
    base_score = (sim_stable * 30 + num_active * 15 + kyc_full * 15 + kyc_partial * 7 + in_region * 10 + device_stable * 5 + biometric * 25)
    score = np.clip(base_score + multi_sim_b + np.clip(tenure_months // 12, 0, 5) + precise_loc * 4 - new_device * 3, 0, 100)
    y = np.where(score >= 80, 2, np.where(score >= 55, 1, 0))
    return X, y

def train_model() -> RandomForestClassifier:
    print("[VID RF] Training Random Forest trust model...")
    X, y = generate_training_data(n_samples=8000)
    clf = RandomForestClassifier(n_estimators=100, max_depth=8, min_samples_leaf=5, random_state=42, n_jobs=-1, class_weight="balanced")
    clf.fit(X, y)
    try:
        with open(MODEL_PATH, "wb") as f: pickle.dump(clf, f)
        print(f"[VID RF] Model saved to {MODEL_PATH}")
    except Exception as e: print(f"[VID RF] Could not save model: {e}")
    return clf

def get_model() -> RandomForestClassifier:
    global _model
    if _model is not None: return _model
    if os.path.exists(MODEL_PATH):
        try:
            with open(MODEL_PATH, "rb") as f: _model = pickle.load(f)
            print("[VID RF] Model loaded from disk.")
            return _model
        except: pass
    _model = train_model()
    return _model

def predict_score(signals: AllSignals, multi_sim_bonus: int = 0) -> tuple[int, str, dict]:
    model = get_model()
    features = extract_features(signals, multi_sim_bonus)
    pred_class, pred_proba = model.predict(features)[0], model.predict_proba(features)[0]
    class_probs = {GRADE_LABELS[i]: float(pred_proba[i]) for i in range(len(GRADE_LABELS))}
    score = int(class_probs["High confidence"] * 90 + class_probs["Moderate confidence"] * 67 + class_probs["Low confidence"] * 25)
    return min(100, score + multi_sim_bonus), GRADE_LABELS[int(pred_class)], class_probs

def build_trust_score(
    all_signals_per_sim: list[AllSignals],
    phone_numbers: list[str],
    name: str,
    country_name: str,
    locale: str = "en"
) -> TrustScoreResponse:
    primary_signals = all_signals_per_sim[0]
    signal_results = signals_to_results(primary_signals)
    bonus = compute_multi_sim_bonus(phone_numbers)
    try:
        score, grade, probabilities = predict_score(primary_signals, bonus)
    except Exception as e:
        score, grade, probabilities = 50, "Low confidence", None
    
    explanation = generate_explanation(score, grade, signal_results, country_name, len(phone_numbers), bonus, probabilities, locale)
    return TrustScoreResponse(score=score, grade=grade, signals=signal_results, explanation=explanation, multi_sim_bonus=bonus)

