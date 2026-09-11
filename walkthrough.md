# Walkthrough: AmazonHelp AI Support Agent — 2-Minute Demo Script & Phase 2 UX Verification

## Overview

This document provides:
1. A concise **2-Minute Interactive Demo Script** for presenting the grounded AI support agent and Multi-Signal Trust Gate.
2. The **Verified Benchmark Results** across all 6 benchmark inquiries, explicitly highlighting **Case 3 (Return Size Exchange)** as an **intentional conservative abstention**.
3. Architectural details of the end-to-end pipeline and safety guardrails.

---

## 1. 2-Minute Interactive Demo Script

### Preparation
1. Ensure the FastAPI backend is running:
   ```powershell
   .\.venv\Scripts\uvicorn.exe api.main:app --host 127.0.0.1 --port 8000
   ```
2. Open `http://127.0.0.1:8000/` in a modern browser.
3. Note the top navigation bar: `🟢 Backend Online · Models Loaded` and dataset badge `twcs.csv`.

---

### Step 1 (0:00 – 0:30): System Overview & Verified Metrics
- **Narrative**:
  > *"Welcome to the AmazonHelp Grounded AI Support Agent. Standard LLM customer bots hallucinate fake policies and commit unauthorized refunds. Our system solves this with a two-pillar architecture: **FAISS Precedent Retrieval** from verified historical Amazon resolutions, guarded by a **Multi-Signal Trust Gate**.*
  >
  > *Look at our verified test-set metrics at the bottom left: On 1,800 unseen customer inquiries, the Trust Gate safely automates **16.44%** of traffic while achieving **90.88% Selective Accuracy** and a near-zero **0.22% Unsafe Auto-Handling Rate**."*

---

### Step 2 (0:30 – 1:00): Automated Self-Service Path (`AUTO-HANDLE`)
- **Action**: Click the first preset pill: **`📦 Where is my package?`**
  - Textarea fills: *"Where is my package? The tracking number says in transit but hasn't updated in 2 days."*
  - Click **Analyze with Trust Gate**.
- **Observation**:
  - Watch the pipeline stepper animate through **Intent & Risk → FAISS Retrieval → Grounded Reply → Trust Gate**.
  - Decision banner lights up in **Vibrant Emerald Green**: **`AUTO-HANDLE`** with reason code `CONFIDENT_GROUNDED`.
  - Intent classified as `ORDER_TRACKING_STATUS` with 75.7% confidence.
  - Review the **Top-3 Retrieved Precedents** from FAISS (e.g., `#conv_909056` at 82.1% match).
  - Review the grounded reply badge: `✓ Adapted from Precedent #conv_909056`.
- **Narrative**:
  > *"Notice how the decision is impossible to miss. Because this inquiry is routine shipping tracking, satisfies the confidence threshold, and closely matches verified historical cases, it is safely auto-handled."*

---

### Step 3 (1:00 – 1:30): Intentional Conservative Abstention (`ESCALATE: LOW_CONFIDENCE`)
- **Action**: Click the third preset pill: **`🔄 Return Size Exchange`**
  - Textarea fills: *"How do I return this sweater that is too small? Can I drop it off at an Amazon Locker?"*
  - Click **Analyze with Trust Gate**.
- **Observation**:
  - Decision banner turns **High-Visibility Coral/Red**: **`ESCALATE TO HUMAN`** with reason code `LOW_CONFIDENCE`.
  - Intent classification: `OTHER` (66.6% confidence < 75.0% threshold).
  - Precedent match: `#conv_262934` (59.8% match < 62.0% similarity threshold).
- **Narrative**:
  > *"Here is the most critical design pattern of our agent: **Intentional Conservative Abstention**. This customer asks a multi-clause question combining product return policy with specific drop-off channel logistics ('Amazon Locker').*
  >
  > *The classifier confidence is 66.6% and semantic precedent similarity is 59.8%—both falling just below our safety thresholds. Rather than guessing or inventing a potentially invalid locker drop-off instruction, the Trust Gate abstains and routes the customer safely to a human specialist."*

---

