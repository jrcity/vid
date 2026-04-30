"""
app/core/country_config.py

Pan-African country configuration.
Maps ISO 3166-1 alpha-2 country codes to VID-specific metadata.

Each entry contains:
  - name:      Full country name
  - vid_label: What VID is called in this country (respects local ID language)
  - region:    African Union regional grouping
  - mnos:      Major Mobile Network Operators in that country
  - prefix:    E.164 country calling code (for display only — phonenumbers lib handles detection)
"""

COUNTRY_CONFIG: dict = {
    # ── West Africa ────────────────────────────────────────────────────────────
    "NG": {
        "name": "Nigeria",
        "vid_label": "Virtual NIN",
        "region": "West Africa",
        "mnos": ["MTN Nigeria", "Airtel Nigeria", "Glo", "9mobile"],
        "prefix": "+234",
    },
    "GH": {
        "name": "Ghana",
        "vid_label": "Virtual Ghana Card",
        "region": "West Africa",
        "mnos": ["MTN Ghana", "Vodafone Ghana", "AirtelTigo"],
        "prefix": "+233",
    },
    "SN": {
        "name": "Senegal",
        "vid_label": "Virtual CNIB",
        "region": "West Africa",
        "mnos": ["Orange Senegal", "Free Senegal", "Expresso"],
        "prefix": "+221",
    },
    "CI": {
        "name": "Côte d'Ivoire",
        "vid_label": "Virtual CNI",
        "region": "West Africa",
        "mnos": ["Orange CI", "MTN CI", "Moov Africa"],
        "prefix": "+225",
    },
    "ML": {
        "name": "Mali",
        "vid_label": "Virtual NINA",
        "region": "West Africa",
        "mnos": ["Orange Mali", "Malitel"],
        "prefix": "+223",
    },
    "BF": {
        "name": "Burkina Faso",
        "vid_label": "Virtual CNIB",
        "region": "West Africa",
        "mnos": ["Orange BF", "Onatel", "Telecel BF"],
        "prefix": "+226",
    },
    "NE": {
        "name": "Niger",
        "vid_label": "Virtual NIE",
        "region": "West Africa",
        "mnos": ["Airtel Niger", "Zamani Telecom", "Niger Telecom"],
        "prefix": "+227",
    },
    "GN": {
        "name": "Guinea",
        "vid_label": "Virtual NIF",
        "region": "West Africa",
        "mnos": ["Orange Guinea", "MTN Guinea", "Cellcom"],
        "prefix": "+224",
    },
    "BJ": {
        "name": "Benin",
        "vid_label": "Virtual CRIET ID",
        "region": "West Africa",
        "mnos": ["MTN Benin", "Moov Benin"],
        "prefix": "+229",
    },
    "TG": {
        "name": "Togo",
        "vid_label": "Virtual CNI",
        "region": "West Africa",
        "mnos": ["Togocom", "Moov Togo"],
        "prefix": "+228",
    },
    "SL": {
        "name": "Sierra Leone",
        "vid_label": "Virtual NID",
        "region": "West Africa",
        "mnos": ["Orange SL", "Africell", "Qcell"],
        "prefix": "+232",
    },
    "LR": {
        "name": "Liberia",
        "vid_label": "Virtual NID",
        "region": "West Africa",
        "mnos": ["Lonestar Cell", "Orange Liberia"],
        "prefix": "+231",
    },
    "GM": {
        "name": "Gambia",
        "vid_label": "Virtual NID",
        "region": "West Africa",
        "mnos": ["Africell Gambia", "QCell Gambia"],
        "prefix": "+220",
    },
    "GW": {
        "name": "Guinea-Bissau",
        "vid_label": "Virtual BI",
        "region": "West Africa",
        "mnos": ["MTN Guinea-Bissau", "Orange Guinea-Bissau"],
        "prefix": "+245",
    },
    "CV": {
        "name": "Cape Verde",
        "vid_label": "Virtual NIF",
        "region": "West Africa",
        "mnos": ["CVMóvel", "T+"],
        "prefix": "+238",
    },
    "MR": {
        "name": "Mauritania",
        "vid_label": "Virtual NNI",
        "region": "West Africa",
        "mnos": ["Mauritel", "Mattel", "Chinguitel"],
        "prefix": "+222",
    },

    # ── East Africa ────────────────────────────────────────────────────────────
    "KE": {
        "name": "Kenya",
        "vid_label": "Virtual Huduma Namba",
        "region": "East Africa",
        "mnos": ["Safaricom", "Airtel Kenya", "Telkom Kenya"],
        "prefix": "+254",
    },
    "ET": {
        "name": "Ethiopia",
        "vid_label": "Virtual Fayda ID",
        "region": "East Africa",
        "mnos": ["Ethio Telecom", "Safaricom Ethiopia"],
        "prefix": "+251",
    },
    "TZ": {
        "name": "Tanzania",
        "vid_label": "Virtual NIDA",
        "region": "East Africa",
        "mnos": ["Vodacom Tanzania", "Airtel Tanzania", "Tigo Tanzania"],
        "prefix": "+255",
    },
    "UG": {
        "name": "Uganda",
        "vid_label": "Virtual NIRA ID",
        "region": "East Africa",
        "mnos": ["MTN Uganda", "Airtel Uganda"],
        "prefix": "+256",
    },
    "RW": {
        "name": "Rwanda",
        "vid_label": "Virtual Irembo ID",
        "region": "East Africa",
        "mnos": ["MTN Rwanda", "Airtel Rwanda"],
        "prefix": "+250",
    },
    "SO": {
        "name": "Somalia",
        "vid_label": "Virtual NID",
        "region": "East Africa",
        "mnos": ["Hormuud Telecom", "Somtel", "Golis Telecom"],
        "prefix": "+252",
    },
    "ER": {
        "name": "Eritrea",
        "vid_label": "Virtual NID",
        "region": "East Africa",
        "mnos": ["EriTel"],
        "prefix": "+291",
    },
    "DJ": {
        "name": "Djibouti",
        "vid_label": "Virtual NID",
        "region": "East Africa",
        "mnos": ["Djibouti Telecom"],
        "prefix": "+253",
    },
    "SD": {
        "name": "Sudan",
        "vid_label": "Virtual NID",
        "region": "East Africa",
        "mnos": ["Zain Sudan", "MTN Sudan", "Sudani"],
        "prefix": "+249",
    },
    "SS": {
        "name": "South Sudan",
        "vid_label": "Virtual NID",
        "region": "East Africa",
        "mnos": ["MTN South Sudan", "Zain South Sudan"],
        "prefix": "+211",
    },

    # ── Central Africa ─────────────────────────────────────────────────────────
    "CD": {
        "name": "DR Congo",
        "vid_label": "Virtual CIN",
        "region": "Central Africa",
        "mnos": ["Vodacom DRC", "Airtel DRC", "Orange DRC"],
        "prefix": "+243",
    },
    "CM": {
        "name": "Cameroon",
        "vid_label": "Virtual CNI",
        "region": "Central Africa",
        "mnos": ["MTN Cameroon", "Orange Cameroon"],
        "prefix": "+237",
    },
    "CG": {
        "name": "Republic of Congo",
        "vid_label": "Virtual CNI",
        "region": "Central Africa",
        "mnos": ["Airtel Congo", "MTN Congo"],
        "prefix": "+242",
    },
    "CF": {
        "name": "Central African Republic",
        "vid_label": "Virtual CNI",
        "region": "Central Africa",
        "mnos": ["Orange CAR", "Moov CAR"],
        "prefix": "+236",
    },
    "GA": {
        "name": "Gabon",
        "vid_label": "Virtual CNI",
        "region": "Central Africa",
        "mnos": ["Airtel Gabon", "Moov Gabon"],
        "prefix": "+241",
    },
    "GQ": {
        "name": "Equatorial Guinea",
        "vid_label": "Virtual DNI",
        "region": "Central Africa",
        "mnos": ["GETESA", "HiTs EG"],
        "prefix": "+240",
    }, 
    "RW": {
        "name": "Rwanda",
        "vid_label": "Virtual Irembo ID",
        "region": "East Africa",
        "mnos": ["MTN Rwanda", "Airtel Rwanda"],
        "prefix": "+250",
    },
    "TD": {
        "name": "Chad",
        "vid_label": "Virtual CNI",
        "region": "Central Africa",
        "mnos": ["Airtel Chad", "Moov Chad"],
        "prefix": "+235",
    },
    "BI": {
        "name": "Burundi",
        "vid_label": "Virtual CNI",
        "region": "Central Africa",
        "mnos": ["Lumitel", "Econet Leo"],
        "prefix": "+257",
    },
    # ── Southern Africa ────────────────────────────────────────────────────────
    "ZA": {
        "name": "South Africa",
        "vid_label": "Virtual SA ID",
        "region": "Southern Africa",
        "mnos": ["Vodacom", "MTN SA", "Cell C", "Telkom Mobile"],
        "prefix": "+27",
    },
    "ZM": {
        "name": "Zambia",
        "vid_label": "Virtual NRC",
        "region": "Southern Africa",
        "mnos": ["MTN Zambia", "Airtel Zambia", "Zamtel"],
        "prefix": "+260",
    },
    "ZW": {
        "name": "Zimbabwe",
        "vid_label": "Virtual NID",
        "region": "Southern Africa",
        "mnos": ["Econet Zimbabwe", "NetOne", "Telecel"],
        "prefix": "+263",
    },
    "MZ": {
        "name": "Mozambique",
        "vid_label": "Virtual DIRE",
        "region": "Southern Africa",
        "mnos": ["Vodacom Mozambique", "Movitel", "Tmcel"],
        "prefix": "+258",
    },
    "BW": {
        "name": "Botswana",
        "vid_label": "Virtual Omang",
        "region": "Southern Africa",
        "mnos": ["Mascom", "Orange Botswana", "BTC Mobile"],
        "prefix": "+267",
    },
    "NA": {
        "name": "Namibia",
        "vid_label": "Virtual NID",
        "region": "Southern Africa",
        "mnos": ["MTC Namibia", "TN Mobile"],
        "prefix": "+264",
    },
    "LS": {
        "name": "Lesotho",
        "vid_label": "Virtual NID",
        "region": "Southern Africa",
        "mnos": ["Vodacom Lesotho", "Econet Telecom Lesotho"],
        "prefix": "+266",
    },
    "SZ": {
        "name": "Eswatini",
        "vid_label": "Virtual NID",
        "region": "Southern Africa",
        "mnos": ["MTN Eswatini", "Eswatini Mobile"],
        "prefix": "+268",
    },
    "MG": {
        "name": "Madagascar",
        "vid_label": "Virtual CIN",
        "region": "Southern Africa",
        "mnos": ["Airtel Madagascar", "Orange Madagascar", "Telma"],
        "prefix": "+261",
    },
    "MU": {
        "name": "Mauritius",
        "vid_label": "Virtual NIC",
        "region": "Southern Africa",
        "mnos": ["Orange Mauritius", "Emtel", "MTML"],
        "prefix": "+230",
    },
    "SC": {
        "name": "Seychelles",
        "vid_label": "Virtual NID",
        "region": "Southern Africa",
        "mnos": ["Airtel Seychelles", "Intelvision"],
        "prefix": "+248",
    },
    "KM": {
        "name": "Comoros",
        "vid_label": "Virtual CIN",
        "region": "Southern Africa",
        "mnos": ["Comores Telecom", "Telma Comoros"],
        "prefix": "+269",
    },

    # ── North Africa ───────────────────────────────────────────────────────────
    "EG": {
        "name": "Egypt",
        "vid_label": "Virtual NID",
        "region": "North Africa",
        "mnos": ["Vodafone Egypt", "Orange Egypt", "Etisalat Egypt"],
        "prefix": "+20",
    },
    "MA": {
        "name": "Morocco",
        "vid_label": "Virtual CNIE",
        "region": "North Africa",
        "mnos": ["Maroc Telecom", "Orange Morocco", "Inwi"],
        "prefix": "+212",
    },
    "DZ": {
        "name": "Algeria",
        "vid_label": "Virtual NID",
        "region": "North Africa",
        "mnos": ["Mobilis", "Djezzy", "Ooredoo Algeria"],
        "prefix": "+213",
    },
    "TN": {
        "name": "Tunisia",
        "vid_label": "Virtual CIN",
        "region": "North Africa",
        "mnos": ["Ooredoo Tunisia", "Orange Tunisia", "Tunisie Telecom"],
        "prefix": "+216",
    },
    "LY": {
        "name": "Libya",
        "vid_label": "Virtual NID",
        "region": "North Africa",
        "mnos": ["Libyana", "Al-Madar"],
        "prefix": "+218",
    },
    "AO": {
        "name": "Angola",
        "vid_label": "Virtual BI",
        "region": "Central Africa",
        "mnos": ["Unitel", "Movicel"],
        "prefix": "+244",
    },
    "ST": {
        "name": "São Tomé and Príncipe",
        "vid_label": "Virtual BI",
        "region": "Central Africa",
        "mnos": ["CST", "Unitel STP"],
        "prefix": "+239",
    },
}


def get_country(iso_code: str) -> dict | None:
    """Get country config by ISO 3166-1 alpha-2 code."""
    return COUNTRY_CONFIG.get(iso_code.upper())


def get_all_countries() -> list[dict]:
    """Return list of all countries for the frontend dropdown."""
    return [
        {
            "iso": iso,
            "name": cfg["name"],
            "vid_label": cfg["vid_label"],
            "region": cfg["region"],
            "prefix": cfg["prefix"],
        }
        for iso, cfg in COUNTRY_CONFIG.items()
    ]
