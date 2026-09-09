# Hiver SDE Intern — Final Evaluation & Proof Plan

## Objective

The core AI support agent for **AmazonHelp** is already implemented.

The remaining work must focus on **evaluation, evidence, failure analysis, and reproducibility**.

Hiver explicitly states:

> **"The proof is worth more than the system."**

Therefore:

- Do not add unnecessary product features.
- Do not expand the architecture unless required.
- Do not optimize only for a higher headline metric.
- Do not fabricate or infer human evaluation results.
- Do not assume failure modes before running the evaluation.
- Every reported result must be reproducible from the repository.

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

Current reported results that must be independently verified:

| Metric | Current Result |
|---|---:|
| Intent accuracy | 68.44% |
| TF-IDF + Logistic Regression | 65.67% |
| Retrieval Recall@1 | 62.67% |
| Retrieval Recall@3 | 82.83% |
| Retrieval Recall@5 | 89.78% |
| Retrieval MRR | 0.7317 |
| False auto-handling rate | 0.22% |
| Escalation recall | 99.58% |
| Unsupported claim rate | 0.00% |
| Selective accuracy | 90.7% |
| Auto-handling coverage | 17.9% |

Do not assume these numbers are final. Re-run the relevant evaluations and verify the definitions and denominators.

---

# Phase 1 — Audit Existing Repository

Before implementing anything, inspect the actual repository.

Map the implementation against every Hiver requirement.

## Required checklist

- [ ] One brand selected and justified
- [ ] Intent taxonomy derived from data
- [ ] Intent classifier
- [ ] Historical precedent retrieval
- [ ] Grounded reply generation
- [ ] Auto-handle / escalation decision
- [ ] Explicit escalation reason
- [ ] 150–250 hand-labelled golden examples
- [ ] Trivial baseline
- [ ] Simple baseline
- [ ] Automated evaluation metrics
- [ ] LLM-as-judge
- [ ] Human validation of LLM judge
- [ ] Judge-human agreement statistics
- [ ] Per-intent analysis
- [ ] Threshold / coverage analysis
- [ ] Top 5 failure modes based on actual failures
- [ ] "What is misleading about my headline number?"
- [ ] Decision log with 10–15 decisions
- [ ] README reproduction under 15 minutes
- [ ] Technical report <= 6 pages

Do not mark a requirement complete merely because a similarly named file exists.

Inspect implementation and run the relevant code.

---

# Phase 2 — Construct the Golden Evaluation Set

## Hiver requirement

Hiver requires:

> **150–250 hand-labelled examples you built yourself.**

Create a **200-example golden evaluation set**.

Recommended files:

```text
data/golden_set.jsonl
data/golden_set.csv
scripts/build_golden_set.py
```

## Golden set fields

At minimum:

```text
conversation_id
customer_message
intent
expected_action
risk_level
```

Recommended additional fields:

```text
conversation_context
reference_resolution
sampling_group
notes
```

## Sampling strategy

Use reproducible sampling.

The golden set should provide:

- Representation across the 15 intents.
- Coverage of rare intents.
- Coverage of high-risk cases.
- Coverage of ambiguous cases.
- Coverage of multi-turn conversations.
- Avoidance of duplicate conversations.

Do not force an artificial equal distribution if the underlying data cannot support it.

The sampling strategy should balance:

```text
Real-world distribution
+
Rare-intent coverage
+
High-risk coverage
+
Edge-case coverage
```

Document the sampling methodology.

---

# Phase 3 — Human Review of Golden Set

This phase requires actual human judgment.

The coding agent must **not fabricate the labels**.

The agent may:

- Prepare candidate examples.
- Display them in a convenient format.
- Suggest provisional labels.
- Create a labelling template.

But the final golden labels must be **human-reviewed**.

The human reviewer should verify:

- Intent
- Expected action
- Risk level
- Reference resolution where applicable

Maintain a record that these examples were manually reviewed.

---

# Phase 4 — Verify Evaluation Data Leakage

Because the production system uses historical retrieval, explicitly verify that golden examples are not leaking into the retrieval/training data.

At minimum check:

```text
Golden conversation IDs
        ∩
Training conversation IDs
        =
EMPTY
```

Also investigate obvious duplicate or near-duplicate conversations where practical.

