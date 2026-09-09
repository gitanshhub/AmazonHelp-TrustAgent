# AI Customer Support Agent — Complete Project Plan

## 1. Project Goal

Build an AI customer-support agent for **one brand** from the Customer Support on Twitter dataset.

The agent must:

1. Classify incoming customer messages into a small set of brand-specific intents.
2. Draft a response grounded in how that brand historically resolved similar issues.
3. Decide whether the message should be **AUTO-HANDLED** or **ESCALATED TO A HUMAN**.
4. Give a clear reason for the escalation decision.
5. Provide measurable evidence that the agent is trustworthy.

The core pipeline is:

```text
Customer Message
       ↓
Conversation / Context
       ↓
Intent Classification
       ↓
Historical Case Retrieval
       ↓
Grounded Response Generation
       ↓
Trust / Escalation Gate
       ↓
AUTO-HANDLE or HUMAN
```

---

# 2. Final Product

The finished product should be a small production-style AI support system.

Example:

```text
Customer:
"My refund hasn't arrived after 10 days."

        ↓

Intent:
REFUND_NOT_RECEIVED
Confidence: 94%

        ↓

Historical Evidence:
3 similar historical conversations found.

        ↓

Decision:
AUTO-HANDLE

Reason:
High classification confidence, strong historical evidence,
and no account-specific investigation is required.

        ↓

Draft Response:
"Sorry about the delay. Please send us your order details
via DM so we can check the refund status."
```

For a risky or uncertain message:

```text
Customer:
"I was charged ₹20,000 because someone stole my card."

        ↓

Intent:
PAYMENT_DISPUTE

        ↓

Decision:
ESCALATE TO HUMAN

Reason:
Financial dispute requires human investigation.
```

---

# 3. Dataset

Primary dataset:

**Customer Support on Twitter — Kaggle**
`thoughtvector/customer-support-on-twitter`

The dataset contains roughly 3 million tweets, multiple brands, and multi-turn customer-support conversations.

Optional secondary dataset:

**Banking77 — Hugging Face**
`PolyAI/banking77`

Banking77 should only be used as an optional experiment for intent classification. The Twitter dataset remains the primary source for the project.

---

# 4. Technology Stack

Recommended stack:

### Backend

- Python
- FastAPI

### Data Processing

- Pandas
- PyArrow
- DuckDB

### Machine Learning

- scikit-learn
- sentence-transformers
- clustering algorithms such as KMeans or HDBSCAN

### Retrieval

Start with:

- FAISS

Possible production-style alternative:

- PostgreSQL + pgvector

### LLM

Use an LLM API or open model.

Keep the LLM provider abstract so it can be replaced later.

### Frontend

Recommended:

- Next.js / React

Simpler alternative:

- Streamlit

### Deployment

Possible:

- Vercel for frontend
- Cloud deployment for FastAPI
- Hosted PostgreSQL/pgvector if required

---

# 5. Repository Structure

Recommended final structure:

```text
ai-support-agent/
│
├── README.md
├── requirements.txt
├── .env.example
├── Dockerfile
├── docker-compose.yml
│
├── data/
│   └── README.md
│
├── notebooks/
│   ├── 01_exploration.ipynb
│   ├── 02_intent_discovery.ipynb
│   └── 03_evaluation.ipynb
│
├── src/
│   ├── ingestion/
│   │   ├── loader.py
│   │   └── conversation_builder.py
│   │
│   ├── preprocessing/
│   │   └── cleaner.py
│   │
│   ├── intents/
│   │   ├── taxonomy.py
│   │   ├── classifier.py
│   │   └── labeling.py
│   │
│   ├── retrieval/
│   │   ├── embeddings.py
│   │   ├── index.py
│   │   └── retriever.py
│   │
│   ├── generation/
│   │   └── responder.py
│   │
│   ├── escalation/
│   │   └── policy.py
│   │
│   └── evaluation/
│       ├── classification.py
│       ├── retrieval.py
│       ├── response.py
│       └── escalation.py
│
├── api/
│   └── main.py
│
├── frontend/
│
├── configs/
│   └── intents.yaml
│
└── tests/
    ├── test_conversation_builder.py
    ├── test_classifier.py
    ├── test_retrieval.py
    ├── test_escalation.py
    └── test_api.py
```

