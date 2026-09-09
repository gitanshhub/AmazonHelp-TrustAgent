# Hiver SDE Intern — Final Evaluation Implementation Plan

## Objective

The core AI support agent for **AmazonHelp** is already implemented.

The remaining work should focus on **evaluation and proof**, because Hiver explicitly states:

> "The proof is worth more than the system."

Do **not** add unnecessary product features. Do not significantly change the existing architecture unless required to satisfy an evaluation requirement.

---

# Current System

The existing pipeline is:

```text
Customer Message
      ↓
Intent Classification
      ↓
Historical Case Retrieval
      ↓
Grounded Response Generation
      ↓
Trust Gate
      ↓
AUTO-HANDLE / ESCALATE
```

Current reported results:

- Intent accuracy: 68.44%
- TF-IDF + Logistic Regression baseline: 65.67%
- Retrieval Recall@1: 62.67%
- Retrieval Recall@3: 82.83%
- Retrieval Recall@5: 89.78%
- Retrieval MRR: 0.7317
- False auto-handling rate: 0.22%
- Escalation recall: 99.58%
- Unsupported claim rate: 0.00%
- Selective accuracy at confidence >= 0.75: 90.7%
- Auto-handling coverage: 17.9%

These numbers must be independently reproducible from the repository.

---

# Phase 1 — Audit Existing Evaluation

Before implementing anything new, inspect the repository and determine which Hiver requirements are already satisfied.

Create a checklist covering:

- [ ] One brand selected and justified
- [ ] Intent taxonomy derived from data
- [ ] Intent classifier
- [ ] Historical precedent retrieval
- [ ] Grounded reply generation
- [ ] Auto-handle / escalation decision
- [ ] Golden evaluation set: 150–250 hand-labelled examples
- [ ] Trivial baseline
- [ ] Simple baseline
- [ ] Automated evaluation metrics
- [ ] LLM-as-judge
- [ ] Human validation of LLM judge
- [ ] Top 5 failure modes with real examples
- [ ] "What is misleading about my headline number?"
- [ ] Decision log with 10–15 decisions
- [ ] README reproduction under 15 minutes
- [ ] Report <= 6 pages

Do not assume a requirement is complete merely because a related component exists.

---

# Phase 2 — Build the Golden Evaluation Set

## Requirement

Hiver requires:

> 150–250 hand-labelled examples you built yourself.

Create a **200-example golden evaluation set**.

The examples should come from the AmazonHelp conversations but must be manually reviewed and labelled.

## Important

Do NOT simply rename the existing 1,800-example test split as the golden set.

The golden set must represent an explicitly constructed, hand-labelled evaluation set.

## Recommended structure

Create:

```text
data/golden_set.csv
```

or:

```text
data/golden_set.jsonl
```

Each record should contain at minimum:

```text
conversation_id
customer_message
intent
expected_action
risk_level
```

If useful, include:

```text
conversation_context
reference_response
sampling_group
notes
```

## Sampling

Use a reproducible sampling process.

Prefer stratified sampling so that the golden set does not consist almost entirely of common intents.

Document:

1. How candidate conversations were selected.
2. How many examples were sampled from each intent.
3. How high-risk cases were included.
4. How ambiguous cases were included.
5. How duplicates were avoided.
6. How the final labels were manually assigned.

The final report should contain a short description of this methodology.

## Manual labelling

The final intent and expected action labels must be reviewed by the developer.

AI assistance may be used to help inspect or organize examples, but the golden labels must represent human-reviewed ground truth.

---

# Phase 3 — Add the Trivial Baseline

Hiver requires:

> Results vs. at least two baselines (a trivial one and a simple one).

The existing TF-IDF + Logistic Regression model is the **simple baseline**.

Add a trivial baseline:

## Majority-class baseline

Determine the most common intent in the training data.

Predict that intent for every test example.

Example:

```text
Every incoming message
        ↓
Most common intent
```

Calculate:

- Accuracy
- Macro-F1 if applicable

The final comparison should look approximately like:

```text
Majority baseline       XX.XX%
TF-IDF + Logistic Reg   65.67%
Production classifier   68.44%
```

Do not fabricate values. Run the evaluation.

---

# Phase 4 — Build the LLM-as-Judge

Hiver requires:

> "an LLM-as-judge rubric for reply quality"

Create an evaluation module, preferably under:

```text
src/evaluation/
```

The judge should evaluate generated replies from the support agent.

## Judge input

For each evaluation example provide:

```text
Customer message
Conversation context (when appropriate)
Retrieved historical evidence
Agent-generated response
```

The judge should NOT be given the expected human score.

## Evaluation dimensions

Use a clear 1–5 scale.

### 1. Correctness

Does the reply correctly address the customer's problem without making unsupported factual claims?

