# VID — Compliance & Privacy 🛡️

Privacy is not an afterthought for VID; it is the core of our technical architecture. This document outlines our "Privacy by Design" principles and compliance with African data protection standards.

---

## 🔒 Zero-Knowledge Philosophy

Traditional ID verification often requires sending photos of physical documents or raw PII (Personally Identifiable Information) to third parties. **VID never does this.**

- **No Raw Data Leakage**: The VID backend never receives your IMSI, precise GPS coordinates, or call history. We only receive binary "signals" (Yes/No) from the network.
- **Certificate Masking**: On the public digital certificate, sensitive information like phone numbers are masked (e.g., `+234 8XX XXX 4567`).
- **Verifiable Hashes**: The unique VID ID is a hash of the verification event, ensuring no linkable identity is stored in plain text.

---

## 🤝 User Consent (Opt-in)

The system enforces a strict "Consent-First" policy. No network signals are requested until the user has explicitly opted-in via the enrollment interface.
- **Mandatory Consent**: Every API call to the mobile network is triggered by a user-signed consent event.
- **Transparency**: Users are shown exactly what signals will be checked before they hit "Enroll."
- **Revocability**: Users can stop the verification process at any time, and their session data is automatically purged.

---

## 🌍 Data Sovereignty

VID is designed to respect the sovereignty of African Union (AU) member states and their data protection laws (such as Nigeria's NDPR or South Africa's POPIA).
- **Network Locality**: By using Nokia's Network-as-Code, verification happens *inside* the operator's infrastructure. Data does not leave the country's sovereign network unnecessarily.
- **Minimal Retention**: VID stores only the minimum necessary data to allow third-party verification (VID ID, score, and timestamp). No permanent PII databases are maintained by the VID service.

---

## 📜 Compliance Standards

VID aims to align with:
1. **AU Convention on Cyber Security and Personal Data Protection** (Malabo Convention).
2. **GDPR/NDPR/POPIA** principles of data minimization and purpose limitation.
3. **W3C Verifiable Credentials**: Our roadmap includes full transition to the W3C VC standard for maximum interoperability.

---

### How to Verify a VID?
Third parties scan the QR code. They receive a **Yes/No/Confidence** result. They **never** receive the user's raw phone number or home address. This allows a bank to trust a user without ever "owning" their sensitive network data.

---
> *Empowering citizens, protecting data.*
