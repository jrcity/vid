# VID — Deployment Guide 🚀

This guide explains how to deploy the VID backend and frontend to a production environment and how to connect to the live Nokia Network-as-Code (NaC) infrastructure.

---

## 🏗️ Deployment Stack

| Component | Platform | Why? |
|---|---|---|
| **Backend API** | [Render](https://render.com) | Excellent Python support and native persistent disk options. |
| **Frontend** | [Vercel](https://vercel.com) | Industry standard for React/Next.js performance and edge delivery. |
| **Network Ops** | [Nokia NaC Portal](https://network.developer.nokia.com) | Central hub for CAMARA API credentials and monitoring. |

---

## 🔑 Environment Variables

Before deploying, ensure the following variables are set in your hosting platform:

### Backend (.env)
- `NOKIA_NAC_TOKEN`: Your API token from the Nokia developer portal.
- `NOKIA_NAC_TOKEN`: Leave blank for local mock mode; set a real token in production to use live network signals.
- `CORS_ORIGINS`: A comma-separated list of your frontend URLs (e.g., `https://vid.africa`).\
- `CERTIFICATE_STORE_PATH`: The location to store the generated certificate in the system.
- `VERIFY_BASE_URL`: Remote or Localhost verify endpoint.
- `RATE_LIMIT_DEFAULT`: Default timelimit for concurrent API calls.
- `RATE_LIMIT_ENROLL`: Limit to enrollment endpoint usage.
- `USE_MOCK_APIS`: A flag to switch to mock test data.
- `AFRICASTALKING_USERNAME`: User name for ussd gateway.
- `AFRICASTALKING_API_KEY`: API key for ussd gateway by Africastalking telcos.
- `APP_ENV`: Set to `production`.

### Frontend
- ` VITE_API_URL`: https://vid-backend-jca8.onrender.com/api/v1

---

## 🚀 Step-by-Step Deployment
### 1. Backend (Render)
1.  **Create a New Web Service**: Link your GitHub repository to [Render](https://dashboard.render.com).
2.  **Environment Setup**:
    - **Runtime**: `Python 3`
    - **Build Command**: `pip install -r requirements.txt`
    - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3.  **Advanced Configuration**:
    - Add a **Persistent Disk** (e.g., 1GB mounted at `/data`) if you want to persist the SQLite database across redeploys.
    - Set the environment variable `DATABASE_URL` or `CERTIFICATE_STORE_PATH` to point to the disk mount.

### 2. Nokia NaC Setup
1. Register at [Nokia Network-as-Code](https://networkascode.nokia.io/auth/sign-up?referral=/hub).
2. Create a new "Application."
3. Request access to the following APIs:
   - **SIM Swap**
   - **Number Verification**
   - **KYC Match**
   - **Location Verification**
   - **Device Status**
4. Copy your **API Token** and add it to your Render environment variables.

### 3. Scaling Strategy
As VID expands across the continent, we recommend:
- **Regional Clusters**: Deploying backend nodes in regions with low latency to local MNOs (e.g., West Africa, East Africa).
- **Edge Functions**: Moving identity verification logic to the edge for faster QR scanning and certificate delivery.

---

## 🛠️ Local Verification
To verify the deployment is working correctly:
1. Hit the health endpoint: `GET /api/v1/health`
2. Check for `"mock_mode": false` in the response.
3. Verify that the `countries` endpoint returns the full list of 54+ AU nations.

---
> *Scaling trust across the African digital landscape.*
