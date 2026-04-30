# VID — Virtual ID · Backend API

Pan-African network identity system built with **FastAPI (Python)**.
Uses Nokia Network-as-Code CAMARA APIs to verify identity from mobile network signals.

## Stack

| Layer | Technology |
|---|---|
| API framework | FastAPI |
| Server | Uvicorn |
| Phone detection | `phonenumbers` library |
| QR generation | `qrcode` + `Pillow` |
| Nokia NaC | `network-as-code` SDK |
| Deployment | Railway (recommended) |

---

## Project structure

```
vid-backend/
├── app/
│   ├── main.py                  ← FastAPI app + CORS setup
│   ├── api/
│   │   └── routes.py            ← All endpoints
│   ├── core/
│   │   ├── config.py            ← Settings from .env
│   │   └── country_config.py    ← 54 AU nation config
│   ├── models/
│   │   └── schemas.py           ← Pydantic request/response models
│   └── services/
│       ├── camara_service.py    ← Nokia NaC API calls + mock fallback
│       ├── trust_engine.py      ← Scoring engine + phone resolver
│       ├── certificate_service.py ← VID cert + QR generation
│       └── store.py             ← SQLite certificate verification store
├── tests/
│   └── test_core.py             ← Unit tests
├── requirements.txt
└── .env.example
```

---

## Setup (local)

```bash
# 1. Clone and enter the backend folder
cd vid-backend

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # Mac/Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your NOKIA_NAC_TOKEN
# Leave it blank to run in mock mode (for development)

# 5. Run the server
uvicorn app.main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/health` | Health check + Nokia NaC status |
| GET | `/api/v1/countries` | List all 54+ supported countries |
| POST | `/api/v1/resolve-phone` | Detect country from phone number |
| POST | `/api/v1/enroll` | Main enrollment — calls all 5 CAMARA APIs |
| GET | `/api/v1/verify/{vid_id}` | Third-party QR verification |

---

## Enroll request example

```json
POST /api/v1/enroll
{
  "phone_numbers": [
    { "number": "+2348031234567", "is_primary": true },
    { "number": "+2341234567890", "is_primary": false }
  ],
  "full_name": "Aminu Bello",
  "consent": true
}
```

## Enroll response (abbreviated)

```json
{
  "success": true,
  "certificate": {
    "vid_id": "VID-NG-2026-8F4A2C91",
    "holder_name": "Aminu Bello",
    "masked_phones": ["+234 8XX XXX 4567"],
    "country": {
      "iso": "NG",
      "name": "Nigeria",
      "vid_label": "Virtual NIN",
      "region": "West Africa"
    },
    "trust_score": {
      "score": 94,
      "grade": "High confidence",
      "explanation": "Identity is high confidence...",
      "signals": [...]
    },
    "qr_data_url": "data:image/png;base64,...",
    "issued_at": "2026-04-29T...",
    "expires_at": "2027-04-29T..."
  }
}
```

---

## Mock mode

When `NOKIA_NAC_TOKEN` is not set, the API runs in **mock mode** — 
CAMARA API calls return realistic simulated responses based on the phone number.
Mock mode lets you build and test the full frontend flow before Nokia NaC credentials arrive.

Check mock status: `GET /api/v1/health` → `"mock_mode": true`

---

## Docker

From the repository root:

```bash
docker compose up --build
```

The API will be available at: http://localhost:8000

The compose setup stores verification records in a persistent Docker volume at
`/data/certificates.db` inside the backend container.

---

## Running tests

```bash
pytest tests/ -v
```

---

## Deploy to Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Set environment variables in Railway dashboard
# NOKIA_NAC_TOKEN=your_token
# APP_ENV=production
# CORS_ORIGINS=https://your-vercel-app.vercel.app
```

---

## Nokia NaC credentials

1. Go to: https://network.developer.nokia.com
2. Register as a developer
3. Create a new application
4. Copy the API token to your `.env` file as `NOKIA_NAC_TOKEN`

If the portal redirects to enterprise pages, email the hackathon organizers:
> "I am a shortlisted team in Africa Ignite 2026 and need sandbox API credentials 
>  for the Nokia Network-as-Code developer portal."