The evaluation should not allow the system to retrieve the exact evaluation conversation from its training/retrieval index.

Create a verification script if necessary:

```text
scripts/check_evaluation_leakage.py
```

The final report should briefly describe the leakage-prevention strategy.

---

# Phase 5 — Implement Trivial Baseline

Hiver requires:

> "at least two baselines (a trivial one and a simple one)."

The existing:

```text
TF-IDF + Logistic Regression
```

is the **simple baseline**.

Add a trivial majority-class baseline.

Create:

```text
src/intents/majority_baseline.py
```

The classifier should:

1. Determine the most common intent in the training data.
2. Predict that intent for every evaluation example.
3. Report:
   - Accuracy
   - Macro-F1

Final comparison:

```text
Majority Baseline       XX.XX%
TF-IDF + Logistic       65.67%
Production Classifier   68.44%
```

Run the experiment rather than assuming values.

---

# Phase 6 — Implement a Real LLM-as-Judge

Hiver explicitly requires:

> "an LLM-as-judge rubric for reply quality"

The primary judge must be an **actual LLM**.

Do not substitute a deterministic heuristic or embedding similarity model as the primary LLM judge.

An offline heuristic may exist as a supplementary reproducibility/fallback tool, but it must not be presented as the required LLM-as-judge.

Create:

```text
src/evaluation/judge.py
```

## Judge input

The judge receives:

```text
Customer message
+
Relevant conversation context
+
Retrieved historical precedents
+
Generated response
```

The judge must NOT receive:

- Human rating
- Expected judge score
- Post-hoc failure label

The judge evaluates independently.

---

# Phase 7 — LLM Judge Rubric

Use a 1–5 Likert scale.

## 1. Correctness

Does the response appropriately address the customer's problem without making false assertions?

## 2. Groundedness

Are the claims supported by the retrieved historical evidence?

## 3. Relevance

Does the response directly address the customer's actual request?

## 4. Helpfulness

Does the response provide a useful and appropriate next step?

## 5. Safety

Does the response avoid:

- Fake refunds
- Fake account actions
- Unsupported backend claims
- Unsafe handling of financial/security issues
- Inappropriate automation

The judge should return structured JSON.

Example:

```json
{
  "correctness": 4,
  "groundedness": 5,
  "relevance": 5,
  "helpfulness": 4,
  "safety": 5,
  "overall": 5,
  "reasoning": "..."
}
```

The exact schema may be adjusted for implementation reliability.

---

# Phase 8 — Human Validation of LLM Judge

This phase requires actual human evaluation.

## Important

The coding agent must **not invent human scores**.

The agent should:

1. Select approximately 50 representative responses.
2. Run the LLM judge independently.
3. Export the 50 examples and judge scores.
4. Create a human-rating template.

Example:

```text
data/judge_human_review.csv
```

The human reviewer then independently rates the same 50 responses using the identical rubric.

Only after the human ratings are completed should the comparison script run.

---

# Phase 9 — Judge vs Human Agreement

Create:

```text
scripts/validate_judge.py
data/judge_human_validation.json
```

Compare the human ratings against the LLM judge ratings.

Calculate appropriate statistics such as:

- Exact agreement percentage
- Agreement within ±1 point
- Spearman correlation
- Weighted Cohen's kappa where appropriate

Example output:

```text
Samples: 50

Correctness:
Exact agreement: XX%
Within ±1: XX%
Spearman rho: XX

Groundedness:
Exact agreement: XX%
Within ±1: XX%
Spearman rho: XX

...

Overall:
Exact agreement: XX%
Within ±1: XX%
Spearman rho: XX
```

Do not claim the judge is reliable unless these results actually support that conclusion.

---

# Phase 10 — Full Golden Set Evaluation

Run the production agent against all 200 golden examples.

Create:

```text
scripts/run_golden_evaluation.py
data/golden_evaluation_results.json
```

Measure:

## Intent

- Accuracy
- Macro-F1
- Precision
- Recall
- Per-intent F1

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
- Overall score

## Escalation

- Escalation recall
- Escalation precision
- False auto-handling rate
- False escalation rate
- Auto-handling coverage

## Grounding

- Unsupported claim rate

All metric definitions and denominators must be documented.

---

# Phase 11 — Per-Intent Analysis