---

# 6. Milestone 1 — Download and Understand the Dataset

Do not build the chatbot yet.

First inspect the dataset.

Determine:

- Available files
- Available columns
- Number of tweets
- Number of brands
- Number of conversations
- Number of customer messages
- Number of brand messages
- Average conversation length
- Median conversation length
- Maximum conversation length
- Number of multi-turn conversations

Create:

```text
notebooks/01_exploration.ipynb
```

The notebook should produce useful statistics and visualizations.

Example output:

```text
Total tweets: X
Total brands: X
Total conversations: X
Average conversation length: X
Median conversation length: X
```

---

# 7. Milestone 2 — Choose the Brand

Do not choose the brand randomly.

Rank brands using:

- Conversation volume
- Number of multi-turn conversations
- Number of customer → brand interactions
- Number of resolved support cases
- Variety of recurring support problems

Example analysis:

| Brand | Tweets | Conversations | Avg. Thread Length |
|---|---:|---:|---:|
| Brand A | X | X | X |
| Brand B | X | X | X |
| Brand C | X | X | X |

Choose the brand that gives enough historical support data.

Document the reason for the choice in the README.

Example:

> We selected [BRAND] because it contains a high volume of multi-turn customer-support interactions and recurring support problems, providing sufficient historical cases for intent discovery and resolution retrieval.

---

# 8. Milestone 3 — Reconstruct Conversations

Raw Twitter data contains individual tweets.

Convert:

```text
Tweet A
Tweet B → reply to A
Tweet C → reply to B
Tweet D → reply to C
```

into:

```text
Conversation 123

Customer:
"My package hasn't arrived."

Brand:
"Sorry to hear that. Can you DM us your order number?"

Customer:
"It's been 5 days."

Brand:
"Please check your DM."
```

Build:

```text
src/ingestion/loader.py
src/ingestion/conversation_builder.py
```

Output:

```text
processed_conversations.parquet
```

---

# 9. Milestone 4 — Clean the Data

Remove or filter:

- Empty messages
- Duplicate tweets
- Broken conversation chains
- Deleted/unusable messages
- Extremely short conversations
- Conversations with insufficient support information
- Clearly irrelevant/non-support content

Identify message roles:

```text
CUSTOMER
BRAND
```

Represent each conversation approximately as:

```json
{
  "conversation_id": "123",
  "brand": "SelectedBrand",
  "messages": [
    {
      "role": "customer",
      "text": "Where is my package?"
    },
    {
      "role": "brand",
      "text": "Please DM us your order number."
    }
  ]
}
```

---

# 10. Milestone 5 — Discover Support Intents

The assignment requires a small set of intents that are derived from the data.

Do not start with arbitrary labels.

Take customer messages and create embeddings:

```text
Customer Messages
       ↓
Sentence Embeddings
       ↓
Clustering
       ↓
Inspect Clusters
       ↓
Human-defined Intent Names
```

Examples:

```text
"Where is my package?"
"Can I track my order?"
"Where's my delivery?"

        ↓

DELIVERY_STATUS
```

Another:

```text
"I was charged twice."
"Why did you bill me two times?"
"I see a duplicate charge."

        ↓

DUPLICATE_CHARGE
```

Target approximately:

**10–15 intents**

plus:

```text
OTHER
```

if necessary.

---

# 11. Milestone 6 — Create the Intent Taxonomy

Create:

```text
configs/intents.yaml
```

Example:

```yaml
intents:

  DELIVERY_STATUS:
    description: Customer wants to know where their order is.

  DELIVERY_DELAY:
    description: Customer says their delivery is late.

  REFUND_REQUEST:
    description: Customer wants to request a refund.

  REFUND_NOT_RECEIVED:
    description: Customer says an expected refund has not arrived.

  PAYMENT_PROBLEM:
    description: Customer reports a payment or billing problem.

  ACCOUNT_PROBLEM:
    description: Customer has an account-related issue.

  PRODUCT_PROBLEM:
    description: Customer reports a problem with a product.

  CANCELLATION:
    description: Customer wants to cancel an order or service.

  TECHNICAL_PROBLEM:
    description: Customer reports a technical problem.

  INFORMATION_REQUEST:
    description: Customer is asking for general information.

  OTHER:
    description: Message does not fit another intent.
```

These are examples only. The final taxonomy must come from the selected brand's actual data.

---

# 12. Milestone 7 — Build the Labeled Dataset

Create:

```text
train
validation
test
```

Important:

## Split by conversation, NOT by individual tweet.

Bad:

```text
Conversation 1:
Tweet A → train
Tweet B → test
```

This creates data leakage.

Correct:

```text
Conversation 1 → train
Conversation 2 → train
Conversation 3 → test
Conversation 4 → test
```

The test conversations must remain unseen during training and retrieval-index construction.

---

# 13. Milestone 8 — Label the Data

An LLM can be used for initial/weak labeling.

Process:

```text
Customer Messages
       ↓
LLM Labeling
       ↓
Human Validation
       ↓
Correct Errors
       ↓
Final Dataset
```

For example:

```text
5,000 messages
        ↓
LLM labels all 5,000
        ↓
Manually inspect a representative sample
        ↓
Correct labeling errors
        ↓
Final labeled dataset
```

Document this methodology.

---

# 14. Milestone 9 — Build Intent Classification

Build at least two baselines and one stronger approach.

## Baseline 1 — Traditional ML

Use:

```text
TF-IDF
+
Logistic Regression
```

## Baseline 2 — LLM

Prompt an LLM with the intent definitions.

Output:

```json
{
  "intent": "DELIVERY_DELAY",
  "confidence": 0.91
}
```

## Final Approach — Retrieval-assisted classification

```text
Incoming Message
       ↓
Embedding
       ↓
Retrieve Similar Labeled Examples
       ↓
LLM Classifier
       ↓
Intent + Confidence
```

Output:

```json
{
  "intent": "DELIVERY_DELAY",
  "confidence": 0.94
}
```

---

# 15. Milestone 10 — Build the Historical Knowledge Base

This is the core of the project.

Do not ask the LLM:

> "How should this brand respond?"

Instead ask:

> "How has this brand historically handled similar problems?"

For each useful historical conversation, store:

```text
Case ID
Intent
Customer problem
Conversation
Brand response
Resolution
```

Example:

```json
{
  "case_id": "case_9821",
  "intent": "REFUND_NOT_RECEIVED",
  "customer_problem": "Customer says refund has not arrived.",
  "conversation": "...",
  "resolution": "Brand asked customer to DM order details and investigated the refund status."
}
```

---

# 16. Milestone 11 — Create the Vector Index

Generate embeddings for historical support cases.

Use:

```text
sentence-transformers
```

Store vectors in:

```text
FAISS
```

Initial architecture:

```text
Historical Support Cases
       ↓
Embedding Model
       ↓
FAISS Vector Index
```

Keep metadata alongside each vector so the retrieved case can be mapped back to the original conversation.

---

# 17. Milestone 12 — Historical Retrieval

For a new customer message:

```text
"My refund hasn't arrived after 10 days."
```

retrieve the most similar historical cases.

Example:

```text
Top 5:

1. Refund pending for 8 days
2. Refund hasn't arrived
3. Customer waiting for refund
4. Refund status question
5. Missing refund
```

Evaluate whether the retrieved cases actually contain useful resolution information.

Important:

## Retrieve conversations/cases, not isolated tweets.

The resolution is usually contained in the complete interaction.

---

