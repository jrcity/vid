# VID — Integration & Future Roadmap 🚀

This document outlines the critical steps needed to integrate the premium frontend with the finalized backend and the path toward production readiness.

## 🔗 Backend Integration Phase

Assuming the backend is ready with the previously stated improvements (Parallel APIs, Digital Signatures, etc.):

- [ ] **Environment Sync**: Point the frontend to the production API by updating `VITE_API_URL` in the deployment environment.
- [ ] **Mock Toggle**: In `src/hooks/useVidApi.ts`, ensure all hooks are calling the real endpoints instead of returning deterministic mock data.
- [ ] **Error Mapping**: Map specific CAMARA error codes (e.g., `403 Permission Denied` for SIM swap checks) to user-friendly UI toasts in `react-hot-toast`.
- [ ] **Signature Verification**: Implement client-side verification for the `certificate_hash` and digital signatures to ensure the card hasn't been tampered with.
- [ ] **Extended Meta Integration**: Update the `VerifyPage` to consume the proposed `country_iso` and `masked_phones` fields from the backend to show the country flag and corroborating SIM prefixes.

## 💎 Frontend Refinements

- [ ] **Offline Mode**: Implement a Service Worker to allow users to view their generated ID cards even when they have no internet connection.
- [ ] **Liveness Detection**: Integrate a lightweight facial liveness check (optional) during enrollment for higher trust scores.
- [ ] **PDF High-Fidelity Export**: Bridge the frontend with a server-side PDF generator to allow users to download a print-ready version of their VID.
- [ ] **Multi-Language Support**: Add translations for Swahili, French, Amharic, and Arabic to support all major African regions.

## 🏗️ Production Readiness

- [ ] **Performance Monitoring**: Integrate Sentry or LogRocket to track frontend errors and performance bottlenecks in real-world African network conditions.
- [ ] **A/B Testing**: Test different "Gold" vs "Silver" card variations to see which resonates more with users in different regions.
- [ ] **Security Audit**: Perform a full penetration test on the frontend to ensure no sensitive data is leaked through the DOM or console.

---
*The mission: Every African citizen with a secure, verified digital identity.*