Do not report only aggregate accuracy.

Produce a table:

```text
Intent                    Precision    Recall    F1
----------------------------------------------------
DELIVERY_DELAY               XX%        XX%      XX%
REFUND                       XX%        XX%      XX%
RETURNS                      XX%        XX%      XX%
...
```

Identify:

- Strongest intents
- Weakest intents
- Rare intents
- Frequently confused intents

Use this analysis to guide failure analysis.

---

# Phase 12 — Trust Gate Threshold Analysis

The current system uses:

```text
Confidence >= 0.75
Similarity >= 0.62
```

Do not assume these thresholds are optimal.

Evaluate multiple confidence thresholds:

```text
0.60
0.70
0.75
0.80
0.90
```

For each threshold calculate:

- Auto-handling coverage
- Selective accuracy
- False auto-handling rate
- Escalation rate

Example:

```text
Threshold    Coverage    Accuracy    False Auto
-------------------------------------------------
0.60            XX%         XX%         XX%
0.70            XX%         XX%         XX%
0.75            XX%         XX%         XX%
0.80            XX%         XX%         XX%
0.90            XX%         XX%         XX%
```

Use the empirical results to justify the final threshold.

Do not choose a threshold merely because it produces an attractive metric.

The objective is a sensible:

```text
Safety ↔ Automation Coverage
```

trade-off.

---

# Phase 13 — Discover the Top 5 Failure Modes

## Critical requirement

Do NOT assume the failure modes in advance.

Do not hard-code assumptions such as:

- Sarcasm
- Carrier terminology
- Multi-issue requests
- Intent ambiguity

unless the evaluation demonstrates that they are actual significant failure modes.

Instead:

```text
Run evaluation
      ↓
Collect incorrect / unsafe / low-quality cases
      ↓
Group failures by root cause
      ↓
Count frequency
      ↓
Identify top 5
      ↓
Analyze actual examples
```

For each of the five actual failure modes document:

```text
Failure mode
Real customer example
Agent prediction / response
Expected result
Why the failure occurred
Potential architectural improvement
```

The examples must come from actual evaluation data.

---

# Phase 14 — "What Is Misleading About My Headline Number?"

This is mandatory.

Do not automatically use 90.7% as the headline number.

First determine which metric best summarizes the system.

Then explain its limitations.

For example, if using:

```text
90.7% selective accuracy
```

explicitly explain that this is measured only on the subset considered safe to automate.

If automation coverage is 17.9%, then:

```text
90.7% accuracy
```

does NOT mean:

```text
90.7% of all incoming conversations are successfully handled.
```

Explain:

- Metric denominator
- Selection bias
- Class imbalance
- Automation coverage
- Escalated population
- Difference between selective accuracy and overall system utility

The goal is to demonstrate that you understand how metrics can create a misleading impression.

---

# Phase 15 — Engineering Decision Log

Create:

```text
DECISION_LOG.md
```

Document 10–15 non-obvious decisions.

Recommended decisions:

1. Why AmazonHelp was selected.
2. Why conversation-level splitting was used.
3. Why 15 intents were selected.
4. How intent boundaries were determined.
5. Why historical precedent retrieval was used.
6. Why SentenceTransformers was selected.
7. Why FAISS was selected.
8. Why retrieval-assisted classification was used.
9. Why the confidence threshold was selected.
10. Why the similarity threshold was selected.
11. Why fraud/payment cases are escalated.
12. Why unsupported claims are prohibited.
13. Why selective automation is preferred to maximum coverage.
14. Why an LLM judge was selected.
15. Why human validation of the judge was required.

Each entry should contain:

```text
Decision:
Why:
Alternative considered:
Trade-off:
```

Keep the document concise.

---

# Phase 16 — Technical Report

Update:

```text
TECHNICAL_REPORT.md
```

Keep it within the Hiver limit of **6 pages**.

Recommended structure:

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

Focus on evidence rather than implementation detail.

The report should communicate:

```text
Messy data
    ↓
Working agent
    ↓
Evaluation methodology
    ↓
Measured results
    ↓
Human validation
    ↓
Real failures
    ↓
Honest interpretation
```

---

# Phase 17 — README Reproducibility

Update:

```text
README.md
```

Add:

```text
## Reproduce Results
```

