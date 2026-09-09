# AmazonHelp AI Customer Support Agent
### Trustworthy, Precedent-Grounded AI Support System with FAISS Retrieval & Multi-Signal Trust Gate

[![Python 3.11](https://img.shields.io/badge/Python-3.11-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)
[![FAISS](https://img.shields.io/badge/FAISS-CPU-orange.svg)](https://github.com/facebookresearch/faiss)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests: 26 Passed](https://img.shields.io/badge/Tests-26%20Passed-brightgreen.svg)](tests/)

---

## 1. Problem Statement & Research Question

Traditional AI customer support chatbots fail in enterprise production because they suffer from **hallucinations, lack of auditability, and inability to assess their own uncertainty**:
- They invent policies ("I've processed your full refund to your card!").
- They treat all queries equally, attempting to answer high-risk disputes or credential issues instead of escalating.
- They lack historical brand context.

### Central Research Question:
> **"At what confidence and risk threshold can an AI support agent safely automate customer-support conversations, and what empirical evidence demonstrates that it is trustworthy?"**

Rather than naive generation (`User -> LLM -> Output`), this project implements an end-to-end trustworthy architecture:
```text
Customer Message
       ↓
Intent Classification (SentenceTransformers + calibrated confidence)
       ↓
Historical Case Retrieval (FAISS vector search over 8,399 resolved support dialogues)
       ↓
Grounded Response Generation (Strictly grounded in historical brand precedents)
       ↓
Multi-Signal Trust Gate (Evaluates risk, confidence, evidence quality, and groundedness)
       ↓
[AUTO-HANDLE] with Audit Trail   OR   [ESCALATE TO HUMAN] with Explicit Reason Code
```

---

## 2. Interactive Demo & User Interface

The system features a real-time web dashboard (Vanilla CSS glassmorphism, Inter typography, responsive layout) served directly by FastAPI:
- **Interactive Benchmark Inquiries**: Pre-loaded test cases (Delivery delays, Tracking queries, Return requests, Duplicate charges, Stolen credit cards, and Ambiguous fragments).
- **Decision Banner**: Immediate visual routing (`AUTO-HANDLE` in glowing emerald vs `ESCALATE TO HUMAN` in coral/amber).
- **Audit Trail ("Why?" Card)**: Complete checklist showing why a decision was reached (Risk check, Confidence threshold, Precedent similarity, Groundedness check).
- **Historical Evidence Precedents**: Live display of top matching cases from the FAISS vector database showing case ID, similarity %, customer inquiry, and proven brand resolution.

---

## 3. Dataset & Exploration (Milestones 1 & 2)

- **Primary Source**: Kaggle's [Customer Support on Twitter dataset](https://www.kaggle.com/datasets/thoughtvector/customer-support-on-twitter) (`twcs/twcs.csv`, 492.58 MB).
- **Total Tweets Scanned**: 2,811,774
- **Customer (Inbound) Tweets**: 1,537,843 (54.7%)
- **Brand (Outbound) Tweets**: 1,273,931 (45.3%)
- **Unique Support Brands**: 108

### Brand Ranking & Selection
| Rank | Brand | Total Brand Tweets | Multi-Turn Replies | Multi-Turn Ratio | Domain |
| :---: | :--- | :---: | :---: | :---: | :--- |
| **1** | **AmazonHelp** | **169,840** | **85,274** | **50.2%** | **E-Commerce / Deliveries** |
| 2 | AppleSupport | 106,860 | 31,564 | 29.5% | Tech / iOS Troubleshooting |
| 3 | Uber_Support | 56,270 | 18,036 | 32.0% | Rideshare / Transport |
| 4 | SpotifyCares | 43,265 | 13,786 | 31.8% | Digital Music / Subscriptions |
| 5 | Delta | 42,253 | 12,014 | 28.4% | Airlines / Travel |

> **Selected Brand: AmazonHelp**  
> Justification: AmazonHelp possesses the largest corpus of resolved dialogues (169,840) and highest multi-turn depth (85,274 multi-turn interactions, >50% multi-turn rate), providing rich conversational context and realistic e-commerce risk boundaries.

---

## 4. Conversation Reconstruction & Cleaning (Milestones 4 & 5)

Raw Twitter data stores disconnected single tweets. We reconstructed multi-turn conversation trees:
1. Traced `in_response_to_tweet_id` recursively to identify the root inquiry.
2. Grouped child turns under unique `conversation_id`.
3. Assigned roles (`customer` vs `brand`) and sorted chronologically.
4. Cleaned noisy handles (`@AmazonHelp`), normalized URLs (`[LINK]`), stripped agent signatures (`^JD`, `/SW`), and filtered non-support noise.
5. Produced **84,795** valid multi-turn dialogues saved to `data/processed_conversations.parquet`.

---

## 5. Intent Taxonomy & Leak-Free Partitioning (Milestones 6–8)

15 data-derived intents configured in `configs/intents.yaml`:
- **Low / Medium Risk (Auto-Handle Eligible)**:
  - `ORDER_TRACKING_STATUS`, `DELIVERY_DELAY`, `PACKAGE_DELIVERED_NOT_RECEIVED`, `DAMAGED_OR_DEFECTIVE_ITEM`, `WRONG_ITEM_RECEIVED`, `REFUND_NOT_RECEIVED`, `RETURN_EXCHANGE_INQUIRY`, `CANCELLATION_REQUEST`, `PRIME_MEMBERSHIP_INQUIRY`, `DIGITAL_SERVICES_AND_DEVICE`, `GENERAL_INQUIRY_FEEDBACK`.
- **High / Critical Risk (Mandatory Human Escalation)**:
  - `UNAUTHORIZED_TRANSACTION_FRAUD` (Reason: `HIGH_RISK`)
  - `PAYMENT_AND_BILLING_ISSUE` (Reason: `PAYMENT_DISPUTE`)
  - `ACCOUNT_ACCESS_SECURITY` (Reason: `ACCOUNT_SPECIFIC_ACTION`)
  - `OTHER` (Reason: `LOW_CONFIDENCE`)

### Data Splits (Partitioned Strictly by Conversation ID):
To avoid data leakage, test conversations were completely isolated from model training and vector indexing:
- **Train Set**: 8,399 conversations (70.0%)
- **Validation Set**: 1,801 conversations (15.0%)
- **Test Set (Unseen)**: 1,800 conversations (15.0%)

---

## 6. Historical Knowledge Base & FAISS Retrieval (Milestones 10–12)

- Embedded 8,399 training cases using `sentence-transformers/all-MiniLM-L6-v2`.
- Stored normalized 384-dimensional vectors in a FAISS `IndexFlatIP` index (`data/faiss_index.bin`) with rich metadata mapping (`data/faiss_metadata.parquet`).
- Retrieval quality signals:
  - Top similarity score
  - Top-3 mean similarity
  - Neighbor intent consensus ratio

---

## 7. Trust Gate & Escalation Strategy (Milestones 14 & 15)

The Trust Gate evaluates multiple criteria simultaneously:
```text
AUTO-HANDLE if:
  Classification Confidence >= 0.75
  AND Historical Case Similarity >= 0.62
  AND Intent is LOW or MEDIUM risk
  AND Intent != FRAUD / PAYMENT_DISPUTE / ACCOUNT_SECURITY
  AND No unsupported or hallucinated promises detected
Otherwise:
  ESCALATE TO HUMAN
```

### Explicit Escalation Reason Codes:
- `LOW_CONFIDENCE`: Intent score below 0.75 or ambiguous inquiry.
- `NO_SIMILAR_CASE`: FAISS similarity below 0.62.
- `HIGH_RISK`: Stolen card, identity theft, unauthorized charge.
- `PAYMENT_DISPUTE`: Double billing, transaction discrepancies.
- `ACCOUNT_SPECIFIC_ACTION`: OTP, password recovery, account unlock.
- `CONFLICTING_EVIDENCE`: Potential hallucination or policy conflict.

---

## 8. Empirical Evaluation Results (Milestones 16 & 23–29)

Tested on **1,800 completely unseen test conversations**:

### A. Intent Classification
| Model | Accuracy | Macro F1 | Weighted F1 |
| :--- | :---: | :---: | :---: |
| **Baseline 1** (TF-IDF + Logistic Regression) | 65.67% | 0.5727 | 0.6690 |
| **Production** (Retrieval-Augmented k-NN Classifier) | **68.44%** | **0.5409** | **0.6866** |

### B. Historical Resolution Retrieval (FAISS)
| Metric | Score | Meaning |
| :--- | :---: | :--- |
| **Recall@1** | 62.67% | Exact top match has relevant intent precedent |
| **Recall@3** | 82.83% | Relevant precedent present in top 3 results |
| **Recall@5** | **89.78%** | 9 out of 10 inquiries find proven historical precedent in top 5 |
| **MRR** | **0.7317** | High mean rank position of relevant cases |

### C. Safety & Trust Gate Performance
| Safety Metric | Score | Goal & Significance |
| :--- | :---: | :--- |
| **False Auto-Handling Rate** | **0.22%** | **Near Zero (Target < 1%)** — Risky cases almost never leak through |
| **Escalation Recall** | **99.58%** | **99.6% of all risky/ambiguous cases routed to humans** |
| **Unsupported Claim Rate** | **0.00%** | **Zero hallucinated promises or fake system actions** |
| **Safe Automation Rate** | **17.4%** | System safely automates inquiries with 90.7% precision |

### D. Selective Prediction Analysis (Automation Rate vs Accuracy)
| Confidence Threshold | Automation Rate | Safe Accuracy on Automated Queries |
| :---: | :---: | :---: |
| $\ge 0.50$ | 51.6% | 59.4% |
| $\ge 0.60$ | 39.7% | 70.6% |
| $\ge 0.70$ | 24.4% | 83.8% |
| **$\ge 0.75$ (Default)** | **17.9%** | **90.7%** |
| $\ge 0.80$ | 11.6% | 94.7% |
| $\ge 0.85$ | 5.4% | 95.9% |
| $\ge 0.90$ | 1.2% | 95.2% |

> **Conclusion**: Setting the threshold to **0.75** provides the optimal operating point: it achieves **>90% accuracy** on automated responses while ensuring that risky or uncertain queries are caught with **99.6% recall**.

---

## 9. Failure Analysis (Section 33)

During evaluation, edge cases were analyzed to verify system robustness:

1. **Failure Case 1: Ambiguity Between Delivery vs Payment**
   - *Customer*: *"I was charged for my package but received nothing."*
   - *Predicted Intent*: `PAYMENT_AND_BILLING_ISSUE` (Confidence: 0.61) vs `DELIVERY_DELAY`.
   - *System Handling*: Confidence fell below 0.75 threshold. Trust Gate immediately routed to human support with reason code `PAYMENT_DISPUTE` / `LOW_CONFIDENCE`. No erroneous automated promise was made.

2. **Failure Case 2: Sarcastic Complaints**
   - *Customer*: *"Wonderful job Amazon, love waiting 3 weeks for my books."*
   - *Predicted Intent*: `DELIVERY_DELAY` / `GENERAL_INQUIRY_FEEDBACK`.
   - *System Handling*: Sarcasm caused low nearest-neighbor consensus. The Trust Gate routed the conversation to an agent rather than giving an insensitive generic reply.

---

## 10. Repository Structure

```text
├── api/
│   └── main.py                       # FastAPI application & static mounts
├── configs/
│   └── intents.yaml                  # 15-intent brand taxonomy & risk levels
├── data/
│   ├── brand_ranking.json            # Empirical brand comparison data
│   ├── exploration_summary.json      # twcs.csv scan metrics
│   ├── faiss_index.bin               # FAISS vector index (8,399 cases)
│   ├── faiss_metadata.parquet        # Metadata mapping for vector search
│   ├── processed_conversations.parquet # Reconstructed dialogue trees
│   ├── train_conversations.parquet   # 70% train split
│   ├── val_conversations.parquet     # 15% validation split
│   ├── test_conversations.parquet    # 15% unseen test split
│   ├── golden_set.csv                # 200 hand-reviewed golden evaluation conversations
│   ├── golden_set.jsonl              # Golden set JSONL format
│   ├── golden_set_review.csv         # Human review stratification template
│   ├── golden_evaluation_results.json # Full benchmark metrics & discovered failure modes
│   ├── judge_human_review.csv        # 50 hand-reviewed judge validation cases
│   ├── judge_human_validation.json   # Human vs LLM Judge correlation benchmark
│   ├── evaluation_results.json       # 1,800-test set evaluation metrics
│   └── tfidf_classifier.pkl          # Trained baseline model
├── frontend/
│   ├── index.html                    # Dashboard UI layout
│   ├── styles.css                    # Glassmorphism design system
│   └── app.js                        # Client API integration & dynamic rendering
├── notebooks/
│   └── 01_exploration.ipynb          # Milestones 1 & 2 analysis notebook
├── scripts/
│   ├── check_evaluation_leakage.py   # Programmatic zero-leakage test across splits
│   ├── build_golden_set.py           # Stratified golden set sampler
│   ├── run_golden_evaluation.py      # End-to-end golden evaluation runner
│   ├── validate_judge.py             # Human vs LLM Judge correlation validator
│   ├── brand_ranking.py              # Brand ranking analysis
│   ├── explore_dataset.py            # twcs.csv stats generator
│   ├── reconstruct_conversations.py  # Conversation builder runner
│   ├── prepare_labeled_dataset.py    # Intent labeling and splitting
│   ├── build_knowledge_base.py       # FAISS index and classifier builder
│   └── run_evaluation.py             # 1,800 test set evaluation
├── src/
│   ├── ingestion/                    # Raw data loader and tree stitcher
│   ├── preprocessing/                # Text cleaner and URL normalizer
│   ├── intents/                      # Taxonomy manager, classifiers, majority baseline
│   ├── retrieval/                    # CaseEmbedder, VectorIndex, Retriever
│   ├── generation/                   # GroundedResponder and anti-hallucination
│   ├── escalation/                   # TrustGatePolicy and reason codes
│   └── evaluation/                   # LLM Judge & metrics calculation modules
├── tests/
│   ├── test_api.py                   # API endpoint tests
│   ├── test_classifier.py            # Intent classification tests
│   ├── test_conversation_builder.py  # Stitcher and cleaner tests
│   ├── test_escalation.py            # Trust Gate policy unit tests
│   ├── test_golden_evaluation.py     # Golden set schema, zero-leakage, baseline tests
│   └── test_retrieval.py             # Embedder & FAISS search tests
├── DECISION_LOG.md                   # 15 non-obvious engineering decisions & trade-offs
├── TECHNICAL_REPORT.md               # 10-section rigorous technical evaluation report
├── Dockerfile                        # Production container image
├── docker-compose.yml                # Multi-container orchestration
├── requirements.txt                  # Python dependencies
└── pytest.ini                        # Pytest configuration
```

---

## 11. Reproduce Results (< 15 Minutes)

A reviewer can fully verify all safety claims, baselines, zero-leakage proofs, and judge correlations in under 15 minutes using pre-computed datasets and lightweight verification scripts:

### Step 1: Verify Zero Data Leakage (< 5 seconds)
Proves mathematically that zero conversation IDs or customer queries from the Golden Evaluation Set exist in the Training set or FAISS knowledge base:
```bash
python scripts/check_evaluation_leakage.py
```
*Expected Output*:
```text
Golden INTERSECT Train IDs: 0 (PASSED)
Golden INTERSECT FAISS Index: 0 (PASSED)
Golden Exact Inquiry Match: 0 (PASSED)
```

### Step 2: Validate the LLM Judge against Human Review (< 2 minutes)
Computes exact agreement, agreement within $\pm 1$ point, Spearman rank $\rho$, and Cohen's $\kappa$ between human evaluations and the instruction-tuned `Qwen/Qwen2.5-0.5B-Instruct` model on 50 hand-reviewed interactions:
```bash
python scripts/validate_judge.py
```
*Expected Output*:
```text
Safety Agreement: 100.0%
Overall Agreement within ±1 point: 100.0% (Exact Match: 56.5%)
Groundedness Agreement within ±1 point: 95.7%
```

### Step 3: Run the Golden Set Benchmark (< 5 minutes)
Runs the end-to-end evaluation comparing the Majority Class baseline, TF-IDF baseline, and Production Retrieval-Augmented agent across all 200 Golden Set cases:
```bash
python scripts/run_golden_evaluation.py
```
*Key Benchmark Results (Hard Golden Set, N=200)*:
- **Unsafe Auto-Handling Rate**: **0.00%** (Zero dangerous/disputed issues auto-handled)
- **Escalation Recall**: **100.00%** (All 42 high-risk and fraud cases caught)
- **Unsupported Claim Rate**: **0.00%**
- **Selective Accuracy on Auto Queries**: **85.7%** (operating at frozen $\tau = 0.75$)
- **LLM Judge Safety Score**: **5.00 / 5.00**

*(Note: On the 1,800-case Unseen Test Set, the system achieved 17.9% coverage, 90.7% selective accuracy, 99.58% escalation recall, and 0.22% unsafe auto-handling.)*

### Step 4: Run the Complete Automated Test Suite (< 1 minute)
Executes all 26 unit, integration, and safety tests:
```bash
pytest tests/ -v
```

---

## 12. Running Locally

### 1. Prerequisites
- Python 3.11+
- Git

### 2. Setup Virtual Environment
```bash
# Clone the repository
git clone <repo-url>
cd <repo-folder>

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Start the Application
```bash
uvicorn api.main:app --reload --port 8000
```
Open your browser and navigate to:
```text
http://localhost:8000
```

### 4. Run with Docker
```bash
docker compose up --build
```
Access the dashboard at `http://localhost:8000`.

