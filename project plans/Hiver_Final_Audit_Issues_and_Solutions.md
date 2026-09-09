# Hiver SDE Intern — Final Audit: Issues & Solutions

## Purpose

This document is a final pre-submission audit for the AmazonHelp AI Customer Support Agent against the Hiver SDE Intern take-home assignment.

The goal is **not** to add more product features. The goal is to make the evaluation evidence, metrics, methodology, and documentation internally consistent and defensible.

---

# 🔴 A. Must-Fix Issues

## 1. Conflicting metrics across documents

### Issue

Different documents contain metrics for different evaluation sets, but the dataset context is not always explicit.

Examples:
- Golden Set: approximately 24–24.5% automation/coverage and 85.7% selective accuracy.
- Unseen Test Set: 17.9% coverage and 90.7% selective accuracy.

These are not necessarily contradictory because they refer to different datasets, but a reviewer should not have to infer that.

### Solution

Always label the evaluation set next to the metric.

Use:

> **Golden Set (N=200):** 24.5% automation coverage, 85.7% selective accuracy.

and:

> **Unseen Test Set (N=1,800):** 17.9% automation coverage, 90.7% selective accuracy.

Apply this consistently in README, technical report, tables, conclusion, and walkthrough.

---

## 2. Failure count inconsistency: 203 vs 215

### Issue

The report states:

> 203 real classification and policy failures

But the five listed failure-mode counts are:

- 110
- 67
- 25
- 1
- 12

Total = **215 occurrences**, not 203.

### Solution

Inspect `data/golden_evaluation_results.json`.

If failure categories overlap, distinguish:

> **203 unique failed cases and 215 failure-mode occurrences because some cases exhibited multiple failure modes.**

If categories are mutually exclusive, correct the counts so the total is mathematically consistent.

Do not guess. Use the actual evaluation output.

---

## 3. “Optimal threshold” is too strong

### Issue

The report calls τ=0.75 the “optimal frontier operating point.”

But the reported golden results show:

| Threshold | Coverage | Selective Accuracy | False Auto-Handling |
|---:|---:|---:|---:|
| 0.75 | 24.5% | 85.7% | 0.00% |
| 0.80 | 15.5% | 90.3% | 0.00% |
| 0.90 | 2.5% | 80.0% | 0.00% |

There is no formal optimization criterion that makes 0.75 objectively optimal.

### Solution

If 0.75 was chosen because it provides more coverage while maintaining zero observed unsafe automation, say:

> “We selected τ=0.75 as the production operating point because it achieved zero observed false auto-handling on the golden set while retaining substantially more automation coverage than τ=0.80.”

If the threshold was actually selected using the validation set, explicitly state that:

> “The operating threshold was selected using the validation set; the golden and test sets were reserved for final evaluation.”

Only use this if it accurately reflects the implementation.

---

## 4. LLM judge is weak because it uses a 0.5B model

### Issue

The judge uses:

`Qwen/Qwen2.5-0.5B-Instruct`

It technically qualifies as an LLM-as-a-judge, but 0.5B parameters is a weak choice for nuanced evaluation of correctness, groundedness, relevance, and helpfulness.

The reported rank correlations are also weak for several dimensions.

### Solution

Prefer a stronger free LLM if practical, such as a currently available free-tier API model.

Keep the evaluator model configurable:

```text
LLM_PROVIDER=...
LLM_MODEL=...
```

If changing the judge:

1. Keep the existing 50 human ratings.
2. Run the new judge on exactly those same 50 cases.
3. Recalculate judge-human agreement.
4. Run the new judge on all 200 golden cases.
5. Recalculate failure modes and report metrics.
6. Update README/report with the new model and numbers.

Never reuse old agreement numbers for a different judge.

If keeping Qwen 0.5B, explicitly acknowledge its small size as a limitation and explain why it was selected.

---

## 5. 50 human cases vs 46 valid comparisons

### Issue

The report says 50 cases were manually reviewed, but the correlation table says:

> N=46 valid comparisons

This needs explanation.

### Solution

Inspect the four excluded cases.

If they were excluded because of invalid/missing judge outputs, document:

> “Fifty cases were manually reviewed; four were excluded from paired agreement analysis due to invalid or incomplete judge outputs, leaving 46 valid comparisons.”

Only use that explanation if it is true.

Otherwise identify the actual reason.

---

## 6. Do not overclaim LLM judge reliability

### Issue

