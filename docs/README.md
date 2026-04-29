# VID Documentation

Central repository for all project-related documentation, architecture diagrams, and user guides.

[Back to Root](../README.md)
## VID — The Pan-African Identity Story 🌍

This document maps out the narrative journey of VID, from the continental problem to the technical solution and its ultimate impact. Use this as a guide for building out comprehensive documentation that "tells a story."

---

## 📖 Chapter 1: The Continental Challenge
**The Problem: "The Ghost in the Machine"**

Across Africa's 54 nations, identity is fragmented. While millions have mobile phones, millions lack official physical ID documents that work across borders. This "identity gap" prevents access to banking, healthcare, and digital services.
- **Fragmentation**: 54 different systems that don't talk to each other.
- **Trust Deficit**: How do you verify someone's identity in a digital-first world without compromising their privacy?
- **The Opportunity**: Mobile network penetration is near-universal. The network *knows* who you are, but that data is trapped in telecom silos.

---

## 🛠 Chapter 2: The VID Vision
**The Solution: "Your Network is Your Identity"**

VID (Virtual ID) bridges the gap by turning mobile network signals into a verifiable, Pan-African digital identity.
- **Mission**: To provide every African citizen with a high-assurance identity score that is private, secure, and universally recognized by AU member states.
- **The Pivot**: Move from "Show me your plastic card" to "Verify my network presence."

---

## ⚙️ Chapter 3: The Engine of Trust
**The Technology: "Decoding the Network"**

How does VID work? It leverages the **Nokia Network-as-Code (NaC)** platform to call **CAMARA APIs** directly into the mobile infrastructure.

### The 4-Layer Architecture
1. **Layer 1: The Face (Frontend)**
   - Minimalist, mobile-first enrollment.
   - Real-time feedback as signals are gathered.
2. **Layer 2: The Brain (Backend API)**
   - **Consent Manager**: Ensures the user is in control of their data.
   - **Orchestrator**: Parallelizes calls to multiple network APIs.
   - **AI Trust Engine**: The heart of the system.
3. **Layer 3: The Pulse (Nokia NaC)**
   - **SIM Swap**: Detects recent fraud attempts.
   - **Number Verify**: Confirms the number is active and real.
   - **KYC Match**: Corroborates profiles across multiple networks.
   - **Location Verify**: Ensures regional consistency.
   - **Device Status**: Validates the physical hardware continuity.
4. **Layer 4: The Result (Output)**
   - A **Pan-African Certificate** with a QR code.
   - **Zero-Knowledge Verification**: Third parties verify the score without seeing raw phone numbers or KYC data.

---

## 📊 Chapter 4: The Trust Score
**The Philosophy: "Probability over Binary"**

VID doesn't just say "Verified." It provides a **Trust Score (0–100)**.
- **Weighted Scoring**: SIM Swap (35%) is weighted higher because it's the strongest fraud signal.
- **Multi-SIM Bonus**: A unique innovation. If you have an MTN *and* an Airtel SIM and both match, your score goes up. This "cross-network corroboration" is the gold standard of digital identity.
- **Human-Readable Grades**: "High Confidence," "Moderate Confidence," or "Low Confidence."

---

## 🚀 Chapter 5: The Impact
**The Future: "One Continent, One Identity"**

- **Cross-Border Banking**: A Nigerian businessman opening a bank account in Kenya using his VID.
- **Emergency Healthcare**: A traveler in Ethiopia being verified at a clinic instantly.
- **Digital Inclusion**: Bringing the "unbanked" into the formal economy through their most trusted asset: their phone.

---

## 🗺 Documentation Roadmap
*Suggested structure for the `docs/` directory*

1. **[Introduction](./README.md)**: This narrative map.
2. **[Architecture Guide](./architecture.md)**: Deep dive into the 4-layer system and Nokia NaC integration.
3. **[API Reference](../vid-backend/README.md)**: Technical specs for the FastAPI service.
4. **[Scoring Methodology](./scoring.md)**: Detailed breakdown of the Trust Engine logic.
5. **[Compliance & Privacy](./privacy.md)**: How we handle AU data sovereignty and user consent.
6. **[Deployment Guide](./deployment.md)**: Scaling across the continent using Nokia's global footprint.
7. **[Project Roadmap](./ROADMAP.md)**: Milestones from prototype to continental launch.

---
> *Empowering African Digital Identity through Mobile Innovation.*