The README must tell the reviewer:

1. Python version
2. Installation
3. Required environment variables
4. Dataset/preprocessed artifact requirements
5. Exact evaluation commands
6. Expected runtime
7. Where results are saved
8. Example output

The reviewer should not need to discover the pipeline themselves.

Example:

```bash
python scripts/run_golden_evaluation.py
```

If full dataset preprocessing takes a long time, provide the appropriate preprocessed/subsampled artifact so that reproducing the headline evaluation results remains under the requested 15-minute window.

---

# Phase 18 — Evaluation Tests

Create:

```text
tests/test_golden_evaluation.py
```

Test:

- Golden set contains 150–250 examples.
- Required fields exist.
- No duplicate conversation IDs.
- Golden examples do not overlap training IDs.
- Majority baseline works.
- Evaluation metrics calculate correctly.
- Judge output follows the expected schema.
- Threshold analysis produces valid results.
- Missing/invalid judge responses are handled safely.

Do not create tests that merely assert hard-coded expected metric values unless the values are mathematically deterministic.

---

# Phase 19 — Final Verification

Run:

```bash
pytest tests/ -v
```

Then:

```bash
python scripts/check_evaluation_leakage.py
```

Then:

```bash
python scripts/run_golden_evaluation.py
```

Then:

```bash
python scripts/validate_judge.py
```

Verify:

- [ ] 200 golden examples exist.
- [ ] Golden labels were actually human-reviewed.
- [ ] No evaluation leakage exists.
- [ ] Majority baseline exists.
- [ ] TF-IDF baseline exists.
- [ ] Production model exists.
- [ ] LLM judge is actually an LLM.
- [ ] Human ratings exist for the judge validation set.
- [ ] Judge-human agreement is calculated from real ratings.
- [ ] Per-intent metrics exist.
- [ ] Reply-quality metrics exist.
- [ ] Escalation metrics exist.
- [ ] Threshold analysis exists.
- [ ] Top 5 failures were discovered from actual results.
- [ ] Each failure has a real example.
- [ ] "Misleading headline number" section exists.
- [ ] Decision log has 10–15 decisions.
- [ ] README reproduces headline results.
- [ ] Technical report is <= 6 pages.
- [ ] All tests pass.

---

# Important Rules for the Coding Agent

## Never fabricate human evidence

Do NOT generate fake:

- Human labels
- Human ratings
- Human-vs-LLM agreement
- Correlations
- Cohen's kappa
- Human validation results

If human input is required, prepare the data and stop for human review.

---

## Never fabricate evaluation results

Do not create attractive numbers simply to populate the report.

All numbers must come from actual execution.

If an evaluation cannot currently be run, report the blocker rather than inventing the result.

---

## Do not assume failure modes

Failure modes must be discovered from actual errors.

The agent may propose hypotheses, but they must be clearly marked as hypotheses and supported by real examples.

---

## Do not add unnecessary features

Do not spend time on:

- Additional frontend features
- Unnecessary API endpoints
- Multiple new model architectures
- Full-dataset processing
- Production infrastructure unrelated to the assignment
- Cosmetic improvements

The system is already sufficiently complex.

Focus on **proof**.

---

# Definition of Done

The final project should demonstrate:

```text
                    AmazonHelp
                         ↓
                Conversation Data
                         ↓
                  Intent Taxonomy
                         ↓
                     AI Agent
                         ↓
               Golden Set (200)
                         ↓
          ┌──────────────┼──────────────┐
          ↓              ↓              ↓
       Intent        Reply Quality   Escalation
      Evaluation     LLM Judge       Evaluation
          │              │              │
          │         Human Validation    │
          │              │              │
          └──────────────┼──────────────┘
                         ↓
                  Threshold Analysis
                         ↓
                 Failure Analysis
                         ↓
              Misleading Metric
                         ↓
                  Decision Log
                         ↓
                  Technical Report
                         ↓
                    README
                         ↓
                    Submission
```

## Final Principle

The goal is not to prove:

> **"My AI is perfect."**

The goal is to demonstrate:

> **"I built a useful support agent, measured it carefully, validated my evaluation methodology, understand where it fails, understand the limitations of my metrics, and can explain the engineering decisions behind it."**

That is the standard this implementation should optimize for.