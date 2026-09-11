# Walkthrough: AmazonHelp AI Support Agent — 2-Minute Demo Script & Phase 2 UX Verification

## Overview

This document provides:
1. A concise **2-Minute Interactive Demo Script** for presenting the customer-first AI support assistant and Multi-Signal Trust Gate.
2. The **Verified Benchmark Results** across all 6 benchmark inquiries, explicitly highlighting **Case 3 (Return Size Exchange)** as an **intentional conservative abstention**.
3. Architectural details of the customer view and expandable Evaluator Details view.

---

## 1. 2-Minute Interactive Demo Script

### Preparation
1. Ensure the FastAPI backend is running:
   ```powershell
   .\.venv\Scripts\uvicorn.exe api.main:app --host 127.0.0.1 --port 8000
   ```
2. Open `http://127.0.0.1:8000/` in a modern browser.
3. Note the top navigation bar: `AmazonHelp Customer Support`, the `⚙️ Evaluator Details` toggle button, and status `🟢 Service Online`.

---

### Step 1 (0:00 – 0:30): System Overview & Verified Metrics
- **Narrative**:
  > *"Welcome to the AmazonHelp Grounded AI Support Assistant. Traditional customer chatbots hallucinate fake policies and commit unauthorized refunds. Our system solves this with a two-pillar architecture: **Similar Past Support Case Retrieval** from verified historical Amazon resolutions, guarded by a multi-signal **Safety Check** (Trust Gate).*
  >
  > *Notice that by default, the interface is completely customer-friendly: prominent drafted replies and plain-language next steps. For engineering and evaluator review, clicking the **Evaluator Details** toggle in the header unlocks the complete technical proof: our 1,800-case unseen test metrics showing **16.44% Full Trust Gate Automation Coverage**, **90.88% Selective Accuracy**, and an ultra-safe **0.22% Unsafe Auto-Handling Rate**."*

---

### Step 2 (0:30 – 1:00): Automated Self-Service Path (`AUTO-HANDLE`)
- **Action**: Click the first preset pill: **`📦 Where is my package?`**
  - Textarea fills: *"Where is my package? The tracking number says in transit but hasn't updated in 2 days."*
  - Click **Get Instant Support Response**.
- **Customer View Observation**:
  - Decision banner lights up in **Vibrant Emerald Green**: **`AUTO-HANDLE`** with status **`Instant Resolution Ready`**.
  - Customer next-step message: *"Our automated assistant has provided verified self-service guidance."*
  - Plain-language explanation: *"This inquiry matches standard delivery guidance and was verified against past support solutions."*
  - Review the **Drafted Support Reply** card: Clear tracking guidance with real orders link placeholder and DM instructions if delayed over 48 hours.
- **Evaluator View Observation** (click **Evaluator Details** in navbar):
  - Pipeline stepper shows 4 green passing steps: *Topic & Risk → Similar Cases → Response Draft → Safety Check (`AUTO: Safe`)*.
  - Intent classified as `ORDER_TRACKING_STATUS` with 75.7% confidence and reason code `CONFIDENT_GROUNDED`.
  - Review top similar case: `#conv_909056` with 82.1% match.

---

### Step 3 (1:00 – 1:30): Intentional Conservative Abstention (`A specialist will help`)
- **Action**: Click the third preset pill: **`🔄 Return Size Exchange`**
  - Textarea fills: *"How do I return this sweater that is too small? Can I drop it off at an Amazon Locker?"*
  - Click **Get Instant Support Response**.
- **Customer View Observation**:
  - Decision banner displays: **`A specialist will help`** in coral/red.
  - Customer next-step message: *"Connecting to a human customer support agent."*
  - Plain-language explanation: *"To make sure you get the most accurate answer without confusion, an agent will assist you personally."*
- **Evaluator View Observation** (with **Evaluator Details** expanded):
  - Stepper flags Step 4: *Safety Check: `ESCALATE: LOW_CONFIDENCE`*.
  - Technical reason code: `LOW_CONFIDENCE` (Confidence: 66.6% < 75.0% threshold).
  - Precedent match: `#conv_262934` (59.8% match < 62.0% similarity threshold).
- **Narrative**:
  > *"Here is the defining architectural feature of our agent: **Intentional Conservative Abstention**. This inquiry combines return policies with specific drop-off channel logistics ('Amazon Locker').*
  >
  > *Confidence is 66.6% and precedent similarity is 59.8%—both below our gate thresholds. Rather than guessing or inventing an inaccurate locker drop-off instruction, the Safety Check safely abstains and routes the customer to a specialist."*