# 18. Milestone 13 — Build Response Generation

Input:

```text
Customer message
+
Intent
+
Historical similar cases
```

Output:

```json
{
  "reply": "Sorry about the delay...",
  "confidence": 0.92
}
```

Generation rules:

- Ground the response in retrieved historical cases.
- Do not invent company policies.
- Do not invent refund rules.
- Do not claim an action was performed unless the system actually performed it.
- Do not fabricate order/account information.
- Do not pretend to have access to internal systems.
- Escalate when historical evidence is insufficient.

Example of a bad response:

> "I've issued your refund."

unless the system actually has the ability to issue refunds.

---

# 19. Milestone 14 — Build the Escalation System

The system must choose:

```text
AUTO-HANDLE
```

or:

```text
ESCALATE TO HUMAN
```

Do not use only:

```python
if confidence < 0.5:
    escalate()
```

Instead combine multiple signals.

Example:

```text
AUTO if:

classification confidence >= threshold
AND
retrieval quality >= threshold
AND
intent is low-risk
AND
historical resolution is clear
AND
no account-specific action is required
AND
no unsupported claims are detected
```

Otherwise:

```text
ESCALATE
```

---

# 20. Escalation Reason Codes

Use explicit reason codes.

Possible codes:

```text
LOW_CONFIDENCE
NO_SIMILAR_CASE
ACCOUNT_SPECIFIC_ACTION
PAYMENT_DISPUTE
HIGH_RISK
CONFLICTING_EVIDENCE
CUSTOMER_REQUESTED_HUMAN
```

Output:

```json
{
  "decision": "ESCALATE",
  "reason_code": "ACCOUNT_SPECIFIC_ACTION",
  "reason": "Resolving this issue requires access to customer-specific account information."
}
```

---

# 21. Milestone 15 — Build the Trust Gate

Final architecture:

```text
                    Customer
                       │
                       ↓
                Intent Classifier
                       │
                       ↓
                  Retrieval
                       │
                       ↓
                Response Draft
                       │
                       ↓
                  TRUST GATE
                  /       \
                 ↓         ↓
              AUTO      ESCALATE
```

The Trust Gate checks:

```text
1. Is classification confident?
2. Is retrieved evidence relevant?
3. Is the response grounded?
4. Is the issue high-risk?
5. Does the response contain unsupported claims?
6. Does the issue require account-specific action?
```

---

# 22. Milestone 16 — Build the Evaluation Dataset

Create a completely unseen test set.

The test set must not be used to build the retrieval index.

Evaluate on conversations the system has never seen.

Suggested split:

```text
70% Train
15% Validation
15% Test
```

The exact percentages can change depending on dataset size.

---

# 23. Evaluation — Intent Classification

Measure:

- Accuracy
- Macro F1
- Precision
- Recall
- Per-intent F1
- Confusion matrix

Example:

| Intent | Precision | Recall | F1 |
|---|---:|---:|---:|
| Delivery | X | X | X |
| Refund | X | X | X |
| Payment | X | X | X |
| Account | X | X | X |
| Other | X | X | X |

Do not fabricate results. Calculate them from the actual test set.

---

# 24. Evaluation — Retrieval

Measure:

```text
Recall@1
Recall@3
Recall@5
MRR
```

Core question:

> Did the system retrieve a genuinely useful historical support case?

Example:

```text
Recall@5 = X
MRR = X
```

---

# 25. Evaluation — Response Quality

Use human evaluation.

Score generated responses on:

```text
1. Correctness
2. Relevance
3. Groundedness
4. Completeness
5. Brand consistency
6. Helpfulness
```

Use a 1–5 scale.

Example:

| Metric | Score |
|---|---:|
| Correctness | X/5 |
| Groundedness | X/5 |
| Relevance | X/5 |
| Helpfulness | X/5 |

---

# 26. Evaluation — Hallucination

Create an important metric:

## Unsupported Claim Rate

For every generated response, determine:

> Does the response make a factual or policy claim that is unsupported by the retrieved historical evidence?

Calculate:

```text
Unsupported Claim Rate =
unsupported responses / total responses
```

Compare:

```text
LLM only
vs
LLM + RAG
vs
LLM + RAG + Trust Gate
```

This demonstrates whether grounding actually improves reliability.

---

# 27. Evaluation — Escalation

Create a manually reviewed test set labeled:

```text
SHOULD_AUTO
SHOULD_ESCALATE
```

Measure:

- Escalation precision
- Escalation recall
- False auto-handling rate
- False escalation rate
- Automation rate

The most important safety metric is:

## False Auto-Handling Rate

```text
Cases that should have gone to a human
but were automatically handled
/
All cases
```

This should be kept low.

---

# 28. Selective Prediction / Automation Threshold

Test different confidence thresholds.

Example:

| Threshold | Automation Rate | Accuracy |
|---:|---:|---:|
| 0.50 | X% | X% |
| 0.60 | X% | X% |
| 0.70 | X% | X% |
| 0.80 | X% | X% |
| 0.90 | X% | X% |

The objective is not:

> Maximize automation.

The objective is:

> Maximize safe automation while keeping false auto-handling low.

This is one of the strongest parts of the project.

---

# 29. Baseline Comparison

Compare:

```text
1. TF-IDF + Logistic Regression
2. LLM without retrieval
3. LLM + historical retrieval
4. LLM + historical retrieval + Trust Gate
```

Example structure:

| System | Intent F1 | Groundedness | Unsupported Claims | False Auto |
|---|---:|---:|---:|---:|
| TF-IDF | X | - | - | - |
| LLM | X | X | X% | X% |
| LLM + RAG | X | X | X% | X% |
| RAG + Trust Gate | X | X | X% | X% |

These numbers must come from your experiments.

---

# 30. Milestone 17 — Build the Backend API

Use FastAPI.

Endpoint:

```text
POST /api/support/analyze
```

Input:

```json
{
  "message": "My refund hasn't arrived."
}
```

Output:

```json
{
  "intent": {
    "name": "REFUND_NOT_RECEIVED",
    "confidence": 0.94
  },

  "evidence": [
    {
      "case_id": "123",
      "similarity": 0.91
    }
  ],

  "response": {
    "text": "..."
  },

  "decision": {
    "action": "AUTO",
    "reason": "High confidence with strong historical evidence."
  }
}
```

---

# 31. Milestone 18 — Build the Frontend

The UI should be simple.

## Customer Message

```text
┌──────────────────────────────────────┐
│ Customer message                     │
│                                      │
│ My refund hasn't arrived...          │
│                                      │
│                     [Analyze]        │
└──────────────────────────────────────┘
```

## Intent

```text
REFUND_NOT_RECEIVED
94% confidence
```

## Historical Evidence

```text
3 similar cases found

Case #102
Case #839
Case #1921
```

## Decision

```text
AUTO-HANDLE

Reason:
High confidence and strong historical evidence.
```

## Draft Response

```text
"Sorry about the delay..."
```

---

# 32. Add a "Why?" Section

Show decision factors without exposing private chain-of-thought.

Example:

```text
Why was this response generated?

✓ Classified as REFUND_NOT_RECEIVED
✓ 3 similar historical cases retrieved
✓ Historical cases show the same resolution pattern
✓ No high-risk action detected
✓ Confidence above automation threshold
```

---

# 33. Add Failure Analysis

Show real failure examples.

Example:

```text
Failure #1

Customer:
"I was charged but didn't receive anything."

Predicted:
PAYMENT_PROBLEM

Correct:
DELIVERY_NOT_RECEIVED

Cause:
The message is ambiguous between payment and delivery.
```

Then explain how the system handles this.

For example:

> Ambiguous cases are routed to human support instead of being automatically answered.

This demonstrates that you understand model limitations.

---

# 34. Optional Banking77 Experiment

Only implement this after the main project works.

Possible experiment:

```text
Brand-specific intent classification
            vs
Generic Banking77 intent classification
```

Use it to test whether your classification methodology generalizes.

Do not allow Banking77 to distract from the main Twitter-based task.

---

# 35. Milestone 19 — Automated Tests

Create:

```text
tests/
├── test_conversation_builder.py
├── test_classifier.py
├── test_retrieval.py
├── test_escalation.py
└── test_api.py
```

Test cases such as:

```text
High confidence + strong evidence → AUTO

Low confidence → ESCALATE

No retrieval results → ESCALATE

High-risk issue → ESCALATE

Account-specific action → ESCALATE

Strong evidence + low-risk issue → AUTO
```

---

# 36. Milestone 20 — Docker

If time allows, add:

```text
Dockerfile
docker-compose.yml
```

Ideally:

```text
docker compose up
```

starts:

```text
Frontend
Backend
Vector database
```

---

# 37. Milestone 21 — Deployment

Optional but recommended.

Possible architecture:

```text
Frontend
   ↓
Vercel

FastAPI Backend
   ↓
Cloud deployment

Vector Database
   ↓
PostgreSQL + pgvector
```

If LLM API costs are a concern, provide a controlled demo mode.

---

# 38. Final README

README structure:

```text
# AI Customer Support Agent

## Problem

## Demo

## Architecture

## Dataset

## Brand Selection

## Conversation Reconstruction

## Intent Taxonomy

## Intent Classification

## Historical Retrieval

## Response Generation

## Escalation Strategy

## Trust Gate

## Evaluation Methodology

## Results

## Baselines

## Failure Analysis

## Limitations

## Future Work

## Running Locally
```

---

# 39. Technical Report

Prepare a 4–8 page report.

Recommended structure:

```text
1. Problem Statement
2. Dataset
3. Data Processing
4. Brand Selection
5. Intent Discovery
6. Intent Classification
7. Historical Retrieval
8. Response Generation
9. Escalation Strategy
10. Trust / Safety Design
11. Evaluation Methodology
12. Results
13. Failure Analysis
14. Limitations
15. Future Improvements
```

---

# 40. Demo Video

Make a 2–4 minute demo.

## 0:00–0:20 — Problem

Explain:

> We built an AI support agent for [BRAND] using real historical Twitter support conversations.

## 0:20–0:50 — Architecture

Show:

```text
Message
 ↓
Intent
 ↓
Historical Retrieval
 ↓
Response
 ↓
Trust Gate
 ↓
Auto / Human
```

## 0:50–1:30 — Normal Case

Show:

```text
Customer:
"Where is my order?"

→ DELIVERY_STATUS
→ Historical cases
→ AUTO
→ Response
```

## 1:30–2:00 — Uncertain Case

Show:

```text
Ambiguous message
        ↓
Low confidence
        ↓
ESCALATE
```

## 2:00–2:30 — High-Risk Case

Show:

```text
Payment dispute
        ↓
ESCALATE
        ↓
Reason
```

## 2:30–3:00 — Evaluation

Show:

```text
Intent F1
Retrieval Recall@5
Groundedness
Unsupported Claim Rate
False Auto-Handling Rate
Automation Rate
```

## 3:00–3:30 — Failure Analysis

Show one or two real failure cases.

Conclude:

> The system is designed to optimize for safe automation rather than maximum automation.

---

# 41. Final Submission Package

Submit:

### 1. GitHub repository

Complete source code.

### 2. Live demo

If possible.

### 3. README

Complete technical documentation.

### 4. Technical report

4–8 pages.

### 5. Demo video

2–4 minutes.

---

# 42. Exact Development Order

Follow these milestones in order:

```text
MILESTONE 1
Download dataset
        ↓
MILESTONE 2
Explore dataset
        ↓
MILESTONE 3
Select brand
        ↓
MILESTONE 4
Reconstruct conversations
        ↓
MILESTONE 5
Clean data
        ↓
MILESTONE 6
Discover intents
        ↓
MILESTONE 7
Create taxonomy
        ↓
MILESTONE 8
Create train/validation/test sets
        ↓
MILESTONE 9
Build intent classifier
        ↓
MILESTONE 10
Build historical knowledge base
        ↓
MILESTONE 11
Build vector index
        ↓
MILESTONE 12
Build retrieval
        ↓
MILESTONE 13
Build response generator
        ↓
MILESTONE 14
Build escalation system
        ↓
MILESTONE 15
Build Trust Gate
        ↓
MILESTONE 16
Build evaluation framework
        ↓
MILESTONE 17
Run experiments
        ↓
MILESTONE 18
Analyze failures
        ↓
MILESTONE 19
Build FastAPI backend
        ↓
MILESTONE 20
Build frontend
        ↓
MILESTONE 21
Automated tests
        ↓
MILESTONE 22
Docker / deployment
        ↓
MILESTONE 23
README
        ↓
MILESTONE 24
Technical report
        ↓
MILESTONE 25
Demo video
        ↓
SUBMIT
```

---

# 43. What Matters Most

Prioritize these areas:

## Highest priority

1. Correct conversation reconstruction
2. Data-derived intent taxonomy
3. Historical-resolution retrieval
4. Grounded response generation
5. Safe escalation
6. Rigorous evaluation
7. Failure analysis

## Medium priority

8. FastAPI
9. Frontend
10. Automated tests

## Lower priority

11. Fancy UI
12. Docker
13. Deployment
14. Banking77 experiment

A beautiful UI with weak evaluation will be less convincing than a simple UI backed by strong experiments.

---

# 44. Central Research Question

Frame the project around:

> **At what confidence and risk threshold can this AI support agent safely automate customer-support conversations, and what evidence demonstrates that it is trustworthy?**

This is stronger than simply saying:

> "We built a chatbot."

The project is fundamentally about:

```text
Historical Support Data
        ↓
Understand Customer Intent
        ↓
Retrieve Proven Resolutions
        ↓
Generate Grounded Response
        ↓
Assess Risk
        ↓
Automate Only When Safe
        ↓
Escalate Everything Else
        ↓
Measure Whether It Actually Works
```

---

# 45. Definition of Done

The project is ready to submit when all of these are true:

- [ ] One brand selected and selection justified
- [ ] Twitter conversations reconstructed
- [ ] Data cleaned
- [ ] 10–15 intents derived from actual data
- [ ] Intent taxonomy documented
- [ ] Train/validation/test split created by conversation
- [ ] Intent classifier implemented
- [ ] Historical cases indexed
- [ ] Similar-case retrieval implemented
- [ ] Grounded response generation implemented
- [ ] Escalation policy implemented
- [ ] Escalation reasons implemented
- [ ] Trust Gate implemented
- [ ] Test set kept separate from retrieval index
- [ ] Intent metrics calculated
- [ ] Retrieval metrics calculated
- [ ] Response quality evaluated
- [ ] Unsupported claim rate calculated
- [ ] Escalation metrics calculated
- [ ] False auto-handling rate calculated
- [ ] Baselines compared
- [ ] Failure analysis documented
- [ ] API implemented
- [ ] Demo UI implemented
- [ ] Automated tests added
- [ ] README completed
- [ ] Technical report completed
- [ ] Demo video recorded
- [ ] Repository is runnable from a clean environment

---

# 46. The Key Idea

This project is **not**:

```text
User → LLM → Answer
```

It is:

```text
                REAL HISTORICAL DATA
                         ↓
                 BRAND-SPECIFIC
                 SUPPORT KNOWLEDGE
                         ↓
Customer → Intent → Retrieval → Response
                              ↓
                         TRUST GATE
                         /        \
                        ↓          ↓
                     AUTO       HUMAN
```

The strongest submission will prove that the system doesn't just produce plausible answers — it knows **when its historical evidence is strong enough to answer and when it should get a human involved**.