The report emphasizes 100% agreement within ±1 point, while Spearman correlations are weak or negative for several dimensions.

A reviewer may interpret the presentation as cherry-picking the favorable metric.

### Solution

Use balanced language:

> “Absolute agreement was strong for safety and acceptable for several dimensions, although rank correlations were weak for some dimensions. Therefore, the LLM judge is treated as a scalable evaluation aid rather than a substitute for human ground truth.”

State clearly:

> **Human evaluation remains the reference standard.**

Report both absolute agreement and correlation statistics.

---

## 7. “False Escalation Rate” should be clarified or renamed

### Issue

The report reports:

> False Escalation Rate = 55%

and describes 110 cases being safely deferred to humans.

Escalation is not automatically “false.” It is only false/unnecessary if the ground-truth policy says the case should have been auto-handled.

### Solution

Prefer:

> **Unnecessary Escalation Rate**

Define the denominator explicitly.

For example:

```text
Unnecessary Escalation Rate =
routine cases unnecessarily escalated / all routine cases
```

or another definition that matches the actual evaluation.

Use one definition consistently.

---

## 8. Not every listed “failure” is actually a customer-facing failure

### Issue

One failure example is a classification error where the Trust Gate correctly escalates the case.

That is a classification failure, but not necessarily a safety/policy failure.

### Solution

Separate failure categories:

- **Classification failure:** wrong intent.
- **Policy failure:** unsafe auto-handling.
- **Response-quality failure:** poor/incorrect generated response.
- **Unnecessary escalation:** safe but overly conservative routing.

Then explain:

> “Not every classification error resulted in an unsafe customer-facing decision.”

This makes the evaluation more precise.

---

## 9. Headline incorrectly implies 17.9% is “routine volume”

### Issue

The conclusion says the system safely automates 17.9% of routine volume.

17.9% is the percentage of unseen test cases that passed the Trust Gate; it is not necessarily 17.9% of all routine real-world volume.

### Solution

Use:

> “On the 1,800-conversation unseen test set, the system auto-handled 17.9% of cases with 90.7% selective accuracy, while achieving 99.58% escalation recall and 0.22% false auto-handling.”

This is precise and defensible.

---

# 🟠 B. Important Improvements / Verification

## 10. Majority baseline wording is confusing

### Issue

One section says the dominant class is `OTHER`, while another says `OTHER / DELIVERY_DELAY`.

A majority classifier should predict exactly one dominant class.

### Solution

Check the actual label distribution and state:

> “The majority baseline always predicts `<ACTUAL_DOMINANT_CLASS>`.”

Do not hard-code the label without verifying it.

---

## 11. Explain why production Macro F1 is lower than TF-IDF Macro F1

### Issue

Production:
- Accuracy = 68.44%
- Macro F1 = 0.5409
- Weighted F1 = 0.6866

TF-IDF:
- Accuracy = 65.67%
- Macro F1 = 0.5727
- Weighted F1 = 0.6690

The production model improves accuracy and weighted F1 but loses Macro F1.

### Solution

Add:

> “The retrieval model improves aggregate accuracy but does not improve macro-F1, indicating that its gains are concentrated in higher-frequency intents rather than being uniform across the taxonomy.”

This is valuable negative evidence.

---

## 12. Use precise language for Recall@k

### Issue

Recall@5 is described as finding a “valid historical resolution,” but the metric appears to measure whether a relevant intent precedent is present.

### Solution

Say:

> “A relevant precedent with the expected intent appears in the top-k retrieved cases.”

Do not call it a “correct resolution” unless the evaluator actually verifies resolution correctness.

---

## 13. Verify the actual report page count

### Issue

Markdown does not inherently have pages, yet the report claims to be within the ≤6-page requirement.

### Solution

Render/export the technical report using the intended submission formatting and verify that it is actually ≤6 pages.

Do not rely on Markdown line count.

---

## 14. README test badge is stale

### Issue

README badge says:

> Tests: 17 Passed

while the current test suite reports:

> 22 passed

### Solution

Change the badge to:

> **Tests: 22 Passed**

assuming 22 is the current actual count.

---

## 15. README overstates what can be reproduced in <15 minutes

### Issue

The README says a reviewer can fully verify all claims in under 15 minutes, but the workflow uses precomputed datasets/results rather than reconstructing the entire 492MB dataset pipeline.

### Solution

Use more precise wording:

> “A reviewer can verify the reported evaluation artifacts and reproduce the key headline metrics from the precomputed evaluation datasets in under 15 minutes.”

Then state separately:

> “Full dataset reconstruction is provided as an offline pipeline and is not required for headline-result verification.”

---

## 16. Define exactly how Unsupported Claim Rate is measured

### Issue

The report repeatedly claims:

> Unsupported Claim Rate = 0.00%

That is a strong claim, but the measurement protocol is not sufficiently explicit.

### Solution

Define the metric, for example:

```text
Unsupported Claim Rate =
responses containing >=1 unsupported factual/action claim
---------------------------------------------------------
total evaluated responses
```

Then state how unsupported claims are detected:

- deterministic rules,
- human review,
- LLM evaluation,
- precedent comparison,
- or a combination.

Use the actual implementation.

---

## 17. Avoid broad “hallucination-free” implications

### Issue

A 0.00% unsupported-claim rate under one evaluation protocol does not prove the system can never hallucinate.

### Solution

Prefer:

> “0% unsupported-claim rate under our evaluation protocol.”

Avoid absolute claims such as:

> “hallucination-free.”

---

## 18. Define ground truth for mandatory escalation

### Issue

The report claims:

> 42 / 42 mandatory escalation cases caught.

The methodology needs to establish how those 42 cases were labeled.

### Solution

If true, document:

> “Mandatory escalation labels were assigned during golden-set human review using predefined risk criteria established before final evaluation.”

Do not imply ground truth if it was derived from the same system being evaluated.

---

## 19. Expand the golden-set sampling/labelling description

### Issue

The report says the set was stratified across intents, rare classes, and high-risk queries, but Hiver explicitly asks for a sampling/labelling note.

### Solution

Include a short methodology:

```text
Sampling:
- Stratified by intent.
- Rare and high-risk intents deliberately represented.
- Ambiguous linguistic cases included.
- Fixed random seed used.

Labelling:
- Human assigned expected intent.
- Human assigned expected action.
- Mandatory escalation cases explicitly marked.
- Labels frozen before final evaluation.
```

Only claim steps that actually happened.

---

## 20. Explicitly separate Train / Validation / Test / Golden

### Issue

The report documents the train/validation/test split but needs a stronger statement about how the golden set was used.

### Solution

If true, state:

> “The Golden Set is a separate evaluation artifact and is not used for model training, retrieval-index construction, or threshold tuning.”

If golden results were used to tune the system, do not make that claim. Document the actual process and, if necessary, rerun a clean final evaluation.

---

## 21. Threshold selection should ideally use Validation

### Correct methodology

```text
Train
  ↓
Validation → choose threshold / tune parameters
  ↓
Freeze system
  ↓
Golden + Test → final evaluation
```

### Incorrect methodology

```text
Train
  ↓
Golden → try thresholds
  ↓
choose best threshold
  ↓
report Golden result
```

### Solution

Inspect the actual development process.

If 0.75 was selected using validation, document it.

If it was selected using golden/test performance, be transparent and consider rerunning the final evaluation using a validation-selected threshold.

---

## 22. Make failure-mode generation reproducible

### Issue

The report says failures were empirically isolated, but the report should make clear how categories were produced.

### Solution

Have the evaluation output contain fields such as:

```json
{
  "failure_mode": "...",
  "count": 110,
  "example_ids": ["..."]
}
```

Then use those records to construct the report.

This makes the failure analysis auditable.

---

# 🟡 C. Good Improvements

## 23. Add a concise Limitations section

Suggested points:

- Twitter support data differs from private/in-app support.
- Only one brand was evaluated.
- Golden set contains 200 cases.
- Judge-human validation contains 46 valid paired comparisons if that remains the final number.
- Retrieval quality depends on historical precedent coverage.
- Intent taxonomy is brand-specific.

---

## 24. Make the brand-derived taxonomy explicit

Add:

> “These intents were derived from recurring patterns in AmazonHelp conversations rather than imported from a generic support taxonomy.”

This directly reinforces the assignment requirement that intents be defined from the data.

---

## 25. Reduce emphasis on frontend/UI in the technical report

The dashboard is useful for demonstration, but Hiver's assignment is primarily about:

**system quality → evaluation → safety → evidence → failure analysis.**

Keep the UI, but don't let it consume report space that could be used for evaluation evidence.

---

## 26. Source or remove the $50–$500 / $3–$6 cost estimates

