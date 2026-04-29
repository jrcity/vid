# VID — Deployment Guide 🚀

This guide explains how to deploy the VID backend and frontend to a production environment and how to connect to the live Nokia Network-as-Code (NaC) infrastructure.

---

## 🏗️ Deployment Stack

| Component | Platform | Why? |
|---|---|---|
| **Backend API** | [Railway](https://railway.app) | Excellent Python support and easy environment variable management. |
| **Frontend** | [Vercel](https://vercel.com) | Industry standard for React/Next.js performance and edge delivery. |
| **Network Ops** | [Nokia NaC Portal](https://network.developer.nokia.com) | Central hub for CAMARA API credentials and monitoring. |

---

## 🔑 Environment Variables

Before deploying, ensure the following variables are set in your hosting platform:

### Backend (.env)
- `NOKIA_NAC_TOKEN`: Your API token from the Nokia developer portal.
- `USE_MOCK_APIS`: Set to `False` in production to use real network signals.
- `CORS_ORIGINS`: A comma-separated list of your frontend URLs (e.g., `https://vid.africa`).
- `APP_ENV`: Set to `production`.

### Frontend
- `NEXT_PUBLIC_API_URL`: The URL of your deployed Railway backend.

---

## 🚀 Step-by-Step Deployment

### 1. Backend (Railway)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and initialize
railway login
railway init

# Deploy
railway up
```

### 2. Nokia NaC Setup
1. Register at [Nokia Network-as-Code](https://network.developer.nokia.com).
2. Create a new "Application."
3. Request access to the following APIs:
   - **SIM Swap**
   - **Number Verification**
   - **KYC Match**
   - **Location Verification**
   - **Device Status**
4. Copy your **API Token** and add it to your Railway environment variables.

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