### Step 4 (1:30 – 2:00): Safety & Financial Guardrails (`ESCALATE: HIGH_RISK`)
- **Action**: Click either **`💳 Duplicate Charge ($75)`** or **`🚨 Stolen Card / Hacked ($500)`**.
- **Observation**:
  - For duplicate charge: Decision is **`ESCALATE TO HUMAN`** with reason code `PAYMENT_DISPUTE`.
  - For stolen card: Decision is **`ESCALATE TO HUMAN`** with reason code `HIGH_RISK`.
  - Audit trail highlights: `⚠ Financial dispute / high-risk security trigger detected`.
- **Narrative**:
  > *"Even if confidence were 100%, our hard risk filters intercept billing disputes and security compromises unconditionally. Autonomous bots should never promise money movement or handle stolen credentials without human authorization."*

---

## 2. Benchmark Case Matrix

| Benchmark Case | Customer Inquiry Summary | Decision | Reason Code | Intent & Confidence | Precedent Provenance | Policy Behavior & Rationale |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| **Empty Input** | `""` (Empty string) | — | — | Blocked submit | — | **Inline Validation**: `⚠️ Enter a customer message.` (no disruptive `alert()`). |
| **1. 📦 Tracking** | *"Where is my package? The tracking number says in transit..."* | **`AUTO-HANDLE`** (Green) | `CONFIDENT_GROUNDED` | `ORDER_TRACKING_STATUS` (75.7%) | Adapted from `#conv_909056` (82.1% match) | **Automated**: Standard low-risk shipping status with strong historical precedent. |
| **2. ⏳ Delay** | *"My order was supposed to arrive yesterday and is now delayed..."* | **`AUTO-HANDLE`** (Green) | `CONFIDENT_GROUNDED` | `DELIVERY_DELAY` (90.0%) | Adapted from `#conv_2283454` (83.3% match) | **Automated**: High-confidence delivery delay inquiry with proven carrier tracking guidance. |
| **3. 🔄 Return** | *"How do I return this sweater that is too small? Can I drop it off at an Amazon Locker?"* | **`ESCALATE TO HUMAN`** (Red) | `LOW_CONFIDENCE` | `OTHER` (66.6%) | Precedent `#conv_262934` (59.8% match) | **Intentional Conservative Abstention**: Multi-clause query with drop-off logistics falls below confidence threshold (66.6% < 75%) and precedent similarity (59.8% < 62%). Abstaining prevents ungrounded drop-off instructions. |
| **4. 💳 Dispute** | *"I see two separate $75 charges on my card for the same order!..."* | **`ESCALATE TO HUMAN`** (Red) | `PAYMENT_DISPUTE` | `PAYMENT_AND_BILLING_ISSUE` (71.2%) | Precedent `#conv_2142929` (65.2% match) | **Escalated (Financial)**: Strict financial dispute rule intercepts duplicate billing to prevent unauthorized automated refunds. |
| **5. 🚨 Fraud** | *"My credit card was stolen and someone placed a $500 order..."* | **`ESCALATE TO HUMAN`** (Red) | `HIGH_RISK` | `UNAUTHORIZED_TRANSACTION_FRAUD` (76.6%) | Precedent `#conv_2946739` (74.0% match) | **Escalated (Security)**: Critical account security violation flagged immediately by safety filters. |
| **6. ❓ Ambiguous**| *"Hey someone check this thing right now it looks weird."* | **`ESCALATE TO HUMAN`** (Red) | `LOW_CONFIDENCE` | `OTHER` (68.2%) | Precedent `#conv_18687` (47.0% match) | **Escalated (Ambiguity)**: Weak signal prevents speculative responses. |

---

## 3. Verified Reliability & Safety Metrics

All displayed figures reflect the full Multi-Signal Trust Gate evaluated on the $N=1,800$ unseen test split (`data/evaluation_results.json`):

- **Full Gate Automation Rate**: **16.44%** ($N=296$)
- **Selective Accuracy on Automated Cohort**: **90.88%** ($269 / 296$)
- **Unsafe Auto-Handling Rate**: **0.22%** ($4 / 1,800$)
- **Precedent Recall@5 (FAISS)**: **89.8%**
- **Test Suite Status**: **29 / 29 Passing** (`pytest tests/ -v`)