### Issue

The report states:

- False auto-handling: $50–$500+
- Human escalation: $3–$6

These are presented as estimates without a visible source.

### Solution

Either cite a credible source or remove the dollar figures.

Safer wording:

> “The costs are asymmetric: unsafe automation can cause financial, compliance, and reputational damage, whereas unnecessary escalation primarily incurs additional human-handling cost.”

---

## 27. Avoid implying actual production deployment

### Issue

The project is a prototype based on public Twitter data.

### Solution

Prefer:

> “production-oriented architecture”

or:

> “prototype designed around production safety constraints.”

Avoid implying that the system is already deployed in enterprise production.

---

## 28. Standardize terminology

Use:

### Coverage
Percentage of all evaluated cases auto-handled.

### Selective Accuracy
Accuracy among auto-handled cases.

### Unsafe Auto-Handling Rate
Unsafe auto-handled cases divided by the declared denominator.

### Unnecessary Escalation Rate
Cases escalated despite being labeled auto-eligible, using a clearly stated denominator.

Use these terms consistently throughout README, report, and code output.

---

## 29. Use a multi-metric headline

Do not headline only:

> “90.7% accuracy.”

A more honest headline is:

> **“On 1,800 unseen conversations, the system auto-handled 17.9% of cases with 90.7% selective accuracy, while achieving 99.58% escalation recall and 0.22% unsafe auto-handling.”**

This communicates both capability and restraint.

---

# 🟢 D. Things That Are Already Good — Do Not Rebuild

These parts already align well with the Hiver assignment:

- One selected brand: AmazonHelp.
- Brand-specific intent taxonomy.
- Conversation-level train/validation/test partitioning.
- FAISS index built from training data.
- 200-example golden set, within Hiver's required 150–250 range.
- Majority-class baseline.
- TF-IDF + Logistic Regression baseline.
- Retrieval-based production model.
- Grounded response generation.
- Explicit Trust Gate.
- Explicit escalation reason codes.
- Zero-leakage verification.
- LLM-as-judge.
- Human judge validation.
- Top failure-mode analysis.
- “What is misleading about my headline number?”
- One-more-week roadmap.
- 15-decision decision log.
- Reproducibility instructions.
- Automated test suite.

The architecture is already appropriate:

```text
Customer Message
      ↓
Intent Classification
      ↓
Historical Precedent Retrieval
      ↓
Grounded Response
      ↓
Trust Gate
      ↓
AUTO-HANDLE / ESCALATE
```

---

# Final Fix Order

Do not give everything to the coding agent at once. Work in this order.

## Phase 1 — Verify Data Integrity

1. Check every reported metric against the actual JSON/CSV outputs.
2. Resolve 203 vs 215 failure counts.
3. Resolve 50 vs 46 judge-validation cases.
4. Verify Golden/Test/Validation separation.
5. Verify threshold selection methodology.
6. Verify the actual majority class.

## Phase 2 — Evaluation Definitions

7. Define Coverage.
8. Define Selective Accuracy.
9. Define Unsafe Auto-Handling Rate.
10. Define Unnecessary Escalation Rate.
11. Define Unsupported Claim Rate.
12. Document golden-set sampling and labelling.

## Phase 3 — LLM Judge

13. Decide whether to keep Qwen 0.5B or replace it.
14. If replacing, rerun the 50-case human comparison.
15. Recalculate judge-human agreement.
16. Rerun the 200-case golden evaluation.
17. Recalculate failure modes.

## Phase 4 — Documentation

18. Fix threshold wording.
19. Fix headline metrics.
20. Standardize terminology.
21. Fix README test badge.
22. Remove or source unsupported cost estimates.
23. Verify report page count.

## Phase 5 — Final Verification

Run:

```bash
python scripts/check_evaluation_leakage.py
python scripts/validate_judge.py
python scripts/run_golden_evaluation.py
python scripts/run_evaluation.py
pytest tests/ -v
```

Then compare:

```text
evaluation_results.json
golden_evaluation_results.json
judge_human_validation.json
        ↓
TECHNICAL_REPORT.md
        ↓
README.md
```

Every reported number must trace back to an actual evaluation artifact.

---

# Final Principle

The project does not need more features.

The highest-value remaining work is:

**make every number correct → make every metric clearly defined → make the evaluation methodology reproducible → make the claims appropriately modest.**

Once those checks pass, the project should be in strong shape for submission.
