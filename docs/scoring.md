# VID — Scoring Methodology 📊

The **VID Trust Engine** translates complex mobile network signals into a single, human-readable confidence score. This document details the math and logic behind that score.

---

## ⚖️ Weighted Signals

The engine evaluates five primary signals via CAMARA APIs. Each signal is weighted based on its relevance to identity assurance and fraud prevention.

| Signal | Weight | Logic |
|---|---|---|
| **SIM Swap** | **35%** | Highest weight. A recent swap (within 90 days) is the strongest indicator of potential account takeover. |
| **Number Verify** | **20%** | Confirms the phone number is active and registered on a legitimate network. |
| **KYC Match** | **20%** | Corroborates the name provided during enrollment with the operator's subscriber records. |
| **Location Verify**| **15%** | Confirms the device is physically located in the declared country (e.g., Nigeria). |
| **Device Status** | **10%** | Checks if the device is reachable and if it's a "stable" handset (not recently changed). |

---

## ➕ Multi-SIM Consistency Bonus

A unique feature of VID is the **Multi-SIM Bonus**. In the African context, many users carry multiple SIMs (e.g., MTN for data, Airtel for calls).
- **1 SIM**: Base score only.
- **2 SIMs (Same Country)**: **+2 points** bonus.
- **3 SIMs (Same Country)**: **+5 points** bonus.

*Note: If SIMs are detected in different countries, no bonus is applied (often indicating a diaspora user or traveler), but no penalty is incurred.*

---

## 🏷️ Trust Grades

The final score (0–100) is mapped to three human-readable grades:

### 🟢 High Confidence (80–100)
- Identity is verified across multiple signals.
- No recent SIM swaps.
- Consistent KYC data.
- **Recommendation**: Accept for high-value transactions (banking, government).

### 🟡 Moderate Confidence (55–79)
- Most signals are positive.
- May have a recent device change or a partial KYC match.
- **Recommendation**: Accept for standard services; request secondary ID for high-risk actions.

### 🔴 Low Confidence (<55)
- Significant flags detected (e.g., recent SIM swap or location mismatch).
- Number could not be verified as active.
- **Recommendation**: Treat with caution; require physical verification or traditional ID.

---

## 🤖 AI Explanations

The Trust Engine generates natural language explanations to ensure the result is actionable by non-technical staff (e.g., clinic workers or bank tellers).

**Example Output:**
> "This identity has a high confidence rating of 94/100 in Nigeria. Confirmed signals: SIM Swap, Number Verification, KYC Match, Location Verification. Identity corroborated across 3 SIM cards in Nigeria (+5 points). This VID certificate can be accepted with high confidence."

---
> *Transparent trust for a digital continent.*