---

### Step 4 (1:30 – 2:00): Financial & Security Safety Guardrails (`ESCALATE: HIGH_RISK`)
- **Action**: Click either **`💳 Duplicate Charge ($75)`** or **`🚨 Stolen Card / Hacked ($500)`**.
- **Customer View Observation**:
  - Banner shows: **`A specialist will help`**.
  - Next step guides customer: *"Connecting you to a billing specialist to review transactions safely"* or *"Routing directly to our account security team for immediate review."*
- **Evaluator View Observation**:
  - Duplicate Charge: Technical reason code `PAYMENT_DISPUTE`, hard financial dispute rule intercepting automated money movement.
  - Stolen Card: Technical reason code `HIGH_RISK`, account security filter flagging unauthorized transaction fraud.
- **Narrative**:
  > *"Even if confidence were high, our hard risk filters intercept billing disputes and compromised credentials unconditionally. Autonomous agents must never commit funds without human authorization."*

---

## 2. Benchmark Case Matrix

| Benchmark Case | Customer Inquiry Summary | Customer Status | Evaluator Decision & Reason Code | Intent & Confidence | Precedent Provenance | Policy Behavior & Rationale |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| **Empty Input** | `""` (Empty string) | — | — | Prevented submission | — | **Inline Validation**: `⚠️ Enter a customer message.` (no disruptive `alert()`). |
| **1. 📦 Tracking** | *"Where is my package? The tracking number says in transit..."* | `Instant Resolution Ready` | **`AUTO-HANDLE`** (`CONFIDENT_GROUNDED`) | `ORDER_TRACKING_STATUS` (75.7%) | Adapted from `#conv_909056` (82.1% match) | **Automated**: Standard low-risk shipping status with strong historical precedent. |
| **2. ⏳ Delay** | *"My order was supposed to arrive yesterday and is now delayed..."* | `Instant Resolution Ready` | **`AUTO-HANDLE`** (`CONFIDENT_GROUNDED`) | `DELIVERY_DELAY` (90.0%) | Adapted from `#conv_2283454` (83.3% match) | **Automated**: High-confidence delivery delay inquiry with proven carrier tracking guidance. |
| **3. 🔄 Return** | *"How do I return this sweater that is too small? Can I drop it off at an Amazon Locker?"* | `A specialist will help` | **`ESCALATE TO HUMAN`** (`LOW_CONFIDENCE`) | `OTHER` (66.6%) | Precedent `#conv_262934` (59.8% match) | **Intentional Conservative Abstention**: Multi-clause query with drop-off logistics falls below confidence threshold (66.6% < 75%) and precedent similarity (59.8% < 62%). Abstaining prevents ungrounded drop-off instructions. |
| **4. 💳 Dispute** | *"I see two separate $75 charges on my card for the same order!..."* | `A specialist will help` | **`ESCALATE TO HUMAN`** (`PAYMENT_DISPUTE`) | `PAYMENT_AND_BILLING_ISSUE` (71.2%) | Precedent `#conv_2142929` (65.2% match) | **Escalated (Financial)**: Strict financial dispute rule intercepts duplicate billing to prevent unauthorized automated refunds. |
| **5. 🚨 Fraud** | *"My credit card was stolen and someone placed a $500 order..."* | `A specialist will help` | **`ESCALATE TO HUMAN`** (`HIGH_RISK`) | `UNAUTHORIZED_TRANSACTION_FRAUD` (76.6%) | Precedent `#conv_2946739` (74.0% match) | **Escalated (Security)**: Critical account security violation flagged immediately by safety filters. |
| **6. ❓ Ambiguous**| *"Hey someone check this thing right now it looks weird."* | `A specialist will help` | **`ESCALATE TO HUMAN`** (`LOW_CONFIDENCE`) | `OTHER` (68.2%) | Precedent `#conv_18687` (47.0% match) | **Escalated (Ambiguity)**: Weak signal prevents speculative responses. |

---

## 3. Verified Reliability & Safety Metrics

All displayed figures reflect the full Multi-Signal Trust Gate evaluated on the $N=1,800$ unseen test split (`data/evaluation_results.json`):

- **Full Gate Automation Rate**: **16.44%** ($N=296$)
- **Selective Accuracy on Automated Cohort**: **90.88%** ($269 / 296$)
- **Unsafe Auto-Handling Rate**: **0.22%** ($4 / 1,800$)
- **Precedent Recall@5 (FAISS)**: **89.8%**
- **Test Suite Status**: **29 / 29 Passing** (`pytest tests/ -v`)
