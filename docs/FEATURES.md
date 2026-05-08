# Feature Catalogue: VID (Virtual ID)

VID is packed with enterprise-grade features designed for the African market.

## 1. Unified Enrollment (Web + USSD)
- **Omni-Channel Flow**: Start on USSD, finish on Web, or vice versa. Your identity state is synchronized via your phone number hash.
- **Auto-Country Detection**: Real-time resolution of 54+ African countries from phone prefixes.
- **Multi-SIM Bonding**: Link up to 3 SIM cards to a single VID to boost your Trust Score and provide redundancy.

---

## 2. GSMA CAMARA Verification Suite
- **SIM Possession Check**: Real-time verification that the user actually owns the SIM they are enrolling with.
- **MNO KYC Match**: Direct verification of Name, Address, and Birthdate against operator records.
- **Network Geofencing**: Verifies the user's location via cell-tower triangulation (Location Verification API).
- **Fraud Signal Detection**: Automated check for recent SIM Swaps (7-day and 24-hour windows).

---

## 3. Machine Learning Trust Engine
- **Weighted Trust Scoring**: Dynamic calculation of an identity "Grade" (HIGH, MEDIUM, LOW) based on signal reliability.
- **Explainable Results**: Users see exactly why they received a specific score (e.g., "Location match failed but KYC passed").
- **Fallback Logic**: If a specific API is down, the engine uses weighted averages to maintain service availability.

---

## 4. Agentic Bonus Layer: Autonomous Revocation
- **Continuous Monitoring**: Background workers poll the network every 5 minutes for security triggers.
- **Auto-Lockdown**: Automatic revocation of VID if a SIM Swap or fraudulent location change is detected.
- **Audit Logging**: Comprehensive trail of autonomous decisions for system transparency.

---

## 5. Privacy & Security
- **Zero-PII Storage**: No names, raw phone numbers, or locations are ever saved in the VID database.
- **Ephemeral Certificates**: High-resolution digital certificates generated on-the-fly.
- **QR Code Verification**: Offline-compatible verification via encrypted QR codes.
- **Rate Limiting & CORS**: Production-hardened API protection.

---

## 6. Globalization & Accessibility
- **Multi-Language Support**:
  - **English** (Default)
  - **Hausa** (West Africa)
  - **Twi** (Ghana)
  - **Swahili** (East Africa)
  - **Zulu** (South Africa)
  - **Sesotho** (Lesotho/South Africa)
- **Feature Phone Optimized**: Text-only USSD interface for 2G/3G devices.

---

## 7. Developer & Partner Tools
- **Swagger Documentation**: Full interactive API reference at `/docs`.
- **Third-Party Verify Portal**: Dedicated page for banks/NGOs to verify VIDs without integration overhead.
- **Nokia NaC Sandbox Mode**: Easy testing with mock operators.