### 2. Groundedness

Is the response supported by the historical evidence provided to the agent?

### 3. Relevance

Does the response directly address the customer's actual request?

### 4. Helpfulness

Would the response provide a useful next step to the customer?

### 5. Safety

Does the response avoid inappropriate automation, fabricated account actions, payment promises, or other risky claims?

The final rubric may combine these into an overall score, but retain the individual dimensions.

---

# Phase 5 — Human Validation of the LLM Judge

This is mandatory.

Hiver specifically asks for:

> "including evidence of how well your judge agrees with a human"

Select approximately **50 examples** from the golden evaluation set for human review.

For every selected response:

1. Human assigns scores using the same rubric.
2. LLM judge assigns scores independently.
3. Store both results.
4. Compare the ratings.

Example:

```text
Example        Human    LLM Judge
-----------------------------------
1                4          4
2                3          3
3                2          3
4                5          5
...
```

Calculate an appropriate agreement statistic.

Possible metrics:

- Exact agreement
- Agreement within ±1 point
- Spearman correlation
- Weighted Cohen's kappa, where appropriate

The report should clearly state:

```text
Human-vs-LLM agreement:
XX%

Correlation:
XX

Sample:
50 examples
```

Do not claim the judge is reliable without evidence.

---

# Phase 6 — Full Golden Set Evaluation

Run the complete production agent against the 200-example golden set.

Measure at least:

## Intent

- Accuracy
- Macro-F1
- Per-intent performance

## Retrieval

- Recall@1
- Recall@3
- Recall@5
- MRR

## Reply quality

- Correctness
- Groundedness
- Relevance
- Helpfulness
- Safety
- Overall judge score

## Escalation

- Escalation recall
- False auto-handling rate
- Auto-handling coverage

## Grounding

- Unsupported claim rate

Store the results in a machine-readable format such as:

```text
data/evaluation_results.json
```

or:

```text
results/
```

---

# Phase 7 — Per-Intent Analysis

Do not report only overall accuracy.

Calculate performance for each of the 15 intents.

Example:

```text
Intent                  Accuracy
--------------------------------
Delivery Tracking          XX%
Late Delivery              XX%
Refund                     XX%
Returns                    XX%
Payment                    XX%
...
```

Identify:

- strongest intents
- weakest intents
- rare intents
- frequently confused intents

This will feed directly into the failure analysis.

---

# Phase 8 — Trust Gate Threshold Analysis

The current system uses:

```text
confidence >= 0.75
similarity >= 0.62
```

Do not assume these thresholds are optimal.

Evaluate several thresholds.

For example:

```text
Threshold    Coverage    Accuracy    False Auto
-------------------------------------------------
0.60            XX%         XX%         XX%
0.70            XX%         XX%         XX%
0.75            17.9%       90.7%       0.22%
0.80            XX%         XX%         XX%
0.90            XX%         XX%         XX%
```

Use the results to explain why the final threshold was selected.

The goal is not maximum automation.

The goal is an appropriate trade-off between:

```text
Safety
   ↕
Automation coverage
```

---

# Phase 9 — Failure Analysis

Identify the **top 5 failure modes**.

Each failure mode must contain a real example from the evaluation data.

For each failure:

```text
Failure mode
↓
Real customer example
↓
Agent prediction / response
↓
Expected result
↓
Why the system failed
↓
Potential improvement
```

Potential categories include:

- Intent confusion
- Ambiguous language
- Long-context failure
- Retrieval mismatch
- Hallucinated or unsupported information
- Incorrect escalation
- Failure to escalate
- Rare-intent weakness
- Incorrect historical precedent
- Customer context loss

Do not invent failure modes.

They must come from actual evaluation results.

---

# Phase 10 — "What Is Misleading About My Headline Number?"

This section is mandatory.

Choose the main headline metric carefully.

For example:

```text
90.7% selective accuracy
```

could be misleading if only:

```text
17.9% of conversations
```

are actually auto-handled.

Explain:

1. What the headline number measures.
2. What it does NOT measure.
3. What population it was calculated on.
4. How class imbalance affects it.
5. How selective prediction affects it.
6. What happens to the remaining conversations.
7. Why a single metric should not be interpreted as overall system quality.

A strong conclusion might look conceptually like:

```text
"90.7% accuracy" does not mean the agent can
successfully handle 90.7% of all incoming support requests.

It refers only to the subset the Trust Gate considers
safe enough to automate, which represents 17.9% of volume.
The remaining cases are escalated.
```

Use the actual measured numbers.

---

# Phase 11 — Decision Log

Create:

```text
DECISION_LOG.md
```

with **10–15 non-obvious engineering decisions**.

Recommended decisions to document:

1. Why AmazonHelp was selected.
2. Why conversation-level splitting was used.
3. Why 15 intents were selected.
4. How the intent taxonomy was derived.
5. Why historical precedent retrieval was used.
6. Why SentenceTransformers was selected.
7. Why FAISS was selected.
8. Why retrieval was used for intent classification.
9. Why the confidence threshold was selected.
10. Why the similarity threshold was selected.
11. Why high-risk cases are escalated.
12. Why unsupported claims are prohibited.
13. Why selective automation is preferred to maximum coverage.
14. Why an LLM judge was used.
15. Why human validation of the judge was performed.

Each decision should answer:

```text
Decision:
Why:
Alternative considered:
Trade-off:
```

Keep it concise.

---

# Phase 12 — Report

The report must remain within the Hiver limit of **6 pages**.

Recommended structure:

```text
1. Problem Framing
2. System Overview
3. Dataset & Sampling
4. Evaluation Methodology
5. Baselines
6. Results
7. LLM Judge Validation
8. Failure Analysis
9. What Is Misleading About My Headline Number?
10. What I Would Do With One More Week
```

Do not spend excessive space describing implementation details.

The central story should be:

```text
Messy dataset
     ↓
Working agent
     ↓
Evaluation methodology
     ↓
Evidence
     ↓
Failures
     ↓
Honest interpretation
```

---

# Phase 13 — README Reproducibility

Hiver says:

> "README must let us reproduce your headline results in under 15 minutes."

The README should have a section:

```text
## Reproduce Results
```

It should clearly state:

1. Python version.
2. Installation command.
3. Required environment variables.
4. Dataset preparation requirements.
5. Exact evaluation command.
6. Expected runtime.
7. Where the results are written.
8. Example output.

Example:

```bash
python scripts/run_evaluation.py
```

The reviewer should not need to manually discover which scripts to run.

If the full dataset processing takes hours, provide the expected preprocessed/subsampled artifact so that the **evaluation itself** can run within the requested time.

---

# Phase 14 — Final Audit

Before submission, run:

```text
pytest tests/ -v
```

Then verify:

- [ ] 17 existing tests pass.
- [ ] New evaluation tests pass.
- [ ] Golden set contains 150–250 examples.
- [ ] Golden labels were human-reviewed.
- [ ] Majority baseline exists.
- [ ] TF-IDF baseline exists.
- [ ] Production model exists.
- [ ] LLM judge exists.
- [ ] Human-vs-LLM judge comparison exists.
- [ ] Per-intent metrics exist.
- [ ] Reply quality metrics exist.
- [ ] Escalation metrics exist.
- [ ] Threshold analysis exists.
- [ ] Top 5 failures have real examples.
- [ ] Misleading headline number section exists.
- [ ] Decision log contains 10–15 decisions.
- [ ] README reproduces headline results.
- [ ] Report is <= 6 pages.

---

# Important Constraints

## Do NOT

- Add unnecessary frontend functionality.
- Add unnecessary API endpoints.
- Add multiple new model architectures without an evaluation reason.
- Process all 2.8M tweets again unless necessary.
- Optimize for a flashy accuracy number.
- Claim zero hallucinations universally.
- Call the 1,800 test examples a golden set unless they were actually hand-labelled.
- Claim an LLM judge is reliable without human agreement evidence.
- Remove poor results simply because they look bad.

## DO

- Prefer simple, reproducible experiments.
- Keep evaluation data separate from training data.
- Prevent conversation-level data leakage.
- Report both strengths and weaknesses.
- Investigate unexpected results.
- Use real failure examples.
- Explain metric limitations honestly.
- Optimize for evidence rather than system complexity.

---

# Definition of Done

The project is ready for submission when the following pipeline is complete:

```text
                    AmazonHelp
                         ↓
                Conversation Data
                         ↓
                  Intent Taxonomy
                         ↓
                ┌────────────────┐
                │   AI Agent     │
                └───────┬────────┘
                        ↓
                Golden Set (200)
                        ↓
          ┌─────────────┼─────────────┐
          ↓             ↓             ↓
       Intent       Reply Quality   Escalation
      Evaluation    LLM Judge       Evaluation
          │             │             │
          │        Human Validation   │
          │             │             │
          └─────────────┼─────────────┘
                        ↓
                 Failure Analysis
                        ↓
             Threshold Analysis
                        ↓
             Misleading Metric
                        ↓
                 Decision Log
                        ↓
                Final Report
                        ↓
                    README
                        ↓
                  Submission
```

## Final Principle

The objective is **not** to prove:

> "My AI is perfect."

The objective is to demonstrate:

> "I built a useful support agent, measured it carefully, understand where it fails, understand the limitations of my metrics, and can explain the engineering decisions behind it."

That is the standard the final implementation should optimize for.