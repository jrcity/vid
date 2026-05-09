# VID (Virtual ID) — Sovereign Network Identity for Africa

[![Africa Ignite 2026](https://img.shields.io/badge/Africa_Ignite-Hackathon_2026-teal?style=for-the-badge)](https://africastalking.com)
[![Privacy First](https://img.shields.io/badge/Privacy-By_Design-blue?style=for-the-badge)](https://camaraproject.org)

**VID (Virtual ID)** is a decentralized, privacy-preserving identity system that leverages the **GSMA CAMARA APIs** (via Nokia Network-as-Code) and **Random Forest ML** to provide every African with a verifiable digital identity—no plastic cards required.

---

## 📺 Project Demo
[**Watch the Full System Walkthrough**](https://www.loom.com/share/5ca44c904da64be5aed2caa980068a2a?t=300)

---

## 🚀 The Problem
- **Identity Gap**: 500M+ Africans lack foundational ID.
- **Privacy Leakage**: Current KYC processes require sharing PII (Names/Phones) with third parties.
- **Fraud**: SIM swapping and identity theft are unchecked.
- **Exclusion**: Rural feature phone users are locked out of digital services.

## 💡 The Solution
VID transforms your **SIM card** into a trust anchor. By analyzing 5 core network signals, we calculate a **Trust Score** and generate a **Virtual ID** (e.g., Virtual NIN in Nigeria, Virtual Huduma in Kenya).

### Key Features:
- **Zero-PII Storage**: We store SHA-256 hashes, never your name or phone number.
- **Multi-SIM Bonding**: Trust scoring across multiple mobile networks.
- **Agentic Monitor**: Autonomous fraud detection and auto-revocation.
- **Universal Access**: Parity between premium Web App and USSD (`*384*57911#`).
- **Pan-African**: Native support for 54+ countries and 6 local languages (Hausa, Swahili, Zulu, etc.).

---

## 🛠️ Architecture
VID is built on a modern, high-performance stack:
- **Backend**: FastAPI (Python 3.11+)
- **Trust Engine**: Scikit-Learn (Random Forest Classifier)
- **Networking**: Nokia NaC SDK (CAMARA APIs)
- **Frontend**: React 18, TypeScript, Tailwind CSS
- **USSD**: Africa's Talking Gateway
- **Monitoring**: Autonomous Agentic Workers (Asyncio)

For a deep dive into the engineering, see [**docs/ARCHITECTURE.md**](docs/ARCHITECTURE.md).

---

## 📂 Documentation
- [**Case Study**](docs/CASE_STUDY.md) — Problem, Solution, and Impact.
- [**Feature Catalogue**](docs/FEATURES.md) — Detailed breakdown of all capabilities.
- [**User Guide**](docs/USER_GUIDE.md) — Step-by-step instructions with screenshots.
- [**Pitch Deck**](docs/PITCH_DECK.md) — Content for presentation slides.

---

## 🛠️ Installation & Setup

### Prerequisites:
- Python 3.11+
- Node.js 18+
- Nokia NaC API Credentials
- Africa's Talking API Key

### Backend Setup:
```bash
cd vid-backend
pip install -r requirements.txt
./run-backend.sh
```

### Frontend Setup:
```bash
cd frontend
pnpm install
pnpm dev
```

---

## 🌍 Africa Ignite Hackathon 2026
This project was developed for the **GSMA Africa Ignite Hackathon**, specifically targeting the **Nokia Network-as-Code** and **Africa's Talking** tracks.

**Team**: Gobe
**Submission Date**: May 9, 2026

---

## ⚖️ Privacy Guarantee
VID is like a **Yes/No Oracle**. When a bank verifies a user, they only receive a "Valid/Invalid" signal and a Trust Grade. No raw subscriber data is ever exchanged. We believe identity is a human right, and privacy is its shield.
